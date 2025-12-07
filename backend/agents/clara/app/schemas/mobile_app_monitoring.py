from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class MobileAppMetricRequest(BaseModel):
    app_id: str
    metrics: Dict[str, Any]

class MobileAppMetricResponse(BaseModel):
    id: int
    app_id: str
    metrics: Dict[str, Any]
    recorded_at: Optional[datetime] = None


class CreateMobileAppUserRequest(BaseModel):
    username: str
    email: str
    role: Optional[str] = "agent"
    permissions: Optional[List[str]] = []
    device_ids: Optional[List[str]] = []
    is_active: bool = True


class UpdateMobileAppUserRequest(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    permissions: Optional[List[str]] = None
    device_ids: Optional[List[str]] = None
    is_active: Optional[bool] = None


class CreateMobileAppSessionRequest(BaseModel):
    user_id: int
    device_id: Optional[str] = None


class UpdateMobileAppSessionRequest(BaseModel):
    last_active_at: Optional[datetime] = None


class CreateMobileAppOverrideRequest(BaseModel):
    user_id: int
    override_type: str
    data: Dict[str, Any]


class UpdateMobileAppOverrideRequest(BaseModel):
    data: Optional[Dict[str, Any]] = None


class CreateMobileAppNotificationRequest(BaseModel):
    title: str
    message: str
    recipients: List[str]


class UpdateMobileAppNotificationRequest(BaseModel):
    title: Optional[str] = None
    message: Optional[str] = None


class MobileAppUserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    permissions: List[str]
    device_ids: List[str]
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class MobileAppSessionResponse(BaseModel):
    id: int
    user_id: int
    device_id: Optional[str] = None
    last_active_at: Optional[datetime] = None


class MobileAppOverrideResponse(BaseModel):
    id: int
    user_id: int
    override_type: str
    data: Dict[str, Any]
    created_at: Optional[datetime] = None


class MobileAppNotificationResponse(BaseModel):
    id: int
    title: str
    message: str
    recipients: List[str]
    sent_at: Optional[datetime] = None


class MobileAppDeviceResponse(BaseModel):
    id: int
    device_id: str
    device_type: str
    created_at: Optional[datetime] = None


class MobileAppAnalyticsResponse(BaseModel):
    total_users: int
    active_sessions: int
    notifications_sent: int
