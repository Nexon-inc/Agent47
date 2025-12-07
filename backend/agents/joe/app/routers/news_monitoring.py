from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List
from pydantic import BaseModel, Field

from ..database import get_joe_database
from ..services.news_monitoring_service import NewsMonitoringService

router = APIRouter(prefix="/news-monitoring", tags=["News Monitoring"])

class NewsMonitoringRequest(BaseModel):
    industry: str = Field(..., description="Industry to monitor")
    keywords: List[str] = Field(default=[], description="Keywords to track")
    time_period: str = Field(default="24h", description="Time period for monitoring")

# Dependency
async def get_news_monitoring_service() -> NewsMonitoringService:
    service = NewsMonitoringService()
    await service.initialize()
    return service

@router.post("/monitor")
async def monitor_industry_news(
    request: NewsMonitoringRequest,
    service: NewsMonitoringService = Depends(get_news_monitoring_service)
):
    """Monitor industry news for specific keywords"""
    try:
        result = await service.monitor_industry_news(
            user_id=1,  # TODO: Get from authentication
            industry=request.industry,
            keywords=request.keywords,
            time_period=request.time_period
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["news_data"],
                "message": f"Monitored {result['total_articles']} news articles for {request.industry}"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"News monitoring failed: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to monitor news: {str(e)}"
        )

@router.get("/alerts")
async def get_news_alerts(
    alert_type: str = "all",
    service: NewsMonitoringService = Depends(get_news_monitoring_service)
):
    """Get news alerts for user"""
    try:
        result = await service.get_news_alerts(
            user_id=1,  # TODO: Get from authentication
            alert_type=alert_type
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["alerts"],
                "message": f"Retrieved {result['total_alerts']} news alerts"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get news alerts: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get news alerts: {str(e)}"
        )

@router.get("/sources")
async def get_news_sources(service: NewsMonitoringService = Depends(get_news_monitoring_service)):
    """Get available news sources"""
    sources = [
        {
            "id": "techcrunch",
            "name": "TechCrunch",
            "category": "Technology",
            "reliability": "High",
            "update_frequency": "Real-time"
        },
        {
            "id": "bloomberg",
            "name": "Bloomberg",
            "category": "Business",
            "reliability": "High",
            "update_frequency": "Real-time"
        },
        {
            "id": "reuters",
            "name": "Reuters",
            "category": "General",
            "reliability": "High",
            "update_frequency": "Real-time"
        },
        {
            "id": "industry_weekly",
            "name": "Industry Weekly",
            "category": "Industry",
            "reliability": "Medium",
            "update_frequency": "Weekly"
        }
    ]
    
    return {
        "status": "success",
        "data": sources,
        "message": f"Retrieved {len(sources)} news sources"
    }
