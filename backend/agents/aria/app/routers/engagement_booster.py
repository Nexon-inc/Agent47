from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List
from ..services.engagement_booster_service import EngagementBoosterService
from ..deps import get_current_user
from backend.core.database.models import User

router = APIRouter(prefix="/engagement-booster", tags=["Engagement Booster"])

@router.post("/generate-prompts")
async def generate_engagement_prompts(
    post_content: Dict[str, Any],
    platform: str,
    current_user: User = Depends(get_current_user),
    engagement_booster_service: EngagementBoosterService = Depends()
):
    """Generate engagement-boosting prompts for a post"""
    try:
        await engagement_booster_service.initialize()
        result = await engagement_booster_service.generate_engagement_prompts(
            current_user.id,
            post_content,
            platform
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/apply-boost/{post_id}")
async def apply_engagement_boost(
    post_id: int,
    boost_type: str,
    boost_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    engagement_booster_service: EngagementBoosterService = Depends()
):
    """Apply engagement boost to a scheduled post"""
    try:
        await engagement_booster_service.initialize()
        result = await engagement_booster_service.apply_engagement_boost(
            current_user.id,
            post_id,
            boost_type,
            boost_data
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/{post_id}")
async def get_engagement_analytics(
    post_id: int,
    current_user: User = Depends(get_current_user),
    engagement_booster_service: EngagementBoosterService = Depends()
):
    """Get engagement analytics for a post"""
    try:
        await engagement_booster_service.initialize()
        result = await engagement_booster_service.get_engagement_analytics(
            current_user.id,
            post_id
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trends")
async def get_engagement_trends(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    engagement_booster_service: EngagementBoosterService = Depends()
):
    """Get engagement trends over time"""
    try:
        await engagement_booster_service.initialize()
        result = await engagement_booster_service.get_engagement_trends(
            current_user.id,
            days
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/boost-types")
async def get_available_boost_types():
    """Get available engagement boost types"""
    return {
        "boost_types": [
            {
                "type": "poll",
                "description": "Add interactive polls to posts",
                "best_for": "All platforms",
                "engagement_potential": "High"
            },
            {
                "type": "question",
                "description": "Ask engaging questions to encourage comments",
                "best_for": "All platforms",
                "engagement_potential": "High"
            },
            {
                "type": "cta",
                "description": "Add clear call-to-action buttons",
                "best_for": "All platforms",
                "engagement_potential": "Medium"
            },
            {
                "type": "interactive",
                "description": "Add interactive elements like tagging",
                "best_for": "Instagram, Facebook, TikTok",
                "engagement_potential": "High"
            }
        ]
    }
