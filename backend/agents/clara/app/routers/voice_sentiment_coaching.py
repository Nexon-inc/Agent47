from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session

from ..database import get_clara_database, get_db
from ..services.voice_sentiment_coaching_service import VoiceSentimentCoachingService
from ..schemas.voice_sentiment_coaching import (
    CreateVoiceSentimentSessionRequest, UpdateVoiceSentimentSessionRequest,
    CreateVoiceSentimentAnalysisRequest, UpdateVoiceSentimentAnalysisRequest,
    CreateVoiceSentimentFeedbackRequest, UpdateVoiceSentimentFeedbackRequest,
    CreateVoiceSentimentCoachingRequest, UpdateVoiceSentimentCoachingRequest,
    CreateVoiceSentimentScenarioRequest, UpdateVoiceSentimentScenarioRequest,
    VoiceSentimentSessionResponse, VoiceSentimentAnalysisResponse, VoiceSentimentFeedbackResponse,
    VoiceSentimentCoachingResponse, VoiceSentimentScenarioResponse, VoiceSentimentAnalyticsResponse
)

router = APIRouter()
voice_sentiment_service = VoiceSentimentCoachingService()


@router.post("/sessions", response_model=VoiceSentimentSessionResponse)
async def create_voice_sentiment_session(
    request: CreateVoiceSentimentSessionRequest,
    db: Session = Depends(get_db)
):
    """Create a new voice sentiment coaching session"""
    return await voice_sentiment_service.create_voice_sentiment_session(db, request)


@router.get("/sessions/{session_id}", response_model=VoiceSentimentSessionResponse)
async def get_voice_sentiment_session(
    session_id: int,
    db: Session = Depends(get_db)
):
    """Get voice sentiment session by ID"""
    return await voice_sentiment_service.get_voice_sentiment_session(db, session_id)


@router.get("/sessions", response_model=List[VoiceSentimentSessionResponse])
async def list_voice_sentiment_sessions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    agent_id: Optional[int] = Query(None),
    session_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List voice sentiment sessions"""
    return await voice_sentiment_service.list_voice_sentiment_sessions(
        db, skip=skip, limit=limit, agent_id=agent_id, session_type=session_type, status=status
    )


@router.put("/sessions/{session_id}", response_model=VoiceSentimentSessionResponse)
async def update_voice_sentiment_session(
    session_id: int,
    request: UpdateVoiceSentimentSessionRequest,
    db: Session = Depends(get_db)
):
    """Update voice sentiment session"""
    return await voice_sentiment_service.update_voice_sentiment_session(db, session_id, request)


@router.delete("/sessions/{session_id}")
async def delete_voice_sentiment_session(
    session_id: int,
    db: Session = Depends(get_db)
):
    """Delete voice sentiment session"""
    return await voice_sentiment_service.delete_voice_sentiment_session(db, session_id)


@router.post("/analyses", response_model=VoiceSentimentAnalysisResponse)
async def create_voice_sentiment_analysis(
    request: CreateVoiceSentimentAnalysisRequest,
    db: Session = Depends(get_db)
):
    """Create a new voice sentiment analysis"""
    return await voice_sentiment_service.create_voice_sentiment_analysis(db, request)


@router.get("/analyses/{analysis_id}", response_model=VoiceSentimentAnalysisResponse)
async def get_voice_sentiment_analysis(
    analysis_id: int,
    db: Session = Depends(get_db)
):
    """Get voice sentiment analysis by ID"""
    return await voice_sentiment_service.get_voice_sentiment_analysis(db, analysis_id)


@router.get("/analyses", response_model=List[VoiceSentimentAnalysisResponse])
async def list_voice_sentiment_analyses(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    session_id: Optional[int] = Query(None),
    scenario_id: Optional[int] = Query(None),
    sentiment_type: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List voice sentiment analyses"""
    return await voice_sentiment_service.list_voice_sentiment_analyses(
        db, skip=skip, limit=limit, session_id=session_id, scenario_id=scenario_id, sentiment_type=sentiment_type
    )


@router.put("/analyses/{analysis_id}", response_model=VoiceSentimentAnalysisResponse)
async def update_voice_sentiment_analysis(
    analysis_id: int,
    request: UpdateVoiceSentimentAnalysisRequest,
    db: Session = Depends(get_db)
):
    """Update voice sentiment analysis"""
    return await voice_sentiment_service.update_voice_sentiment_analysis(db, analysis_id, request)


@router.delete("/analyses/{analysis_id}")
async def delete_voice_sentiment_analysis(
    analysis_id: int,
    db: Session = Depends(get_db)
):
    """Delete voice sentiment analysis"""
    return await voice_sentiment_service.delete_voice_sentiment_analysis(db, analysis_id)


@router.post("/feedbacks", response_model=VoiceSentimentFeedbackResponse)
async def create_voice_sentiment_feedback(
    request: CreateVoiceSentimentFeedbackRequest,
    db: Session = Depends(get_db)
):
    """Create a new voice sentiment feedback"""
    return await voice_sentiment_service.create_voice_sentiment_feedback(db, request)


@router.get("/feedbacks/{feedback_id}", response_model=VoiceSentimentFeedbackResponse)
async def get_voice_sentiment_feedback(
    feedback_id: int,
    db: Session = Depends(get_db)
):
    """Get voice sentiment feedback by ID"""
    return await voice_sentiment_service.get_voice_sentiment_feedback(db, feedback_id)


@router.get("/feedbacks", response_model=List[VoiceSentimentFeedbackResponse])
async def list_voice_sentiment_feedbacks(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    agent_id: Optional[int] = Query(None),
    analysis_id: Optional[int] = Query(None),
    feedback_type: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List voice sentiment feedbacks"""
    return await voice_sentiment_service.list_voice_sentiment_feedbacks(
        db, skip=skip, limit=limit, agent_id=agent_id, analysis_id=analysis_id, feedback_type=feedback_type
    )


@router.put("/feedbacks/{feedback_id}", response_model=VoiceSentimentFeedbackResponse)
async def update_voice_sentiment_feedback(
    feedback_id: int,
    request: UpdateVoiceSentimentFeedbackRequest,
    db: Session = Depends(get_db)
):
    """Update voice sentiment feedback"""
    return await voice_sentiment_service.update_voice_sentiment_feedback(db, feedback_id, request)


@router.delete("/feedbacks/{feedback_id}")
async def delete_voice_sentiment_feedback(
    feedback_id: int,
    db: Session = Depends(get_db)
):
    """Delete voice sentiment feedback"""
    return await voice_sentiment_service.delete_voice_sentiment_feedback(db, feedback_id)


@router.post("/coachings", response_model=VoiceSentimentCoachingResponse)
async def create_voice_sentiment_coaching(
    request: CreateVoiceSentimentCoachingRequest,
    db: Session = Depends(get_db)
):
    """Create a new voice sentiment coaching recommendation"""
    return await voice_sentiment_service.create_voice_sentiment_coaching(db, request)


@router.get("/coachings/{coaching_id}", response_model=VoiceSentimentCoachingResponse)
async def get_voice_sentiment_coaching(
    coaching_id: int,
    db: Session = Depends(get_db)
):
    """Get voice sentiment coaching by ID"""
    return await voice_sentiment_service.get_voice_sentiment_coaching(db, coaching_id)


@router.get("/coachings", response_model=List[VoiceSentimentCoachingResponse])
async def list_voice_sentiment_coachings(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    agent_id: Optional[int] = Query(None),
    session_id: Optional[int] = Query(None),
    coaching_type: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List voice sentiment coachings"""
    return await voice_sentiment_service.list_voice_sentiment_coachings(
        db, skip=skip, limit=limit, agent_id=agent_id, session_id=session_id, coaching_type=coaching_type
    )


@router.put("/coachings/{coaching_id}", response_model=VoiceSentimentCoachingResponse)
async def update_voice_sentiment_coaching(
    coaching_id: int,
    request: UpdateVoiceSentimentCoachingRequest,
    db: Session = Depends(get_db)
):
    """Update voice sentiment coaching"""
    return await voice_sentiment_service.update_voice_sentiment_coaching(db, coaching_id, request)


@router.delete("/coachings/{coaching_id}")
async def delete_voice_sentiment_coaching(
    coaching_id: int,
    db: Session = Depends(get_db)
):
    """Delete voice sentiment coaching"""
    return await voice_sentiment_service.delete_voice_sentiment_coaching(db, coaching_id)


@router.post("/scenarios", response_model=VoiceSentimentScenarioResponse)
async def create_voice_sentiment_scenario(
    request: CreateVoiceSentimentScenarioRequest,
    db: Session = Depends(get_db)
):
    """Create a new voice sentiment scenario"""
    return await voice_sentiment_service.create_voice_sentiment_scenario(db, request)


@router.get("/scenarios/{scenario_id}", response_model=VoiceSentimentScenarioResponse)
async def get_voice_sentiment_scenario(
    scenario_id: int,
    db: Session = Depends(get_db)
):
    """Get voice sentiment scenario by ID"""
    return await voice_sentiment_service.get_voice_sentiment_scenario(db, scenario_id)


@router.get("/scenarios", response_model=List[VoiceSentimentScenarioResponse])
async def list_voice_sentiment_scenarios(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    scenario_type: Optional[str] = Query(None),
    difficulty_level: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    """List voice sentiment scenarios"""
    return await voice_sentiment_service.list_voice_sentiment_scenarios(
        db, skip=skip, limit=limit, scenario_type=scenario_type, difficulty_level=difficulty_level, is_active=is_active
    )


@router.put("/scenarios/{scenario_id}", response_model=VoiceSentimentScenarioResponse)
async def update_voice_sentiment_scenario(
    scenario_id: int,
    request: UpdateVoiceSentimentScenarioRequest,
    db: Session = Depends(get_db)
):
    """Update voice sentiment scenario"""
    return await voice_sentiment_service.update_voice_sentiment_scenario(db, scenario_id, request)


@router.delete("/scenarios/{scenario_id}")
async def delete_voice_sentiment_scenario(
    scenario_id: int,
    db: Session = Depends(get_db)
):
    """Delete voice sentiment scenario"""
    return await voice_sentiment_service.delete_voice_sentiment_scenario(db, scenario_id)


@router.get("/analytics", response_model=VoiceSentimentAnalyticsResponse)
async def get_voice_sentiment_analytics(
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    agent_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """Get voice sentiment analytics"""
    return await voice_sentiment_service.get_voice_sentiment_analytics(db, start_date, end_date, agent_id)


@router.get("/health")
async def health_check():
    """Check the health of voice sentiment coaching system"""
    return await voice_sentiment_service.health_check()
