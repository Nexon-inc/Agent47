from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, List, Any

from ..database import get_db
from ..services.performance_forecasting_service import PerformanceForecastingService

router = APIRouter(prefix="/performance-forecasting", tags=["Campaign Performance Forecasting"])

@router.post("/predict-performance")
def predict_campaign_performance(campaign_data: Dict[str, Any], forecast_horizon: str = "30d", 
                               db: Session = Depends(get_db)):
    service = PerformanceForecastingService(db)
    return service.predict_campaign_performance(campaign_data, forecast_horizon)

@router.post("/forecast-model")
def create_forecast_model(model_type: str, training_data: Dict[str, Any], 
                         db: Session = Depends(get_db)):
    service = PerformanceForecastingService(db)
    return service.create_forecast_model(model_type, training_data)

@router.post("/historical-analysis")
def analyze_historical_performance(historical_data: List[Dict[str, Any]], analysis_period: str, 
                                 db: Session = Depends(get_db)):
    service = PerformanceForecastingService(db)
    return service.analyze_historical_performance(historical_data, analysis_period)

@router.get("/analytics")
def get_forecasting_analytics(timeframe: str = "30d", db: Session = Depends(get_db)):
    service = PerformanceForecastingService(db)
    return service.get_forecasting_analytics(timeframe)
