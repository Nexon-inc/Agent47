from fastapi import APIRouter, HTTPException
from typing import Dict, List, Any

from ..services.campaign_version_control_service import CampaignVersionControlService

router = APIRouter(prefix="/campaign-version-control", tags=["Campaign Version Control"])

@router.post("/create-version")
async def create_campaign_version(campaign_id: str, version_data: Dict[str, Any], version_notes: str = ""):
    try:
        service = CampaignVersionControlService()
        await service.initialize()
        return await service.create_campaign_version(campaign_id, version_data, version_notes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/track-changes")
async def track_version_changes(version_id: str, changes: List[Dict[str, Any]]):
    try:
        service = CampaignVersionControlService()
        await service.initialize()
        return await service.track_version_changes(version_id, changes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/rollback-version")
async def rollback_campaign_version(campaign_id: str, target_version_id: str):
    try:
        service = CampaignVersionControlService()
        await service.initialize()
        return await service.rollback_campaign_version(campaign_id, target_version_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/version-history")
async def get_version_history(campaign_id: str):
    try:
        service = CampaignVersionControlService()
        await service.initialize()
        return await service.get_version_history(campaign_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics")
async def get_version_control_analytics(timeframe: str = "30d"):
    try:
        service = CampaignVersionControlService()
        await service.initialize()
        return await service.get_version_control_analytics(timeframe)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
