from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from ..database import get_joe_database
from backend.core.event_bus.kafka_manager import get_event_bus
from backend.core.cache.redis_manager import get_redis
from ..services.market_intelligence_service import MarketIntelligenceService

router = APIRouter()

class MarketDynamicsRequest(BaseModel):
    market_data: Dict[str, Any] = Field(..., description="Market data to analyze")
    analysis_period: str = Field(default="12m", description="Analysis period")

class CompetitiveIntelligenceRequest(BaseModel):
    competitors: List[str] = Field(..., description="Competitors to track")
    intelligence_focus: List[str] = Field(..., description="Areas of intelligence focus")

class IndustryTrendsRequest(BaseModel):
    industry: str = Field(..., description="Industry to monitor")
    trend_categories: List[str] = Field(..., description="Trend categories to monitor")
    monitoring_period: str = Field(default="6m", description="Monitoring period")

class MarketInsightsRequest(BaseModel):
    market_data: Dict[str, Any] = Field(..., description="Market data for insights")
    insight_type: str = Field(default="comprehensive", description="Type of insights to generate")

@router.post("/analyze-market-dynamics")
async def analyze_market_dynamics(
    request: MarketDynamicsRequest,
    db: AsyncSession = Depends(get_joe_database),
    event_bus = Depends(get_event_bus),
    redis = Depends(get_redis)
) -> Dict[str, Any]:
    """Analyze market dynamics and identify key trends and patterns"""
    try:
        service = MarketIntelligenceService(db, event_bus, redis)
        result = await service.analyze_market_dynamics(
            market_data=request.market_data,
            analysis_period=request.analysis_period
        )
        return {
            "status": "success",
            "data": result,
            "message": f"Analyzed market dynamics for {request.analysis_period} period"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Market dynamics analysis failed: {str(e)}")

@router.post("/track-competitive-intelligence")
async def track_competitive_intelligence(
    request: CompetitiveIntelligenceRequest,
    db: AsyncSession = Depends(get_joe_database),
    event_bus = Depends(get_event_bus),
    redis = Depends(get_redis)
) -> Dict[str, Any]:
    """Track competitive intelligence and monitor competitor activities"""
    try:
        service = MarketIntelligenceService(db, event_bus, redis)
        result = await service.track_competitive_intelligence(
            competitors=request.competitors,
            intelligence_focus=request.intelligence_focus
        )
        return {
            "status": "success",
            "data": result,
            "message": f"Tracked competitive intelligence for {len(request.competitors)} competitors"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Competitive intelligence tracking failed: {str(e)}")

@router.post("/monitor-industry-trends")
async def monitor_industry_trends(
    request: IndustryTrendsRequest,
    db: AsyncSession = Depends(get_joe_database),
    event_bus = Depends(get_event_bus),
    redis = Depends(get_redis)
) -> Dict[str, Any]:
    """Monitor industry trends and identify emerging patterns"""
    try:
        service = MarketIntelligenceService(db, event_bus, redis)
        result = await service.monitor_industry_trends(
            industry=request.industry,
            trend_categories=request.trend_categories,
            monitoring_period=request.monitoring_period
        )
        return {
            "status": "success",
            "data": result,
            "message": f"Monitored industry trends for {request.industry} across {len(request.trend_categories)} categories"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Industry trends monitoring failed: {str(e)}")

@router.post("/generate-market-insights")
async def generate_market_insights(
    request: MarketInsightsRequest,
    db: AsyncSession = Depends(get_joe_database),
    event_bus = Depends(get_event_bus),
    redis = Depends(get_redis)
) -> Dict[str, Any]:
    """Generate actionable market insights from comprehensive data analysis"""
    try:
        service = MarketIntelligenceService(db, event_bus, redis)
        result = await service.generate_market_insights(
            market_data=request.market_data,
            insight_type=request.insight_type
        )
        return {
            "status": "success",
            "data": result,
            "message": f"Generated {request.insight_type} market insights"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Market insights generation failed: {str(e)}")
