from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, List, Any

from ..database import get_db
from ..services.dynamic_personalization_service import DynamicPersonalizationService

router = APIRouter(prefix="/dynamic-personalization", tags=["Dynamic Customer Personalization"])

@router.post("/customer-segment")
def create_customer_segment(segment_criteria: Dict[str, Any], segment_name: str, 
                           db: Session = Depends(get_db)):
    service = DynamicPersonalizationService(db)
    return service.create_customer_segment(segment_criteria, segment_name)

@router.post("/dynamic-content")
def generate_dynamic_content(content_template: str, customer_data: Dict[str, Any], 
                           db: Session = Depends(get_db)):
    service = DynamicPersonalizationService(db)
    return service.generate_dynamic_content(content_template, customer_data)

@router.get("/analytics")
def get_personalization_analytics(timeframe: str = "30d", db: Session = Depends(get_db)):
    service = DynamicPersonalizationService(db)
    return service.get_personalization_analytics(timeframe)
