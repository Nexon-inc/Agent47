from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..database import get_clara_database, get_db
from ..services.onboarding_assistance_service import OnboardingAssistanceService
from ..models import OnboardingStep, ClaraOnboardingSession, OnboardingTutorial, OnboardingProgress


# Pydantic models for request/response
class OnboardingStepCreate(BaseModel):
    step_name: str
    step_type: str
    description: Optional[str] = None
    content: str
    order_index: int
    is_required: bool = True
    estimated_time_minutes: Optional[int] = None

class OnboardingStepUpdate(BaseModel):
    step_name: Optional[str] = None
    step_type: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    order_index: Optional[int] = None
    is_required: Optional[bool] = None
    estimated_time_minutes: Optional[int] = None

class OnboardingSessionCreate(BaseModel):
    user_id: int
    step_id: int
    status: str = "in_progress"

class OnboardingSessionUpdate(BaseModel):
    status: Optional[str] = None
    completed_at: Optional[datetime] = None
    notes: Optional[str] = None

class OnboardingTutorialCreate(BaseModel):
    title: str
    content: str
    category: str
    tags: Optional[List[str]] = None
    difficulty_level: str = "beginner"

class OnboardingTutorialUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    difficulty_level: Optional[str] = None


router = APIRouter()
onboarding_service = OnboardingAssistanceService()


# Onboarding Steps endpoints
@router.post("/steps", response_model=Dict[str, Any])
async def create_onboarding_step(
    step: OnboardingStepCreate,
    db: Session = Depends(get_db)
):
    """Create a new onboarding step"""
    return await onboarding_service.create_onboarding_step(
        db=db,
        step_name=step.step_name,
        step_type=step.step_type,
        description=step.description,
        content=step.content,
        order_index=step.order_index,
        is_required=step.is_required,
        estimated_time_minutes=step.estimated_time_minutes
    )

@router.get("/steps/{step_id}", response_model=Dict[str, Any])
async def get_onboarding_step(
    step_id: int = Path(..., description="The ID of the onboarding step"),
    db: Session = Depends(get_db)
):
    """Get onboarding step by ID"""
    return await onboarding_service.get_onboarding_step(db=db, step_id=step_id)

@router.get("/steps", response_model=List[Dict[str, Any]])
async def list_onboarding_steps(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    step_type: Optional[str] = Query(None),
    is_required: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    """List onboarding steps"""
    return await onboarding_service.list_onboarding_steps(
        db=db,
        skip=skip,
        limit=limit,
        step_type=step_type,
        is_required=is_required
    )

@router.put("/steps/{step_id}", response_model=Dict[str, Any])
async def update_onboarding_step(
    step: OnboardingStepUpdate,
    step_id: int = Path(..., description="The ID of the onboarding step"),
    db: Session = Depends(get_db)
):
    """Update onboarding step"""
    return await onboarding_service.update_onboarding_step(
        db=db,
        step_id=step_id,
        step_name=step.step_name,
        step_type=step.step_type,
        description=step.description,
        content=step.content,
        order_index=step.order_index,
        is_required=step.is_required,
        estimated_time_minutes=step.estimated_time_minutes
    )

@router.delete("/steps/{step_id}", response_model=Dict[str, str])
async def delete_onboarding_step(
    step_id: int = Path(..., description="The ID of the onboarding step"),
    db: Session = Depends(get_db)
):
    """Delete onboarding step"""
    return await onboarding_service.delete_onboarding_step(db=db, step_id=step_id)

@router.get("/steps/{step_id}/next", response_model=Dict[str, Any])
async def get_next_step(
    step_id: int = Path(..., description="The ID of the current step"),
    db: Session = Depends(get_db)
):
    """Get the next onboarding step"""
    return await onboarding_service.get_next_step(db=db, current_step_id=step_id)


# Onboarding Sessions endpoints
@router.post("/sessions", response_model=Dict[str, Any])
async def create_onboarding_session(
    session: OnboardingSessionCreate,
    db: Session = Depends(get_db)
):
    """Create a new onboarding session"""
    return await onboarding_service.create_onboarding_session(
        db=db,
        user_id=session.user_id,
        step_id=session.step_id,
        status=session.status
    )

@router.get("/sessions/{session_id}", response_model=Dict[str, Any])
async def get_onboarding_session(
    session_id: int = Path(..., description="The ID of the onboarding session"),
    db: Session = Depends(get_db)
):
    """Get onboarding session by ID"""
    return await onboarding_service.get_onboarding_session(db=db, session_id=session_id)

@router.get("/sessions", response_model=List[Dict[str, Any]])
async def list_onboarding_sessions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    user_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List onboarding sessions"""
    return await onboarding_service.list_onboarding_sessions(
        db=db,
        skip=skip,
        limit=limit,
        user_id=user_id,
        status=status
    )

@router.put("/sessions/{session_id}", response_model=Dict[str, Any])
async def update_onboarding_session(
    session: OnboardingSessionUpdate,
    session_id: int = Path(..., description="The ID of the onboarding session"),
    db: Session = Depends(get_db)
):
    """Update onboarding session"""
    return await onboarding_service.update_onboarding_session(
        db=db,
        session_id=session_id,
        status=session.status,
        completed_at=session.completed_at,
        notes=session.notes
    )

@router.delete("/sessions/{session_id}", response_model=Dict[str, str])
async def delete_onboarding_session(
    session_id: int = Path(..., description="The ID of the onboarding session"),
    db: Session = Depends(get_db)
):
    """Delete onboarding session"""
    return await onboarding_service.delete_onboarding_session(db=db, session_id=session_id)


# Onboarding Tutorials endpoints
@router.post("/tutorials", response_model=Dict[str, Any])
async def create_onboarding_tutorial(
    tutorial: OnboardingTutorialCreate,
    db: Session = Depends(get_db)
):
    """Create a new onboarding tutorial"""
    return await onboarding_service.create_onboarding_tutorial(
        db=db,
        title=tutorial.title,
        content=tutorial.content,
        category=tutorial.category,
        tags=tutorial.tags,
        difficulty_level=tutorial.difficulty_level
    )

@router.get("/tutorials/{tutorial_id}", response_model=Dict[str, Any])
async def get_onboarding_tutorial(
    tutorial_id: int = Path(..., description="The ID of the onboarding tutorial"),
    db: Session = Depends(get_db)
):
    """Get onboarding tutorial by ID"""
    return await onboarding_service.get_onboarding_tutorial(db=db, tutorial_id=tutorial_id)

@router.get("/tutorials", response_model=List[Dict[str, Any]])
async def list_onboarding_tutorials(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    category: Optional[str] = Query(None),
    difficulty_level: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List onboarding tutorials"""
    return await onboarding_service.list_onboarding_tutorials(
        db=db,
        skip=skip,
        limit=limit,
        category=category,
        difficulty_level=difficulty_level
    )

@router.put("/tutorials/{tutorial_id}", response_model=Dict[str, Any])
async def update_onboarding_tutorial(
    tutorial: OnboardingTutorialUpdate,
    tutorial_id: int = Path(..., description="The ID of the onboarding tutorial"),
    db: Session = Depends(get_db)
):
    """Update onboarding tutorial"""
    return await onboarding_service.update_onboarding_tutorial(
        db=db,
        tutorial_id=tutorial_id,
        title=tutorial.title,
        content=tutorial.content,
        category=tutorial.category,
        tags=tutorial.tags,
        difficulty_level=tutorial.difficulty_level
    )

@router.delete("/tutorials/{tutorial_id}", response_model=Dict[str, str])
async def delete_onboarding_tutorial(
    tutorial_id: int = Path(..., description="The ID of the onboarding tutorial"),
    db: Session = Depends(get_db)
):
    """Delete onboarding tutorial"""
    return await onboarding_service.delete_onboarding_tutorial(db=db, tutorial_id=tutorial_id)

@router.get("/tutorials/search", response_model=List[Dict[str, Any]])
async def search_onboarding_tutorials(
    query: str = Query(..., description="Search query"),
    category: Optional[str] = Query(None),
    difficulty_level: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Search onboarding tutorials"""
    return await onboarding_service.search_onboarding_tutorials(
        db=db,
        query=query,
        category=category,
        difficulty_level=difficulty_level,
        limit=limit
    )


# Progress and Analytics endpoints
@router.get("/progress/{user_id}", response_model=Dict[str, Any])
async def get_onboarding_progress(
    user_id: int = Path(..., description="The ID of the user"),
    db: Session = Depends(get_db)
):
    """Get user's onboarding progress"""
    return await onboarding_service.get_onboarding_progress(db=db, user_id=user_id)

@router.post("/progress/{user_id}/calculate", response_model=Dict[str, Any])
async def calculate_onboarding_progress(
    user_id: int = Path(..., description="The ID of the user"),
    db: Session = Depends(get_db)
):
    """Calculate user's onboarding progress"""
    return await onboarding_service.calculate_onboarding_progress(db=db, user_id=user_id)

@router.get("/analytics", response_model=Dict[str, Any])
async def get_onboarding_analytics(
    start_date: datetime = Query(..., description="Start date for analytics"),
    end_date: datetime = Query(..., description="End date for analytics"),
    db: Session = Depends(get_db)
):
    """Get onboarding analytics"""
    return await onboarding_service.get_onboarding_analytics(
        db=db,
        start_date=start_date,
        end_date=end_date
    )


# Health check endpoint
@router.get("/health", response_model=Dict[str, Any])
async def health_check():
    """Health check for onboarding assistance system"""
    return await onboarding_service.health_check()
