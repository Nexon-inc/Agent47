"""
Hypothesis Testing Router

This router handles statistical hypothesis validation and testing endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List
from pydantic import BaseModel, Field

from ..database import get_joe_database
from ..services.hypothesis_testing_service import HypothesisTestingService

router = APIRouter(prefix="/hypothesis-testing", tags=["Hypothesis Testing"])

class HypothesisTestRequest(BaseModel):
    hypothesis_data: Dict[str, Any] = Field(..., description="Hypothesis data for testing")

class AssumptionValidationRequest(BaseModel):
    data_characteristics: Dict[str, Any] = Field(..., description="Data characteristics for assumption validation")

# Dependency
async def get_hypothesis_testing_service() -> HypothesisTestingService:
    service = HypothesisTestingService()
    await service.initialize()
    return service

@router.post("/test-hypothesis")
async def test_hypothesis(
    request: HypothesisTestRequest,
    service: HypothesisTestingService = Depends(get_hypothesis_testing_service)
):
    """Test a statistical hypothesis with provided data"""
    try:
        result = await service.test_hypothesis(
            user_id=1,  # TODO: Get from authentication
            hypothesis_data=request.hypothesis_data
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["test_data"],
                "message": "Hypothesis testing completed successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Hypothesis testing failed: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to test hypothesis: {str(e)}"
        )

@router.post("/validate-assumptions")
async def validate_statistical_assumptions(
    request: AssumptionValidationRequest,
    service: HypothesisTestingService = Depends(get_hypothesis_testing_service)
):
    """Validate statistical assumptions for hypothesis testing"""
    try:
        result = await service.validate_statistical_assumptions(
            user_id=1,  # TODO: Get from authentication
            data_characteristics=request.data_characteristics
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["validation_data"],
                "message": "Statistical assumptions validation completed"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Assumption validation failed: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate assumptions: {str(e)}"
        )

@router.get("/test-types")
async def get_available_test_types(service: HypothesisTestingService = Depends(get_hypothesis_testing_service)):
    """Get available statistical test types"""
    test_types = [
        {
            "id": "t_test",
            "name": "T-Test",
            "description": "Compare means between two groups",
            "assumptions": ["normality", "homogeneity", "independence"],
            "use_case": "Two-group comparisons"
        },
        {
            "id": "anova",
            "name": "ANOVA",
            "description": "Compare means across multiple groups",
            "assumptions": ["normality", "homogeneity", "independence"],
            "use_case": "Multi-group comparisons"
        },
        {
            "id": "chi_square",
            "name": "Chi-Square Test",
            "description": "Test independence between categorical variables",
            "assumptions": ["independence", "expected frequencies"],
            "use_case": "Categorical data analysis"
        },
        {
            "id": "correlation",
            "name": "Correlation Analysis",
            "description": "Measure relationship between variables",
            "assumptions": ["linearity", "normality", "homoscedasticity"],
            "use_case": "Relationship analysis"
        },
        {
            "id": "regression",
            "name": "Regression Analysis",
            "description": "Predict dependent variable from independent variables",
            "assumptions": ["linearity", "normality", "homoscedasticity", "independence"],
            "use_case": "Prediction modeling"
        }
    ]
    
    return {
        "status": "success",
        "data": test_types,
        "message": f"Retrieved {len(test_types)} statistical test types"
    }
