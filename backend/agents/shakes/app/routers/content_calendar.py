from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
from ..services.content_calendar_service import ContentCalendarService
from ..models import ContentType, PlatformType, ToneType
from ..database import get_shakes_database

router = APIRouter(prefix="/content-calendar", tags=["Content Calendar"])

# Pydantic Models
class CreateContentCalendarRequest(BaseModel):
    user_id: int = Field(..., description="User ID")
    calendar_name: str = Field(..., description="Calendar name")
    calendar_description: str = Field(..., description="Calendar description")
    start_date: datetime = Field(..., description="Calendar start date")
    end_date: datetime = Field(..., description="Calendar end date")
    content_themes: List[str] = Field(..., description="Content themes")
    posting_frequency: str = Field(..., description="Posting frequency")
    target_audience: str = Field(..., description="Target audience")

class CreateContentCalendarResponse(BaseModel):
    success: bool
    calendar_id: int
    calendar_name: str
    calendar_strategy: str
    content_plan: List[Dict[str, Any]]
    scheduled_entries: List[Dict[str, Any]]
    total_entries: int
    start_date: str
    end_date: str
    timestamp: str

class ScheduleContentRequest(BaseModel):
    calendar_id: int = Field(..., description="Calendar ID")
    content_piece_id: int = Field(..., description="Content piece ID")
    scheduled_time: datetime = Field(..., description="Scheduled time")
    platform: str = Field(..., description="Target platform")
    notes: str = Field(default="", description="Scheduling notes")

class OptimizeCalendarRequest(BaseModel):
    calendar_id: int = Field(..., description="Calendar ID")
    optimization_goals: List[str] = Field(..., description="Optimization goals")

# Dependency
async def get_content_calendar_service() -> ContentCalendarService:
    """Get content calendar service instance"""
    service = ContentCalendarService()
    await service.initialize()
    return service

# Endpoints
@router.post("/create", response_model=CreateContentCalendarResponse, status_code=201)
async def create_content_calendar(
    request: CreateContentCalendarRequest,
    service: ContentCalendarService = Depends(get_content_calendar_service)
):
    """Create a comprehensive content calendar"""
    try:
        result = await service.create_content_calendar(
            user_id=request.user_id,
            calendar_name=request.calendar_name,
            calendar_description=request.calendar_description,
            start_date=request.start_date,
            end_date=request.end_date,
            content_themes=request.content_themes,
            posting_frequency=request.posting_frequency,
            target_audience=request.target_audience
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to create content calendar")
            )
        
        return CreateContentCalendarResponse(**result)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Content calendar creation failed: {str(e)}"
        )

@router.post("/schedule", response_model=Dict[str, Any], status_code=201)
async def schedule_content(
    request: ScheduleContentRequest,
    service: ContentCalendarService = Depends(get_content_calendar_service)
):
    """Schedule content in the calendar"""
    try:
        result = await service.schedule_content(
            calendar_id=request.calendar_id,
            content_piece_id=request.content_piece_id,
            scheduled_time=request.scheduled_time,
            platform=request.platform,
            notes=request.notes
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

@router.get("/view/{calendar_id}", response_model=Dict[str, Any], status_code=200)
async def get_calendar_view(
    calendar_id: int,
    view_type: str = Query(default="month", description="Calendar view type"),
    start_date: datetime = Query(default=None, description="Start date for view"),
    service: ContentCalendarService = Depends(get_content_calendar_service)
):
    """Get calendar view with scheduled content"""
    try:
        result = await service.get_calendar_view(
            calendar_id=calendar_id,
            view_type=view_type,
            start_date=start_date
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to get calendar view")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Calendar view retrieval failed: {str(e)}"
        )

@router.post("/optimize", response_model=Dict[str, Any], status_code=200)
async def optimize_calendar(
    request: OptimizeCalendarRequest,
    service: ContentCalendarService = Depends(get_content_calendar_service)
):
    """Optimize calendar for better performance"""
    try:
        result = await service.optimize_calendar(
            calendar_id=request.calendar_id,
            optimization_goals=request.optimization_goals
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to optimize calendar")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Calendar optimization failed: {str(e)}"
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
                "considerations": ["content_quality", "audience_fatigue"]
            },
            {
                "id": "twice_daily",
                "name": "Twice Daily",
                "description": "Two posts per day",
                "posts_per_day": 2,
                "best_for": ["high_engagement", "news_updates"],
                "considerations": ["content_volume", "audience_attention"]
            },
            {
                "id": "every_other_day",
                "name": "Every Other Day",
                "description": "One post every two days",
                "posts_per_day": 0.5,
                "best_for": ["quality_focus", "limited_resources"],
                "considerations": ["consistency", "audience_expectations"]
            },
            {
                "id": "weekly",
                "name": "Weekly",
                "description": "One post per week",
                "posts_per_day": 0.14,
                "best_for": ["long_form_content", "newsletter_style"],
                "considerations": ["content_depth", "audience_retention"]
            }
        ]
    }

@router.get("/content-themes")
async def get_content_themes():
    """Get popular content themes for calendar planning"""
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

@router.get("/calendar-strategies")
async def get_calendar_strategies():
    """Get content calendar strategies and best practices"""
    return {
        "calendar_strategies": [
            {
                "strategy": "theme_based_planning",
                "name": "Theme-Based Planning",
                "description": "Organize content around specific themes or topics",
                "benefits": ["consistency", "brand_alignment", "audience_engagement"],
                "implementation": ["define_monthly_themes", "create_theme_content", "maintain_consistency"],
                "best_for": ["brand_building", "thought_leadership", "audience_education"]
            },
            {
                "strategy": "audience_segmentation",
                "name": "Audience Segmentation",
                "description": "Create different content for different audience segments",
                "benefits": ["personalization", "relevance", "engagement"],
                "implementation": ["identify_segments", "create_segment_content", "schedule_appropriately"],
                "best_for": ["diverse_audiences", "personalization", "targeted_marketing"]
            },
            {
                "strategy": "seasonal_planning",
                "name": "Seasonal Planning",
                "description": "Align content with seasons, holidays, and events",
                "benefits": ["relevance", "timeliness", "engagement"],
                "implementation": ["identify_seasons", "plan_seasonal_content", "schedule_appropriately"],
                "best_for": ["retail", "lifestyle", "event_based_businesses"]
            },
            {
                "strategy": "content_mix_balance",
                "name": "Content Mix Balance",
                "description": "Balance different types of content for optimal engagement",
                "benefits": ["variety", "engagement", "audience_retention"],
                "implementation": ["define_content_types", "create_mix_ratio", "schedule_balanced"],
                "best_for": ["diverse_content", "audience_retention", "engagement_optimization"]
            }
        ]
    }
