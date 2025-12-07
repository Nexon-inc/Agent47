from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List
from pydantic import BaseModel, Field

from ..database import get_joe_database
from ..services.customer_persona_service import CustomerPersonaService

router = APIRouter(prefix="/customer-persona", tags=["Customer Personas"])

class PersonaRequest(BaseModel):
    target_audience: str = Field(..., description="Target audience for persona")
    industry: str = Field(..., description="Industry context")
    demographics: Dict[str, Any] = Field(default={}, description="Demographic data")

class PersonaInsightsRequest(BaseModel):
    persona_id: int = Field(None, description="Persona ID to analyze")
    data_sources: List[str] = Field(default=[], description="Data sources to analyze")

# Dependency
async def get_customer_persona_service() -> CustomerPersonaService:
    service = CustomerPersonaService()
    await service.initialize()
    return service

@router.post("/build")
async def build_customer_persona(
    request: PersonaRequest,
    service: CustomerPersonaService = Depends(get_customer_persona_service)
):
    """Build detailed customer persona for target audience"""
    try:
        result = await service.build_customer_persona(
            user_id=1,  # TODO: Get from authentication
            target_audience=request.target_audience,
            industry=request.industry,
            demographics=request.demographics
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["persona_data"],
                "message": f"Customer persona built for {request.target_audience}"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Persona building failed: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to build customer persona: {str(e)}"
        )

@router.post("/analyze-insights")
async def analyze_persona_insights(
    request: PersonaInsightsRequest,
    service: CustomerPersonaService = Depends(get_customer_persona_service)
):
    """Analyze insights from customer persona data"""
    try:
        result = await service.analyze_persona_insights(
            user_id=1,  # TODO: Get from authentication
            persona_id=request.persona_id,
            data_sources=request.data_sources
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["insights"],
                "message": f"Retrieved {result['total_insights']} persona insights"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Persona insights analysis failed: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze persona insights: {str(e)}"
        )

@router.get("/templates")
async def get_persona_templates(service: CustomerPersonaService = Depends(get_customer_persona_service)):
    """Get customer persona templates"""
    templates = [
        {
            "id": "b2b_professional",
            "name": "B2B Professional",
            "description": "Business-to-business professional persona",
            "industry": "Technology",
            "characteristics": [
                "Decision maker",
                "Budget conscious",
                "Results oriented",
                "Time sensitive"
            ]
        },
        {
            "id": "startup_founder",
            "name": "Startup Founder",
            "description": "Early-stage startup founder persona",
            "industry": "Technology",
            "characteristics": [
                "Innovation focused",
                "Resource constrained",
                "Growth minded",
                "Risk tolerant"
            ]
        },
        {
            "id": "enterprise_manager",
            "name": "Enterprise Manager",
            "description": "Large enterprise manager persona",
            "industry": "Corporate",
            "characteristics": [
                "Process oriented",
                "Compliance focused",
                "Team leader",
                "Stability minded"
            ]
        }
    ]
    
    return {
        "status": "success",
        "data": templates,
        "message": f"Retrieved {len(templates)} persona templates"
    }
