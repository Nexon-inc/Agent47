from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from datetime import datetime

from ..services.mobile_app_monitoring_service import MobileAppMonitoringService
from ..database import get_eric_database

router = APIRouter()

class MobileDashboardRequest(BaseModel):
    user_id: int
    brand_id: int

class ApprovalRequest(BaseModel):
    user_id: int
    action_id: int
    action_type: str
    approval_data: Dict[str, Any]

class RejectionRequest(BaseModel):
    user_id: int
    action_id: int
    action_type: str
    rejection_data: Dict[str, Any]

class MobilePreferencesRequest(BaseModel):
    user_id: int
    preferences: Dict[str, Any]

class MobilePreferencesResponse(BaseModel):
    success: bool
    preferences: Dict[str, Any]

class MobileDashboardResponse(BaseModel):
    success: bool
    dashboard: Dict[str, Any]
    last_updated: str

class ApprovalResponse(BaseModel):
    success: bool
    message: str
    action_id: int

class NotificationsResponse(BaseModel):
    success: bool
    notifications: List[Dict[str, Any]]
    unread_count: int
    last_updated: str

@router.get("/mobile/dashboard", response_model=MobileDashboardResponse)
async def get_mobile_dashboard(
    user_id: int = Query(..., description="User ID"),
    brand_id: int = Query(..., description="Brand ID")
):
    """Get mobile dashboard with real-time analytics and actionable insights"""
    try:
        service = MobileAppMonitoringService()
        result = await service.get_mobile_dashboard(user_id, brand_id)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/mobile/approve-action", response_model=ApprovalResponse)
async def approve_mobile_action(request: ApprovalRequest):
    """Approve a mobile action"""
    try:
        service = MobileAppMonitoringService()
        result = await service.approve_mobile_action(
            request.user_id,
            request.action_id,
            request.action_type,
            request.approval_data
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/mobile/reject-action", response_model=ApprovalResponse)
async def reject_mobile_action(request: RejectionRequest):
    """Reject a mobile action"""
    try:
        service = MobileAppMonitoringService()
        result = await service.reject_mobile_action(
            request.user_id,
            request.action_id,
            request.action_type,
            request.rejection_data
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/mobile/notifications", response_model=NotificationsResponse)
async def get_mobile_notifications(
    user_id: int = Query(..., description="User ID"),
    brand_id: int = Query(..., description="Brand ID"),
    limit: int = Query(20, description="Number of notifications to return")
):
    """Get mobile notifications for the user"""
    try:
        service = MobileAppMonitoringService()
        result = await service.get_mobile_notifications(user_id, brand_id, limit)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/mobile/preferences", response_model=MobilePreferencesResponse)
async def update_mobile_preferences(request: MobilePreferencesRequest):
    """Update mobile app preferences for the user"""
    try:
        service = MobileAppMonitoringService()
        result = await service.update_mobile_preferences(request.user_id, request.preferences)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/mobile/preferences", response_model=MobilePreferencesResponse)
async def get_mobile_preferences(
    user_id: int = Query(..., description="User ID")
):
    """Get mobile app preferences for the user"""
    try:
        service = MobileAppMonitoringService()
        result = await service.get_mobile_preferences(user_id)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/mobile/urgent-actions")
async def get_urgent_actions(
    brand_id: int = Query(..., description="Brand ID")
):
    """Get urgent actions that require immediate attention"""
    try:
        service = MobileAppMonitoringService()
        db = await get_eric_database()
        async with db.get_session() as session:
            urgent_actions = await service._get_urgent_actions(session, brand_id)
            return {
                "success": True,
                "urgent_actions": urgent_actions
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/mobile/performance-alerts")
async def get_performance_alerts(
    brand_id: int = Query(..., description="Brand ID")
):
    """Get performance alerts and warnings"""
    try:
        service = MobileAppMonitoringService()
        db = await get_eric_database()
        async with db.get_session() as session:
            alerts = await service._get_performance_alerts(session, brand_id)
            return {
                "success": True,
                "alerts": alerts
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/mobile/quick-insights")
async def get_quick_insights(
    brand_id: int = Query(..., description="Brand ID")
):
    """Get quick insights and trends"""
    try:
        service = MobileAppMonitoringService()
        db = await get_eric_database()
        async with db.get_session() as session:
            insights = await service._get_quick_insights(session, brand_id)
            return {
                "success": True,
                "insights": insights
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/mobile/pending-approvals")
async def get_pending_approvals(
    user_id: int = Query(..., description="User ID"),
    brand_id: int = Query(..., description="Brand ID")
):
    """Get pending approvals for the user"""
    try:
        service = MobileAppMonitoringService()
        db = await get_eric_database()
        async with db.get_session() as session:
            approvals = await service._get_pending_approvals(session, user_id, brand_id)
            return {
                "success": True,
                "pending_approvals": approvals
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/mobile/real-time-notifications")
async def get_real_time_notifications(
    brand_id: int = Query(..., description="Brand ID")
):
    """Get real-time notifications"""
    try:
        service = MobileAppMonitoringService()
        db = await get_eric_database()
        async with db.get_session() as session:
            notifications = await service._get_real_time_notifications(session, brand_id)
            return {
                "success": True,
                "notifications": notifications
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
