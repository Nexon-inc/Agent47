from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import json

from ..database import get_db
from ..services.crm_integration_service import CRMIntegrationService
from ..models import JackieCRMINtegration
from pydantic import BaseModel
from typing import Dict, Any, Optional

router = APIRouter(prefix="/crm-integration", tags=["CRM Integration"])

class ConnectCRMRequest(BaseModel):
    crm_platform: str
    api_key: str
    api_secret: Optional[str] = None
    base_url: Optional[str] = None

class SyncDataRequest(BaseModel):
    data_type: str
    sync_direction: str = "bidirectional"
    filters: Optional[Dict[str, Any]] = None

class CRMSyncResponse(BaseModel):
    id: int
    crm_platform: str
    sync_status: str
    records_synced: int
    last_sync: datetime
    created_at: datetime

@router.post("/connect")
async def connect_crm(
    request: ConnectCRMRequest,
    db: Session = Depends(get_db)
):
    service = CRMIntegrationService(db)
    try:
        result = service.connect_crm(request.crm_platform, request.api_key, request.api_secret, request.base_url)
        return {
            "message": f"Successfully connected to {request.crm_platform}",
            "connection_id": result["connection_id"],
            "status": result["status"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/connections")
async def list_connections(db: Session = Depends(get_db)):
    service = CRMIntegrationService(db)
    try:
        connections = service.list_connections()
        return {"connections": connections}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/connections/{connection_id}")
async def get_connection(connection_id: int, db: Session = Depends(get_db)):
    service = CRMIntegrationService(db)
    try:
        connection = service.get_connection(connection_id)
        if not connection:
            raise HTTPException(status_code=404, detail="Connection not found")
        return connection
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/connections/{connection_id}")
async def disconnect_crm(connection_id: int, db: Session = Depends(get_db)):
    service = CRMIntegrationService(db)
    try:
        success = service.disconnect_crm(connection_id)
        if not success:
            raise HTTPException(status_code=404, detail="Connection not found")
        return {"message": "CRM disconnected successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sync")
async def sync_data(
    request: SyncDataRequest,
    db: Session = Depends(get_db)
):
    service = CRMIntegrationService(db)
    try:
        result = service.sync_data(request.data_type, request.sync_direction, request.filters)
        return {
            "message": "Data sync initiated",
            "sync_id": result["sync_id"],
            "status": result["status"],
            "estimated_duration": result["estimated_duration"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sync/{sync_id}")
async def get_sync_status(sync_id: int, db: Session = Depends(get_db)):
    service = CRMIntegrationService(db)
    try:
        status = service.get_sync_status(sync_id)
        if not status:
            raise HTTPException(status_code=404, detail="Sync not found")
        return status
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/contacts")
async def get_contacts(
    crm_platform: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    service = CRMIntegrationService(db)
    try:
        contacts = service.get_contacts(crm_platform, limit, offset)
        return {"contacts": contacts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/leads")
async def get_leads(
    crm_platform: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    service = CRMIntegrationService(db)
    try:
        leads = service.get_leads(crm_platform, limit, offset)
        return {"leads": leads}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/deals")
async def get_deals(
    crm_platform: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    service = CRMIntegrationService(db)
    try:
        deals = service.get_deals(crm_platform, limit, offset)
        return {"deals": deals}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/contacts")
async def create_contact(
    contact_data: Dict[str, Any],
    crm_platform: Optional[str] = None,
    db: Session = Depends(get_db)
):
    service = CRMIntegrationService(db)
    try:
        result = service.create_contact(contact_data, crm_platform)
        return {
            "message": "Contact created successfully",
            "contact_id": result["contact_id"],
            "crm_platform": result["crm_platform"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/contacts/{contact_id}")
async def update_contact(
    contact_id: str,
    contact_data: Dict[str, Any],
    crm_platform: Optional[str] = None,
    db: Session = Depends(get_db)
):
    service = CRMIntegrationService(db)
    try:
        result = service.update_contact(contact_id, contact_data, crm_platform)
        if not result:
            raise HTTPException(status_code=404, detail="Contact not found")
        return {"message": "Contact updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/leads")
async def create_lead(
    lead_data: Dict[str, Any],
    crm_platform: Optional[str] = None,
    db: Session = Depends(get_db)
):
    service = CRMIntegrationService(db)
    try:
        result = service.create_lead(lead_data, crm_platform)
        return {
            "message": "Lead created successfully",
            "lead_id": result["lead_id"],
            "crm_platform": result["crm_platform"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/deals")
async def create_deal(
    deal_data: Dict[str, Any],
    crm_platform: Optional[str] = None,
    db: Session = Depends(get_db)
):
    service = CRMIntegrationService(db)
    try:
        result = service.create_deal(deal_data, crm_platform)
        return {
            "message": "Deal created successfully",
            "deal_id": result["deal_id"],
            "crm_platform": result["crm_platform"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics")
async def get_crm_analytics(
    crm_platform: Optional[str] = None,
    timeframe: str = "30d",
    db: Session = Depends(get_db)
):
    service = CRMIntegrationService(db)
    try:
        analytics = service.get_crm_analytics(crm_platform, timeframe)
        return analytics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/webhooks")
async def setup_webhook(
    webhook_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    service = CRMIntegrationService(db)
    try:
        result = service.setup_webhook(webhook_data)
        return {
            "message": "Webhook setup successfully",
            "webhook_id": result["webhook_id"],
            "url": result["webhook_url"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/webhooks")
async def list_webhooks(db: Session = Depends(get_db)):
    service = CRMIntegrationService(db)
    try:
        webhooks = service.list_webhooks()
        return {"webhooks": webhooks}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/webhooks/{webhook_id}")
async def delete_webhook(webhook_id: int, db: Session = Depends(get_db)):
    service = CRMIntegrationService(db)
    try:
        success = service.delete_webhook(webhook_id)
        if not success:
            raise HTTPException(status_code=404, detail="Webhook not found")
        return {"message": "Webhook deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/supported-platforms")
async def get_supported_platforms(db: Session = Depends(get_db)):
    service = CRMIntegrationService(db)
    try:
        platforms = service.get_supported_platforms()
        return {"supported_platforms": platforms}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
