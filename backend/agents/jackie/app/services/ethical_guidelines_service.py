import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session

from core.utils.nlp_utils import NLPProcessor
from core.cache.redis_manager import RedisManager
from ..models import EthicalReview, ComplianceCheck, EthicalGuideline

class EthicalGuidelinesService:
    def __init__(self, db: Session):
        self.db = db
        self.nlp_processor = NLPProcessor()
        self.redis_manager = RedisManager()
        
    def review_content_ethics(self, content: str, content_type: str, target_audience: List[str],
                            industry: str, review_criteria: Dict[str, Any]) -> Dict[str, Any]:
        review_id = str(uuid.uuid4())
        
        prompt = f"""
        Content: {content}
        Content Type: {content_type}
        Target Audience: {target_audience}
        Industry: {industry}
        Review Criteria: {review_criteria}
        
        Review this content for ethical compliance and potential issues.
        """
        
        review_result = self.nlp_processor.review_content_ethics(prompt)
        
        ethical_score = self._calculate_ethical_score(review_result)
        
        review_record = EthicalReview(
            id=review_id, content=content, content_type=content_type,
            target_audience=json.dumps(target_audience), industry=industry,
            review_criteria=json.dumps(review_criteria), review_result=json.dumps(review_result),
            ethical_score=ethical_score, created_at=datetime.utcnow()
        )
        self.db.add(review_record)
        self.db.commit()
        
        return {
            "review_id": review_id, "content": content, "content_type": content_type,
            "ethical_score": ethical_score, "review_result": review_result,
            "created_at": review_record.created_at.isoformat()
        }
    
    def check_misleading_claims(self, content: str, claim_types: List[str]) -> Dict[str, Any]:
        prompt = f"""
        Content: {content}
        Claim Types: {claim_types}
        
        Check for potentially misleading claims in this content.
        """
        
        claims_result = self.nlp_processor.check_misleading_claims(prompt)
        
        return {
            "content": content, "claim_types": claim_types,
            "misleading_claims": claims_result.get("misleading_claims", []),
            "risk_level": claims_result.get("risk_level", "low"),
            "suggestions": claims_result.get("suggestions", [])
        }
    
    def suggest_inclusive_language(self, content: str, target_audience: List[str],
                                 inclusivity_guidelines: Dict[str, Any]) -> Dict[str, Any]:
        prompt = f"""
        Content: {content}
        Target Audience: {target_audience}
        Inclusivity Guidelines: {inclusivity_guidelines}
        
        Suggest inclusive language improvements for this content.
        """
        
        inclusivity_result = self.nlp_processor.suggest_inclusive_language(prompt)
        
        return {
            "content": content, "target_audience": target_audience,
            "suggested_changes": inclusivity_result.get("suggested_changes", []),
            "inclusive_alternatives": inclusivity_result.get("inclusive_alternatives", {}),
            "improved_content": inclusivity_result.get("improved_content", content)
        }
    
    def validate_compliance(self, content: str, compliance_standards: List[str],
                          industry_regulations: Dict[str, Any]) -> Dict[str, Any]:
        prompt = f"""
        Content: {content}
        Compliance Standards: {compliance_standards}
        Industry Regulations: {industry_regulations}
        
        Validate this content against the specified compliance standards and regulations.
        """
        
        compliance_result = self.nlp_processor.validate_compliance(prompt)
        
        compliance_id = str(uuid.uuid4())
        compliance_record = ComplianceCheck(
            id=compliance_id, content=content, compliance_standards=json.dumps(compliance_standards),
            industry_regulations=json.dumps(industry_regulations), compliance_result=json.dumps(compliance_result),
            created_at=datetime.utcnow()
        )
        self.db.add(compliance_record)
        self.db.commit()
        
        return {
            "compliance_id": compliance_id, "content": content,
            "compliance_standards": compliance_standards,
            "compliance_result": compliance_result,
            "created_at": compliance_record.created_at.isoformat()
        }
    
    def check_data_privacy(self, content: str, privacy_regulations: List[str],
                          data_types: List[str]) -> Dict[str, Any]:
        prompt = f"""
        Content: {content}
        Privacy Regulations: {privacy_regulations}
        Data Types: {data_types}
        
        Check this content for data privacy compliance and potential issues.
        """
        
        privacy_result = self.nlp_processor.check_data_privacy(prompt)
        
        return {
            "content": content, "privacy_regulations": privacy_regulations,
            "data_types": data_types, "privacy_issues": privacy_result.get("privacy_issues", []),
            "compliance_status": privacy_result.get("compliance_status", "unknown"),
            "recommendations": privacy_result.get("recommendations", [])
        }
    
    def review_targeting_ethics(self, targeting_criteria: Dict[str, Any], 
                              target_audience: List[str], industry: str) -> Dict[str, Any]:
        prompt = f"""
        Targeting Criteria: {targeting_criteria}
        Target Audience: {target_audience}
        Industry: {industry}
        
        Review the ethical implications of these targeting criteria.
        """
        
        targeting_result = self.nlp_processor.review_targeting_ethics(prompt)
        
        return {
            "targeting_criteria": targeting_criteria, "target_audience": target_audience,
            "industry": industry, "ethical_concerns": targeting_result.get("ethical_concerns", []),
            "risk_assessment": targeting_result.get("risk_assessment", {}),
            "alternative_suggestions": targeting_result.get("alternative_suggestions", [])
        }
    
    def check_transparency(self, content: str, transparency_requirements: Dict[str, Any]) -> Dict[str, Any]:
        prompt = f"""
        Content: {content}
        Transparency Requirements: {transparency_requirements}
        
        Check this content for transparency compliance and disclosure requirements.
        """
        
        transparency_result = self.nlp_processor.check_transparency(prompt)
        
        return {
            "content": content, "transparency_requirements": transparency_requirements,
            "transparency_score": transparency_result.get("transparency_score", 0.0),
            "missing_disclosures": transparency_result.get("missing_disclosures", []),
            "transparency_improvements": transparency_result.get("transparency_improvements", [])
        }
    
    def validate_consent_mechanisms(self, consent_flow: Dict[str, Any], 
                                  consent_requirements: Dict[str, Any]) -> Dict[str, Any]:
        prompt = f"""
        Consent Flow: {consent_flow}
        Consent Requirements: {consent_requirements}
        
        Validate the consent mechanisms against legal and ethical requirements.
        """
        
        consent_result = self.nlp_processor.validate_consent_mechanisms(prompt)
        
        return {
            "consent_flow": consent_flow, "consent_requirements": consent_requirements,
            "compliance_status": consent_result.get("compliance_status", "unknown"),
            "validation_issues": consent_result.get("validation_issues", []),
            "improvement_suggestions": consent_result.get("improvement_suggestions", [])
        }
    
    def check_accessibility_compliance(self, content: str, accessibility_standards: List[str]) -> Dict[str, Any]:
        prompt = f"""
        Content: {content}
        Accessibility Standards: {accessibility_standards}
        
        Check this content for accessibility compliance and inclusive design.
        """
        
        accessibility_result = self.nlp_processor.check_accessibility_compliance(prompt)
        
        return {
            "content": content, "accessibility_standards": accessibility_standards,
            "accessibility_score": accessibility_result.get("accessibility_score", 0.0),
            "accessibility_issues": accessibility_result.get("accessibility_issues", []),
            "inclusive_design_suggestions": accessibility_result.get("inclusive_design_suggestions", [])
        }
    
    def review_cultural_sensitivity(self, content: str, target_cultures: List[str],
                                  cultural_guidelines: Dict[str, Any]) -> Dict[str, Any]:
        prompt = f"""
        Content: {content}
        Target Cultures: {target_cultures}
        Cultural Guidelines: {cultural_guidelines}
        
        Review this content for cultural sensitivity and appropriateness.
        """
        
        cultural_result = self.nlp_processor.review_cultural_sensitivity(prompt)
        
        return {
            "content": content, "target_cultures": target_cultures,
            "cultural_sensitivity_score": cultural_result.get("cultural_sensitivity_score", 0.0),
            "cultural_concerns": cultural_result.get("cultural_concerns", []),
            "cultural_adaptations": cultural_result.get("cultural_adaptations", [])
        }
    
    def check_age_appropriateness(self, content: str, target_age_groups: List[str],
                                content_rating: str) -> Dict[str, Any]:
        prompt = f"""
        Content: {content}
        Target Age Groups: {target_age_groups}
        Content Rating: {content_rating}
        
        Check this content for age appropriateness and suitability.
        """
        
        age_result = self.nlp_processor.check_age_appropriateness(prompt)
        
        return {
            "content": content, "target_age_groups": target_age_groups,
            "content_rating": content_rating, "age_appropriateness_score": age_result.get("age_appropriateness_score", 0.0),
            "age_concerns": age_result.get("age_concerns", []), "suggested_ratings": age_result.get("suggested_ratings", [])
        }
    
    def validate_environmental_claims(self, content: str, environmental_standards: List[str]) -> Dict[str, Any]:
        prompt = f"""
        Content: {content}
        Environmental Standards: {environmental_standards}
        
        Validate environmental claims and sustainability statements in this content.
        """
        
        environmental_result = self.nlp_processor.validate_environmental_claims(prompt)
        
        return {
            "content": content, "environmental_standards": environmental_standards,
            "environmental_claims": environmental_result.get("environmental_claims", []),
            "validation_status": environmental_result.get("validation_status", "unknown"),
            "supporting_evidence": environmental_result.get("supporting_evidence", [])
        }
    
    def check_health_claims(self, content: str, health_regulations: List[str]) -> Dict[str, Any]:
        prompt = f"""
        Content: {content}
        Health Regulations: {health_regulations}
        
        Check health claims and medical statements for compliance and accuracy.
        """
        
        health_result = self.nlp_processor.check_health_claims(prompt)
        
        return {
            "content": content, "health_regulations": health_regulations,
            "health_claims": health_result.get("health_claims", []),
            "compliance_status": health_result.get("compliance_status", "unknown"),
            "medical_disclaimers": health_result.get("medical_disclaimers", [])
        }
    
    def validate_financial_claims(self, content: str, financial_regulations: List[str]) -> Dict[str, Any]:
        prompt = f"""
        Content: {content}
        Financial Regulations: {financial_regulations}
        
        Validate financial claims and investment statements for compliance.
        """
        
        financial_result = self.nlp_processor.validate_financial_claims(prompt)
        
        return {
            "content": content, "financial_regulations": financial_regulations,
            "financial_claims": financial_result.get("financial_claims", []),
            "compliance_status": financial_result.get("compliance_status", "unknown"),
            "risk_disclosures": financial_result.get("risk_disclosures", [])
        }
    
    def generate_ethical_guidelines(self, industry: str, target_audience: List[str],
                                  guideline_type: str) -> Dict[str, Any]:
        prompt = f"""
        Industry: {industry}
        Target Audience: {target_audience}
        Guideline Type: {guideline_type}
        
        Generate ethical guidelines for this industry and target audience.
        """
        
        guidelines_result = self.nlp_processor.generate_ethical_guidelines(prompt)
        
        guideline_id = str(uuid.uuid4())
        guideline_record = EthicalGuideline(
            id=guideline_id, industry=industry, target_audience=json.dumps(target_audience),
            guideline_type=guideline_type, guidelines=json.dumps(guidelines_result),
            created_at=datetime.utcnow()
        )
        self.db.add(guideline_record)
        self.db.commit()
        
        return {
            "guideline_id": guideline_id, "industry": industry,
            "target_audience": target_audience, "guideline_type": guideline_type,
            "guidelines": guidelines_result, "created_at": guideline_record.created_at.isoformat()
        }
    
    def create_ethical_checklist(self, content_type: str, industry: str,
                               compliance_requirements: Dict[str, Any]) -> Dict[str, Any]:
        prompt = f"""
        Content Type: {content_type}
        Industry: {industry}
        Compliance Requirements: {compliance_requirements}
        
        Create an ethical checklist for this content type and industry.
        """
        
        checklist_result = self.nlp_processor.create_ethical_checklist(prompt)
        
        return {
            "content_type": content_type, "industry": industry,
            "compliance_requirements": compliance_requirements,
            "ethical_checklist": checklist_result.get("checklist", []),
            "checklist_categories": checklist_result.get("categories", [])
        }
    
    def check_competitor_compliance(self, competitor_content: List[Dict[str, Any]],
                                  compliance_standards: List[str]) -> Dict[str, Any]:
        prompt = f"""
        Competitor Content: {competitor_content}
        Compliance Standards: {compliance_standards}
        
        Check competitor content for compliance with ethical standards.
        """
        
        competitor_result = self.nlp_processor.check_competitor_compliance(prompt)
        
        return {
            "competitor_content": competitor_content, "compliance_standards": compliance_standards,
            "compliance_analysis": competitor_result.get("compliance_analysis", {}),
            "ethical_gaps": competitor_result.get("ethical_gaps", []),
            "competitive_advantages": competitor_result.get("competitive_advantages", [])
        }
    
    def review_testimonial_ethics(self, testimonials: List[Dict[str, Any]],
                                testimonial_guidelines: Dict[str, Any]) -> Dict[str, Any]:
        prompt = f"""
        Testimonials: {testimonials}
        Testimonial Guidelines: {testimonial_guidelines}
        
        Review testimonials for ethical compliance and authenticity.
        """
        
        testimonial_result = self.nlp_processor.review_testimonial_ethics(prompt)
        
        return {
            "testimonials": testimonials, "testimonial_guidelines": testimonial_guidelines,
            "authenticity_score": testimonial_result.get("authenticity_score", 0.0),
            "ethical_concerns": testimonial_result.get("ethical_concerns", []),
            "verification_suggestions": testimonial_result.get("verification_suggestions", [])
        }
    
    def get_ethical_analytics(self, timeframe: str = "30d") -> Dict[str, Any]:
        cutoff_date = datetime.utcnow() - timedelta(days=30 if timeframe == "30d" else 7)
        
        total_reviews = self.db.query(EthicalReview).filter(
            EthicalReview.created_at >= cutoff_date
        ).count()
        
        avg_score = self.db.query(EthicalReview).filter(
            EthicalReview.created_at >= cutoff_date
        ).with_entities(EthicalReview.ethical_score).all()
        
        avg_score_value = sum(score[0] for score in avg_score) / len(avg_score) if avg_score else 0.0
        
        compliance_checks = self.db.query(ComplianceCheck).filter(
            ComplianceCheck.created_at >= cutoff_date
        ).count()
        
        return {
            "timeframe": timeframe, "total_reviews": total_reviews,
            "average_ethical_score": avg_score_value, "compliance_checks": compliance_checks,
            "reviews_with_scores": len(avg_score)
        }
    
    def batch_ethical_review(self, content_batch: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results = []
        
        for content_item in content_batch:
            try:
                result = self.review_content_ethics(
                    content_item.get("content", ""),
                    content_item.get("content_type", "general"),
                    content_item.get("target_audience", []),
                    content_item.get("industry", "general"),
                    content_item.get("review_criteria", {})
                )
                results.append({
                    "content_id": content_item.get("id"),
                    "result": result
                })
            except Exception as e:
                results.append({
                    "content_id": content_item.get("id"),
                    "error": str(e)
                })
        
        return results
    
    def _calculate_ethical_score(self, review_result: Dict[str, Any]) -> float:
        score = 0.0
        total_criteria = 0
        
        criteria = [
            "transparency", "accuracy", "inclusivity", "privacy_compliance",
            "cultural_sensitivity", "age_appropriateness", "regulatory_compliance"
        ]
        
        for criterion in criteria:
            if criterion in review_result:
                score += review_result[criterion]
                total_criteria += 1
        
        return score / total_criteria if total_criteria > 0 else 0.0
