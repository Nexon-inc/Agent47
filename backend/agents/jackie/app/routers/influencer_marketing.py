from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from ..services.influencer_marketing_service import InfluencerMarketingService
from ..database import get_jackie_database

router = APIRouter()

class CreateInfluencerCampaignRequest(BaseModel):
    user_id: int
    campaign_name: str
    influencer_id: int
    campaign_brief: str
    budget: float
    deliverables: List[str]
    timeline: Dict[str, Any]

class InfluencerSearchRequest(BaseModel):
    user_id: int
    industry: str
    target_audience: List[str]
    budget_range: Dict[str, float]
    platform_preferences: List[str]

async def get_influencer_marketing_service() -> InfluencerMarketingService:
    service = InfluencerMarketingService()
    await service.initialize()
    return service

@router.post("/campaigns/create", response_model=Dict[str, Any])
async def create_influencer_campaign(
    request: CreateInfluencerCampaignRequest,
    service: InfluencerMarketingService = Depends(get_influencer_marketing_service)
):
    try:
        result = await service.create_influencer_campaign(
            user_id=request.user_id,
            campaign_name=request.campaign_name,
            influencer_id=request.influencer_id,
            campaign_brief=request.campaign_brief,
            budget=request.budget,
            deliverables=request.deliverables,
            timeline=request.timeline
        )

        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/influencers/search", response_model=Dict[str, Any])
async def search_influencers(
    request: InfluencerSearchRequest,
    service: InfluencerMarketingService = Depends(get_influencer_marketing_service)
):
    try:
        result = await service.search_influencers(
            user_id=request.user_id,
            industry=request.industry,
            target_audience=request.target_audience,
            budget_range=request.budget_range,
            platform_preferences=request.platform_preferences
        )

        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/campaigns/{campaign_id}/performance", response_model=Dict[str, Any])
async def get_influencer_performance(
    campaign_id: int,
    service: InfluencerMarketingService = Depends(get_influencer_marketing_service)
):
    try:
        result = await service.get_influencer_performance(campaign_id)

        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=404, detail=result["error"])

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/roi-predictor", response_model=Dict[str, Any])
async def predict_influencer_roi(
    influencer_id: int = Body(...),
    campaign_budget: float = Body(...),
    expected_reach: int = Body(...),
    service: InfluencerMarketingService = Depends(get_influencer_marketing_service)
):
    try:
        result = await service.predict_influencer_roi(
            influencer_id=influencer_id,
            campaign_budget=campaign_budget,
            expected_reach=expected_reach
        )

        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
