from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, List, Any

from ..database import get_db
from ..services.onboarding_service import OnboardingService

router = APIRouter(prefix="/onboarding", tags=["Streamlined Onboarding"])

@router.post("/session")
def create_onboarding_session(user_id: str, business_info: Dict[str, Any], 
                            onboarding_type: str = "comprehensive", db: Session = Depends(get_db)):
    service = OnboardingService(db)
    return service.create_onboarding_session(user_id, business_info, onboarding_type)

@router.post("/setup-wizard")
def create_setup_wizard(wizard_type: str, steps_data: List[Dict[str, Any]], 
                       target_audience: str, db: Session = Depends(get_db)):
    service = OnboardingService(db)
    return service.create_setup_wizard(wizard_type, steps_data, target_audience)

@router.post("/tutorial-step")
def create_tutorial_step(step_data: Dict[str, Any], tutorial_type: str, 
                        difficulty_level: str = "beginner", db: Session = Depends(get_db)):
    service = OnboardingService(db)
    return service.create_tutorial_step(step_data, tutorial_type, difficulty_level)

@router.post("/track-progress")
def track_user_progress(user_id: str, session_id: str, progress_data: Dict[str, Any], 
                       current_step: str, db: Session = Depends(get_db)):
    service = OnboardingService(db)
    return service.track_user_progress(user_id, session_id, progress_data, current_step)

@router.get("/next-step")
def get_next_onboarding_step(user_id: str, session_id: str, current_step: str, 
                           db: Session = Depends(get_db)):
    service = OnboardingService(db)
    return service.get_next_onboarding_step(user_id, session_id, current_step)

@router.post("/recommendations")
def generate_onboarding_recommendations(user_data: Dict[str, Any], business_type: str, 
                                      db: Session = Depends(get_db)):
    service = OnboardingService(db)
    return service.generate_onboarding_recommendations(user_data, business_type)

@router.post("/quick-start-guide")
def create_quick_start_guide(business_info: Dict[str, Any], guide_type: str = "marketing", 
                           db: Session = Depends(get_db)):
    service = OnboardingService(db)
    return service.create_quick_start_guide(business_info, guide_type)

@router.get("/analytics")
def get_onboarding_analytics(timeframe: str = "30d", db: Session = Depends(get_db)):
    service = OnboardingService(db)
    return service.get_onboarding_analytics(timeframe)
