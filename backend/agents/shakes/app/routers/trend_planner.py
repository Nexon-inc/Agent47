from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
from ..services.trend_planner_service import TrendPlannerService
from ..models import ContentType, PlatformType, ToneType
from ..database import get_shakes_database

router = APIRouter(prefix="/trend-planner", tags=["Trend Planner"])

# Pydantic Models
class AnalyzeTrendsRequest(BaseModel):
    user_id: int = Field(..., description="User ID")
    trend_categories: List[str] = Field(..., description="Trend categories")
    analysis_period_days: int = Field(default=30, description="Analysis period in days")
    target_platforms: List[str] = Field(..., description="Target platforms")

class CreateTrendContentPlanRequest(BaseModel):
    user_id: int = Field(..., description="User ID")
    trend_opportunities: List[Dict[str, Any]] = Field(..., description="Trend opportunities")
    planning_horizon_days: int = Field(..., description="Planning horizon in days")
    content_goals: List[str] = Field(..., description="Content goals")

class OptimizeTrendStrategyRequest(BaseModel):
    user_id: int = Field(..., description="User ID")
    current_strategy: Dict[str, Any] = Field(..., description="Current strategy")
    performance_data: Dict[str, Any] = Field(..., description="Performance data")
    optimization_goals: List[str] = Field(..., description="Optimization goals")

class MonitorTrendPerformanceRequest(BaseModel):
    user_id: int = Field(..., description="User ID")
    trend_monitoring_config: Dict[str, Any] = Field(..., description="Trend monitoring config")
    monitoring_period_days: int = Field(default=30, description="Monitoring period in days")

# Dependency
async def get_trend_planner_service() -> TrendPlannerService:
    """Get trend planner service instance"""
    service = TrendPlannerService()
    await service.initialize()
    return service

# Endpoints
@router.post("/analyze-trends", response_model=Dict[str, Any], status_code=200)
async def analyze_trends(
    request: AnalyzeTrendsRequest,
    service: TrendPlannerService = Depends(get_trend_planner_service)
):
    """Analyze current trends for content planning"""
    try:
        result = await service.analyze_trends(
            user_id=request.user_id,
            trend_categories=request.trend_categories,
            analysis_period_days=request.analysis_period_days,
            target_platforms=request.target_platforms
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to analyze trends")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Trend analysis failed: {str(e)}"
        )

@router.post("/create-content-plan", response_model=Dict[str, Any], status_code=201)
async def create_trend_content_plan(
    request: CreateTrendContentPlanRequest,
    service: TrendPlannerService = Depends(get_trend_planner_service)
):
    """Create content plan based on trend opportunities"""
    try:
        result = await service.create_trend_content_plan(
            user_id=request.user_id,
            trend_opportunities=request.trend_opportunities,
            planning_horizon_days=request.planning_horizon_days,
            content_goals=request.content_goals
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to create trend content plan")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Trend content plan creation failed: {str(e)}"
        )

@router.post("/optimize-strategy", response_model=Dict[str, Any], status_code=200)
async def optimize_trend_strategy(
    request: OptimizeTrendStrategyRequest,
    service: TrendPlannerService = Depends(get_trend_planner_service)
):
    """Optimize trend-based content strategy"""
    try:
        result = await service.optimize_trend_strategy(
            user_id=request.user_id,
            current_strategy=request.current_strategy,
            performance_data=request.performance_data,
            optimization_goals=request.optimization_goals
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to optimize trend strategy")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Trend strategy optimization failed: {str(e)}"
        )

@router.post("/monitor-performance", response_model=Dict[str, Any], status_code=200)
async def monitor_trend_performance(
    request: MonitorTrendPerformanceRequest,
    service: TrendPlannerService = Depends(get_trend_planner_service)
):
    """Monitor performance of trend-based content"""
    try:
        result = await service.monitor_trend_performance(
            user_id=request.user_id,
            trend_monitoring_config=request.trend_monitoring_config,
            monitoring_period_days=request.monitoring_period_days
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to monitor trend performance")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Trend performance monitoring failed: {str(e)}"
        )

@router.get("/trend-categories")
async def get_trend_categories():
    """Get available trend categories for analysis"""
    return {
        "trend_categories": [
            {
                "id": "industry_trends",
                "name": "Industry Trends",
                "description": "Trends specific to your industry",
                "sources": ["industry_reports", "trade_publications", "expert_analysis", "market_research"],
                "relevance": "high",
                "update_frequency": "weekly"
            },
            {
                "id": "social_media_trends",
                "name": "Social Media Trends",
                "description": "Trending topics on social media platforms",
                "sources": ["twitter_trends", "instagram_trends", "tiktok_trends", "linkedin_trends"],
                "relevance": "high",
                "update_frequency": "daily"
            },
            {
                "id": "content_trends",
                "name": "Content Trends",
                "description": "Trending content formats and styles",
                "sources": ["content_platforms", "creator_insights", "engagement_data", "format_analysis"],
                "relevance": "high",
                "update_frequency": "weekly"
            },
            {
                "id": "technology_trends",
                "name": "Technology Trends",
                "description": "Emerging technology and digital trends",
                "sources": ["tech_news", "product_launches", "innovation_reports", "adoption_data"],
                "relevance": "medium",
                "update_frequency": "weekly"
            },
            {
                "id": "cultural_trends",
                "name": "Cultural Trends",
                "description": "Cultural and societal trends",
                "sources": ["cultural_analysis", "social_movements", "lifestyle_changes", "demographic_shifts"],
                "relevance": "medium",
                "update_frequency": "monthly"
            },
            {
                "id": "seasonal_trends",
                "name": "Seasonal Trends",
                "description": "Seasonal and cyclical trends",
                "sources": ["seasonal_data", "holiday_trends", "weather_patterns", "calendar_events"],
                "relevance": "medium",
                "update_frequency": "monthly"
            }
        ]
    }

@router.get("/target-platforms")
async def get_target_platforms():
    """Get available target platforms for trend analysis"""
    return {
        "target_platforms": [
            {
                "id": "youtube",
                "name": "YouTube",
                "description": "Video content platform",
                "trend_sources": ["trending_videos", "creator_insights", "search_trends", "viewer_behavior"],
                "content_types": ["long_form_video", "short_form_video", "live_streaming", "shorts"],
                "audience_demographics": ["all_ages", "global_reach", "diverse_interests"]
            },
            {
                "id": "instagram",
                "name": "Instagram",
                "description": "Visual content platform",
                "trend_sources": ["explore_page", "hashtag_trends", "story_trends", "reels_trends"],
                "content_types": ["photos", "stories", "reels", "igtv", "live_video"],
                "audience_demographics": ["young_adults", "visual_focused", "lifestyle_oriented"]
            },
            {
                "id": "tiktok",
                "name": "TikTok",
                "description": "Short-form video platform",
                "trend_sources": ["for_you_page", "trending_sounds", "hashtag_challenges", "creator_trends"],
                "content_types": ["short_videos", "dance_trends", "comedy_skits", "educational_content"],
                "audience_demographics": ["gen_z", "millennials", "creative_community"]
            },
            {
                "id": "linkedin",
                "name": "LinkedIn",
                "description": "Professional networking platform",
                "trend_sources": ["industry_insights", "professional_trends", "thought_leadership", "career_trends"],
                "content_types": ["articles", "posts", "videos", "carousels", "newsletters"],
                "audience_demographics": ["professionals", "business_owners", "industry_experts"]
            },
            {
                "id": "twitter",
                "name": "Twitter",
                "description": "Micro-blogging platform",
                "trend_sources": ["trending_topics", "hashtag_trends", "news_trends", "conversation_trends"],
                "content_types": ["tweets", "threads", "spaces", "fleets"],
                "audience_demographics": ["news_consumers", "thought_leaders", "real_time_engagement"]
            },
            {
                "id": "facebook",
                "name": "Facebook",
                "description": "Social networking platform",
                "trend_sources": ["trending_topics", "group_discussions", "event_trends", "community_trends"],
                "content_types": ["posts", "videos", "stories", "live_video", "groups"],
                "audience_demographics": ["diverse_age_groups", "community_focused", "local_engagement"]
            }
        ]
    }

@router.get("/content-goals")
async def get_content_goals():
    """Get available content goals for trend planning"""
    return {
        "content_goals": [
            {
                "id": "brand_awareness",
                "name": "Brand Awareness",
                "description": "Increase brand recognition and visibility",
                "metrics": ["reach", "impressions", "brand_mentions", "share_of_voice"],
                "trend_focus": ["industry_trends", "cultural_trends", "social_media_trends"],
                "priority": "high"
            },
            {
                "id": "engagement",
                "name": "Engagement",
                "description": "Increase audience engagement and interaction",
                "metrics": ["likes", "comments", "shares", "saves", "time_spent"],
                "trend_focus": ["content_trends", "social_media_trends", "cultural_trends"],
                "priority": "high"
            },
            {
                "id": "lead_generation",
                "name": "Lead Generation",
                "description": "Generate qualified leads and prospects",
                "metrics": ["leads", "sign_ups", "downloads", "contact_form_submissions"],
                "trend_focus": ["industry_trends", "technology_trends", "content_trends"],
                "priority": "high"
            },
            {
                "id": "thought_leadership",
                "name": "Thought Leadership",
                "description": "Establish expertise and industry authority",
                "metrics": ["expert_mentions", "speaking_opportunities", "media_coverage", "industry_recognition"],
                "trend_focus": ["industry_trends", "technology_trends", "cultural_trends"],
                "priority": "medium"
            },
            {
                "id": "community_building",
                "name": "Community Building",
                "description": "Build and nurture a community around your brand",
                "metrics": ["community_growth", "member_engagement", "user_generated_content", "community_retention"],
                "trend_focus": ["social_media_trends", "cultural_trends", "content_trends"],
                "priority": "medium"
            },
            {
                "id": "sales_conversion",
                "name": "Sales Conversion",
                "description": "Drive sales and revenue growth",
                "metrics": ["sales", "revenue", "conversion_rate", "customer_acquisition_cost"],
                "trend_focus": ["industry_trends", "seasonal_trends", "content_trends"],
                "priority": "high"
            }
        ]
    }

@router.get("/optimization-goals")
async def get_optimization_goals():
    """Get available optimization goals for trend strategy"""
    return {
        "optimization_goals": [
            {
                "id": "trend_adoption",
                "name": "Trend Adoption",
                "description": "Optimize for faster trend adoption",
                "target_metrics": ["trend_response_time", "trend_engagement", "trend_relevance"],
                "strategies": ["early_trend_detection", "quick_content_creation", "trend_amplification"],
                "priority": "high"
            },
            {
                "id": "audience_growth",
                "name": "Audience Growth",
                "description": "Optimize for audience growth through trends",
                "target_metrics": ["follower_growth", "audience_engagement", "reach_expansion"],
                "strategies": ["trend_targeting", "audience_segmentation", "content_personalization"],
                "priority": "high"
            },
            {
                "id": "content_performance",
                "name": "Content Performance",
                "description": "Optimize for better content performance",
                "target_metrics": ["engagement_rate", "reach", "conversion_rate", "quality_score"],
                "strategies": ["trend_integration", "format_optimization", "timing_optimization"],
                "priority": "high"
            },
            {
                "id": "brand_relevance",
                "name": "Brand Relevance",
                "description": "Optimize for brand relevance in trending topics",
                "target_metrics": ["brand_mentions", "sentiment_score", "brand_recall", "relevance_score"],
                "strategies": ["trend_alignment", "brand_voice_consistency", "authentic_engagement"],
                "priority": "medium"
            },
            {
                "id": "competitive_advantage",
                "name": "Competitive Advantage",
                "description": "Optimize for competitive advantage through trends",
                "target_metrics": ["market_share", "competitive_position", "innovation_score"],
                "strategies": ["trend_leadership", "innovation_tracking", "competitive_analysis"],
                "priority": "medium"
            }
        ]
    }

@router.get("/monitoring-configs")
async def get_monitoring_configs():
    """Get available monitoring configurations for trend performance"""
    return {
        "monitoring_configs": [
            {
                "id": "real_time",
                "name": "Real-Time Monitoring",
                "description": "Monitor trends in real-time",
                "frequency": "continuous",
                "metrics": ["trend_velocity", "engagement_rate", "reach_growth", "sentiment_score"],
                "alerts": ["trend_spikes", "engagement_drops", "negative_sentiment"],
                "best_for": ["viral_content", "newsjacking", "crisis_management"]
            },
            {
                "id": "daily",
                "name": "Daily Monitoring",
                "description": "Monitor trends on a daily basis",
                "frequency": "daily",
                "metrics": ["daily_engagement", "trend_momentum", "audience_growth", "content_performance"],
                "alerts": ["performance_changes", "trend_shifts", "audience_changes"],
                "best_for": ["regular_content", "social_media_management", "audience_engagement"]
            },
            {
                "id": "weekly",
                "name": "Weekly Monitoring",
                "description": "Monitor trends on a weekly basis",
                "frequency": "weekly",
                "metrics": ["weekly_performance", "trend_analysis", "competitive_position", "strategy_effectiveness"],
                "alerts": ["strategy_changes", "competitive_threats", "opportunity_alerts"],
                "best_for": ["strategic_planning", "competitive_analysis", "long_term_trends"]
            },
            {
                "id": "monthly",
                "name": "Monthly Monitoring",
                "description": "Monitor trends on a monthly basis",
                "frequency": "monthly",
                "metrics": ["monthly_performance", "trend_evolution", "market_position", "roi_analysis"],
                "alerts": ["market_changes", "trend_declines", "strategy_recommendations"],
                "best_for": ["strategic_review", "market_analysis", "roi_optimization"]
            }
        ]
    }
