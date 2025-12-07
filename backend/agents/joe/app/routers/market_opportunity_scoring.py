from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List
from pydantic import BaseModel, Field

from ..database import get_joe_database
from ..services.market_opportunity_scoring_service import MarketOpportunityScoringService

router = APIRouter(prefix="/market-opportunity-scoring", tags=["Market Opportunity Scoring"])

class OpportunityScoringRequest(BaseModel):
    opportunities: List[Dict[str, Any]] = Field(..., description="List of market opportunities to score")
    scoring_criteria: Dict[str, Any] = Field(..., description="Criteria for scoring opportunities")

class ReportGenerationRequest(BaseModel):
    scoring_results: Dict[str, Any] = Field(..., description="Results from opportunity scoring")
    report_format: str = Field(default="comprehensive", description="Format of the report to generate")

# Dependency
async def get_market_opportunity_scoring_service() -> MarketOpportunityScoringService:
    service = MarketOpportunityScoringService()
    await service.initialize()
    return service

@router.post("/score-opportunities")
async def score_market_opportunities(
    request: OpportunityScoringRequest,
    service: MarketOpportunityScoringService = Depends(get_market_opportunity_scoring_service)
):
    """Score and rank market opportunities based on defined criteria"""
    try:
        result = await service.score_market_opportunities(
            user_id=1,  # TODO: Get from authentication
            opportunities=request.opportunities,
            scoring_criteria=request.scoring_criteria
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["scoring_data"],
                "message": f"Scored {len(request.opportunities)} market opportunities successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Opportunity scoring failed: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to score market opportunities: {str(e)}"
        )

@router.post("/generate-report")
async def generate_opportunity_report(
    request: ReportGenerationRequest,
    service: MarketOpportunityScoringService = Depends(get_market_opportunity_scoring_service)
):
    """Generate detailed report for scored market opportunities"""
    try:
        result = await service.generate_opportunity_report(
            user_id=1,  # TODO: Get from authentication
            scoring_results=request.scoring_results,
            report_format=request.report_format
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["report_data"],
                "message": "Market opportunity report generated successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Report generation failed: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate opportunity report: {str(e)}"
        )

@router.get("/scoring-criteria")
async def get_scoring_criteria(service: MarketOpportunityScoringService = Depends(get_market_opportunity_scoring_service)):
    """Get available scoring criteria for market opportunities"""
    scoring_criteria = [
        {
            "criterion_id": "market_size",
            "name": "Market Size",
            "description": "Total addressable market size and potential",
            "weight": 0.25,
            "scale": ["small", "medium", "large", "very_large"],
            "importance": "High"
        },
        {
            "criterion_id": "growth_rate",
            "name": "Growth Rate",
            "description": "Market growth rate and expansion potential",
            "weight": 0.20,
            "scale": ["low", "medium", "high", "very_high"],
            "importance": "High"
        },
        {
            "criterion_id": "competition_level",
            "name": "Competition Level",
            "description": "Level of competition in the market",
            "weight": 0.15,
            "scale": ["low", "medium", "high", "very_high"],
            "importance": "Medium"
        },
        {
            "criterion_id": "entry_barriers",
            "name": "Entry Barriers",
            "description": "Barriers to entering the market",
            "weight": 0.15,
            "scale": ["low", "medium", "high", "very_high"],
            "importance": "Medium"
        },
        {
            "criterion_id": "profit_margin",
            "name": "Profit Margin",
            "description": "Potential profit margins in the market",
            "weight": 0.15,
            "scale": ["low", "medium", "high", "very_high"],
            "importance": "High"
        },
        {
            "criterion_id": "scalability",
            "name": "Scalability",
            "description": "Ability to scale the business model",
            "weight": 0.10,
            "scale": ["low", "medium", "high", "very_high"],
            "importance": "Medium"
        }
    ]
    
    return {
        "status": "success",
        "data": scoring_criteria,
        "message": f"Retrieved {len(scoring_criteria)} scoring criteria"
    }
