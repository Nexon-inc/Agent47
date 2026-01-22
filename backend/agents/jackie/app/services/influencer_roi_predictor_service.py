import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session

from core.utils.nlp_utils import NLPProcessor
from core.cache.redis_manager import RedisManager
from ..models import JackieInfluencerROIPrediction, JackiePredictionModel, JackieHistoricalROI, JackieInfluencerMetrics

class InfluencerROIPredictorService:
    def __init__(self, db: Session):
        self.db = db
        self.nlp_processor = NLPProcessor()
        self.redis_manager = RedisManager()
        
    def predict_influencer_roi(self, influencer_id: str, campaign_budget: float, campaign_type: str) -> Dict[str, Any]:
        prediction_id = str(uuid.uuid4())
        
        prompt = f"""
        JackieInfluencer ID: {influencer_id}
        Campaign Budget: {campaign_budget}
        Campaign Type: {campaign_type}
        
        Predict ROI for influencer campaign based on historical data and metrics.
        """
        
        prediction_result = self.nlp_processor.predict_influencer_roi(prompt)
        
        prediction = JackieInfluencerROIPrediction(
            id=prediction_id, influencer_id=influencer_id, campaign_budget=campaign_budget,
            campaign_type=campaign_type, prediction_data=json.dumps(prediction_result),
            created_at=datetime.utcnow()
        )
        self.db.add(prediction)
        self.db.commit()
        
        return {"prediction_id": prediction_id, "prediction_data": prediction_result}
    
    def create_prediction_model(self, model_type: str, training_data: Dict[str, Any]) -> Dict[str, Any]:
        model_id = str(uuid.uuid4())
        
        prompt = f"""
        Model Type: {model_type}
        Training Data: {training_data}
        
        Create an ROI prediction model for influencer campaigns.
        """
        
        model_result = self.nlp_processor.create_prediction_model(prompt)
        
        model = PredictionModel(
            id=model_id, model_type=model_type, training_data=json.dumps(training_data),
            model_config=json.dumps(model_result), created_at=datetime.utcnow()
        )
        self.db.add(model)
        self.db.commit()
        
        return {"model_id": model_id, "model_config": model_result}
    
    def analyze_historical_roi(self, influencer_id: str, analysis_period: str) -> Dict[str, Any]:
        analysis_id = str(uuid.uuid4())
        
        prompt = f"""
        JackieInfluencer ID: {influencer_id}
        Analysis Period: {analysis_period}
        
        Analyze historical ROI data for the influencer.
        """
        
        analysis_result = self.nlp_processor.analyze_historical_roi(prompt)
        
        analysis = JackieHistoricalROI(
            id=analysis_id, influencer_id=influencer_id, analysis_period=analysis_period,
            analysis_data=json.dumps(analysis_result), created_at=datetime.utcnow()
        )
        self.db.add(analysis)
        self.db.commit()
        
        return {"analysis_id": analysis_id, "analysis_data": analysis_result}
    
    def get_roi_predictor_analytics(self, timeframe: str = "30d") -> Dict[str, Any]:
        cutoff_date = datetime.utcnow() - timedelta(days=30 if timeframe == "30d" else 7)
        
        predictions_made = self.db.query(JackieInfluencerROIPrediction).filter(JackieInfluencerROIPrediction.created_at >= cutoff_date).count()
        models_created = self.db.query(PredictionModel).filter(PredictionModel.created_at >= cutoff_date).count()
        historical_analyses = self.db.query(JackieHistoricalROI).filter(JackieHistoricalROI.created_at >= cutoff_date).count()
        
        return {
            "timeframe": timeframe, "predictions_made": predictions_made,
            "models_created": models_created, "historical_analyses": historical_analyses
        }
