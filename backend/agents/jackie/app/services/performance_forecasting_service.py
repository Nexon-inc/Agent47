import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session

from core.utils.nlp_utils import NLPProcessor
from core.cache.redis_manager import RedisManager
from ..models import JackiePredictionResult
from pydantic import BaseModel

class PerformanceForecast(BaseModel):
    id: str
    campaign_data: str  # JSON string
    forecast_horizon: str
    forecast_result: str  # JSON string
    created_at: datetime = datetime.utcnow()

class ForecastModel(BaseModel):
    id: str
    model_type: str
    training_data: str  # JSON string
    model_config: str  # JSON string
    created_at: datetime = datetime.utcnow()

class HistoricalData(BaseModel):
    id: str
    historical_data: str  # JSON string
    analysis_period: str
    analysis_result: str  # JSON string
    created_at: datetime = datetime.utcnow()

class PerformanceForecastingService:
    def __init__(self, db: Session):
        self.db = db
        self.nlp_processor = NLPProcessor()
        self.redis_manager = RedisManager()
        
    def predict_campaign_performance(self, campaign_data: Dict[str, Any], forecast_horizon: str = "30d") -> Dict[str, Any]:
        forecast_id = str(uuid.uuid4())
        
        prompt = f"""
        JackieCampaign Data: {campaign_data}
        Forecast Horizon: {forecast_horizon}
        
        Predict campaign performance metrics and engagement rates.
        """
        
        forecast_result = self.nlp_processor.predict_campaign_performance(prompt)
        
        forecast = PerformanceForecast(
            id=forecast_id, campaign_data=json.dumps(campaign_data), forecast_horizon=forecast_horizon,
            forecast_result=json.dumps(forecast_result), created_at=datetime.utcnow()
        )
        self.db.add(forecast)
        self.db.commit()
        
        return {"forecast_id": forecast_id, "forecast_result": forecast_result}
    
    def create_forecast_model(self, model_type: str, training_data: Dict[str, Any]) -> Dict[str, Any]:
        model_id = str(uuid.uuid4())
        
        prompt = f"""
        Model Type: {model_type}
        Training Data: {training_data}
        
        Create a performance forecasting model based on historical data.
        """
        
        model_result = self.nlp_processor.create_forecast_model(prompt)
        
        model = ForecastModel(
            id=model_id, model_type=model_type, training_data=json.dumps(training_data),
            model_config=json.dumps(model_result), created_at=datetime.utcnow()
        )
        self.db.add(model)
        self.db.commit()
        
        return {"model_id": model_id, "model_config": model_result}
    
    def analyze_historical_performance(self, historical_data: List[Dict[str, Any]], analysis_period: str) -> Dict[str, Any]:
        analysis_id = str(uuid.uuid4())
        
        prompt = f"""
        Historical Data: {historical_data}
        Analysis Period: {analysis_period}
        
        Analyze historical campaign performance to identify patterns and trends.
        """
        
        analysis_result = self.nlp_processor.analyze_historical_performance(prompt)
        
        analysis = HistoricalData(
            id=analysis_id, historical_data=json.dumps(historical_data), analysis_period=analysis_period,
            analysis_result=json.dumps(analysis_result), created_at=datetime.utcnow()
        )
        self.db.add(analysis)
        self.db.commit()
        
        return {"analysis_id": analysis_id, "analysis_result": analysis_result}
    
    def get_forecasting_analytics(self, timeframe: str = "30d") -> Dict[str, Any]:
        cutoff_date = datetime.utcnow() - timedelta(days=30 if timeframe == "30d" else 7)
        
        forecasts_created = self.db.query(PerformanceForecast).filter(PerformanceForecast.created_at >= cutoff_date).count()
        models_created = self.db.query(ForecastModel).filter(ForecastModel.created_at >= cutoff_date).count()
        historical_analyses = self.db.query(HistoricalData).filter(HistoricalData.created_at >= cutoff_date).count()
        
        return {
            "timeframe": timeframe, "forecasts_created": forecasts_created,
            "models_created": models_created, "historical_analyses": historical_analyses
        }
