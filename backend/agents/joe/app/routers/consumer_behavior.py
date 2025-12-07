from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List
from pydantic import BaseModel, Field

from ..database import get_joe_database
from ..services.consumer_behavior_service import ConsumerBehaviorService

router = APIRouter(prefix="/consumer-behavior", tags=["Consumer Behavior"])

class ConsumerBehaviorRequest(BaseModel):
    product_category: str = Field(..., description="Product category to analyze")
    demographics: Dict[str, Any] = Field(default={}, description="Demographic filters")
    time_period: str = Field(default="30d", description="Time period for analysis")

class BehaviorTrendsRequest(BaseModel):
    category: str = Field(..., description="Category to analyze trends for")
    metric: str = Field(default="purchase_volume", description="Metric to track")

# Dependency
async def get_consumer_behavior_service() -> ConsumerBehaviorService:
    service = ConsumerBehaviorService()
    await service.initialize()
    return service

@router.post("/analyze")
async def analyze_consumer_behavior(
    request: ConsumerBehaviorRequest,
    service: ConsumerBehaviorService = Depends(get_consumer_behavior_service)
):
    """Analyze consumer behavior for a product category"""
    try:
        result = await service.analyze_consumer_behavior(
            user_id=1,  # TODO: Get from authentication
            product_category=request.product_category,
            demographics=request.demographics,
            time_period=request.time_period
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["behavior_data"],
                "message": f"Consumer behavior analysis completed for {request.product_category}"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Consumer behavior analysis failed: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze consumer behavior: {str(e)}"
        )

@router.get("/trends/{category}")
async def get_behavior_trends(
    category: str,
    metric: str = "purchase_volume",
    service: ConsumerBehaviorService = Depends(get_consumer_behavior_service)
):
    """Get behavior trends for a category"""
    try:
        result = await service.get_behavior_trends(
            user_id=1,  # TODO: Get from authentication
            category=category,
            metric=metric
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["trends"],
                "message": f"Retrieved behavior trends for {category}"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get behavior trends: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get behavior trends: {str(e)}"
        )

@router.get("/insights")
async def get_behavior_insights(service: ConsumerBehaviorService = Depends(get_consumer_behavior_service)):
    """Get general consumer behavior insights"""
    insights = [
        {
            "insight": "Mobile shopping continues to grow",
            "percentage": 65,
            "trend": "increasing"
        },
        {
            "insight": "Price sensitivity is highest among millennials",
            "percentage": 78,
            "trend": "stable"
        },
        {
            "insight": "Sustainability influences purchase decisions",
            "percentage": 45,
            "trend": "increasing"
        }
    ]
    
    return {
        "status": "success",
        "data": insights,
        "message": f"Retrieved {len(insights)} consumer behavior insights"
    }
