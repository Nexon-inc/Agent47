from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, List, Any

from ..database import get_db
from ..services.interactive_elements_service import InteractiveElementsService

router = APIRouter(prefix="/interactive-elements", tags=["Interactive Campaign Elements"])

@router.post("/poll")
def create_interactive_poll(poll_data: Dict[str, Any], target_audience: List[str], 
                          db: Session = Depends(get_db)):
    service = InteractiveElementsService(db)
    return service.create_interactive_poll(poll_data, target_audience)

@router.post("/quiz")
def create_campaign_quiz(quiz_data: Dict[str, Any], quiz_type: str, db: Session = Depends(get_db)):
    service = InteractiveElementsService(db)
    return service.create_campaign_quiz(quiz_data, quiz_type)

@router.post("/survey")
def create_email_survey(survey_data: Dict[str, Any], target_segments: List[str], 
                       db: Session = Depends(get_db)):
    service = InteractiveElementsService(db)
    return service.create_email_survey(survey_data, target_segments)

@router.post("/content")
def create_interactive_content(content_brief: Dict[str, Any], content_type: str, 
                             db: Session = Depends(get_db)):
    service = InteractiveElementsService(db)
    return service.create_interactive_content(content_brief, content_type)

@router.get("/analytics")
def get_interactive_analytics(timeframe: str = "30d", db: Session = Depends(get_db)):
    service = InteractiveElementsService(db)
    return service.get_interactive_analytics(timeframe)
