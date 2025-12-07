from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from backend.core.user_management.user_manager import UserManager
from backend.core.user_management.profile_manager import ProfileManager
from backend.core.user_management.activity_tracker import ActivityTracker
from backend.core.user_management.models import UserRole
from backend.core.database.models import UserTier
from backend.core.authentication.auth_manager import get_current_user
from backend.core.user_management.user_manager import User

router = APIRouter(prefix="/api/v1/account", tags=["account"])

class UserProfileResponse(BaseModel):
    id: int
    user_id: int
    bio: str
    avatar_url: str
    company: str
    job_title: str
    location: str
    website: str
    social_links: Dict[str, Any]
    preferences: Dict[str, Any]
    notification_settings: Dict[str, Any]
    timezone: str
    language: str
    created_at: datetime
    updated_at: datetime

class UserActivityResponse(BaseModel):
    id: int
    user_id: int
    activity_type: str
    description: str
    metadata: Dict[str, Any]
    timestamp: datetime
    ip_address: Optional[str]
    user_agent: Optional[str]

class UserStatsResponse(BaseModel):
    total_activities: int
    recent_activities: List[UserActivityResponse]
    account_age_days: int
    last_login: Optional[datetime]
    profile_completion: float
    tier: str
    role: str
    is_verified: bool
    is_active: bool

class UpdateProfileRequest(BaseModel):
    bio: Optional[str] = None
    company: Optional[str] = None
    job_title: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    social_links: Optional[Dict[str, Any]] = None
    timezone: Optional[str] = None
    language: Optional[str] = None

class UpdatePreferencesRequest(BaseModel):
    theme: Optional[str] = None
    notifications: Optional[bool] = None
    language: Optional[str] = None
    timezone: Optional[str] = None

class UpdateNotificationSettingsRequest(BaseModel):
    email_notifications: Optional[bool] = None
    push_notifications: Optional[bool] = None
    marketing_emails: Optional[bool] = None
    weekly_reports: Optional[bool] = None

@router.get("/profile", response_model=UserProfileResponse)
async def get_user_profile(
    current_user: User = Depends(get_current_user)
):
    """Get user profile information"""
    try:
        profile_manager = ProfileManager()
        await profile_manager.initialize()
        
        profile = await profile_manager.get_user_profile(current_user.id)
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )
        
        return UserProfileResponse(
            id=profile.id,
            user_id=profile.user_id,
            bio=profile.bio,
            avatar_url=profile.avatar_url,
            company=profile.company,
            job_title=profile.job_title,
            location=profile.location,
            website=profile.website,
            social_links=profile.social_links,
            preferences=profile.preferences,
            notification_settings=profile.notification_settings,
            timezone=profile.timezone,
            language=profile.language,
            created_at=profile.created_at,
            updated_at=profile.updated_at
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user profile: {str(e)}"
        )

@router.put("/profile")
async def update_user_profile(
    request: UpdateProfileRequest,
    current_user: User = Depends(get_current_user)
):
    """Update user profile information"""
    try:
        profile_manager = ProfileManager()
        await profile_manager.initialize()
        
        update_data = request.dict(exclude_unset=True)
        success = await profile_manager.update_user_profile(current_user.id, update_data)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )
        
        return {
            "success": True,
            "message": "Profile updated successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user profile: {str(e)}"
        )

@router.put("/preferences")
async def update_user_preferences(
    request: UpdatePreferencesRequest,
    current_user: User = Depends(get_current_user)
):
    """Update user preferences"""
    try:
        profile_manager = ProfileManager()
        await profile_manager.initialize()
        
        update_data = request.dict(exclude_unset=True)
        success = await profile_manager.update_user_preferences(current_user.id, update_data)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )
        
        return {
            "success": True,
            "message": "Preferences updated successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user preferences: {str(e)}"
        )

@router.put("/notification-settings")
async def update_notification_settings(
    request: UpdateNotificationSettingsRequest,
    current_user: User = Depends(get_current_user)
):
    """Update notification settings"""
    try:
        profile_manager = ProfileManager()
        await profile_manager.initialize()
        
        update_data = request.dict(exclude_unset=True)
        success = await profile_manager.update_notification_settings(current_user.id, update_data)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )
        
        return {
            "success": True,
            "message": "Notification settings updated successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update notification settings: {str(e)}"
        )

@router.get("/activity", response_model=List[UserActivityResponse])
async def get_user_activity(
    limit: int = Query(50, description="Number of activities to return"),
    offset: int = Query(0, description="Number of activities to skip"),
    activity_type: Optional[str] = Query(None, description="Filter by activity type"),
    current_user: User = Depends(get_current_user)
):
    """Get user activity history"""
    try:
        activity_tracker = ActivityTracker()
        await activity_tracker.initialize()
        
        activities = await activity_tracker.get_user_activities(
            user_id=current_user.id,
            limit=limit,
            offset=offset,
            activity_type=activity_type
        )
        
        return [
            UserActivityResponse(
                id=activity.id,
                user_id=activity.user_id,
                activity_type=activity.activity_type,
                description=activity.description,
                metadata=activity.metadata,
                timestamp=activity.timestamp,
                ip_address=activity.ip_address,
                user_agent=activity.user_agent
            )
            for activity in activities
        ]
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user activity: {str(e)}"
        )

@router.get("/stats", response_model=UserStatsResponse)
async def get_user_stats(
    current_user: User = Depends(get_current_user)
):
    """Get user account statistics"""
    try:
        user_manager = UserManager()
        await user_manager.initialize()
        
        activity_tracker = ActivityTracker()
        await activity_tracker.initialize()
        
        # Get user stats
        stats = await user_manager.get_user_stats(current_user.id)
        
        # Get recent activities
        recent_activities = await activity_tracker.get_user_activities(
            user_id=current_user.id,
            limit=10,
            offset=0
        )
        
        return UserStatsResponse(
            total_activities=stats["total_activities"],
            recent_activities=[
                UserActivityResponse(
                    id=activity.id,
                    user_id=activity.user_id,
                    activity_type=activity.activity_type,
                    description=activity.description,
                    metadata=activity.metadata,
                    timestamp=activity.timestamp,
                    ip_address=activity.ip_address,
                    user_agent=activity.user_agent
                )
                for activity in recent_activities
            ],
            account_age_days=stats["account_age_days"],
            last_login=stats["last_login"],
            profile_completion=stats["profile_completion"],
            tier=current_user.tier.value,
            role=current_user.role.value,
            is_verified=current_user.is_verified,
            is_active=current_user.is_active
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user stats: {str(e)}"
        )

@router.post("/upload-avatar")
async def upload_avatar(
    avatar_url: str,
    current_user: User = Depends(get_current_user)
):
    """Update user avatar"""
    try:
        profile_manager = ProfileManager()
        await profile_manager.initialize()
        
        success = await profile_manager.update_user_avatar(current_user.id, avatar_url)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )
        
        return {
            "success": True,
            "message": "Avatar updated successfully",
            "avatar_url": avatar_url
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update avatar: {str(e)}"
        )

@router.delete("/account")
async def delete_account(
    current_user: User = Depends(get_current_user)
):
    """Delete user account"""
    try:
        user_manager = UserManager()
        await user_manager.initialize()
        
        success = await user_manager.delete_user(current_user.id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return {
            "success": True,
            "message": "Account deleted successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete account: {str(e)}"
        )
