from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import Dict, Any, Optional
from pydantic import BaseModel
from ..services.offline_support_service import OfflineSupportService
from ..models import TicketCategory, SupportChannel

router = APIRouter()

# Pydantic models for request/response
class OfflineResponseRequest(BaseModel):
    customer_id: int
    message: str
    channel: str
    priority: str = "normal"
    metadata: Optional[Dict[str, Any]] = None

class OfflineTicketRequest(BaseModel):
    customer_id: int
    subject: str
    description: str
    category: str
    priority: str = "normal"
    metadata: Optional[Dict[str, Any]] = None

class ConnectivityRequest(BaseModel):
    customer_id: int
    connectivity_level: str = "low"  # very_low, low, normal
    metadata: Optional[Dict[str, Any]] = None

class DeliveryRequest(BaseModel):
    customer_id: int
    delivery_channel: str

# Dependency
async def get_offline_support_service() -> OfflineSupportService:
    service = OfflineSupportService()
    await service.initialize()
    return service

@router.post("/responses/queue", response_model=Dict[str, Any])
async def queue_offline_response(
    request: OfflineResponseRequest,
    service: OfflineSupportService = Depends(get_offline_support_service)
):
    """Queue a response for when customer comes back online"""
    try:
        result = await service.queue_offline_response(
            customer_id=request.customer_id,
            message=request.message,
            channel=SupportChannel(request.channel),
            priority=request.priority,
            metadata=request.metadata
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/responses/queued", response_model=Dict[str, Any])
async def get_queued_responses(
    customer_id: int = Query(..., description="Customer ID"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of responses to return"),
    service: OfflineSupportService = Depends(get_offline_support_service)
):
    """Get queued responses for a customer"""
    try:
        result = await service.get_queued_responses(
            customer_id=customer_id,
            limit=limit
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/responses/deliver", response_model=Dict[str, Any])
async def deliver_queued_responses(
    request: DeliveryRequest,
    service: OfflineSupportService = Depends(get_offline_support_service)
):
    """Deliver all queued responses to a customer"""
    try:
        result = await service.deliver_queued_responses(
            customer_id=request.customer_id,
            delivery_channel=SupportChannel(request.delivery_channel)
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tickets/create", response_model=Dict[str, Any])
async def create_offline_ticket(
    request: OfflineTicketRequest,
    service: OfflineSupportService = Depends(get_offline_support_service)
):
    """Create a support ticket for offline customer"""
    try:
        result = await service.create_offline_ticket(
            customer_id=request.customer_id,
            subject=request.subject,
            description=request.description,
            category=TicketCategory(request.category),
            priority=request.priority,
            metadata=request.metadata
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/summary/customer", response_model=Dict[str, Any])
async def get_offline_support_summary(
    customer_id: int = Query(..., description="Customer ID"),
    service: OfflineSupportService = Depends(get_offline_support_service)
):
    """Get summary of offline support activities"""
    try:
        result = await service.get_offline_support_summary(
            customer_id=customer_id
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/connectivity/handle", response_model=Dict[str, Any])
async def handle_low_connectivity(
    request: ConnectivityRequest,
    service: OfflineSupportService = Depends(get_offline_support_service)
):
    """Handle low connectivity scenarios"""
    try:
        result = await service.handle_low_connectivity(
            customer_id=request.customer_id,
            connectivity_level=request.connectivity_level,
            metadata=request.metadata
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/system", response_model=Dict[str, Any])
async def get_offline_support_system_status(
    service: OfflineSupportService = Depends(get_offline_support_service)
):
    """Get offline support system status"""
    try:
        status = {
            "success": True,
            "offline_support_status": {
                "system_status": "active",
                "queued_responses_count": 0,
                "offline_tickets_count": 0,
                "delivery_queue_size": 0,
                "last_delivery_attempt": "2024-01-01T00:00:00Z",
                "connectivity_monitoring": True,
                "auto_queuing_enabled": True,
                "delivery_retry_limit": 3,
                "supported_channels": [
                    "email",
                    "sms",
                    "push_notification",
                    "chat"
                ]
            },
            "last_updated": "2024-01-01T00:00:00Z"
        }
        
        return status
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/config/settings", response_model=Dict[str, Any])
async def get_offline_support_configuration(
    service: OfflineSupportService = Depends(get_offline_support_service)
):
    """Get offline support configuration settings"""
    try:
        config = {
            "success": True,
            "offline_support_config": {
                "enabled": True,
                "auto_queuing": True,
                "delivery_retry_limit": 3,
                "retry_interval_hours": 6,
                "priority_levels": {
                    "critical": {"retry_interval": 1, "max_retries": 5},
                    "high": {"retry_interval": 2, "max_retries": 4},
                    "normal": {"retry_interval": 6, "max_retries": 3},
                    "low": {"retry_interval": 12, "max_retries": 2}
                },
                "connectivity_thresholds": {
                    "very_low": "Connection < 10%",
                    "low": "Connection 10-50%",
                    "normal": "Connection > 50%"
                },
                "notification_preferences": {
                    "email": True,
                    "sms": False,
                    "push": True,
                    "chat": True
                }
            }
        }
        
        return config
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/overview", response_model=Dict[str, Any])
async def get_offline_support_statistics(
    service: OfflineSupportService = Depends(get_offline_support_service)
):
    """Get offline support usage statistics"""
    try:
        # Get offline support statistics from the service
        stats = await service.get_offline_support_statistics()
        
        return {
            "success": True,
            "offline_support_stats": stats
        }
        
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
