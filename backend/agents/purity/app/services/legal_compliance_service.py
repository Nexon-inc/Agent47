from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Dict, Any
import json
from datetime import datetime, timedelta

from ..models import BusinessIdea, LegalRequirement, BusinessModel
from backend.core.ai import get_ai_service_manager, AIServiceManager
from backend.core.event_bus.kafka_manager import KafkaManager
from backend.core.cache.redis_manager import RedisManager

class LegalComplianceService:
    def __init__(self):
        self.ai_service_manager: Optional[AIServiceManager] = None
        self.event_bus = KafkaManager()
        self.redis_manager = RedisManager()
    
    async def check_legal_requirements(
        self,
        db: AsyncSession,
        business_idea_id: int,
        business_location: str,
        business_type: str,
        industry: str,
        expected_annual_revenue: float,
        employee_count: int,
        has_international_operations: bool,
        handles_personal_data: bool,
        sells_products_online: bool
    ) -> LegalRequirement:
        try:
            business_idea_result = await db.execute(
                select(BusinessIdea).where(BusinessIdea.id == business_idea_id)
            )
            business_idea = business_idea_result.scalar_one_or_none()
            if not business_idea:
                raise ValueError("Business idea not found")
            
            cache_key = f"legal_requirements:{business_location}:{business_type}:{industry}"
            cached_result = await self.redis_manager.get(cache_key)
            if cached_result:
                return json.loads(cached_result)
            
            prompt = self._create_legal_requirements_prompt(
                business_location, business_type, industry, expected_annual_revenue,
                employee_count, has_international_operations, handles_personal_data,
                sells_products_online, business_idea.description
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                from backend.core.ai import get_ai_service_manager
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that helps with legal compliance. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            legal_data = json.loads(ai_response)
            
            legal_requirement = LegalRequirement(
                business_idea_id=business_idea_id,
                business_location=business_location,
                business_type=business_type,
                industry=industry,
                required_licenses=json.dumps(legal_data.get("required_licenses", [])),
                required_permits=json.dumps(legal_data.get("required_permits", [])),
                tax_obligations=json.dumps(legal_data.get("tax_obligations", [])),
                compliance_requirements=json.dumps(legal_data.get("compliance_requirements", [])),
                privacy_requirements=json.dumps(legal_data.get("privacy_requirements", [])),
                intellectual_property_needs=json.dumps(legal_data.get("intellectual_property_needs", [])),
                risk_assessment=legal_data.get("risk_assessment", ""),
                compliance_score=legal_data.get("compliance_score", 0.0),
                estimated_compliance_cost=legal_data.get("estimated_compliance_cost", 0.0)
            )
            
            db.add(legal_requirement)
            await db.commit()
            await db.refresh(legal_requirement)
            
            await self.redis_manager.set(cache_key, json.dumps(legal_data), expire=3600)
            await self.event_bus.publish("purity.legal_requirements_checked", {
                "business_idea_id": business_idea_id,
                "compliance_score": legal_requirement.compliance_score,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return legal_requirement
            
        except Exception as e:
            await db.rollback()
            raise e
    
    async def validate_compliance(
        self,
        db: AsyncSession,
        legal_requirement_id: int,
        current_licenses: List[str],
        current_permits: List[str],
        compliance_status: Dict[str, Any],
        audit_findings: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        try:
            legal_req_result = await db.execute(
                select(LegalRequirement).where(LegalRequirement.id == legal_requirement_id)
            )
            legal_requirement = legal_req_result.scalar_one_or_none()
            if not legal_requirement:
                raise ValueError("Legal requirement not found")
            
            required_licenses = json.loads(legal_requirement.required_licenses)
            required_permits = json.loads(legal_requirement.required_permits)
            
            missing_licenses = [license for license in required_licenses if license not in current_licenses]
            missing_permits = [permit for permit in required_permits if permit not in current_permits]
            
            compliance_score = self._calculate_compliance_score(
                len(missing_licenses), len(missing_permits), compliance_status, audit_findings
            )
            
            validation_result = {
                "id": legal_requirement_id,
                "compliance_score": compliance_score,
                "missing_requirements": missing_licenses + missing_permits,
                "compliance_gaps": self._identify_compliance_gaps(compliance_status),
                "recommendations": self._generate_compliance_recommendations(
                    missing_licenses, missing_permits, compliance_status
                ),
                "risk_level": self._assess_risk_level(compliance_score),
                "next_audit_date": datetime.utcnow() + timedelta(days=90),
                "created_at": datetime.utcnow()
            }
            
            await self.event_bus.publish("purity.compliance_validated", {
                "legal_requirement_id": legal_requirement_id,
                "compliance_score": compliance_score,
                "risk_level": validation_result["risk_level"],
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return validation_result
            
        except Exception as e:
            raise e
    
    async def get_regulatory_guidance(
        self,
        db: AsyncSession,
        business_idea_id: int,
        specific_concern: str,
        industry_regulations: List[str],
        compliance_questions: List[str]
    ) -> Dict[str, Any]:
        try:
            business_idea_result = await db.execute(
                select(BusinessIdea).where(BusinessIdea.id == business_idea_id)
            )
            business_idea = business_idea_result.scalar_one_or_none()
            if not business_idea:
                raise ValueError("Business idea not found")
            
            prompt = self._create_regulatory_guidance_prompt(
                business_idea.description, specific_concern, industry_regulations, compliance_questions
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                from backend.core.ai import get_ai_service_manager
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that helps with legal compliance. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            guidance_data = json.loads(ai_response)
            
            guidance_result = {
                "id": business_idea_id,
                "guidance_summary": guidance_data.get("guidance_summary", ""),
                "regulatory_requirements": guidance_data.get("regulatory_requirements", []),
                "compliance_timeline": guidance_data.get("compliance_timeline", []),
                "risk_mitigation_strategies": guidance_data.get("risk_mitigation_strategies", []),
                "expert_recommendations": guidance_data.get("expert_recommendations", []),
                "created_at": datetime.utcnow()
            }
            
            await self.event_bus.publish("purity.regulatory_guidance_requested", {
                "business_idea_id": business_idea_id,
                "specific_concern": specific_concern,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return guidance_result
            
        except Exception as e:
            raise e
    
    async def update_legal_requirement(
        self,
        db: AsyncSession,
        requirement_id: int,
        business_location: str,
        business_type: str,
        industry: str,
        expected_annual_revenue: float,
        employee_count: int,
        has_international_operations: bool,
        handles_personal_data: bool,
        sells_products_online: bool
    ) -> LegalRequirement:
        try:
            result = await db.execute(
                select(LegalRequirement).where(LegalRequirement.id == requirement_id)
            )
            legal_requirement = result.scalar_one_or_none()
            if not legal_requirement:
                raise ValueError("Legal requirement not found")
            
            prompt = self._create_legal_requirements_prompt(
                business_location, business_type, industry, expected_annual_revenue,
                employee_count, has_international_operations, handles_personal_data,
                sells_products_online, ""
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                from backend.core.ai import get_ai_service_manager
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that helps with legal compliance. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            legal_data = json.loads(ai_response)
            
            legal_requirement.business_location = business_location
            legal_requirement.business_type = business_type
            legal_requirement.industry = industry
            legal_requirement.required_licenses = json.dumps(legal_data.get("required_licenses", []))
            legal_requirement.required_permits = json.dumps(legal_data.get("required_permits", []))
            legal_requirement.tax_obligations = json.dumps(legal_data.get("tax_obligations", []))
            legal_requirement.compliance_requirements = json.dumps(legal_data.get("compliance_requirements", []))
            legal_requirement.privacy_requirements = json.dumps(legal_data.get("privacy_requirements", []))
            legal_requirement.intellectual_property_needs = json.dumps(legal_data.get("intellectual_property_needs", []))
            legal_requirement.risk_assessment = legal_data.get("risk_assessment", "")
            legal_requirement.compliance_score = legal_data.get("compliance_score", 0.0)
            legal_requirement.estimated_compliance_cost = legal_data.get("estimated_compliance_cost", 0.0)
            legal_requirement.updated_at = datetime.utcnow()
            
            await db.commit()
            await db.refresh(legal_requirement)
            
            await self.event_bus.publish("purity.legal_requirement_updated", {
                "requirement_id": requirement_id,
                "compliance_score": legal_requirement.compliance_score,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return legal_requirement
            
        except Exception as e:
            await db.rollback()
            raise e
    
    def _create_legal_requirements_prompt(
        self,
        business_location: str,
        business_type: str,
        industry: str,
        expected_annual_revenue: float,
        employee_count: int,
        has_international_operations: bool,
        handles_personal_data: bool,
        sells_products_online: bool,
        business_description: str
    ) -> str:
        return f"""
        Analyze legal requirements for a business with the following characteristics:
        - Location: {business_location}
        - Business Type: {business_type}
        - Industry: {industry}
        - Expected Annual Revenue: ${expected_annual_revenue:,.2f}
        - Employee Count: {employee_count}
        - International Operations: {has_international_operations}
        - Handles Personal Data: {handles_personal_data}
        - Sells Products Online: {sells_products_online}
        - Business Description: {business_description}
        
        Provide a comprehensive legal analysis including:
        1. Required licenses and permits
        2. Tax obligations
        3. Compliance requirements
        4. Privacy requirements (if applicable)
        5. Intellectual property needs
        6. Risk assessment
        7. Compliance score (0-100)
        8. Estimated compliance costs
        
        Return the response as a JSON object with the following structure:
        {{
            "required_licenses": [{{"name": "License Name", "cost": 1000, "timeline": "30 days"}}],
            "required_permits": [{{"name": "Permit Name", "cost": 500, "timeline": "15 days"}}],
            "tax_obligations": [{{"type": "Tax Type", "rate": "5%", "frequency": "monthly"}}],
            "compliance_requirements": [{{"requirement": "Requirement Description", "deadline": "90 days"}}],
            "privacy_requirements": [{{"requirement": "Privacy Requirement", "impact": "high"}}],
            "intellectual_property_needs": [{{"type": "IP Type", "cost": 2000, "priority": "high"}}],
            "risk_assessment": "Comprehensive risk assessment description",
            "compliance_score": 85.5,
            "estimated_compliance_cost": 15000.0
        }}
        """
    
    def _create_regulatory_guidance_prompt(
        self,
        business_description: str,
        specific_concern: str,
        industry_regulations: List[str],
        compliance_questions: List[str]
    ) -> str:
        return f"""
        Provide regulatory guidance for a business with the following context:
        - Business Description: {business_description}
        - Specific Concern: {specific_concern}
        - Industry Regulations: {', '.join(industry_regulations)}
        - Compliance Questions: {', '.join(compliance_questions)}
        
        Provide comprehensive regulatory guidance including:
        1. Guidance summary
        2. Regulatory requirements
        3. Compliance timeline
        4. Risk mitigation strategies
        5. Expert recommendations
        
        Return the response as a JSON object with the following structure:
        {{
            "guidance_summary": "Summary of regulatory guidance",
            "regulatory_requirements": [{{"requirement": "Requirement", "deadline": "Date", "priority": "high"}}],
            "compliance_timeline": [{{"phase": "Phase", "duration": "30 days", "activities": ["Activity 1", "Activity 2"]}}],
            "risk_mitigation_strategies": ["Strategy 1", "Strategy 2"],
            "expert_recommendations": ["Recommendation 1", "Recommendation 2"]
        }}
        """
    
    def _calculate_compliance_score(
        self,
        missing_licenses: int,
        missing_permits: int,
        compliance_status: Dict[str, Any],
        audit_findings: Optional[List[str]] = None
    ) -> float:
        base_score = 100.0
        license_penalty = missing_licenses * 10.0
        permit_penalty = missing_permits * 5.0
        audit_penalty = len(audit_findings or []) * 3.0
        
        compliance_penalty = 0.0
        for status in compliance_status.values():
            if not status.get("compliant", False):
                compliance_penalty += 5.0
        
        final_score = base_score - license_penalty - permit_penalty - audit_penalty - compliance_penalty
        return max(0.0, min(100.0, final_score))
    
    def _identify_compliance_gaps(self, compliance_status: Dict[str, Any]) -> List[Dict[str, Any]]:
        gaps = []
        for requirement, status in compliance_status.items():
            if not status.get("compliant", False):
                gaps.append({
                    "requirement": requirement,
                    "current_status": status.get("status", "non-compliant"),
                    "deadline": status.get("deadline"),
                    "severity": status.get("severity", "medium")
                })
        return gaps
    
    def _generate_compliance_recommendations(
        self,
        missing_licenses: List[str],
        missing_permits: List[str],
        compliance_status: Dict[str, Any]
    ) -> List[str]:
        recommendations = []
        
        if missing_licenses:
            recommendations.append(f"Obtain missing licenses: {', '.join(missing_licenses)}")
        
        if missing_permits:
            recommendations.append(f"Apply for missing permits: {', '.join(missing_permits)}")
        
        for requirement, status in compliance_status.items():
            if not status.get("compliant", False):
                recommendations.append(f"Address compliance issue: {requirement}")
        
        if not recommendations:
            recommendations.append("Maintain current compliance status")
        
        return recommendations
    
    def _assess_risk_level(self, compliance_score: float) -> str:
        if compliance_score >= 90:
            return "low"
        elif compliance_score >= 70:
            return "medium"
        else:
            return "high"
