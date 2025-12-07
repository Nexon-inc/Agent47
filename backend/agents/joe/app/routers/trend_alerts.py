from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List
from pydantic import BaseModel, Field

from ..database import get_joe_database
from ..services.trend_alerts_service import TrendAlertsService

router = APIRouter(prefix="/trend-alerts", tags=["Trend Alerts"])

class TrendAlertRequest(BaseModel):
    alert_type: str = Field(..., description="Type of alert to create")
    keywords: List[str] = Field(..., description="Keywords to monitor")
    threshold: float = Field(default=0.8, description="Alert threshold")

# Dependency
async def get_trend_alerts_service() -> TrendAlertsService:
    service = TrendAlertsService()
    await service.initialize()
    return service

@router.post("/create")
async def create_trend_alert(
    request: TrendAlertRequest,
    service: TrendAlertsService = Depends(get_trend_alerts_service)
):
    """Create a new trend alert"""
    try:
        result = await service.create_trend_alert(
            user_id=1,  # TODO: Get from authentication
            alert_type=request.alert_type,
            keywords=request.keywords,
            threshold=request.threshold
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["alert_data"],
                "message": f"Trend alert created for {request.alert_type}"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Trend alert creation failed: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create trend alert: {str(e)}"
        )

@router.get("/active")
async def get_active_alerts(service: TrendAlertsService = Depends(get_trend_alerts_service)):
    """Get user's active trend alerts"""
    try:
        result = await service.get_active_alerts(
            user_id=1  # TODO: Get from authentication
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["alerts"],
                "message": f"Retrieved {result['total_alerts']} active alerts"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get active alerts: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get active alerts: {str(e)}"
        )

@router.get("/types")
async def get_alert_types(service: TrendAlertsService = Depends(get_trend_alerts_service)):
    """Get available alert types"""
    alert_types = [
        {
            "id": "market_trend",
            "name": "Market Trend Alert",
            "description": "Monitor emerging market trends",
            "keywords_required": True,
            "threshold_range": "0.1-1.0"
        },
        {
            "id": "competitor_move",
            "name": "Competitor Move Alert",
            "description": "Track competitor activities and moves",
            "keywords_required": True,
            "threshold_range": "0.1-1.0"
        },
        {
            "id": "industry_news",
            "name": "Industry News Alert",
            "description": "Monitor industry news and developments",
            "keywords_required": True,
            "threshold_range": "0.1-1.0"
        },
        {
            "id": "product_launch",
            "name": "Product Launch Alert",
            "description": "Track new product launches in the market",
            "keywords_required": False,
            "threshold_range": "0.1-1.0"
        }
    ]
    
    return {
        "status": "success",
        "data": alert_types,
        "message": f"Retrieved {len(alert_types)} alert types"
    }
