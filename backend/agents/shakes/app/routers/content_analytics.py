from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from ..services.content_analytics_service import ContentAnalyticsService
from ..models import ContentType, PlatformType, ToneType
from ..database import get_shakes_database

router = APIRouter(prefix="/content-analytics", tags=["Content Analytics"])

# Pydantic Models
class TrackContentPerformanceRequest(BaseModel):
    content_piece_id: int = Field(..., description="Content piece ID")
    platform: str = Field(..., description="Platform name")
    metrics: Dict[str, Any] = Field(..., description="Performance metrics")

class TrackContentPerformanceResponse(BaseModel):
    success: bool
    analytics_id: int
    content_piece_id: int
    platform: str
    metrics: Dict[str, Any]
    performance_analysis: str
    timestamp: str

class GetPerformanceSummaryRequest(BaseModel):
    user_id: int = Field(..., description="User ID")
    date_range_days: int = Field(default=30, description="Date range in days")
    platform: Optional[str] = Field(default=None, description="Platform filter")

class CompareContentPerformanceRequest(BaseModel):
    content_piece_ids: List[int] = Field(..., description="Content piece IDs to compare")
    comparison_metrics: List[str] = Field(..., description="Metrics to compare")

# Dependency
async def get_content_analytics_service() -> ContentAnalyticsService:
    """Get content analytics service instance"""
    service = ContentAnalyticsService()
    await service.initialize()
    return service

# Endpoints
@router.post("/track-performance", response_model=TrackContentPerformanceResponse, status_code=201)
async def track_content_performance(
    request: TrackContentPerformanceRequest,
    service: ContentAnalyticsService = Depends(get_content_analytics_service)
):
    """Track content performance metrics"""
    try:
        result = await service.track_content_performance(
            content_piece_id=request.content_piece_id,
            platform=request.platform,
            metrics=request.metrics
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to track content performance")
            )
        
        return TrackContentPerformanceResponse(**result)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Content performance tracking failed: {str(e)}"
        )

@router.get("/analytics/{content_piece_id}", response_model=Dict[str, Any], status_code=200)
async def get_content_analytics(
    content_piece_id: int,
    platform: Optional[str] = Query(default=None, description="Platform filter"),
    service: ContentAnalyticsService = Depends(get_content_analytics_service)
):
    """Get analytics for specific content piece"""
    try:
        result = await service.get_content_analytics(
            content_piece_id=content_piece_id,
            platform=platform
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to get content analytics")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Content analytics retrieval failed: {str(e)}"
        )

@router.post("/performance-summary", response_model=Dict[str, Any], status_code=200)
async def get_performance_summary(
    request: GetPerformanceSummaryRequest,
    service: ContentAnalyticsService = Depends(get_content_analytics_service)
):
    """Get performance summary for user's content"""
    try:
        result = await service.get_performance_summary(
            user_id=request.user_id,
            date_range_days=request.date_range_days,
            platform=request.platform
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to get performance summary")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Performance summary retrieval failed: {str(e)}"
        )

@router.post("/compare-performance", response_model=Dict[str, Any], status_code=200)
async def compare_content_performance(
    request: CompareContentPerformanceRequest,
    service: ContentAnalyticsService = Depends(get_content_analytics_service)
):
    """Compare performance of multiple content pieces"""
    try:
        result = await service.compare_content_performance(
            content_piece_ids=request.content_piece_ids,
            comparison_metrics=request.comparison_metrics
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to compare content performance")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Content performance comparison failed: {str(e)}"
        )

@router.get("/performance-metrics")
async def get_performance_metrics():
    """Get available performance metrics for tracking"""
    return {
        "performance_metrics": [
            {
                "id": "views",
                "name": "Views",
                "description": "Number of times content was viewed",
                "category": "reach",
                "importance": "high",
                "platforms": ["all"],
                "measurement": "count"
            },
            {
                "id": "likes",
                "name": "Likes",
                "description": "Number of likes or positive reactions",
                "category": "engagement",
                "importance": "high",
                "platforms": ["social_media", "blog"],
                "measurement": "count"
            },
            {
                "id": "shares",
                "name": "Shares",
                "description": "Number of times content was shared",
                "category": "engagement",
                "importance": "high",
                "platforms": ["social_media", "blog"],
                "measurement": "count"
            },
            {
                "id": "comments",
                "name": "Comments",
                "description": "Number of comments or responses",
                "category": "engagement",
                "importance": "medium",
                "platforms": ["social_media", "blog"],
                "measurement": "count"
            },
            {
                "id": "clicks",
                "name": "Clicks",
                "description": "Number of clicks on content or links",
                "category": "engagement",
                "importance": "high",
                "platforms": ["all"],
                "measurement": "count"
            },
            {
                "id": "engagement_rate",
                "name": "Engagement Rate",
                "description": "Percentage of engaged users",
                "category": "engagement",
                "importance": "high",
                "platforms": ["social_media", "blog"],
                "measurement": "percentage"
            },
            {
                "id": "reach",
                "name": "Reach",
                "description": "Number of unique users who saw content",
                "category": "reach",
                "importance": "medium",
                "platforms": ["social_media"],
                "measurement": "count"
            },
            {
                "id": "impressions",
                "name": "Impressions",
                "description": "Number of times content was displayed",
                "category": "reach",
                "importance": "medium",
                "platforms": ["social_media", "advertising"],
                "measurement": "count"
            }
        ]
    }

@router.get("/analytics-insights")
async def get_analytics_insights():
    """Get insights and recommendations for content analytics"""
    return {
        "analytics_insights": [
            {
                "category": "performance_analysis",
                "title": "Performance Analysis",
                "insights": [
                    "Track engagement rate trends over time",
                    "Compare performance across different content types",
                    "Identify peak performance periods",
                    "Analyze audience behavior patterns",
                    "Monitor content lifecycle performance"
                ]
            },
            {
                "category": "optimization_opportunities",
                "title": "Optimization Opportunities",
                "insights": [
                    "Identify underperforming content for improvement",
                    "Analyze successful content patterns",
                    "Optimize posting times based on engagement data",
                    "Improve content based on audience feedback",
                    "Test different content formats and styles"
                ]
            },
            {
                "category": "audience_insights",
                "title": "Audience Insights",
                "insights": [
                    "Understand audience preferences and behavior",
                    "Identify most engaged audience segments",
                    "Analyze content consumption patterns",
                    "Track audience growth and retention",
                    "Optimize content for target demographics"
                ]
            },
            {
                "category": "content_strategy",
                "title": "Content Strategy",
                "insights": [
                    "Develop data-driven content strategies",
                    "Plan content based on performance trends",
                    "Align content with audience interests",
                    "Optimize content mix for better engagement",
                    "Create content calendars based on performance data"
                ]
            }
        ]
    }

@router.get("/benchmarking-guidelines")
async def get_benchmarking_guidelines():
    """Get guidelines for content performance benchmarking"""
    return {
        "benchmarking_guidelines": [
            {
                "category": "industry_benchmarks",
                "title": "Industry Benchmarks",
                "guidelines": [
                    "Compare performance against industry averages",
                    "Use industry-specific metrics and standards",
                    "Consider seasonal variations in performance",
                    "Account for platform-specific differences",
                    "Update benchmarks regularly"
                ]
            },
            {
                "category": "internal_benchmarks",
                "title": "Internal Benchmarks",
                "guidelines": [
                    "Establish baseline performance metrics",
                    "Track performance improvements over time",
                    "Compare similar content types",
                    "Monitor progress against goals",
                    "Identify best-performing content patterns"
                ]
            },
            {
                "category": "competitive_analysis",
                "title": "Competitive Analysis",
                "guidelines": [
                    "Monitor competitor content performance",
                    "Identify competitive advantages",
                    "Learn from successful competitor strategies",
                    "Differentiate content from competitors",
                    "Stay updated on industry trends"
                ]
            },
            {
                "category": "performance_goals",
                "title": "Performance Goals",
                "guidelines": [
                    "Set realistic and achievable goals",
                    "Define clear success metrics",
                    "Track progress toward goals",
                    "Adjust goals based on performance",
                    "Celebrate achievements and milestones"
                ]
            }
        ]
    }
