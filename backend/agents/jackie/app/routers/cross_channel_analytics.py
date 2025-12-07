from fastapi import APIRouter, HTTPException
from typing import Dict, List, Any

from ..services.cross_channel_analytics_service import CrossChannelAnalyticsService

router = APIRouter(prefix="/cross-channel-analytics", tags=["Cross-Channel Analytics"])

@router.post("/unify-metrics")
async def unify_channel_metrics(campaign_id: str, channel_data: Dict[str, Any]):
    try:
        service = CrossChannelAnalyticsService()
        await service.initialize()
        return await service.unify_channel_metrics(campaign_id, channel_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/compare-performance")
async def compare_channel_performance(channels: List[str], comparison_metrics: List[str]):
    try:
        service = CrossChannelAnalyticsService()
        await service.initialize()
        return await service.compare_channel_performance(channels, comparison_metrics)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-insights")
async def generate_performance_insights(analytics_data: Dict[str, Any], insight_focus: List[str]):
    try:
        service = CrossChannelAnalyticsService()
        await service.initialize()
        return await service.generate_performance_insights(analytics_data, insight_focus)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics")
async def get_cross_channel_analytics(timeframe: str = "30d"):
    try:
        service = CrossChannelAnalyticsService()
        await service.initialize()
        return await service.get_cross_channel_analytics(timeframe)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
