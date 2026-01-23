from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
from pydantic import BaseModel, Field

from ..database import get_db
from ..services.ethical_guidelines_service import EthicalGuidelinesService

router = APIRouter(prefix="/ethical-guidelines", tags=["Ethical JackieCampaign Guidelines"])

class ContentReviewRequest(BaseModel):
    content: str
    content_type: str
    target_audience: Optional[List[str]] = Field(default_factory=list)
    industry: Optional[str]
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)


class EthicalReviewResponse(BaseModel):
    id: str
    original_content: str
    flagged_issues: List[Dict[str, Any]]
    suggestions: List[str]
    ethical_score: float
    compliance_status: str
    recommendations: List[str]
    created_at: datetime

@router.post("/review-content", response_model=EthicalReviewResponse)
async def review_content_ethics(
    request: ContentReviewRequest,
    db: Session = Depends(get_db)
):
    service = EthicalGuidelinesService(db)
    try:
        result = service.review_content_ethics(
            request.content,
            request.content_type,
            request.target_audience,
            request.industry,
            request.context
        )
        return EthicalReviewResponse(
            id=result["id"],
            original_content=result["original_content"],
            flagged_issues=result["flagged_issues"],
            suggestions=result["suggestions"],
            ethical_score=result["ethical_score"],
            compliance_status=result["compliance_status"],
            recommendations=result["recommendations"],
            created_at=result["created_at"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/check-misleading-claims")
async def check_misleading_claims(
    content: str,
    industry: str,
    claim_types: Optional[List[str]] = None,
    db: Session = Depends(get_db)
):
    service = EthicalGuidelinesService(db)
    try:
        result = service.check_misleading_claims(content, industry, claim_types)
        return {
            "misleading_claims": result["misleading_claims"],
            "risk_level": result["risk_level"],
            "suggestions": result["suggestions"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/suggest-inclusive-language")
async def suggest_inclusive_language(
    content: str,
    target_audience: List[str],
    inclusivity_focus: Optional[List[str]] = None,
    db: Session = Depends(get_db)
):
    service = EthicalGuidelinesService(db)
    try:
        result = service.suggest_inclusive_language(content, target_audience, inclusivity_focus)
        return {
            "original_content": result["original_content"],
            "suggested_content": result["suggested_content"],
            "changes": result["changes"],
            "inclusivity_score": result["inclusivity_score"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/validate-compliance")
async def validate_compliance(
    content: str,
    regulations: List[str],
    industry: str,
    db: Session = Depends(get_db)
):
    service = EthicalGuidelinesService(db)
    try:
        result = service.validate_compliance(content, regulations, industry)
        return {
            "compliance_status": result["compliance_status"],
            "violations": result["violations"],
            "recommendations": result["recommendations"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/check-data-privacy")
async def check_data_privacy_compliance(
    data_usage: Dict[str, Any],
    privacy_regulations: List[str],
    db: Session = Depends(get_db)
):
    service = EthicalGuidelinesService(db)
    try:
        result = service.check_data_privacy_compliance(data_usage, privacy_regulations)
        return {
            "privacy_compliance": result["privacy_compliance"],
            "issues": result["issues"],
            "required_actions": result["required_actions"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/review-targeting")
async def review_targeting_ethics(
    targeting_criteria: Dict[str, Any],
    industry: str,
    db: Session = Depends(get_db)
):
    service = EthicalGuidelinesService(db)
    try:
        result = service.review_targeting_ethics(targeting_criteria, industry)
        return {
            "ethical_targeting": result["ethical_targeting"],
            "concerns": result["concerns"],
            "alternatives": result["alternatives"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/check-transparency")
async def check_transparency_requirements(
    campaign_info: Dict[str, Any],
    platform: str,
    db: Session = Depends(get_db)
):
    service = EthicalGuidelinesService(db)
    try:
        result = service.check_transparency_requirements(campaign_info, platform)
        return {
            "transparency_compliance": result["transparency_compliance"],
            "missing_elements": result["missing_elements"],
            "required_disclosures": result["required_disclosures"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/review-consent-mechanisms")
async def review_consent_mechanisms(
    consent_flow: Dict[str, Any],
    consent_type: str,
    db: Session = Depends(get_db)
):
    service = EthicalGuidelinesService(db)
    try:
        result = service.review_consent_mechanisms(consent_flow, consent_type)
        return {
            "consent_compliance": result["consent_compliance"],
            "improvements": result["improvements"],
            "best_practices": result["best_practices"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/check-accessibility-compliance")
async def check_accessibility_compliance(
    content: str,
    accessibility_standards: List[str],
    db: Session = Depends(get_db)
):
    service = EthicalGuidelinesService(db)
    try:
        result = service.check_accessibility_compliance(content, accessibility_standards)
        return {
            "accessibility_compliance": result["accessibility_compliance"],
            "issues": result["issues"],
            "improvements": result["improvements"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/review-cultural-sensitivity")
async def review_cultural_sensitivity(
    content: str,
    target_cultures: List[str],
    db: Session = Depends(get_db)
):
    service = EthicalGuidelinesService(db)
    try:
        result = service.review_cultural_sensitivity(content, target_cultures)
        return {
            "cultural_sensitivity": result["cultural_sensitivity"],
            "concerns": result["concerns"],
            "suggestions": result["suggestions"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/check-age-appropriateness")
async def check_age_appropriateness(
    content: str,
    target_age_groups: List[str],
    content_type: str,
    db: Session = Depends(get_db)
):
    service = EthicalGuidelinesService(db)
    try:
        result = service.check_age_appropriateness(content, target_age_groups, content_type)
        return {
            "age_appropriateness": result["age_appropriateness"],
            "concerns": result["concerns"],
            "recommendations": result["recommendations"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/review-environmental-claims")
async def review_environmental_claims(
    content: str,
    industry: str,
    db: Session = Depends(get_db)
):
    service = EthicalGuidelinesService(db)
    try:
        result = service.review_environmental_claims(content, industry)
        return {
            "environmental_compliance": result["environmental_compliance"],
            "greenwashing_risks": result["greenwashing_risks"],
            "suggestions": result["suggestions"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/check-health-claims")
async def check_health_claims(
    content: str,
    health_claim_type: str,
    db: Session = Depends(get_db)
):
    service = EthicalGuidelinesService(db)
    try:
        result = service.check_health_claims(content, health_claim_type)
        return {
            "health_claim_compliance": result["health_claim_compliance"],
            "violations": result["violations"],
            "required_disclaimers": result["required_disclaimers"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/review-financial-claims")
async def review_financial_claims(
    content: str,
    financial_product_type: str,
    db: Session = Depends(get_db)
):
    service = EthicalGuidelinesService(db)
    try:
        result = service.review_financial_claims(content, financial_product_type)
        return {
            "financial_compliance": result["financial_compliance"],
            "risks": result["risks"],
            "required_disclosures": result["required_disclosures"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-ethical-guidelines")
async def generate_ethical_guidelines(
    industry: str,
    campaign_type: str,
    target_audience: List[str],
    db: Session = Depends(get_db)
):
    service = EthicalGuidelinesService(db)
    try:
        result = service.generate_ethical_guidelines(industry, campaign_type, target_audience)
        return {
            "guidelines": result["guidelines"],
            "checklist": result["checklist"],
            "best_practices": result["best_practices"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/guidelines/{industry}")
async def get_industry_guidelines(
    industry: str,
    guideline_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    service = EthicalGuidelinesService(db)
    try:
        guidelines = service.get_industry_guidelines(industry, guideline_type)
        return {"guidelines": guidelines}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch-review")
async def batch_review_content(
    content_batch: List[Dict[str, Any]],
    db: Session = Depends(get_db)
):
    service = EthicalGuidelinesService(db)
    try:
        results = service.batch_review_content(content_batch)
        return {
            "reviewed_count": len(results),
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create-compliance-report")
async def create_compliance_report(
    campaign_id: str,
    report_type: str = "comprehensive",
    db: Session = Depends(get_db)
):
    service = EthicalGuidelinesService(db)
    try:
        result = service.create_compliance_report(campaign_id, report_type)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/regulations/{region}")
async def get_regional_regulations(
    region: str,
    regulation_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    service = EthicalGuidelinesService(db)
    try:
        regulations = service.get_regional_regulations(region, regulation_type)
        return {"regulations": regulations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/check-competitor-compliance")
async def check_competitor_compliance(
    competitor_content: List[Dict[str, Any]],
    industry: str,
    db: Session = Depends(get_db)
):
    service = EthicalGuidelinesService(db)
    try:
        result = service.check_competitor_compliance(competitor_content, industry)
        return {
            "competitor_analysis": result["competitor_analysis"],
            "compliance_gaps": result["compliance_gaps"],
            "opportunities": result["opportunities"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-disclaimers")
async def generate_disclaimers(
    content: str,
    disclaimer_type: str,
    industry: str,
    db: Session = Depends(get_db)
):
    service = EthicalGuidelinesService(db)
    try:
        result = service.generate_disclaimers(content, disclaimer_type, industry)
        return {
            "required_disclaimers": result["required_disclaimers"],
            "suggested_disclaimers": result["suggested_disclaimers"],
            "placement_recommendations": result["placement_recommendations"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/review-testimonials")
async def review_testimonials(
    testimonials: List[Dict[str, Any]],
    industry: str,
    db: Session = Depends(get_db)
):
    service = EthicalGuidelinesService(db)
    try:
        result = service.review_testimonials(testimonials, industry)
        return {
            "testimonial_compliance": result["testimonial_compliance"],
            "issues": result["issues"],
            "required_verification": result["required_verification"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/check-pricing-transparency")
async def check_pricing_transparency(
    pricing_info: Dict[str, Any],
    industry: str,
    db: Session = Depends(get_db)
):
    service = EthicalGuidelinesService(db)
    try:
        result = service.check_pricing_transparency(pricing_info, industry)
        return {
            "pricing_transparency": result["pricing_transparency"],
            "hidden_costs": result["hidden_costs"],
            "required_disclosures": result["required_disclosures"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/review-subscription-terms")
async def review_subscription_terms(
    terms: str,
    subscription_type: str,
    db: Session = Depends(get_db)
):
    service = EthicalGuidelinesService(db)
    try:
        result = service.review_subscription_terms(terms, subscription_type)
        return {
            "terms_compliance": result["terms_compliance"],
            "concerns": result["concerns"],
            "improvements": result["improvements"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/check-influencer-compliance")
async def check_influencer_compliance(
    influencer_content: Dict[str, Any],
    disclosure_requirements: List[str],
    db: Session = Depends(get_db)
):
    service = EthicalGuidelinesService(db)
    try:
        result = service.check_influencer_compliance(influencer_content, disclosure_requirements)
        return {
            "influencer_compliance": result["influencer_compliance"],
            "missing_disclosures": result["missing_disclosures"],
            "required_actions": result["required_actions"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/review-urgency-tactics")
async def review_urgency_tactics(
    content: str,
    urgency_type: str,
    db: Session = Depends(get_db)
):
    service = EthicalGuidelinesService(db)
    try:
        result = service.review_urgency_tactics(content, urgency_type)
        return {
            "urgency_ethics": result["urgency_ethics"],
            "manipulative_elements": result["manipulative_elements"],
            "alternatives": result["alternatives"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/check-scarcity-claims")
async def check_scarcity_claims(
    content: str,
    scarcity_type: str,
    db: Session = Depends(get_db)
):
    service = EthicalGuidelinesService(db)
    try:
        result = service.check_scarcity_claims(content, scarcity_type)
        return {
            "scarcity_verification": result["scarcity_verification"],
            "false_claims": result["false_claims"],
            "verification_required": result["verification_required"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/review-social-proof")
async def review_social_proof(
    social_proof_elements: List[Dict[str, Any]],
    db: Session = Depends(get_db)
):
    service = EthicalGuidelinesService(db)
    try:
        result = service.review_social_proof(social_proof_elements)
        return {
            "social_proof_ethics": result["social_proof_ethics"],
            "verification_needed": result["verification_needed"],
            "improvements": result["improvements"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/ethical-compliance")
async def get_ethical_compliance_analytics(
    timeframe: str = "30d",
    db: Session = Depends(get_db)
):
    service = EthicalGuidelinesService(db)
    try:
        analytics = service.get_ethical_compliance_analytics(timeframe)
        return analytics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-ethical-checklist")
async def generate_ethical_checklist(
    campaign_type: str,
    industry: str,
    platforms: List[str],
    db: Session = Depends(get_db)
):
    service = EthicalGuidelinesService(db)
    try:
        result = service.generate_ethical_checklist(campaign_type, industry, platforms)
        return {
            "checklist": result["checklist"],
            "priority_items": result["priority_items"],
            "compliance_tips": result["compliance_tips"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/review-ai-generated-content")
async def review_ai_generated_content(
    content: str,
    ai_disclosure_required: bool = True,
    db: Session = Depends(get_db)
):
    service = EthicalGuidelinesService(db)
    try:
        result = service.review_ai_generated_content(content, ai_disclosure_required)
        return {
            "ai_content_ethics": result["ai_content_ethics"],
            "disclosure_requirements": result["disclosure_requirements"],
            "transparency_measures": result["transparency_measures"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
