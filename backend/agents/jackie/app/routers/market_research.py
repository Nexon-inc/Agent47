from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import json

from ..database import get_db
from ..services.market_research_service import MarketResearchService
from ..models import JackieMarketResearch
from pydantic import BaseModel
from typing import Dict

router = APIRouter(prefix="/market-research", tags=["Market Research"])

class CompetitorAnalysisRequest(BaseModel):
    competitor_urls: List[str]
    analysis_type: str = "comprehensive"

class TrendAnalysisRequest(BaseModel):
    industry: str
    timeframe: str = "30d"
    keywords: Optional[List[str]] = None

class AudienceResearchRequest(BaseModel):
    target_demographics: Dict
    interests: List[str]
    platforms: List[str]

class MarketInsightsRequest(BaseModel):
    market_segment: str
    analysis_depth: str = "detailed"

class MarketResearchResponse(BaseModel):
    id: int
    research_type: str
    data: Dict
    insights: List[str]
    created_at: datetime

@router.post("/competitor-analysis", response_model=MarketResearchResponse)
async def analyze_competitors(
    request: CompetitorAnalysisRequest,
    db: Session = Depends(get_db)
):
    service = MarketResearchService(db)
    try:
        result = service.analyze_competitors(request.competitor_urls, request.analysis_type)
        return MarketResearchResponse(
            id=result["id"],
            research_type="competitor_analysis",
            data=result["data"],
            insights=result["insights"],
            created_at=result["created_at"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/trend-analysis", response_model=MarketResearchResponse)
async def analyze_trends(
    request: TrendAnalysisRequest,
    db: Session = Depends(get_db)
):
    service = MarketResearchService(db)
    try:
        result = service.analyze_trends(request.industry, request.timeframe, request.keywords)
        return MarketResearchResponse(
            id=result["id"],
            research_type="trend_analysis",
            data=result["data"],
            insights=result["insights"],
            created_at=result["created_at"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/audience-research", response_model=MarketResearchResponse)
async def research_audience(
    request: AudienceResearchRequest,
    db: Session = Depends(get_db)
):
    service = MarketResearchService(db)
    try:
        result = service.research_audience(request.target_demographics, request.interests, request.platforms)
        return MarketResearchResponse(
            id=result["id"],
            research_type="audience_research",
            data=result["data"],
            insights=result["insights"],
            created_at=result["created_at"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/market-insights", response_model=MarketResearchResponse)
async def get_market_insights(
    request: MarketInsightsRequest,
    db: Session = Depends(get_db)
):
    service = MarketResearchService(db)
    try:
        result = service.get_market_insights(request.market_segment, request.analysis_depth)
        return MarketResearchResponse(
            id=result["id"],
            research_type="market_insights",
            data=result["data"],
            insights=result["insights"],
            created_at=result["created_at"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/research/{research_id}", response_model=MarketResearchResponse)
async def get_research_by_id(research_id: int, db: Session = Depends(get_db)):
    service = MarketResearchService(db)
    try:
        result = service.get_research_by_id(research_id)
        if not result:
            raise HTTPException(status_code=404, detail="Research not found")
        return MarketResearchResponse(
            id=result["id"],
            research_type=result["research_type"],
            data=result["data"],
            insights=result["insights"],
            created_at=result["created_at"]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/research", response_model=List[MarketResearchResponse])
async def list_research(
    research_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    service = MarketResearchService(db)
    try:
        results = service.list_research(research_type, limit, offset)
        return [
            MarketResearchResponse(
                id=result["id"],
                research_type=result["research_type"],
                data=result["data"],
                insights=result["insights"],
                created_at=result["created_at"]
            )
            for result in results
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/research/{research_id}")
async def delete_research(research_id: int, db: Session = Depends(get_db)):
    service = MarketResearchService(db)
    try:
        success = service.delete_research(research_id)
        if not success:
            raise HTTPException(status_code=404, detail="Research not found")
        return {"message": "Research deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
