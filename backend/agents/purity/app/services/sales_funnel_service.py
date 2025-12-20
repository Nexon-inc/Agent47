from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Dict, Any
import json
from datetime import datetime

from ..models import BusinessIdea, BusinessModel, CustomerAvatar
from core.ai import get_ai_service_manager, AIServiceManager
from core.event_bus.kafka_manager import KafkaManager
from core.cache.redis_manager import RedisManager

class SalesFunnelService:
    def __init__(self):
        self.ai_service_manager: Optional[AIServiceManager] = None
        self.event_bus = KafkaManager()
        self.redis_manager = RedisManager()
    
    async def generate_sales_funnel(
        self,
        db: AsyncSession,
        business_idea_id: int,
        target_audience: str,
        funnel_type: str,
        conversion_goals: List[str],
        budget_range: str
    ) -> Dict[str, Any]:
        try:
            business_idea_result = await db.execute(
                select(BusinessIdea).where(BusinessIdea.id == business_idea_id)
            )
            business_idea = business_idea_result.scalar_one_or_none()
            if not business_idea:
                raise ValueError("Business idea not found")
            
            cache_key = f"sales_funnel:{business_idea_id}:{funnel_type}"
            cached_result = await self.redis_manager.get(cache_key)
            if cached_result:
                return json.loads(cached_result)
            
            prompt = self._create_sales_funnel_prompt(
                business_idea, target_audience, funnel_type, conversion_goals, budget_range
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                from core.ai import get_ai_service_manager
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that creates sales funnels. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            funnel_data = json.loads(ai_response)
            
            sales_funnel = {
                "id": business_idea_id,
                "business_idea_id": business_idea_id,
                "target_audience": target_audience,
                "funnel_type": funnel_type,
                "conversion_goals": conversion_goals,
                "budget_range": budget_range,
                "funnel_stages": funnel_data.get("funnel_stages", []),
                "lead_magnets": funnel_data.get("lead_magnets", []),
                "email_sequences": funnel_data.get("email_sequences", []),
                "landing_pages": funnel_data.get("landing_pages", []),
                "conversion_tactics": funnel_data.get("conversion_tactics", []),
                "tracking_metrics": funnel_data.get("tracking_metrics", {}),
                "created_at": datetime.utcnow()
            }
            
            await self.redis_manager.set(cache_key, json.dumps(funnel_data), expire=3600)
            await self.event_bus.publish("purity.sales_funnel_generated", {
                "business_idea_id": business_idea_id,
                "funnel_type": funnel_type,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return sales_funnel
            
        except Exception as e:
            raise e
    
    async def create_lead_nurturing_sequence(
        self,
        db: AsyncSession,
        business_idea_id: int,
        lead_stage: str,
        sequence_length: int,
        nurture_goals: List[str],
        personalization_level: str
    ) -> Dict[str, Any]:
        try:
            business_idea_result = await db.execute(
                select(BusinessIdea).where(BusinessIdea.id == business_idea_id)
            )
            business_idea = business_idea_result.scalar_one_or_none()
            if not business_idea:
                raise ValueError("Business idea not found")
            
            prompt = self._create_lead_nurturing_prompt(
                business_idea, lead_stage, sequence_length, nurture_goals, personalization_level
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                from core.ai import get_ai_service_manager
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that creates sales funnels. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            nurturing_data = json.loads(ai_response)
            
            lead_nurturing = {
                "id": business_idea_id,
                "business_idea_id": business_idea_id,
                "lead_stage": lead_stage,
                "sequence_length": sequence_length,
                "nurture_goals": nurture_goals,
                "personalization_level": personalization_level,
                "email_sequence": nurturing_data.get("email_sequence", []),
                "touchpoints": nurturing_data.get("touchpoints", []),
                "content_assets": nurturing_data.get("content_assets", []),
                "timing_strategy": nurturing_data.get("timing_strategy", {}),
                "conversion_triggers": nurturing_data.get("conversion_triggers", []),
                "created_at": datetime.utcnow()
            }
            
            await self.event_bus.publish("purity.lead_nurturing_created", {
                "business_idea_id": business_idea_id,
                "lead_stage": lead_stage,
                "sequence_length": sequence_length,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return lead_nurturing
            
        except Exception as e:
            raise e
    
    async def optimize_conversion_funnel(
        self,
        db: AsyncSession,
        business_idea_id: int,
        current_conversion_rate: float,
        funnel_stages: List[str],
        optimization_goals: List[str]
    ) -> Dict[str, Any]:
        try:
            business_idea_result = await db.execute(
                select(BusinessIdea).where(BusinessIdea.id == business_idea_id)
            )
            business_idea = business_idea_result.scalar_one_or_none()
            if not business_idea:
                raise ValueError("Business idea not found")
            
            prompt = self._create_conversion_optimization_prompt(
                business_idea, current_conversion_rate, funnel_stages, optimization_goals
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                from core.ai import get_ai_service_manager
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that creates sales funnels. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            optimization_data = json.loads(ai_response)
            
            conversion_optimization = {
                "id": business_idea_id,
                "business_idea_id": business_idea_id,
                "current_conversion_rate": current_conversion_rate,
                "funnel_stages": funnel_stages,
                "optimization_goals": optimization_goals,
                "optimization_strategies": optimization_data.get("optimization_strategies", []),
                "a_b_testing_ideas": optimization_data.get("a_b_testing_ideas", []),
                "conversion_barriers": optimization_data.get("conversion_barriers", []),
                "improvement_recommendations": optimization_data.get("improvement_recommendations", []),
                "expected_improvements": optimization_data.get("expected_improvements", {}),
                "created_at": datetime.utcnow()
            }
            
            await self.event_bus.publish("purity.conversion_optimization_created", {
                "business_idea_id": business_idea_id,
                "current_conversion_rate": current_conversion_rate,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return conversion_optimization
            
        except Exception as e:
            raise e
    
    async def create_funnel_analytics(
        self,
        db: AsyncSession,
        business_idea_id: int,
        funnel_metrics: Dict[str, Any],
        tracking_period: str
    ) -> Dict[str, Any]:
        try:
            business_idea_result = await db.execute(
                select(BusinessIdea).where(BusinessIdea.id == business_idea_id)
            )
            business_idea = business_idea_result.scalar_one_or_none()
            if not business_idea:
                raise ValueError("Business idea not found")
            
            prompt = self._create_funnel_analytics_prompt(
                business_idea, funnel_metrics, tracking_period
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                from core.ai import get_ai_service_manager
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that creates sales funnels. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            analytics_data = json.loads(ai_response)
            
            funnel_analytics = {
                "id": business_idea_id,
                "business_idea_id": business_idea_id,
                "funnel_metrics": funnel_metrics,
                "tracking_period": tracking_period,
                "performance_analysis": analytics_data.get("performance_analysis", {}),
                "bottleneck_identification": analytics_data.get("bottleneck_identification", []),
                "trend_analysis": analytics_data.get("trend_analysis", {}),
                "optimization_opportunities": analytics_data.get("optimization_opportunities", []),
                "roi_calculations": analytics_data.get("roi_calculations", {}),
                "created_at": datetime.utcnow()
            }
            
            await self.event_bus.publish("purity.funnel_analytics_created", {
                "business_idea_id": business_idea_id,
                "tracking_period": tracking_period,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return funnel_analytics
            
        except Exception as e:
            raise e
    
    def _create_sales_funnel_prompt(
        self,
        business_idea: BusinessIdea,
        target_audience: str,
        funnel_type: str,
        conversion_goals: List[str],
        budget_range: str
    ) -> str:
        return f"""
        Generate sales funnel for:
        - Business Idea: {business_idea.description}
        - Target Audience: {target_audience}
        - Funnel Type: {funnel_type}
        - Conversion Goals: {', '.join(conversion_goals)}
        - Budget Range: {budget_range}
        
        Create comprehensive sales funnel including:
        1. Funnel stages
        2. Lead magnets
        3. Email sequences
        4. Landing pages
        5. Conversion tactics
        6. Tracking metrics
        
        Return the response as a JSON object with the following structure:
        {{
            "funnel_stages": [
                {{
                    "stage": "Awareness",
                    "description": "Stage description",
                    "tactics": ["Tactic 1", "Tactic 2"],
                    "content_types": ["Content 1", "Content 2"]
                }}
            ],
            "lead_magnets": [
                {{
                    "type": "Lead magnet type",
                    "title": "Lead magnet title",
                    "description": "Lead magnet description",
                    "delivery_method": "Delivery method"
                }}
            ],
            "email_sequences": [
                {{
                    "sequence_name": "Sequence name",
                    "emails": [
                        {{
                            "subject": "Email subject",
                            "content": "Email content",
                            "timing": "Send timing"
                        }}
                    ]
                }}
            ],
            "landing_pages": [
                {{
                    "page_type": "Page type",
                    "headline": "Page headline",
                    "content": "Page content",
                    "cta": "Call to action"
                }}
            ],
            "conversion_tactics": [
                "Tactic 1: Urgency creation",
                "Tactic 2: Social proof",
                "Tactic 3: Risk reversal"
            ],
            "tracking_metrics": {{
                "conversion_rate": "Conversion rate tracking",
                "lead_quality": "Lead quality metrics",
                "roi": "ROI tracking"
            }}
        }}
        """
    
    def _create_lead_nurturing_prompt(
        self,
        business_idea: BusinessIdea,
        lead_stage: str,
        sequence_length: int,
        nurture_goals: List[str],
        personalization_level: str
    ) -> str:
        return f"""
        Create lead nurturing sequence for:
        - Business Idea: {business_idea.description}
        - Lead Stage: {lead_stage}
        - Sequence Length: {sequence_length} emails
        - Nurture Goals: {', '.join(nurture_goals)}
        - Personalization Level: {personalization_level}
        
        Develop comprehensive lead nurturing including:
        1. Email sequence
        2. Touchpoints
        3. Content assets
        4. Timing strategy
        5. Conversion triggers
        
        Return the response as a JSON object with the following structure:
        {{
            "email_sequence": [
                {{
                    "email_number": 1,
                    "subject": "Email subject",
                    "content": "Email content",
                    "timing": "Send timing",
                    "goal": "Email goal"
                }}
            ],
            "touchpoints": [
                {{
                    "type": "Touchpoint type",
                    "content": "Touchpoint content",
                    "timing": "Touchpoint timing"
                }}
            ],
            "content_assets": [
                {{
                    "type": "Content type",
                    "title": "Content title",
                    "description": "Content description"
                }}
            ],
            "timing_strategy": {{
                "frequency": "Email frequency",
                "best_times": ["Time 1", "Time 2"],
                "spacing": "Email spacing"
            }},
            "conversion_triggers": [
                "Trigger 1: Engagement milestone",
                "Trigger 2: Behavior pattern",
                "Trigger 3: Time-based trigger"
            ]
        }}
        """
    
    def _create_conversion_optimization_prompt(
        self,
        business_idea: BusinessIdea,
        current_conversion_rate: float,
        funnel_stages: List[str],
        optimization_goals: List[str]
    ) -> str:
        return f"""
        Optimize conversion funnel for:
        - Business Idea: {business_idea.description}
        - Current Conversion Rate: {current_conversion_rate}%
        - Funnel Stages: {', '.join(funnel_stages)}
        - Optimization Goals: {', '.join(optimization_goals)}
        
        Provide comprehensive optimization including:
        1. Optimization strategies
        2. A/B testing ideas
        3. Conversion barriers
        4. Improvement recommendations
        5. Expected improvements
        
        Return the response as a JSON object with the following structure:
        {{
            "optimization_strategies": [
                "Strategy 1: Improve landing page design",
                "Strategy 2: Optimize call-to-action buttons",
                "Strategy 3: Enhance value proposition"
            ],
            "a_b_testing_ideas": [
                {{
                    "test_name": "Test name",
                    "hypothesis": "Test hypothesis",
                    "variants": ["Variant A", "Variant B"],
                    "success_metric": "Success metric"
                }}
            ],
            "conversion_barriers": [
                "Barrier 1: Complex checkout process",
                "Barrier 2: Lack of trust signals",
                "Barrier 3: Poor mobile experience"
            ],
            "improvement_recommendations": [
                "Recommendation 1: Simplify checkout",
                "Recommendation 2: Add testimonials",
                "Recommendation 3: Improve mobile design"
            ],
            "expected_improvements": {{
                "conversion_rate_increase": "Expected increase",
                "revenue_impact": "Revenue impact",
                "implementation_timeline": "Timeline"
            }}
        }}
        """
    
    def _create_funnel_analytics_prompt(
        self,
        business_idea: BusinessIdea,
        funnel_metrics: Dict[str, Any],
        tracking_period: str
    ) -> str:
        return f"""
        Analyze funnel analytics for:
        - Business Idea: {business_idea.description}
        - Funnel Metrics: {funnel_metrics}
        - Tracking Period: {tracking_period}
        
        Provide comprehensive analytics including:
        1. Performance analysis
        2. Bottleneck identification
        3. Trend analysis
        4. Optimization opportunities
        5. ROI calculations
        
        Return the response as a JSON object with the following structure:
        {{
            "performance_analysis": {{
                "overall_performance": "Overall performance assessment",
                "stage_performance": "Stage-by-stage analysis",
                "key_insights": ["Insight 1", "Insight 2"]
            }},
            "bottleneck_identification": [
                "Bottleneck 1: Awareness to consideration",
                "Bottleneck 2: Consideration to decision",
                "Bottleneck 3: Decision to purchase"
            ],
            "trend_analysis": {{
                "conversion_trends": "Conversion trend analysis",
                "traffic_trends": "Traffic trend analysis",
                "revenue_trends": "Revenue trend analysis"
            }},
            "optimization_opportunities": [
                "Opportunity 1: Improve top-of-funnel",
                "Opportunity 2: Optimize middle-funnel",
                "Opportunity 3: Enhance bottom-of-funnel"
            ],
            "roi_calculations": {{
                "funnel_roi": "Funnel ROI calculation",
                "stage_roi": "Stage ROI breakdown",
                "optimization_roi": "Optimization ROI projection"
            }}
        }}
        """
