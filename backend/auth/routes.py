"""
Authentication routes for Azure AD OAuth2 integration.
Implements Authorization Code Flow with PKCE for secure authentication.
"""

from fastapi import APIRouter, Request, Response, HTTPException, Depends, status
from fastapi.responses import RedirectResponse, JSONResponse
from typing import Dict, Any, Optional
import httpx
import msal
import structlog
import asyncio
from urllib.parse import urlencode, parse_qs
from datetime import datetime, timezone

from config import settings
from auth.utils import pkce_generator, token_manager, state_manager, generate_session_id
from auth.middleware import get_current_user
from dataverse_service import get_dataverse_service

logger = structlog.get_logger()

router = APIRouter(prefix="/auth", tags=["authentication"])

# In-memory store for PKCE and state (use Redis in production)
_auth_state_store = {}


@router.get("/login")
async def initiate_login(request: Request):
    """
    Initiate OAuth2 login flow with Azure AD.
    Generates PKCE challenge and redirects to Azure AD.
    """
    try:
        # Generate PKCE parameters
        code_verifier, code_challenge = pkce_generator.generate_pkce_pair()
        
        # Generate state for CSRF protection
        state = state_manager.generate_state()
        
        # Store PKCE verifier and state temporarily
        session_key = generate_session_id()
        _auth_state_store[session_key] = {
            "code_verifier": code_verifier,
            "state": state,
            "timestamp": datetime.now(timezone.utc)
        }
        
        # Build Azure AD authorization URL
        # Embed session key in state parameter as a fallback for browsers that block cookies
        # Format: original_state:session_key
        state_with_session = f"{state}:{session_key}"
        
        auth_params = {
            "client_id": settings.azure_client_id,
            "response_type": "code",
            "redirect_uri": settings.azure_redirect_uri,
            "scope": " ".join(settings.azure_scope),
            "state": state_with_session,  # Use combined state with session key
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
            "response_mode": "query"
        }
        
        auth_url = f"{settings.azure_authority}/oauth2/v2.0/authorize?" + urlencode(auth_params)
        
        # Debug logging for OAuth parameters
        print(f"🔵 [DEBUG] Azure scopes being requested: {settings.azure_scope}")
        print(f"🔵 [DEBUG] Scope string: {' '.join(settings.azure_scope)}")
        print(f"🔵 [DEBUG] Clean authentication approach (no Dataverse scope during login)")
        print(f"🔵 [DEBUG] Session tracking will be handled separately")
        
        logger.info("OAuth Parameters", 
                   client_id=settings.azure_client_id,
                   redirect_uri=settings.azure_redirect_uri,
                   auth_url=auth_url[:100] + "..." if len(auth_url) > 100 else auth_url)
        
        logger.info("Login initiated", session_key=session_key)
        
        # Create response with session key in cookie
        response = RedirectResponse(url=auth_url, status_code=302)
        
        # Get cookie settings
        secure_setting = not (settings.environment == "development" and settings.debug)
        
        # For local development with secure=false, we must use samesite="lax" not "none"
        # SameSite=None requires Secure=true in modern browsers
        if settings.environment == "development" and settings.debug:
            samesite_setting = "lax"  # Use "lax" for localhost development
        else:
            samesite_setting = settings.cookie_samesite
        
        # For local development, we don't set a domain to ensure cookies work on localhost
        domain = None
        
        response.set_cookie(
            key="auth_session",
            value=session_key,
            max_age=600,  # 10 minutes
            httponly=True,
            secure=secure_setting,
            samesite=samesite_setting,
            path="/",
            domain=domain
        )
        
        return response
        
    except Exception as e:
        logger.error("Login initiation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate login"
        )


@router.get("/callback")
async def handle_callback(request: Request):
    """
    Handle OAuth2 callback from Azure AD.
    Exchanges authorization code for tokens.
    """
    print(f"🔵 [DEBUG] === CALLBACK START ===")
    print(f"🔵 [DEBUG] Request URL: {request.url}")
    print(f"🔵 [DEBUG] Request cookies: {request.cookies}")
    
    try:
        # Get query parameters
        code = request.query_params.get("code")
        state = request.query_params.get("state")
        error = request.query_params.get("error")
        
        print(f"🔵 [DEBUG] Query parameters:")
        print(f"  - code: {'Present' if code else 'Missing'}")
        print(f"  - state: {state}")
        print(f"  - error: {error}")
        
        if error:
            print(f"🔴 [DEBUG] OAuth error received: {error}")
            logger.error("OAuth callback error", error=error)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Authentication failed: {error}"
            )
        
        if not code or not state:
            print(f"🔴 [DEBUG] Missing required parameters!")
            logger.error("Missing code or state in callback")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid callback parameters"
            )
        
        # Get session data
        session_key = request.cookies.get("auth_session")
        print(f"🔵 [DEBUG] Session key from cookies: {session_key}")
        
        # ALWAYS check if state contains embedded session info (format: state_value:session_key)
        # This handles the case where Azure AD returns the combined state parameter
        original_state = state
        if state and ":" in state:
            state_parts = state.split(":", 1)
            embedded_session_key = state_parts[1]
            state = state_parts[0]  # Extract the original CSRF state token
            print(f"🔵 [DEBUG] Extracted session key from state: {embedded_session_key}")
            print(f"🔵 [DEBUG] Updated state value: {state}")
            
            # Use embedded session key if cookies don't have it or if it's not in store
            if not session_key or session_key not in _auth_state_store:
                if embedded_session_key in _auth_state_store:
                    print(f"🔵 [DEBUG] Using embedded session key from state parameter")
                    logger.info("Using session key embedded in state parameter", 
                               embedded_key=embedded_session_key)
                    session_key = embedded_session_key
                else:
                    print(f"🔴 [DEBUG] Embedded session key not found in store")
                    logger.warning("Embedded session key not found in state store", 
                                  embedded_key=embedded_session_key)
            else:
                print(f"🔵 [DEBUG] Session key from cookies is valid, using that")
        
        print(f"🔵 [DEBUG] Final session key: {session_key}")
        print(f"🔵 [DEBUG] Final state value: {state}")
        logger.info("Processing OAuth callback", session_key=session_key, original_state=original_state)
        
        if not session_key or session_key not in _auth_state_store:
            # Try all fallback approaches
            
            # Approach 1: Check all auth state store keys
            if len(_auth_state_store) > 0:
                # For development only - use the most recent auth session
                newest_session = max(_auth_state_store.items(), 
                                    key=lambda x: x[1]["timestamp"] if "timestamp" in x[1] else datetime.min)
                newest_key = newest_session[0]
                
                logger.warning("Using most recent session as fallback", 
                             newest_key=newest_key,
                             time_diff=(datetime.now(timezone.utc) - newest_session[1]["timestamp"]).seconds,
                             available_sessions=len(_auth_state_store))
                
                session_key = newest_key
            # Approach 2: Create emergency session
            elif settings.environment == "development" and settings.debug:
                # Create an emergency session with a new code verifier
                emergency_session_key = generate_session_id()
                emergency_code_verifier = pkce_generator.generate_code_verifier()
                
                logger.warning("Creating emergency session in dev mode", 
                              emergency_session=emergency_session_key)
                
                _auth_state_store[emergency_session_key] = {
                    "code_verifier": emergency_code_verifier,
                    "state": state,  # Use received state
                    "timestamp": datetime.now(timezone.utc),
                    "is_emergency": True
                }
                
                session_key = emergency_session_key
            # Approach 3: Fail with helpful error message
            else:
                logger.error("Invalid or missing auth session", 
                            session_key=session_key, 
                            available_sessions=list(_auth_state_store.keys()),
                            all_cookies=dict(request.cookies),
                            has_embedded_state=(":" in state if state else False))
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid authentication session"
                )
        
        auth_data = _auth_state_store.pop(session_key)
        
        print(f"🔵 [DEBUG] --- STEP 1: State verification ---")
        # Verify state parameter
        if not state_manager.verify_state(auth_data["state"], state):
            # In development with emergency sessions, skip state verification
            if settings.environment == "development" and settings.debug and auth_data.get("is_emergency", False):
                print(f"🟡 [DEBUG] Skipping state verification for emergency session in dev mode")
                logger.warning(
                    "Skipping state verification for emergency session in development mode", 
                    expected_state=auth_data["state"][:10],
                    received_state=state[:10] if state else None
                )
            else:
                print(f"🔴 [DEBUG] State parameter mismatch!")
                print(f"  Expected: {auth_data['state'][:10]}...")
                print(f"  Received: {state[:10] if state else None}...")
                logger.error(
                    "State parameter mismatch",
                    expected_state=auth_data["state"][:10],
                    received_state=state[:10] if state else None,
                    is_emergency=auth_data.get("is_emergency", False)
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid state parameter"
                )
        
        print(f"🟢 [DEBUG] State verification passed")
        
        print(f"🔵 [DEBUG] --- STEP 2: Token exchange ---")
        # Exchange authorization code for tokens
        tokens = await _exchange_code_for_tokens(code, auth_data["code_verifier"])
        print(f"🟢 [DEBUG] Token exchange successful")
        print(f"🔵 [DEBUG] Access token length: {len(tokens['access_token']) if tokens.get('access_token') else 'None'}")
        
        print(f"🔵 [DEBUG] --- STEP 3: Get user info ---")
        # Get user information from Microsoft Graph
        user_info = await _get_user_info(tokens["access_token"])
        print(f"🟢 [DEBUG] User info retrieved")
        print(f"🔵 [DEBUG] User info: {user_info}")
        
        # Create or update user - simplified approach
        # Just store Azure AD user info and create session tracking
        user = await _create_or_update_user_simple(user_info, request)
        print(f"🟢 [DEBUG] User creation/update completed")
        print(f"🔵 [DEBUG] User data: {user}")
        
        print(f"🔵 [DEBUG] --- STEP 5: Generate app tokens ---")
        # Generate application tokens
        token_data = {
            "sub": str(user["id"]),
            "email": user["email"],
            "name": user["name"],
            "azure_user_id": user["azure_user_id"]
        }
        
        access_token = token_manager.create_access_token(token_data)
        refresh_token = token_manager.create_refresh_token(token_data)
        
        print(f"🟢 [DEBUG] Application tokens generated")
        
        logger.info("User authenticated successfully", user_id=user["id"])
        
        print(f"🔵 [DEBUG] --- STEP 6: Prepare response ---")
        # Instead of setting cookies in the redirect response, 
        # store the tokens temporarily and redirect with a success token
        success_token = generate_session_id()
        
        # Store tokens temporarily for the frontend to retrieve
        _auth_state_store[success_token] = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user_data": token_data,
            "timestamp": datetime.now(timezone.utc),
            "type": "auth_success"
        }
        
        # Create response redirecting to frontend with success token
        frontend_url = f"{settings.allowed_origins[0]}/callback?success_token={success_token}"
        response = RedirectResponse(url=frontend_url, status_code=302)
        
        print(f"🟢 [DEBUG] === CALLBACK SUCCESS ===")
        print(f"🟢 [DEBUG] Redirecting to: {frontend_url}")
        print(f"🟢 [DEBUG] Success token: {success_token}")
        
        logger.info(
            "Redirecting to frontend with success token",
            frontend_url=frontend_url,
            success_token=success_token,
            user_email=user.get("email", "unknown")
        )
        
        return response
        
    except HTTPException as he:
        print(f"🔴 [DEBUG] HTTP Exception in callback: {he.detail}")
        print(f"🔴 [DEBUG] Status code: {he.status_code}")
        raise
    except Exception as e:
        print(f"🔴 [DEBUG] Unexpected exception in callback: {str(e)}")
        print(f"🔴 [DEBUG] Exception type: {type(e).__name__}")
        logger.error("Callback handling failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication callback failed"
        )


@router.post("/complete-auth")
async def complete_authentication(request: Request):
    """
    Complete authentication by exchanging success token for auth cookies.
    This is called by the frontend after OAuth callback redirect.
    """
    try:
        # Get request body
        body = await request.json()
        success_token = body.get("success_token")
        
        if not success_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Success token required"
            )
        
        # Retrieve stored auth data
        if success_token not in _auth_state_store:
            logger.error("Invalid success token", token=success_token)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired success token"
            )
        
        auth_data = _auth_state_store.pop(success_token)
        
        # Verify this is an auth success token
        if auth_data.get("type") != "auth_success":
            logger.error("Invalid token type", token_type=auth_data.get("type"))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token type"
            )
        
        # Get tokens and user data
        access_token = auth_data["access_token"]
        refresh_token = auth_data["refresh_token"]
        user_data = auth_data["user_data"]
        
        logger.info("Completing authentication", user_email=user_data.get("email"))
        
        # Return tokens directly in response body for localStorage storage
        # No cookies needed - use Authorization header approach instead
        response = JSONResponse(content={
            "status": "success",
            "message": "Authentication completed",
            "tokens": {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "Bearer",
                "expires_in": settings.access_token_expire_minutes * 60
            },
            "user": {
                "id": user_data["sub"],
                "email": user_data["email"],
                "name": user_data["name"],
                "azure_user_id": user_data["azure_user_id"]
            }
        })
        
        print(f"🔵 [DEBUG] === COOKIELESS AUTH RESPONSE ===")
        print(f"🔵 [DEBUG] Returning tokens in response body for localStorage storage")
        print(f"🔵 [DEBUG] Access token length: {len(access_token)}")
        print(f"🔵 [DEBUG] No cookies needed - using Authorization header approach")
        
        logger.info("Authentication completed successfully", user_email=user_data["email"])
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Complete authentication failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete authentication"
        )


@router.post("/refresh")
async def refresh_token(request: Request):
    """Refresh access token using refresh token."""
    try:
        # Try to get refresh token from request body first (new approach)
        refresh_token = None
        try:
            body = await request.json()
            refresh_token = body.get("refresh_token")
            print(f"🔵 [DEBUG] Refresh token from request body: {'Found' if refresh_token else 'None'}")
        except:
            print(f"🔵 [DEBUG] No JSON body or refresh_token in body")
        
        # Fallback: Check cookies for backward compatibility
        if not refresh_token:
            refresh_token = request.cookies.get("refresh_token")
            if refresh_token:
                print(f"🔵 [DEBUG] Refresh token found in cookie (fallback)")
        
        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token not found"
            )
        
        # Generate new tokens
        tokens = token_manager.refresh_access_token(refresh_token)
        if not tokens:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        new_access_token, new_refresh_token = tokens
        
        # Return new tokens in response body (no cookies)
        response = JSONResponse({
            "status": "success",
            "message": "Tokens refreshed successfully",
            "tokens": {
                "access_token": new_access_token,
                "refresh_token": new_refresh_token,
                "token_type": "Bearer",
                "expires_in": settings.access_token_expire_minutes * 60
            }
        })
        
        print(f"🔵 [DEBUG] === TOKEN REFRESH SUCCESS ===")
        print(f"🔵 [DEBUG] Returning new tokens in response body (no cookies)")
        print(f"🔵 [DEBUG] New access token length: {len(new_access_token)}")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Token refresh failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )


@router.post("/logout")
async def logout(request: Request):
    """Logout user and clear tokens."""
    try:
        logger.info("User logout")
        
        # Create response - client will clear localStorage
        response = JSONResponse({
            "status": "success",
            "message": "Logged out successfully. Clear tokens from localStorage."
        })
        
        print(f"🔵 [DEBUG] === LOGOUT ===")
        print(f"🔵 [DEBUG] Client should clear tokens from localStorage")
        
        return response
        
    except Exception as e:
        logger.error("Logout failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


@router.get("/user")
async def get_current_user_info(request: Request):
    """Get current authenticated user information."""
    try:
        print(f"🔵 [DEBUG] === /auth/user REQUEST ===")
        print(f"🔵 [DEBUG] All request cookies: {dict(request.cookies)}")
        print(f"🔵 [DEBUG] Authorization header: {request.headers.get('Authorization')}")
        
        # Primary: Check Authorization header for Bearer token
        token = None
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]  # Remove "Bearer " prefix
            print(f"🔵 [DEBUG] Token found in Authorization header")
        
        # Fallback: Check cookies for backward compatibility
        if not token:
            token = request.cookies.get("auth_token")
            if token:
                print(f"🔵 [DEBUG] Token found in auth_token cookie (fallback)")
        
        print(f"🔵 [DEBUG] Final token status: {'Found' if token else 'None'}")
        
        if not token:
            logger.error("No authentication token found in request", 
                       cookies=dict(request.cookies),
                       has_auth_header=bool(request.headers.get("Authorization")))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
            
        # Verify token manually (don't rely on middleware for this endpoint)
        payload = token_manager.verify_token(token)
        if not payload:
            logger.error("Invalid authentication token")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token"
            )
        
        # Get user information from token
        user_data = {
            "id": payload.get("sub"),
            "email": payload.get("email"),
            "name": payload.get("name"),
            "azure_user_id": payload.get("azure_user_id"),
            "is_active": True
        }
        
        # Include access token in development for hybrid auth approach
        if settings.debug and settings.environment == "development":
            user_data["accessToken"] = token
            
        logger.info("User authenticated successfully", user_id=user_data["id"])
        return user_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get user info", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )


@router.get("/login-url")
async def get_login_url(request: Request):
    """
    Get OAuth2 login URL for API clients.
    Returns the authorization URL instead of redirecting.
    """
    try:
        # Generate PKCE parameters
        code_verifier, code_challenge = pkce_generator.generate_pkce_pair()
        
        # Generate state for CSRF protection
        state = state_manager.generate_state()
        
        # Store PKCE verifier and state temporarily
        session_key = generate_session_id()
        _auth_state_store[session_key] = {
            "code_verifier": code_verifier,
            "state": state,
            "timestamp": datetime.now(timezone.utc)
        }
        
        # Build Azure AD authorization URL
        auth_params = {
            "client_id": settings.azure_client_id,
            "response_type": "code",
            "redirect_uri": settings.azure_redirect_uri,
            "scope": " ".join(settings.azure_scope),
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
            "response_mode": "query"
        }
        
        auth_url = f"{settings.azure_authority}/oauth2/v2.0/authorize?" + urlencode(auth_params)
        
        logger.info("Login URL generated", session_key=session_key)
        
        return {
            "auth_url": auth_url,
            "session_key": session_key,
            "state": state
        }
        
    except Exception as e:
        logger.error("Login URL generation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate login URL"
        )


@router.get("/dataverse-token")
async def get_dataverse_token(request: Request):
    """
    Get a Dataverse access token for the current user.
    This is called only when the app needs to access Dataverse data.
    """
    try:
        # Verify user is authenticated first - prioritize Authorization header
        token = None
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]
        
        # Fallback: Check cookies
        if not token:
            token = request.cookies.get("auth_token")
        
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
            
        payload = token_manager.verify_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token"
            )
        
        print(f"🔵 [DEBUG] Getting Dataverse token for user: {payload.get('email')}")
        
        # Get Dataverse token using client credentials (app-only access)
        dataverse_token = await _get_dataverse_token()
        
        if not dataverse_token:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Unable to obtain Dataverse access token"
            )
        
        print(f"🟢 [DEBUG] Dataverse token obtained successfully")
        
        return {
            "access_token": dataverse_token,
            "token_type": "Bearer",
            "scope": "dataverse",
            "expires_in": 3600  # Typical token lifetime
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get Dataverse token", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to obtain Dataverse access token"
        )


@router.get("/dataverse/user-sessions")
async def get_user_sessions(request: Request):
    """
    Get user sessions from Dataverse.
    Example of how to access Dataverse data with proper permissions.
    """
    try:
        # Verify user is authenticated - prioritize Authorization header
        token = None
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]
        
        # Fallback: Check cookies
        if not token:
            token = request.cookies.get("auth_token")
        
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
            
        payload = token_manager.verify_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token"
            )
        
        user_id = payload.get("azure_user_id") or payload.get("sub")
        print(f"🔵 [DEBUG] Getting sessions for user: {user_id}")
        
        # Get Dataverse token
        dataverse_token = await _get_dataverse_token()
        if not dataverse_token:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Unable to access Dataverse"
            )
        
        # Query user sessions from Dataverse
        dataverse = get_dataverse_service(settings.dataverse_environment_url)
        
        # Use Dataverse Web API to query sessions
        query_url = f"{dataverse.base_url}/hbrd_usersessions?$filter=hbrd_azureuserid eq '{user_id}'&$orderby=hbrd_sessionstart desc&$top=10"
        
        headers = dataverse._get_headers(dataverse_token)
        
        async with httpx.AsyncClient() as client:
            response = await client.get(query_url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            sessions = data.get("value", [])
            
            print(f"🟢 [DEBUG] Retrieved {len(sessions)} sessions for user")
            
            # Transform data for frontend
            formatted_sessions = []
            for session in sessions:
                formatted_sessions.append({
                    "id": session.get("hbrd_usersessionid"),
                    "session_start": session.get("hbrd_sessionstart"),
                    "ip_address": session.get("hbrd_ipaddress"),
                    "user_agent": session.get("hbrd_useragent"),
                    "name": session.get("hbrd_name")
                })
            
            return {
                "sessions": formatted_sessions,
                "total": len(formatted_sessions)
            }
        else:
            print(f"🔴 [DEBUG] Dataverse query failed: {response.status_code}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to Dataverse data"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get user sessions", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user sessions"
        )


async def _exchange_code_for_tokens(code: str, code_verifier: str) -> Dict[str, Any]:
    """Exchange authorization code for access token using PKCE."""
    token_data = {
        "client_id": settings.azure_client_id,
        "client_secret": settings.azure_client_secret,
        "code": code,
        "redirect_uri": settings.azure_redirect_uri,
        "grant_type": "authorization_code",
        "code_verifier": code_verifier
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.azure_authority}/oauth2/v2.0/token",
            data=token_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
    
    if response.status_code != 200:
        logger.error("Token exchange failed", status_code=response.status_code, response=response.text)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to exchange authorization code for tokens"
        )
    
    token_response = response.json()
    
    # Debug: Show token details
    print(f"DEBUG: Token exchange successful")
    print(f"DEBUG: Token type: {token_response.get('token_type', 'Unknown')}")
    print(f"DEBUG: Expires in: {token_response.get('expires_in', 'Unknown')} seconds")
    print(f"DEBUG: Scope received: {token_response.get('scope', 'No scope in response')}")
    
    # Decode access token to see claims (for debugging only)
    access_token = token_response.get('access_token', '')
    if access_token:
        try:
            import base64
            import json
            # JWT tokens have 3 parts separated by dots
            parts = access_token.split('.')
            if len(parts) >= 2:
                # Decode the payload (second part)
                payload = parts[1]
                # Add padding if needed
                padding = 4 - (len(payload) % 4)
                if padding != 4:
                    payload += '=' * padding
                decoded = base64.urlsafe_b64decode(payload)
                claims = json.loads(decoded)
                print(f"DEBUG: Token audience (aud): {claims.get('aud', 'Not found')}")
                print(f"DEBUG: Token scopes (scp): {claims.get('scp', 'Not found')}")
                print(f"DEBUG: Token issuer (iss): {claims.get('iss', 'Not found')}")
                print(f"DEBUG: Token app ID (appid): {claims.get('appid', 'Not found')}")
        except Exception as e:
            print(f"DEBUG: Could not decode token for analysis: {e}")
    
    return token_response


async def _get_user_info(access_token: str) -> Dict[str, Any]:
    """Get user information from Microsoft Graph API."""
    headers = {"Authorization": f"Bearer {access_token}"}
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://graph.microsoft.com/v1.0/me",
            headers=headers
        )
    
    if response.status_code != 200:
        logger.error("Failed to get user info", status_code=response.status_code)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to get user information"
        )
    
    return response.json()


async def _create_or_update_user_simple(user_info: Dict[str, Any], request: Optional[Request] = None) -> Dict[str, Any]:
    """
    Simple user creation - just return Azure AD user data without Dataverse complexity.
    Session tracking is handled separately when needed.
    
    Args:
        user_info: User info from Microsoft Graph
        request: Request object to get IP and user agent
        
    Returns:
        User data for the application
    """
    print(f"🔵 [DEBUG] === _create_or_update_user_simple START ===")
    
    azure_user_id = user_info.get("id")
    if not azure_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing Azure user ID"
        )
    
    email = user_info.get("mail") or user_info.get("userPrincipalName")
    display_name = user_info.get("displayName") or "Unknown User"
    
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing user email"
        )
    
    print(f"🔵 [DEBUG] Azure User ID: {azure_user_id}")
    print(f"🔵 [DEBUG] Email: {email}")
    print(f"🔵 [DEBUG] Display Name: {display_name}")
    
    # Return user data for application use (no Dataverse calls during login)
    user_data = {
        "id": azure_user_id,  # Using Azure AD ID as primary identifier
        "azure_user_id": azure_user_id,
        "email": email,
        "name": display_name,
        "given_name": user_info.get("givenName"),
        "family_name": user_info.get("surname"),
        "job_title": user_info.get("jobTitle"),
        "department": user_info.get("department"),
        "source": "azure_ad"
    }
    
    print(f"🔵 [DEBUG] User data built: {user_data}")
    print(f"🟢 [DEBUG] === _create_or_update_user_simple SUCCESS ===")
    
    # Optional: Track session in background (non-blocking)
    if request and settings.dataverse_environment_url:
        # This runs in background and doesn't block the login flow
        asyncio.create_task(_track_user_session_background(user_data, request))
    
    return user_data


async def _track_user_session_background(user_data: Dict[str, Any], request: Request):
    """
    Track user session in Dataverse in background (non-blocking).
    This doesn't affect the login flow if it fails.
    """
    try:
        print(f"🔵 [DEBUG] === Background session tracking START ===")
        
        # Get Dataverse token when needed (separate from login token)
        dataverse_token = await _get_dataverse_token()
        if not dataverse_token:
            print(f"🟡 [DEBUG] No Dataverse token available, skipping session tracking")
            return
        
        # Extract request info
        ip_address = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")[:500]
        
        # Create session record
        dataverse = get_dataverse_service(settings.dataverse_environment_url)
        session_id = await dataverse.create_user_session(
            azure_user_id=user_data["azure_user_id"],
            user_name=user_data.get("name", "Unknown"),
            ip_address=ip_address,
            user_agent=user_agent,
            access_token=dataverse_token
        )
        
        if session_id:
            print(f"🟢 [DEBUG] Background session tracking successful: {session_id}")
        else:
            print(f"🟡 [DEBUG] Background session tracking failed")
            
    except Exception as e:
        print(f"🟡 [DEBUG] Background session tracking error (non-critical): {str(e)}")
        logger.warning("Background session tracking failed", error=str(e))


async def _get_dataverse_token() -> Optional[str]:
    """
    Get a Dataverse token using client credentials flow (app-only).
    This is separate from the user's login token.
    """
    try:
        # Use client credentials flow for app-only Dataverse access
        token_data = {
            "client_id": settings.azure_client_id,
            "client_secret": settings.azure_client_secret,
            "scope": f"{settings.dataverse_environment_url}/.default",
            "grant_type": "client_credentials"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.azure_authority}/oauth2/v2.0/token",
                data=token_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
        
        if response.status_code == 200:
            token_response = response.json()
            return token_response.get("access_token")
        else:
            print(f"🟡 [DEBUG] Failed to get Dataverse token: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"🟡 [DEBUG] Dataverse token request error: {str(e)}")
        return None


async def _create_or_update_user(user_info: Dict[str, Any], access_token: Optional[str] = None, request: Optional[Request] = None) -> Dict[str, Any]:
    """
    Create or update user using pure Dataverse integration.
    
    This function will:
    1. Create/update user app metadata in Dataverse
    2. Create a new session record in Dataverse for audit tracking
    3. Return user data for application use
    
    Args:
        user_info: User info from Microsoft Graph
        access_token: Access token with Dataverse permissions
        request: Request object to get IP and user agent
        
    Returns:
        User data for the application
    """
    print(f"🔵 [DEBUG] === _create_or_update_user START ===")
    print(f"🔵 [DEBUG] User info received: {user_info}")
    print(f"🔵 [DEBUG] Access token provided: {bool(access_token)}")
    print(f"🔵 [DEBUG] Request object provided: {bool(request)}")
    
    if not access_token:
        print(f"🔴 [DEBUG] ERROR: No access token provided!")
        logger.error("Access token required for Dataverse integration")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Missing access token for Dataverse access"
        )
    
    azure_user_id = user_info.get("id")
    if not azure_user_id:
        print(f"🔴 [DEBUG] ERROR: No Azure user ID in user_info!")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing Azure user ID"
        )
    
    print(f"🔵 [DEBUG] Azure User ID: {azure_user_id}")
    
    email = user_info.get("mail") or user_info.get("userPrincipalName")
    display_name = user_info.get("displayName") or "Unknown User"
    
    print(f"🔵 [DEBUG] Email: {email}")
    print(f"🔵 [DEBUG] Display Name: {display_name}")
    
    if not email:
        print(f"🔴 [DEBUG] ERROR: No email found in user_info!")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing user email"
        )
    
    # Get Dataverse service
    if not settings.dataverse_environment_url:
        print(f"🔴 [DEBUG] ERROR: Dataverse environment URL not configured!")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Dataverse environment URL not configured"
        )
        
    print(f"🔵 [DEBUG] Dataverse URL: {settings.dataverse_environment_url}")
    dataverse = get_dataverse_service(settings.dataverse_environment_url)
    print(f"🔵 [DEBUG] Dataverse service initialized")
    
    try:
        print(f"🔵 [DEBUG] --- STEP 1: Creating/updating user metadata ---")
        # Create or update user app metadata
        metadata_success = await dataverse.create_or_update_user_metadata(
            azure_user_id=azure_user_id,
            email=email,
            display_name=display_name,
            access_token=access_token
        )
        
        print(f"🔵 [DEBUG] User metadata operation result: {metadata_success}")
        
        if not metadata_success:
            print(f"🟡 [DEBUG] WARNING: Failed to create/update user metadata, continuing with session creation")
            logger.warning("Failed to create/update user metadata, continuing with session creation")
        
        print(f"🔵 [DEBUG] --- STEP 2: Extracting request info ---")
        # Create session record for audit tracking
        ip_address = "unknown"
        user_agent = "unknown"
        
        if request:
            print(f"🔵 [DEBUG] Request object available, extracting IP and user agent")
            # Get client IP (handling reverse proxy scenarios)
            ip_address = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
            if not ip_address:
                ip_address = request.headers.get("x-real-ip", "")
            if not ip_address and request.client:
                ip_address = request.client.host
            
            # Get user agent
            user_agent = request.headers.get("user-agent", "unknown")
            
            # Truncate if too long
            if len(user_agent) > 500:
                user_agent = user_agent[:497] + "..."
                
            print(f"🔵 [DEBUG] Extracted IP: {ip_address}")
            print(f"🔵 [DEBUG] Extracted User Agent: {user_agent[:100]}...")
        else:
            print(f"🟡 [DEBUG] No request object - using default values")
        
        print(f"🔵 [DEBUG] --- STEP 3: Creating session record ---")
        session_id = await dataverse.create_user_session(
            azure_user_id=azure_user_id,
            user_name=user_info.get("displayName", user_info.get("name", "Unknown User")),
            ip_address=ip_address or "unknown",
            user_agent=user_agent or "unknown",
            access_token=access_token
        )
        
        print(f"🔵 [DEBUG] Session creation result: {session_id}")
        
        if not session_id:
            print(f"🟡 [DEBUG] WARNING: Failed to create session record in Dataverse")
            logger.warning("Failed to create session record in Dataverse")
        
        print(f"🔵 [DEBUG] --- STEP 4: Building response data ---")
        # Return user data for application use
        user_data = {
            "id": azure_user_id,  # Using Azure AD ID as primary identifier
            "azure_user_id": azure_user_id,
            "email": email,
            "name": display_name,
            "given_name": user_info.get("givenName"),
            "family_name": user_info.get("surname"),
            "job_title": user_info.get("jobTitle"),
            "department": user_info.get("department"),
            "source": "dataverse",
            "session_id": session_id
        }
        
        print(f"🔵 [DEBUG] User data built: {user_data}")
        
        logger.info("User processed with Dataverse", 
                   email=email, 
                   azure_user_id=azure_user_id,
                   session_id=session_id)
        
        print(f"🟢 [DEBUG] === _create_or_update_user SUCCESS ===")
        return user_data
        
    except HTTPException:
        print(f"🔴 [DEBUG] HTTPException caught and re-raising")
        raise
    except Exception as e:
        print(f"🔴 [DEBUG] Unexpected exception in _create_or_update_user: {str(e)}")
        print(f"🔴 [DEBUG] Exception type: {type(e).__name__}")
        logger.error("Dataverse operation failed", 
                   error=str(e), 
                   azure_user_id=azure_user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process user data in Dataverse"
        )
        
        if existing_user:
            # Update existing user
            if email:
                existing_user.email = email
            if name:
                existing_user.name = name
            if given_name is not None:
                existing_user.given_name = given_name
            if family_name is not None:
                existing_user.family_name = family_name
            if job_title is not None:
                existing_user.job_title = job_title
            if department is not None:
                existing_user.department = department
                
            existing_user.last_login = current_time
            existing_user.updated_at = current_time
            
            db.commit()
            db.refresh(existing_user)
            
            user_data = {
                "id": str(existing_user.id),
                "azure_user_id": existing_user.azure_user_id,
                "email": existing_user.email,
                "name": existing_user.name,
                "given_name": existing_user.given_name,
                "family_name": existing_user.family_name,
                "job_title": existing_user.job_title,
                "department": existing_user.department
            }
            
            logger.info("User updated in database", email=existing_user.email, user_id=str(existing_user.id))



