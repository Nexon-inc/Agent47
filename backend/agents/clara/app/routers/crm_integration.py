from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel
from ..services.crm_integration_service import CRMIntegrationService
from ..models import SupportChannel, TicketPriority, TicketStatus, TicketCategory

router = APIRouter()

# Pydantic models for request/response
class CRMSyncRequest(BaseModel):
    crm_platform: str
    crm_data: Optional[Dict[str, Any]] = None

class CRMUpdateRequest(BaseModel):
    update_data: Dict[str, Any]

class CRMAnalyticsRequest(BaseModel):
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None

async def get_crm_service() -> CRMIntegrationService:
    """Dependency to get CRM integration service"""
    service = CRMIntegrationService()
    await service.initialize()
    return service

@router.post("/sync/ticket/{ticket_id}", response_model=Dict[str, Any])
async def sync_ticket_to_crm(
    ticket_id: int,
    request: CRMSyncRequest,
    crm_service: CRMIntegrationService = Depends(get_crm_service)
):
    """Sync a support ticket to external CRM"""
    try:
        result = await crm_service.sync_ticket_to_crm(
            ticket_id=ticket_id,
            crm_platform=request.crm_platform,
            crm_data=request.crm_data
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sync/customer/{customer_id}", response_model=Dict[str, Any])
async def sync_customer_to_crm(
    customer_id: int,
    request: CRMSyncRequest,
    crm_service: CRMIntegrationService = Depends(get_crm_service)
):
    """Sync customer profile to external CRM"""
    try:
        result = await crm_service.sync_customer_to_crm(
            customer_id=customer_id,
            crm_platform=request.crm_platform,
            crm_data=request.crm_data
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ticket/{ticket_id}/status/{crm_platform}", response_model=Dict[str, Any])
async def get_crm_ticket_status(
    ticket_id: int,
    crm_platform: str,
    crm_service: CRMIntegrationService = Depends(get_crm_service)
):
    """Get ticket status from external CRM"""
    try:
        result = await crm_service.get_crm_ticket_status(
            ticket_id=ticket_id,
            crm_platform=crm_platform
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/ticket/{ticket_id}/update/{crm_platform}", response_model=Dict[str, Any])
async def update_crm_ticket(
    ticket_id: int,
    crm_platform: str,
    request: CRMUpdateRequest,
    crm_service: CRMIntegrationService = Depends(get_crm_service)
):
    """Update ticket in external CRM"""
    try:
        result = await crm_service.update_crm_ticket(
            ticket_id=ticket_id,
            crm_platform=crm_platform,
            update_data=request.update_data
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/{crm_platform}", response_model=Dict[str, Any])
async def get_crm_analytics(
    crm_platform: str,
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    crm_service: CRMIntegrationService = Depends(get_crm_service)
):
    """Get analytics data from external CRM"""
    try:
        result = await crm_service.get_crm_analytics(
            crm_platform=crm_platform,
            date_from=date_from,
            date_to=date_to
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/platforms", response_model=Dict[str, Any])
async def get_available_crm_platforms(
    crm_service: CRMIntegrationService = Depends(get_crm_service)
):
    """Get list of available CRM platforms"""
    try:
        platforms = list(crm_service._crm_clients.keys())
        return {
            "success": True,
            "platforms": platforms,
            "count": len(platforms),
            "message": f"Found {len(platforms)} CRM platforms configured"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health/{crm_platform}", response_model=Dict[str, Any])
async def check_crm_health(
    crm_platform: str,
    crm_service: CRMIntegrationService = Depends(get_crm_service)
):
    """Check health status of CRM integration"""
    try:
        # Check if platform is configured
        if crm_platform not in crm_service._crm_clients:
            return {
                "success": False,
                "platform": crm_platform,
                "status": "not_configured",
                "message": f"CRM platform {crm_platform} is not configured"
            }
        
        # Perform actual health check for the platform
        try:
            client = crm_service._crm_clients[crm_platform]
            health_status = await client.check_connection()
            
            if health_status["success"]:
                return {
                    "success": True,
                    "platform": crm_platform,
                    "status": "healthy",
                    "message": f"CRM platform {crm_platform} is healthy",
                    "response_time": health_status.get("response_time"),
                    "last_sync": health_status.get("last_sync")
                }
            else:
                return {
                    "success": False,
                    "platform": crm_platform,
                    "status": "unhealthy",
                    "message": f"CRM platform {crm_platform} is unhealthy",
                    "error": health_status.get("error")
                }
        except Exception as health_error:
            return {
                "success": False,
                "platform": crm_platform,
                "status": "error",
                "message": f"Error checking health for {crm_platform}",
                "error": str(health_error)
            }
    except Exception as e:
        return {
            "success": False,
            "platform": crm_platform,
            "status": "error",
            "error": str(e)
        }
