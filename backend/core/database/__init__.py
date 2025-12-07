from .connection import get_database, get_supabase, get_db, SupabaseManager, init_database, close_database
from .models import Base, User, Task, Agent, Event, BillingRecord, Community, TeamMember, Subscription, Payment, BillingPlan, Usage, UserProfile, UserActivity, UserError, UserRole, CommunityType

# Alias for backward compatibility
DatabaseManager = SupabaseManager

# Lazy import to avoid circular dependency
def _get_platform_models():
    """Lazy import of platform models to avoid circular dependency"""
    from ..platforms.models import PlatformCredential, SocialPlatform, PlatformMetrics
    return PlatformCredential, SocialPlatform, PlatformMetrics

# Export platform models via lazy getter
def __getattr__(name):
    if name in ("PlatformCredential", "SocialPlatform", "PlatformMetrics"):
        PlatformCredential, SocialPlatform, PlatformMetrics = _get_platform_models()
        if name == "PlatformCredential":
            return PlatformCredential
        elif name == "SocialPlatform":
            return SocialPlatform
        elif name == "PlatformMetrics":
            return PlatformMetrics
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "get_database",
    "get_supabase",
    "get_db",
    "DatabaseManager", 
    "SupabaseManager",
    "init_database",
    "close_database",
    "Base",
    "User",
    "Task",
    "Agent",
    "Event",
    "PlatformCredential",
    "SocialPlatform", 
    "PlatformMetrics",
    "BillingRecord",
    "Community",
    "TeamMember",
    "Subscription",
    "Payment",
    "BillingPlan",
    "Usage",
    "UserProfile",
    "UserActivity",
    "UserError",
    "UserRole",
    "CommunityType"
]
