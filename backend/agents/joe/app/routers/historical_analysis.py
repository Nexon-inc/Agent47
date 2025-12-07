from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List
from pydantic import BaseModel, Field

from ..database import get_joe_database
from ..services.historical_analysis_service import HistoricalAnalysisService

router = APIRouter(prefix="/historical-analysis", tags=["Historical Analysis"])

class HistoricalTrendRequest(BaseModel):
    topic: str = Field(..., description="Topic to analyze")
    time_period: str = Field(default="1_year", description="Time period for analysis")

class HistoricalComparisonRequest(BaseModel):
    current_data: Dict[str, Any] = Field(..., description="Current period data")
    historical_data: Dict[str, Any] = Field(..., description="Historical period data")

# Dependency
async def get_historical_analysis_service() -> HistoricalAnalysisService:
    service = HistoricalAnalysisService()
    await service.initialize()
    return service

@router.post("/analyze-trends")
async def analyze_historical_trends(
    request: HistoricalTrendRequest,
    service: HistoricalAnalysisService = Depends(get_historical_analysis_service)
):
    """Analyze historical trends for a specific topic"""
    try:
        result = await service.analyze_historical_trends(
            user_id=1,  # TODO: Get from authentication
            topic=request.topic,
            time_period=request.time_period
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["analysis_data"],
                "message": f"Historical trends analyzed for {request.topic}"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Historical trend analysis failed: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze historical trends: {str(e)}"
        )

@router.post("/compare-data")
async def compare_historical_data(
    request: HistoricalComparisonRequest,
    service: HistoricalAnalysisService = Depends(get_historical_analysis_service)
):
    """Compare current data with historical data"""
    try:
        result = await service.compare_historical_data(
            user_id=1,  # TODO: Get from authentication
            current_data=request.current_data,
            historical_data=request.historical_data
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["comparison_data"],
                "message": "Historical data comparison completed"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Historical comparison failed: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compare historical data: {str(e)}"
        )

@router.get("/time-periods")
async def get_time_periods(service: HistoricalAnalysisService = Depends(get_historical_analysis_service)):
    """Get available time periods for historical analysis"""
    time_periods = [
        {
            "id": "3_months",
            "name": "3 Months",
            "description": "Quarterly analysis",
            "data_points": "90 days",
            "suitable_for": "Short-term trends"
        },
        {
            "id": "6_months",
            "name": "6 Months",
            "description": "Semi-annual analysis",
            "data_points": "180 days",
            "suitable_for": "Medium-term trends"
        },
        {
            "id": "1_year",
            "name": "1 Year",
            "description": "Annual analysis",
            "data_points": "365 days",
            "suitable_for": "Long-term trends"
        },
        {
            "id": "2_years",
            "name": "2 Years",
            "description": "Biannual analysis",
            "data_points": "730 days",
            "suitable_for": "Extended trends"
        }
    ]
    
    return {
        "status": "success",
        "data": time_periods,
        "message": f"Retrieved {len(time_periods)} time periods"
    }
