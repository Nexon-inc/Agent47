from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List
from pydantic import BaseModel, Field

from ..database import get_joe_database
from ..services.onboarding_wizard_service import OnboardingWizardService

router = APIRouter(prefix="/onboarding-wizard", tags=["Onboarding Wizard"])

class OnboardingStartRequest(BaseModel):
    user_profile: Dict[str, Any] = Field(..., description="User profile information")

class StepCompletionRequest(BaseModel):
    step_id: int = Field(..., description="ID of the step to complete")
    step_data: Dict[str, Any] = Field(..., description="Data for step completion")

# Dependency
async def get_onboarding_wizard_service() -> OnboardingWizardService:
    service = OnboardingWizardService()
    await service.initialize()
    return service

@router.post("/start")
async def start_onboarding(
    request: OnboardingStartRequest,
    service: OnboardingWizardService = Depends(get_onboarding_wizard_service)
):
    """Start the onboarding process for a new user"""
    try:
        result = await service.start_onboarding(
            user_id=1,  # TODO: Get from authentication
            user_profile=request.user_profile
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["onboarding_data"],
                "message": "Onboarding process started successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Onboarding start failed: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start onboarding: {str(e)}"
        )

@router.post("/complete-step")
async def complete_onboarding_step(
    request: StepCompletionRequest,
    service: OnboardingWizardService = Depends(get_onboarding_wizard_service)
):
    """Complete a specific onboarding step"""
    try:
        result = await service.complete_onboarding_step(
            user_id=1,  # TODO: Get from authentication
            step_id=request.step_id,
            step_data=request.step_data
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["step_completion_data"],
                "message": f"Onboarding step {request.step_id} completed successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Step completion failed: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete onboarding step: {str(e)}"
        )

@router.get("/onboarding-steps")
async def get_onboarding_steps(service: OnboardingWizardService = Depends(get_onboarding_wizard_service)):
    """Get available onboarding steps and their details"""
    onboarding_steps = [
        {
            "step_id": 1,
            "title": "Welcome & Introduction",
            "description": "Get acquainted with the research platform",
            "duration": "2-3 minutes",
            "required": True,
            "features": ["Platform overview", "Key benefits", "Getting started guide"]
        },
        {
            "step_id": 2,
            "title": "Profile Setup",
            "description": "Configure your research preferences and settings",
            "duration": "5-7 minutes",
            "required": True,
            "features": ["Research interests", "Industry focus", "Notification preferences"]
        },
        {
            "step_id": 3,
            "title": "First Project",
            "description": "Create your first research project",
            "duration": "8-10 minutes",
            "required": True,
            "features": ["Project creation", "Basic setup", "Template selection"]
        },
        {
            "step_id": 4,
            "title": "Tool Familiarization",
            "description": "Learn key platform features and tools",
            "duration": "10-12 minutes",
            "required": False,
            "features": ["Feature walkthrough", "Interactive tutorials", "Best practices"]
        },
        {
            "step_id": 5,
            "title": "Completion & Next Steps",
            "description": "Finish setup and plan your research journey",
            "duration": "3-5 minutes",
            "required": True,
            "features": ["Setup completion", "Resource recommendations", "Support information"]
        }
    ]
    
    return {
        "status": "success",
        "data": onboarding_steps,
        "message": f"Retrieved {len(onboarding_steps)} onboarding steps"
    }
