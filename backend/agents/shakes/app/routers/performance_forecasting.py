from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from ..services.performance_forecasting_service import PerformanceForecastingService
from ..models import ContentType, PlatformType, ToneType
from ..database import get_shakes_database

router = APIRouter(prefix="/performance-forecasting", tags=["Performance Forecasting"])

# Pydantic Models
class ForecastContentPerformanceRequest(BaseModel):
    content_piece_id: int = Field(..., description="Content piece ID")
    forecast_period_days: int = Field(default=30, description="Forecast period in days")
    forecast_metrics: List[str] = Field(default=[], description="Metrics to forecast")

class ForecastCampaignPerformanceRequest(BaseModel):
    user_id: int = Field(..., description="User ID")
    campaign_parameters: Dict[str, Any] = Field(..., description="Campaign parameters")
    forecast_period_days: int = Field(default=30, description="Forecast period in days")

class PredictOptimalPostingTimesRequest(BaseModel):
    user_id: int = Field(..., description="User ID")
    platform: str = Field(..., description="Target platform")
    content_type: str = Field(..., description="Content type")
    target_audience: str = Field(..., description="Target audience")

class ForecastContentTrendsRequest(BaseModel):
    industry: str = Field(..., description="Industry")
    forecast_period_days: int = Field(default=90, description="Forecast period in days")
    trend_categories: List[str] = Field(default=[], description="Trend categories to forecast")

# Dependency
async def get_performance_forecasting_service() -> PerformanceForecastingService:
    """Get performance forecasting service instance"""
    service = PerformanceForecastingService()
    await service.initialize()
    return service

# Endpoints
@router.post("/forecast-content-performance", response_model=Dict[str, Any], status_code=200)
async def forecast_content_performance(
    request: ForecastContentPerformanceRequest,
    service: PerformanceForecastingService = Depends(get_performance_forecasting_service)
):
    """Forecast performance for specific content piece"""
    try:
        result = await service.forecast_content_performance(
            content_piece_id=request.content_piece_id,
            forecast_period_days=request.forecast_period_days,
            forecast_metrics=request.forecast_metrics
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to forecast content performance")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Content performance forecasting failed: {str(e)}"
        )

@router.post("/forecast-campaign-performance", response_model=Dict[str, Any], status_code=200)
async def forecast_campaign_performance(
    request: ForecastCampaignPerformanceRequest,
    service: PerformanceForecastingService = Depends(get_performance_forecasting_service)
):
    """Forecast performance for content campaign"""
    try:
        result = await service.forecast_campaign_performance(
            user_id=request.user_id,
            campaign_parameters=request.campaign_parameters,
            forecast_period_days=request.forecast_period_days
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to forecast campaign performance")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Campaign performance forecasting failed: {str(e)}"
        )

@router.post("/predict-optimal-posting-times", response_model=Dict[str, Any], status_code=200)
async def predict_optimal_posting_times(
    request: PredictOptimalPostingTimesRequest,
    service: PerformanceForecastingService = Depends(get_performance_forecasting_service)
):
    """Predict optimal posting times for content"""
    try:
        result = await service.predict_optimal_posting_times(
            user_id=request.user_id,
            platform=request.platform,
            content_type=request.content_type,
            target_audience=request.target_audience
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to predict optimal posting times")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Optimal posting time prediction failed: {str(e)}"
        )

@router.post("/forecast-content-trends", response_model=Dict[str, Any], status_code=200)
async def forecast_content_trends(
    request: ForecastContentTrendsRequest,
    service: PerformanceForecastingService = Depends(get_performance_forecasting_service)
):
    """Forecast content trends for industry"""
    try:
        result = await service.forecast_content_trends(
            industry=request.industry,
            forecast_period_days=request.forecast_period_days,
            trend_categories=request.trend_categories
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to forecast content trends")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Content trend forecasting failed: {str(e)}"
        )

@router.get("/forecast-metrics")
async def get_forecast_metrics():
    """Get available metrics for performance forecasting"""
    return {
        "forecast_metrics": [
            {
                "id": "views",
                "name": "Views",
                "description": "Predicted number of content views",
                "category": "reach",
                "forecast_accuracy": "high",
                "factors": ["content_type", "platform", "audience", "timing"]
            },
            {
                "id": "likes",
                "name": "Likes",
                "description": "Predicted number of likes or positive reactions",
                "category": "engagement",
                "forecast_accuracy": "medium",
                "factors": ["content_quality", "audience_engagement", "timing", "platform"]
            },
            {
                "id": "shares",
                "name": "Shares",
                "description": "Predicted number of content shares",
                "category": "engagement",
                "forecast_accuracy": "medium",
                "factors": ["content_virality", "audience_behavior", "platform", "timing"]
            },
            {
                "id": "comments",
                "name": "Comments",
                "description": "Predicted number of comments or responses",
                "category": "engagement",
                "forecast_accuracy": "low",
                "factors": ["content_controversy", "audience_engagement", "platform", "timing"]
            },
            {
                "id": "engagement_rate",
                "name": "Engagement Rate",
                "description": "Predicted engagement rate percentage",
                "category": "engagement",
                "forecast_accuracy": "high",
                "factors": ["content_quality", "audience_match", "platform", "timing"]
            },
            {
                "id": "reach",
                "name": "Reach",
                "description": "Predicted number of unique users reached",
                "category": "reach",
                "forecast_accuracy": "medium",
                "factors": ["platform_algorithm", "audience_size", "content_type", "timing"]
            }
        ]
    }

@router.get("/forecasting-methods")
async def get_forecasting_methods():
    """Get available forecasting methods and approaches"""
    return {
        "forecasting_methods": [
            {
                "id": "historical_analysis",
                "name": "Historical Analysis",
                "description": "Analyze historical performance data to predict future performance",
                "accuracy": "high",
                "best_for": ["established_content", "consistent_audience", "stable_platforms"],
                "limitations": ["requires_historical_data", "may_not_account_for_trends"]
            },
            {
                "id": "similar_content_comparison",
                "name": "Similar Content Comparison",
                "description": "Compare with similar content to predict performance",
                "accuracy": "medium",
                "best_for": ["new_content", "content_experimentation", "benchmarking"],
                "limitations": ["requires_similar_content", "may_not_account_for_differences"]
            },
            {
                "id": "audience_behavior_modeling",
                "name": "Audience Behavior Modeling",
                "description": "Model audience behavior to predict engagement",
                "accuracy": "medium",
                "best_for": ["audience_targeting", "engagement_optimization", "personalization"],
                "limitations": ["requires_audience_data", "behavior_may_change"]
            },
            {
                "id": "trend_analysis",
                "name": "Trend Analysis",
                "description": "Analyze industry and platform trends to predict performance",
                "accuracy": "low",
                "best_for": ["trending_topics", "seasonal_content", "industry_insights"],
                "limitations": ["trends_may_change", "difficult_to_predict_virality"]
            },
            {
                "id": "machine_learning_prediction",
                "name": "Machine Learning Prediction",
                "description": "Use ML models to predict performance based on multiple factors",
                "accuracy": "high",
                "best_for": ["complex_forecasting", "multi_factor_analysis", "accurate_predictions"],
                "limitations": ["requires_training_data", "model_complexity", "interpretability"]
            }
        ]
    }

@router.get("/forecasting-best-practices")
async def get_forecasting_best_practices():
    """Get best practices for content performance forecasting"""
    return {
        "forecasting_best_practices": [
            {
                "category": "data_quality",
                "title": "Data Quality",
                "practices": [
                    "Ensure historical data is accurate and complete",
                    "Clean and validate data before forecasting",
                    "Use sufficient data points for reliable predictions",
                    "Account for data gaps and anomalies",
                    "Regularly update and refresh data"
                ]
            },
            {
                "category": "forecast_accuracy",
                "title": "Forecast Accuracy",
                "practices": [
                    "Use multiple forecasting methods for comparison",
                    "Validate forecasts against actual performance",
                    "Adjust forecasts based on new information",
                    "Consider confidence intervals and uncertainty",
                    "Regularly review and improve forecasting models"
                ]
            },
            {
                "category": "context_consideration",
                "title": "Context Consideration",
                "practices": [
                    "Account for seasonal variations and trends",
                    "Consider external factors and events",
                    "Factor in platform algorithm changes",
                    "Include audience behavior changes",
                    "Consider competitive landscape shifts"
                ]
            },
            {
                "category": "forecast_application",
                "title": "Forecast Application",
                "practices": [
                    "Use forecasts to inform content strategy",
                    "Set realistic expectations based on predictions",
                    "Monitor actual performance against forecasts",
                    "Adjust strategies based on forecast accuracy",
                    "Learn from forecasting successes and failures"
                ]
            }
        ]
    }
