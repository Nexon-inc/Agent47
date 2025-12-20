from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import logging
from datetime import datetime

from ..services.onboarding_wizard_service import OnboardingWizardService, OnboardingStep, OnboardingSession
from ..database import get_eric_database
from core.cache.redis_manager import RedisManager

router = APIRouter(prefix="/onboarding-wizard", tags=["Onboarding Wizard"])
onboarding_service = OnboardingWizardService()
redis_manager = RedisManager()

logger = logging.getLogger(__name__)

# Request/Response Models
class OnboardingSessionCreate(BaseModel):
    user_id: str

class StepDataUpdate(BaseModel):
    step_number: int
    user_data: Dict[str, Any]

class StepCompletion(BaseModel):
    step_number: int

class StepNavigation(BaseModel):
    step_number: int

class OnboardingPreferences(BaseModel):
    preferences: Dict[str, Any]

# Session Management Endpoints
@router.post("/sessions", response_model=OnboardingSession, summary="Create Onboarding Session")
async def create_onboarding_session(session_data: OnboardingSessionCreate):
    """Create a new onboarding session for a user"""
    try:
        session = await onboarding_service.create_onboarding_session(session_data.user_id)
        return session
    except Exception as e:
        logger.error(f"Failed to create onboarding session: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/sessions/{session_token}", response_model=OnboardingSession, summary="Get Onboarding Session")
async def get_onboarding_session(session_token: str):
    """Get an onboarding session by token"""
    try:
        session = await onboarding_service.get_onboarding_session(session_token)
        if not session:
            raise HTTPException(status_code=404, detail="Onboarding session not found")
        return session
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get onboarding session: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Step Management Endpoints
@router.get("/sessions/{session_token}/current-step", response_model=OnboardingStep, summary="Get Current Step")
async def get_current_step(session_token: str):
    """Get the current step for an onboarding session"""
    try:
        step = await onboarding_service.get_current_step(session_token)
        return step
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get current step: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/sessions/{session_token}/steps", response_model=List[OnboardingStep], summary="Get All Steps")
async def get_all_steps(session_token: str):
    """Get all onboarding steps with completion status"""
    try:
        steps = await onboarding_service.get_all_steps(session_token)
        return steps
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get all steps: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/sessions/{session_token}/steps/{step_number}/data", summary="Update Step Data")
async def update_step_data(session_token: str, step_number: int, step_data: StepDataUpdate):
    """Update user data for a specific step"""
    try:
        success = await onboarding_service.update_step_data(session_token, step_number, step_data.user_data)
        if success:
            return {"message": "Step data updated successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to update step data")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update step data: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/sessions/{session_token}/steps/{step_number}/complete", summary="Complete Step")
async def complete_step(session_token: str, step_number: int):
    """Mark a step as completed and move to next step"""
    try:
        success = await onboarding_service.complete_step(session_token, step_number)
        if success:
            return {"message": "Step completed successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to complete step")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to complete step: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/sessions/{session_token}/steps/{step_number}/navigate", summary="Navigate to Step")
async def navigate_to_step(session_token: str, step_number: int):
    """Navigate to a specific step"""
    try:
        success = await onboarding_service.go_to_step(session_token, step_number)
        if success:
            return {"message": f"Navigated to step {step_number}"}
        else:
            raise HTTPException(status_code=400, detail="Failed to navigate to step")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to navigate to step: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Progress and Analytics Endpoints
@router.get("/sessions/{session_token}/progress", summary="Get Onboarding Progress")
async def get_onboarding_progress(session_token: str):
    """Get detailed onboarding progress information"""
    try:
        progress = await onboarding_service.get_onboarding_progress(session_token)
        return progress
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get onboarding progress: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/sessions/{session_token}/summary", summary="Get Onboarding Summary")
async def get_onboarding_summary(session_token: str):
    """Get a summary of the completed onboarding"""
    try:
        summary = await onboarding_service.get_onboarding_summary(session_token)
        return summary
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get onboarding summary: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Help and Support Endpoints
@router.get("/steps/{step_number}/help", summary="Get Step Help")
async def get_step_help(step_number: int):
    """Get detailed help information for a specific step"""
    try:
        help_content = await onboarding_service.get_step_help(step_number)
        return help_content
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get step help: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Preferences Management Endpoints
@router.post("/sessions/{session_token}/preferences", summary="Save Onboarding Preferences")
async def save_onboarding_preferences(session_token: str, preferences: OnboardingPreferences):
    """Save user preferences from onboarding"""
    try:
        success = await onboarding_service.save_onboarding_preferences(session_token, preferences.preferences)
        if success:
            return {"message": "Preferences saved successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to save preferences")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to save preferences: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Analytics and Reporting Endpoints
@router.get("/analytics/sessions", summary="Get Onboarding Analytics")
async def get_onboarding_analytics():
    """Get analytics for onboarding sessions"""
    try:
        # This would typically aggregate data from multiple sessions
        analytics = {
            "total_sessions": 0,
            "completed_sessions": 0,
            "average_completion_time": 0,
            "step_completion_rates": {},
            "common_issues": [],
            "user_feedback": []
        }
        return analytics
    except Exception as e:
        logger.error(f"Failed to get onboarding analytics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/analytics/steps/{step_number}", summary="Get Step Analytics")
async def get_step_analytics(step_number: int):
    """Get analytics for a specific step"""
    try:
        analytics = {
            "step_number": step_number,
            "completion_rate": 0.0,
            "average_time": 0,
            "common_errors": [],
            "user_feedback": []
        }
        return analytics
    except Exception as e:
        logger.error(f"Failed to get step analytics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Utility Endpoints
@router.get("/steps", summary="Get All Step Definitions")
async def get_step_definitions():
    """Get all step definitions for reference"""
    try:
        steps = onboarding_service.onboarding_steps
        return {
            "steps": steps,
            "total_steps": len(steps),
            "step_types": list(set(step["step_type"] for step in steps))
        }
    except Exception as e:
        logger.error(f"Failed to get step definitions: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/validation-rules", summary="Get Validation Rules")
async def get_validation_rules():
    """Get validation rules for all steps"""
    try:
        validation_rules = {}
        for step in onboarding_service.onboarding_steps:
            validation_rules[step["step_number"]] = {
                "required_fields": step.get("required_fields", []),
                "optional_fields": step.get("optional_fields", []),
                "validation_rules": step.get("validation_rules", {})
            }
        return validation_rules
    except Exception as e:
        logger.error(f"Failed to get validation rules: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/estimated-times", summary="Get Estimated Times")
async def get_estimated_times():
    """Get estimated completion times for all steps"""
    try:
        times = {}
        total_time = 0
        for step in onboarding_service.onboarding_steps:
            times[step["step_number"]] = {
                "step_name": step["step_name"],
                "estimated_time": step.get("estimated_time", 5)
            }
            total_time += step.get("estimated_time", 5)
        
        return {
            "step_times": times,
            "total_estimated_time": total_time,
            "average_time_per_step": total_time / len(times) if times else 0
        }
    except Exception as e:
        logger.error(f"Failed to get estimated times: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Health Check Endpoint
@router.get("/health", summary="Onboarding Wizard Health Check")
async def health_check():
    """Check the health of the onboarding wizard service"""
    try:
        return {
            "status": "healthy",
            "service": "Onboarding Wizard",
            "timestamp": datetime.utcnow().isoformat(),
            "features": [
                "Step-by-Step Guidance",
                "Progress Tracking",
                "Data Validation",
                "Help and Support",
                "Analytics and Reporting"
            ],
            "total_steps": len(onboarding_service.onboarding_steps)
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Service unhealthy")
