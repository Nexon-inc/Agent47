from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
from ..services.content_dna_service import ContentDNAService
from ..models import ContentType, PlatformType, ToneType
from ..database import get_shakes_database

router = APIRouter(prefix="/content-dna", tags=["Content DNA"])

# Pydantic Models
class AnalyzeContentDNARequest(BaseModel):
    user_id: int = Field(..., description="User ID")
    analysis_scope: str = Field(default="all", description="Analysis scope")
    time_period_days: int = Field(default=90, description="Time period in days")

class GenerateContentHeatmapRequest(BaseModel):
    user_id: int = Field(..., description="User ID")
    heatmap_type: str = Field(default="performance", description="Heatmap type")
    time_period_days: int = Field(default=30, description="Time period in days")

class IdentifyContentPatternsRequest(BaseModel):
    user_id: int = Field(..., description="User ID")
    pattern_types: List[str] = Field(default=[], description="Pattern types to identify")

class OptimizeContentDNARequest(BaseModel):
    user_id: int = Field(..., description="User ID")
    optimization_goals: List[str] = Field(..., description="Optimization goals")
    target_metrics: Dict[str, Any] = Field(..., description="Target metrics")

# Dependency
async def get_content_dna_service() -> ContentDNAService:
    """Get content DNA service instance"""
    service = ContentDNAService()
    await service.initialize()
    return service

# Endpoints
@router.post("/analyze", response_model=Dict[str, Any], status_code=200)
async def analyze_content_dna(
    request: AnalyzeContentDNARequest,
    service: ContentDNAService = Depends(get_content_dna_service)
):
    """Analyze content DNA for user's content portfolio"""
    try:
        result = await service.analyze_content_dna(
            user_id=request.user_id,
            analysis_scope=request.analysis_scope,
            time_period_days=request.time_period_days
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to analyze content DNA")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Content DNA analysis failed: {str(e)}"
        )

@router.post("/heatmap", response_model=Dict[str, Any], status_code=200)
async def generate_content_heatmap(
    request: GenerateContentHeatmapRequest,
    service: ContentDNAService = Depends(get_content_dna_service)
):
    """Generate content performance heatmap"""
    try:
        result = await service.generate_content_heatmap(
            user_id=request.user_id,
            heatmap_type=request.heatmap_type,
            time_period_days=request.time_period_days
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to generate content heatmap")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Content heatmap generation failed: {str(e)}"
        )

@router.post("/patterns", response_model=Dict[str, Any], status_code=200)
async def identify_content_patterns(
    request: IdentifyContentPatternsRequest,
    service: ContentDNAService = Depends(get_content_dna_service)
):
    """Identify patterns in user's content"""
    try:
        result = await service.identify_content_patterns(
            user_id=request.user_id,
            pattern_types=request.pattern_types
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to identify content patterns")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Content pattern identification failed: {str(e)}"
        )

@router.post("/optimize", response_model=Dict[str, Any], status_code=200)
async def optimize_content_dna(
    request: OptimizeContentDNARequest,
    service: ContentDNAService = Depends(get_content_dna_service)
):
    """Optimize content DNA based on goals and metrics"""
    try:
        result = await service.optimize_content_dna(
            user_id=request.user_id,
            optimization_goals=request.optimization_goals,
            target_metrics=request.target_metrics
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to optimize content DNA")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Content DNA optimization failed: {str(e)}"
        )

@router.get("/analysis-scopes")
async def get_analysis_scopes():
    """Get available analysis scopes for content DNA"""
    return {
        "analysis_scopes": [
            {
                "id": "all",
                "name": "All Content",
                "description": "Analyze all content in the specified time period",
                "best_for": ["comprehensive_analysis", "overall_insights", "portfolio_review"],
                "time_range": "flexible"
            },
            {
                "id": "recent",
                "name": "Recent Content",
                "description": "Analyze content from the last 30 days",
                "best_for": ["current_trends", "recent_performance", "quick_insights"],
                "time_range": "30_days"
            },
            {
                "id": "top_performing",
                "name": "Top Performing Content",
                "description": "Analyze only the best performing content",
                "best_for": ["success_patterns", "best_practices", "optimization_insights"],
                "time_range": "flexible"
            },
            {
                "id": "underperforming",
                "name": "Underperforming Content",
                "description": "Analyze content that needs improvement",
                "best_for": ["improvement_opportunities", "problem_identification", "optimization_focus"],
                "time_range": "flexible"
            }
        ]
    }

@router.get("/heatmap-types")
async def get_heatmap_types():
    """Get available heatmap types for content analysis"""
    return {
        "heatmap_types": [
            {
                "id": "performance",
                "name": "Performance Heatmap",
                "description": "Visualize content performance across different dimensions",
                "dimensions": ["time", "platform", "content_type", "engagement"],
                "best_for": ["performance_analysis", "trend_identification", "optimization_insights"]
            },
            {
                "id": "themes",
                "name": "Theme Heatmap",
                "description": "Visualize content themes and topic distribution",
                "dimensions": ["topics", "keywords", "categories", "sentiment"],
                "best_for": ["content_strategy", "theme_analysis", "audience_insights"]
            },
            {
                "id": "engagement",
                "name": "Engagement Heatmap",
                "description": "Visualize engagement patterns and user behavior",
                "dimensions": ["time", "platform", "audience", "interaction_type"],
                "best_for": ["engagement_analysis", "audience_behavior", "optimization_opportunities"]
            },
            {
                "id": "content_mix",
                "name": "Content Mix Heatmap",
                "description": "Visualize content type distribution and balance",
                "dimensions": ["content_type", "platform", "format", "purpose"],
                "best_for": ["content_planning", "balance_analysis", "strategy_optimization"]
            }
        ]
    }

@router.get("/pattern-types")
async def get_pattern_types():
    """Get available pattern types for content analysis"""
    return {
        "pattern_types": [
            {
                "id": "themes",
                "name": "Content Themes",
                "description": "Identify recurring themes and topics in content",
                "analysis_focus": ["topic_frequency", "theme_evolution", "content_categories"],
                "insights": ["popular_topics", "content_gaps", "theme_consistency"]
            },
            {
                "id": "tone",
                "name": "Tone and Voice",
                "description": "Analyze tone patterns and brand voice consistency",
                "analysis_focus": ["emotional_tone", "brand_voice", "communication_style"],
                "insights": ["tone_consistency", "voice_evolution", "audience_alignment"]
            },
            {
                "id": "format",
                "name": "Content Format",
                "description": "Analyze content format patterns and preferences",
                "analysis_focus": ["content_types", "format_distribution", "platform_optimization"],
                "insights": ["format_preferences", "platform_optimization", "content_strategy"]
            },
            {
                "id": "timing",
                "name": "Timing Patterns",
                "description": "Analyze content timing and scheduling patterns",
                "analysis_focus": ["posting_times", "frequency_patterns", "seasonal_trends"],
                "insights": ["optimal_timing", "frequency_optimization", "seasonal_opportunities"]
            },
            {
                "id": "performance",
                "name": "Performance Patterns",
                "description": "Analyze performance patterns and success factors",
                "analysis_focus": ["engagement_patterns", "success_factors", "performance_trends"],
                "insights": ["success_patterns", "optimization_opportunities", "performance_insights"]
            }
        ]
    }

@router.get("/optimization-goals")
async def get_optimization_goals():
    """Get available optimization goals for content DNA"""
    return {
        "optimization_goals": [
            {
                "id": "engagement",
                "name": "Increase Engagement",
                "description": "Optimize content to increase user engagement",
                "target_metrics": ["likes", "shares", "comments", "time_spent"],
                "strategies": ["content_optimization", "timing_improvement", "format_enhancement"]
            },
            {
                "id": "reach",
                "name": "Expand Reach",
                "description": "Optimize content to reach more audiences",
                "target_metrics": ["views", "impressions", "reach", "new_followers"],
                "strategies": ["content_variety", "platform_expansion", "audience_targeting"]
            },
            {
                "id": "conversion",
                "name": "Improve Conversion",
                "description": "Optimize content to drive conversions",
                "target_metrics": ["click_through_rate", "conversion_rate", "sales", "leads"],
                "strategies": ["cta_optimization", "content_personalization", "funnel_improvement"]
            },
            {
                "id": "brand_consistency",
                "name": "Enhance Brand Consistency",
                "description": "Optimize content for consistent brand voice",
                "target_metrics": ["brand_mention_sentiment", "voice_consistency_score", "brand_recognition"],
                "strategies": ["voice_standardization", "content_guidelines", "brand_alignment"]
            },
            {
                "id": "content_quality",
                "name": "Improve Content Quality",
                "description": "Optimize content for higher quality standards",
                "target_metrics": ["content_quality_score", "readability_score", "accuracy_score"],
                "strategies": ["content_enhancement", "fact_checking", "proofreading"]
            }
        ]
    }

@router.get("/dna-insights")
async def get_dna_insights():
    """Get insights and recommendations for content DNA analysis"""
    return {
        "dna_insights": [
            {
                "category": "content_analysis",
                "title": "Content Analysis Insights",
                "insights": [
                    "Identify your most successful content patterns",
                    "Analyze content theme distribution and gaps",
                    "Understand audience preferences and behavior",
                    "Track content performance trends over time",
                    "Optimize content mix for better engagement"
                ]
            },
            {
                "category": "performance_optimization",
                "title": "Performance Optimization",
                "insights": [
                    "Optimize content timing for maximum engagement",
                    "Improve content format based on performance data",
                    "Enhance content quality and consistency",
                    "Target content to specific audience segments",
                    "Implement data-driven content strategies"
                ]
            },
            {
                "category": "brand_development",
                "title": "Brand Development",
                "insights": [
                    "Maintain consistent brand voice across content",
                    "Develop unique content characteristics",
                    "Build recognizable content patterns",
                    "Enhance brand storytelling capabilities",
                    "Create distinctive content DNA"
                ]
            },
            {
                "category": "audience_engagement",
                "title": "Audience Engagement",
                "insights": [
                    "Understand audience content preferences",
                    "Optimize content for audience engagement",
                    "Develop audience-specific content strategies",
                    "Improve content personalization",
                    "Enhance audience connection and loyalty"
                ]
            }
        ]
    }
