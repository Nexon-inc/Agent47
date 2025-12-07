from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any
from pydantic import BaseModel, Field

from ..database import get_purity_database
from ..services.tax_planning_service import TaxPlanningService

router = APIRouter(prefix="/tax-planning", tags=["Tax Planning"])

class TaxPlanningRequest(BaseModel):
    business_location: str = Field(..., description="Business location")
    business_type: str = Field(..., description="Type of business")
    annual_revenue: float = Field(..., description="Annual revenue")
    business_structure: str = Field(..., description="Business structure")

@router.post("/create-strategy")
async def create_tax_strategy(
    request: TaxPlanningRequest,
    db: AsyncSession = Depends(get_purity_database)
):
    """Create automated tax planning strategy"""
    try:
        service = TaxPlanningService()
        result = await service.create_tax_strategy(
            db=db,
            business_location=request.business_location,
            business_type=request.business_type,
            annual_revenue=request.annual_revenue,
            business_structure=request.business_structure
        )
        return {
            "status": "success",
            "data": result,
            "message": "Tax strategy created successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create tax strategy: {str(e)}"
        )

@router.get("/tax-strategies")
async def get_tax_strategies(db: AsyncSession = Depends(get_purity_database)):
    """Get common tax strategies and best practices"""
    strategies = {
        "deductions": ["Business expenses", "Home office", "Vehicle use", "Equipment depreciation"],
        "credits": ["Research and development", "Small business health care", "Work opportunity"],
        "structures": ["Sole proprietorship", "LLC", "S-Corporation", "C-Corporation"],
        "timing": ["Accelerated depreciation", "Deferred income", "Prepaid expenses"]
    }
    return {"status": "success", "data": strategies, "message": "Tax strategies retrieved successfully"}
