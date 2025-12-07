from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List
from pydantic import BaseModel, Field

from ..database import get_joe_database
# We'll import the TrendForecastingService lazily inside the dependency to avoid
# importing a potentially large module at import-time (and to work around
# previously corrupted files during repair).


router = APIRouter(prefix="/trend-forecasting", tags=["Trend Forecasting"])

class TrendForecastRequest(BaseModel):
    category: str = Field(..., description="Category to forecast trends for")
    timeframe: str = Field(default="6m", description="Forecast timeframe")
    confidence_level: float = Field(default=0.8, description="Confidence level for predictions")

# Dependency
async def get_trend_forecasting_service():
    from ..services.trend_forecasting_service import TrendForecastingService as _TFS

    service = _TFS()
    await service.initialize()
    return service

@router.post("/forecast")
async def forecast_trends(
    request: TrendForecastRequest,
    service = Depends(get_trend_forecasting_service)
):
    """Forecast trends for a specific category"""
    try:
        result = await service.forecast_trends(
            user_id=1,  # TODO: Get from authentication
            category=request.category,
            timeframe=request.timeframe,
            confidence_level=request.confidence_level
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["forecast"],
                "message": f"Trend forecast generated for {request.category}"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Trend forecasting failed: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to forecast trends: {str(e)}"
        )

@router.get("/accuracy")
async def get_forecast_accuracy(
    forecast_id: int = None,
    service = Depends(get_trend_forecasting_service)
):
    """Get accuracy of previous forecasts"""
    try:
        result = await service.get_forecast_accuracy(
            user_id=1,  # TODO: Get from authentication
            forecast_id=forecast_id
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["accuracy_data"],
                "message": "Forecast accuracy data retrieved"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get forecast accuracy: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get forecast accuracy: {str(e)}"
        )

@router.get("/models")
async def get_forecasting_models(service = Depends(get_trend_forecasting_service)):
    """Get available forecasting models"""
    models = [
        {
            "id": "arima",
            "name": "ARIMA Model",
            "description": "Autoregressive Integrated Moving Average",
            "best_for": "Time series forecasting",
            "accuracy": 85
        },
        {
            "id": "prophet",
            "name": "Prophet Model",
            "description": "Facebook's forecasting tool",
            "best_for": "Seasonal trends",
            "accuracy": 82
        },
        {
            "id": "lstm",
            "name": "LSTM Neural Network",
            "description": "Long Short-Term Memory",
            "best_for": "Complex patterns",
            "accuracy": 88
        },
        {
            "id": "ensemble",
            "name": "Ensemble Model",
            "description": "Combination of multiple models",
            "best_for": "High accuracy predictions",
            "accuracy": 92
        }
    ]
    
    return {
        "status": "success",
        "data": models,
        "message": f"Retrieved {len(models)} forecasting models"
    }
