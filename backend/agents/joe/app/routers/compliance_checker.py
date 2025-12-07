from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List
from pydantic import BaseModel, Field

from ..database import get_joe_database
from ..services.compliance_checker_service import ComplianceCheckerService

router = APIRouter(prefix="/compliance-checker", tags=["Compliance Checker"])

class ComplianceCheckRequest(BaseModel):
    research_type: str = Field(..., description="Type of research to check")
    data_sources: List[str] = Field(..., description="Data sources used")
    region: str = Field(default="global", description="Region for compliance")

# Dependency
async def get_compliance_checker_service() -> ComplianceCheckerService:
    service = ComplianceCheckerService()
    await service.initialize()
    return service

@router.post("/check")
async def check_research_compliance(
    request: ComplianceCheckRequest,
    service: ComplianceCheckerService = Depends(get_compliance_checker_service)
):
    """Check compliance for research activities"""
    try:
        result = await service.check_research_compliance(
            user_id=1,  # TODO: Get from authentication
            research_type=request.research_type,
            data_sources=request.data_sources,
            region=request.region
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["compliance_data"],
                "message": f"Compliance check completed for {request.research_type}"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Compliance check failed: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check compliance: {str(e)}"
        )

@router.get("/guidelines/{region}")
async def get_compliance_guidelines(
    region: str,
    service: ComplianceCheckerService = Depends(get_compliance_checker_service)
):
    """Get compliance guidelines for a region"""
    try:
        result = await service.get_compliance_guidelines(
            user_id=1,  # TODO: Get from authentication
            region=region
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["guidelines"],
                "message": f"Retrieved {result['total_guidelines']} compliance guidelines for {region}"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get compliance guidelines: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get compliance guidelines: {str(e)}"
        )

@router.get("/regulations")
async def get_supported_regulations(service: ComplianceCheckerService = Depends(get_compliance_checker_service)):
    """Get supported regulations and compliance frameworks"""
    regulations = [
        {
            "id": "gdpr",
            "name": "General Data Protection Regulation",
            "region": "European Union",
            "scope": "Data protection and privacy",
            "enforcement_date": "2018-05-25"
        },
        {
            "id": "ccpa",
            "name": "California Consumer Privacy Act",
            "region": "California, USA",
            "scope": "Consumer privacy rights",
            "enforcement_date": "2020-01-01"
        },
        {
            "id": "lgpd",
            "name": "Lei Geral de Proteção de Dados",
            "region": "Brazil",
            "scope": "Data protection",
            "enforcement_date": "2020-09-18"
        },
        {
            "id": "pipeda",
            "name": "Personal Information Protection and Electronic Documents Act",
            "region": "Canada",
            "scope": "Personal information protection",
            "enforcement_date": "2001-04-13"
        }
    ]
    
    return {
        "status": "success",
        "data": regulations,
        "message": f"Retrieved {len(regulations)} supported regulations"
    }
