from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from ..services.campaign_service import CampaignService
from ..models import CampaignStatus, CampaignType, PlatformType
from ..database import get_jackie_database

router = APIRouter()

class CreateCampaignRequest(BaseModel):
    user_id: int
    name: str
    description: Optional[str] = None
    campaign_type: CampaignType
    platforms: List[PlatformType]
    target_audience: Dict[str, Any]
    budget: float
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    goals: Dict[str, Any]
    kpis: Dict[str, Any]

class UpdateCampaignRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[CampaignStatus] = None
    budget: Optional[float] = None
    target_audience: Optional[Dict[str, Any]] = None
    goals: Optional[Dict[str, Any]] = None
    kpis: Optional[Dict[str, Any]] = None

class CampaignResponse(BaseModel):
    id: int
    campaign_id: str
    user_id: int
    name: str
    description: Optional[str]
    campaign_type: str
    status: str
    platforms: List[str]
    target_audience: Dict[str, Any]
    budget: float
    spent_budget: float
    start_date: Optional[str]
    end_date: Optional[str]
    goals: Dict[str, Any]
    kpis: Dict[str, Any]
    performance_metrics: Dict[str, Any]
    created_at: str
    updated_at: str

async def get_campaign_service() -> CampaignService:
    service = CampaignService()
    await service.initialize()
    return service

@router.post("/", response_model=Dict[str, Any])
async def create_campaign(
    request: CreateCampaignRequest,
    service: CampaignService = Depends(get_campaign_service)
):
    try:
        result = await service.create_campaign(
            user_id=request.user_id,
            name=request.name,
            description=request.description,
            campaign_type=request.campaign_type,
            platforms=request.platforms,
            target_audience=request.target_audience,
            budget=request.budget,
            start_date=request.start_date,
            end_date=request.end_date,
            goals=request.goals,
            kpis=request.kpis
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{campaign_id}", response_model=Dict[str, Any])
async def get_campaign(
    campaign_id: int,
    service: CampaignService = Depends(get_campaign_service)
):
    try:
        result = await service.get_campaign_details(campaign_id)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=404, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{campaign_id}", response_model=Dict[str, Any])
async def update_campaign(
    campaign_id: int,
    request: UpdateCampaignRequest,
    service: CampaignService = Depends(get_campaign_service)
):
    try:
        result = await service.update_campaign(
            campaign_id=campaign_id,
            name=request.name,
            description=request.description,
            status=request.status,
            budget=request.budget,
            target_audience=request.target_audience,
            goals=request.goals,
            kpis=request.kpis
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{campaign_id}", response_model=Dict[str, Any])
async def delete_campaign(
    campaign_id: int,
    service: CampaignService = Depends(get_campaign_service)
):
    try:
        result = await service.delete_campaign(campaign_id)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=Dict[str, Any])
async def list_campaigns(
    user_id: int = Query(...),
    status: Optional[CampaignStatus] = Query(None),
    campaign_type: Optional[CampaignType] = Query(None),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: CampaignService = Depends(get_campaign_service)
):
    try:
        result = await service.list_campaigns(
            user_id=user_id,
            status=status,
            campaign_type=campaign_type,
            limit=limit,
            offset=offset
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{campaign_id}/optimize", response_model=Dict[str, Any])
async def optimize_campaign(
    campaign_id: int,
    service: CampaignService = Depends(get_campaign_service)
):
    try:
        result = await service.optimize_campaign(campaign_id)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{campaign_id}/analytics", response_model=Dict[str, Any])
async def get_campaign_analytics(
    campaign_id: int,
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    service: CampaignService = Depends(get_campaign_service)
):
    try:
        result = await service.get_campaign_analytics(
            campaign_id=campaign_id,
            start_date=start_date,
            end_date=end_date
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{campaign_id}/duplicate", response_model=Dict[str, Any])
async def duplicate_campaign(
    campaign_id: int,
    new_name: str = Body(...),
    service: CampaignService = Depends(get_campaign_service)
):
    try:
        result = await service.duplicate_campaign(campaign_id, new_name)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{campaign_id}/schedule", response_model=Dict[str, Any])
async def schedule_campaign(
    campaign_id: int,
    scheduled_time: str = Body(...),
    service: CampaignService = Depends(get_campaign_service)
):
    try:
        result = await service.schedule_campaign(campaign_id, scheduled_time)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{campaign_id}/pause", response_model=Dict[str, Any])
async def pause_campaign(
    campaign_id: int,
    service: CampaignService = Depends(get_campaign_service)
):
    try:
        result = await service.pause_campaign(campaign_id)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{campaign_id}/resume", response_model=Dict[str, Any])
async def resume_campaign(
    campaign_id: int,
    service: CampaignService = Depends(get_campaign_service)
):
    try:
        result = await service.resume_campaign(campaign_id)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
