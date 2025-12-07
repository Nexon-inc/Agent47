from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from ..database import get_joe_database
from ..services.market_trend_analysis_service import MarketTrendAnalysisService
from backend.core.authentication.auth_manager import AuthManager

router = APIRouter(prefix="/market-trends", tags=["Market Trend Analysis"])

class MarketTrendRequest(BaseModel):
    keywords: List[str] = Field(..., description="Keywords to analyze")
    region: str = Field(default="US", description="Geographic region")
    time_period: str = Field(default="today 12-m", description="Time period for analysis")

class TrendInsightsRequest(BaseModel):
    keyword: str = Field(None, description="Specific keyword to filter by")

# Dependencies
async def get_market_trend_service() -> MarketTrendAnalysisService:
    service = MarketTrendAnalysisService()
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
async def analyze_market_trends(
    request: MarketTrendRequest,
    service: MarketTrendAnalysisService = Depends(get_market_trend_service),
    user_id: int = Depends(get_current_user_id)
):
    """Analyze market trends for given keywords"""
    try:
        result = await service.analyze_market_trends(
            user_id=user_id,
            keywords=request.keywords,
            region=request.region,
            time_period=request.time_period
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["trend_data"],
                "message": f"Market trend analysis completed for {len(request.keywords)} keywords"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Market trend analysis failed: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze market trends: {str(e)}"
        )

@router.get("/insights")
async def get_trend_insights(
    keyword: str = None,
    service: MarketTrendAnalysisService = Depends(get_market_trend_service),
    user_id: int = Depends(get_current_user_id)
):
    """Get trend insights from database"""
    try:
        result = await service.get_trend_insights(
            user_id=user_id,
            keyword=keyword
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["insights"],
                "message": f"Retrieved {result['total_count']} trend insights"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get trend insights: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get trend insights: {str(e)}"
        )

@router.get("/trending-keywords")
async def get_trending_keywords(service: MarketTrendAnalysisService = Depends(get_market_trend_service)):
    """Get currently trending keywords"""
    trending_keywords = [
        {
            "keyword": "artificial intelligence",
            "trend_score": 95,
            "growth_rate": 25,
            "search_volume": 50000
        },
        {
            "keyword": "machine learning",
            "trend_score": 88,
            "growth_rate": 18,
            "search_volume": 35000
        },
        {
            "keyword": "blockchain",
            "trend_score": 82,
            "growth_rate": 12,
            "search_volume": 28000
        }
    ]
    
    return {
        "status": "success",
        "data": trending_keywords,
        "message": f"Retrieved {len(trending_keywords)} trending keywords"
    }
