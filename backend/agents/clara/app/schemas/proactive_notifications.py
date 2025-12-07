from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class CreateNotificationRuleRequest(BaseModel):
    name: str
    description: Optional[str] = None
    conditions: Dict[str, Any]
    actions: List[Dict[str, Any]]
    is_active: bool = True
    priority: Optional[str] = "medium"
    schedule: Optional[Dict[str, Any]] = None


class UpdateNotificationRuleRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    conditions: Optional[Dict[str, Any]] = None
    actions: Optional[List[Dict[str, Any]]] = None
    is_active: Optional[bool] = None
    priority: Optional[str] = None
    schedule: Optional[Dict[str, Any]] = None


class CreateNotificationTemplateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    content: str
    variables: Optional[List[str]] = []
    channel: Optional[str] = "email"
    is_active: bool = True


class UpdateNotificationTemplateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    variables: Optional[List[str]] = None
    channel: Optional[str] = None
    is_active: Optional[bool] = None


class SendProactiveNotificationRequest(BaseModel):
    recipients: List[str]
    template_id: Optional[int] = None
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class NotificationRuleResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    conditions: Dict[str, Any]
    actions: List[Dict[str, Any]]
    is_active: bool
    priority: Optional[str] = None
    schedule: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class NotificationTemplateResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    content: str
    variables: List[str] = []
    channel: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ProactiveNotificationResponse(BaseModel):
    id: int
    rule_id: Optional[int] = None
    template_id: Optional[int] = None
    recipients: List[str] = []
    sent_at: Optional[datetime] = None


class NotificationAnalyticsResponse(BaseModel):
    rule_id: int
    sent_count: int
    delivered_count: int
    failed_count: int
    opened_count: int
