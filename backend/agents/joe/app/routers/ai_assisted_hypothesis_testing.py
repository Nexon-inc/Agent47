from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from ..database import get_joe_database
from ..services.ai_assisted_hypothesis_testing_service import AIAssistedHypothesisTestingService
from core.authentication.auth_manager import AuthManager

router = APIRouter(prefix="/ai-assisted-hypothesis-testing", tags=["AI-Assisted Hypothesis Testing"])

class HypothesisTestingRequest(BaseModel):
    hypothesis: Dict[str, Any] = Field(..., description="Business hypothesis to test")
    data_set: Dict[str, Any] = Field(..., description="Data set for hypothesis testing")
    test_parameters: Dict[str, Any] = Field(..., description="Parameters for statistical testing")

class InsightGenerationRequest(BaseModel):
    testing_results: Dict[str, Any] = Field(..., description="Results from hypothesis testing")
    business_context: Dict[str, Any] = Field(..., description="Business context for insight generation")

# Dependencies
async def get_ai_assisted_hypothesis_testing_service() -> AIAssistedHypothesisTestingService:
    service = AIAssistedHypothesisTestingService()
    await service.initialize()
    return service

async def get_current_user_id(authorization: Optional[str] = Header(None)) -> int:
    """Get current user ID from authentication token"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    try:
        # Extract token from "Bearer <token>" format
        token = authorization.replace("Bearer ", "")
        auth_manager = AuthManager()
        user_data = await auth_manager.verify_token(token)
        return user_data.get("user_id")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid authentication token: {str(e)}")

@router.post("/test-hypothesis")
async def test_hypothesis(
    request: HypothesisTestingRequest,
    service: AIAssistedHypothesisTestingService = Depends(get_ai_assisted_hypothesis_testing_service),
    user_id: int = Depends(get_current_user_id)
):
    """Test a business hypothesis using AI-assisted statistical analysis"""
    try:
        result = await service.test_hypothesis(
            user_id=user_id,
            hypothesis=request.hypothesis,
            data_set=request.data_set,
            test_parameters=request.test_parameters
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["testing_results"],
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

@router.post("/generate-insights")
async def generate_hypothesis_insights(
    request: InsightGenerationRequest,
    service: AIAssistedHypothesisTestingService = Depends(get_ai_assisted_hypothesis_testing_service),
    user_id: int = Depends(get_current_user_id)
):
    """Generate business insights from hypothesis testing results"""
    try:
        result = await service.generate_hypothesis_insights(
            user_id=user_id,
            testing_results=request.testing_results,
            business_context=request.business_context
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["insights_data"],
                "message": "Hypothesis insights generated successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Insight generation failed: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate hypothesis insights: {str(e)}"
        )

@router.get("/statistical-tests")
async def get_available_statistical_tests(service: AIAssistedHypothesisTestingService = Depends(get_ai_assisted_hypothesis_testing_service)):
    """Get available statistical tests for hypothesis testing"""
    statistical_tests = [
        {
            "test_id": "t_test",
            "name": "T-Test",
            "description": "Compare means between two groups",
            "use_case": "A/B testing, before/after comparisons",
            "assumptions": ["Normal distribution", "Equal variances", "Independent samples"],
            "outputs": ["t-statistic", "p-value", "confidence interval"]
        },
        {
            "test_id": "anova",
            "name": "ANOVA",
            "description": "Compare means across multiple groups",
            "use_case": "Multi-variant testing, group comparisons",
            "assumptions": ["Normal distribution", "Equal variances", "Independent samples"],
            "outputs": ["F-statistic", "p-value", "effect size"]
        },
        {
            "test_id": "chi_square",
            "name": "Chi-Square Test",
            "description": "Test independence between categorical variables",
            "use_case": "JoeSurvey analysis, categorical data relationships",
            "assumptions": ["Expected frequencies > 5", "Independent observations"],
            "outputs": ["Chi-square statistic", "p-value", "degrees of freedom"]
        },
        {
            "test_id": "correlation",
            "name": "Correlation Analysis",
            "description": "Measure relationship between continuous variables",
            "use_case": "Market research, trend analysis",
            "assumptions": ["Linear relationship", "Bivariate normal distribution"],
            "outputs": ["Correlation coefficient", "p-value", "R-squared"]
        },
        {
            "test_id": "regression",
            "name": "Regression Analysis",
            "description": "Predict dependent variable from independent variables",
            "use_case": "Forecasting, causal analysis",
            "assumptions": ["Linear relationship", "Normal residuals", "Homoscedasticity"],
            "outputs": ["Coefficients", "R-squared", "p-values", "Residuals"]
        }
    ]
    
    return {
        "status": "success",
        "data": statistical_tests,
        "message": f"Retrieved {len(statistical_tests)} statistical tests"
    }
