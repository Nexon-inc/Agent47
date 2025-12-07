from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import json

from ..database import get_purity_database
from ..models import BusinessIdea, LegalRequirement, BusinessModel
from ..services.legal_compliance_service import LegalComplianceService

router = APIRouter(prefix="/legal-compliance", tags=["Legal & Compliance"])

class LegalRequirementRequest(BaseModel):
    business_idea_id: int
    business_location: str
    business_type: str
    industry: str
    expected_annual_revenue: float = Field(..., ge=0)
    employee_count: int = Field(0, ge=0)
    has_international_operations: bool = False
    handles_personal_data: bool = False
    sells_products_online: bool = False

class LegalRequirementResponse(BaseModel):
    id: int
    business_idea_id: int
    business_location: str
    business_type: str
    industry: str
    required_licenses: List[dict]
    required_permits: List[dict]
    tax_obligations: List[dict]
    compliance_requirements: List[dict]
    privacy_requirements: List[dict]
    intellectual_property_needs: List[dict]
    risk_assessment: str
    compliance_score: float
    estimated_compliance_cost: float
    created_at: datetime
    updated_at: datetime

class ComplianceValidationRequest(BaseModel):
    legal_requirement_id: int
    current_licenses: List[str]
    current_permits: List[str]
    compliance_status: dict
    audit_findings: Optional[List[str]] = None

class ComplianceValidationResponse(BaseModel):
    id: int
    legal_requirement_id: int
    compliance_score: float
    missing_requirements: List[str]
    compliance_gaps: List[dict]
    recommendations: List[str]
    risk_level: str
    next_audit_date: datetime
    created_at: datetime

class RegulatoryGuidanceRequest(BaseModel):
    business_idea_id: int
    specific_concern: str
    industry_regulations: List[str]
    compliance_questions: List[str]

class RegulatoryGuidanceResponse(BaseModel):
    id: int
    business_idea_id: int
    guidance_summary: str
    regulatory_requirements: List[dict]
    compliance_timeline: List[dict]
    risk_mitigation_strategies: List[str]
    expert_recommendations: List[str]
    created_at: datetime

@router.post("/requirements", response_model=LegalRequirementResponse)
async def check_legal_requirements(
    request: LegalRequirementRequest,
    db: AsyncSession = Depends(get_purity_database)
):
    try:
        service = LegalComplianceService()
        legal_req = await service.check_legal_requirements(
            db=db,
            business_idea_id=request.business_idea_id,
            business_location=request.business_location,
            business_type=request.business_type,
            industry=request.industry,
            expected_annual_revenue=request.expected_annual_revenue,
            employee_count=request.employee_count,
            has_international_operations=request.has_international_operations,
            handles_personal_data=request.handles_personal_data,
            sells_products_online=request.sells_products_online
        )
        return LegalRequirementResponse(
            id=legal_req.id,
            business_idea_id=legal_req.business_idea_id,
            business_location=legal_req.business_location,
            business_type=legal_req.business_type,
            industry=legal_req.industry,
            required_licenses=json.loads(legal_req.required_licenses),
            required_permits=json.loads(legal_req.required_permits),
            tax_obligations=json.loads(legal_req.tax_obligations),
            compliance_requirements=json.loads(legal_req.compliance_requirements),
            privacy_requirements=json.loads(legal_req.privacy_requirements),
            intellectual_property_needs=json.loads(legal_req.intellectual_property_needs),
            risk_assessment=legal_req.risk_assessment,
            compliance_score=legal_req.compliance_score,
            estimated_compliance_cost=legal_req.estimated_compliance_cost,
            created_at=legal_req.created_at,
            updated_at=legal_req.updated_at
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/validate", response_model=ComplianceValidationResponse)
async def validate_compliance(
    request: ComplianceValidationRequest,
    db: AsyncSession = Depends(get_purity_database)
):
    try:
        service = LegalComplianceService()
        validation = await service.validate_compliance(
            db=db,
            legal_requirement_id=request.legal_requirement_id,
            current_licenses=request.current_licenses,
            current_permits=request.current_permits,
            compliance_status=request.compliance_status,
            audit_findings=request.audit_findings
        )
        return ComplianceValidationResponse(
            id=validation.id,
            legal_requirement_id=validation.legal_requirement_id,
            compliance_score=validation.compliance_score,
            missing_requirements=json.loads(validation.missing_requirements),
            compliance_gaps=json.loads(validation.compliance_gaps),
            recommendations=json.loads(validation.recommendations),
            risk_level=validation.risk_level,
            next_audit_date=validation.next_audit_date,
            created_at=validation.created_at
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/guidance", response_model=RegulatoryGuidanceResponse)
async def get_regulatory_guidance(
    request: RegulatoryGuidanceRequest,
    db: AsyncSession = Depends(get_purity_database)
):
    try:
        service = LegalComplianceService()
        guidance = await service.get_regulatory_guidance(
            db=db,
            business_idea_id=request.business_idea_id,
            specific_concern=request.specific_concern,
            industry_regulations=request.industry_regulations,
            compliance_questions=request.compliance_questions
        )
        return RegulatoryGuidanceResponse(
            id=guidance.id,
            business_idea_id=guidance.business_idea_id,
            guidance_summary=guidance.guidance_summary,
            regulatory_requirements=json.loads(guidance.regulatory_requirements),
            compliance_timeline=json.loads(guidance.compliance_timeline),
            risk_mitigation_strategies=json.loads(guidance.risk_mitigation_strategies),
            expert_recommendations=json.loads(guidance.expert_recommendations),
            created_at=guidance.created_at
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/requirements/{requirement_id}", response_model=LegalRequirementResponse)
async def get_legal_requirement(
    requirement_id: int,
    db: AsyncSession = Depends(get_purity_database)
):
    try:
        result = await db.execute(select(LegalRequirement).where(LegalRequirement.id == requirement_id))
        legal_req = result.scalar_one_or_none()
        if not legal_req:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Legal requirement not found")
        return LegalRequirementResponse(
            id=legal_req.id,
            business_idea_id=legal_req.business_idea_id,
            business_location=legal_req.business_location,
            business_type=legal_req.business_type,
            industry=legal_req.industry,
            required_licenses=json.loads(legal_req.required_licenses),
            required_permits=json.loads(legal_req.required_permits),
            tax_obligations=json.loads(legal_req.tax_obligations),
            compliance_requirements=json.loads(legal_req.compliance_requirements),
            privacy_requirements=json.loads(legal_req.privacy_requirements),
            intellectual_property_needs=json.loads(legal_req.intellectual_property_needs),
            risk_assessment=legal_req.risk_assessment,
            compliance_score=legal_req.compliance_score,
            estimated_compliance_cost=legal_req.estimated_compliance_cost,
            created_at=legal_req.created_at,
            updated_at=legal_req.updated_at
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/requirements/business/{business_idea_id}", response_model=List[LegalRequirementResponse])
async def get_business_legal_requirements(
    business_idea_id: int,
    db: AsyncSession = Depends(get_purity_database)
):
    try:
        result = await db.execute(select(LegalRequirement).where(LegalRequirement.business_idea_id == business_idea_id))
        legal_reqs = result.scalars().all()
        return [
            LegalRequirementResponse(
                id=legal_req.id,
                business_idea_id=legal_req.business_idea_id,
                business_location=legal_req.business_location,
                business_type=legal_req.business_type,
                industry=legal_req.industry,
                required_licenses=json.loads(legal_req.required_licenses),
                required_permits=json.loads(legal_req.required_permits),
                tax_obligations=json.loads(legal_req.tax_obligations),
                compliance_requirements=json.loads(legal_req.compliance_requirements),
                privacy_requirements=json.loads(legal_req.privacy_requirements),
                intellectual_property_needs=json.loads(legal_req.intellectual_property_needs),
                risk_assessment=legal_req.risk_assessment,
                compliance_score=legal_req.compliance_score,
                estimated_compliance_cost=legal_req.estimated_compliance_cost,
                created_at=legal_req.created_at,
                updated_at=legal_req.updated_at
            )
            for legal_req in legal_reqs
        ]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.put("/requirements/{requirement_id}", response_model=LegalRequirementResponse)
async def update_legal_requirement(
    requirement_id: int,
    request: LegalRequirementRequest,
    db: AsyncSession = Depends(get_purity_database)
):
    try:
        result = await db.execute(select(LegalRequirement).where(LegalRequirement.id == requirement_id))
        legal_req = result.scalar_one_or_none()
        if not legal_req:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Legal requirement not found")
        
        service = LegalComplianceService()
        updated_req = await service.update_legal_requirement(
            db=db,
            requirement_id=requirement_id,
            business_location=request.business_location,
            business_type=request.business_type,
            industry=request.industry,
            expected_annual_revenue=request.expected_annual_revenue,
            employee_count=request.employee_count,
            has_international_operations=request.has_international_operations,
            handles_personal_data=request.handles_personal_data,
            sells_products_online=request.sells_products_online
        )
        return LegalRequirementResponse(
            id=updated_req.id,
            business_idea_id=updated_req.business_idea_id,
            business_location=updated_req.business_location,
            business_type=updated_req.business_type,
            industry=updated_req.industry,
            required_licenses=json.loads(updated_req.required_licenses),
            required_permits=json.loads(updated_req.required_permits),
            tax_obligations=json.loads(updated_req.tax_obligations),
            compliance_requirements=json.loads(updated_req.compliance_requirements),
            privacy_requirements=json.loads(updated_req.privacy_requirements),
            intellectual_property_needs=json.loads(updated_req.intellectual_property_needs),
            risk_assessment=updated_req.risk_assessment,
            compliance_score=updated_req.compliance_score,
            estimated_compliance_cost=updated_req.estimated_compliance_cost,
            created_at=updated_req.created_at,
            updated_at=updated_req.updated_at
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.delete("/requirements/{requirement_id}")
async def delete_legal_requirement(
    requirement_id: int,
    db: AsyncSession = Depends(get_purity_database)
):
    try:
        result = await db.execute(select(LegalRequirement).where(LegalRequirement.id == requirement_id))
        legal_req = result.scalar_one_or_none()
        if not legal_req:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Legal requirement not found")
        await db.delete(legal_req)
        await db.commit()
        return {"message": "Legal requirement deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
