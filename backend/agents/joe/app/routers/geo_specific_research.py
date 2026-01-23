from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from ..database import get_joe_database
from core.event_bus.kafka_manager import get_event_bus
from core.cache.redis_manager import get_redis
from ..services.geo_specific_research_service import GeoSpecificResearchService

router = APIRouter()

class RegionalMarketsRequest(BaseModel):
    regions: List[str] = Field(..., description="Regions to analyze")
    industry: str = Field(..., description="Industry context")
    research_focus: str = Field(..., description="Research focus area")

class LocalSearchTrendsRequest(BaseModel):
    region: str = Field(..., description="JoeRegion to analyze")
    keywords: List[str] = Field(..., description="Keywords to analyze")
    timeframe: str = Field(default="30d", description="Analysis timeframe")

class RegionalHashtagsRequest(BaseModel):
    region: str = Field(..., description="JoeRegion to analyze")
    industry: str = Field(..., description="Industry context")
    social_platforms: List[str] = Field(..., description="Social media platforms to analyze")

class RegionalReportRequest(BaseModel):
    region: str = Field(..., description="JoeRegion for report")
    research_data: Dict[str, Any] = Field(..., description="Research data")
    report_type: str = Field(default="comprehensive", description="Report type")

class RegionalComparisonRequest(BaseModel):
    regions: List[str] = Field(..., description="Regions to compare")
    comparison_metrics: List[str] = Field(..., description="Metrics to compare")

@router.post("/analyze-regional-markets")
async def analyze_regional_markets(
    request: RegionalMarketsRequest,
    db: AsyncSession = Depends(get_joe_database),
    event_bus = Depends(get_event_bus),
    redis = Depends(get_redis)
) -> Dict[str, Any]:
    """Analyze regional markets with localized data and insights"""
    try:
        service = GeoSpecificResearchService(db, event_bus, redis)
        result = await service.analyze_regional_markets(
            regions=request.regions,
            industry=request.industry,
            research_focus=request.research_focus
        )
        return {
            "status": "success",
            "data": result,
            "message": f"Analyzed {len(request.regions)} regional markets for {request.industry}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Regional market analysis failed: {str(e)}")

@router.post("/analyze-local-search-trends")
async def analyze_local_search_trends(
    request: LocalSearchTrendsRequest,
    db: AsyncSession = Depends(get_joe_database),
    event_bus = Depends(get_event_bus),
    redis = Depends(get_redis)
) -> Dict[str, Any]:
    """Analyze local search trends and patterns"""
    try:
        service = GeoSpecificResearchService(db, event_bus, redis)
        result = await service.analyze_local_search_trends(
            region=request.region,
            keywords=request.keywords,
            timeframe=request.timeframe
        )
        return {
            "status": "success",
            "data": result,
            "message": f"Analyzed local search trends for {request.region} with {len(request.keywords)} keywords"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Local search trends analysis failed: {str(e)}")

@router.post("/analyze-regional-hashtags")
async def analyze_regional_hashtags(
    request: RegionalHashtagsRequest,
    db: AsyncSession = Depends(get_joe_database),
    event_bus = Depends(get_event_bus),
    redis = Depends(get_redis)
) -> Dict[str, Any]:
    """Analyze regional hashtags and social media trends"""
    try:
        service = GeoSpecificResearchService(db, event_bus, redis)
        result = await service.analyze_regional_hashtags(
            region=request.region,
            industry=request.industry,
            social_platforms=request.social_platforms
        )
        return {
            "status": "success",
            "data": result,
            "message": f"Analyzed regional hashtags for {request.region} in {request.industry}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Regional hashtags analysis failed: {str(e)}")

@router.post("/generate-regional-report")
async def generate_regional_report(
    request: RegionalReportRequest,
    db: AsyncSession = Depends(get_joe_database),
    event_bus = Depends(get_event_bus),
    redis = Depends(get_redis)
) -> Dict[str, Any]:
    """Generate comprehensive regional market report"""
    try:
        service = GeoSpecificResearchService(db, event_bus, redis)
        result = await service.generate_regional_report(
            region=request.region,
            research_data=request.research_data,
            report_type=request.report_type
        )
        return {
            "status": "success",
            "data": result,
            "message": f"Generated {request.report_type} regional report for {request.region}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Regional report generation failed: {str(e)}")

@router.post("/compare-regional-markets")
async def compare_regional_markets(
    request: RegionalComparisonRequest,
    db: AsyncSession = Depends(get_joe_database),
    event_bus = Depends(get_event_bus),
    redis = Depends(get_redis)
) -> Dict[str, Any]:
    """Compare multiple regional markets across various metrics"""
    try:
        service = GeoSpecificResearchService(db, event_bus, redis)
        result = await service.compare_regional_markets(
            regions=request.regions,
            comparison_metrics=request.comparison_metrics
        )
        return {
            "status": "success",
            "data": result,
            "message": f"Compared {len(request.regions)} regional markets across {len(request.comparison_metrics)} metrics"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Regional market comparison failed: {str(e)}")
