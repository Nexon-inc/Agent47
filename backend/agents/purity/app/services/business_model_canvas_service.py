from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Dict, Any
import json
from datetime import datetime

from ..models import BusinessIdea, BusinessModel, BusinessModelCanvas
from backend.core.utils.nlp_utils import NLPUtils
from backend.core.event_bus.kafka_manager import KafkaManager
from backend.core.cache.redis_manager import RedisManager

class BusinessModelCanvasService:
    def __init__(self):
        self.nlp_utils = NLPUtils()
        self.event_bus = KafkaManager()
        self.redis_manager = RedisManager()
        self.ai_config = {
            "model": "gpt-4",
            "temperature": 0.5,
            "max_tokens": 3000
        }
    
    async def create_business_model_canvas(
        self,
        db: AsyncSession,
        business_idea_id: int,
        industry: str,
        target_market: str,
        value_proposition: str,
        revenue_streams: List[str]
    ) -> Dict[str, Any]:
        try:
            business_idea_result = await db.execute(
                select(BusinessIdea).where(BusinessIdea.id == business_idea_id)
            )
            business_idea = business_idea_result.scalar_one_or_none()
            if not business_idea:
                raise ValueError("Business idea not found")
            
            cache_key = f"business_model_canvas:{business_idea_id}:{industry}"
            cached_result = await self.redis_manager.get(cache_key)
            if cached_result:
                return json.loads(cached_result)
            
            prompt = self._create_canvas_prompt(
                business_idea, industry, target_market, value_proposition, revenue_streams
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                from backend.core.ai import get_ai_service_manager
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that creates business model canvases. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            canvas_data = json.loads(ai_response)
            
            business_model_canvas = {
                "id": business_idea_id,
                "business_idea_id": business_idea_id,
                "industry": industry,
                "target_market": target_market,
                "value_proposition": value_proposition,
                "revenue_streams": revenue_streams,
                "key_partners": canvas_data.get("key_partners", []),
                "key_activities": canvas_data.get("key_activities", []),
                "key_resources": canvas_data.get("key_resources", []),
                "value_propositions": canvas_data.get("value_propositions", []),
                "customer_relationships": canvas_data.get("customer_relationships", []),
                "channels": canvas_data.get("channels", []),
                "customer_segments": canvas_data.get("customer_segments", []),
                "cost_structure": canvas_data.get("cost_structure", {}),
                "revenue_streams_detailed": canvas_data.get("revenue_streams_detailed", []),
                "created_at": datetime.utcnow()
            }
            
            await self.redis_manager.set(cache_key, json.dumps(canvas_data), expire=3600)
            await self.event_bus.publish("purity.business_model_canvas_created", {
                "business_idea_id": business_idea_id,
                "industry": industry,
                "target_market": target_market,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return business_model_canvas
            
        except Exception as e:
            raise e
    
    async def validate_canvas_coherence(
        self,
        db: AsyncSession,
        business_idea_id: int,
        canvas_components: Dict[str, Any],
        validation_criteria: List[str]
    ) -> Dict[str, Any]:
        try:
            business_idea_result = await db.execute(
                select(BusinessIdea).where(BusinessIdea.id == business_idea_id)
            )
            business_idea = business_idea_result.scalar_one_or_none()
            if not business_idea:
                raise ValueError("Business idea not found")
            
            prompt = self._create_coherence_validation_prompt(
                business_idea, canvas_components, validation_criteria
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                from backend.core.ai import get_ai_service_manager
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that creates business model canvases. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            validation_data = json.loads(ai_response)
            
            coherence_validation = {
                "id": f"coherence_{business_idea_id}",
                "business_idea_id": business_idea_id,
                "canvas_components": canvas_components,
                "validation_criteria": validation_criteria,
                "coherence_score": validation_data.get("coherence_score", 0.0),
                "component_alignment": validation_data.get("component_alignment", {}),
                "inconsistencies": validation_data.get("inconsistencies", []),
                "improvement_suggestions": validation_data.get("improvement_suggestions", []),
                "risk_assessment": validation_data.get("risk_assessment", {}),
                "created_at": datetime.utcnow()
            }
            
            await self.event_bus.publish("purity.canvas_coherence_validated", {
                "business_idea_id": business_idea_id,
                "coherence_score": coherence_validation["coherence_score"],
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return coherence_validation
            
        except Exception as e:
            raise e
    
    def _create_canvas_prompt(
        self,
        business_idea: BusinessIdea,
        industry: str,
        target_market: str,
        value_proposition: str,
        revenue_streams: List[str]
    ) -> str:
        return f"""
        Create business model canvas for:
        - Business Idea: {business_idea.description}
        - Industry: {industry}
        - Target Market: {target_market}
        - Value Proposition: {value_proposition}
        - Revenue Streams: {', '.join(revenue_streams)}
        
        Fill in all 9 components of the Business Model Canvas:
        1. Key Partners
        2. Key Activities
        3. Key Resources
        4. Value Propositions
        5. Customer Relationships
        6. Channels
        7. Customer Segments
        8. Cost Structure
        9. Revenue Streams
        
        Return the response as a JSON object with the following structure:
        {{
            "key_partners": [
                {{
                    "partner_type": "Partner type",
                    "partner_name": "Partner name",
                    "partnership_purpose": "Partnership purpose",
                    "value_contribution": "Value contribution"
                }}
            ],
            "key_activities": [
                {{
                    "activity_name": "Activity name",
                    "activity_description": "Activity description",
                    "importance_level": "High/Medium/Low",
                    "resource_requirements": "Resource requirements"
                }}
            ],
            "key_resources": [
                {{
                    "resource_type": "Resource type",
                    "resource_name": "Resource name",
                    "resource_description": "Resource description",
                    "availability": "Availability status"
                }}
            ],
            "value_propositions": [
                {{
                    "proposition_name": "Value proposition name",
                    "proposition_description": "Value proposition description",
                    "customer_benefit": "Customer benefit",
                    "differentiation_factor": "Differentiation factor"
                }}
            ],
            "customer_relationships": [
                {{
                    "relationship_type": "Relationship type",
                    "relationship_description": "Relationship description",
                    "customer_expectations": "Customer expectations",
                    "relationship_duration": "Relationship duration"
                }}
            ],
            "channels": [
                {{
                    "channel_name": "Channel name",
                    "channel_type": "Channel type",
                    "channel_description": "Channel description",
                    "reach_capability": "Reach capability"
                }}
            ],
            "customer_segments": [
                {{
                    "segment_name": "Customer segment name",
                    "segment_description": "Segment description",
                    "demographics": "Demographic characteristics",
                    "pain_points": "Pain points"
                }}
            ],
            "cost_structure": {{
                "fixed_costs": ["Cost 1", "Cost 2"],
                "variable_costs": ["Cost 1", "Cost 2"],
                "cost_drivers": ["Driver 1", "Driver 2"],
                "economies_of_scale": "Economies of scale potential"
            }},
            "revenue_streams_detailed": [
                {{
                    "stream_name": "Revenue stream name",
                    "stream_type": "Revenue stream type",
                    "pricing_model": "Pricing model",
                    "revenue_potential": "Revenue potential"
                }}
            ]
        }}
        """
    
    def _create_coherence_validation_prompt(
        self,
        business_idea: BusinessIdea,
        canvas_components: Dict[str, Any],
        validation_criteria: List[str]
    ) -> str:
        return f"""
        Validate business model canvas coherence for:
        - Business Idea: {business_idea.description}
        - Canvas Components: {canvas_components}
        - Validation Criteria: {', '.join(validation_criteria)}
        
        Provide comprehensive coherence validation including:
        1. Coherence score
        2. Component alignment
        3. Inconsistencies
        4. Improvement suggestions
        5. Risk assessment
        
        Return the response as a JSON object with the following structure:
        {{
            "coherence_score": 85.5,
            "component_alignment": {{
                "value_proposition_customer_fit": "Value proposition and customer segment alignment",
                "revenue_cost_balance": "Revenue streams and cost structure balance",
                "activities_resources_alignment": "Key activities and key resources alignment",
                "channels_relationships_coherence": "Channels and customer relationships coherence"
            }},
            "inconsistencies": [
                "Inconsistency 1: Value proposition not aligned with customer needs",
                "Inconsistency 2: Revenue streams not supported by cost structure",
                "Inconsistency 3: Key activities not supported by key resources"
            ],
            "improvement_suggestions": [
                "Suggestion 1: Strengthen value proposition alignment",
                "Suggestion 2: Optimize revenue-cost balance",
                "Suggestion 3: Enhance resource-activity alignment"
            ],
            "risk_assessment": {{
                "coherence_risks": ["Risk 1", "Risk 2"],
                "implementation_risks": ["Risk 1", "Risk 2"],
                "market_risks": ["Risk 1", "Risk 2"],
                "mitigation_strategies": ["Strategy 1", "Strategy 2"]
            }}
        }}
        """
