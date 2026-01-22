from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, List, Any

from ..database import get_db
from ..services.influencer_roi_predictor_service import InfluencerROIPredictorService

router = APIRouter(prefix="/influencer-roi-predictor", tags=["JackieInfluencer ROI Predictor"])

@router.post("/predict-roi")
def predict_influencer_roi(influencer_id: str, campaign_budget: float, campaign_type: str, 
                          db: Session = Depends(get_db)):
    service = InfluencerROIPredictorService(db)
    return service.predict_influencer_roi(influencer_id, campaign_budget, campaign_type)

@router.post("/prediction-model")
def create_prediction_model(model_type: str, training_data: Dict[str, Any], 
                          db: Session = Depends(get_db)):
    service = InfluencerROIPredictorService(db)
    return service.create_prediction_model(model_type, training_data)

@router.post("/historical-roi")
def analyze_historical_roi(influencer_id: str, analysis_period: str, 
                          db: Session = Depends(get_db)):
    service = InfluencerROIPredictorService(db)
    return service.analyze_historical_roi(influencer_id, analysis_period)

@router.get("/analytics")
def get_roi_predictor_analytics(timeframe: str = "30d", db: Session = Depends(get_db)):
    service = InfluencerROIPredictorService(db)
    return service.get_roi_predictor_analytics(timeframe)
