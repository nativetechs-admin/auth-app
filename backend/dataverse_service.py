"""
Microsoft Dataverse Service
==========================

Service module for integrating with Microsoft Dataverse for user management.
This replaces the local SQLite database with Dataverse as the authoritative 
user data source.
"""

import httpx
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import structlog
from fastapi import HTTPException, status
from config import settings

logger = structlog.get_logger()


class DataverseService:
    """Service for Microsoft Dataverse Web API operations."""
    
    def __init__(self, environment_url: str):
        """
        Initialize Dataverse service.
        
        Args:
            environment_url: Dataverse environment URL (e.g., https://yourorg.crm.dynamics.com)
        """
        self.environment_url = environment_url.rstrip('/')
        self.base_url = f"{self.environment_url}/api/data/v9.2"
    
    def _get_headers(self, access_token: str) -> Dict[str, str]:
        """Get headers for Dataverse API requests."""
        
        # Debug: Show token details for Dataverse call
        print(f"DEBUG: Preparing Dataverse API call")
        print(f"DEBUG: Access token length: {len(access_token) if access_token else 0}")
        print(f"DEBUG: Access token starts with: {access_token[:50] if access_token else 'None'}...")
        print(f"DEBUG: Dataverse base URL: {self.base_url}")
        
        return {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "OData-MaxVersion": "4.0",
            "OData-Version": "4.0",
            "Prefer": "return=representation"
        }
    
    async def get_user_by_azure_id(self, azure_user_id: str, access_token: str) -> Optional[Dict[str, Any]]:
        """
        Get user from Dataverse by Azure AD user ID.
        
        Args:
            azure_user_id: Azure AD user ID (ObjectId)
            access_token: Access token with Dataverse permissions
            
        Returns:
            User data from Dataverse or None if not found
        """
        try:
            headers = self._get_headers(access_token)
            
            # Query systemuser entity by Azure AD object ID
            query = f"systemusers?$filter=azureactivedirectoryobjectid eq '{azure_user_id}'"
            query += "&$select=systemuserid,azureactivedirectoryobjectid,internalemailaddress,fullname,firstname,lastname,title,isdisabled,createdon,modifiedon"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/{query}",
                    headers=headers,
                    timeout=30.0
                )
            
            if response.status_code == 200:
                data = response.json()
                users = data.get("value", [])
                
                if users:
                    user = users[0]  # Should be unique
                    return self._format_user_data(user)
            
            elif response.status_code == 401:
                logger.error("Unauthorized access to Dataverse", azure_user_id=azure_user_id)
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Insufficient permissions for Dataverse access"
                )
            
            elif response.status_code == 403:
                logger.error("Forbidden access to Dataverse", azure_user_id=azure_user_id)
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to Dataverse"
                )
            
            else:
                logger.warning("Dataverse query failed", 
                             status_code=response.status_code,
                             response=response.text[:200])
            
            return None
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to query Dataverse", error=str(e), azure_user_id=azure_user_id)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to query user data from Dataverse"
            )
    
    async def update_user_last_login(self, user_id: str, access_token: str) -> bool:
        """
        Update user's last login timestamp in Dataverse.
        
        Note: This requires a custom field 'new_lastlogintime' to be added
        to the systemuser entity in your Dataverse environment.
        
        Args:
            user_id: Dataverse systemuser ID
            access_token: Access token with Dataverse permissions
            
        Returns:
            True if successful, False otherwise
        """
        try:
            headers = self._get_headers(access_token)
            
            # Update custom field for last login
            # Note: You'll need to create this custom field in Dataverse
            update_data = {
                "new_lastlogintime": datetime.now(timezone.utc).isoformat()
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.patch(
                    f"{self.base_url}/systemusers({user_id})",
                    headers=headers,
                    json=update_data,
                    timeout=30.0
                )
            
            success = response.status_code == 204
            
            if success:
                logger.info("Updated last login in Dataverse", user_id=user_id)
            else:
                logger.warning("Failed to update last login", 
                             status_code=response.status_code,
                             response=response.text[:200])
            
            return success
            
        except Exception as e:
            logger.error("Failed to update last login in Dataverse", error=str(e), user_id=user_id)
            return False
    
    async def get_user_business_unit(self, user_id: str, access_token: str) -> Optional[str]:
        """
        Get user's business unit name from Dataverse.
        
        Args:
            user_id: Dataverse systemuser ID
            access_token: Access token with Dataverse permissions
            
        Returns:
            Business unit name or None
        """
        try:
            headers = self._get_headers(access_token)
            
            # Get business unit information
            query = f"systemusers({user_id})?$expand=businessunitid($select=name)"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/{query}",
                    headers=headers,
                    timeout=30.0
                )
            
            if response.status_code == 200:
                data = response.json()
                business_unit = data.get("businessunitid")
                if business_unit:
                    return business_unit.get("name")
            
            return None
            
        except Exception as e:
            logger.error("Failed to get business unit", error=str(e), user_id=user_id)
            return None
    
    async def get_systemuser_by_azure_id(self, azure_user_id: str, access_token: str) -> Optional[str]:
        """
        Get systemuser ID by Azure User ID from Dataverse.
        
        Args:
            azure_user_id: Azure AD user ID
            access_token: Access token with Dataverse permissions
            
        Returns:
            Systemuser ID (GUID) if found, None otherwise
        """
        try:
            headers = self._get_headers(access_token)
            
            # Query systemusers by Azure User ID
            # Note: This assumes there's a custom field to store Azure User ID
            # You may need to adjust the field name based on your Dataverse schema
            query = f"systemusers?$filter=azureactivedirectoryobjectid eq '{azure_user_id}'&$select=systemuserid"
            
            print(f"🔵 [DEBUG] Looking up systemuser for Azure ID: {azure_user_id}")
            print(f"🔵 [DEBUG] Query: {query}")
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/{query}",
                    headers=headers,
                    timeout=30.0
                )
            
            print(f"🔵 [DEBUG] Systemuser lookup response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                users = data.get("value", [])
                
                if users:
                    systemuser_id = users[0].get("systemuserid")
                    print(f"🟢 [DEBUG] Found systemuser: {systemuser_id}")
                    return systemuser_id
                else:
                    print(f"🟡 [DEBUG] No systemuser found for Azure ID: {azure_user_id}")
                    return None
            else:
                print(f"🔴 [DEBUG] Systemuser lookup failed: {response.status_code}")
                print(f"🔴 [DEBUG] Response: {response.text[:200]}")
                return None
            
        except Exception as e:
            print(f"🔴 [DEBUG] Exception in systemuser lookup: {str(e)}")
            logger.error("Failed to lookup systemuser", error=str(e), azure_user_id=azure_user_id)
            return None

    async def create_user_session(self, azure_user_id: str, user_name: str, ip_address: str, user_agent: str, access_token: str) -> Optional[str]:
        """
        Create a new user session record in Dataverse.
        
        Args:
            azure_user_id: Azure AD user ID
            user_name: User's display name for session naming
            ip_address: User's IP address
            user_agent: User's browser/device info
            access_token: Access token with Dataverse permissions
            
        Returns:
            Session ID if successful, None otherwise
        """
        print(f"🔵 [DEBUG] Creating user session for Azure ID: {azure_user_id}")
        print(f"🔵 [DEBUG] IP Address: {ip_address}")
        print(f"🔵 [DEBUG] User Agent: {user_agent[:100]}...")
        print(f"🔵 [DEBUG] Access Token Length: {len(access_token) if access_token else 'None'}")
        
        try:
            headers = self._get_headers(access_token)
            print(f"🔵 [DEBUG] Request headers prepared")
            
            # Step 1: Lookup systemuser by Azure User ID
            print(f"🔵 [DEBUG] --- STEP 1: Looking up systemuser ---")
            systemuser_id = await self.get_systemuser_by_azure_id(azure_user_id, access_token)
            
            if not systemuser_id:
                print(f"🟡 [DEBUG] WARNING: No systemuser found for Azure ID: {azure_user_id}")
                print(f"🟡 [DEBUG] Session will be created without systemuser lookup")
            
            # Step 2: Format session name using APP_NAME
            print(f"🔵 [DEBUG] --- STEP 2: Formatting session name ---")
            
            # Create datetime string in format: yyyymmddhh:mm:ss:ms
            now = datetime.now(timezone.utc)
            datetime_str = now.strftime('%Y%m%d%H:%M:%S:') + f"{now.microsecond // 1000:03d}"
            
            # Use APP_NAME from settings instead of user name
            session_name = f"{settings.app_name}-{datetime_str}"
            print(f"🔵 [DEBUG] Session name format: {settings.app_name}-{datetime_str}")
            
            # Step 3: Prepare session data
            print(f"🔵 [DEBUG] --- STEP 3: Preparing session data ---")
            session_data = {
                "hbrd_azureuserid": azure_user_id,
                "hbrd_sessionstart": now.isoformat(),
                "hbrd_ipaddress": ip_address,
                "hbrd_useragent": user_agent,
                "hbrd_name": session_name
            }
            
            # Add systemuser lookup if found
            if systemuser_id:
                session_data["hbrd_user@odata.bind"] = f"/systemusers({systemuser_id})"
                print(f"🟢 [DEBUG] Added systemuser lookup: {systemuser_id}")
            
            print(f"🔵 [DEBUG] Session data prepared:")
            print(f"  - hbrd_azureuserid: {session_data['hbrd_azureuserid']}")
            print(f"  - hbrd_sessionstart: {session_data['hbrd_sessionstart']}")
            print(f"  - hbrd_name: {session_data['hbrd_name']}")
            if systemuser_id:
                print(f"  - hbrd_user: {systemuser_id} (lookup)")
            
            # Step 4: Create session record
            print(f"🔵 [DEBUG] --- STEP 4: Creating session record ---")
            api_url = f"{self.base_url}/hbrd_usersessions"
            print(f"🔵 [DEBUG] Making POST request to: {api_url}")
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    api_url,
                    headers=headers,
                    json=session_data,
                    timeout=30.0
                )
            
            print(f"🔵 [DEBUG] Dataverse API Response Status: {response.status_code}")
            print(f"🔵 [DEBUG] Response Headers: {dict(response.headers)}")
            
            if response.status_code == 201:
                created_session = response.json()
                print(f"🟢 [DEBUG] Session created successfully!")
                print(f"🟢 [DEBUG] Response body: {created_session}")
                session_id = created_session.get("hbrd_usersessionid")
                print(f"🟢 [DEBUG] Session ID extracted: {session_id}")
                
                logger.info("Created user session in Dataverse", 
                          session_id=session_id, 
                          azure_user_id=azure_user_id)
                return session_id
            else:
                print(f"🔴 [DEBUG] Failed to create session - Status: {response.status_code}")
                print(f"🔴 [DEBUG] Error response body: {response.text}")
                logger.warning("Failed to create user session", 
                             status_code=response.status_code,
                             response=response.text[:200])
                return None
            
        except Exception as e:
            print(f"🔴 [DEBUG] Exception in create_user_session: {str(e)}")
            print(f"🔴 [DEBUG] Exception type: {type(e).__name__}")
            logger.error("Failed to create user session in Dataverse", 
                        error=str(e), 
                        azure_user_id=azure_user_id)
            return None
    
    async def create_or_update_user_metadata(self, azure_user_id: str, email: str, display_name: str, access_token: str) -> bool:
        """
        Create or update user app metadata in Dataverse.
        
        Args:
            azure_user_id: Azure AD user ID
            email: User's email address
            display_name: User's display name
            access_token: Access token with Dataverse permissions
            
        Returns:
            True if successful, False otherwise
        """
        print(f"🔵 [DEBUG] Creating/updating user metadata for Azure ID: {azure_user_id}")
        print(f"🔵 [DEBUG] Email: {email}")
        print(f"🔵 [DEBUG] Display Name: {display_name}")
        
        try:
            headers = self._get_headers(access_token)
            print(f"🔵 [DEBUG] Headers prepared for metadata operation")
            
            # First, check if user metadata already exists
            query = f"hbrd_userappmetadatas?$filter=hbrd_azureuserid eq '{azure_user_id}'"
            query_url = f"{self.base_url}/{query}"
            print(f"🔵 [DEBUG] Checking existing user with query: {query_url}")
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    query_url,
                    headers=headers,
                    timeout=30.0
                )
                
                print(f"🔵 [DEBUG] Query response status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    existing_users = data.get("value", [])
                    print(f"🔵 [DEBUG] Found {len(existing_users)} existing user records")
                    
                    current_time = datetime.now(timezone.utc).isoformat()
                    
                    if existing_users:
                        # Update existing user
                        user_metadata_id = existing_users[0]["hbrd_userappmetadataid"]
                        existing_login_count = existing_users[0].get("hbrd_logincount", 0)
                        
                        print(f"🔵 [DEBUG] Updating existing user ID: {user_metadata_id}")
                        print(f"🔵 [DEBUG] Current login count: {existing_login_count}")
                        
                        update_data = {
                            "hbrd_email": email,
                            "hbrd_name": display_name,
                            "hbrd_lastlogin": current_time,
                            "hbrd_logincount": existing_login_count + 1
                        }
                        
                        print(f"🔵 [DEBUG] Update data: {update_data}")
                        
                        update_url = f"{self.base_url}/hbrd_userappmetadatas({user_metadata_id})"
                        print(f"🔵 [DEBUG] Making PATCH request to: {update_url}")
                        
                        response = await client.patch(
                            update_url,
                            headers=headers,
                            json=update_data,
                            timeout=30.0
                        )
                        
                        print(f"🔵 [DEBUG] Update response status: {response.status_code}")
                        
                        success = response.status_code == 204
                        if success:
                            print(f"🟢 [DEBUG] User metadata updated successfully!")
                            print(f"🟢 [DEBUG] New login count: {existing_login_count + 1}")
                            logger.info("Updated user metadata in Dataverse", 
                                      azure_user_id=azure_user_id,
                                      login_count=existing_login_count + 1)
                        else:
                            print(f"🔴 [DEBUG] Update failed: {response.text}")
                    else:
                        # Create new user metadata
                        print(f"🔵 [DEBUG] Creating new user metadata record")
                        
                        create_data = {
                            "hbrd_azureuserid": azure_user_id,
                            "hbrd_email": email,
                            "hbrd_name": display_name,
                            "hbrd_lastlogin": current_time,
                            "hbrd_logincount": 1
                        }
                        
                        print(f"🔵 [DEBUG] Create data: {create_data}")
                        
                        create_url = f"{self.base_url}/hbrd_userappmetadatas"
                        print(f"🔵 [DEBUG] Making POST request to: {create_url}")
                        
                        response = await client.post(
                            create_url,
                            headers=headers,
                            json=create_data,
                            timeout=30.0
                        )
                        
                        print(f"🔵 [DEBUG] Create response status: {response.status_code}")
                        
                        success = response.status_code == 201
                        if success:
                            created_user = response.json()
                            print(f"🟢 [DEBUG] User metadata created successfully!")
                            print(f"🟢 [DEBUG] Created record: {created_user}")
                            logger.info("Created user metadata in Dataverse", 
                                      azure_user_id=azure_user_id)
                        else:
                            print(f"🔴 [DEBUG] Create failed: {response.text}")
                    
                    if not success:
                        print(f"🔴 [DEBUG] Overall operation failed")
                        logger.warning("Failed to create/update user metadata", 
                                     status_code=response.status_code,
                                     response=response.text[:200])
                    
                    return success
                else:
                    print(f"🔴 [DEBUG] Query failed with status: {response.status_code}")
                    print(f"🔴 [DEBUG] Query error response: {response.text}")
                    logger.warning("Failed to query existing user metadata", 
                                 status_code=response.status_code)
                    return False
            
        except Exception as e:
            print(f"🔴 [DEBUG] Exception in create_or_update_user_metadata: {str(e)}")
            print(f"🔴 [DEBUG] Exception type: {type(e).__name__}")
            logger.error("Failed to create/update user metadata in Dataverse", 
                        error=str(e), 
                        azure_user_id=azure_user_id)
            return False

    def _format_user_data(self, dataverse_user: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format Dataverse user data into our application's user format.
        
        Args:
            dataverse_user: Raw user data from Dataverse API
            
        Returns:
            Formatted user data
        """
        return {
            "id": dataverse_user.get("systemuserid"),
            "azure_user_id": dataverse_user.get("azureactivedirectoryobjectid"),
            "email": dataverse_user.get("internalemailaddress"),
            "name": dataverse_user.get("fullname"),
            "given_name": dataverse_user.get("firstname"),
            "family_name": dataverse_user.get("lastname"),
            "job_title": dataverse_user.get("title"),
            "department": None,  # Will be populated by business unit lookup
            "is_active": not dataverse_user.get("isdisabled", False),
            "created_on": dataverse_user.get("createdon"),
            "modified_on": dataverse_user.get("modifiedon"),
            "source": "dataverse"
        }


# Global Dataverse service instance
_dataverse_service: Optional[DataverseService] = None


def get_dataverse_service(environment_url: str) -> DataverseService:
    """
    Get or create Dataverse service instance.
    
    Args:
        environment_url: Dataverse environment URL
        
    Returns:
        DataverseService instance
    """
    global _dataverse_service
    
    if _dataverse_service is None:
        _dataverse_service = DataverseService(environment_url)
        logger.info("Dataverse service initialized", environment_url=environment_url)
    
    return _dataverse_service
