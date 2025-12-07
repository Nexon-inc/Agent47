from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class PredictiveIssueRequest(BaseModel):
    ticket_id: int
    features: Dict[str, Any]

class PredictiveIssueResponse(BaseModel):
    ticket_id: int
    predicted_issue_type: Optional[str]
    confidence: float = 0.0


class CreatePredictionModelRequest(BaseModel):
    name: str
    description: Optional[str] = None
    model_type: str
    features: List[str]
    hyperparameters: Dict[str, Any] = {}
    is_active: bool = True


class UpdatePredictionModelRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    model_type: Optional[str] = None
    features: Optional[List[str]] = None
    hyperparameters: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class CreateAlertRuleRequest(BaseModel):
    name: str
    conditions: Dict[str, Any]
    actions: List[Dict[str, Any]]


class UpdateAlertRuleRequest(BaseModel):
    name: Optional[str] = None
    conditions: Optional[Dict[str, Any]] = None
    actions: Optional[List[Dict[str, Any]]] = None


class TrackSystemMetricRequest(BaseModel):
    metric_name: str
    value: float
    timestamp: Optional[datetime] = None


class PredictionModelResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    model_type: str
    features: List[str]
    hyperparameters: Dict[str, Any]
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class AlertRuleResponse(BaseModel):
    id: int
    name: str
    conditions: Dict[str, Any]
    actions: List[Dict[str, Any]]
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class SystemMetricResponse(BaseModel):
    id: int
    metric_name: str
    value: float
    timestamp: Optional[datetime] = None


class IssuePredictionResponse(BaseModel):
    id: int
    ticket_id: int
    predicted_issue_type: Optional[str]
    confidence: float
    created_at: Optional[datetime] = None


class DetectionAnalyticsResponse(BaseModel):
    total_predictions: int
    true_positives: int
    false_positives: int
    false_negatives: int
    precision: float
    recall: float
    f1_score: float
