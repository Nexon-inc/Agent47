"""
Onboarding Assistance Schemas
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum

class OnboardingStepType(str, Enum):
    WELCOME = "welcome"
    PROFILE_SETUP = "profile_setup"
    PREFERENCES = "preferences"
    INTEGRATION = "integration"
    TESTING = "testing"
    COMPLETION = "completion"

class OnboardingStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"

# Onboarding Step Schemas
class OnboardingStepBase(BaseModel):
    step_type: OnboardingStepType
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    content: Optional[str] = None
    order_index: int
    is_required: bool = True
    is_active: bool = True

class OnboardingStepCreate(OnboardingStepBase):
    pass

class OnboardingStepUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    content: Optional[str] = None
    order_index: Optional[int] = None
    is_required: Optional[bool] = None
    is_active: Optional[bool] = None

class OnboardingStepResponse(OnboardingStepBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Onboarding Session Schemas
class OnboardingSessionBase(BaseModel):
    user_id: int
    current_step_id: Optional[int] = None
    status: OnboardingStatus = OnboardingStatus.NOT_STARTED
    progress_percentage: float = 0.0
    metadata: Dict[str, Any] = {}

class OnboardingSessionCreate(OnboardingSessionBase):
    pass

class OnboardingSessionUpdate(BaseModel):
    current_step_id: Optional[int] = None
    status: Optional[OnboardingStatus] = None
    progress_percentage: Optional[float] = Field(None, ge=0.0, le=100.0)
    metadata: Optional[Dict[str, Any]] = None

class OnboardingSessionResponse(OnboardingSessionBase):
    id: int
    start_time: datetime
    completion_time: Optional[datetime] = None

    class Config:
        from_attributes = True

# Onboarding Tutorial Schemas
class OnboardingTutorialBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    content: str = Field(..., min_length=1)
    video_url: Optional[str] = None
    step_id: Optional[int] = None
    is_active: bool = True

class OnboardingTutorialCreate(OnboardingTutorialBase):
    pass

class OnboardingTutorialUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    content: Optional[str] = Field(None, min_length=1)
    video_url: Optional[str] = None
    step_id: Optional[int] = None
    is_active: Optional[bool] = None

class OnboardingTutorialResponse(OnboardingTutorialBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Onboarding Progress Schemas
class OnboardingProgressBase(BaseModel):
    session_id: int
    step_id: int
    status: OnboardingStatus = OnboardingStatus.NOT_STARTED
    time_spent: Optional[int] = None  # in seconds
    metadata: Dict[str, Any] = {}

class OnboardingProgressCreate(OnboardingProgressBase):
    pass

class OnboardingProgressUpdate(BaseModel):
    status: Optional[OnboardingStatus] = None
    time_spent: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None

class OnboardingProgressResponse(OnboardingProgressBase):
    id: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Onboarding Analytics Schemas
class OnboardingAnalyticsRequest(BaseModel):
    start_date: datetime
    end_date: datetime
    user_id: Optional[int] = None
    step_type: Optional[OnboardingStepType] = None

class OnboardingAnalyticsResponse(BaseModel):
    total_sessions: int
    completed_sessions: int
    abandoned_sessions: int
    average_completion_time: float  # in minutes
    step_completion_rates: Dict[str, float]
    common_dropoff_points: List[str]
    user_satisfaction: float
    recommendations: List[str]

# Onboarding Flow Schemas
class OnboardingFlowRequest(BaseModel):
    user_id: int
    flow_type: str = "standard"
    custom_steps: Optional[List[Dict[str, Any]]] = None

class OnboardingFlowResponse(BaseModel):
    session_id: int
    flow_type: str
    total_steps: int
    current_step: int
    progress_percentage: float
    estimated_completion_time: int  # in minutes
    next_step: Optional[OnboardingStepResponse] = None
    completed_steps: List[OnboardingStepResponse]
    remaining_steps: List[OnboardingStepResponse]

# Onboarding Checklist Schemas
class OnboardingChecklistItem(BaseModel):
    step_id: int
    title: str
    description: str
    is_completed: bool
    is_required: bool
    order_index: int

class OnboardingChecklistResponse(BaseModel):
    session_id: int
    user_id: int
    total_items: int
    completed_items: int
    required_items: int
    completed_required_items: int
    progress_percentage: float
    items: List[OnboardingChecklistItem]
    can_proceed: bool
    next_required_step: Optional[OnboardingChecklistItem] = None

# Onboarding Help Schemas
class OnboardingHelpRequest(BaseModel):
    session_id: int
    step_id: int
    help_type: str  # tutorial, video, documentation, support
    specific_question: Optional[str] = None

class OnboardingHelpResponse(BaseModel):
    help_id: str
    help_type: str
    content: str
    resources: List[Dict[str, Any]]
    related_tutorials: List[OnboardingTutorialResponse]
    support_contact: Optional[Dict[str, str]] = None

# Onboarding Feedback Schemas
class OnboardingFeedbackRequest(BaseModel):
    session_id: int
    step_id: int
    rating: int = Field(..., ge=1, le=5)
    feedback: Optional[str] = None
    difficulty_level: Optional[str] = None
    suggestions: Optional[str] = None

class OnboardingFeedbackResponse(BaseModel):
    id: int
    session_id: int
    step_id: int
    rating: int
    feedback: Optional[str] = None
    difficulty_level: Optional[str] = None
    suggestions: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

# Onboarding Skip Schemas
class OnboardingSkipRequest(BaseModel):
    session_id: int
    step_id: int
    reason: str
    skip_permanently: bool = False

class OnboardingSkipResponse(BaseModel):
    success: bool
    skipped_step: OnboardingStepResponse
    next_step: Optional[OnboardingStepResponse] = None
    updated_progress: float
    message: str

# Onboarding Restart Schemas
class OnboardingRestartRequest(BaseModel):
    session_id: int
    restart_from_step: Optional[int] = None
    clear_progress: bool = False

class OnboardingRestartResponse(BaseModel):
    success: bool
    new_session_id: int
    current_step: OnboardingStepResponse
    progress_percentage: float
    message: str

# Onboarding Completion Schemas
class OnboardingCompletionRequest(BaseModel):
    session_id: int
    final_feedback: Optional[str] = None
    satisfaction_rating: Optional[int] = Field(None, ge=1, le=5)

class OnboardingCompletionResponse(BaseModel):
    success: bool
    session_id: int
    completion_time: datetime
    total_time_spent: int  # in minutes
    certificate_url: Optional[str] = None
    next_steps: List[str]
    welcome_message: str
