from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime
from ..services.business_intelligence_service import BusinessIntelligenceService
from ..models import PurityBusinessIdea, IndustryType, ValidationStatus
from ..database import get_purity_database

router = APIRouter()

# Pydantic models for request/response
class IdeaGenerationRequest(BaseModel):
    skills: List[str]
    interests: List[str]
    budget_range: str
    industry_preference: Optional[IndustryType] = None
    market_trends: Optional[List[str]] = None
    location: Optional[str] = None

class IdeaValidationRequest(BaseModel):
    validation_criteria: Optional[Dict[str, Any]] = None

class BusinessModelCanvasRequest(BaseModel):
    canvas_data: Optional[Dict[str, Any]] = None

class CustomerAvatarRequest(BaseModel):
    avatar_data: Optional[Dict[str, Any]] = None

class BusinessIdeaResponse(BaseModel):
    id: int
    title: str
    description: str
    industry: IndustryType
    target_market: Optional[str]
    unique_value_proposition: Optional[str]
    revenue_potential: Optional[float]
    startup_cost: Optional[float]
    time_to_market: Optional[int]
    competition_level: Optional[str]
    market_size: Optional[str]
    validation_score: Optional[float]
    status: ValidationStatus
    tags: List[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

@router.post("/ideas/generate", response_model=Dict[str, Any])
async def generate_business_ideas(
    request: IdeaGenerationRequest,
    user_id: int = Query(..., description="User ID")
):
    """Generate AI-powered business ideas based on user inputs"""
    try:
        service = BusinessIntelligenceService()
        await service.initialize()
        
        result = await service.generate_business_ideas(
            user_id=user_id,
            skills=request.skills,
            interests=request.interests,
            budget_range=request.budget_range,
            industry_preference=request.industry_preference,
            market_trends=request.market_trends,
            location=request.location
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "success": True,
            "ideas": [
                {
                    "id": idea.id,
                    "title": idea.title,
                    "description": idea.description,
                    "industry": idea.industry.value,
                    "target_market": idea.target_market,
                    "unique_value_proposition": idea.unique_value_proposition,
                    "revenue_potential": idea.revenue_potential,
                    "startup_cost": idea.startup_cost,
                    "time_to_market": idea.time_to_market,
                    "competition_level": idea.competition_level,
                    "market_size": idea.market_size,
                    "validation_score": idea.validation_score,
                    "status": idea.status.value,
                    "tags": idea.tags,
                    "created_at": idea.created_at.isoformat(),
                    "updated_at": idea.updated_at.isoformat() if idea.updated_at else None
                }
                for idea in result["ideas"]
            ],
            "total_generated": result["total_generated"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate business ideas: {str(e)}")

@router.post("/ideas/{idea_id}/validate", response_model=Dict[str, Any])
async def validate_business_idea(
    idea_id: int,
    request: IdeaValidationRequest
):
    """Validate a business idea using AI and market data"""
    try:
        service = BusinessIntelligenceService()
        await service.initialize()
        
        result = await service.validate_business_idea(
            idea_id=idea_id,
            validation_criteria=request.validation_criteria
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "success": True,
            "validation_result": result["validation_result"],
            "idea": {
                "id": result["idea"].id,
                "title": result["idea"].title,
                "validation_score": result["idea"].validation_score,
                "status": result["idea"].status.value,
                "updated_at": result["idea"].updated_at.isoformat() if result["idea"].updated_at else None
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to validate business idea: {str(e)}")

@router.post("/ideas/{idea_id}/business-model-canvas", response_model=Dict[str, Any])
async def create_business_model_canvas(
    idea_id: int,
    request: BusinessModelCanvasRequest
):
    """Create a complete business model canvas using AI"""
    try:
        service = BusinessIntelligenceService()
        await service.initialize()
        
        result = await service.create_business_model_canvas(
            idea_id=idea_id,
            canvas_data=request.canvas_data
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "success": True,
            "business_model": {
                "id": result["business_model"].id,
                "idea_id": result["business_model"].idea_id,
                "key_partners": result["business_model"].key_partners,
                "key_activities": result["business_model"].key_activities,
                "key_resources": result["business_model"].key_resources,
                "value_propositions": result["business_model"].value_propositions,
                "customer_relationships": result["business_model"].customer_relationships,
                "channels": result["business_model"].channels,
                "customer_segments": result["business_model"].customer_segments,
                "cost_structure": result["business_model"].cost_structure,
                "revenue_streams": result["business_model"].revenue_streams,
                "revenue_model": result["business_model"].revenue_model.value if result["business_model"].revenue_model else None,
                "pricing_strategy": result["business_model"].pricing_strategy,
                "competitive_advantage": result["business_model"].competitive_advantage,
                "scalability_factors": result["business_model"].scalability_factors,
                "risk_factors": result["business_model"].risk_factors,
                "created_at": result["business_model"].created_at.isoformat(),
                "updated_at": result["business_model"].updated_at.isoformat() if result["business_model"].updated_at else None
            },
            "canvas_data": result["canvas_data"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create business model canvas: {str(e)}")

@router.post("/ideas/{idea_id}/customer-avatar", response_model=Dict[str, Any])
async def build_customer_avatar(
    idea_id: int,
    request: CustomerAvatarRequest
):
    """Build detailed customer personas using AI"""
    try:
        service = BusinessIntelligenceService()
        await service.initialize()
        
        result = await service.build_customer_avatar(
            idea_id=idea_id,
            avatar_data=request.avatar_data
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "success": True,
            "customer_avatars": [
                {
                    "id": avatar.id,
                    "idea_id": avatar.idea_id,
                    "name": avatar.name,
                    "age_range": avatar.age_range,
                    "gender": avatar.gender,
                    "income_level": avatar.income_level,
                    "education_level": avatar.education_level,
                    "occupation": avatar.occupation,
                    "location": avatar.location,
                    "interests": avatar.interests,
                    "pain_points": avatar.pain_points,
                    "goals": avatar.goals,
                    "buying_behavior": avatar.buying_behavior,
                    "preferred_channels": avatar.preferred_channels,
                    "decision_factors": avatar.decision_factors,
                    "objections": avatar.objections,
                    "created_at": avatar.created_at.isoformat(),
                    "updated_at": avatar.updated_at.isoformat() if avatar.updated_at else None
                }
                for avatar in result["customer_avatars"]
            ],
            "total_avatars": result["total_avatars"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to build customer avatar: {str(e)}")

@router.get("/ideas", response_model=List[BusinessIdeaResponse])
async def get_business_ideas(
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    industry: Optional[IndustryType] = Query(None, description="Filter by industry"),
    status: Optional[ValidationStatus] = Query(None, description="Filter by validation status"),
    limit: int = Query(10, description="Number of ideas to return"),
    offset: int = Query(0, description="Number of ideas to skip")
):
    """Get business ideas with optional filtering"""
    try:
        db = await get_purity_database()
        async with db.get_session() as session:
            from sqlalchemy import select
            
            query = select(PurityBusinessIdea)
            
            if user_id:
                query = query.where(PurityBusinessIdea.user_id == user_id)
            if industry:
                query = query.where(PurityBusinessIdea.industry == industry)
            if status:
                query = query.where(PurityBusinessIdea.status == status)
            
            query = query.order_by(PurityBusinessIdea.created_at.desc())
            query = query.offset(offset).limit(limit)
            
            result = await session.execute(query)
            ideas = result.scalars().all()
            
            return [
                BusinessIdeaResponse(
                    id=idea.id,
                    title=idea.title,
                    description=idea.description,
                    industry=idea.industry,
                    target_market=idea.target_market,
                    unique_value_proposition=idea.unique_value_proposition,
                    revenue_potential=idea.revenue_potential,
                    startup_cost=idea.startup_cost,
                    time_to_market=idea.time_to_market,
                    competition_level=idea.competition_level,
                    market_size=idea.market_size,
                    validation_score=idea.validation_score,
                    status=idea.status,
                    tags=idea.tags,
                    created_at=idea.created_at,
                    updated_at=idea.updated_at
                )
                for idea in ideas
            ]
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get business ideas: {str(e)}")

@router.get("/ideas/{idea_id}", response_model=BusinessIdeaResponse)
async def get_business_idea(idea_id: int):
    """Get a specific business idea by ID"""
    try:
        db = await get_purity_database()
        async with db.get_session() as session:
            from sqlalchemy import select
            
            query = select(PurityBusinessIdea).where(PurityBusinessIdea.id == idea_id)
            result = await session.execute(query)
            idea = result.scalar_one_or_none()
            
            if not idea:
                raise HTTPException(status_code=404, detail="Business idea not found")
            
            return BusinessIdeaResponse(
                id=idea.id,
                title=idea.title,
                description=idea.description,
                industry=idea.industry,
                target_market=idea.target_market,
                unique_value_proposition=idea.unique_value_proposition,
                revenue_potential=idea.revenue_potential,
                startup_cost=idea.startup_cost,
                time_to_market=idea.time_to_market,
                competition_level=idea.competition_level,
                market_size=idea.market_size,
                validation_score=idea.validation_score,
                status=idea.status,
                tags=idea.tags,
                created_at=idea.created_at,
                updated_at=idea.updated_at
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get business idea: {str(e)}")

@router.put("/ideas/{idea_id}", response_model=BusinessIdeaResponse)
async def update_business_idea(
    idea_id: int,
    update_data: Dict[str, Any]
):
    """Update a business idea"""
    try:
        db = await get_purity_database()
        async with db.get_session() as session:
            from sqlalchemy import select, update
            
            # Check if idea exists
            query = select(PurityBusinessIdea).where(PurityBusinessIdea.id == idea_id)
            result = await session.execute(query)
            idea = result.scalar_one_or_none()
            
            if not idea:
                raise HTTPException(status_code=404, detail="Business idea not found")
            
            # Update fields
            allowed_fields = [
                "title", "description", "target_market", "unique_value_proposition",
                "revenue_potential", "startup_cost", "time_to_market", "competition_level",
                "market_size", "tags", "metadata"
            ]
            
            update_fields = {}
            for field, value in update_data.items():
                if field in allowed_fields:
                    update_fields[field] = value
            
            if update_fields:
                stmt = update(PurityBusinessIdea).where(PurityBusinessIdea.id == idea_id).values(**update_fields)
                await session.execute(stmt)
                await session.commit()
                
                # Get updated idea
                result = await session.execute(query)
                idea = result.scalar_one_or_none()
            
            return BusinessIdeaResponse(
                id=idea.id,
                title=idea.title,
                description=idea.description,
                industry=idea.industry,
                target_market=idea.target_market,
                unique_value_proposition=idea.unique_value_proposition,
                revenue_potential=idea.revenue_potential,
                startup_cost=idea.startup_cost,
                time_to_market=idea.time_to_market,
                competition_level=idea.competition_level,
                market_size=idea.market_size,
                validation_score=idea.validation_score,
                status=idea.status,
                tags=idea.tags,
                created_at=idea.created_at,
                updated_at=idea.updated_at
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update business idea: {str(e)}")

@router.delete("/ideas/{idea_id}")
async def delete_business_idea(idea_id: int):
    """Delete a business idea"""
    try:
        db = await get_purity_database()
        async with db.get_session() as session:
            from sqlalchemy import select, delete
            
            # Check if idea exists
            query = select(PurityBusinessIdea).where(PurityBusinessIdea.id == idea_id)
            result = await session.execute(query)
            idea = result.scalar_one_or_none()
            
            if not idea:
                raise HTTPException(status_code=404, detail="Business idea not found")
            
            # Delete idea
            stmt = delete(PurityBusinessIdea).where(PurityBusinessIdea.id == idea_id)
            await session.execute(stmt)
            await session.commit()
            
            return {"success": True, "message": "Business idea deleted successfully"}
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete business idea: {str(e)}")

@router.get("/ideas/{idea_id}/summary", response_model=Dict[str, Any])
async def get_business_idea_summary(idea_id: int):
    """Get a comprehensive summary of a business idea with all related data"""
    try:
        db = await get_purity_database()
        async with db.get_session() as session:
            from sqlalchemy import select
            from sqlalchemy.orm import selectinload
            
            # Get idea with all related data
            query = select(PurityBusinessIdea).options(
                selectinload(PurityBusinessIdea.business_models),
                selectinload(PurityBusinessIdea.market_research),
                selectinload(PurityBusinessIdea.customer_avatars)
            ).where(PurityBusinessIdea.id == idea_id)
            
            result = await session.execute(query)
            idea = result.scalar_one_or_none()
            
            if not idea:
                raise HTTPException(status_code=404, detail="Business idea not found")
            
            return {
                "success": True,
                "idea": {
                    "id": idea.id,
                    "title": idea.title,
                    "description": idea.description,
                    "industry": idea.industry.value,
                    "target_market": idea.target_market,
                    "unique_value_proposition": idea.unique_value_proposition,
                    "revenue_potential": idea.revenue_potential,
                    "startup_cost": idea.startup_cost,
                    "time_to_market": idea.time_to_market,
                    "competition_level": idea.competition_level,
                    "market_size": idea.market_size,
                    "validation_score": idea.validation_score,
                    "status": idea.status.value,
                    "tags": idea.tags,
                    "created_at": idea.created_at.isoformat(),
                    "updated_at": idea.updated_at.isoformat() if idea.updated_at else None
                },
                "business_models_count": len(idea.business_models),
                "market_research_count": len(idea.market_research),
                "customer_avatars_count": len(idea.customer_avatars),
                "summary": {
                    "total_related_data": len(idea.business_models) + len(idea.market_research) + len(idea.customer_avatars),
                    "completion_percentage": _calculate_completion_percentage(idea),
                    "next_steps": _get_next_steps(idea)
                }
            }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get business idea summary: {str(e)}")

def _calculate_completion_percentage(idea: PurityBusinessIdea) -> float:
    """Calculate completion percentage based on available data"""
    total_steps = 4
    completed_steps = 1  # Basic idea is always present
    
    if idea.business_models:
        completed_steps += 1
    if idea.market_research:
        completed_steps += 1
    if idea.customer_avatars:
        completed_steps += 1
    
    return (completed_steps / total_steps) * 100

def _get_next_steps(idea: PurityBusinessIdea) -> List[str]:
    """Get recommended next steps based on current data"""
    next_steps = []
    
    if not idea.business_models:
        next_steps.append("Create business model canvas")
    if not idea.market_research:
        next_steps.append("Conduct market research")
    if not idea.customer_avatars:
        next_steps.append("Build customer avatars")
    if idea.validation_score is None or idea.validation_score == 0:
        next_steps.append("Validate business idea")
    
    if not next_steps:
        next_steps.append("Proceed to financial planning")
        next_steps.append("Develop launch strategy")
    
    return next_steps
