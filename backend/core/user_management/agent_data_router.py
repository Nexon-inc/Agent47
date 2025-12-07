"""
API Router for agents to access user's connected platforms, integrations, and profile data
This allows agents to know what platforms/integrations the user has connected
and access their website URL for automation tasks.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, List, Any, Optional
import logging

from ..database import get_db
from ..database.models import User, UserProfile
from ..platforms.oauth_service import get_oauth_service
from ..integrations.integration_manager import IntegrationManager, get_integration_manager
from ..authentication.auth_manager import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/agent-data", tags=["agent-data"])


@router.get("/user-platforms")
async def get_user_platforms_for_agent(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user's connected platforms for agent use
    Agents can call this to know what platforms the user has connected
    """
    try:
        # Verify the request is for the current user (agents can only access their user's data)
        if user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Cannot access other user's data")
        
        oauth_service = await get_oauth_service()
        platforms = await oauth_service.get_user_platforms(user_id)
        
        # Format for agent consumption
        formatted_platforms = []
        for platform in platforms:
            formatted_platforms.append({
                "platform_name": platform.get("platform_name"),
                "display_name": platform.get("display_name"),
                "status": platform.get("status"),
                "connected_at": platform.get("connected_at"),
                "platform_type": platform.get("platform_type", "social_media")
            })
        
        return {
            "success": True,
            "user_id": user_id,
            "platforms": formatted_platforms,
            "total": len(formatted_platforms)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user platforms for agent: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user platforms")


@router.get("/user-integrations")
async def get_user_integrations_for_agent(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user's connected integrations for agent use
    Agents can call this to know what integrations/tools the user has connected
    """
    try:
        # Verify the request is for the current user
        if user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Cannot access other user's data")
        
        integration_manager = IntegrationManager()
        await integration_manager.initialize()
        
        usage = await integration_manager.get_user_integration_usage(user_id)
        
        # Format for agent consumption
        formatted_integrations = []
        for usage_item in usage:
            formatted_integrations.append({
                "integration_id": usage_item.integration_id,
                "integration_name": usage_item.integration_name,
                "status": usage_item.status.value,
                "connected_at": usage_item.connected_at.isoformat() if usage_item.connected_at else None,
                "last_used": usage_item.last_used.isoformat() if usage_item.last_used else None,
                "credentials_status": usage_item.credentials_status.value
            })
        
        return {
            "success": True,
            "user_id": user_id,
            "integrations": formatted_integrations,
            "total": len(formatted_integrations)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user integrations for agent: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user integrations")


@router.get("/user-profile")
async def get_user_profile_for_agent(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user's profile data including website URL for agent use
    Agents can use this to access user's website URL and other profile info
    """
    try:
        # Verify the request is for the current user
        if user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Cannot access other user's data")
        
        # Get user and profile
        result = await db.execute(
            select(User, UserProfile).outerjoin(
                UserProfile, User.id == UserProfile.user_id
            ).where(User.id == user_id)
        )
        user_data = result.first()
        
        if not user_data:
            raise HTTPException(status_code=404, detail="User profile not found")
        
        user, profile = user_data
        
        # Get website URL from multiple sources (priority order)
        website_url = ""
        if user:
            # Priority 1: User.website_url (direct field)
            if user.website_url:
                website_url = user.website_url
            # Priority 2: onboarding_data.profile.business_website
            elif user.onboarding_data and isinstance(user.onboarding_data, dict):
                profile_data = user.onboarding_data.get("profile", {})
                if profile_data.get("business_website"):
                    website_url = profile_data.get("business_website")
                # Priority 3: onboarding_data.profile.website
                elif profile_data.get("website"):
                    website_url = profile_data.get("website")
        
        # Extract onboarding data for comprehensive profile info
        onboarding_data = user.onboarding_data if user.onboarding_data else {}
        onboarding_profile = onboarding_data.get("profile", {}) if isinstance(onboarding_data, dict) else {}
        onboarding_business = onboarding_data.get("business", {}) if isinstance(onboarding_data, dict) else {}
        
        return {
            "success": True,
            "user_id": user_id,
            "profile": {
                "website_url": website_url,
                "full_name": user.full_name if user else (profile.first_name + " " + profile.last_name if profile and profile.first_name and profile.last_name else ""),
                "bio": profile.bio if profile else (onboarding_profile.get("bio", "")),
                "company": onboarding_profile.get("company", "") or onboarding_business.get("businessName", ""),
                "business_name": onboarding_business.get("businessName", ""),
                "business_website": onboarding_business.get("businessWebsite", ""),
                "industry": onboarding_business.get("industry", ""),
                "role": onboarding_business.get("role", ""),
                "job_title": onboarding_profile.get("jobTitle", ""),
                "location": onboarding_profile.get("location", ""),
                "business_size": onboarding_business.get("businessSize", ""),
                "business_stage": onboarding_business.get("businessStage", ""),
                "primary_goals": onboarding_business.get("primaryGoals", []),
                "main_purpose": onboarding_business.get("mainPurpose", ""),
                "timezone": profile.timezone if profile else (onboarding_profile.get("timezone", "")),
                "language": profile.language if profile else (onboarding_profile.get("language", "en")),
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user profile for agent: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user profile")


@router.get("/user-resources")
async def get_all_user_resources_for_agent(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all user resources (platforms, integrations, profile) in one call
    Convenient endpoint for agents to get everything they need
    """
    try:
        # Verify the request is for the current user
        if user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Cannot access other user's data")
        
        # Get platforms
        oauth_service = await get_oauth_service()
        platforms = await oauth_service.get_user_platforms(user_id)
        formatted_platforms = [
            {
                "platform_name": p.get("platform_name"),
                "display_name": p.get("display_name"),
                "status": p.get("status"),
                "platform_type": p.get("platform_type", "social_media")
            }
            for p in platforms
        ]
        
        # Get integrations
        integration_manager = IntegrationManager()
        await integration_manager.initialize()
        usage = await integration_manager.get_user_integration_usage(user_id)
        formatted_integrations = [
            {
                "integration_name": u.integration_name,
                "status": u.status.value,
                "credentials_status": u.credentials_status.value
            }
            for u in usage
        ]
        
        # Get user and profile for comprehensive data
        result = await db.execute(
            select(User, UserProfile).outerjoin(
                UserProfile, User.id == UserProfile.user_id
            ).where(User.id == user_id)
        )
        user_data = result.first()
        
        # Get website URL from multiple sources (priority order)
        website_url = ""
        profile_data = {}
        if user_data:
            user, profile = user_data
            if user:
                # Priority 1: User.website_url (direct field)
                if user.website_url:
                    website_url = user.website_url
                # Priority 2: onboarding_data.profile.business_website
                elif user.onboarding_data and isinstance(user.onboarding_data, dict):
                    onboarding_profile = user.onboarding_data.get("profile", {})
                    if onboarding_profile.get("business_website"):
                        website_url = onboarding_profile.get("business_website")
                    # Priority 3: onboarding_data.profile.website
                    elif onboarding_profile.get("website"):
                        website_url = onboarding_profile.get("website")
                
                # Extract comprehensive profile info
                onboarding_data = user.onboarding_data if user.onboarding_data else {}
                onboarding_profile = onboarding_data.get("profile", {}) if isinstance(onboarding_data, dict) else {}
                onboarding_business = onboarding_data.get("business", {}) if isinstance(onboarding_data, dict) else {}
                
                profile_data = {
                    "website_url": website_url,
                    "full_name": user.full_name if user else (profile.first_name + " " + profile.last_name if profile and profile.first_name and profile.last_name else ""),
                    "bio": profile.bio if profile else (onboarding_profile.get("bio", "")),
                    "company": onboarding_profile.get("company", "") or onboarding_business.get("businessName", ""),
                    "business_name": onboarding_business.get("businessName", ""),
                    "business_website": onboarding_business.get("businessWebsite", ""),
                    "industry": onboarding_business.get("industry", ""),
                    "role": onboarding_business.get("role", ""),
                    "job_title": onboarding_profile.get("jobTitle", ""),
                    "location": onboarding_profile.get("location", ""),
                }
        
        return {
            "success": True,
            "user_id": user_id,
            "platforms": formatted_platforms,
            "integrations": formatted_integrations,
            "profile": profile_data,
            "summary": {
                "total_platforms": len(formatted_platforms),
                "total_integrations": len(formatted_integrations),
                "has_website": bool(website_url)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user resources for agent: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user resources")

