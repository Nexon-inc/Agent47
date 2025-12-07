from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from ..services.social_media_service import SocialMediaService
from ..models import PlatformType
from ..database import get_jackie_database

router = APIRouter()

class CreateSocialPostRequest(BaseModel):
    user_id: int
    platform: PlatformType
    content: str
    media_urls: Optional[List[str]] = None
    scheduled_time: Optional[str] = None
    targeting: Optional[Dict[str, Any]] = None

class SocialMediaCampaignRequest(BaseModel):
    user_id: int
    campaign_name: str
    platforms: List[PlatformType]
    content_template: str
    posting_schedule: Dict[str, Any]
    budget: float

async def get_social_media_service() -> SocialMediaService:
    service = SocialMediaService()
    await service.initialize()
    return service

@router.post("/posts/create", response_model=Dict[str, Any])
async def create_social_post(
    request: CreateSocialPostRequest,
    service: SocialMediaService = Depends(get_social_media_service)
):
    try:
        result = await service.create_social_post(
            user_id=request.user_id,
            platform=request.platform,
            content=request.content,
            media_urls=request.media_urls,
            scheduled_time=request.scheduled_time,
            targeting=request.targeting
        )

        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/campaigns/create", response_model=Dict[str, Any])
async def create_social_campaign(
    request: SocialMediaCampaignRequest,
    service: SocialMediaService = Depends(get_social_media_service)
):
    try:
        result = await service.create_social_campaign(
            user_id=request.user_id,
            campaign_name=request.campaign_name,
            platforms=request.platforms,
            content_template=request.content_template,
            posting_schedule=request.posting_schedule,
            budget=request.budget
        )

        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/{campaign_id}", response_model=Dict[str, Any])
async def get_social_analytics(
    campaign_id: int,
    service: SocialMediaService = Depends(get_social_media_service)
):
    try:
        result = await service.get_social_analytics(campaign_id)

        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=404, detail=result["error"])

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/posts/{post_id}/optimize", response_model=Dict[str, Any])
async def optimize_social_post(
    post_id: int,
    optimization_type: str = Body(...),
    service: SocialMediaService = Depends(get_social_media_service)
):
    try:
        result = await service.optimize_social_post(
            post_id=post_id,
            optimization_type=optimization_type
        )

        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trends", response_model=Dict[str, Any])
async def get_social_trends(
    platform: PlatformType = Query(...),
    service: SocialMediaService = Depends(get_social_media_service)
):
    try:
        result = await service.get_social_trends(platform)

        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
