from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from ..services.ethical_guidelines_service import EthicalGuidelinesService
from ..models import ContentType, PlatformType, ToneType
from ..database import get_shakes_database

router = APIRouter(prefix="/ethical-guidelines", tags=["Ethical Guidelines"])

# Pydantic Models
class CheckContentEthicsRequest(BaseModel):
    content_piece_id: int = Field(..., description="Content piece ID")
    ethical_categories: List[str] = Field(default=[], description="Ethical categories to check")

class GenerateEthicalGuidelinesRequest(BaseModel):
    industry: str = Field(..., description="Industry")
    content_type: str = Field(..., description="Content type")
    target_audience: str = Field(..., description="Target audience")
    regulatory_requirements: List[str] = Field(default=[], description="Regulatory requirements")

class AuditContentBiasRequest(BaseModel):
    content_piece_id: int = Field(..., description="Content piece ID")
    bias_categories: List[str] = Field(default=[], description="Bias categories to audit")

class CheckAccessibilityComplianceRequest(BaseModel):
    content_piece_id: int = Field(..., description="Content piece ID")
    accessibility_standards: List[str] = Field(default=[], description="Accessibility standards")

class ValidateContentAccuracyRequest(BaseModel):
    content_piece_id: int = Field(..., description="Content piece ID")
    accuracy_categories: List[str] = Field(default=[], description="Accuracy categories")

# Dependency
async def get_ethical_guidelines_service() -> EthicalGuidelinesService:
    """Get ethical guidelines service instance"""
    service = EthicalGuidelinesService()
    await service.initialize()
    return service

# Endpoints
@router.post("/check-ethics", response_model=Dict[str, Any], status_code=200)
async def check_content_ethics(
    request: CheckContentEthicsRequest,
    service: EthicalGuidelinesService = Depends(get_ethical_guidelines_service)
):
    """Check content for ethical compliance"""
    try:
        result = await service.check_content_ethics(
            content_piece_id=request.content_piece_id,
            ethical_categories=request.ethical_categories
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to check content ethics")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Content ethics check failed: {str(e)}"
        )

@router.post("/generate-guidelines", response_model=Dict[str, Any], status_code=200)
async def generate_ethical_guidelines(
    request: GenerateEthicalGuidelinesRequest,
    service: EthicalGuidelinesService = Depends(get_ethical_guidelines_service)
):
    """Generate ethical guidelines for specific context"""
    try:
        result = await service.generate_ethical_guidelines(
            industry=request.industry,
            content_type=request.content_type,
            target_audience=request.target_audience,
            regulatory_requirements=request.regulatory_requirements
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to generate ethical guidelines")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ethical guidelines generation failed: {str(e)}"
        )

@router.post("/audit-bias", response_model=Dict[str, Any], status_code=200)
async def audit_content_bias(
    request: AuditContentBiasRequest,
    service: EthicalGuidelinesService = Depends(get_ethical_guidelines_service)
):
    """Audit content for bias and inclusivity issues"""
    try:
        result = await service.audit_content_bias(
            content_piece_id=request.content_piece_id,
            bias_categories=request.bias_categories
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to audit content bias")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Content bias audit failed: {str(e)}"
        )

@router.post("/check-accessibility", response_model=Dict[str, Any], status_code=200)
async def check_accessibility_compliance(
    request: CheckAccessibilityComplianceRequest,
    service: EthicalGuidelinesService = Depends(get_ethical_guidelines_service)
):
    """Check content for accessibility compliance"""
    try:
        result = await service.check_accessibility_compliance(
            content_piece_id=request.content_piece_id,
            accessibility_standards=request.accessibility_standards
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to check accessibility compliance")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Accessibility compliance check failed: {str(e)}"
        )

@router.post("/validate-accuracy", response_model=Dict[str, Any], status_code=200)
async def validate_content_accuracy(
    request: ValidateContentAccuracyRequest,
    service: EthicalGuidelinesService = Depends(get_ethical_guidelines_service)
):
    """Validate content for accuracy and fact-checking"""
    try:
        result = await service.validate_content_accuracy(
            content_piece_id=request.content_piece_id,
            accuracy_categories=request.accuracy_categories
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to validate content accuracy")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Content accuracy validation failed: {str(e)}"
        )

@router.get("/ethical-categories")
async def get_ethical_categories():
    """Get available ethical categories for content analysis"""
    return {
        "ethical_categories": [
            {
                "id": "accuracy",
                "name": "Accuracy",
                "description": "Ensuring content is factually correct and truthful",
                "checkpoints": [
                    "Fact verification",
                    "Source credibility",
                    "Information accuracy",
                    "Misleading content detection"
                ],
                "importance": "high"
            },
            {
                "id": "bias",
                "name": "Bias",
                "description": "Identifying and addressing bias in content",
                "checkpoints": [
                    "Gender bias detection",
                    "Racial bias identification",
                    "Cultural bias assessment",
                    "Stereotype recognition"
                ],
                "importance": "high"
            },
            {
                "id": "privacy",
                "name": "Privacy",
                "description": "Protecting user privacy and data",
                "checkpoints": [
                    "Personal information protection",
                    "Data collection transparency",
                    "Consent requirements",
                    "Privacy policy compliance"
                ],
                "importance": "high"
            },
            {
                "id": "accessibility",
                "name": "Accessibility",
                "description": "Ensuring content is accessible to all users",
                "checkpoints": [
                    "Screen reader compatibility",
                    "Color contrast compliance",
                    "Keyboard navigation",
                    "Alt text for images"
                ],
                "importance": "high"
            },
            {
                "id": "inclusivity",
                "name": "Inclusivity",
                "description": "Promoting inclusive and diverse content",
                "checkpoints": [
                    "Representation diversity",
                    "Inclusive language use",
                    "Cultural sensitivity",
                    "Accessibility considerations"
                ],
                "importance": "medium"
            },
            {
                "id": "transparency",
                "name": "Transparency",
                "description": "Maintaining transparency in content and practices",
                "checkpoints": [
                    "Source disclosure",
                    "Sponsored content labeling",
                    "Conflict of interest disclosure",
                    "Methodology transparency"
                ],
                "importance": "medium"
            }
        ]
    }

@router.get("/regulatory-requirements")
async def get_regulatory_requirements():
    """Get common regulatory requirements for content compliance"""
    return {
        "regulatory_requirements": [
            {
                "id": "GDPR",
                "name": "General Data Protection Regulation",
                "description": "EU regulation for data protection and privacy",
                "requirements": [
                    "Data processing consent",
                    "Right to be forgotten",
                    "Data portability",
                    "Privacy by design"
                ],
                "applicable_regions": ["EU", "EEA"],
                "content_implications": ["privacy_policies", "data_collection", "user_consent"]
            },
            {
                "id": "CCPA",
                "name": "California Consumer Privacy Act",
                "description": "California state law for consumer privacy rights",
                "requirements": [
                    "Consumer privacy rights",
                    "Data disclosure requirements",
                    "Opt-out mechanisms",
                    "Data security measures"
                ],
                "applicable_regions": ["California"],
                "content_implications": ["privacy_notices", "data_usage", "consumer_rights"]
            },
            {
                "id": "ADA",
                "name": "Americans with Disabilities Act",
                "description": "US law ensuring accessibility for people with disabilities",
                "requirements": [
                    "Accessible web content",
                    "Screen reader compatibility",
                    "Keyboard navigation",
                    "Alternative text for images"
                ],
                "applicable_regions": ["United States"],
                "content_implications": ["web_accessibility", "content_formatting", "user_interface"]
            },
            {
                "id": "FTC",
                "name": "Federal Trade Commission Guidelines",
                "description": "US guidelines for advertising and marketing practices",
                "requirements": [
                    "Truth in advertising",
                    "Endorsement disclosure",
                    "Deceptive practices prevention",
                    "Consumer protection"
                ],
                "applicable_regions": ["United States"],
                "content_implications": ["advertising_claims", "endorsements", "marketing_practices"]
            }
        ]
    }

@router.get("/accessibility-standards")
async def get_accessibility_standards():
    """Get accessibility standards for content compliance"""
    return {
        "accessibility_standards": [
            {
                "id": "WCAG_2.1",
                "name": "Web Content Accessibility Guidelines 2.1",
                "description": "International standard for web accessibility",
                "levels": ["A", "AA", "AAA"],
                "requirements": [
                    "Perceivable content",
                    "Operable interface",
                    "Understandable information",
                    "Robust content"
                ],
                "applicable_content": ["web_content", "digital_documents", "multimedia"]
            },
            {
                "id": "ADA",
                "name": "Americans with Disabilities Act",
                "description": "US law ensuring accessibility for people with disabilities",
                "requirements": [
                    "Equal access to information",
                    "Reasonable accommodations",
                    "Effective communication",
                    "Accessible technology"
                ],
                "applicable_content": ["public_accommodations", "government_services", "commercial_facilities"]
            },
            {
                "id": "Section_508",
                "name": "Section 508 of the Rehabilitation Act",
                "description": "US federal accessibility requirements for electronic information",
                "requirements": [
                    "Accessible electronic content",
                    "Assistive technology compatibility",
                    "Alternative formats",
                    "User interface accessibility"
                ],
                "applicable_content": ["federal_agencies", "government_contractors", "public_sector"]
            }
        ]
    }

@router.get("/ethical-guidelines-framework")
async def get_ethical_guidelines_framework():
    """Get comprehensive ethical guidelines framework"""
    return {
        "ethical_guidelines_framework": [
            {
                "category": "content_creation",
                "title": "Content Creation Ethics",
                "principles": [
                    "Accuracy and truthfulness",
                    "Transparency and disclosure",
                    "Respect for privacy",
                    "Inclusivity and diversity",
                    "Harm prevention"
                ],
                "guidelines": [
                    "Verify all facts and claims",
                    "Cite sources appropriately",
                    "Disclose conflicts of interest",
                    "Use inclusive language",
                    "Avoid harmful stereotypes"
                ]
            },
            {
                "category": "audience_respect",
                "title": "Audience Respect",
                "principles": [
                    "Respect for human dignity",
                    "Cultural sensitivity",
                    "Age-appropriate content",
                    "Accessibility for all",
                    "Informed consent"
                ],
                "guidelines": [
                    "Consider diverse audiences",
                    "Respect cultural differences",
                    "Provide age-appropriate content",
                    "Ensure accessibility compliance",
                    "Obtain proper consent"
                ]
            },
            {
                "category": "transparency",
                "title": "Transparency and Disclosure",
                "principles": [
                    "Open communication",
                    "Honest representation",
                    "Clear disclosure",
                    "Accountability",
                    "Integrity"
                ],
                "guidelines": [
                    "Be transparent about sources",
                    "Disclose sponsored content",
                    "Provide clear disclaimers",
                    "Maintain editorial independence",
                    "Admit mistakes and correct them"
                ]
            },
            {
                "category": "privacy_protection",
                "title": "Privacy Protection",
                "principles": [
                    "Data minimization",
                    "Purpose limitation",
                    "Consent-based processing",
                    "Security measures",
                    "User rights"
                ],
                "guidelines": [
                    "Collect only necessary data",
                    "Use data for stated purposes",
                    "Obtain explicit consent",
                    "Implement security measures",
                    "Respect user privacy rights"
                ]
            }
        ]
    }
