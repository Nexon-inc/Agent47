from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
from datetime import datetime

from ..services.crm_automation_service import CRMAutomationService
from ..database import get_db

router = APIRouter(prefix="/crm-automation", tags=["CRM Automation"])
crm_automation_service = CRMAutomationService()

class LeadSyncRequest(BaseModel):
    lead_id: int
    crm_platform: str
    crm_config: Dict[str, Any]

class DealSyncRequest(BaseModel):
    deal_id: int
    crm_platform: str
    crm_config: Dict[str, Any]

class CRMUpdateRequest(BaseModel):
    brand_id: int
    crm_platform: str
    update_data: Dict[str, Any]

class CRMAnalyticsRequest(BaseModel):
    brand_id: int
    crm_platform: str
    date_range: str = "30d"

@router.post("/sync-lead")
async def sync_lead_to_crm(request: LeadSyncRequest):
    """Sync lead data to external CRM"""
    try:
        result = await crm_automation_service.sync_lead_to_crm(
            lead_id=request.lead_id,
            crm_platform=request.crm_platform,
            crm_config=request.crm_config
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to sync lead to CRM: {str(e)}")

@router.post("/sync-deal")
async def sync_deal_to_crm(request: DealSyncRequest):
    """Sync deal data to external CRM"""
    try:
        result = await crm_automation_service.sync_deal_to_crm(
            deal_id=request.deal_id,
            crm_platform=request.crm_platform,
            crm_config=request.crm_config
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to sync deal to CRM: {str(e)}")

@router.post("/update-records")
async def update_crm_records(request: CRMUpdateRequest):
    """Update multiple CRM records"""
    try:
        result = await crm_automation_service.update_crm_records(
            brand_id=request.brand_id,
            crm_platform=request.crm_platform,
            update_data=request.update_data
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update CRM records: {str(e)}")

@router.post("/analytics")
async def get_crm_analytics(request: CRMAnalyticsRequest):
    """Get CRM analytics and insights"""
    try:
        result = await crm_automation_service.get_crm_analytics(
            brand_id=request.brand_id,
            crm_platform=request.crm_platform,
            date_range=request.date_range
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get CRM analytics: {str(e)}")

@router.get("/supported-platforms")
async def get_supported_platforms():
    """Get list of supported CRM platforms"""
    return {
        "supported_platforms": [
            {
                "name": "Salesforce",
                "features": ["lead_sync", "deal_sync", "analytics"],
                "api_version": "v58.0"
            },
            {
                "name": "HubSpot",
                "features": ["contact_sync", "deal_sync", "analytics"],
                "api_version": "v3"
            },
            {
                "name": "Pipedrive",
                "features": ["person_sync", "deal_sync", "analytics"],
                "api_version": "v1"
            }
        ]
    }

@router.get("/health")
async def health_check():
    """Health check for CRM automation service"""
    return {
        "status": "healthy",
        "service": "crm_automation",
        "timestamp": datetime.now().isoformat()
    }
