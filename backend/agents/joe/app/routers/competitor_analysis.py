from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from ..database import get_joe_database
from ..services.competitor_analysis_service import CompetitorAnalysisService
from core.authentication.auth_manager import AuthManager

router = APIRouter(prefix="/competitor-analysis", tags=["Competitor Analysis"])

class CompetitorAnalysisRequest(BaseModel):
    domain: str = Field(..., description="Main domain to analyze")
    competitors: List[str] = Field(default=[], description="List of competitor domains")

class CompetitorInsightsRequest(BaseModel):
    competitor_domain: str = Field(..., description="Specific competitor domain to analyze")

# Dependencies
async def get_competitor_analysis_service() -> CompetitorAnalysisService:
    service = CompetitorAnalysisService()
    await service.initialize()
    return service

async def get_current_user_id(authorization: Optional[str] = Header(None)) -> int:
    """Get current user ID from authentication token"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    try:
        # Extract token from "Bearer <token>" format
        token = authorization.replace("Bearer ", "")
        auth_manager = AuthManager()
        user_data = await auth_manager.verify_token(token)
        return user_data.get("user_id")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid authentication token: {str(e)}")

@router.post("/analyze")
async def analyze_competitors(
    request: CompetitorAnalysisRequest,
    service: CompetitorAnalysisService = Depends(get_competitor_analysis_service),
    user_id: int = Depends(get_current_user_id)
):
    """Analyze competitors for a given domain"""
    try:
        result = await service.analyze_competitors(
            user_id=user_id,
            domain=request.domain,
            competitors=request.competitors
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["analysis_results"],
                "message": f"Competitor analysis completed for {request.domain}"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Competitor analysis failed: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze competitors: {str(e)}"
        )

@router.get("/insights/{competitor_domain}")
async def get_competitor_insights(
    competitor_domain: str,
    service: CompetitorAnalysisService = Depends(get_competitor_analysis_service),
    user_id: int = Depends(get_current_user_id)
):
    """Get detailed insights for a specific competitor"""
    try:
        result = await service.get_competitor_insights(
            user_id=user_id,
            competitor_domain=competitor_domain
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["insights"],
                "message": f"Retrieved insights for {competitor_domain}"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get competitor insights: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get competitor insights: {str(e)}"
        )

@router.get("/top-competitors")
async def get_top_competitors(service: CompetitorAnalysisService = Depends(get_competitor_analysis_service)):
    """Get top competitors in the market"""
    top_competitors = [
        {
            "domain": "competitor1.com",
            "traffic_rank": 1,
            "monthly_visits": 150000,
            "market_share": 35.2
        },
        {
            "domain": "competitor2.com", 
            "traffic_rank": 2,
            "monthly_visits": 120000,
            "market_share": 28.1
        },
        {
            "domain": "competitor3.com",
            "traffic_rank": 3,
            "monthly_visits": 95000,
            "market_share": 22.3
        }
    ]
    
    return {
        "status": "success",
        "data": top_competitors,
        "message": f"Retrieved {len(top_competitors)} top competitors"
    }
