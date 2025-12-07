from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class CreateCoachingSessionRequest(BaseModel):
    agent_id: int
    call_id: Optional[str] = None
    recorded_audio_url: Optional[str] = None
    notes: Optional[str] = None


class UpdateCoachingSessionRequest(BaseModel):
    session_id: int
    notes: Optional[str] = None
    score: Optional[float] = None


class CoachingSessionResponse(BaseModel):
    id: int
    agent_id: int
    call_id: Optional[str]
    recorded_audio_url: Optional[str]
    notes: Optional[str]
    score: Optional[float]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


class CoachingAnalyticsResponse(BaseModel):
    total_sessions: int
    average_score: Optional[float]
    sessions_by_agent: Dict[int, int]


# --- Aliases / expected names used by service imports ---
class CreateVoiceSentimentSessionRequest(BaseModel):
    agent_id: int
    session_type: Optional[str] = None
    total_scenarios: Optional[int] = None


class UpdateVoiceSentimentSessionRequest(BaseModel):
    session_id: int
    status: Optional[str] = None
    scenarios_completed: Optional[int] = None


class CreateVoiceSentimentAnalysisRequest(BaseModel):
    session_id: int
    scenario_id: Optional[int] = None
    audio_data: Optional[str] = None
    transcript: Optional[str] = None


class UpdateVoiceSentimentAnalysisRequest(BaseModel):
    analysis_id: int
    audio_data: Optional[str] = None
    transcript: Optional[str] = None
    sentiment_type: Optional[str] = None
    sentiment_score: Optional[float] = None


class CreateVoiceSentimentFeedbackRequest(BaseModel):
    analysis_id: int
    agent_id: int
    feedback_type: Optional[str] = None
    feedback_text: Optional[str] = None
    improvement_suggestions: Optional[List[str]] = []
    empathy_score: Optional[float] = None
    tone_score: Optional[float] = None
    response_effectiveness: Optional[float] = None


class UpdateVoiceSentimentFeedbackRequest(BaseModel):
    feedback_id: int
    feedback_text: Optional[str] = None
    empathy_score: Optional[float] = None
    tone_score: Optional[float] = None


class CreateVoiceSentimentCoachingRequest(BaseModel):
    session_id: int
    coach_id: Optional[int] = None
    notes: Optional[str] = None


class UpdateVoiceSentimentCoachingRequest(BaseModel):
    coaching_id: int
    notes: Optional[str] = None
    outcome: Optional[str] = None


class CreateVoiceSentimentScenarioRequest(BaseModel):
    name: str
    description: Optional[str] = None
    example_transcript: Optional[str] = None


class UpdateVoiceSentimentScenarioRequest(BaseModel):
    scenario_id: int
    name: Optional[str] = None
    description: Optional[str] = None


# Response aliases
class VoiceSentimentSessionResponse(CoachingSessionResponse):
    pass


class VoiceSentimentAnalysisResponse(BaseModel):
    id: int
    session_id: int
    scenario_id: Optional[int]
    audio_data: Optional[str]
    transcript: Optional[str]
    sentiment_type: Optional[str]
    sentiment_score: Optional[float]
    confidence_score: Optional[float]
    detected_emotions: Optional[List[str]] = []
    tone_analysis: Optional[Dict[str, Any]] = {}
    created_at: Optional[datetime] = None


class VoiceSentimentFeedbackResponse(BaseModel):
    id: int
    analysis_id: int
    agent_id: int
    feedback_type: Optional[str]
    feedback_text: Optional[str]
    empathy_score: Optional[float]
    tone_score: Optional[float]
    response_effectiveness: Optional[float]
    created_at: Optional[datetime] = None


class VoiceSentimentCoachingResponse(BaseModel):
    id: int
    session_id: int
    coach_id: Optional[int]
    notes: Optional[str]
    outcome: Optional[str]
    created_at: Optional[datetime] = None


class VoiceSentimentScenarioResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    example_transcript: Optional[str]


class VoiceSentimentAnalyticsResponse(CoachingAnalyticsResponse):
    pass

