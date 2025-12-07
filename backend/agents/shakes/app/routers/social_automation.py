from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
from ..services.social_automation_service import SocialMediaAutomationService
from ..models import ContentType, PlatformType, ToneType
from ..database import get_shakes_database

router = APIRouter(prefix="/social-automation", tags=["Social Media Automation"])

# Pydantic Models
class CreateAutomationCampaignRequest(BaseModel):
    user_id: int = Field(..., description="User ID")
    campaign_name: str = Field(..., description="Campaign name")
    platforms: List[str] = Field(..., description="Target platforms")
    content_themes: List[str] = Field(..., description="Content themes")
    posting_frequency: str = Field(..., description="Posting frequency")
    target_audience: str = Field(..., description="Target audience")
    campaign_duration_days: int = Field(..., description="Campaign duration in days")
    tone: str = Field(..., description="Content tone")

class CreateAutomationCampaignResponse(BaseModel):
    success: bool
    project_id: int
    campaign_name: str
    campaign_strategy: str
    scheduled_posts: List[Dict[str, Any]]
    total_posts: int
    platforms: List[str]
    campaign_duration_days: int
    timestamp: str

class ScheduleContentRequest(BaseModel):
    content_piece_id: int = Field(..., description="Content piece ID")
    platforms: List[str] = Field(..., description="Target platforms")
    scheduled_times: List[datetime] = Field(..., description="Scheduled posting times")
    automation_settings: Dict[str, Any] = Field(default={}, description="Automation settings")

class OptimizePostingTimesRequest(BaseModel):
    user_id: int = Field(..., description="User ID")
    platform: str = Field(..., description="Target platform")
    target_audience: str = Field(..., description="Target audience")
    content_type: str = Field(..., description="Content type")

# Dependency
async def get_social_automation_service() -> SocialMediaAutomationService:
    """Get social media automation service instance"""
    service = SocialMediaAutomationService()
    await service.initialize()
    return service

# Endpoints
@router.post("/campaign", response_model=CreateAutomationCampaignResponse, status_code=201)
async def create_automation_campaign(
    request: CreateAutomationCampaignRequest,
    service: SocialMediaAutomationService = Depends(get_social_automation_service)
):
    """Create automated social media campaign"""
    try:
        result = await service.create_automation_campaign(
            user_id=request.user_id,
            campaign_name=request.campaign_name,
            platforms=request.platforms,
            content_themes=request.content_themes,
            posting_frequency=request.posting_frequency,
            target_audience=request.target_audience,
            campaign_duration_days=request.campaign_duration_days,
            tone=request.tone
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to create automation campaign")
            )
        
        return CreateAutomationCampaignResponse(**result)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Automation campaign creation failed: {str(e)}"
        )

@router.post("/schedule", response_model=Dict[str, Any], status_code=201)
async def schedule_content(
    request: ScheduleContentRequest,
    service: SocialMediaAutomationService = Depends(get_social_automation_service)
):
    """Schedule content for multiple platforms"""
    try:
        result = await service.schedule_content(
            content_piece_id=request.content_piece_id,
            platforms=request.platforms,
            scheduled_times=request.scheduled_times,
            automation_settings=request.automation_settings
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to schedule content")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Content scheduling failed: {str(e)}"
        )

@router.post("/optimize-posting-times", response_model=Dict[str, Any], status_code=200)
async def optimize_posting_times(
    request: OptimizePostingTimesRequest,
    service: SocialMediaAutomationService = Depends(get_social_automation_service)
):
    """Optimize posting times based on audience and platform"""
    try:
        result = await service.optimize_posting_times(
            user_id=request.user_id,
            platform=request.platform,
            target_audience=request.target_audience,
            content_type=request.content_type
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to optimize posting times")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Posting time optimization failed: {str(e)}"
        )

@router.get("/posting-frequencies")
async def get_posting_frequencies():
    """Get available posting frequency options"""
    return {
        "posting_frequencies": [
            {
                "id": "daily",
                "name": "Daily",
                "description": "One post per day",
                "posts_per_day": 1,
                "best_for": ["consistent_presence", "audience_engagement"],
                "platforms": ["all"],
                "considerations": ["content_quality", "audience_fatigue"]
            },
            {
                "id": "twice_daily",
                "name": "Twice Daily",
                "description": "Two posts per day",
                "posts_per_day": 2,
                "best_for": ["high_engagement", "news_updates"],
                "platforms": ["twitter", "linkedin", "facebook"],
                "considerations": ["content_volume", "audience_attention"]
            },
            {
                "id": "every_other_day",
                "name": "Every Other Day",
                "description": "One post every two days",
                "posts_per_day": 0.5,
                "best_for": ["quality_focus", "limited_resources"],
                "platforms": ["all"],
                "considerations": ["consistency", "audience_expectations"]
            },
            {
                "id": "weekly",
                "name": "Weekly",
                "description": "One post per week",
                "posts_per_day": 0.14,
                "best_for": ["long_form_content", "newsletter_style"],
                "platforms": ["linkedin", "blog"],
                "considerations": ["content_depth", "audience_retention"]
            }
        ]
    }

@router.get("/content-themes")
async def get_content_themes():
    """Get popular content themes for automation"""
    return {
        "content_themes": [
            {
                "id": "educational",
                "name": "Educational",
                "description": "Informative and educational content",
                "best_for": ["thought_leadership", "audience_education"],
                "content_types": ["how_to", "tips", "tutorials", "guides"],
                "engagement_tips": ["ask_questions", "encourage_sharing", "provide_value"]
            },
            {
                "id": "promotional",
                "name": "Promotional",
                "description": "Product and service promotion",
                "best_for": ["sales", "product_launches", "offers"],
                "content_types": ["product_showcase", "announcements", "offers"],
                "engagement_tips": ["create_urgency", "highlight_benefits", "clear_cta"]
            },
            {
                "id": "behind_scenes",
                "name": "Behind the Scenes",
                "description": "Company culture and behind-the-scenes content",
                "best_for": ["brand_building", "authenticity", "team_showcase"],
                "content_types": ["team_spotlight", "office_tour", "process_showcase"],
                "engagement_tips": ["show_personality", "be_authentic", "encourage_interaction"]
            },
            {
                "id": "user_generated",
                "name": "User Generated Content",
                "description": "Content from customers and users",
                "best_for": ["social_proof", "community_building", "authenticity"],
                "content_types": ["testimonials", "reviews", "user_spotlight"],
                "engagement_tips": ["encourage_tagging", "showcase_users", "create_hashtags"]
            },
            {
                "id": "trending",
                "name": "Trending Topics",
                "description": "Content around current trends and news",
                "best_for": ["relevance", "timeliness", "engagement"],
                "content_types": ["news_updates", "trend_commentary", "industry_insights"],
                "engagement_tips": ["be_timely", "add_perspective", "encourage_discussion"]
            }
        ]
    }

@router.get("/platform-best-practices")
async def get_platform_best_practices():
    """Get platform-specific best practices for automation"""
    return {
        "platform_best_practices": [
            {
                "platform": "facebook",
                "optimal_posting_times": ["9am-10am", "3pm-4pm", "7pm-9pm"],
                "content_types": ["text", "image", "video", "link"],
                "character_limits": {"post": 63206, "ad_headline": 40},
                "best_practices": [
                    "Use visual content to increase engagement",
                    "Ask questions to encourage comments",
                    "Post when your audience is most active",
                    "Use Facebook's native video for better reach"
                ],
                "automation_tips": [
                    "Schedule posts during peak hours",
                    "Use Facebook's built-in scheduling",
                    "Monitor engagement and adjust timing",
                    "Test different content types"
                ]
            },
            {
                "platform": "twitter",
                "optimal_posting_times": ["9am-10am", "12pm-1pm", "5pm-6pm"],
                "content_types": ["text", "image", "video", "poll"],
                "character_limits": {"tweet": 280, "thread": 280},
                "best_practices": [
                    "Keep tweets concise and engaging",
                    "Use relevant hashtags (1-2 per tweet)",
                    "Engage with trending topics",
                    "Use threads for longer content"
                ],
                "automation_tips": [
                    "Post frequently for better visibility",
                    "Use Twitter's native scheduling",
                    "Monitor trending hashtags",
                    "Engage with replies promptly"
                ]
            },
            {
                "platform": "linkedin",
                "optimal_posting_times": ["8am-9am", "12pm-1pm", "5pm-6pm"],
                "content_types": ["text", "image", "video", "article", "poll"],
                "character_limits": {"post": 3000, "article": 125000},
                "best_practices": [
                    "Maintain professional tone",
                    "Share industry insights and expertise",
                    "Use LinkedIn's native video",
                    "Engage with professional content"
                ],
                "automation_tips": [
                    "Post during business hours",
                    "Use LinkedIn's scheduling feature",
                    "Focus on professional value",
                    "Engage with industry discussions"
                ]
            },
            {
                "platform": "instagram",
                "optimal_posting_times": ["11am-1pm", "5pm-7pm"],
                "content_types": ["image", "video", "story", "reel", "igtv"],
                "character_limits": {"caption": 2200, "bio": 150},
                "best_practices": [
                    "Use high-quality visuals",
                    "Write engaging captions",
                    "Use relevant hashtags (5-10)",
                    "Post consistently"
                ],
                "automation_tips": [
                    "Use Instagram's native scheduling",
                    "Plan visual content in advance",
                    "Use Stories for real-time engagement",
                    "Monitor hashtag performance"
                ]
            }
        ]
    }
