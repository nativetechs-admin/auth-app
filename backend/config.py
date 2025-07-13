"""
Configuration module for the authentication application.
Follows Azure best practices for secure configuration management.
"""

from typing import List, Optional, Literal, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, Field, ConfigDict
import os


class Settings(BaseSettings):
    """Application settings with validation and type hints."""
    
    model_config = SettingsConfigDict(
        env_file=".env", 
        case_sensitive=False,
        extra="ignore"  # Allow extra fields in .env file
    )
    
    # Azure AD Configuration
    azure_client_id: str = "dummy-client-id-for-dev"
    azure_client_secret: str = "dummy-secret-for-dev"
    azure_tenant_id: str = "dummy-tenant-id-for-dev"
    azure_redirect_uri: str = "http://localhost:8000/auth/callback"
    
    # Application Configuration
    app_name: str = "SSO-APP"  # Default fallback
    secret_key: str = "dev-secret-key-for-testing-only"
    environment: str = "development"
    debug: bool = True
    
    # Database Configuration
    database_url: str = "sqlite:///./sso_app.db"
    
    # Microsoft Dataverse Configuration (Required)
    dataverse_environment_url: str = "https://dev.crm.dynamics.com"  # Default placeholder
    use_dataverse_for_users: bool = True  # Always use Dataverse
    dataverse_scope: str = "https://yourorg.crm.dynamics.com/user_impersonation"
    
    @field_validator('database_url')
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Validate database URL and warn about SQLite in production."""
        if v.startswith("sqlite:") and os.getenv("ENVIRONMENT", "development") == "production":
            import warnings
            warnings.warn(
                "SQLite is not recommended for production Azure deployments. "
                "Consider using Azure SQL Database or Azure Database for PostgreSQL.",
                RuntimeWarning
            )
        return v
    
    # CORS Configuration
    allowed_origins: Union[str, List[str]] = "http://localhost:5173,http://localhost:3000"
    
    # Session Configuration
    cookie_secure: bool = False  # Set default to False for local development
    session_cookie_httponly: bool = True
    cookie_samesite: Literal["lax", "strict", "none"] = "none"  # Set default to 'none' for cross-domain communication
    
    # Security Configuration
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    
    # Logging
    log_level: str = "INFO"
    
    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        return v
    
    @property
    def cors_origins(self) -> List[str]:
        """Get CORS origins as a list."""
        if isinstance(self.allowed_origins, str):
            return [i.strip() for i in self.allowed_origins.split(",")]
        return self.allowed_origins
    
    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v):
        if v not in ["development", "staging", "production"]:
            raise ValueError("Environment must be one of: development, staging, production")
        return v
    
    @property
    def session_cookie_secure(self) -> bool:
        """Determine if cookies should be secure based on environment."""
        # In development, allow non-secure cookies for easier testing
        if self.environment == "development" and self.debug:
            return False
        return self.cookie_secure
        
    @property
    def session_cookie_samesite(self) -> Literal["lax", "strict", "none"]:
        """Determine the SameSite setting based on environment."""
        # In development with debug, use 'none' for cross-domain communication
        if self.environment == "development" and self.debug:
            return "none"
        # Otherwise, use the configured value
        return self.cookie_samesite
    
    @property
    def azure_authority(self) -> str:
        """Get Azure AD authority URL."""
        return f"https://login.microsoftonline.com/{self.azure_tenant_id}"
    
    @property
    def azure_scope(self) -> List[str]:
        """Clean scopes for Azure AD authentication (no Dataverse during login)."""
        # Use standard scopes only - cleaner approach
        # Dataverse access will be handled separately when needed
        return ["openid", "profile", "email", "User.Read"]
    
    @property
    def azure_scope_with_dataverse(self) -> List[str]:
        """Scopes including Dataverse (for explicit Dataverse operations)."""
        scopes = ["openid", "profile", "email", "User.Read"]
        
        # Add Dataverse scope if enabled
        if self.use_dataverse_for_users and self.dataverse_environment_url:
            # Extract organization name from URL for scope
            # e.g., https://yourorg.crm.dynamics.com -> yourorg.crm.dynamics.com/user_impersonation
            if "://" in self.dataverse_environment_url:
                domain = self.dataverse_environment_url.split("://")[1].rstrip("/")
                dataverse_scope = f"https://{domain}/user_impersonation"
                scopes.append(dataverse_scope)
            
        return scopes


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Dependency to get settings instance."""
    return settings
