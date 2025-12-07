from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import json

from ..database import get_purity_database
from ..models import MVPBlueprint, BusinessIdea
from ..services.mvp_builder_service import MVPBuilderService

router = APIRouter(prefix="/mvp-builder", tags=["MVP Builder"])

class MVPBlueprintRequest(BaseModel):
    business_idea: str = Field(..., description="Business idea description")
    target_market: str = Field(..., description="Target market")
    budget_constraints: Dict[str, Any] = Field(..., description="Budget constraints")
    timeline: str = Field(..., description="Development timeline")
    technical_requirements: List[str] = Field(..., description="Technical requirements")

@router.post("/create-blueprint")
async def create_mvp_blueprint(
    request: MVPBlueprintRequest,
    db: AsyncSession = Depends(get_purity_database)
):
    """Create an MVP blueprint with prioritized features and development plan"""
    try:
        service = MVPBuilderService()
        result = await service.create_mvp_blueprint(
            db=db,
            business_idea=request.business_idea,
            target_market=request.target_market,
            budget_constraints=request.budget_constraints,
            timeline=request.timeline,
            technical_requirements=request.technical_requirements
        )
        return {
            "status": "success",
            "data": result,
            "message": f"MVP blueprint created with score: {result.get('blueprint_score', 0)}"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create MVP blueprint: {str(e)}"
        )

@router.get("/templates")
async def get_mvp_templates(db: AsyncSession = Depends(get_purity_database)):
    """Get MVP templates and examples"""
    templates = {
        "saas_mvp": {"core_features": ["User registration", "Basic dashboard"], "timeline": "8-12 weeks"},
        "ecommerce_mvp": {"core_features": ["Product catalog", "Shopping cart"], "timeline": "4-8 weeks"},
        "mobile_app_mvp": {"core_features": ["User authentication", "Core functionality"], "timeline": "12-16 weeks"}
    }
    return {"status": "success", "data": templates, "message": "MVP templates retrieved successfully"}

class MVPBlueprintRequest(BaseModel):
    business_idea: str = Field(..., description="Business idea description")
    target_market: str = Field(..., description="Target market")
    budget_constraints: Dict[str, Any] = Field(..., description="Budget constraints")
    timeline: str = Field(..., description="Development timeline")
    technical_requirements: List[str] = Field(..., description="Technical requirements")

class FeaturePrioritizationRequest(BaseModel):
    mvp_blueprint_id: str = Field(..., description="MVP blueprint ID")
    user_feedback: Dict[str, Any] = Field(..., description="User feedback")
    market_validation: Dict[str, Any] = Field(..., description="Market validation data")

class DevelopmentToolsRequest(BaseModel):
    mvp_blueprint_id: str = Field(..., description="MVP blueprint ID")
    team_expertise: List[str] = Field(..., description="Team expertise")
    budget_constraints: Dict[str, Any] = Field(..., description="Budget constraints")

class MVPValidationRequest(BaseModel):
    mvp_blueprint_id: str = Field(..., description="MVP blueprint ID")
    validation_criteria: Dict[str, Any] = Field(..., description="Validation criteria")

@router.post("/create-blueprint")
async def create_mvp_blueprint(
    request: MVPBlueprintRequest,
    db: AsyncSession = Depends(get_purity_database)
):
    """Create an MVP blueprint with prioritized features and development plan"""
    try:
        service = MVPBuilderService()
        result = await service.create_mvp_blueprint(
            db=db,
            business_idea=request.business_idea,
            target_market=request.target_market,
            budget_constraints=request.budget_constraints,
            timeline=request.timeline,
            technical_requirements=request.technical_requirements
        )
        return {
            "status": "success",
            "data": result,
            "message": f"MVP blueprint created with score: {result.get('blueprint_score', 0)}"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create MVP blueprint: {str(e)}"
        )

@router.post("/prioritize-features")
async def prioritize_features(
    request: FeaturePrioritizationRequest,
    db: AsyncSession = Depends(get_purity_database)
):
    """Prioritize features based on user feedback and market validation"""
    try:
        service = MVPBuilderService()
        result = await service.prioritize_features(
            db=db,
            mvp_blueprint_id=request.mvp_blueprint_id,
            user_feedback=request.user_feedback,
            market_validation=request.market_validation
        )
        return {
            "status": "success",
            "data": result,
            "message": f"Features prioritized with score: {result.get('prioritization_score', 0)}"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to prioritize features: {str(e)}"
        )

@router.post("/recommend-tools")
async def recommend_development_tools(
    request: DevelopmentToolsRequest,
    db: AsyncSession = Depends(get_purity_database)
):
    """Recommend development tools based on requirements and team expertise"""
    try:
        service = MVPBuilderService()
        result = await service.recommend_development_tools(
            db=db,
            mvp_blueprint_id=request.mvp_blueprint_id,
            team_expertise=request.team_expertise,
            budget_constraints=request.budget_constraints
        )
        return {
            "status": "success",
            "data": result,
            "message": f"Development tools recommended with score: {result.get('recommendation_score', 0)}"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to recommend development tools: {str(e)}"
        )

@router.post("/validate-blueprint")
async def validate_mvp_blueprint(
    request: MVPValidationRequest,
    db: AsyncSession = Depends(get_purity_database)
):
    """Validate MVP blueprint against criteria"""
    try:
        service = MVPBuilderService()
        result = await service.validate_mvp_blueprint(
            db=db,
            mvp_blueprint_id=request.mvp_blueprint_id,
            validation_criteria=request.validation_criteria
        )
        return {
            "status": "success",
            "data": result,
            "message": f"MVP blueprint validated with score: {result.get('overall_score', 0)}"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate MVP blueprint: {str(e)}"
        )

@router.get("/mvp-templates")
async def get_mvp_templates(
    db: AsyncSession = Depends(get_purity_database)
):
    """Get MVP templates and examples"""
    try:
        templates = {
            "saas_mvp": {
                "core_features": ["User registration", "Basic dashboard", "Payment integration"],
                "nice_to_have": ["Advanced analytics", "API access", "White-label options"],
                "technical_stack": ["React", "Node.js", "PostgreSQL", "Stripe"],
                "timeline": "8-12 weeks",
                "estimated_cost": "$25,000-$40,000"
            },
            "ecommerce_mvp": {
                "core_features": ["Product catalog", "Shopping cart", "Payment processing"],
                "nice_to_have": ["Inventory management", "Customer reviews", "Email marketing"],
                "technical_stack": ["Shopify/WooCommerce", "Payment gateway", "Email service"],
                "timeline": "4-8 weeks",
                "estimated_cost": "$5,000-$15,000"
            },
            "mobile_app_mvp": {
                "core_features": ["User authentication", "Core functionality", "Push notifications"],
                "nice_to_have": ["Offline mode", "Social features", "Analytics"],
                "technical_stack": ["React Native", "Firebase", "App Store/Play Store"],
                "timeline": "12-16 weeks",
                "estimated_cost": "$30,000-$50,000"
            }
        }
        return {
            "status": "success",
            "data": templates,
            "message": "MVP templates retrieved successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve MVP templates: {str(e)}"
        )

@router.get("/development-phases")
async def get_development_phases(
    db: AsyncSession = Depends(get_purity_database)
):
    """Get development phases and best practices"""
    try:
        phases = {
            "phase_1_planning": {
                "duration": "1-2 weeks",
                "activities": ["Requirements gathering", "User research", "Technical planning"],
                "deliverables": ["Product requirements document", "User stories", "Technical architecture"]
            },
            "phase_2_design": {
                "duration": "2-3 weeks",
                "activities": ["UI/UX design", "Prototyping", "User testing"],
                "deliverables": ["Design mockups", "Interactive prototype", "User feedback"]
            },
            "phase_3_development": {
                "duration": "6-10 weeks",
                "activities": ["Core development", "Testing", "Integration"],
                "deliverables": ["Working MVP", "Test results", "Documentation"]
            },
            "phase_4_launch": {
                "duration": "1-2 weeks",
                "activities": ["Deployment", "User onboarding", "Monitoring"],
                "deliverables": ["Live MVP", "User guides", "Analytics setup"]
            }
        }
        return {
            "status": "success",
            "data": phases,
            "message": "Development phases retrieved successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve development phases: {str(e)}"
        )

@router.get("/success-metrics")
async def get_success_metrics(
    db: AsyncSession = Depends(get_purity_database)
):
    """Get MVP success metrics and KPIs"""
    try:
        metrics = {
            "user_metrics": [
                "User registration rate",
                "Daily/Monthly active users",
                "User retention rate",
                "Time spent in app"
            ],
            "business_metrics": [
                "Conversion rate",
                "Revenue per user",
                "Customer acquisition cost",
                "Customer lifetime value"
            ],
            "product_metrics": [
                "Feature adoption rate",
                "User engagement score",
                "Support ticket volume",
                "App store ratings"
            ],
            "technical_metrics": [
                "App performance",
                "Crash rate",
                "Load times",
                "API response times"
            ]
        }
        return {
            "status": "success",
            "data": metrics,
            "message": "Success metrics retrieved successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve success metrics: {str(e)}"
        )
