from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
from datetime import datetime

from ..services.sales_forecasting_service import SalesForecastingService
from ..database import get_db

router = APIRouter(prefix="/sales-forecasting", tags=["Sales Forecasting"])
sales_forecasting_service = SalesForecastingService()

class SalesForecastRequest(BaseModel):
    brand_id: int
    forecast_period: str = "30d"
    forecast_type: str = "revenue"

class RevenueTrendsRequest(BaseModel):
    brand_id: int
    trend_period: str = "90d"

class PipelineForecastRequest(BaseModel):
    brand_id: int
    pipeline_id: Optional[int] = None

class ForecastHistoryRequest(BaseModel):
    brand_id: int
    limit: int = 10

@router.post("/generate-forecast")
async def generate_sales_forecast(request: SalesForecastRequest):
    """Generate sales forecast for specified period"""
    try:
        result = await sales_forecasting_service.generate_sales_forecast(
            brand_id=request.brand_id,
            forecast_period=request.forecast_period,
            forecast_type=request.forecast_type
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate sales forecast: {str(e)}")

@router.post("/predict-revenue-trends")
async def predict_revenue_trends(request: RevenueTrendsRequest):
    """Predict revenue trends and patterns"""
    try:
        result = await sales_forecasting_service.predict_revenue_trends(
            brand_id=request.brand_id,
            trend_period=request.trend_period
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to predict revenue trends: {str(e)}")

@router.post("/forecast-pipeline-performance")
async def forecast_pipeline_performance(request: PipelineForecastRequest):
    """Forecast pipeline performance and conversion rates"""
    try:
        result = await sales_forecasting_service.forecast_pipeline_performance(
            brand_id=request.brand_id,
            pipeline_id=request.pipeline_id
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to forecast pipeline performance: {str(e)}")

@router.get("/forecast-history")
async def get_forecast_history(
    brand_id: int,
    limit: int = 10
):
    """Get forecast history and accuracy"""
    try:
        result = await sales_forecasting_service.get_forecast_history(
            brand_id=brand_id,
            limit=limit
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get forecast history: {str(e)}")

@router.get("/forecast-metrics")
async def get_forecast_metrics(brand_id: int):
    """Get key forecasting metrics and KPIs"""
    try:
        # This would typically aggregate metrics from various forecasts
        return {
            "brand_id": brand_id,
            "metrics": {
                "total_forecasts": 15,
                "average_accuracy": 0.85,
                "forecast_confidence": 0.78,
                "revenue_prediction": 125000,
                "lead_prediction": 45,
                "deal_prediction": 12
            },
            "trends": {
                "revenue_trend": "increasing",
                "lead_trend": "stable",
                "conversion_trend": "improving"
            },
            "insights": [
                "Revenue forecast shows 15% growth potential",
                "EricLead generation is on track for targets",
                "Conversion rates improving month-over-month"
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get forecast metrics: {str(e)}")

@router.get("/forecast-comparison")
async def compare_forecasts(
    brand_id: int,
    forecast_period: str = "30d"
):
    """Compare actual vs forecasted performance"""
    try:
        # This would compare historical forecasts with actual results
        return {
            "brand_id": brand_id,
            "forecast_period": forecast_period,
            "comparison": {
                "revenue": {
                    "forecasted": 100000,
                    "actual": 95000,
                    "accuracy": 0.95,
                    "variance": -0.05
                },
                "leads": {
                    "forecasted": 50,
                    "actual": 48,
                    "accuracy": 0.96,
                    "variance": -0.04
                },
                "deals": {
                    "forecasted": 10,
                    "actual": 9,
                    "accuracy": 0.90,
                    "variance": -0.10
                }
            },
            "accuracy_insights": [
                "Revenue forecasts are highly accurate (95%)",
                "EricLead forecasts show consistent accuracy",
                "EricDeal forecasts need refinement for better accuracy"
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compare forecasts: {str(e)}")

@router.get("/forecast-scenarios")
async def get_forecast_scenarios(brand_id: int):
    """Get different forecast scenarios (best case, worst case, likely)"""
    try:
        return {
            "brand_id": brand_id,
            "scenarios": {
                "best_case": {
                    "revenue": 150000,
                    "leads": 60,
                    "deals": 15,
                    "probability": 0.25,
                    "assumptions": [
                        "Strong market conditions",
                        "High conversion rates",
                        "Increased marketing spend"
                    ]
                },
                "likely_case": {
                    "revenue": 125000,
                    "leads": 45,
                    "deals": 12,
                    "probability": 0.50,
                    "assumptions": [
                        "Normal market conditions",
                        "Average conversion rates",
                        "Standard marketing spend"
                    ]
                },
                "worst_case": {
                    "revenue": 100000,
                    "leads": 30,
                    "deals": 8,
                    "probability": 0.25,
                    "assumptions": [
                        "Economic downturn",
                        "Lower conversion rates",
                        "Reduced marketing spend"
                    ]
                }
            },
            "recommendations": [
                "Focus on likely case scenario for planning",
                "Prepare contingency plans for worst case",
                "Optimize for best case opportunities"
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get forecast scenarios: {str(e)}")

@router.get("/forecast-drivers")
async def get_forecast_drivers(brand_id: int):
    """Get key drivers affecting forecasts"""
    try:
        return {
            "brand_id": brand_id,
            "drivers": {
                "market_factors": [
                    {
                        "factor": "Market growth rate",
                        "impact": "high",
                        "trend": "positive",
                        "confidence": 0.8
                    },
                    {
                        "factor": "Competition intensity",
                        "impact": "medium",
                        "trend": "stable",
                        "confidence": 0.7
                    }
                ],
                "internal_factors": [
                    {
                        "factor": "Sales team performance",
                        "impact": "high",
                        "trend": "improving",
                        "confidence": 0.9
                    },
                    {
                        "factor": "Product adoption rate",
                        "impact": "medium",
                        "trend": "positive",
                        "confidence": 0.8
                    }
                ],
                "external_factors": [
                    {
                        "factor": "Economic conditions",
                        "impact": "medium",
                        "trend": "stable",
                        "confidence": 0.6
                    },
                    {
                        "factor": "Regulatory changes",
                        "impact": "low",
                        "trend": "stable",
                        "confidence": 0.5
                    }
                ]
            },
            "risk_factors": [
                "Market volatility",
                "Team turnover",
                "Product delays",
                "Economic uncertainty"
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get forecast drivers: {str(e)}")

@router.get("/forecast-calendar")
async def get_forecast_calendar(brand_id: int, year: int = 2024):
    """Get forecast calendar for the year"""
    try:
        return {
            "brand_id": brand_id,
            "year": year,
            "calendar": [
                {
                    "month": "January",
                    "revenue_forecast": 100000,
                    "lead_forecast": 40,
                    "deal_forecast": 10,
                    "confidence": 0.85
                },
                {
                    "month": "February",
                    "revenue_forecast": 110000,
                    "lead_forecast": 45,
                    "deal_forecast": 11,
                    "confidence": 0.80
                },
                {
                    "month": "March",
                    "revenue_forecast": 120000,
                    "lead_forecast": 50,
                    "deal_forecast": 12,
                    "confidence": 0.75
                }
            ],
            "quarterly_totals": {
                "Q1": {
                    "revenue": 330000,
                    "leads": 135,
                    "deals": 33
                },
                "Q2": {
                    "revenue": 360000,
                    "leads": 150,
                    "deals": 36
                },
                "Q3": {
                    "revenue": 390000,
                    "leads": 165,
                    "deals": 39
                },
                "Q4": {
                    "revenue": 420000,
                    "leads": 180,
                    "deals": 42
                }
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get forecast calendar: {str(e)}")

@router.get("/health")
async def health_check():
    """Health check for sales forecasting service"""
    return {
        "status": "healthy",
        "service": "sales_forecasting",
        "timestamp": datetime.now().isoformat()
    }
