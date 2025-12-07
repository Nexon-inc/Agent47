from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import json

from ..database import get_purity_database
from ..models import BusinessIdea, BusinessModel
from ..services.business_idea_generator_service import BusinessIdeaGeneratorService

router = APIRouter(prefix="/business-ideas", tags=["Business Idea Generator"])

class BusinessIdeaRequest(BaseModel):
    skills: List[str] = Field(..., description="List of skills")
    passions: List[str] = Field(..., description="List of passions")
    available_capital: float = Field(..., ge=0, description="Available capital")
    industry_preferences: List[str] = Field(..., description="Industry preferences")
    risk_tolerance: str = Field(..., description="Risk tolerance level")

class IdeaViabilityRequest(BaseModel):
    business_idea: str = Field(..., description="Business idea description")
    target_market: str = Field(..., description="Target market")
    competition_level: str = Field(..., description="Competition level")
    market_size: str = Field(..., description="Market size")

class IdeaRoadmapRequest(BaseModel):
    business_idea: str = Field(..., description="Business idea description")
    timeline_months: int = Field(..., ge=1, le=60, description="Timeline in months")
    budget_allocation: dict = Field(..., description="Budget allocation")
    milestones: List[str] = Field(..., description="Key milestones")

@router.post("/generate")
async def generate_business_ideas(
    request: BusinessIdeaRequest,
    db: AsyncSession = Depends(get_purity_database)
):
    """Generate tailored business ideas based on skills, passions, and capital"""
    try:
        service = BusinessIdeaGeneratorService()
        result = await service.generate_business_ideas(
            db=db,
            skills=request.skills,
            passions=request.passions,
            available_capital=request.available_capital,
            industry_preferences=request.industry_preferences,
            risk_tolerance=request.risk_tolerance
        )
        return {
            "status": "success",
            "data": result,
            "message": f"Generated {len(result.get('generated_ideas', []))} business ideas"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate business ideas: {str(e)}"
        )

@router.post("/analyze-viability")
async def analyze_idea_viability(
    request: IdeaViabilityRequest,
    db: AsyncSession = Depends(get_purity_database)
):
    """Analyze the viability of a business idea"""
    try:
        service = BusinessIdeaGeneratorService()
        result = await service.analyze_idea_viability(
            db=db,
            business_idea=request.business_idea,
            target_market=request.target_market,
            competition_level=request.competition_level,
            market_size=request.market_size
        )
        return {
            "status": "success",
            "data": result,
            "message": f"Viability analysis completed with score: {result.get('viability_score', 0)}"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze idea viability: {str(e)}"
        )

@router.post("/create-roadmap")
async def create_idea_roadmap(
    request: IdeaRoadmapRequest,
    db: AsyncSession = Depends(get_purity_database)
):
    """Create a roadmap for implementing a business idea"""
    try:
        service = BusinessIdeaGeneratorService()
        result = await service.create_idea_roadmap(
            db=db,
            business_idea=request.business_idea,
            timeline_months=request.timeline_months,
            budget_allocation=request.budget_allocation,
            milestones=request.milestones
        )
        return {
            "status": "success",
            "data": result,
            "message": f"Roadmap created for {request.timeline_months} month timeline"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create idea roadmap: {str(e)}"
        )

@router.get("/trends")
async def get_business_trends(
    db: AsyncSession = Depends(get_purity_database)
):
    """Get current business trends and opportunities"""
    try:
        service = BusinessIdeaGeneratorService()
        # This would typically fetch from a trends database or external API
        trends = {
            "emerging_industries": [
                "Artificial Intelligence and Machine Learning",
                "Sustainable Technology",
                "Digital Health",
                "E-commerce and D2C",
                "Remote Work Solutions"
            ],
            "high_growth_sectors": [
                "Fintech",
                "EdTech",
                "Clean Energy",
                "Cybersecurity",
                "Food Technology"
            ],
            "market_opportunities": [
                "Aging population services",
                "Mental health solutions",
                "Local business digitization",
                "Personalized learning",
                "Sustainable consumer products"
            ]
        }
        return {
            "status": "success",
            "data": trends,
            "message": "Business trends retrieved successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve business trends: {str(e)}"
        )
