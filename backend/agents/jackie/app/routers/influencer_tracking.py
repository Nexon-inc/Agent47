from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, List, Any

from ..database import get_db
from ..services.influencer_tracking_service import InfluencerTrackingService

router = APIRouter(prefix="/influencer-tracking", tags=["JackieInfluencer Performance Tracking"])

@router.post("/track-performance")
def track_influencer_performance(influencer_id: str, campaign_id: str, performance_data: Dict[str, Any], 
                                db: Session = Depends(get_db)):
    service = InfluencerTrackingService(db)
    return service.track_influencer_performance(influencer_id, campaign_id, performance_data)

@router.post("/calculate-roi")
def calculate_influencer_roi(campaign_id: str, investment_amount: float, revenue_generated: float, 
                            db: Session = Depends(get_db)):
    service = InfluencerTrackingService(db)
    return service.calculate_influencer_roi(campaign_id, investment_amount, revenue_generated)

@router.get("/analytics")
def get_influencer_analytics(timeframe: str = "30d", db: Session = Depends(get_db)):
    service = InfluencerTrackingService(db)
    return service.get_influencer_analytics(timeframe)
