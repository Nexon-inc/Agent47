from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from ..services.seo_service import SEOService
from ..database import get_jackie_database

router = APIRouter()

class SEOAnalysisRequest(BaseModel):
    user_id: int
    website_url: str
    target_keywords: List[str]
    competitor_urls: Optional[List[str]] = None

class SEOOptimizationRequest(BaseModel):
    user_id: int
    content: str
    target_keywords: List[str]
    content_type: str

async def get_seo_service() -> SEOService:
    service = SEOService()
    await service.initialize()
    return service

@router.post("/analyze", response_model=Dict[str, Any])
async def analyze_seo(
    request: SEOAnalysisRequest,
    service: SEOService = Depends(get_seo_service)
):
    try:
        result = await service.analyze_seo(
            user_id=request.user_id,
            website_url=request.website_url,
            target_keywords=request.target_keywords,
            competitor_urls=request.competitor_urls
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/optimize", response_model=Dict[str, Any])
async def optimize_seo(
    request: SEOOptimizationRequest,
    service: SEOService = Depends(get_seo_service)
):
    try:
        result = await service.optimize_seo(
            user_id=request.user_id,
            content=request.content,
            target_keywords=request.target_keywords,
            content_type=request.content_type
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/keywords/{project_id}", response_model=Dict[str, Any])
async def get_keyword_rankings(
    project_id: int,
    service: SEOService = Depends(get_seo_service)
):
    try:
        result = await service.get_keyword_rankings(project_id)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=404, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/backlinks/analyze", response_model=Dict[str, Any])
async def analyze_backlinks(
    website_url: str = Body(...),
    service: SEOService = Depends(get_seo_service)
):
    try:
        result = await service.analyze_backlinks(website_url)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
