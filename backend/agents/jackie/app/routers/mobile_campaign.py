from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, List, Any
from pydantic import BaseModel, Field

from ..database import get_db
from ..services.mobile_campaign_service import MobileCampaignService

router = APIRouter(prefix="/mobile-campaign", tags=["Mobile JackieCampaign Management"])


class MobileCampaignRequest(BaseModel):
    campaign_data: Dict[str, Any]
    mobile_platforms: List[str]
    target_devices: List[str]


class PushNotificationRequest(BaseModel):
    notification_data: Dict[str, Any]
    target_users: List[str]
    notification_type: str


class MobileContentRequest(BaseModel):
    content_brief: Dict[str, Any]
    mobile_format: str
    target_platform: str


class AppEngagementRequest(BaseModel):
    user_id: str
    engagement_data: Dict[str, Any]
    engagement_type: str

@router.post("/campaign")
def create_mobile_campaign(request: MobileCampaignRequest, db: Session = Depends(get_db)):
    service = MobileCampaignService(db)
    return service.create_mobile_campaign(request.campaign_data, request.mobile_platforms, request.target_devices)

@router.post("/push-notification")
def send_push_notification(request: PushNotificationRequest, db: Session = Depends(get_db)):
    service = MobileCampaignService(db)
    return service.send_push_notification(request.notification_data, request.target_users, request.notification_type)

@router.post("/content")
def create_mobile_content(request: MobileContentRequest, db: Session = Depends(get_db)):
    service = MobileCampaignService(db)
    return service.create_mobile_content(request.content_brief, request.mobile_format, request.target_platform)

@router.post("/engagement")
def track_app_engagement(request: AppEngagementRequest, db: Session = Depends(get_db)):
    service = MobileCampaignService(db)
    return service.track_app_engagement(request.user_id, request.engagement_data, request.engagement_type)

@router.put("/campaign/{campaign_id}/optimize")
def optimize_mobile_campaign(campaign_id: str, optimization_goals: Dict[str, Any], db: Session = Depends(get_db)):
    service = MobileCampaignService(db)
    return service.optimize_mobile_campaign(campaign_id, optimization_goals)

@router.post("/mobile-ad")
def create_mobile_ad(ad_brief: Dict[str, Any], ad_format: str, target_platform: str, db: Session = Depends(get_db)):
    service = MobileCampaignService(db)
    return service.create_mobile_ad(ad_brief, ad_format, target_platform)

@router.post("/budget/{campaign_id}")
def manage_mobile_budget(campaign_id: str, budget_data: Dict[str, Any], db: Session = Depends(get_db)):
    service = MobileCampaignService(db)
    return service.manage_mobile_budget(campaign_id, budget_data)

@router.get("/analytics/{campaign_id}")
def get_mobile_analytics(campaign_id: str, timeframe: str = "30d", db: Session = Depends(get_db)):
    service = MobileCampaignService(db)
    return service.get_mobile_analytics(campaign_id, timeframe)

@router.post("/batch-notifications")
def batch_send_notifications(notifications_batch: List[Dict[str, Any]], db: Session = Depends(get_db)):
    service = MobileCampaignService(db)
    return service.batch_send_notifications(notifications_batch)
