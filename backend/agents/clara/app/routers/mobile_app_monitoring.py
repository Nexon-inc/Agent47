from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session

from ..database import get_clara_database, get_db
from ..services.mobile_app_monitoring_service import MobileAppMonitoringService
from ..schemas.mobile_app_monitoring import (
    CreateMobileAppUserRequest, UpdateMobileAppUserRequest,
    CreateMobileAppSessionRequest, UpdateMobileAppSessionRequest,
    CreateMobileAppOverrideRequest, UpdateMobileAppOverrideRequest,
    CreateMobileAppNotificationRequest, UpdateMobileAppNotificationRequest,
    MobileAppUserResponse, MobileAppSessionResponse, MobileAppOverrideResponse,
    MobileAppNotificationResponse, MobileAppDeviceResponse, MobileAppAnalyticsResponse
)

router = APIRouter()
mobile_app_service = MobileAppMonitoringService()


@router.post("/users", response_model=MobileAppUserResponse)
async def create_mobile_app_user(
    request: CreateMobileAppUserRequest,
    db: Session = Depends(get_db)
):
    """Create a new mobile app user"""
    return await mobile_app_service.create_mobile_app_user(db, request)


@router.get("/users/{user_id}", response_model=MobileAppUserResponse)
async def get_mobile_app_user(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Get mobile app user by ID"""
    return await mobile_app_service.get_mobile_app_user(db, user_id)


@router.get("/users", response_model=List[MobileAppUserResponse])
async def list_mobile_app_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    role: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    """List mobile app users"""
    return await mobile_app_service.list_mobile_app_users(
        db, skip=skip, limit=limit, role=role, is_active=is_active
    )


@router.put("/users/{user_id}", response_model=MobileAppUserResponse)
async def update_mobile_app_user(
    user_id: int,
    request: UpdateMobileAppUserRequest,
    db: Session = Depends(get_db)
):
    """Update mobile app user"""
    return await mobile_app_service.update_mobile_app_user(db, user_id, request)


@router.delete("/users/{user_id}")
async def delete_mobile_app_user(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Delete mobile app user"""
    return await mobile_app_service.delete_mobile_app_user(db, user_id)


@router.post("/sessions", response_model=MobileAppSessionResponse)
async def create_mobile_app_session(
    request: CreateMobileAppSessionRequest,
    db: Session = Depends(get_db)
):
    """Create a new mobile app session"""
    return await mobile_app_service.create_mobile_app_session(db, request)


@router.get("/sessions/{session_id}", response_model=MobileAppSessionResponse)
async def get_mobile_app_session(
    session_id: int,
    db: Session = Depends(get_db)
):
    """Get mobile app session by ID"""
    return await mobile_app_service.get_mobile_app_session(db, session_id)


@router.get("/sessions", response_model=List[MobileAppSessionResponse])
async def list_mobile_app_sessions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    user_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List mobile app sessions"""
    return await mobile_app_service.list_mobile_app_sessions(
        db, skip=skip, limit=limit, user_id=user_id, status=status
    )


@router.put("/sessions/{session_id}", response_model=MobileAppSessionResponse)
async def update_mobile_app_session(
    session_id: int,
    request: UpdateMobileAppSessionRequest,
    db: Session = Depends(get_db)
):
    """Update mobile app session"""
    return await mobile_app_service.update_mobile_app_session(db, session_id, request)


@router.delete("/sessions/{session_id}")
async def delete_mobile_app_session(
    session_id: int,
    db: Session = Depends(get_db)
):
    """Delete mobile app session"""
    return await mobile_app_service.delete_mobile_app_session(db, session_id)


@router.post("/overrides", response_model=MobileAppOverrideResponse)
async def create_mobile_app_override(
    request: CreateMobileAppOverrideRequest,
    db: Session = Depends(get_db)
):
    """Create a new mobile app override"""
    return await mobile_app_service.create_mobile_app_override(db, request)


@router.get("/overrides/{override_id}", response_model=MobileAppOverrideResponse)
async def get_mobile_app_override(
    override_id: int,
    db: Session = Depends(get_db)
):
    """Get mobile app override by ID"""
    return await mobile_app_service.get_mobile_app_override(db, override_id)


@router.get("/overrides", response_model=List[MobileAppOverrideResponse])
async def list_mobile_app_overrides(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    user_id: Optional[int] = Query(None),
    ticket_id: Optional[int] = Query(None),
    override_type: Optional[str] = Query(None),
    is_approved: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    """List mobile app overrides"""
    return await mobile_app_service.list_mobile_app_overrides(
        db, skip=skip, limit=limit, user_id=user_id, ticket_id=ticket_id,
        override_type=override_type, is_approved=is_approved
    )


@router.put("/overrides/{override_id}", response_model=MobileAppOverrideResponse)
async def update_mobile_app_override(
    override_id: int,
    request: UpdateMobileAppOverrideRequest,
    db: Session = Depends(get_db)
):
    """Update mobile app override"""
    return await mobile_app_service.update_mobile_app_override(db, override_id, request)


@router.delete("/overrides/{override_id}")
async def delete_mobile_app_override(
    override_id: int,
    db: Session = Depends(get_db)
):
    """Delete mobile app override"""
    return await mobile_app_service.delete_mobile_app_override(db, override_id)


@router.post("/overrides/{override_id}/approve", response_model=MobileAppOverrideResponse)
async def approve_mobile_app_override(
    override_id: int,
    approved_by: int = Query(...),
    db: Session = Depends(get_db)
):
    """Approve a mobile app override"""
    return await mobile_app_service.approve_mobile_app_override(db, override_id, approved_by)


@router.post("/notifications", response_model=MobileAppNotificationResponse)
async def create_mobile_app_notification(
    request: CreateMobileAppNotificationRequest,
    db: Session = Depends(get_db)
):
    """Create a new mobile app notification"""
    return await mobile_app_service.create_mobile_app_notification(db, request)


@router.get("/notifications/{notification_id}", response_model=MobileAppNotificationResponse)
async def get_mobile_app_notification(
    notification_id: int,
    db: Session = Depends(get_db)
):
    """Get mobile app notification by ID"""
    return await mobile_app_service.get_mobile_app_notification(db, notification_id)


@router.get("/notifications", response_model=List[MobileAppNotificationResponse])
async def list_mobile_app_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    user_id: Optional[int] = Query(None),
    notification_type: Optional[str] = Query(None),
    is_read: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    """List mobile app notifications"""
    return await mobile_app_service.list_mobile_app_notifications(
        db, skip=skip, limit=limit, user_id=user_id,
        notification_type=notification_type, is_read=is_read
    )


@router.put("/notifications/{notification_id}", response_model=MobileAppNotificationResponse)
async def update_mobile_app_notification(
    notification_id: int,
    request: UpdateMobileAppNotificationRequest,
    db: Session = Depends(get_db)
):
    """Update mobile app notification"""
    return await mobile_app_service.update_mobile_app_notification(db, notification_id, request)


@router.delete("/notifications/{notification_id}")
async def delete_mobile_app_notification(
    notification_id: int,
    db: Session = Depends(get_db)
):
    """Delete mobile app notification"""
    return await mobile_app_service.delete_mobile_app_notification(db, notification_id)


@router.post("/notifications/{notification_id}/mark-read", response_model=MobileAppNotificationResponse)
async def mark_notification_as_read(
    notification_id: int,
    db: Session = Depends(get_db)
):
    """Mark notification as read"""
    return await mobile_app_service.mark_notification_as_read(db, notification_id)


@router.get("/analytics", response_model=MobileAppAnalyticsResponse)
async def get_mobile_app_analytics(
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    user_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """Get mobile app analytics"""
    return await mobile_app_service.get_mobile_app_analytics(db, start_date, end_date, user_id)


@router.get("/health")
async def health_check():
    """Check the health of mobile app monitoring system"""
    return await mobile_app_service.health_check()
