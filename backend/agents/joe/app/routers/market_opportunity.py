from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List
from pydantic import BaseModel, Field

from ..database import get_joe_database
from ..services.market_opportunity_service import MarketOpportunityService

router = APIRouter(prefix="/market-opportunity", tags=["Market Opportunity"])

class OpportunityScoringRequest(BaseModel):
    opportunity_data: Dict[str, Any] = Field(..., description="Opportunity data for scoring")

class OpportunityRankingRequest(BaseModel):
    opportunities: List[Dict[str, Any]] = Field(..., description="List of opportunities to rank")

# Dependency
async def get_market_opportunity_service() -> MarketOpportunityService:
    service = MarketOpportunityService()
    await service.initialize()
    return service

@router.post("/score-opportunity")
async def score_market_opportunity(
    request: OpportunityScoringRequest,
    service: MarketOpportunityService = Depends(get_market_opportunity_service)
):
    """Score a market opportunity based on multiple criteria"""
    try:
        result = await service.score_market_opportunity(
            user_id=1,  # TODO: Get from authentication
            opportunity_data=request.opportunity_data
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["scoring_data"],
                "message": "Market opportunity scored successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Opportunity scoring failed: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to score market opportunity: {str(e)}"
        )

@router.post("/rank-opportunities")
async def rank_opportunities(
    request: OpportunityRankingRequest,
    service: MarketOpportunityService = Depends(get_market_opportunity_service)
):
    """Rank multiple market opportunities by score"""
    try:
        result = await service.rank_opportunities(
            user_id=1,  # TODO: Get from authentication
            opportunities=request.opportunities
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["ranking_data"],
                "message": f"Ranked {len(request.opportunities)} opportunities"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Opportunity ranking failed: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to rank opportunities: {str(e)}"
        )

@router.get("/scoring-criteria")
async def get_scoring_criteria(service: MarketOpportunityService = Depends(get_market_opportunity_service)):
    """Get available scoring criteria for market opportunities"""
    criteria = [
        {
            "id": "market_size",
            "name": "Market Size",
            "description": "Total addressable market size",
            "weight": 20,
            "scale": "1-10"
        },
        {
            "id": "growth_potential",
            "name": "Growth Potential",
            "description": "Expected market growth rate",
            "weight": 25,
            "scale": "1-10"
        },
        {
            "id": "competition_level",
            "name": "Competition Level",
            "description": "Intensity of market competition",
            "weight": 15,
            "scale": "1-10"
        },
        {
            "id": "entry_barriers",
            "name": "Entry Barriers",
            "description": "Barriers to market entry",
            "weight": 15,
            "scale": "1-10"
        },
        {
            "id": "profitability",
            "name": "Profitability",
            "description": "Expected profit margins",
            "weight": 15,
            "scale": "1-10"
        },
        {
            "id": "scalability",
            "name": "Scalability",
            "description": "Potential for business scaling",
            "weight": 10,
            "scale": "1-10"
        }
    ]
    
    return {
        "status": "success",
        "data": criteria,
        "message": f"Retrieved {len(criteria)} scoring criteria"
    }
