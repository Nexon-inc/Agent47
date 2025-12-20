from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List
from ..services.trend_alerts_service import TrendAlertsService
from ..deps import get_current_user
from core.database.models import User

router = APIRouter(prefix="/trend-alerts", tags=["Trend Alerts"])

@router.post("/setup-monitoring")
async def setup_trend_monitoring(
    keywords: List[str],
    platforms: List[str],
    alert_frequency: str = "daily",
    current_user: User = Depends(get_current_user),
    trend_alerts_service: TrendAlertsService = Depends()
):
    """Setup automated trend monitoring"""
    try:
        await trend_alerts_service.initialize()
        result = await trend_alerts_service.setup_trend_monitoring(
            current_user.id,
            keywords,
            platforms,
            alert_frequency
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stop-monitoring/{task_id}")
async def stop_trend_monitoring(
    task_id: str,
    current_user: User = Depends(get_current_user),
    trend_alerts_service: TrendAlertsService = Depends()
):
    """Stop trend monitoring for a specific task"""
    try:
        await trend_alerts_service.initialize()
        result = await trend_alerts_service.stop_monitoring(task_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/active-monitoring")
async def get_active_monitoring(
    current_user: User = Depends(get_current_user),
    trend_alerts_service: TrendAlertsService = Depends()
):
    """Get active monitoring tasks for a user"""
    try:
        await trend_alerts_service.initialize()
        result = await trend_alerts_service.get_active_monitoring(current_user.id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trend-data")
async def get_trend_data(
    keywords: List[str] = None,
    platforms: List[str] = None,
    current_user: User = Depends(get_current_user),
    trend_alerts_service: TrendAlertsService = Depends()
):
    """Get current trend data for specified keywords and platforms"""
    try:
        await trend_alerts_service.initialize()
        # This would return current trend data
        return {
            "success": True,
            "keywords": keywords or [],
            "platforms": platforms or [],
            "trend_data": "Current trend information"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
