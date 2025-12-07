from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from ..services.ads_service import AdsService
from ..models import PlatformType
from ..database import get_jackie_database

router = APIRouter()

class CreateAdRequest(BaseModel):
    user_id: int
    platform: PlatformType
    ad_type: str
    ad_copy: str
    targeting: Dict[str, Any]
    budget: float
    bid_amount: float

class OptimizeAdRequest(BaseModel):
    ad_id: int
    optimization_type: str
    target_metrics: Dict[str, Any]

async def get_ads_service() -> AdsService:
    service = AdsService()
    await service.initialize()
    return service

@router.post("/create", response_model=Dict[str, Any])
async def create_ad(
    request: CreateAdRequest,
    service: AdsService = Depends(get_ads_service)
):
    try:
        result = await service.create_ad(
            user_id=request.user_id,
            platform=request.platform,
            ad_type=request.ad_type,
            ad_copy=request.ad_copy,
            targeting=request.targeting,
            budget=request.budget,
            bid_amount=request.bid_amount
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{ad_id}/optimize", response_model=Dict[str, Any])
async def optimize_ad(
    ad_id: int,
    request: OptimizeAdRequest,
    service: AdsService = Depends(get_ads_service)
):
    try:
        result = await service.optimize_ad(
            ad_id=ad_id,
            optimization_type=request.optimization_type,
            target_metrics=request.target_metrics
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{ad_id}/performance", response_model=Dict[str, Any])
async def get_ad_performance(
    ad_id: int,
    service: AdsService = Depends(get_ads_service)
):
    try:
        result = await service.get_ad_performance(ad_id)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=404, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/budget-allocate", response_model=Dict[str, Any])
async def allocate_budget(
    campaign_id: int = Body(...),
    platform: PlatformType = Body(...),
    allocated_budget: float = Body(...),
    service: AdsService = Depends(get_ads_service)
):
    try:
        result = await service.allocate_budget(
            campaign_id=campaign_id,
            platform=platform,
            allocated_budget=allocated_budget
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
