from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import json

from ..database import get_db
from ..services.agent_training_service import AgentTrainingService
from ..models import AgentTraining, TrainingModule, TrainingSession, AgentPerformance, TrainingAssessment
from ..core.integration_manager import IntegrationManager
from ..core.event_bus import EventBus

router = APIRouter()

# Pydantic models for request/response
class CreateTrainingModuleRequest(BaseModel):
    module_name: str = Field(..., description="Module name")
    module_type: str = Field(..., description="Module type (product_knowledge, communication, technical, soft_skills)")
    difficulty_level: str = Field(..., description="Difficulty level (beginner, intermediate, advanced)")
    content: str = Field(..., description="Training content")
    learning_objectives: List[str] = Field(..., description="Learning objectives")
    estimated_duration: int = Field(..., description="Estimated duration in minutes")
    prerequisites: List[str] = Field([], description="Prerequisite modules")
    is_active: bool = Field(True, description="Module active status")

class UpdateTrainingModuleRequest(BaseModel):
    module_name: Optional[str] = Field(None, description="Module name")
    module_type: Optional[str] = Field(None, description="Module type")
    difficulty_level: Optional[str] = Field(None, description="Difficulty level")
    content: Optional[str] = Field(None, description="Training content")
    learning_objectives: Optional[List[str]] = Field(None, description="Learning objectives")
    estimated_duration: Optional[int] = Field(None, description="Estimated duration in minutes")
    prerequisites: Optional[List[str]] = Field(None, description="Prerequisite modules")
    is_active: Optional[bool] = Field(None, description="Module active status")

class CreateTrainingSessionRequest(BaseModel):
    agent_id: str = Field(..., description="Agent ID")
    module_id: int = Field(..., description="Training module ID")
    session_type: str = Field(..., description="Session type (self_study, guided, assessment)")
    scheduled_at: Optional[datetime] = Field(None, description="Scheduled session time")
    duration: Optional[int] = Field(None, description="Session duration in minutes")

class StartTrainingSessionRequest(BaseModel):
    session_id: int = Field(..., description="Training session ID")
    start_time: Optional[datetime] = Field(None, description="Session start time")

class CompleteTrainingSessionRequest(BaseModel):
    session_id: int = Field(..., description="Training session ID")
    completion_time: Optional[datetime] = Field(None, description="Session completion time")
    score: Optional[float] = Field(None, description="Session score")
    feedback: Optional[str] = Field(None, description="Session feedback")
    assessment_data: Optional[Dict[str, Any]] = Field(None, description="Assessment data")

class CreateAssessmentRequest(BaseModel):
    agent_id: str = Field(..., description="Agent ID")
    assessment_type: str = Field(..., description="Assessment type (knowledge, skills, performance)")
    module_id: Optional[int] = Field(None, description="Related module ID")
    questions: List[Dict[str, Any]] = Field(..., description="Assessment questions")
    passing_score: float = Field(..., description="Passing score percentage")
    time_limit: Optional[int] = Field(None, description="Time limit in minutes")

class TrainingModuleResponse(BaseModel):
    id: int
    module_name: str
    module_type: str
    difficulty_level: str
    content: str
    learning_objectives: List[str]
    estimated_duration: int
    prerequisites: List[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class TrainingSessionResponse(BaseModel):
    id: int
    agent_id: str
    module_id: int
    session_type: str
    status: str
    scheduled_at: Optional[datetime]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration: Optional[int]
    score: Optional[float]
    feedback: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class AgentPerformanceResponse(BaseModel):
    id: int
    agent_id: str
    performance_metrics: Dict[str, Any]
    skill_levels: Dict[str, Any]
    training_progress: Dict[str, Any]
    improvement_areas: List[str]
    strengths: List[str]
    assessment_date: datetime
    created_at: datetime

    class Config:
        from_attributes = True

class TrainingAssessmentResponse(BaseModel):
    id: int
    agent_id: str
    assessment_type: str
    module_id: Optional[int]
    questions: List[Dict[str, Any]]
    answers: Optional[List[Dict[str, Any]]]
    score: Optional[float]
    passing_score: float
    status: str
    time_limit: Optional[int]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True

class TrainingAnalyticsResponse(BaseModel):
    total_agents: int
    active_learners: int
    completion_rate: float
    average_score: float
    top_performers: List[Dict[str, Any]]
    struggling_agents: List[Dict[str, Any]]
    popular_modules: List[Dict[str, Any]]
    skill_gaps: List[Dict[str, Any]]

# Dependency
async def get_agent_training_service(db: AsyncSession = Depends(get_db)) -> AgentTrainingService:
    integration_manager = IntegrationManager()
    event_bus = EventBus()
    return AgentTrainingService(db, integration_manager, event_bus)

# Training Module Management
@router.post("/modules", response_model=TrainingModuleResponse, status_code=status.HTTP_201_CREATED)
async def create_training_module(
    request: CreateTrainingModuleRequest,
    service: AgentTrainingService = Depends(get_agent_training_service)
):
    """Create a new training module"""
    try:
        module = await service.create_training_module(
            module_name=request.module_name,
            module_type=request.module_type,
            difficulty_level=request.difficulty_level,
            content=request.content,
            learning_objectives=request.learning_objectives,
            estimated_duration=request.estimated_duration,
            prerequisites=request.prerequisites,
            is_active=request.is_active
        )
        return TrainingModuleResponse.from_orm(module)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/modules", response_model=List[TrainingModuleResponse])
async def get_training_modules(
    module_type: Optional[str] = None,
    difficulty_level: Optional[str] = None,
    active_only: bool = True,
    service: AgentTrainingService = Depends(get_agent_training_service)
):
    """Get training modules with optional filtering"""
    try:
        modules = await service.get_training_modules(
            module_type=module_type,
            difficulty_level=difficulty_level,
            active_only=active_only
        )
        return [TrainingModuleResponse.from_orm(module) for module in modules]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/modules/{module_id}", response_model=TrainingModuleResponse)
async def get_training_module(
    module_id: int,
    service: AgentTrainingService = Depends(get_agent_training_service)
):
    """Get a specific training module by ID"""
    try:
        module = await service.get_training_module(module_id)
        if not module:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Training module not found")
        return TrainingModuleResponse.from_orm(module)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.put("/modules/{module_id}", response_model=TrainingModuleResponse)
async def update_training_module(
    module_id: int,
    request: UpdateTrainingModuleRequest,
    service: AgentTrainingService = Depends(get_agent_training_service)
):
    """Update a training module"""
    try:
        module = await service.update_training_module(
            module_id=module_id,
            module_name=request.module_name,
            module_type=request.module_type,
            difficulty_level=request.difficulty_level,
            content=request.content,
            learning_objectives=request.learning_objectives,
            estimated_duration=request.estimated_duration,
            prerequisites=request.prerequisites,
            is_active=request.is_active
        )
        if not module:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Training module not found")
        return TrainingModuleResponse.from_orm(module)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.delete("/modules/{module_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_training_module(
    module_id: int,
    service: AgentTrainingService = Depends(get_agent_training_service)
):
    """Delete a training module"""
    try:
        success = await service.delete_training_module(module_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Training module not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Training Session Management
@router.post("/sessions", response_model=TrainingSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_training_session(
    request: CreateTrainingSessionRequest,
    service: AgentTrainingService = Depends(get_agent_training_service)
):
    """Create a new training session"""
    try:
        session = await service.create_training_session(
            agent_id=request.agent_id,
            module_id=request.module_id,
            session_type=request.session_type,
            scheduled_at=request.scheduled_at,
            duration=request.duration
        )
        return TrainingSessionResponse.from_orm(session)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/sessions", response_model=List[TrainingSessionResponse])
async def get_training_sessions(
    agent_id: Optional[str] = None,
    module_id: Optional[int] = None,
    status: Optional[str] = None,
    session_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    service: AgentTrainingService = Depends(get_agent_training_service)
):
    """Get training sessions with optional filtering"""
    try:
        sessions = await service.get_training_sessions(
            agent_id=agent_id,
            module_id=module_id,
            status=status,
            session_type=session_type,
            start_date=start_date,
            end_date=end_date
        )
        return [TrainingSessionResponse.from_orm(session) for session in sessions]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/sessions/{session_id}", response_model=TrainingSessionResponse)
async def get_training_session(
    session_id: int,
    service: AgentTrainingService = Depends(get_agent_training_service)
):
    """Get a specific training session by ID"""
    try:
        session = await service.get_training_session(session_id)
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Training session not found")
        return TrainingSessionResponse.from_orm(session)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.put("/sessions/{session_id}/start", response_model=TrainingSessionResponse)
async def start_training_session(
    session_id: int,
    request: StartTrainingSessionRequest,
    service: AgentTrainingService = Depends(get_agent_training_service)
):
    """Start a training session"""
    try:
        session = await service.start_training_session(
            session_id=session_id,
            start_time=request.start_time
        )
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Training session not found")
        return TrainingSessionResponse.from_orm(session)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.put("/sessions/{session_id}/complete", response_model=TrainingSessionResponse)
async def complete_training_session(
    session_id: int,
    request: CompleteTrainingSessionRequest,
    service: AgentTrainingService = Depends(get_agent_training_service)
):
    """Complete a training session"""
    try:
        session = await service.complete_training_session(
            session_id=session_id,
            completion_time=request.completion_time,
            score=request.score,
            feedback=request.feedback,
            assessment_data=request.assessment_data
        )
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Training session not found")
        return TrainingSessionResponse.from_orm(session)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

# Assessment Management
@router.post("/assessments", response_model=TrainingAssessmentResponse, status_code=status.HTTP_201_CREATED)
async def create_assessment(
    request: CreateAssessmentRequest,
    service: AgentTrainingService = Depends(get_agent_training_service)
):
    """Create a new training assessment"""
    try:
        assessment = await service.create_assessment(
            agent_id=request.agent_id,
            assessment_type=request.assessment_type,
            module_id=request.module_id,
            questions=request.questions,
            passing_score=request.passing_score,
            time_limit=request.time_limit
        )
        return TrainingAssessmentResponse.from_orm(assessment)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/assessments", response_model=List[TrainingAssessmentResponse])
async def get_assessments(
    agent_id: Optional[str] = None,
    assessment_type: Optional[str] = None,
    status: Optional[str] = None,
    service: AgentTrainingService = Depends(get_agent_training_service)
):
    """Get assessments with optional filtering"""
    try:
        assessments = await service.get_assessments(
            agent_id=agent_id,
            assessment_type=assessment_type,
            status=status
        )
        return [TrainingAssessmentResponse.from_orm(assessment) for assessment in assessments]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/assessments/{assessment_id}", response_model=TrainingAssessmentResponse)
async def get_assessment(
    assessment_id: int,
    service: AgentTrainingService = Depends(get_agent_training_service)
):
    """Get a specific assessment by ID"""
    try:
        assessment = await service.get_assessment(assessment_id)
        if not assessment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")
        return TrainingAssessmentResponse.from_orm(assessment)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.put("/assessments/{assessment_id}/start", response_model=TrainingAssessmentResponse)
async def start_assessment(
    assessment_id: int,
    service: AgentTrainingService = Depends(get_agent_training_service)
):
    """Start an assessment"""
    try:
        assessment = await service.start_assessment(assessment_id)
        if not assessment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")
        return TrainingAssessmentResponse.from_orm(assessment)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.put("/assessments/{assessment_id}/submit", response_model=TrainingAssessmentResponse)
async def submit_assessment(
    assessment_id: int,
    answers: List[Dict[str, Any]],
    service: AgentTrainingService = Depends(get_agent_training_service)
):
    """Submit assessment answers"""
    try:
        assessment = await service.submit_assessment(assessment_id, answers)
        if not assessment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")
        return TrainingAssessmentResponse.from_orm(assessment)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

# Agent Performance and Analytics
@router.get("/agents/{agent_id}/performance", response_model=AgentPerformanceResponse)
async def get_agent_performance(
    agent_id: str,
    service: AgentTrainingService = Depends(get_agent_training_service)
):
    """Get agent performance metrics"""
    try:
        performance = await service.get_agent_performance(agent_id)
        if not performance:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent performance not found")
        return AgentPerformanceResponse.from_orm(performance)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/agents/{agent_id}/assess-performance")
async def assess_agent_performance(
    agent_id: str,
    service: AgentTrainingService = Depends(get_agent_training_service)
):
    """Assess agent performance and generate recommendations"""
    try:
        assessment = await service.assess_agent_performance(agent_id)
        return assessment
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/analytics", response_model=TrainingAnalyticsResponse)
async def get_training_analytics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    service: AgentTrainingService = Depends(get_agent_training_service)
):
    """Get training analytics"""
    try:
        analytics = await service.get_training_analytics(
            start_date=start_date,
            end_date=end_date
        )
        return TrainingAnalyticsResponse(**analytics)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# AI-Driven Coaching and Recommendations
@router.post("/agents/{agent_id}/generate-recommendations")
async def generate_training_recommendations(
    agent_id: str,
    focus_areas: Optional[List[str]] = None,
    service: AgentTrainingService = Depends(get_agent_training_service)
):
    """Generate AI-driven training recommendations for an agent"""
    try:
        recommendations = await service.generate_training_recommendations(
            agent_id=agent_id,
            focus_areas=focus_areas
        )
        return recommendations
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/agents/{agent_id}/coaching-session")
async def create_coaching_session(
    agent_id: str,
    coaching_type: str,
    objectives: List[str],
    service: AgentTrainingService = Depends(get_agent_training_service)
):
    """Create an AI-driven coaching session"""
    try:
        coaching_session = await service.create_coaching_session(
            agent_id=agent_id,
            coaching_type=coaching_type,
            objectives=objectives
        )
        return coaching_session
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/agents/{agent_id}/skill-gap-analysis")
async def analyze_skill_gaps(
    agent_id: str,
    target_role: Optional[str] = None,
    service: AgentTrainingService = Depends(get_agent_training_service)
):
    """Analyze skill gaps for an agent"""
    try:
        skill_gaps = await service.analyze_skill_gaps(
            agent_id=agent_id,
            target_role=target_role
        )
        return skill_gaps
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Personalized Learning Paths
@router.post("/agents/{agent_id}/learning-path")
async def create_learning_path(
    agent_id: str,
    goals: List[str],
    timeline_weeks: int,
    service: AgentTrainingService = Depends(get_agent_training_service)
):
    """Create a personalized learning path for an agent"""
    try:
        learning_path = await service.create_learning_path(
            agent_id=agent_id,
            goals=goals,
            timeline_weeks=timeline_weeks
        )
        return learning_path
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/agents/{agent_id}/learning-progress")
async def get_learning_progress(
    agent_id: str,
    service: AgentTrainingService = Depends(get_agent_training_service)
):
    """Get agent learning progress"""
    try:
        progress = await service.get_learning_progress(agent_id)
        return progress
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Gamification and Motivation
@router.post("/agents/{agent_id}/achievements")
async def award_achievement(
    agent_id: str,
    achievement_type: str,
    achievement_data: Dict[str, Any],
    service: AgentTrainingService = Depends(get_agent_training_service)
):
    """Award an achievement to an agent"""
    try:
        achievement = await service.award_achievement(
            agent_id=agent_id,
            achievement_type=achievement_type,
            achievement_data=achievement_data
        )
        return achievement
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/agents/{agent_id}/leaderboard")
async def get_agent_leaderboard(
    agent_id: str,
    leaderboard_type: str = "overall",
    service: AgentTrainingService = Depends(get_agent_training_service)
):
    """Get agent leaderboard position"""
    try:
        leaderboard = await service.get_agent_leaderboard(
            agent_id=agent_id,
            leaderboard_type=leaderboard_type
        )
        return leaderboard
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Health Check
@router.get("/health")
async def health_check():
    """Health check endpoint for Agent Training Tools"""
    return {
        "status": "healthy",
        "service": "Agent Training Tools",
        "features": [
            "training_module_management",
            "training_session_tracking",
            "assessment_management",
            "agent_performance_analytics",
            "ai_driven_coaching",
            "skill_gap_analysis",
            "personalized_learning_paths",
            "gamification_achievements",
            "leaderboard_competition"
        ],
        "message": "Agent Training Tools service is running and ready!"
    }
