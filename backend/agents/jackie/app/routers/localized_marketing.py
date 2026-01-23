from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import json

from ..database import get_db
from ..services.localized_marketing_service import LocalizedMarketingService

router = APIRouter(prefix="/localized-marketing", tags=["Localized Marketing Optimization"])
from pydantic import BaseModel


class LocalizationRequest(BaseModel):
    target_region: str
    content_type: str
    original_content: str
    cultural_context: Optional[Dict[str, Any]] = None


class KeywordLocalizationRequest(BaseModel):
    base_keywords: List[str]
    target_regions: List[str]
    industry: str
    language_preferences: Optional[Dict[str, str]] = None


class TrendAnalysisRequest(BaseModel):
    region: str
    trend_type: str
    timeframe: str
    filters: Optional[Dict[str, Any]] = None

@router.post("/content/localize")
async def localize_content(
    request: LocalizationRequest,
    db: Session = Depends(get_db)
):
    service = LocalizedMarketingService(db)
    try:
        result = service.localize_content(
            request.target_region,
            request.content_type,
            request.original_content,
            request.cultural_context
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/keywords/localize")
async def localize_keywords(
    request: KeywordLocalizationRequest,
    db: Session = Depends(get_db)
):
    service = LocalizedMarketingService(db)
    try:
        result = service.localize_keywords(
            request.base_keywords,
            request.target_regions,
            request.industry,
            request.language_preferences
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/keywords/{region}/trending")
async def get_trending_keywords(
    region: str,
    industry: Optional[str] = None,
    timeframe: str = "30d",
    limit: int = 50,
    db: Session = Depends(get_db)
):
    service = LocalizedMarketingService(db)
    try:
        keywords = service.get_trending_keywords(region, industry, timeframe, limit)
        return {"keywords": keywords}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/trends/analyze")
async def analyze_local_trends(
    request: TrendAnalysisRequest,
    db: Session = Depends(get_db)
):
    service = LocalizedMarketingService(db)
    try:
        result = service.analyze_local_trends(
            request.region,
            request.trend_type,
            request.timeframe,
            request.filters
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trends/{region}")
async def get_regional_trends(
    region: str,
    trend_category: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    service = LocalizedMarketingService(db)
    try:
        trends = service.get_regional_trends(region, trend_category, limit, offset)
        return {"trends": trends}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ads/optimize")
async def optimize_ads_for_region(
    region: str,
    ad_data: Dict[str, Any],
    optimization_type: str = "performance",
    db: Session = Depends(get_db)
):
    service = LocalizedMarketingService(db)
    try:
        result = service.optimize_ads_for_region(region, ad_data, optimization_type)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ads/{region}/best-practices")
async def get_regional_ad_best_practices(
    region: str,
    ad_type: Optional[str] = None,
    industry: Optional[str] = None,
    db: Session = Depends(get_db)
):
    service = LocalizedMarketingService(db)
    try:
        best_practices = service.get_regional_ad_best_practices(region, ad_type, industry)
        return {"best_practices": best_practices}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/campaigns/adapt")
async def adapt_campaign_for_region(
    campaign_id: str,
    target_regions: List[str],
    adaptation_type: str = "full",
    db: Session = Depends(get_db)
):
    service = LocalizedMarketingService(db)
    try:
        result = service.adapt_campaign_for_region(campaign_id, target_regions, adaptation_type)
        return {
            "message": "JackieCampaign adapted for regions successfully",
            "adapted_campaigns": result["adapted_campaigns"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/campaigns/{region}/performance")
async def get_regional_campaign_performance(
    region: str,
    campaign_id: Optional[str] = None,
    timeframe: str = "30d",
    db: Session = Depends(get_db)
):
    service = LocalizedMarketingService(db)
    try:
        performance = service.get_regional_campaign_performance(region, campaign_id, timeframe)
        return performance
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cultural/analyze")
async def analyze_cultural_context(
    region: str,
    content: str,
    content_type: str,
    db: Session = Depends(get_db)
):
    service = LocalizedMarketingService(db)
    try:
        result = service.analyze_cultural_context(region, content, content_type)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/cultural/{region}/insights")
async def get_cultural_insights(
    region: str,
    insight_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    service = LocalizedMarketingService(db)
    try:
        insights = service.get_cultural_insights(region, insight_type)
        return {"insights": insights}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/language/translate")
async def translate_content(
    content: str,
    source_language: str,
    target_language: str,
    context: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db)
):
    service = LocalizedMarketingService(db)
    try:
        result = service.translate_content(content, source_language, target_language, context)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/languages/{region}/supported")
async def get_supported_languages_for_region(
    region: str,
    db: Session = Depends(get_db)
):
    service = LocalizedMarketingService(db)
    try:
        languages = service.get_supported_languages_for_region(region)
        return {"languages": languages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/audience/analyze")
async def analyze_regional_audience(
    region: str,
    audience_data: Dict[str, Any],
    analysis_type: str = "demographics",
    db: Session = Depends(get_db)
):
    service = LocalizedMarketingService(db)
    try:
        result = service.analyze_regional_audience(region, audience_data, analysis_type)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/audience/{region}/segments")
async def get_regional_audience_segments(
    region: str,
    segment_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    service = LocalizedMarketingService(db)
    try:
        segments = service.get_regional_audience_segments(region, segment_type, limit, offset)
        return {"segments": segments}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/competition/analyze")
async def analyze_regional_competition(
    region: str,
    industry: str,
    analysis_scope: str = "comprehensive",
    db: Session = Depends(get_db)
):
    service = LocalizedMarketingService(db)
    try:
        result = service.analyze_regional_competition(region, industry, analysis_scope)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/competition/{region}/insights")
async def get_regional_competition_insights(
    region: str,
    industry: Optional[str] = None,
    insight_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    service = LocalizedMarketingService(db)
    try:
        insights = service.get_regional_competition_insights(region, industry, insight_type)
        return {"insights": insights}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/timing/optimize")
async def optimize_timing_for_region(
    region: str,
    content_type: str,
    target_audience: List[str],
    optimization_goal: str = "engagement",
    db: Session = Depends(get_db)
):
    service = LocalizedMarketingService(db)
    try:
        result = service.optimize_timing_for_region(region, content_type, target_audience, optimization_goal)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/timing/{region}/recommendations")
async def get_timing_recommendations(
    region: str,
    content_type: Optional[str] = None,
    audience_segment: Optional[str] = None,
    db: Session = Depends(get_db)
):
    service = LocalizedMarketingService(db)
    try:
        recommendations = service.get_timing_recommendations(region, content_type, audience_segment)
        return {"recommendations": recommendations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/holidays/plan")
async def plan_for_regional_holidays(
    region: str,
    planning_period: str,
    campaign_type: str,
    db: Session = Depends(get_db)
):
    service = LocalizedMarketingService(db)
    try:
        result = service.plan_for_regional_holidays(region, planning_period, campaign_type)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/holidays/{region}/calendar")
async def get_regional_holiday_calendar(
    region: str,
    year: Optional[int] = None,
    db: Session = Depends(get_db)
):
    service = LocalizedMarketingService(db)
    try:
        calendar = service.get_regional_holiday_calendar(region, year)
        return {"calendar": calendar}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/regulations/check")
async def check_regional_regulations(
    region: str,
    content_type: str,
    content: str,
    db: Session = Depends(get_db)
):
    service = LocalizedMarketingService(db)
    try:
        result = service.check_regional_regulations(region, content_type, content)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/regulations/{region}/guidelines")
async def get_regional_regulatory_guidelines(
    region: str,
    content_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    service = LocalizedMarketingService(db)
    try:
        guidelines = service.get_regional_regulatory_guidelines(region, content_type)
        return {"guidelines": guidelines}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/currency/optimize")
async def optimize_for_regional_currency(
    region: str,
    pricing_data: Dict[str, Any],
    optimization_strategy: str = "competitive",
    db: Session = Depends(get_db)
):
    service = LocalizedMarketingService(db)
    try:
        result = service.optimize_for_regional_currency(region, pricing_data, optimization_strategy)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/currency/{region}/rates")
async def get_regional_currency_rates(
    region: str,
    base_currency: str = "USD",
    db: Session = Depends(get_db)
):
    service = LocalizedMarketingService(db)
    try:
        rates = service.get_regional_currency_rates(region, base_currency)
        return {"rates": rates}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/regions/supported")
async def get_supported_regions(db: Session = Depends(get_db)):
    service = LocalizedMarketingService(db)
    try:
        regions = service.get_supported_regions()
        return {"regions": regions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/regions/{region}/info")
async def get_region_info(region: str, db: Session = Depends(get_db)):
    service = LocalizedMarketingService(db)
    try:
        info = service.get_region_info(region)
        if not info:
            raise HTTPException(status_code=404, detail="Region not found")
        return info
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/overview")
async def get_localized_marketing_overview(
    timeframe: str = "30d",
    db: Session = Depends(get_db)
):
    service = LocalizedMarketingService(db)
    try:
        overview = service.get_localized_marketing_overview(timeframe)
        return overview
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/{region}/performance")
async def get_regional_performance_analytics(
    region: str,
    metrics: List[str],
    timeframe: str = "30d",
    db: Session = Depends(get_db)
):
    service = LocalizedMarketingService(db)
    try:
        analytics = service.get_regional_performance_analytics(region, metrics, timeframe)
        return analytics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
