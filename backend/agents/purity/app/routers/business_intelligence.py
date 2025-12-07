from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any
from pydantic import BaseModel, Field

from ..database import get_purity_database
from ..services.business_intelligence_service import BusinessIntelligenceService

router = APIRouter(prefix="/business-intelligence", tags=["Business Intelligence"])

class BusinessIntelligenceRequest(BaseModel):
    business_id: str = Field(..., description="Business ID")
    data_sources: list = Field(..., description="Data sources to analyze")
    analysis_period: str = Field(..., description="Analysis period")
    metrics: list = Field(..., description="Key metrics to track")

@router.post("/generate-insights")
async def generate_business_insights(
    request: BusinessIntelligenceRequest,
    db: AsyncSession = Depends(get_purity_database)
):
    """Generate business intelligence insights and analytics"""
    try:
        service = BusinessIntelligenceService()
        result = await service.generate_business_insights(
            db=db,
            business_id=request.business_id,
            data_sources=request.data_sources,
            analysis_period=request.analysis_period,
            metrics=request.metrics
        )
        return {
            "status": "success",
            "data": result,
            "message": "Business insights generated successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate business insights: {str(e)}"
        )

@router.get("/kpi-templates")
async def get_kpi_templates(db: AsyncSession = Depends(get_purity_database)):
    """Get KPI templates and business metrics"""
    kpis = {
        "financial_kpis": ["Revenue growth", "Profit margin", "Cash flow", "Customer lifetime value"],
        "operational_kpis": ["Customer acquisition cost", "Conversion rate", "Churn rate", "Employee productivity"],
        "marketing_kpis": ["Website traffic", "Lead generation", "Social media engagement", "Email open rates"],
        "customer_kpis": ["Customer satisfaction", "Net promoter score", "Customer retention", "Support ticket volume"]
    }
    return {"status": "success", "data": kpis, "message": "KPI templates retrieved successfully"}
