from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float, ForeignKey, JSON, Enum, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

from ..database.models import Base

class IntegrationType(enum.Enum):
    MARKETING = "marketing"
    ANALYTICS = "analytics"
    CRM = "crm"
    CONTENT = "content"
    DESIGN = "design"
    PRODUCTIVITY = "productivity"
    FINANCE = "finance"
    RESEARCH = "research"
    AUTOMATION = "automation"

class IntegrationStatus(enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    MAINTENANCE = "maintenance"
    DEPRECATED = "deprecated"

class CredentialStatus(enum.Enum):
    VALID = "valid"
    EXPIRED = "expired"
    INVALID = "invalid"
    REVOKED = "revoked"

class Integration(Base):
    __tablename__ = "integrations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    display_name = Column(String(200), nullable=False)
    integration_type = Column(Enum(IntegrationType, values_callable=lambda obj: [e.value for e in obj]), nullable=False)
    description = Column(Text)
    provider = Column(String(100), nullable=False)
    api_version = Column(String(20))
    base_url = Column(String(500), nullable=False)
    api_documentation_url = Column(String(500))
    pricing_tier = Column(String(50), default="free")
    rate_limits = Column(JSON, default={
        "requests_per_minute": 60,
        "requests_per_hour": 1000,
        "requests_per_day": 10000
    })
    supported_features = Column(JSON, default={
        "api_access": True,
        "webhooks": False,
        "real_time": False,
        "bulk_operations": False
    })
    authentication_methods = Column(JSON, default={
        "oauth2": True,
        "api_key": True,
        "bearer_token": False
    })
    status = Column(Enum(IntegrationStatus, values_callable=lambda obj: [e.value for e in obj]), default=IntegrationStatus.ACTIVE)
    is_available = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    credentials = relationship("IntegrationCredentials", back_populates="integration")
    usage = relationship("IntegrationUsage", back_populates="integration")

class IntegrationCredentials(Base):
    __tablename__ = "integration_credentials"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    integration_id = Column(Integer, ForeignKey("integrations.id"), nullable=False)
    credential_type = Column(String(50), nullable=False)  # oauth2, api_key, bearer_token
    access_token = Column(Text)
    refresh_token = Column(Text)
    api_key = Column(String(500))
    api_secret = Column(String(500))
    bearer_token = Column(Text)
    expires_at = Column(DateTime(timezone=True))
    scopes = Column(JSON, default=[])
    # 'metadata' is reserved in SQLAlchemy Declarative API; use a different attribute name
    extra_metadata = Column('metadata', JSON, default={})
    status = Column(Enum(CredentialStatus), default=CredentialStatus.VALID)
    last_used = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    user = relationship("User")
    integration = relationship("Integration", back_populates="credentials")

class IntegrationUsage(Base):
    __tablename__ = "integration_usage"
    
    id = Column(Integer, primary_key=True, index=True)
    integration_id = Column(Integer, ForeignKey("integrations.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(String(10), nullable=False)  # Format: YYYY-MM-DD
    api_calls_count = Column(Integer, default=0)
    data_processed_mb = Column(Float, default=0.0)
    cost_usd = Column(Float, default=0.0)
    # 'metadata' is reserved in SQLAlchemy Declarative API; use a different attribute name
    extra_metadata = Column('metadata', JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    integration = relationship("Integration", back_populates="usage")
    user = relationship("User")
