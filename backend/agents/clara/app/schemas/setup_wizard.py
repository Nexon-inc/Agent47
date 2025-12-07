from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class SetupStep(BaseModel):
    id: str
    name: str
    type: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = {}

class SetupWizardResponse(BaseModel):
    steps: List[SetupStep]
    status: Optional[str] = None


class CreateSetupWizardStepRequest(BaseModel):
    title: str
    description: Optional[str] = None
    step_type: Optional[str] = None
    content: Optional[Dict[str, Any]] = {}
    order_index: Optional[int] = 0
    is_required: bool = False
    validation_rules: Optional[Dict[str, Any]] = {}
    help_text: Optional[str] = None


class UpdateSetupWizardStepRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    step_type: Optional[str] = None
    content: Optional[Dict[str, Any]] = None
    order_index: Optional[int] = None
    is_required: Optional[bool] = None
    validation_rules: Optional[Dict[str, Any]] = None
    help_text: Optional[str] = None


class CreateSetupWizardSessionRequest(BaseModel):
    user_id: int
    steps_completed: Optional[List[str]] = []


class UpdateSetupWizardSessionRequest(BaseModel):
    steps_completed: Optional[List[str]] = None
    current_step: Optional[str] = None


class CreateSetupWizardConfigRequest(BaseModel):
    name: str
    config: Dict[str, Any]


class UpdateSetupWizardConfigRequest(BaseModel):
    name: Optional[str] = None
    config: Optional[Dict[str, Any]] = None


class SetupWizardStepResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    step_type: Optional[str] = None
    content: Optional[Dict[str, Any]] = None
    order_index: Optional[int] = None
    is_required: bool = False
    validation_rules: Optional[Dict[str, Any]] = None
    help_text: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class SetupWizardSessionResponse(BaseModel):
    id: int
    user_id: int
    steps_completed: List[str]
    current_step: Optional[str] = None
    status: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class SetupWizardConfigResponse(BaseModel):
    id: int
    name: str
    config: Dict[str, Any]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class SetupWizardValidationResponse(BaseModel):
    id: int
    validation_type: Optional[str] = None
    field: Optional[str] = None
    message: Optional[str] = None


class SetupWizardAnalyticsResponse(BaseModel):
    total_sessions: int
    completed_sessions: int
    failed_sessions: int


class CreateSetupWizardValidationRequest(BaseModel):
    validation_type: str
    field: str
    message: Optional[str] = None
    rules: Optional[Dict[str, Any]] = None


class UpdateSetupWizardValidationRequest(BaseModel):
    validation_type: Optional[str] = None
    field: Optional[str] = None
    message: Optional[str] = None
    rules: Optional[Dict[str, Any]] = None
