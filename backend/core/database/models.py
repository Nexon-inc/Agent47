from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float, ForeignKey, JSON, Enum, Table, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Dict, Any
import enum

Base = declarative_base()

# Enums
class UserTier(enum.Enum):
    FREE = "free"
    STARTER = "starter"
    PRO = "pro"

class BillingTier(enum.Enum):
    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    ENTERPRISE = "enterprise"

class TaskStatus(enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskPriority(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class AgentStatus(enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    ERROR = "error"

class EventType(enum.Enum):
    TASK_CREATED = "task_created"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    AGENT_STATUS_CHANGED = "agent_status_changed"
    USER_ACTION = "user_action"
    SYSTEM_EVENT = "system_event"
    INTEGRATION_EVENT = "integration_event"

class TokenStatus(enum.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    PENDING = "pending"

class AuditAction(enum.Enum):
    ACCESS = "access"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    REVOKE = "revoke"

class AuditSeverity(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class IntegrationAuditAction(enum.Enum):
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    ACCESS = "access"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    SYNC = "sync"
    WEBHOOK = "webhook"

class IntegrationAuditSeverity(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class TeamInviteStatus(enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    EXPIRED = "expired"

class MessageStatus(enum.Enum):
    UNREAD = "unread"
    READ = "read"
    ARCHIVED = "archived"
    DELETED = "deleted"

class MessageType(enum.Enum):
    TASK_COMPLETION = "task_completion"
    AGENT_STATUS = "agent_status"
    SYSTEM_UPDATE = "system_update"
    TEAM_INVITE = "team_invite"
    BILLING_NOTIFICATION = "billing_notification"

class SubscriptionStatus(enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    INACTIVE = "inactive"
    CANCELLED = "cancelled"
    PAST_DUE = "past_due"
    TRIALING = "trialing"
    EXPIRED = "expired"

class PaymentStatus(enum.Enum):
    PENDING = "pending"
    SUCCESSFUL = "successful"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"

# Models
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    # Username is no longer unique as per user request
    username = Column(String(100), unique=False, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    tier = Column(Enum(UserTier), nullable=True)  # Changed to nullable
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    # Feature flags
    intercommunication_enabled = Column(Boolean, default=False)
    automation_enabled = Column(Boolean, default=False)
    # Onboarding fields
    onboarding_data = Column(JSON)
    onboarding_completed = Column(Boolean, default=False)
    onboarding_completed_at = Column(DateTime(timezone=True))
    website_url = Column(String(500))  # User's website URL for automation
    last_login = Column(DateTime(timezone=True))
    preferences = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    # Use fully-qualified target to avoid ambiguous class name resolution when other
    # modules (agents) define their own Task classes that register with the same
    # declarative base/name. This ensures SQLAlchemy resolves the correct mapper.
    tasks = relationship("Task", back_populates="user")
    platforms = relationship("UserPlatformToken", back_populates="user")
    verification_tokens = relationship("EmailVerificationToken", back_populates="user")
    subscriptions = relationship("Subscription", back_populates="user")
    # NOTE: Agent-specific models (e.g. Clara's SupportTicket) should define
    # their own relationships with backrefs to avoid core model coupling.

class EmailVerificationToken(Base):
    __tablename__ = "email_verification_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="verification_tokens")

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING)
    priority = Column(Enum(TaskPriority), default=TaskPriority.MEDIUM)
    input_data = Column(JSON)
    output_data = Column(JSON)
    task_metadata = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    estimated_duration = Column(Integer)  # in seconds
    actual_duration = Column(Integer)  # in seconds
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    tags = Column(JSON)
    
    # Relationships
    # Qualify the Task target in other relationships as well to prevent SQLAlchemy
    # from becoming ambiguous when multiple classes named 'Task' exist.
    user = relationship("User", back_populates="tasks")
    agent = relationship("Agent", back_populates="tasks")
    events = relationship("Event", back_populates="task")

class Agent(Base):
    __tablename__ = "agents"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    status = Column(Enum(AgentStatus), default=AgentStatus.ACTIVE)
    capabilities = Column(JSON)
    configuration = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    # Reference the core Task model explicitly by module path to avoid collisions
    # with agent-specific Task classes.
    tasks = relationship("Task", back_populates="agent")

class Event(Base):
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    event_type = Column(Enum(EventType), nullable=False)
    description = Column(Text)
    data = Column(JSON)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    # Explicitly point to the core Task model to ensure correct mapper lookup.
    task = relationship("Task", back_populates="events")

class BillingRecord(Base):
    __tablename__ = "billing_records"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="USD")
    description = Column(Text)
    transaction_id = Column(String(255), unique=True)
    payment_method = Column(String(100))
    status = Column(String(50), default="pending")
    billing_cycle = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True))
    billing_metadata = Column(JSON)
    
    # Relationships
    user = relationship("User")

class Community(Base):
    __tablename__ = "communities"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


# Team model (represents an organizational team separate from communities)
class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"))
    settings = Column(JSON, default={})
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    # Explicitly reference the core TeamMember ORM class to avoid conflicts with
    # non-core or agent-specific classes named 'TeamMember'.
    members = relationship("TeamMember", back_populates="team")


class CommunityMember(Base):
    __tablename__ = "community_members"

    id = Column(Integer, primary_key=True, index=True)
    community_id = Column(Integer, ForeignKey("communities.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String(50))
    permissions = Column(JSON, default={})
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String(50), default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    community = relationship("Community")
    user = relationship("User")

class TeamMember(Base):
    __tablename__ = "team_members"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    role = Column(String(50))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User")
    team = relationship("Team", back_populates="members")

class UserPlatformToken(Base):
    __tablename__ = "user_platform_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    platform_name = Column(String(100), nullable=False)
    access_token_encrypted = Column(Text)
    access_token_salt = Column(String(255))
    refresh_token_encrypted = Column(Text)
    refresh_token_salt = Column(String(255))
    token_expires_at = Column(DateTime(timezone=True))
    status = Column(Enum(TokenStatus), default=TokenStatus.ACTIVE)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="platforms")

class UserSelectedAgent(Base):
    __tablename__ = "user_selected_agents"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    # agent_key maps to code-name of agent e.g., aria|clara|eric|jackie|shakes|joe|purity
    agent_key = Column(String(50), nullable=False)
    status = Column(String(20), default="active")  # active|paused|inactive
    locked = Column(Boolean, default=False)
    automation_enabled = Column(Boolean, default=False)
    # Custom configuration/tweaks for the agent (JSON field)
    configuration = Column(JSON, default={})  # Stores custom_instructions, preferences, etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Index to enforce one row per user-agent pair
    __table_args__ = (
        Index("ix_user_selected_agents_user_agent", "user_id", "agent_key", unique=True),
    )

class PlatformAuditLog(Base):
    __tablename__ = "platform_audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    platform_name = Column(String(100), nullable=False)
    action = Column(Enum(AuditAction), nullable=False, index=True)
    severity = Column(Enum(AuditSeverity), default=AuditSeverity.LOW, index=True)
    request_id = Column(String(255), index=True)
    agent_name = Column(String(100))
    ip_address = Column(String(45))  # IPv4 or IPv6
    user_agent = Column(Text)
    
    # Action details
    description = Column(Text, nullable=False)
    audit_metadata = Column(JSON, default={})
    scopes_used = Column(JSON, default=[])
    
    # Result details
    success = Column(String(10), nullable=False)
    error_message = Column(Text)
    response_code = Column(Integer)
    
    # Timing
    duration_ms = Column(Integer)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    user = relationship("User")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "platform_name": self.platform_name,
            "action": self.action.value,
            "severity": self.severity.value,
            "request_id": self.request_id,
            "agent_name": self.agent_name,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "description": self.description,
            "audit_metadata": self.audit_metadata,
            "scopes_used": self.scopes_used,
            "success": self.success,
            "error_message": self.error_message,
            "response_code": self.response_code,
            "duration_ms": self.duration_ms,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }

class IntegrationAuditLog(Base):
    __tablename__ = "integration_audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    integration_name = Column(String(100), nullable=False)
    action = Column(Enum(IntegrationAuditAction), nullable=False, index=True)
    severity = Column(Enum(IntegrationAuditSeverity), default=IntegrationAuditSeverity.LOW, index=True)
    request_id = Column(String(255), index=True)
    agent_name = Column(String(100))
    ip_address = Column(String(45))
    user_agent = Column(Text)
    
    # Action details
    description = Column(Text, nullable=False)
    audit_metadata = Column(JSON, default={})
    scopes_used = Column(JSON, default=[])
    
    # Result details
    success = Column(String(10), nullable=False)
    error_message = Column(Text)
    response_code = Column(Integer)
    
    # Timing
    duration_ms = Column(Integer)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    user = relationship("User")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "integration_name": self.integration_name,
            "action": self.action.value,
            "severity": self.severity.value,
            "request_id": self.request_id,
            "agent_name": self.agent_name,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "description": self.description,
            "audit_metadata": self.audit_metadata,
            "scopes_used": self.scopes_used,
            "success": self.success,
            "error_message": self.error_message,
            "response_code": self.response_code,
            "duration_ms": self.duration_ms,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }


# Legacy Billing Models removed (moved to core/billing/models.py)

# Additional User Management Models
class UserProfile(Base):
    __tablename__ = "user_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    bio = Column(Text)
    avatar_url = Column(String(500))
    phone = Column(String(20))
    country = Column(String(100))
    timezone = Column(String(50))
    language = Column(String(10), default="en")
    preferences = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User")

class UserActivity(Base):
    __tablename__ = "user_activities"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    activity_type = Column(String(50), nullable=False)
    description = Column(Text)
    activity_metadata = Column(JSON)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User")

class UserError(Base):
    __tablename__ = "user_errors"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    error_type = Column(String(100), nullable=False)
    error_message = Column(Text)
    stack_trace = Column(Text)
    request_data = Column(JSON)
    resolved = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("User")

class UserRole(enum.Enum):
    USER = "user"
    ADMIN = "admin"
    MODERATOR = "moderator"
    SUPPORT = "support"

class CommunityType(enum.Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    INVITE_ONLY = "invite_only"

# Team Management Models
class TeamInvite(Base):
    __tablename__ = "team_invites"
    
    id = Column(Integer, primary_key=True, index=True)
    inviter_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    invitee_email = Column(String(255), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    status = Column(Enum(TeamInviteStatus), default=TeamInviteStatus.PENDING)
    expires_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    accepted_at = Column(DateTime(timezone=True))
    
    # Relationships
    inviter = relationship("User", foreign_keys=[inviter_id])
    team = relationship("Team")

# Inbox Models
class InboxMessage(Base):
    __tablename__ = "inbox_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message_type = Column(Enum(MessageType), nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    status = Column(Enum(MessageStatus), default=MessageStatus.UNREAD)
    message_metadata = Column(JSON)  # For storing additional data like task_id, agent_id, etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    read_at = Column(DateTime(timezone=True))
    archived_at = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("User")

# Analytics Models
class UserAnalytics(Base):
    __tablename__ = "user_analytics"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(DateTime(timezone=True), nullable=False)
    tasks_completed = Column(Integer, default=0)
    tasks_failed = Column(Integer, default=0)
    total_duration = Column(Integer, default=0)  # in seconds
    agents_used = Column(JSON)  # List of agent keys used
    integrations_used = Column(JSON)  # List of integration names used
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User")
    
    # Index for efficient querying
    __table_args__ = (
        Index('idx_user_analytics_user_date', 'user_id', 'date'),
    )

# Team Agent Request Models
class TeamAgentRequest(Base):
    __tablename__ = "team_agent_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    team_member_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    agent_key = Column(String(50), nullable=False)
    request_type = Column(String(50), nullable=False)  # task, query, automation, etc.
    request_data = Column(JSON, default={})
    status = Column(String(20), default="pending")  # pending, processing, completed, failed
    output_data = Column(JSON, default={})
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    
    # Relationships
    team = relationship("Team")
    team_member = relationship("User", foreign_keys=[team_member_id])
    
    # Indexes
    __table_args__ = (
        Index('idx_team_agent_requests_team_id', 'team_id'),
        Index('idx_team_agent_requests_team_member_id', 'team_member_id'),
        Index('idx_team_agent_requests_agent_key', 'agent_key'),
        Index('idx_team_agent_requests_status', 'status'),
        Index('idx_team_agent_requests_created_at', 'created_at'),
    )

class TeamChatMessage(Base):
    __tablename__ = "team_chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    agent_key = Column(String(50))  # Nullable - can be user or agent message
    message_type = Column(String(20), default="text")  # text, voice, file, agent_output
    content = Column(Text, nullable=False)
    audio_url = Column(Text)
    file_url = Column(Text)
    file_name = Column(String(255))
    file_size = Column(Integer)
    message_metadata = Column(JSON, default={})  # Renamed from 'metadata' to avoid SQLAlchemy reserved name conflict
    reply_to_message_id = Column(Integer, ForeignKey("team_chat_messages.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True))
    
    # Relationships
    team = relationship("Team")
    user = relationship("User")
    reply_to = relationship("TeamChatMessage", remote_side=[id])
    
    # Indexes
    __table_args__ = (
        Index('idx_team_chat_messages_team_id', 'team_id'),
        Index('idx_team_chat_messages_user_id', 'user_id'),
        Index('idx_team_chat_messages_agent_key', 'agent_key'),
        Index('idx_team_chat_messages_created_at', 'created_at'),
        Index('idx_team_chat_messages_reply_to', 'reply_to_message_id'),
    )

class GeoTargetedCampaign(Base):
    __tablename__ = "geo_targeted_campaigns"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    campaign_name = Column(String(255), nullable=False)
    target_locations = Column(Text, nullable=False)  # JSON string of locations
    campaign_type = Column(String(50), default="outreach")
    agent_key = Column(String(50))
    total_businesses = Column(Integer, default=0)
    status = Column(String(20), default="active")  # active, completed, paused
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("User")
    
    # Indexes
    __table_args__ = (
        Index('idx_geo_targeted_campaigns_user_id', 'user_id'),
        Index('idx_geo_targeted_campaigns_status', 'status'),
        Index('idx_geo_targeted_campaigns_created_at', 'created_at'),
    )
