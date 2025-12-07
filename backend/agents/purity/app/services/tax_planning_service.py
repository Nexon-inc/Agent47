from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Dict, Any
import json
from datetime import datetime

from ..models import BusinessIdea, TaxStrategy, BusinessModel
from backend.core.ai import get_ai_service_manager, AIServiceManager
from backend.core.event_bus.kafka_manager import KafkaManager
from backend.core.cache.redis_manager import RedisManager

class TaxPlanningService:
    def __init__(self):
        self.ai_service_manager: Optional[AIServiceManager] = None
        self.event_bus = KafkaManager()
        self.redis_manager = RedisManager()
    
    async def develop_tax_strategy(
        self,
        db: AsyncSession,
        business_idea_id: int,
        business_location: str,
        business_structure: str,
        expected_revenue: float,
        tax_year: int
    ) -> Dict[str, Any]:
        try:
            business_idea_result = await db.execute(
                select(BusinessIdea).where(BusinessIdea.id == business_idea_id)
            )
            business_idea = business_idea_result.scalar_one_or_none()
            if not business_idea:
                raise ValueError("Business idea not found")
            
            cache_key = f"tax_strategy:{business_idea_id}:{business_location}:{tax_year}"
            cached_result = await self.redis_manager.get(cache_key)
            if cached_result:
                return json.loads(cached_result)
            
            prompt = self._create_tax_strategy_prompt(
                business_idea, business_location, business_structure, expected_revenue, tax_year
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that helps with tax planning. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            strategy_data = json.loads(ai_response)
            
            tax_strategy = {
                "id": business_idea_id,
                "business_idea_id": business_idea_id,
                "business_location": business_location,
                "business_structure": business_structure,
                "expected_revenue": expected_revenue,
                "tax_year": tax_year,
                "tax_obligations": strategy_data.get("tax_obligations", {}),
                "deduction_opportunities": strategy_data.get("deduction_opportunities", []),
                "tax_credits": strategy_data.get("tax_credits", []),
                "compliance_requirements": strategy_data.get("compliance_requirements", []),
                "optimization_strategies": strategy_data.get("optimization_strategies", []),
                "created_at": datetime.utcnow()
            }
            
            await self.redis_manager.set(cache_key, json.dumps(strategy_data), expire=3600)
            await self.event_bus.publish("purity.tax_strategy_developed", {
                "business_idea_id": business_idea_id,
                "business_location": business_location,
                "tax_year": tax_year,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return tax_strategy
            
        except Exception as e:
            raise e
    
    async def check_tax_compliance(
        self,
        db: AsyncSession,
        business_idea_id: int,
        compliance_requirements: List[str],
        filing_deadlines: Dict[str, Any],
        documentation_needs: List[str]
    ) -> Dict[str, Any]:
        try:
            business_idea_result = await db.execute(
                select(BusinessIdea).where(BusinessIdea.id == business_idea_id)
            )
            business_idea = business_idea_result.scalar_one_or_none()
            if not business_idea:
                raise ValueError("Business idea not found")
            
            prompt = self._create_compliance_check_prompt(
                business_idea, compliance_requirements, filing_deadlines, documentation_needs
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that helps with tax planning. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            compliance_data = json.loads(ai_response)
            
            tax_compliance = {
                "id": business_idea_id,
                "business_idea_id": business_idea_id,
                "compliance_requirements": compliance_requirements,
                "filing_deadlines": filing_deadlines,
                "documentation_needs": documentation_needs,
                "compliance_status": compliance_data.get("compliance_status", {}),
                "required_filings": compliance_data.get("required_filings", []),
                "deadline_tracking": compliance_data.get("deadline_tracking", {}),
                "documentation_checklist": compliance_data.get("documentation_checklist", []),
                "risk_assessment": compliance_data.get("risk_assessment", {}),
                "created_at": datetime.utcnow()
            }
            
            await self.event_bus.publish("purity.tax_compliance_checked", {
                "business_idea_id": business_idea_id,
                "compliance_status": compliance_data.get("compliance_status", {}),
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return tax_compliance
            
        except Exception as e:
            raise e
    
    async def optimize_tax_position(
        self,
        db: AsyncSession,
        business_idea_id: int,
        current_tax_liability: float,
        optimization_goals: List[str],
        risk_tolerance: str
    ) -> Dict[str, Any]:
        try:
            business_idea_result = await db.execute(
                select(BusinessIdea).where(BusinessIdea.id == business_idea_id)
            )
            business_idea = business_idea_result.scalar_one_or_none()
            if not business_idea:
                raise ValueError("Business idea not found")
            
            prompt = self._create_tax_optimization_prompt(
                business_idea, current_tax_liability, optimization_goals, risk_tolerance
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that helps with tax planning. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            optimization_data = json.loads(ai_response)
            
            tax_optimization = {
                "id": business_idea_id,
                "business_idea_id": business_idea_id,
                "current_tax_liability": current_tax_liability,
                "optimization_goals": optimization_goals,
                "risk_tolerance": risk_tolerance,
                "optimization_strategies": optimization_data.get("optimization_strategies", []),
                "tax_savings_projection": optimization_data.get("tax_savings_projection", {}),
                "implementation_plan": optimization_data.get("implementation_plan", {}),
                "risk_mitigation": optimization_data.get("risk_mitigation", []),
                "monitoring_plan": optimization_data.get("monitoring_plan", {}),
                "created_at": datetime.utcnow()
            }
            
            await self.event_bus.publish("purity.tax_position_optimized", {
                "business_idea_id": business_idea_id,
                "current_tax_liability": current_tax_liability,
                "projected_savings": optimization_data.get("tax_savings_projection", {}),
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return tax_optimization
            
        except Exception as e:
            raise e
    
    def _create_tax_strategy_prompt(
        self,
        business_idea: BusinessIdea,
        business_location: str,
        business_structure: str,
        expected_revenue: float,
        tax_year: int
    ) -> str:
        return f"""
        Develop tax strategy for:
        - Business Idea: {business_idea.description}
        - Business Location: {business_location}
        - Business Structure: {business_structure}
        - Expected Revenue: ${expected_revenue:,.2f}
        - Tax Year: {tax_year}
        
        Provide comprehensive tax strategy including:
        1. Tax obligations
        2. Deduction opportunities
        3. Tax credits
        4. Compliance requirements
        5. Optimization strategies
        
        Return the response as a JSON object with the following structure:
        {{
            "tax_obligations": {{
                "income_tax": "Income tax obligations",
                "sales_tax": "Sales tax requirements",
                "payroll_tax": "Payroll tax obligations",
                "property_tax": "Property tax requirements",
                "other_taxes": "Other tax obligations"
            }},
            "deduction_opportunities": [
                "Deduction 1: Business expenses",
                "Deduction 2: Equipment depreciation",
                "Deduction 3: Home office expenses",
                "Deduction 4: Vehicle expenses",
                "Deduction 5: Professional development"
            ],
            "tax_credits": [
                "Credit 1: Research and development credit",
                "Credit 2: Small business health care credit",
                "Credit 3: Work opportunity credit",
                "Credit 4: Energy efficiency credit",
                "Credit 5: Employee retention credit"
            ],
            "compliance_requirements": [
                "Requirement 1: Quarterly estimated payments",
                "Requirement 2: Annual tax return filing",
                "Requirement 3: Sales tax reporting",
                "Requirement 4: Payroll tax deposits",
                "Requirement 5: Record keeping requirements"
            ],
            "optimization_strategies": [
                "Strategy 1: Entity structure optimization",
                "Strategy 2: Timing of income and expenses",
                "Strategy 3: Retirement plan contributions",
                "Strategy 4: Health savings accounts",
                "Strategy 5: Business expense maximization"
            ]
        }}
        """
    
    def _create_compliance_check_prompt(
        self,
        business_idea: BusinessIdea,
        compliance_requirements: List[str],
        filing_deadlines: Dict[str, Any],
        documentation_needs: List[str]
    ) -> str:
        return f"""
        Check tax compliance for:
        - Business Idea: {business_idea.description}
        - Compliance Requirements: {', '.join(compliance_requirements)}
        - Filing Deadlines: {filing_deadlines}
        - Documentation Needs: {', '.join(documentation_needs)}
        
        Provide comprehensive compliance check including:
        1. Compliance status
        2. Required filings
        3. Deadline tracking
        4. Documentation checklist
        5. Risk assessment
        
        Return the response as a JSON object with the following structure:
        {{
            "compliance_status": {{
                "overall_status": "Compliant/Non-compliant",
                "compliance_score": 85.5,
                "pending_requirements": ["Requirement 1", "Requirement 2"],
                "completed_requirements": ["Requirement 1", "Requirement 2"],
                "compliance_notes": "Compliance status notes"
            }},
            "required_filings": [
                {{
                    "filing_type": "Filing type",
                    "deadline": "Filing deadline",
                    "status": "Pending/Completed",
                    "requirements": ["Requirement 1", "Requirement 2"],
                    "penalties": "Potential penalties"
                }}
            ],
            "deadline_tracking": {{
                "upcoming_deadlines": ["Deadline 1", "Deadline 2"],
                "overdue_filings": ["Filing 1", "Filing 2"],
                "deadline_reminders": "Reminder system",
                "extension_options": "Extension options"
            }},
            "documentation_checklist": [
                "Document 1: Financial records",
                "Document 2: Receipts and invoices",
                "Document 3: Bank statements",
                "Document 4: Employment records",
                "Document 5: Asset documentation"
            ],
            "risk_assessment": {{
                "compliance_risks": ["Risk 1", "Risk 2"],
                "penalty_risks": ["Risk 1", "Risk 2"],
                "audit_risks": ["Risk 1", "Risk 2"],
                "mitigation_strategies": ["Strategy 1", "Strategy 2"]
            }}
        }}
        """
    
    def _create_tax_optimization_prompt(
        self,
        business_idea: BusinessIdea,
        current_tax_liability: float,
        optimization_goals: List[str],
        risk_tolerance: str
    ) -> str:
        return f"""
        Optimize tax position for:
        - Business Idea: {business_idea.description}
        - Current Tax Liability: ${current_tax_liability:,.2f}
        - Optimization Goals: {', '.join(optimization_goals)}
        - Risk Tolerance: {risk_tolerance}
        
        Provide comprehensive tax optimization including:
        1. Optimization strategies
        2. Tax savings projection
        3. Implementation plan
        4. Risk mitigation
        5. Monitoring plan
        
        Return the response as a JSON object with the following structure:
        {{
            "optimization_strategies": [
                "Strategy 1: Accelerate deductions",
                "Strategy 2: Defer income recognition",
                "Strategy 3: Maximize retirement contributions",
                "Strategy 4: Optimize entity structure",
                "Strategy 5: Utilize tax credits"
            ],
            "tax_savings_projection": {{
                "projected_savings": 15000.0,
                "savings_percentage": 25.5,
                "implementation_cost": 2000.0,
                "net_savings": 13000.0,
                "roi": 650.0
            }},
            "implementation_plan": {{
                "phase_1": {{
                    "duration": "3 months",
                    "activities": ["Activity 1", "Activity 2"],
                    "cost": "Implementation cost",
                    "expected_savings": "Expected savings"
                }},
                "phase_2": {{
                    "duration": "6 months",
                    "activities": ["Activity 1", "Activity 2"],
                    "cost": "Implementation cost",
                    "expected_savings": "Expected savings"
                }}
            }},
            "risk_mitigation": [
                "Risk 1: Audit risk mitigation",
                "Risk 2: Compliance risk mitigation",
                "Risk 3: Regulatory risk mitigation",
                "Risk 4: Documentation risk mitigation"
            ],
            "monitoring_plan": {{
                "key_metrics": ["Metric 1", "Metric 2"],
                "monitoring_frequency": "Monitoring frequency",
                "review_schedule": "Review schedule",
                "adjustment_triggers": ["Trigger 1", "Trigger 2"]
            }}
        }}
        """
