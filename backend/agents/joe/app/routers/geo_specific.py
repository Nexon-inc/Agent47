from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List
from pydantic import BaseModel, Field

from ..database import get_joe_database
from ..services.geo_specific_service import GeoSpecificService

router = APIRouter(prefix="/geo-specific", tags=["Geo-Specific Research"])

class RegionalAnalysisRequest(BaseModel):
    region: str = Field(..., description="Region to analyze")
    industry: str = Field(..., description="Industry to analyze")
    analysis_type: str = Field(default="comprehensive", description="Type of analysis")

# Dependency
async def get_geo_specific_service() -> GeoSpecificService:
    service = GeoSpecificService()
    await service.initialize()
    return service

@router.post("/analyze-regional-market")
async def analyze_regional_market(
    request: RegionalAnalysisRequest,
    service: GeoSpecificService = Depends(get_geo_specific_service)
):
    """Analyze market data for a specific region"""
    try:
        result = await service.analyze_regional_market(
            user_id=1,  # TODO: Get from authentication
            region=request.region,
            industry=request.industry,
            analysis_type=request.analysis_type
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["analysis_data"],
                "message": f"Regional market analysis completed for {request.region}"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Regional market analysis failed: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze regional market: {str(e)}"
        )

@router.get("/regional-trends/{region}")
async def get_regional_trends(
    region: str,
    service: GeoSpecificService = Depends(get_geo_specific_service)
):
    """Get trends specific to a region"""
    try:
        result = await service.get_regional_trends(
            user_id=1,  # TODO: Get from authentication
            region=region
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["trends"],
                "message": f"Retrieved {result['total_trends']} regional trends for {region}"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get regional trends: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get regional trends: {str(e)}"
        )

@router.get("/regions")
async def get_supported_regions(service: GeoSpecificService = Depends(get_geo_specific_service)):
    """Get supported regions for analysis"""
    regions = [
        {
            "id": "north_america",
            "name": "North America",
            "countries": ["USA", "Canada", "Mexico"],
            "data_availability": "High",
            "analysis_depth": "Comprehensive"
        },
        {
            "id": "europe",
            "name": "Europe",
            "countries": ["UK", "Germany", "France", "Spain", "Italy"],
            "data_availability": "High",
            "analysis_depth": "Comprehensive"
        },
        {
            "id": "asia_pacific",
            "name": "Asia Pacific",
            "countries": ["China", "Japan", "India", "Australia", "Singapore"],
            "data_availability": "Medium",
            "analysis_depth": "Standard"
        },
        {
            "id": "latin_america",
            "name": "Latin America",
            "countries": ["Brazil", "Argentina", "Chile", "Colombia"],
            "data_availability": "Medium",
            "analysis_depth": "Standard"
        }
    ]
    
    return {
        "status": "success",
        "data": regions,
        "message": f"Retrieved {len(regions)} supported regions"
    }
