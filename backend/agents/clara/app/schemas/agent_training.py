"""
Agent Training Schemas
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum

class TrainingStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PAUSED = "paused"
    FAILED = "failed"

class AssessmentType(str, Enum):
    QUIZ = "quiz"
    PRACTICAL = "practical"
    SIMULATION = "simulation"
    PEER_REVIEW = "peer_review"

class DifficultyLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"

# Training Module Schemas
class CreateTrainingModuleRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    content: str = Field(..., min_length=1)
    difficulty_level: DifficultyLevel = DifficultyLevel.BEGINNER
    estimated_duration: Optional[int] = Field(None, ge=1)  # in minutes
    skills_covered: List[str] = []
    prerequisites: List[str] = []
    is_active: bool = True

class UpdateTrainingModuleRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    content: Optional[str] = Field(None, min_length=1)
    difficulty_level: Optional[DifficultyLevel] = None
    estimated_duration: Optional[int] = Field(None, ge=1)
    skills_covered: Optional[List[str]] = None
    prerequisites: Optional[List[str]] = None
    is_active: Optional[bool] = None

class TrainingModuleResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    content: str
    difficulty_level: str
    estimated_duration: Optional[int] = None
    skills_covered: List[str]
    prerequisites: List[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Training Session Schemas
class CreateTrainingSessionRequest(BaseModel):
    agent_id: int
    module_id: int
    start_time: Optional[datetime] = None

class StartTrainingSessionRequest(BaseModel):
    session_id: int
    start_time: Optional[datetime] = None

class CompleteTrainingSessionRequest(BaseModel):
    session_id: int
    end_time: Optional[datetime] = None
    score: Optional[float] = Field(None, ge=0.0, le=100.0)
    feedback: Optional[str] = None

class TrainingSessionResponse(BaseModel):
    id: int
    agent_id: int
    module_id: int
    status: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[int] = None  # in minutes
    progress: float = 0.0
    score: Optional[float] = None
    feedback: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

# Agent Performance Schemas
class AgentPerformanceResponse(BaseModel):
    id: int
    agent_id: int
    period_start: datetime
    period_end: datetime
    tickets_resolved: int
    average_resolution_time: Optional[float] = None
    customer_satisfaction: Optional[float] = None
    first_contact_resolution_rate: Optional[float] = None
    training_completion_rate: Optional[float] = None
    performance_score: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True

# Training Assessment Schemas
class CreateAssessmentRequest(BaseModel):
    session_id: int
    assessment_type: AssessmentType
    questions: List[Dict[str, Any]]
    max_score: float = 100.0

class TrainingAssessmentResponse(BaseModel):
    id: int
    session_id: int
    assessment_type: str
    questions: List[Dict[str, Any]]
    answers: Dict[str, Any] = {}
    score: Optional[float] = None
    max_score: float
    passed: Optional[bool] = None
    feedback: Optional[str] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

# Training Analytics Schemas
class TrainingAnalyticsResponse(BaseModel):
    total_modules: int
    total_sessions: int
    completed_sessions: int
    average_completion_rate: float
    average_score: float
    top_performers: List[Dict[str, Any]]
    module_performance: Dict[str, Any]
    skill_gaps: List[str]
    recommendations: List[str]

# Progress Tracking Schemas
class TrainingProgressRequest(BaseModel):
    agent_id: int
    module_id: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

class TrainingProgressResponse(BaseModel):
    agent_id: int
    total_modules_assigned: int
    modules_completed: int
    modules_in_progress: int
    modules_not_started: int
    overall_progress: float
    current_module: Optional[TrainingModuleResponse] = None
    recent_sessions: List[TrainingSessionResponse]
    performance_trend: List[Dict[str, Any]]

# Skill Assessment Schemas
class SkillAssessmentRequest(BaseModel):
    agent_id: int
    skills: List[str]

class SkillAssessmentResponse(BaseModel):
    agent_id: int
    skills_assessed: List[str]
    skill_levels: Dict[str, float]  # skill_name -> proficiency_score
    skill_gaps: List[str]
    recommended_modules: List[TrainingModuleResponse]
    improvement_plan: Dict[str, Any]

# Certification Schemas
class CertificationRequest(BaseModel):
    agent_id: int
    certification_type: str
    modules_required: List[int]
    minimum_score: float = 80.0

class CertificationResponse(BaseModel):
    id: int
    agent_id: int
    certification_type: str
    status: str  # pending, in_progress, completed, failed
    modules_completed: List[int]
    overall_score: Optional[float] = None
    issued_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

# Peer Review Schemas
class PeerReviewRequest(BaseModel):
    reviewer_id: int
    reviewee_id: int
    session_id: int
    review_criteria: List[str]
    comments: str

class PeerReviewResponse(BaseModel):
    id: int
    reviewer_id: int
    reviewee_id: int
    session_id: int
    review_criteria: List[str]
    scores: Dict[str, float]
    comments: str
    overall_score: float
    created_at: datetime

    class Config:
        from_attributes = True

# Training Recommendations Schemas
class TrainingRecommendationRequest(BaseModel):
    agent_id: int
    include_completed: bool = False
    limit: int = Field(5, ge=1, le=20)

class TrainingRecommendationResponse(BaseModel):
    agent_id: int
    recommendations: List[TrainingModuleResponse]
    reasoning: Dict[str, Any]
    priority_order: List[int]
    estimated_completion_time: int  # in hours

# Bulk Training Operations Schemas
class BulkTrainingAssignmentRequest(BaseModel):
    agent_ids: List[int]
    module_ids: List[int]
    start_date: Optional[datetime] = None
    deadline: Optional[datetime] = None

class BulkTrainingAssignmentResponse(BaseModel):
    success: bool
    total_assignments: int
    successful_assignments: int
    failed_assignments: int
    errors: List[Dict[str, Any]]
    assignments: List[TrainingSessionResponse]
