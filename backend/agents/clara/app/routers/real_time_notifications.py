from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel
from ..services.real_time_notifications_service import RealTimeNotificationsService
from ..models import SupportChannel, TicketPriority, TicketStatus, TicketCategory

router = APIRouter()

# Pydantic models for request/response
class EscalationNotificationRequest(BaseModel):
    escalated_to_agent_id: int
    reason: str
    channels: Optional[List[str]] = None

class SatisfactionAlertRequest(BaseModel):
    satisfaction_score: int
    channels: Optional[List[str]] = None

async def get_notifications_service() -> RealTimeNotificationsService:
    """Dependency to get real-time notifications service"""
    service = RealTimeNotificationsService()
    await service.initialize()
    return service

@router.post("/urgent-ticket/{ticket_id}", response_model=Dict[str, Any])
async def send_urgent_ticket_notification(
    ticket_id: int,
    channels: Optional[List[str]] = Query(None),
    notifications_service: RealTimeNotificationsService = Depends(get_notifications_service)
):
    """Send notification for urgent ticket creation"""
    try:
        result = await notifications_service.send_urgent_ticket_notification(
            ticket_id=ticket_id,
            channels=channels
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sla-breach/{ticket_id}", response_model=Dict[str, Any])
async def send_sla_breach_notification(
    ticket_id: int,
    channels: Optional[List[str]] = Query(None),
    notifications_service: RealTimeNotificationsService = Depends(get_notifications_service)
):
    """Send notification for SLA breach"""
    try:
        result = await notifications_service.send_sla_breach_notification(
            ticket_id=ticket_id,
            channels=channels
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/escalation/{ticket_id}", response_model=Dict[str, Any])
async def send_escalation_notification(
    ticket_id: int,
    request: EscalationNotificationRequest,
    notifications_service: RealTimeNotificationsService = Depends(get_notifications_service)
):
    """Send notification for ticket escalation"""
    try:
        result = await notifications_service.send_escalation_notification(
            ticket_id=ticket_id,
            escalated_to_agent_id=request.escalated_to_agent_id,
            reason=request.reason,
            channels=request.channels
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/high-volume-alert", response_model=Dict[str, Any])
async def send_high_volume_alert(
    channels: Optional[List[str]] = Query(None),
    notifications_service: RealTimeNotificationsService = Depends(get_notifications_service)
):
    """Send notification for high ticket volume"""
    try:
        result = await notifications_service.send_high_volume_alert(channels=channels)
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/agent-unavailable/{agent_id}", response_model=Dict[str, Any])
async def send_agent_unavailable_notification(
    agent_id: int,
    channels: Optional[List[str]] = Query(None),
    notifications_service: RealTimeNotificationsService = Depends(get_notifications_service)
):
    """Send notification when agent becomes unavailable"""
    try:
        result = await notifications_service.send_agent_unavailable_notification(
            agent_id=agent_id,
            channels=channels
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/satisfaction-alert/{ticket_id}", response_model=Dict[str, Any])
async def send_satisfaction_alert(
    ticket_id: int,
    request: SatisfactionAlertRequest,
    notifications_service: RealTimeNotificationsService = Depends(get_notifications_service)
):
    """Send notification for low customer satisfaction"""
    try:
        result = await notifications_service.send_satisfaction_alert(
            ticket_id=ticket_id,
            satisfaction_score=request.satisfaction_score,
            channels=request.channels
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history", response_model=Dict[str, Any])
async def get_notification_history(
    rule_name: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    notifications_service: RealTimeNotificationsService = Depends(get_notifications_service)
):
    """Get notification history"""
    try:
        result = await notifications_service.get_notification_history(
            rule_name=rule_name,
            limit=limit
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/channels", response_model=Dict[str, Any])
async def get_notification_channels(
    notifications_service: RealTimeNotificationsService = Depends(get_notifications_service)
):
    """Get available notification channels"""
    try:
        return {
            "success": True,
            "channels": notifications_service._notification_channels,
            "available_channels": [
                channel for channel, config in notifications_service._notification_channels.items()
                if config.get("enabled", False)
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/rules", response_model=Dict[str, Any])
async def get_notification_rules(
    notifications_service: RealTimeNotificationsService = Depends(get_notifications_service)
):
    """Get notification rules configuration"""
    try:
        return {
            "success": True,
            "rules": notifications_service._notification_rules,
            "rule_count": len(notifications_service._notification_rules)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health", response_model=Dict[str, Any])
async def check_notifications_health(
    notifications_service: RealTimeNotificationsService = Depends(get_notifications_service)
):
    """Check health status of notifications service"""
    try:
        return {
            "success": True,
            "service": "real_time_notifications",
            "status": "healthy",
            "channels_configured": len(notifications_service._notification_channels),
            "rules_configured": len(notifications_service._notification_rules),
            "notification_history_count": len(notifications_service._notification_history),
            "message": "Real-time notifications service is operational"
        }
    except Exception as e:
        return {
            "success": False,
            "service": "real_time_notifications",
            "status": "error",
            "error": str(e)
        }
