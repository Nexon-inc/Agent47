from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any, Optional
from pydantic import BaseModel
from ..services.analytics_service import AnalyticsService
from ..database import get_jackie_database

router = APIRouter()

async def get_analytics_service() -> AnalyticsService:
    service = AnalyticsService()
    await service.initialize()
    return service

@router.get("/overview", response_model=Dict[str, Any])
async def get_marketing_overview(
    user_id: int = Query(...),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    service: AnalyticsService = Depends(get_analytics_service)
):
    try:
        result = await service.get_marketing_overview(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/roi", response_model=Dict[str, Any])
async def get_roi_analysis(
    user_id: int = Query(...),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    service: AnalyticsService = Depends(get_analytics_service)
):
    try:
        result = await service.get_roi_analysis(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
