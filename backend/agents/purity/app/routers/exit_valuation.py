from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any
from pydantic import BaseModel, Field

from ..database import get_purity_database
from ..services.exit_valuation_service import ExitValuationService

router = APIRouter(prefix="/exit-valuation", tags=["Exit Valuation"])

class ExitValuationRequest(BaseModel):
    business_type: str = Field(..., description="Type of business")
    annual_revenue: float = Field(..., description="Annual revenue")
    profit_margin: float = Field(..., description="Profit margin percentage")
    growth_rate: float = Field(..., description="Annual growth rate")
    market_conditions: str = Field(..., description="Current market conditions")

@router.post("/estimate-valuation")
async def estimate_business_valuation(
    request: ExitValuationRequest,
    db: AsyncSession = Depends(get_purity_database)
):
    """Estimate business valuation for potential exit"""
    try:
        service = ExitValuationService()
        result = await service.estimate_business_valuation(
            db=db,
            business_type=request.business_type,
            annual_revenue=request.annual_revenue,
            profit_margin=request.profit_margin,
            growth_rate=request.growth_rate,
            market_conditions=request.market_conditions
        )
        return {
            "status": "success",
            "data": result,
            "message": "Business valuation estimated successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to estimate business valuation: {str(e)}"
        )

@router.get("/valuation-methods")
async def get_valuation_methods(db: AsyncSession = Depends(get_purity_database)):
    """Get business valuation methods and approaches"""
    methods = {
        "asset_based": "Based on company assets and liabilities",
        "market_based": "Based on comparable company sales",
        "income_based": "Based on future cash flows and earnings",
        "discounted_cash_flow": "Present value of future cash flows",
        "multiple_analysis": "Revenue or earnings multiples"
    }
    return {"status": "success", "data": methods, "message": "Valuation methods retrieved successfully"}
