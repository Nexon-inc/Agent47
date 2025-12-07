from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
from ..services.content_remix_service import ContentRemixService
from ..models import ContentType, PlatformType, ToneType
from ..database import get_shakes_database

router = APIRouter(prefix="/content-remix", tags=["Content Remix"])

# Pydantic Models
class RemixContentRequest(BaseModel):
    source_content_id: int = Field(..., description="Source content ID")
    target_formats: List[str] = Field(..., description="Target formats")
    remix_strategy: str = Field(..., description="Remix strategy")
    customization_options: Dict[str, Any] = Field(default={}, description="Customization options")

class ScheduleRemixAutomationRequest(BaseModel):
    content_piece_id: int = Field(..., description="Content piece ID")
    remix_schedule: Dict[str, Any] = Field(..., description="Remix schedule")
    automation_rules: List[Dict[str, Any]] = Field(..., description="Automation rules")

class AnalyzeRemixPerformanceRequest(BaseModel):
    remix_id: int = Field(..., description="Remix ID")
    analysis_period_days: int = Field(default=30, description="Analysis period in days")
    performance_metrics: List[str] = Field(default=[], description="Performance metrics")

class OptimizeRemixStrategyRequest(BaseModel):
    content_piece_id: int = Field(..., description="Content piece ID")
    current_remixes: List[Dict[str, Any]] = Field(..., description="Current remixes")
    optimization_goals: List[str] = Field(..., description="Optimization goals")

# Dependency
async def get_content_remix_service() -> ContentRemixService:
    """Get content remix service instance"""
    service = ContentRemixService()
    await service.initialize()
    return service

# Endpoints
@router.post("/remix", response_model=Dict[str, Any], status_code=201)
async def remix_content(
    request: RemixContentRequest,
    service: ContentRemixService = Depends(get_content_remix_service)
):
    """Remix content into different formats and platforms"""
    try:
        result = await service.remix_content(
            source_content_id=request.source_content_id,
            target_formats=request.target_formats,
            remix_strategy=request.remix_strategy,
            customization_options=request.customization_options
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to remix content")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Content remixing failed: {str(e)}"
        )

@router.post("/schedule-automation", response_model=Dict[str, Any], status_code=201)
async def schedule_remix_automation(
    request: ScheduleRemixAutomationRequest,
    service: ContentRemixService = Depends(get_content_remix_service)
):
    """Schedule automated content remixing"""
    try:
        result = await service.schedule_remix_automation(
            content_piece_id=request.content_piece_id,
            remix_schedule=request.remix_schedule,
            automation_rules=request.automation_rules
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to schedule remix automation")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Remix automation scheduling failed: {str(e)}"
        )

@router.post("/analyze-performance", response_model=Dict[str, Any], status_code=200)
async def analyze_remix_performance(
    request: AnalyzeRemixPerformanceRequest,
    service: ContentRemixService = Depends(get_content_remix_service)
):
    """Analyze performance of remixed content"""
    try:
        result = await service.analyze_remix_performance(
            remix_id=request.remix_id,
            analysis_period_days=request.analysis_period_days,
            performance_metrics=request.performance_metrics
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to analyze remix performance")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Remix performance analysis failed: {str(e)}"
        )

@router.post("/optimize-strategy", response_model=Dict[str, Any], status_code=200)
async def optimize_remix_strategy(
    request: OptimizeRemixStrategyRequest,
    service: ContentRemixService = Depends(get_content_remix_service)
):
    """Optimize remix strategy based on performance data"""
    try:
        result = await service.optimize_remix_strategy(
            content_piece_id=request.content_piece_id,
            current_remixes=request.current_remixes,
            optimization_goals=request.optimization_goals
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to optimize remix strategy")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Remix strategy optimization failed: {str(e)}"
        )

@router.get("/target-formats")
async def get_target_formats():
    """Get available target formats for content remixing"""
    return {
        "target_formats": [
            {
                "id": "blog_post",
                "name": "Blog Post",
                "description": "Long-form written content for blogs",
                "characteristics": ["detailed", "informative", "seo_optimized", "structured"],
                "best_for": ["educational_content", "thought_leadership", "in_depth_analysis"],
                "platforms": ["wordpress", "medium", "company_blog", "linkedin_articles"]
            },
            {
                "id": "social_media_post",
                "name": "Social Media Post",
                "description": "Short-form content for social platforms",
                "characteristics": ["concise", "engaging", "visual", "shareable"],
                "best_for": ["quick_updates", "announcements", "engagement", "viral_content"],
                "platforms": ["twitter", "facebook", "instagram", "linkedin", "tiktok"]
            },
            {
                "id": "email_newsletter",
                "name": "Email Newsletter",
                "description": "Email marketing content",
                "characteristics": ["personal", "direct", "action_oriented", "segmented"],
                "best_for": ["customer_communication", "marketing_campaigns", "updates", "nurturing"],
                "platforms": ["mailchimp", "constant_contact", "hubspot", "sendgrid"]
            },
            {
                "id": "video_script",
                "name": "Video Script",
                "description": "Script for video content",
                "characteristics": ["visual", "narrative", "engaging", "timed"],
                "best_for": ["tutorials", "presentations", "storytelling", "marketing_videos"],
                "platforms": ["youtube", "vimeo", "tiktok", "instagram_reels"]
            },
            {
                "id": "podcast_script",
                "name": "Podcast Script",
                "description": "Script for audio content",
                "characteristics": ["conversational", "audio_focused", "structured", "engaging"],
                "best_for": ["interviews", "discussions", "storytelling", "educational_content"],
                "platforms": ["spotify", "apple_podcasts", "google_podcasts", "anchor"]
            },
            {
                "id": "infographic",
                "name": "Infographic",
                "description": "Visual representation of information",
                "characteristics": ["visual", "data_driven", "shareable", "informative"],
                "best_for": ["data_visualization", "statistics", "process_explanation", "comparisons"],
                "platforms": ["pinterest", "linkedin", "twitter", "company_website"]
            }
        ]
    }

@router.get("/remix-strategies")
async def get_remix_strategies():
    """Get available remix strategies for content"""
    return {
        "remix_strategies": [
            {
                "id": "direct_adaptation",
                "name": "Direct Adaptation",
                "description": "Direct translation of content to new format",
                "approach": "maintain_core_message",
                "changes": ["format_specific", "platform_optimization", "length_adjustment"],
                "best_for": ["consistent_messaging", "brand_consistency", "quick_remixing"],
                "effort_level": "low"
            },
            {
                "id": "creative_reinterpretation",
                "name": "Creative Reinterpretation",
                "description": "Creative reimagining of content for new format",
                "approach": "reinterpret_core_ideas",
                "changes": ["creative_approach", "format_innovation", "audience_adaptation"],
                "best_for": ["creative_content", "entertainment", "viral_potential"],
                "effort_level": "high"
            },
            {
                "id": "audience_specific",
                "name": "Audience-Specific",
                "description": "Tailored remix for specific audience segments",
                "approach": "audience_customization",
                "changes": ["tone_adjustment", "content_focus", "cultural_adaptation"],
                "best_for": ["targeted_marketing", "segmented_audiences", "personalization"],
                "effort_level": "medium"
            },
            {
                "id": "platform_optimized",
                "name": "Platform-Optimized",
                "description": "Optimized for specific platform requirements",
                "approach": "platform_native",
                "changes": ["format_requirements", "algorithm_optimization", "platform_features"],
                "best_for": ["platform_specific_content", "algorithm_optimization", "native_formatting"],
                "effort_level": "medium"
            },
            {
                "id": "trend_adapted",
                "name": "Trend-Adapted",
                "description": "Adapted to current trends and topics",
                "approach": "trend_integration",
                "changes": ["trending_topics", "current_events", "seasonal_content"],
                "best_for": ["trending_content", "seasonal_campaigns", "newsjacking"],
                "effort_level": "medium"
            }
        ]
    }

@router.get("/automation-rules")
async def get_automation_rules():
    """Get available automation rules for content remixing"""
    return {
        "automation_rules": [
            {
                "id": "time_based",
                "name": "Time-Based",
                "description": "Automated remixing based on time triggers",
                "triggers": ["daily", "weekly", "monthly", "custom_schedule"],
                "actions": ["auto_remix", "schedule_posting", "performance_check"],
                "best_for": ["regular_content", "newsletters", "social_media_updates"]
            },
            {
                "id": "performance_based",
                "name": "Performance-Based",
                "description": "Automated remixing based on performance metrics",
                "triggers": ["high_engagement", "low_performance", "viral_threshold"],
                "actions": ["create_variations", "optimize_content", "expand_reach"],
                "best_for": ["performance_optimization", "viral_content", "engagement_boost"]
            },
            {
                "id": "audience_based",
                "name": "Audience-Based",
                "description": "Automated remixing based on audience behavior",
                "triggers": ["audience_growth", "engagement_patterns", "demographic_changes"],
                "actions": ["audience_adaptation", "content_personalization", "format_optimization"],
                "best_for": ["audience_growth", "personalization", "demographic_targeting"]
            },
            {
                "id": "trend_based",
                "name": "Trend-Based",
                "description": "Automated remixing based on trending topics",
                "triggers": ["trending_topics", "seasonal_events", "industry_news"],
                "actions": ["trend_integration", "content_adaptation", "timely_posting"],
                "best_for": ["trending_content", "newsjacking", "seasonal_campaigns"]
            },
            {
                "id": "cross_platform",
                "name": "Cross-Platform",
                "description": "Automated remixing across multiple platforms",
                "triggers": ["platform_specific_requirements", "audience_preferences", "content_performance"],
                "actions": ["multi_platform_remix", "platform_optimization", "synchronized_posting"],
                "best_for": ["multi_platform_strategy", "brand_consistency", "reach_maximization"]
            }
        ]
    }

@router.get("/performance-metrics")
async def get_performance_metrics():
    """Get available performance metrics for remixed content"""
    return {
        "performance_metrics": [
            {
                "id": "engagement_metrics",
                "name": "Engagement Metrics",
                "description": "Metrics related to user engagement",
                "metrics": ["likes", "comments", "shares", "saves", "click_through_rate"],
                "measurement": "count_and_percentage",
                "importance": "high"
            },
            {
                "id": "reach_metrics",
                "name": "Reach Metrics",
                "description": "Metrics related to content reach",
                "metrics": ["impressions", "reach", "unique_viewers", "follower_growth"],
                "measurement": "count_and_percentage",
                "importance": "high"
            },
            {
                "id": "conversion_metrics",
                "name": "Conversion Metrics",
                "description": "Metrics related to conversions and actions",
                "metrics": ["conversion_rate", "sign_ups", "purchases", "downloads", "leads"],
                "measurement": "count_and_percentage",
                "importance": "high"
            },
            {
                "id": "quality_metrics",
                "name": "Quality Metrics",
                "description": "Metrics related to content quality",
                "metrics": ["completion_rate", "time_spent", "bounce_rate", "return_visits"],
                "measurement": "percentage_and_duration",
                "importance": "medium"
            },
            {
                "id": "brand_metrics",
                "name": "Brand Metrics",
                "description": "Metrics related to brand performance",
                "metrics": ["brand_mentions", "sentiment_score", "brand_recall", "brand_awareness"],
                "measurement": "score_and_count",
                "importance": "medium"
            }
        ]
    }

@router.get("/optimization-goals")
async def get_optimization_goals():
    """Get available optimization goals for remix strategy"""
    return {
        "optimization_goals": [
            {
                "id": "engagement_optimization",
                "name": "Engagement Optimization",
                "description": "Optimize for higher engagement rates",
                "target_metrics": ["engagement_rate", "interaction_rate", "time_spent"],
                "strategies": ["content_improvement", "format_optimization", "timing_optimization"],
                "priority": "high"
            },
            {
                "id": "reach_optimization",
                "name": "Reach Optimization",
                "description": "Optimize for broader content reach",
                "target_metrics": ["impressions", "reach", "unique_viewers", "follower_growth"],
                "strategies": ["platform_expansion", "content_amplification", "audience_targeting"],
                "priority": "high"
            },
            {
                "id": "conversion_optimization",
                "name": "Conversion Optimization",
                "description": "Optimize for higher conversion rates",
                "target_metrics": ["conversion_rate", "lead_generation", "sales", "sign_ups"],
                "strategies": ["cta_optimization", "content_personalization", "funnel_optimization"],
                "priority": "high"
            },
            {
                "id": "efficiency_optimization",
                "name": "Efficiency Optimization",
                "description": "Optimize for content creation efficiency",
                "target_metrics": ["creation_time", "resource_usage", "automation_rate"],
                "strategies": ["automation_improvement", "workflow_optimization", "resource_optimization"],
                "priority": "medium"
            },
            {
                "id": "quality_optimization",
                "name": "Quality Optimization",
                "description": "Optimize for content quality and consistency",
                "target_metrics": ["quality_score", "consistency_rating", "brand_alignment"],
                "strategies": ["quality_standards", "brand_guidelines", "content_review"],
                "priority": "medium"
            }
        ]
    }
