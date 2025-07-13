"""
Authentication utilities for token handling and PKCE implementation.
Following Azure and security best practices.
"""

import secrets
import base64
import hashlib
import jwt
from typing import Dict, Optional, Tuple, Any
from datetime import datetime, timedelta, timezone
from jose import JWTError
from passlib.context import CryptContext
from config import settings
import structlog

logger = structlog.get_logger()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class PKCEGenerator:
    """PKCE (Proof Key for Code Exchange) implementation for secure OAuth2 flows."""
    
    @staticmethod
    def generate_code_verifier() -> str:
        """Generate a cryptographically random code verifier."""
        # Generate 32 random bytes and base64url encode
        code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8')
        # Remove padding
        return code_verifier.rstrip('=')
    
    @staticmethod
    def generate_code_challenge(code_verifier: str) -> str:
        """Generate code challenge from verifier using SHA256."""
        # SHA256 hash the code verifier
        digest = hashlib.sha256(code_verifier.encode('utf-8')).digest()
        # Base64url encode the hash
        code_challenge = base64.urlsafe_b64encode(digest).decode('utf-8')
        # Remove padding
        return code_challenge.rstrip('=')
    
    @classmethod
    def generate_pkce_pair(cls) -> Tuple[str, str]:
        """Generate PKCE verifier and challenge pair."""
        verifier = cls.generate_code_verifier()
        challenge = cls.generate_code_challenge(verifier)
        return verifier, challenge


class TokenManager:
    """Secure token management for JWT tokens."""
    
    def __init__(self):
        self.secret_key = settings.secret_key
        self.algorithm = "HS256"
        self.access_token_expire_minutes = settings.access_token_expire_minutes
        self.refresh_token_expire_days = settings.refresh_token_expire_days
    
    def create_access_token(self, data: Dict[str, Any]) -> str:
        """Create a new access token."""
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "access"
        })
        
        try:
            encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
            logger.info("Access token created", user_id=data.get("sub"))
            return encoded_jwt
        except Exception as e:
            logger.error("Failed to create access token", error=str(e))
            raise
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Create a new refresh token."""
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(days=self.refresh_token_expire_days)
        to_encode.update({
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "refresh"
        })
        
        try:
            encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
            logger.info("Refresh token created", user_id=data.get("sub"))
            return encoded_jwt
        except Exception as e:
            logger.error("Failed to create refresh token", error=str(e))
            raise
    
    def verify_token(self, token: str, token_type: str = "access", validate_exp: bool = True) -> Optional[Dict[str, Any]]:
        """Verify and decode a JWT token."""
        try:
            options = {"verify_exp": validate_exp}
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm], options=options)
            
            # Verify token type
            if payload.get("type") != token_type:
                logger.warning("Invalid token type", expected=token_type, actual=payload.get("type"))
                return None
            
            # Check expiration
            if datetime.now(timezone.utc) > datetime.fromtimestamp(payload.get("exp", 0), tz=timezone.utc):
                logger.warning("Token expired", token_type=token_type)
                return None
            
            return payload
        except JWTError as e:
            logger.warning("JWT verification failed", error=str(e), token_type=token_type)
            return None
        except Exception as e:
            logger.error("Unexpected error during token verification", error=str(e))
            return None
    
    def refresh_access_token(self, refresh_token: str) -> Optional[Tuple[str, str]]:
        """Generate new access and refresh tokens from valid refresh token."""
        payload = self.verify_token(refresh_token, "refresh")
        if not payload:
            return None
        
        # Create new tokens with same user data
        user_data = {k: v for k, v in payload.items() 
                    if k not in ["exp", "iat", "type"]}
        
        new_access_token = self.create_access_token(user_data)
        new_refresh_token = self.create_refresh_token(user_data)
        
        return new_access_token, new_refresh_token


class StateManager:
    """Manage OAuth2 state parameter for CSRF protection."""
    
    @staticmethod
    def generate_state() -> str:
        """Generate a cryptographically secure state parameter."""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def verify_state(stored_state: str, received_state: str) -> bool:
        """Verify the state parameter to prevent CSRF attacks."""
        return secrets.compare_digest(stored_state, received_state)


def hash_token(token: str) -> str:
    """Hash a token for secure storage."""
    return pwd_context.hash(token)


def verify_token_hash(plain_token: str, hashed_token: str) -> bool:
    """Verify a token against its hash."""
    return pwd_context.verify(plain_token, hashed_token)


def generate_session_id() -> str:
    """Generate a secure session identifier."""
    return secrets.token_urlsafe(32)


# Global instances
pkce_generator = PKCEGenerator()
token_manager = TokenManager()
state_manager = StateManager()
