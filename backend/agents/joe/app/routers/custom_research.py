from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List
from pydantic import BaseModel, Field

from ..database import get_joe_database
from ..services.custom_research_service import CustomResearchService

router = APIRouter(prefix="/custom-research", tags=["Custom Research"])

class CustomResearchRequest(BaseModel):
    query: str = Field(..., description="Research query to execute")
    research_type: str = Field(default="general", description="Type of research")
    data_sources: List[str] = Field(default=[], description="Data sources to use")

# Dependency
async def get_custom_research_service() -> CustomResearchService:
    service = CustomResearchService()
    await service.initialize()
    return service

@router.post("/execute")
async def execute_custom_query(
    request: CustomResearchRequest,
    service: CustomResearchService = Depends(get_custom_research_service)
):
    """Execute custom research query"""
    try:
        result = await service.execute_custom_query(
            user_id=1,  # TODO: Get from authentication
            query=request.query,
            research_type=request.research_type,
            data_sources=request.data_sources
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["research_data"],
                "message": f"Custom research executed for: {request.query}"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Custom research execution failed: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute custom research: {str(e)}"
        )

@router.get("/history")
async def get_research_history(
    limit: int = 10,
    service: CustomResearchService = Depends(get_custom_research_service)
):
    """Get user's research history"""
    try:
        result = await service.get_research_history(
            user_id=1,  # TODO: Get from authentication
            limit=limit
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["history"],
                "message": f"Retrieved {result['total_queries']} research queries"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get research history: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get research history: {str(e)}"
        )

@router.get("/query-templates")
async def get_query_templates(service: CustomResearchService = Depends(get_custom_research_service)):
    """Get research query templates"""
    templates = [
        {
            "id": "market_analysis",
            "name": "Market Analysis",
            "description": "Comprehensive market analysis template",
            "example": "Analyze the market size and growth potential for AI tools in healthcare",
            "research_type": "market_analysis"
        },
        {
            "id": "competitor_analysis",
            "name": "Competitor Analysis",
            "description": "Competitive landscape analysis template",
            "example": "Research competitors in the e-commerce platform market",
            "research_type": "competitor_analysis"
        },
        {
            "id": "trend_analysis",
            "name": "Trend Analysis",
            "description": "Industry trend analysis template",
            "example": "Identify emerging trends in renewable energy technology",
            "research_type": "trend_analysis"
        }
    ]
    
    return {
        "status": "success",
        "data": templates,
        "message": f"Retrieved {len(templates)} query templates"
    }
