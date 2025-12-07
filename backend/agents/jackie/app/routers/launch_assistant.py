from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, List, Any

from ..database import get_db
from ..services.launch_assistant_service import LaunchAssistantService

router = APIRouter(prefix="/launch-assistant", tags=["Launch Assistant"])

@router.post("/project")
def create_launch_project(project_brief: Dict[str, Any], business_info: Dict[str, Any], 
                         db: Session = Depends(get_db)):
    service = LaunchAssistantService(db)
    return service.create_launch_project(project_brief, business_info)

@router.post("/marketing-funnel")
def build_marketing_funnel(funnel_type: str, conversion_goals: List[str], db: Session = Depends(get_db)):
    service = LaunchAssistantService(db)
    return service.build_marketing_funnel(funnel_type, conversion_goals)

@router.post("/landing-page")
def create_landing_page(page_brief: Dict[str, Any], conversion_goals: List[str], 
                       db: Session = Depends(get_db)):
    service = LaunchAssistantService(db)
    return service.create_landing_page(page_brief, conversion_goals)

@router.post("/email-flow")
def create_email_flow(flow_brief: Dict[str, Any], subscriber_segments: List[str], 
                     db: Session = Depends(get_db)):
    service = LaunchAssistantService(db)
    return service.create_email_flow(flow_brief, subscriber_segments)

@router.get("/analytics")
def get_launch_analytics(timeframe: str = "30d", db: Session = Depends(get_db)):
    service = LaunchAssistantService(db)
    return service.get_launch_analytics(timeframe)
