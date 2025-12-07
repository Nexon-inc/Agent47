from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from ..services.predictive_analytics_service import PredictiveAnalyticsService
from ..models import TicketCategory, SupportChannel

router = APIRouter()

# Pydantic models for request/response
class ForecastRequest(BaseModel):
    days_ahead: int = 30
    category: Optional[str] = None
    channel: Optional[str] = None

class ChurnAnalysisRequest(BaseModel):
    customer_id: int
    analysis_period_days: int = 90

class IssueDetectionRequest(BaseModel):
    analysis_period_days: int = 7

class BenchmarkRequest(BaseModel):
    metrics: Optional[List[str]] = None

# Dependency
async def get_predictive_analytics_service() -> PredictiveAnalyticsService:
    service = PredictiveAnalyticsService()
    await service.initialize()
    return service

@router.post("/forecast/ticket-volume", response_model=Dict[str, Any])
async def forecast_ticket_volume(
    request: ForecastRequest,
    service: PredictiveAnalyticsService = Depends(get_predictive_analytics_service)
):
    """Forecast ticket volume for the next N days"""
    try:
        result = await service.forecast_ticket_volume(
            days_ahead=request.days_ahead,
            category=TicketCategory(request.category) if request.category else None,
            channel=SupportChannel(request.channel) if request.channel else None
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/predict/customer-churn", response_model=Dict[str, Any])
async def predict_customer_churn(
    request: ChurnAnalysisRequest,
    service: PredictiveAnalyticsService = Depends(get_predictive_analytics_service)
):
    """Predict customer churn risk"""
    try:
        result = await service.predict_customer_churn(
            customer_id=request.customer_id,
            analysis_period_days=request.analysis_period_days
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/detect/potential-issues", response_model=Dict[str, Any])
async def detect_potential_issues(
    request: IssueDetectionRequest,
    service: PredictiveAnalyticsService = Depends(get_predictive_analytics_service)
):
    """Detect potential issues before they become widespread"""
    try:
        result = await service.detect_potential_issues(
            analysis_period_days=request.analysis_period_days
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/benchmark/industry", response_model=Dict[str, Any])
async def benchmark_against_industry(
    request: BenchmarkRequest,
    service: PredictiveAnalyticsService = Depends(get_predictive_analytics_service)
):
    """Benchmark support performance against industry standards"""
    try:
        result = await service.benchmark_against_industry(
            metrics=request.metrics
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/insights/summary", response_model=Dict[str, Any])
async def get_predictive_insights_summary(
    service: PredictiveAnalyticsService = Depends(get_predictive_analytics_service)
):
    """Get summary of all predictive insights"""
    try:
        # Get recent forecasts
        forecast_result = await service.forecast_ticket_volume(days_ahead=7)
        
        # Get recent issue detection
        issues_result = await service.detect_potential_issues(analysis_period_days=7)
        
        # Get industry benchmark
        benchmark_result = await service.benchmark_against_industry()
        
        summary = {
            "success": True,
            "insights_summary": {
                "ticket_forecast": {
                    "available": forecast_result["success"],
                    "next_7_days": forecast_result.get("forecast", []) if forecast_result["success"] else []
                },
                "potential_issues": {
                    "available": issues_result["success"],
                    "issues_found": issues_result.get("potential_issues", []) if issues_result["success"] else []
                },
                "industry_benchmark": {
                    "available": benchmark_result["success"],
                    "overall_performance": benchmark_result.get("benchmark_results", {}) if benchmark_result["success"] else {}
                }
            },
            "last_updated": "2024-01-01T00:00:00Z"  # This would be dynamic
        }
        
        return summary
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
