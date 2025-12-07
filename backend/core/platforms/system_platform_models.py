"""
System-level platform connection models for Agent47's own platform accounts
These are separate from user platform credentials - these belong to Agent47 itself
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, Enum, Table
from ..database.models import Base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum


class SystemPlatformConnectionStatus(enum.Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    EXPIRED = "expired"
    ERROR = "error"
    PENDING = "pending"


class SystemPlatformCredential(Base):
    """
    System-level platform credentials for Agent47's own accounts
    These are NOT user-specific - they belong to Agent47 as an organization
    """
    __tablename__ = "system_platform_credentials"
    __table_args__ = {"extend_existing": True}
    
    id = Column(Integer, primary_key=True, index=True)
    platform_id = Column(Integer, ForeignKey("social_platforms.id"), nullable=False)
    account_name = Column(String(255), nullable=False)  # e.g., "Agent47 Official", "Agent47 Support"
    account_handle = Column(String(255))  # e.g., "@agent47", "agent47official"
    credential_type = Column(String(50), nullable=False)  # oauth2, api_key, bearer_token
    access_token = Column(Text)  # Encrypted
    refresh_token = Column(Text)  # Encrypted
    api_key = Column(String(500))  # Encrypted
    api_secret = Column(String(500))  # Encrypted
    bearer_token = Column(Text)  # Encrypted
    expires_at = Column(DateTime(timezone=True))
    scopes = Column(JSON, default=[])
    status = Column(Enum(SystemPlatformConnectionStatus), default=SystemPlatformConnectionStatus.CONNECTED)
    meta_data = Column(JSON, default={})  # Platform-specific metadata
    is_active = Column(Boolean, default=True)
    last_used = Column(DateTime(timezone=True))
    last_used_by_agent = Column(String(50))  # Which agent last used this
    created_by = Column(String(255))  # Admin user who created this
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    platform = relationship("SocialPlatform")
    agent_assignments = relationship("AgentPlatformAssignment", back_populates="credential", cascade="all, delete-orphan")
    posts = relationship("SystemPlatformPost", back_populates="credential", cascade="all, delete-orphan")


# Association table for many-to-many relationship between agents and platforms
agent_platform_assignment = Table(
    "agent_platform_assignments",
    Base.metadata,
    Column("id", Integer, primary_key=True),
    Column("credential_id", Integer, ForeignKey("system_platform_credentials.id"), nullable=False),
    Column("agent_name", String(50), nullable=False),  # aria, clara, eric, joe, jackie, shakes, purity
    Column("permissions", JSON, default={
        "can_post": True,
        "can_read": True,
        "can_engage": True,
        "can_analyze": True,
        "can_schedule": True
    }),
    Column("is_active", Boolean, default=True),
    Column("priority", Integer, default=0),  # Higher priority agents get access first
    Column("created_at", DateTime(timezone=True), server_default=func.now()),
    Column("updated_at", DateTime(timezone=True), onupdate=func.now()),
    Column("created_by", String(255)),  # Admin user who created this assignment
    Column("last_used_at", DateTime(timezone=True)),
    Column("usage_count", Integer, default=0),
    Column("meta_data", JSON, default={})
)


class AgentPlatformAssignment(Base):
    """
    Explicit model for agent-platform assignments with additional metadata
    """
    __tablename__ = "agent_platform_assignments"
    __table_args__ = {"extend_existing": True}
    
    id = Column(Integer, primary_key=True, index=True)
    credential_id = Column(Integer, ForeignKey("system_platform_credentials.id"), nullable=False)
    agent_name = Column(String(50), nullable=False, index=True)  # aria, clara, eric, joe, jackie, shakes, purity
    permissions = Column(JSON, default={
        "can_post": True,
        "can_read": True,
        "can_engage": True,
        "can_analyze": True,
        "can_schedule": True,
        "can_moderate": False,
        "can_delete": False
    })
    is_active = Column(Boolean, default=True, index=True)
    priority = Column(Integer, default=0)  # Higher priority agents get access first
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String(255))  # Admin user who created this assignment
    last_used_at = Column(DateTime(timezone=True))
    usage_count = Column(Integer, default=0)
    meta_data = Column(JSON, default={})
    
    credential = relationship("SystemPlatformCredential", back_populates="agent_assignments")


class SystemPlatformPost(Base):
    """
    Tracks posts made by agents on Agent47's platform accounts
    """
    __tablename__ = "system_platform_posts"
    __table_args__ = {"extend_existing": True}
    
    id = Column(Integer, primary_key=True, index=True)
    credential_id = Column(Integer, ForeignKey("system_platform_credentials.id"), nullable=False)
    agent_name = Column(String(50), nullable=False, index=True)
    platform_id = Column(Integer, ForeignKey("social_platforms.id"), nullable=False)
    content = Column(Text, nullable=False)
    media_urls = Column(JSON, default=[])  # List of media URLs
    post_type = Column(String(50), default="post")  # post, story, reel, video, etc.
    scheduled_time = Column(DateTime(timezone=True))
    posted_at = Column(DateTime(timezone=True))
    platform_post_id = Column(String(255))  # ID returned by platform API
    platform_post_url = Column(String(500))  # URL to the post on the platform
    status = Column(String(50), default="pending")  # pending, posted, failed, scheduled
    error_message = Column(Text)
    engagement_metrics = Column(JSON, default={})  # likes, shares, comments, etc.
    meta_data = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    credential = relationship("SystemPlatformCredential", back_populates="posts")
    platform = relationship("SocialPlatform")


class SystemPlatformActivity(Base):
    """
    Tracks all activities performed by agents on Agent47's platform accounts
    """
    __tablename__ = "system_platform_activities"
    __table_args__ = {"extend_existing": True}
    
    id = Column(Integer, primary_key=True, index=True)
    credential_id = Column(Integer, ForeignKey("system_platform_credentials.id"), nullable=False)
    agent_name = Column(String(50), nullable=False, index=True)
    platform_id = Column(Integer, ForeignKey("social_platforms.id"), nullable=False)
    activity_type = Column(String(50), nullable=False)  # post, comment, like, share, follow, analyze
    activity_data = Column(JSON, default={})
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    meta_data = Column(JSON, default={})
    
    credential = relationship("SystemPlatformCredential")
    platform = relationship("SocialPlatform")

