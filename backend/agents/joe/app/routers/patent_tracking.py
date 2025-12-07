from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List
from pydantic import BaseModel, Field

from ..database import get_joe_database
from ..services.patent_tracking_service import PatentTrackingService

router = APIRouter(prefix="/patent-tracking", tags=["Patent Tracking"])

class PatentTrackingRequest(BaseModel):
    technology_area: str = Field(..., description="Technology area to track")
    keywords: List[str] = Field(default=[], description="Keywords to search for")
    time_period: str = Field(default="30d", description="Time period for tracking")

# Dependency
async def get_patent_tracking_service() -> PatentTrackingService:
    service = PatentTrackingService()
    await service.initialize()
    return service

@router.post("/track")
async def track_patents(
    request: PatentTrackingRequest,
    service: PatentTrackingService = Depends(get_patent_tracking_service)
):
    """Track patents in a specific technology area"""
    try:
        result = await service.track_patents(
            user_id=1,  # TODO: Get from authentication
            technology_area=request.technology_area,
            keywords=request.keywords,
            time_period=request.time_period
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["patent_data"],
                "message": f"Tracked {result['total_patents']} patents in {request.technology_area}"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Patent tracking failed: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to track patents: {str(e)}"
        )

@router.get("/trends/{technology_area}")
async def analyze_patent_trends(
    technology_area: str,
    service: PatentTrackingService = Depends(get_patent_tracking_service)
):
    """Analyze patent trends in a technology area"""
    try:
        result = await service.analyze_patent_trends(
            user_id=1,  # TODO: Get from authentication
            technology_area=technology_area
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["trends"],
                "message": f"Retrieved {result['total_trends']} patent trends for {technology_area}"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to analyze patent trends: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze patent trends: {str(e)}"
        )

@router.get("/technology-areas")
async def get_technology_areas(service: PatentTrackingService = Depends(get_patent_tracking_service)):
    """Get available technology areas for patent tracking"""
    areas = [
        {
            "id": "artificial_intelligence",
            "name": "Artificial Intelligence",
            "description": "AI and machine learning technologies",
            "patent_count": 15420,
            "growth_rate": 28.5
        },
        {
            "id": "blockchain",
            "name": "Blockchain",
            "description": "Distributed ledger technologies",
            "patent_count": 8230,
            "growth_rate": 35.2
        },
        {
            "id": "biotechnology",
            "name": "Biotechnology",
            "description": "Biological and medical technologies",
            "patent_count": 25680,
            "growth_rate": 22.1
        },
        {
            "id": "renewable_energy",
            "name": "Renewable Energy",
            "description": "Clean energy technologies",
            "patent_count": 18950,
            "growth_rate": 31.8
        }
    ]
    
    return {
        "status": "success",
        "data": areas,
        "message": f"Retrieved {len(areas)} technology areas"
    }
