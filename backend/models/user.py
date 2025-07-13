"""
User data models with SQLAlchemy ORM.
Following Azure best practices for data modeling.
"""

from sqlalchemy import Column, String, DateTime, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional
import uuid

Base = declarative_base()


class User(Base):
    """User model for storing authenticated user data."""
    
    __tablename__ = "users"
    
    # Primary key using UUID for security
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Azure AD user information
    azure_user_id = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    given_name = Column(String(255), nullable=True)
    family_name = Column(String(255), nullable=True)
    
    # Profile information
    profile_picture = Column(String(500), nullable=True)
    job_title = Column(String(255), nullable=True)
    department = Column(String(255), nullable=True)
    
    # Authentication metadata
    last_login = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, name={self.name})>"
    
    def to_dict(self) -> dict:
        """Convert user object to dictionary."""
        return {
            "id": str(self.id),
            "azure_user_id": self.azure_user_id,
            "email": self.email,
            "name": self.name,
            "given_name": self.given_name,
            "family_name": self.family_name,
            "profile_picture": self.profile_picture,
            "job_title": self.job_title,
            "department": self.department,
            "last_login": self.last_login.isoformat() if self.last_login is not None else None,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at is not None else None,
        }


class UserSession(Base):
    """User session model for tracking active sessions."""
    
    __tablename__ = "user_sessions"
    
    # Session identifier
    session_id = Column(String(255), primary_key=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Token information (encrypted)
    access_token_hash = Column(Text, nullable=True)
    refresh_token_hash = Column(Text, nullable=True)
    
    # Session metadata
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_accessed = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Client information
    user_agent = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    
    def __repr__(self):
        return f"<UserSession(session_id={self.session_id}, user_id={self.user_id})>"
