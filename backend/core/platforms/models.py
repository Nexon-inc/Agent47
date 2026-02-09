from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float, ForeignKey, JSON, Enum, Table
from ..database.models import Base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum


class PlatformType(enum.Enum):
    SOCIAL_MEDIA = "social_media"
    MESSAGING = "messaging"
    EMAIL = "email"
    VIDEO = "video"
    BLOG = "blog"
    FORUM = "forum"
    ECOMMERCE = "ecommerce"

class PlatformStatus(enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    MAINTENANCE = "maintenance"

class CredentialStatus(enum.Enum):
    valid = "valid"
    expired = "expired"
    invalid = "invalid"
    revoked = "revoked"

class SocialPlatform(Base):
    __tablename__ = "social_platforms"
    __table_args__ = {"extend_existing": True}
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    display_name = Column(String(200), nullable=False)
    platform_type = Column(Enum(PlatformType, values_callable=lambda obj: [e.value for e in obj]), nullable=False)
    description = Column(Text)
    api_version = Column(String(20))
    base_url = Column(String(500), nullable=False)
    api_documentation_url = Column(String(500))
    rate_limits = Column(JSON, default={
        "requests_per_minute": 60,
        "requests_per_hour": 1000,
        "requests_per_day": 10000
    })
    supported_features = Column(JSON, default={
        "posting": True,
        "analytics": True,
        "engagement": True,
        "scheduling": True,
        "automation": True
    })
    authentication_methods = Column(JSON, default={
        "oauth2": True,
        "api_key": False,
        "bearer_token": False
    })
    status = Column(Enum(PlatformStatus, values_callable=lambda obj: [e.value for e in obj]), default=PlatformStatus.ACTIVE)
    is_available = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    credentials = relationship("PlatformCredential", back_populates="platform")
    metrics = relationship("PlatformMetrics", back_populates="platform")

class PlatformCredential(Base):
    __tablename__ = "platform_credentials"
    __table_args__ = {"extend_existing": True}
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    platform_id = Column(Integer, ForeignKey("social_platforms.id"), nullable=False)
    credential_type = Column(String(50), nullable=False)  # oauth2, api_key, bearer_token
    access_token = Column(Text)
    refresh_token = Column(Text)
    api_key = Column(String(500))
    api_secret = Column(String(500))
    bearer_token = Column(Text)
    expires_at = Column(DateTime(timezone=True))
    scopes = Column(JSON, default=[])
    # `metadata` is reserved on Declarative base; store in DB column 'metadata' but expose as `extra_metadata`
    extra_metadata = Column('metadata', JSON, default={})
    status = Column(Enum(CredentialStatus, values_callable=lambda obj: [e.value for e in obj], native_enum=True), default=CredentialStatus.valid)
    last_used = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    user = relationship("User")
    platform = relationship("SocialPlatform", back_populates="credentials")

class PlatformMetrics(Base):
    __tablename__ = "platform_metrics"
    __table_args__ = {"extend_existing": True}
    
    id = Column(Integer, primary_key=True, index=True)
    platform_id = Column(Integer, ForeignKey("social_platforms.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(String(10), nullable=False)  # Format: YYYY-MM-DD
    metric_type = Column(String(50), nullable=False)  # followers, engagement, reach, impressions
    value = Column(Float, nullable=False)
    previous_value = Column(Float)
    change_percentage = Column(Float)
    # `metadata` is reserved on Declarative base; store in DB column 'metadata' but expose as `extra_metadata`
    extra_metadata = Column('metadata', JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    platform = relationship("SocialPlatform", back_populates="metrics")
    user = relationship("User")
