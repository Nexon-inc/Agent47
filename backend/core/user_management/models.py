from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float, ForeignKey, JSON, Enum, Table
from backend.core.database.models import Base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum


class UserRole(enum.Enum):
    USER = "user"
    ADMIN = "admin"
    MODERATOR = "moderator"
    TEAM_LEADER = "team_leader"
    TEAM_MEMBER = "team_member"

class ActivityType(enum.Enum):
    LOGIN = "login"
    LOGOUT = "logout"
    AGENT_ACCESS = "agent_access"
    API_CALL = "api_call"
    SUBSCRIPTION_CHANGE = "subscription_change"
    PROFILE_UPDATE = "profile_update"
    TEAM_JOIN = "team_join"
    TEAM_LEAVE = "team_leave"
    COMMUNITY_JOIN = "community_join"
    COMMUNITY_LEAVE = "community_leave"

class ErrorSeverity(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class CommunityType(enum.Enum):
    CREATIVE = "creative"
    BUSINESS = "business"
    DEVELOPER = "developer"
    MARKETING = "marketing"
    SALES = "sales"
    SUPPORT = "support"
    RESEARCH = "research"
    GENERAL = "general"

# Use canonical model definitions from backend.core.database.models to avoid duplicate table
from backend.core.database.models import (
    UserProfile,
    UserActivity,
    UserError,
    Community,
    TeamMember,
)
