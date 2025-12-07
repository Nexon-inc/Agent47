from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any
from pydantic import BaseModel, Field

from ..database import get_purity_database
from ..services.business_model_canvas_service import BusinessModelCanvasService

router = APIRouter(prefix="/business-model-canvas", tags=["Business Model Canvas"])

class BusinessModelCanvasRequest(BaseModel):
    business_idea: str = Field(..., description="Business idea description")
    target_market: str = Field(..., description="Target market")
    business_type: str = Field(..., description="Type of business")

@router.post("/create")
async def create_business_model_canvas(
    request: BusinessModelCanvasRequest,
    db: AsyncSession = Depends(get_purity_database)
):
    """Create a complete Business Model Canvas with all 9 components"""
    try:
        service = BusinessModelCanvasService()
        result = await service.create_business_model_canvas(
            db=db,
            business_idea=request.business_idea,
            target_market=request.target_market,
            business_type=request.business_type
        )
        return {
            "status": "success",
            "data": result,
            "message": "Business Model Canvas created successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create Business Model Canvas: {str(e)}"
        )

@router.get("/components")
async def get_canvas_components(db: AsyncSession = Depends(get_purity_database)):
    """Get the 9 components of the Business Model Canvas"""
    components = {
        "key_partners": "Strategic alliances and partnerships",
        "key_activities": "Core business activities and processes",
        "key_resources": "Essential resources and assets",
        "value_propositions": "Unique value offered to customers",
        "customer_relationships": "How to interact with customers",
        "channels": "Distribution and communication channels",
        "customer_segments": "Target customer groups",
        "cost_structure": "Major cost categories",
        "revenue_streams": "Sources of income"
    }
    return {"status": "success", "data": components, "message": "Canvas components retrieved successfully"}
