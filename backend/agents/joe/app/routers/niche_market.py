from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List
from pydantic import BaseModel, Field

from ..database import get_joe_database
from ..services.niche_market_service import NicheMarketService

router = APIRouter(prefix="/niche-market", tags=["Niche Markets"])

class NicheMarketRequest(BaseModel):
    industry: str = Field(..., description="Industry to find niches in")
    criteria: Dict[str, Any] = Field(default={}, description="Search criteria")

class NicheAnalysisRequest(BaseModel):
    niche_name: str = Field(..., description="Niche market to analyze")
    market_data: Dict[str, Any] = Field(default={}, description="Additional market data")

# Dependency
async def get_niche_market_service() -> NicheMarketService:
    service = NicheMarketService()
    await service.initialize()
    return service

@router.post("/find")
async def find_niche_markets(
    request: NicheMarketRequest,
    service: NicheMarketService = Depends(get_niche_market_service)
):
    """Find profitable niche markets within an industry"""
    try:
        result = await service.find_niche_markets(
            user_id=1,  # TODO: Get from authentication
            industry=request.industry,
            criteria=request.criteria
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["niche_markets"],
                "message": f"Found {result['total_found']} niche markets in {request.industry}"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Niche market discovery failed: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to find niche markets: {str(e)}"
        )

@router.post("/analyze")
async def analyze_niche_potential(
    request: NicheAnalysisRequest,
    service: NicheMarketService = Depends(get_niche_market_service)
):
    """Analyze the potential of a specific niche market"""
    try:
        result = await service.analyze_niche_potential(
            user_id=1,  # TODO: Get from authentication
            niche_name=request.niche_name,
            market_data=request.market_data
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["analysis"],
                "message": f"Niche analysis completed for {request.niche_name}"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Niche analysis failed: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze niche potential: {str(e)}"
        )

@router.get("/trending-niches")
async def get_trending_niches(service: NicheMarketService = Depends(get_niche_market_service)):
    """Get trending niche markets"""
    trending_niches = [
        {
            "niche": "AI-Powered Personal Assistants",
            "growth_rate": 45.2,
            "market_size": "$2.5B",
            "competition": "Medium",
            "trend": "increasing"
        },
        {
            "niche": "Sustainable Fashion",
            "growth_rate": 32.8,
            "market_size": "$8.5B",
            "competition": "High",
            "trend": "stable"
        },
        {
            "niche": "Remote Work Tools",
            "growth_rate": 28.5,
            "market_size": "$15.2B",
            "competition": "Medium",
            "trend": "increasing"
        }
    ]
    
    return {
        "status": "success",
        "data": trending_niches,
        "message": f"Retrieved {len(trending_niches)} trending niches"
    }
