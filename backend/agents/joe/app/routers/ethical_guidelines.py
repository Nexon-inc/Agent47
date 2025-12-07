"""
Ethical Guidelines Router

This router handles research ethics validation and compliance checking endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from ..database import get_joe_database
from ..services.ethical_guidelines_service import EthicalGuidelinesService
from backend.core.authentication.auth_manager import AuthManager

router = APIRouter(prefix="/ethical-guidelines", tags=["Ethical Guidelines"])

class EthicsValidationRequest(BaseModel):
    research_proposal: Dict[str, Any] = Field(..., description="Research proposal to validate")
    compliance_standards: List[str] = Field(default=["GDPR", "IRB", "Industry_Standards"], description="Compliance standards to check")

class GuidelinesRequest(BaseModel):
    research_domain: str = Field(default="general", description="Research domain for guidelines")

# Dependencies
async def get_ethical_guidelines_service() -> EthicalGuidelinesService:
    service = EthicalGuidelinesService()
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

@router.post("/validate-ethics")
async def validate_research_ethics(
    request: EthicsValidationRequest,
    service: EthicalGuidelinesService = Depends(get_ethical_guidelines_service),
    user_id: int = Depends(get_current_user_id)
):
    """Validate research proposal against ethical guidelines"""
    try:
        result = await service.validate_research_ethics(
            user_id=user_id,
            research_proposal=request.research_proposal,
            compliance_standards=request.compliance_standards
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["validation_data"],
                "message": "Research ethics validation completed successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Ethics validation failed: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate research ethics: {str(e)}"
        )

@router.post("/get-guidelines")
async def get_ethical_guidelines(
    request: GuidelinesRequest,
    service: EthicalGuidelinesService = Depends(get_ethical_guidelines_service),
    user_id: int = Depends(get_current_user_id)
):
    """Get ethical guidelines for specific research domains"""
    try:
        result = await service.get_ethical_guidelines(
            user_id=user_id,
            research_domain=request.research_domain
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["guidelines_data"],
                "message": f"Ethical guidelines retrieved for {request.research_domain} domain"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get ethical guidelines: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get ethical guidelines: {str(e)}"
        )

@router.get("/compliance-standards")
async def get_compliance_standards(service: EthicalGuidelinesService = Depends(get_ethical_guidelines_service)):
    """Get available compliance standards and frameworks"""
    compliance_standards = [
        {
            "standard_id": "GDPR",
            "name": "General Data Protection Regulation",
            "description": "EU regulation on data protection and privacy",
            "scope": "Personal data processing and privacy rights",
            "key_requirements": [
                "Data minimization",
                "Purpose limitation",
                "Data subject rights",
                "Data protection by design"
            ],
            "applicability": "EU residents and organizations"
        },
        {
            "standard_id": "IRB",
            "name": "Institutional Review Board",
            "description": "Ethics committee for human research protection",
            "scope": "Human subjects research and clinical trials",
            "key_requirements": [
                "Informed consent",
                "Risk-benefit assessment",
                "Participant protection",
                "Research protocol review"
            ],
            "applicability": "Academic and medical research"
        },
        {
            "standard_id": "Industry_Standards",
            "name": "Industry Best Practices",
            "description": "Voluntary standards for research integrity",
            "scope": "Research methodology and reporting",
            "key_requirements": [
                "Transparency in methods",
                "Data quality assurance",
                "Conflict of interest disclosure",
                "Reproducible research"
            ],
            "applicability": "Industry and commercial research"
        },
        {
            "standard_id": "ISO_27001",
            "name": "Information Security Management",
            "description": "International standard for information security",
            "scope": "Data security and risk management",
            "key_requirements": [
                "Information security policies",
                "Risk assessment",
                "Security controls",
                "Continuous improvement"
            ],
            "applicability": "Organizations handling sensitive data"
        }
    ]
    
    return {
        "status": "success",
        "data": compliance_standards,
        "message": f"Retrieved {len(compliance_standards)} compliance standards"
    }
