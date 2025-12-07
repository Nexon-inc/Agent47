from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List
from pydantic import BaseModel, Field

from ..database import get_joe_database
from ..services.accessibility_service import AccessibilityService

router = APIRouter(prefix="/accessibility", tags=["Accessibility"])

class AccessibilityAuditRequest(BaseModel):
    research_platform: str = Field(..., description="Research platform to audit")

class PlatformDataRequest(BaseModel):
    platform_data: Dict[str, Any] = Field(..., description="Platform data for report generation")

# Dependency
async def get_accessibility_service() -> AccessibilityService:
    service = AccessibilityService()
    await service.initialize()
    return service

@router.post("/audit-compliance")
async def audit_accessibility_compliance(
    request: AccessibilityAuditRequest,
    service: AccessibilityService = Depends(get_accessibility_service)
):
    """Audit accessibility compliance for research platforms"""
    try:
        result = await service.audit_accessibility_compliance(
            user_id=1,  # TODO: Get from authentication
            research_platform=request.research_platform
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["audit_data"],
                "message": f"Accessibility audit completed for {request.research_platform}"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Accessibility audit failed: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to audit accessibility: {str(e)}"
        )

@router.post("/generate-report")
async def generate_accessibility_report(
    request: PlatformDataRequest,
    service: AccessibilityService = Depends(get_accessibility_service)
):
    """Generate comprehensive accessibility report"""
    try:
        result = await service.generate_accessibility_report(
            user_id=1,  # TODO: Get from authentication
            platform_data=request.platform_data
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["report_data"],
                "message": "Accessibility report generated successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Report generation failed: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate accessibility report: {str(e)}"
        )

@router.get("/standards")
async def get_accessibility_standards(service: AccessibilityService = Depends(get_accessibility_service)):
    """Get supported accessibility standards and guidelines"""
    standards = [
        {
            "id": "wcag_2_1",
            "name": "WCAG 2.1",
            "description": "Web Content Accessibility Guidelines 2.1",
            "levels": ["A", "AA", "AAA"],
            "focus_areas": ["Perceivable", "Operable", "Understandable", "Robust"]
        },
        {
            "id": "section_508",
            "name": "Section 508",
            "description": "Federal accessibility requirements for electronic information",
            "levels": ["Compliant", "Non-compliant"],
            "focus_areas": ["Software", "Web applications", "Electronic documents"]
        },
        {
            "id": "ada",
            "name": "ADA Title III",
            "description": "Americans with Disabilities Act - Public accommodations",
            "levels": ["Compliant", "Non-compliant"],
            "focus_areas": ["Digital accessibility", "Equal access", "Reasonable accommodation"]
        },
        {
            "id": "iso_9241",
            "name": "ISO 9241",
            "description": "Ergonomics of human-system interaction",
            "levels": ["Basic", "Enhanced", "Advanced"],
            "focus_areas": ["Usability", "Accessibility", "User experience"]
        }
    ]
    
    return {
        "status": "success",
        "data": standards,
        "message": f"Retrieved {len(standards)} accessibility standards"
    }
