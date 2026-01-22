from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List
from pydantic import BaseModel, Field

from ..database import get_joe_database
from ..services.survey_creation_service import SurveyCreationService

router = APIRouter(prefix="/survey-creation", tags=["JoeSurvey Creation"])

class SurveyRequest(BaseModel):
    survey_type: str = Field(..., description="Type of survey to create")
    target_audience: str = Field(..., description="Target audience for survey")
    questions: List[Dict[str, Any]] = Field(default=[], description="JoeSurvey questions")

# Dependency
async def get_survey_creation_service() -> SurveyCreationService:
    service = SurveyCreationService()
    await service.initialize()
    return service

@router.post("/create")
async def create_survey(
    request: SurveyRequest,
    service: SurveyCreationService = Depends(get_survey_creation_service)
):
    """Create a new survey"""
    try:
        result = await service.create_survey(
            user_id=1,  # TODO: Get from authentication
            survey_type=request.survey_type,
            target_audience=request.target_audience,
            questions=request.questions
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["survey_data"],
                "message": f"JoeSurvey created for {request.target_audience}"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"JoeSurvey creation failed: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create survey: {str(e)}"
        )

@router.get("/responses/{survey_id}")
async def get_survey_responses(
    survey_id: int,
    service: SurveyCreationService = Depends(get_survey_creation_service)
):
    """Get responses for a survey"""
    try:
        result = await service.get_survey_responses(
            user_id=1,  # TODO: Get from authentication
            survey_id=survey_id
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["responses"],
                "message": f"Retrieved {result['total_responses']} survey responses"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get survey responses: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get survey responses: {str(e)}"
        )

@router.get("/templates")
async def get_survey_templates(service: SurveyCreationService = Depends(get_survey_creation_service)):
    """Get survey templates"""
    templates = [
        {
            "id": "customer_satisfaction",
            "name": "Customer Satisfaction JoeSurvey",
            "description": "Measure customer satisfaction and loyalty",
            "question_count": 10,
            "estimated_time": "5 minutes"
        },
        {
            "id": "market_research",
            "name": "Market Research JoeSurvey",
            "description": "Gather market insights and preferences",
            "question_count": 15,
            "estimated_time": "8 minutes"
        },
        {
            "id": "product_feedback",
            "name": "Product Feedback JoeSurvey",
            "description": "Collect product improvement suggestions",
            "question_count": 12,
            "estimated_time": "6 minutes"
        },
        {
            "id": "employee_engagement",
            "name": "Employee Engagement JoeSurvey",
            "description": "Measure employee satisfaction and engagement",
            "question_count": 20,
            "estimated_time": "10 minutes"
        }
    ]
    
    return {
        "status": "success",
        "data": templates,
        "message": f"Retrieved {len(templates)} survey templates"
    }
