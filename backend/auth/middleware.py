"""
Authentication middleware for FastAPI.
Implements secure session management and token validation.
"""

from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from typing import Optional, Callable
import structlog
from auth.utils import token_manager
from config import settings

logger = structlog.get_logger()

# HTTP Bearer token scheme
security = HTTPBearer(auto_error=False)


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Middleware to handle authentication for protected routes."""
    
    def __init__(self, app, exempt_paths: Optional[list] = None):
        super().__init__(app)
        self.exempt_paths = exempt_paths or [
            "/docs",
            "/redoc", 
            "/openapi.json",
            "/auth/login",
            "/auth/callback",
            "/health"
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process requests and validate authentication."""
        path = request.url.path
        
        # Skip authentication for exempt paths
        if any(path.startswith(exempt) for exempt in self.exempt_paths):
            return await call_next(request)
        
        # Extract token from Authorization header or cookies
        token = self._extract_token(request)
        
        if not token:
            logger.warning("No authentication token provided", path=path)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verify token
        payload = token_manager.verify_token(token)
        if not payload:
            logger.warning("Invalid authentication token", path=path)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Add user info to request state
        request.state.user = {
            "id": payload.get("sub"),
            "email": payload.get("email"),
            "name": payload.get("name")
        }
        
        response = await call_next(request)
        return response
    
    def _extract_token(self, request: Request) -> Optional[str]:
        """Extract token from Authorization header or cookies."""
        # Try Authorization header first
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            return auth_header[7:]  # Remove "Bearer " prefix
        
        # Try cookie fallback for browser requests
        return request.cookies.get("access_token")


async def get_current_user(request: Request) -> dict:
    """Dependency to get current authenticated user from cookies or headers."""
    # Try to get token from cookies first (for browser requests)
    token = request.cookies.get("access_token")
    
    # If no cookie, try Authorization header
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]  # Remove "Bearer " prefix
    
    if not token:
        logger.error("No authentication token found in request", 
                    cookies=list(request.cookies.keys()),
                    headers=request.headers.get("Authorization"))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    payload = token_manager.verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Log successful authentication for debugging
    if settings.debug:
        logger.info(
            "User authenticated successfully", 
            user_id=payload.get("sub"),
            email=payload.get("email"),
            token_type=payload.get("type", "unknown")
        )
    
    return {
        "id": payload.get("sub"),
        "email": payload.get("email"),
        "name": payload.get("name"),
        "azure_user_id": payload.get("azure_user_id")
    }


async def get_current_active_user(request: Request) -> dict:
    """Dependency to get current active user with database validation."""
    current_user = await get_current_user(request)
    
    # In a real implementation, you would check the database here
    # to ensure the user is still active
    return current_user


class SecurityHeaders:
    """Security headers middleware for enhanced protection."""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        """Add security headers to all responses."""
        if scope["type"] == "http":
            async def send_wrapper(message):
                if message["type"] == "http.response.start":
                    headers = dict(message.get("headers", []))
                    
                    # Add security headers
                    security_headers = {
                        b"X-Content-Type-Options": b"nosniff",
                        b"X-Frame-Options": b"DENY",
                        b"X-XSS-Protection": b"1; mode=block",
                        b"Strict-Transport-Security": b"max-age=31536000; includeSubDomains",
                        b"Content-Security-Policy": b"default-src 'self'",
                        b"Referrer-Policy": b"strict-origin-when-cross-origin"
                    }
                    
                    headers.update(security_headers)
                    message["headers"] = list(headers.items())
                
                await send(message)
            
            await self.app(scope, receive, send_wrapper)
        else:
            await self.app(scope, receive, send)
