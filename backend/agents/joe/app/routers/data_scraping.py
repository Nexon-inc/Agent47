from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List
from pydantic import BaseModel, Field

from ..database import get_joe_database
from ..services.data_scraping_service import DataScrapingService

router = APIRouter(prefix="/data-scraping", tags=["Data Scraping"])

class DataScrapingRequest(BaseModel):
    urls: List[str] = Field(..., description="URLs to scrape")
    selectors: Dict[str, str] = Field(default={}, description="CSS selectors for specific data")
    data_type: str = Field(default="general", description="Type of data to scrape")

# Dependency
async def get_data_scraping_service() -> DataScrapingService:
    service = DataScrapingService()
    await service.initialize()
    return service

@router.post("/scrape")
async def scrape_data(
    request: DataScrapingRequest,
    service: DataScrapingService = Depends(get_data_scraping_service)
):
    """Scrape data from specified URLs"""
    try:
        result = await service.scrape_data(
            user_id=1,  # TODO: Get from authentication
            urls=request.urls,
            selectors=request.selectors,
            data_type=request.data_type
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["scraped_data"],
                "message": f"Data scraped from {len(request.urls)} URLs"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Data scraping failed: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to scrape data: {str(e)}"
        )

@router.get("/history")
async def get_scraping_history(
    limit: int = 10,
    service: DataScrapingService = Depends(get_data_scraping_service)
):
    """Get scraping history for user"""
    try:
        result = await service.get_scraping_history(
            user_id=1,  # TODO: Get from authentication
            limit=limit
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["history"],
                "message": f"Retrieved {result['total_records']} scraping records"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get scraping history: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get scraping history: {str(e)}"
        )

@router.get("/status")
async def get_scraping_status(service: DataScrapingService = Depends(get_data_scraping_service)):
    """Get scraping service status"""
    status_info = {
        "service": "Data Scraping",
        "status": "active",
        "features": [
            "Web scraping",
            "Data extraction",
            "History tracking",
            "GDPR compliance"
        ],
        "supported_sources": [
            "Websites",
            "Social media",
            "News sites",
            "E-commerce platforms"
        ]
    }
    
    return {
        "status": "success",
        "data": status_info,
        "message": "Data scraping service is operational"
    }
