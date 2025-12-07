from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import json

from ..database import get_db
from ..services.predictive_analytics_service import PredictiveAnalyticsService

from pydantic import BaseModel

router = APIRouter(prefix="/predictive-analytics", tags=["Predictive Analytics"])

class ForecastRequest(BaseModel):
    forecast_type: str
    timeframe: str
    data_points: List[Dict[str, Any]]
    parameters: Optional[Dict[str, Any]] = None


class TrendAnalysisRequest(BaseModel):
    trend_type: str
    data_source: str
    analysis_period: str
    filters: Optional[Dict[str, Any]] = None


class ConsumerBehaviorRequest(BaseModel):
    behavior_type: str
    audience_segment: str
    time_range: str
    metrics: List[str]


class ForecastResponse(BaseModel):
    id: str
    forecast_type: str
    timeframe: str
    predictions: List[Dict[str, Any]]
    confidence_level: float
    created_at: datetime

@router.post("/forecast", response_model=ForecastResponse)
async def create_forecast(
    request: ForecastRequest,
    db: Session = Depends(get_db)
):
    service = PredictiveAnalyticsService(db)
    try:
        result = service.create_forecast(
            request.forecast_type,
            request.timeframe,
            request.data_points,
            request.parameters
        )
        return ForecastResponse(
            id=result["id"],
            forecast_type=result["forecast_type"],
            timeframe=result["timeframe"],
            predictions=result["predictions"],
            confidence_level=result["confidence_level"],
            created_at=result["created_at"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/forecast/{forecast_id}", response_model=ForecastResponse)
async def get_forecast(forecast_id: str, db: Session = Depends(get_db)):
    service = PredictiveAnalyticsService(db)
    try:
        result = service.get_forecast(forecast_id)
        if not result:
            raise HTTPException(status_code=404, detail="Forecast not found")
        return ForecastResponse(
            id=result["id"],
            forecast_type=result["forecast_type"],
            timeframe=result["timeframe"],
            predictions=result["predictions"],
            confidence_level=result["confidence_level"],
            created_at=result["created_at"]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/forecast", response_model=List[ForecastResponse])
async def list_forecasts(
    forecast_type: Optional[str] = None,
    timeframe: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    service = PredictiveAnalyticsService(db)
    try:
        results = service.list_forecasts(forecast_type, timeframe, limit, offset)
        return [
            ForecastResponse(
                id=result["id"],
                forecast_type=result["forecast_type"],
                timeframe=result["timeframe"],
                predictions=result["predictions"],
                confidence_level=result["confidence_level"],
                created_at=result["created_at"]
            )
            for result in results
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/trends/analyze")
async def analyze_trends(
    request: TrendAnalysisRequest,
    db: Session = Depends(get_db)
):
    service = PredictiveAnalyticsService(db)
    try:
        result = service.analyze_trends(
            request.trend_type,
            request.data_source,
            request.analysis_period,
            request.filters
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trends")
async def get_trends(
    trend_type: Optional[str] = None,
    data_source: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    service = PredictiveAnalyticsService(db)
    try:
        trends = service.get_trends(trend_type, data_source, limit, offset)
        return {"trends": trends}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/consumer-behavior/analyze")
async def analyze_consumer_behavior(
    request: ConsumerBehaviorRequest,
    db: Session = Depends(get_db)
):
    service = PredictiveAnalyticsService(db)
    try:
        result = service.analyze_consumer_behavior(
            request.behavior_type,
            request.audience_segment,
            request.time_range,
            request.metrics
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/consumer-behavior/patterns")
async def get_behavior_patterns(
    audience_segment: Optional[str] = None,
    behavior_type: Optional[str] = None,
    time_range: str = "30d",
    db: Session = Depends(get_db)
):
    service = PredictiveAnalyticsService(db)
    try:
        patterns = service.get_behavior_patterns(audience_segment, behavior_type, time_range)
        return {"patterns": patterns}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/campaign-performance/predict")
async def predict_campaign_performance(
    campaign_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    service = PredictiveAnalyticsService(db)
    try:
        result = service.predict_campaign_performance(campaign_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/campaign-performance/predictions")
async def get_campaign_predictions(
    campaign_id: Optional[int] = None,
    prediction_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    service = PredictiveAnalyticsService(db)
    try:
        predictions = service.get_campaign_predictions(campaign_id, prediction_type, limit, offset)
        return {"predictions": predictions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/market-opportunities/identify")
async def identify_market_opportunities(
    market_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    service = PredictiveAnalyticsService(db)
    try:
        result = service.identify_market_opportunities(market_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/market-opportunities")
async def get_market_opportunities(
    opportunity_type: Optional[str] = None,
    market_segment: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    service = PredictiveAnalyticsService(db)
    try:
        opportunities = service.get_market_opportunities(opportunity_type, market_segment, limit, offset)
        return {"opportunities": opportunities}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/demand-forecasting/calculate")
async def calculate_demand_forecast(
    demand_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    service = PredictiveAnalyticsService(db)
    try:
        result = service.calculate_demand_forecast(demand_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/demand-forecasting/forecasts")
async def get_demand_forecasts(
    product_category: Optional[str] = None,
    forecast_period: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    service = PredictiveAnalyticsService(db)
    try:
        forecasts = service.get_demand_forecasts(product_category, forecast_period, limit, offset)
        return {"forecasts": forecasts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/seasonal-patterns/analyze")
async def analyze_seasonal_patterns(
    pattern_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    service = PredictiveAnalyticsService(db)
    try:
        result = service.analyze_seasonal_patterns(pattern_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/seasonal-patterns")
async def get_seasonal_patterns(
    pattern_type: Optional[str] = None,
    time_period: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    service = PredictiveAnalyticsService(db)
    try:
        patterns = service.get_seasonal_patterns(pattern_type, time_period, limit, offset)
        return {"patterns": patterns}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/anomaly-detection/detect")
async def detect_anomalies(
    anomaly_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    service = PredictiveAnalyticsService(db)
    try:
        result = service.detect_anomalies(anomaly_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/anomaly-detection/anomalies")
async def get_anomalies(
    anomaly_type: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    service = PredictiveAnalyticsService(db)
    try:
        anomalies = service.get_anomalies(anomaly_type, severity, limit, offset)
        return {"anomalies": anomalies}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/predictive-models/train")
async def train_predictive_model(
    model_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    service = PredictiveAnalyticsService(db)
    try:
        result = service.train_predictive_model(model_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/predictive-models")
async def list_predictive_models(
    model_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    service = PredictiveAnalyticsService(db)
    try:
        models = service.list_predictive_models(model_type, status, limit, offset)
        return {"models": models}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/predictive-models/{model_id}/performance")
async def get_model_performance(model_id: str, db: Session = Depends(get_db)):
    service = PredictiveAnalyticsService(db)
    try:
        performance = service.get_model_performance(model_id)
        if not performance:
            raise HTTPException(status_code=404, detail="Model not found")
        return performance
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/predictive-models/{model_id}/update")
async def update_predictive_model(
    model_id: str,
    update_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    service = PredictiveAnalyticsService(db)
    try:
        result = service.update_predictive_model(model_id, update_data)
        if not result:
            raise HTTPException(status_code=404, detail="Model not found")
        return {"message": "Model updated successfully", "model_id": model_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/overview")
async def get_predictive_analytics_overview(
    timeframe: str = "30d",
    db: Session = Depends(get_db)
):
    service = PredictiveAnalyticsService(db)
    try:
        overview = service.get_predictive_analytics_overview(timeframe)
        return overview
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/accuracy")
async def get_prediction_accuracy(
    model_type: Optional[str] = None,
    timeframe: str = "30d",
    db: Session = Depends(get_db)
):
    service = PredictiveAnalyticsService(db)
    try:
        accuracy = service.get_prediction_accuracy(model_type, timeframe)
        return accuracy
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
