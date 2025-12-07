from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, List, Any

from ..database import get_db
from ..services.campaign_storyboard_service import CampaignStoryboardService

router = APIRouter(prefix="/campaign-storyboard", tags=["AI Campaign Storyboard"])

@router.post("/storyboard")
def create_campaign_storyboard(campaign_brief: Dict[str, Any], storyboard_type: str = "multi_channel", 
                              db: Session = Depends(get_db)):
    service = CampaignStoryboardService(db)
    return service.create_campaign_storyboard(campaign_brief, storyboard_type)

@router.post("/scene")
def create_storyboard_scene(scene_data: Dict[str, Any], scene_order: int, channel: str, 
                           db: Session = Depends(get_db)):
    service = CampaignStoryboardService(db)
    return service.create_storyboard_scene(scene_data, scene_order, channel)

@router.get("/analytics")
def get_storyboard_analytics(timeframe: str = "30d", db: Session = Depends(get_db)):
    service = CampaignStoryboardService(db)
    return service.get_storyboard_analytics(timeframe)
