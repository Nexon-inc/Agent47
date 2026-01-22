from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import json

from ..database import get_purity_database
from ..models import PurityCustomerAvatar, PurityBusinessIdea
from ..services.customer_avatar_service import CustomerAvatarService

router = APIRouter(prefix="/customer-avatar", tags=["Customer Avatar"])

class CustomerAvatarRequest(BaseModel):
    business_idea: str = Field(..., description="Business idea description")
    target_market: str = Field(..., description="Target market")
    demographics: Dict[str, Any] = Field(..., description="Demographic information")
    psychographics: Dict[str, Any] = Field(..., description="Psychographic information")
    pain_points: List[str] = Field(..., description="Customer pain points")
    goals: List[str] = Field(..., description="Customer goals")
    buying_behavior: Dict[str, Any] = Field(..., description="Buying behavior patterns")

class CustomerSegmentsRequest(BaseModel):
    business_idea: str = Field(..., description="Business idea description")
    market_data: Dict[str, Any] = Field(..., description="Market data")
    segmentation_criteria: List[str] = Field(..., description="Segmentation criteria")

class MarketingPersonasRequest(BaseModel):
    customer_avatar_id: str = Field(..., description="Customer avatar ID")
    marketing_channels: List[str] = Field(..., description="Marketing channels")
    campaign_objectives: List[str] = Field(..., description="Campaign objectives")

class AvatarValidationRequest(BaseModel):
    customer_avatar_id: str = Field(..., description="Customer avatar ID")
    validation_criteria: Dict[str, Any] = Field(..., description="Validation criteria")

@router.post("/create")
async def create_customer_avatar(
    request: CustomerAvatarRequest,
    db: AsyncSession = Depends(get_purity_database)
):
    """Create a detailed customer avatar for marketing and product development"""
    try:
        service = CustomerAvatarService()
        result = await service.create_customer_avatar(
            db=db,
            business_idea=request.business_idea,
            target_market=request.target_market,
            demographics=request.demographics,
            psychographics=request.psychographics,
            pain_points=request.pain_points,
            goals=request.goals,
            buying_behavior=request.buying_behavior
        )
        return {
            "status": "success",
            "data": result,
            "message": f"Customer avatar created with score: {result.get('avatar_score', 0)}"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create customer avatar: {str(e)}"
        )

@router.post("/analyze-segments")
async def analyze_customer_segments(
    request: CustomerSegmentsRequest,
    db: AsyncSession = Depends(get_purity_database)
):
    """Analyze customer segments for a business idea"""
    try:
        service = CustomerAvatarService()
        result = await service.analyze_customer_segments(
            db=db,
            business_idea=request.business_idea,
            market_data=request.market_data,
            segmentation_criteria=request.segmentation_criteria
        )
        return {
            "status": "success",
            "data": result,
            "message": f"Customer segments analyzed with score: {result.get('segmentation_score', 0)}"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze customer segments: {str(e)}"
        )

@router.post("/generate-marketing-personas")
async def generate_marketing_personas(
    request: MarketingPersonasRequest,
    db: AsyncSession = Depends(get_purity_database)
):
    """Generate marketing personas based on customer avatar"""
    try:
        service = CustomerAvatarService()
        result = await service.generate_marketing_personas(
            db=db,
            customer_avatar_id=request.customer_avatar_id,
            marketing_channels=request.marketing_channels,
            campaign_objectives=request.campaign_objectives
        )
        return {
            "status": "success",
            "data": result,
            "message": f"Marketing personas generated with score: {result.get('persona_score', 0)}"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate marketing personas: {str(e)}"
        )

@router.post("/validate")
async def validate_customer_avatar(
    request: AvatarValidationRequest,
    db: AsyncSession = Depends(get_purity_database)
):
    """Validate customer avatar against criteria"""
    try:
        service = CustomerAvatarService()
        result = await service.validate_customer_avatar(
            db=db,
            customer_avatar_id=request.customer_avatar_id,
            validation_criteria=request.validation_criteria
        )
        return {
            "status": "success",
            "data": result,
            "message": f"Customer avatar validated with score: {result.get('overall_score', 0)}"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate customer avatar: {str(e)}"
        )

@router.get("/avatar-templates")
async def get_avatar_templates(
    db: AsyncSession = Depends(get_purity_database)
):
    """Get customer avatar templates and examples"""
    try:
        templates = {
            "b2b_avatar": {
                "persona_name": "Sarah Johnson",
                "age_range": "28-35",
                "occupation": "Marketing Manager",
                "income_level": "$60K-$80K",
                "company_size": "50-200 employees",
                "pain_points": ["Limited time", "Budget constraints", "Need for ROI"],
                "goals": ["Increase efficiency", "Reduce costs", "Improve results"]
            },
            "b2c_avatar": {
                "persona_name": "Mike Chen",
                "age_range": "25-40",
                "occupation": "Freelancer",
                "income_level": "$40K-$70K",
                "lifestyle": "Digital nomad",
                "pain_points": ["Work-life balance", "Income stability", "Skill development"],
                "goals": ["Financial freedom", "Location independence", "Career growth"]
            },
            "startup_avatar": {
                "persona_name": "Alex Rodriguez",
                "age_range": "22-30",
                "occupation": "Founder/CEO",
                "income_level": "Variable",
                "company_stage": "Early stage",
                "pain_points": ["Limited resources", "Market validation", "Team building"],
                "goals": ["Product-market fit", "Funding", "Growth"]
            }
        }
        return {
            "status": "success",
            "data": templates,
            "message": "Avatar templates retrieved successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve avatar templates: {str(e)}"
        )

@router.get("/best-practices")
async def get_avatar_best_practices(
    db: AsyncSession = Depends(get_purity_database)
):
    """Get customer avatar creation best practices"""
    try:
        best_practices = {
            "research_methods": [
                "Customer interviews and surveys",
                "Social media analysis",
                "Competitor customer analysis",
                "Analytics data review",
                "Sales team feedback"
            ],
            "avatar_components": [
                "Demographics (age, location, income)",
                "Psychographics (values, interests, lifestyle)",
                "Pain points and challenges",
                "Goals and aspirations",
                "Buying behavior patterns",
                "Communication preferences"
            ],
            "validation_techniques": [
                "A/B testing with different personas",
                "Customer feedback collection",
                "Market research validation",
                "Sales performance analysis",
                "User behavior tracking"
            ],
            "common_mistakes": [
                "Creating too many personas",
                "Making assumptions without data",
                "Focusing only on demographics",
                "Not updating personas regularly",
                "Ignoring negative personas"
            ]
        }
        return {
            "status": "success",
            "data": best_practices,
            "message": "Avatar best practices retrieved successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve avatar best practices: {str(e)}"
        )
