from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List
from pydantic import BaseModel, Field

from ..database import get_joe_database
from ..services.industry_report_service import IndustryReportService

router = APIRouter(prefix="/industry-report", tags=["Industry Reports"])

class IndustryReportRequest(BaseModel):
    industry: str = Field(..., description="Industry to generate report for")
    report_type: str = Field(default="comprehensive", description="Type of report to generate")
    time_period: str = Field(default="12m", description="Time period for analysis")

# Dependency
async def get_industry_report_service() -> IndustryReportService:
    service = IndustryReportService()
    await service.initialize()
    return service

@router.post("/generate")
async def generate_industry_report(
    request: IndustryReportRequest,
    service: IndustryReportService = Depends(get_industry_report_service)
):
    """Generate industry report for specified industry"""
    try:
        result = await service.generate_industry_report(
            user_id=1,  # TODO: Get from authentication
            industry=request.industry,
            report_type=request.report_type,
            time_period=request.time_period
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["report_data"],
                "message": f"Industry report generated for {request.industry}"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Industry report generation failed: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate industry report: {str(e)}"
        )

@router.get("/insights/{industry}")
async def get_industry_insights(
    industry: str,
    service: IndustryReportService = Depends(get_industry_report_service)
):
    """Get key insights for an industry"""
    try:
        result = await service.get_industry_insights(
            user_id=1,  # TODO: Get from authentication
            industry=industry
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["insights"],
                "message": f"Retrieved {result['total_insights']} insights for {industry}"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get industry insights: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get industry insights: {str(e)}"
        )

@router.get("/trending-industries")
async def get_trending_industries(service: IndustryReportService = Depends(get_industry_report_service)):
    """Get trending industries"""
    trending_industries = [
        {
            "industry": "Artificial Intelligence",
            "growth_rate": 25.5,
            "market_size": "$500B",
            "trend": "increasing"
        },
        {
            "industry": "E-commerce",
            "growth_rate": 18.2,
            "market_size": "$6.2T",
            "trend": "stable"
        },
        {
            "industry": "Healthcare Technology",
            "growth_rate": 22.1,
            "market_size": "$350B",
            "trend": "increasing"
        }
    ]
    
    return {
        "status": "success",
        "data": trending_industries,
        "message": f"Retrieved {len(trending_industries)} trending industries"
    }
