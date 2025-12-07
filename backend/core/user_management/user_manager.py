import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from sqlalchemy import select, and_, or_, func
from ..database.models import (
    User, UserProfile, UserActivity, UserError, UserTier, UserRole,
    Community, TeamMember, CommunityType
)
from ..database.connection import get_supabase
from ..utils.validation import ValidationUtils, Agent47Validator
from ..authentication.auth_manager import AuthManager
from ..billing import get_billing

logger = logging.getLogger(__name__)

class UserManager:
    """Manages user operations and user lifecycle for Agent47."""
    
    def __init__(self):
        self.auth_manager = AuthManager()
        self._initialized = False
    
    async def initialize(self):
        """Initialize the user manager."""
        if self._initialized:
            return
        
        # Initialize dependencies
        await get_billing()
        
        self._initialized = True
        logger.info("User manager initialized successfully")
    
    async def create_user(self, email: str, username: str, password: str, full_name: str, tier: UserTier = None) -> Dict[str, Any]:
        """Create a new user account."""
        # Validate input data
        if not DataValidator.validate_email(email):
            raise ValueError("Invalid email address")
        
        username_validation = Agent47Validator.validate_username(username)
        if not username_validation["is_valid"]:
            raise ValueError(f"Invalid username: {', '.join(username_validation['errors'])}")
        
        password_validation = DataValidator.validate_password_strength(password)
        if not password_validation["is_valid"]:
            raise ValueError(f"Invalid password: {', '.join(password_validation['errors'])}")
        
        db = await get_supabase()
        
        try:
            async with db.get_session() as session:
                    # Check if email or username already exists
                existing_user = await session.execute(
                    select(User).where(
                        or_(User.email == email, User.username == username)
                    )
                )
                if existing_user.scalar_one_or_none():
                    raise ValueError("Email or username already exists")
                
                # Create user
                user = User(
                    email=email,
                    username=username,
                    hashed_password=hashed_password,
                    full_name=full_name,
                    tier=tier,
                    is_active=True,
                    is_verified=False
                )
                
                session.add(user)
                await session.commit()
                
                # Create user profile
                profile = UserProfile(
                    user_id=user.id,
                    bio="",
                    avatar_url="",
                    company="",
                    job_title="",
                    location="",
                    website="",
                    social_links={},
                    preferences={
                        "theme": "light",
                        "notifications": True,
                        "language": "en",
                        "timezone": "UTC"
                    },
                    notification_settings={
                        "email_notifications": True,
                        "push_notifications": True,
                        "marketing_emails": False,
                        "weekly_reports": True
                    },
                    timezone="UTC",
                    language="en"
                )
                
                session.add(profile)
                await session.commit()
                
                # Log user creation activity
                await self.log_user_activity(
                    user_id=user.id,
                    activity_type="account_creation",
                    description="User account created successfully"
                )
                
                logger.info(f"Created user account: {email}")
                
                return {
                    "id": user.id,
                    "email": user.email,
                    "username": user.username,
                    "full_name": user.full_name,
                    "tier": user.tier.value,
                    "is_active": user.is_active,
                    "created_at": user.created_at.isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to create user {email}: {e}")
            raise
    
    async def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user details by ID."""
        db = await get_supabase()

        async with db.get_session() as session:
            result = await session.execute(
                select(User, UserProfile).join(
                    UserProfile, User.id == UserProfile.user_id
                ).where(User.id == user_id)
            )
            
            user_data = result.first()
            if user_data:
                user, profile = user_data
                return {
                    "id": user.id,
                    "email": user.email,
                    "username": user.username,
                    "full_name": user.full_name,
                    "tier": user.tier.value,
                    "is_active": user.is_active,
                    "is_verified": user.is_verified,
                    "created_at": user.created_at.isoformat(),
                    "updated_at": user.updated_at.isoformat() if user.updated_at else None,
                    "profile": {
                        "bio": profile.bio,
                        "avatar_url": profile.avatar_url,
                        "company": profile.company,
                        "job_title": profile.job_title,
                        "location": profile.location,
                        "website": profile.website,
                        "social_links": profile.social_links,
                        "preferences": profile.preferences,
                        "notification_settings": profile.notification_settings,
                        "timezone": profile.timezone,
                        "language": profile.language
                    }
                }
            return None
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user details by email."""
        db = await get_supabase()

        async with db.get_session() as session:
            result = await session.execute(
                select(User, UserProfile).join(
                    UserProfile, User.id == UserProfile.user_id
                ).where(User.email == email)
            )
            
            user_data = result.first()
            if user_data:
                user, profile = user_data
                return {
                    "id": user.id,
                    "email": user.email,
                    "username": user.username,
                    "full_name": user.full_name,
                    "tier": user.tier.value,
                    "is_active": user.is_active,
                    "is_verified": user.is_verified,
                    "created_at": user.created_at.isoformat(),
                    "updated_at": user.updated_at.isoformat() if user.updated_at else None,
                    "profile": {
                        "bio": profile.bio,
                        "avatar_url": profile.avatar_url,
                        "company": profile.company,
                        "job_title": profile.job_title,
                        "location": profile.location,
                        "website": profile.website,
                        "social_links": profile.social_links,
                        "preferences": profile.preferences,
                        "notification_settings": profile.notification_settings,
                        "timezone": profile.timezone,
                        "language": profile.language
                    }
                }
            return None
    
    async def update_user_profile(self, user_id: int, profile_data: Dict[str, Any]) -> bool:
        """Update user profile information."""
        db = await get_supabase()
        
        try:
            async with db.get_session() as session:
                profile = await session.execute(
                    select(UserProfile).where(UserProfile.user_id == user_id)
                )
                profile = profile.scalar_one_or_none()
                
                if not profile:
                    raise ValueError("User profile not found")
                
                # Update allowed fields
                allowed_fields = [
                    "bio", "avatar_url", "company", "job_title", "location", 
                    "website", "social_links", "preferences", "notification_settings",
                    "timezone", "language"
                ]
                
                for field in allowed_fields:
                    if field in profile_data:
                        setattr(profile, field, profile_data[field])
                
                profile.updated_at = datetime.utcnow()
                session.add(profile)
                await session.commit()
                
                # Log profile update activity
                await self.log_user_activity(
                    user_id=user_id,
                    activity_type="profile_update",
                    description="User profile updated"
                )
                
                logger.info(f"Updated profile for user {user_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to update profile for user {user_id}: {e}")
            return False
    
    async def update_user_tier(self, user_id: int, new_tier: UserTier) -> bool:
        """Update user's billing tier."""
        db = await get_supabase()
        
        try:
            async with db.get_session() as session:
                user = await session.execute(select(User).where(User.id == user_id))
                user = user.scalar_one_or_none()
                
                if not user:
                    raise ValueError("User not found")
                
                old_tier = user.tier
                user.tier = new_tier
                user.updated_at = datetime.utcnow()
                
                session.add(user)
                await session.commit()
                
                # Log tier change activity
                await self.log_user_activity(
                    user_id=user_id,
                    activity_type="tier_change",
                    description=f"User tier changed from {(old_tier.value if old_tier else 'none')} to {new_tier.value}"
                )
                
                logger.info(f"Updated tier for user {user_id}: {(old_tier.value if old_tier else 'none')} -> {new_tier.value}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to update tier for user {user_id}: {e}")
            return False
    
    async def deactivate_user(self, user_id: int, reason: str = "Administrative action") -> bool:
        """Deactivate a user account."""
        db = await get_supabase()
        
        try:
            async with db.get_session() as session:
                user = await session.execute(select(User).where(User.id == user_id))
                user = user.scalar_one_or_none()
                
                if not user:
                    raise ValueError("User not found")
                
                user.is_active = False
                user.updated_at = datetime.utcnow()
                
                session.add(user)
                await session.commit()
                
                # Log deactivation activity
                await self.log_user_activity(
                    user_id=user_id,
                    activity_type="account_deactivation",
                    description=f"Account deactivated: {reason}"
                )
                
                logger.info(f"Deactivated user {user_id}: {reason}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to deactivate user {user_id}: {e}")
            return False
    
    async def reactivate_user(self, user_id: int, reason: str = "Administrative action") -> bool:
        """Reactivate a deactivated user account."""
        db = await get_supabase()
        
        try:
            async with db.get_session() as session:
                user = await session.execute(select(User).where(User.id == user_id))
                user = user.scalar_one_or_none()
                
                if not user:
                    raise ValueError("User not found")
                
                user.is_active = True
                user.updated_at = datetime.utcnow()
                
                session.add(user)
                await session.commit()
                
                # Log reactivation activity
                await self.log_user_activity(
                    user_id=user_id,
                    activity_type="account_reactivation",
                    description=f"Account reactivated: {reason}"
                )
                
                logger.info(f"Reactivated user {user_id}: {reason}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to reactivate user {user_id}: {e}")
            return False
    
    async def verify_user_email(self, user_id: int) -> bool:
        """Mark user email as verified."""
        db = await get_supabase()
        
        try:
            async with db.get_session() as session:
                user = await session.execute(select(User).where(User.id == user_id))
                user = user.scalar_one_or_none()
                
                if not user:
                    raise ValueError("User not found")
                
                user.is_verified = True
                user.updated_at = datetime.utcnow()
                
                session.add(user)
                await session.commit()
                
                # Log verification activity
                await self.log_user_activity(
                    user_id=user_id,
                    activity_type="email_verification",
                    description="Email address verified"
                )
                
                logger.info(f"Verified email for user {user_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to verify email for user {user_id}: {e}")
            return False
    
    async def change_user_password(self, user_id: int, current_password: str, new_password: str) -> bool:
        """Change user password."""
        try:
            # Get user to verify current password
            user = await self._get_user_by_id(user_id)
            if not user:
                raise ValueError("User not found")
            
            # Use auth manager to change password
            return await self.auth_manager.change_password(user, current_password, new_password)
            
        except Exception as e:
            logger.error(f"Failed to change password for user {user_id}: {e}")
            return False
    
    async def log_user_activity(self, user_id: int, activity_type: str, description: str, metadata: Optional[Dict[str, Any]] = None, ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> bool:
        """Log user activity for audit purposes."""
        db = await get_supabase()
        
        try:
            async with db.get_session() as session:
                # Get user profile
                profile = await session.execute(
                    select(UserProfile).where(UserProfile.user_id == user_id)
                )
                profile = profile.scalar_one_or_none()
                
                if not profile:
                    logger.warning(f"User profile not found for activity logging: {user_id}")
                    return False
                
                # Create activity record
                activity = UserActivity(
                    user_id=user_id,
                    profile_id=profile.id,
                    activity_type=activity_type,
                    description=description,
                    metadata=metadata or {},
                    ip_address=ip_address,
                    user_agent=user_agent,
                    session_id=None  # Could be enhanced with session tracking
                )
                
                session.add(activity)
                await session.commit()
                
                logger.debug(f"Logged activity for user {user_id}: {activity_type}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to log activity for user {user_id}: {e}")
            return False
    
    async def log_user_error(self, user_id: int, error_type: str, error_message: str, stack_trace: Optional[str] = None, severity: str = "medium", context: Optional[Dict[str, Any]] = None) -> bool:
        """Log user errors for debugging and support."""
        db = await get_supabase()
        
        try:
            async with db.get_session() as session:
                # Get user profile
                profile = await session.execute(
                    select(UserProfile).where(UserProfile.user_id == user_id)
                )
                profile = profile.scalar_one_or_none()
                
                if not profile:
                    logger.warning(f"User profile not found for error logging: {user_id}")
                    return False
                
                # Create error record
                error = UserError(
                    user_id=user_id,
                    profile_id=profile.id,
                    error_type=error_type,
                    error_message=error_message,
                    stack_trace=stack_trace,
                    severity=severity,
                    context=context or {},
                    resolved=False
                )
                
                session.add(error)
                await session.commit()
                
                logger.warning(f"Logged error for user {user_id}: {error_type} - {error_message}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to log error for user {user_id}: {e}")
            return False
    
    async def get_user_activities(self, user_id: int, limit: int = 50, activity_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get user activity history."""
        db = await get_supabase()
        
        async with db.get_session() as session:
            query = select(UserActivity).where(UserActivity.user_id == user_id)
            
            if activity_type:
                query = query.where(UserActivity.activity_type == activity_type)
            
            result = await session.execute(
                query.order_by(UserActivity.created_at.desc()).limit(limit)
            )
            
            activities = result.scalars().all()
            return [
                {
                    "id": activity.id,
                    "activity_type": activity.activity_type,
                    "description": activity.description,
                    "metadata": activity.metadata,
                    "ip_address": activity.ip_address,
                    "user_agent": activity.user_agent,
                    "created_at": activity.created_at.isoformat()
                }
                for activity in activities
            ]
    
    async def get_user_errors(self, user_id: int, limit: int = 50, severity: Optional[str] = None, resolved: Optional[bool] = None) -> List[Dict[str, Any]]:
        """Get user error history."""
        db = await get_supabase()
        
        async with db.get_session() as session:
            query = select(UserError).where(UserError.user_id == user_id)
            
            if severity:
                query = query.where(UserError.severity == severity)
            
            if resolved is not None:
                query = query.where(UserError.resolved == resolved)
            
            result = await session.execute(
                query.order_by(UserError.created_at.desc()).limit(limit)
            )
            
            errors = result.scalars().all()
            return [
                {
                    "id": error.id,
                    "error_type": error.error_type,
                    "error_message": error.error_message,
                    "stack_trace": error.stack_trace,
                    "severity": error.severity,
                    "context": error.context,
                    "resolved": error.resolved,
                    "resolved_at": error.resolved_at.isoformat() if error.resolved_at else None,
                    "created_at": error.created_at.isoformat()
                }
                for error in errors
            ]
    
    async def search_users(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search users by name, email, or username."""
        db = get_database()
        
        search_term = f"%{query}%"
        
        async with db.get_session() as session:
            result = await session.execute(
                select(User, UserProfile).join(
                    UserProfile, User.id == UserProfile.user_id
                ).where(
                    or_(
                        User.full_name.ilike(search_term),
                        User.email.ilike(search_term),
                        User.username.ilike(search_term)
                    )
                ).limit(limit)
            )
            
            users = []
            for user, profile in result:
                users.append({
                    "id": user.id,
                    "email": user.email,
                    "username": user.username,
                    "full_name": user.full_name,
                    "tier": user.tier.value,
                    "is_active": user.is_active,
                    "company": profile.company,
                    "job_title": profile.job_title,
                    "location": profile.location
                })
            
            return users
    
    async def get_user_statistics(self) -> Dict[str, Any]:
        """Get system-wide user statistics."""
        db = get_database()
        
        async with db.get_session() as session:
            # Total users
            total_users = await session.execute(select(func.count(User.id)))
            total_users = total_users.scalar()
            
            # Users by tier
            tier_counts = await session.execute(
                select(User.tier, func.count(User.id))
                .group_by(User.tier)
            )
            
            tier_stats = {}
            for tier, count in tier_counts:
                tier_stats[tier.value] = count
            
            # Active vs inactive users
            active_users = await session.execute(
                select(func.count(User.id)).where(User.is_active == True)
            )
            active_users = active_users.scalar()
            
            inactive_users = total_users - active_users
            
            # Verified vs unverified users
            verified_users = await session.execute(
                select(func.count(User.id)).where(User.is_verified == True)
            )
            verified_users = verified_users.scalar()
            
            unverified_users = total_users - verified_users
            
            # Recent registrations (last 30 days)
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            recent_registrations = await session.execute(
                select(func.count(User.id)).where(User.created_at >= thirty_days_ago)
            )
            recent_registrations = recent_registrations.scalar()
            
            return {
                "total_users": total_users,
                "active_users": active_users,
                "inactive_users": inactive_users,
                "verified_users": verified_users,
                "unverified_users": unverified_users,
                "users_by_tier": tier_stats,
                "recent_registrations_30_days": recent_registrations
            }
    
    async def _get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get User object by ID for internal use."""
        db = get_database()
        
        async with db.get_session() as session:
            result = await session.execute(select(User).where(User.id == user_id))
            return result.scalar_one_or_none()

# Global instance
user_manager = UserManager()

async def get_user_manager() -> UserManager:
    """Get the global user manager instance."""
    if not user_manager._initialized:
        await user_manager.initialize()
    return user_manager

async def init_user_management():
    """Initialize the user management system."""
    await user_manager.initialize()
