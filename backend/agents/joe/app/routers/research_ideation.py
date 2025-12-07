from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List
from pydantic import BaseModel, Field

from ..database import get_joe_database
from ..services.research_ideation_service import ResearchIdeationService

router = APIRouter(prefix="/research-ideation", tags=["Research Ideation"])

class TopicGenerationRequest(BaseModel):
    industry: str = Field(..., description="Industry or sector for research")
    research_goals: List[str] = Field(..., description="List of research goals")
    constraints: Dict[str, Any] = Field(default={}, description="Research constraints")

class TopicViabilityRequest(BaseModel):
    topic_id: str = Field(..., description="ID of the topic to analyze")
    analysis_criteria: Dict[str, Any] = Field(..., description="Criteria for viability analysis")

# Dependency
async def get_research_ideation_service() -> ResearchIdeationService:
    service = ResearchIdeationService()
    await service.initialize()
    return service

@router.post("/generate-topics")
async def generate_research_topics(
    request: TopicGenerationRequest,
    service: ResearchIdeationService = Depends(get_research_ideation_service)
):
    """Generate research topics based on industry and goals"""
    try:
        result = await service.generate_research_topics(
            user_id=1,  # TODO: Get from authentication
            industry=request.industry,
            research_goals=request.research_goals,
            constraints=request.constraints
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["topics_data"],
                "message": "Research topics generated successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Topic generation failed: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate research topics: {str(e)}"
        )

@router.post("/analyze-viability")
async def analyze_topic_viability(
    request: TopicViabilityRequest,
    service: ResearchIdeationService = Depends(get_research_ideation_service)
):
    """Analyze the viability of a specific research topic"""
    try:
        result = await service.analyze_topic_viability(
            user_id=1,  # TODO: Get from authentication
            topic_id=request.topic_id,
            analysis_criteria=request.analysis_criteria
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["viability_data"],
                "message": "Topic viability analyzed successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Viability analysis failed: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze topic viability: {str(e)}"
        )

@router.get("/ideation-templates")
async def get_ideation_templates(service: ResearchIdeationService = Depends(get_research_ideation_service)):
    """Get research ideation templates and frameworks"""
    ideation_templates = [
        {
            "template_id": "swot_analysis",
            "name": "SWOT Analysis Framework",
            "description": "Strengths, Weaknesses, Opportunities, Threats analysis for research planning",
            "sections": ["Strengths", "Weaknesses", "Opportunities", "Threats"],
            "best_for": "Strategic research planning"
        },
        {
            "template_id": "pestle_analysis",
            "name": "PESTLE Analysis",
            "description": "Political, Economic, Social, Technological, Legal, Environmental factors",
            "sections": ["Political", "Economic", "Social", "Technological", "Legal", "Environmental"],
            "best_for": "Macro-environmental research"
        },
        {
            "template_id": "research_funnel",
            "name": "Research Funnel",
            "description": "Broad to specific research topic refinement process",
            "sections": ["Awareness", "Interest", "Consideration", "Intent", "Action"],
            "best_for": "Topic refinement and validation"
        },
        {
            "template_id": "innovation_matrix",
            "name": "Innovation Matrix",
            "description": "Evaluate research ideas based on novelty and market impact",
            "sections": ["Incremental", "Breakthrough", "Disruptive", "Radical"],
            "best_for": "Innovation-focused research"
        }
    ]
    
    return {
        "status": "success",
        "data": ideation_templates,
        "message": f"Retrieved {len(ideation_templates)} ideation templates"
    }
