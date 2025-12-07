"""
Utility functions for agents to fetch user's connected platforms, integrations, and profile data
Agents can use these functions to access user's connected resources
"""
import logging
from typing import Dict, List, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..platforms.oauth_service import get_oauth_service
from ..integrations.integration_manager import IntegrationManager
from ..database.models import User, UserProfile

logger = logging.getLogger(__name__)


async def get_user_platforms_for_agent(user_id: int, db: AsyncSession) -> List[Dict[str, Any]]:
    """
    Fetch user's connected platforms for agent use
    Returns list of connected platforms with their status
    """
    try:
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
        
        return formatted_platforms
    except Exception as e:
        logger.error(f"Failed to fetch user platforms for agent: {e}")
        return []


async def get_user_integrations_for_agent(user_id: int, db: AsyncSession) -> List[Dict[str, Any]]:
    """
    Fetch user's connected integrations for agent use
    Returns list of connected integrations with their status
    """
    try:
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
        
        return formatted_integrations
    except Exception as e:
        logger.error(f"Failed to fetch user integrations for agent: {e}")
        return []


async def get_user_profile_for_agent(user_id: int, db: AsyncSession) -> Optional[Dict[str, Any]]:
    """
    Fetch user's profile data including website URL for agent use
    Returns profile dict with website_url and other info from multiple sources
    """
    try:
        # Get User and UserProfile
        result = await db.execute(
            select(User, UserProfile).outerjoin(
                UserProfile, User.id == UserProfile.user_id
            ).where(User.id == user_id)
        )
        user_data = result.first()
        
        if not user_data:
            return None
        
        user, profile = user_data if user_data else (None, None)
        
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
        onboarding_data = user.onboarding_data if user and user.onboarding_data else {}
        onboarding_profile = onboarding_data.get("profile", {}) if isinstance(onboarding_data, dict) else {}
        onboarding_business = onboarding_data.get("business", {}) if isinstance(onboarding_data, dict) else {}
        
        return {
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
    except Exception as e:
        logger.error(f"Failed to fetch user profile for agent: {e}")
        return None


async def get_all_user_resources_for_agent(user_id: int, db: AsyncSession) -> Dict[str, Any]:
    """
    Fetch all user resources (platforms, integrations, profile) in one call
    Convenient function for agents to get everything they need
    """
    try:
        # Get platforms
        platforms = await get_user_platforms_for_agent(user_id, db)
        
        # Get integrations
        integrations = await get_user_integrations_for_agent(user_id, db)
        
        # Get profile
        profile = await get_user_profile_for_agent(user_id, db) or {}
        
        return {
            "platforms": platforms,
            "integrations": integrations,
            "profile": profile,
            "summary": {
                "total_platforms": len(platforms),
                "total_integrations": len(integrations),
                "has_website": bool(profile.get("website_url"))
            }
        }
    except Exception as e:
        logger.error(f"Failed to fetch user resources for agent: {e}")
        return {"platforms": [], "integrations": [], "profile": {}, "summary": {}}

