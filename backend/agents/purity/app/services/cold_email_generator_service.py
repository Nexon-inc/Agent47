from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Dict, Any
import json
from datetime import datetime

from ..models import PurityBusinessIdea, PurityBusinessModel, PurityCustomerAvatar
from core.ai import get_ai_service_manager, AIServiceManager
from core.event_bus.kafka_manager import KafkaManager
from core.cache.redis_manager import RedisManager

class ColdEmailGeneratorService:
    def __init__(self):
        self.ai_service_manager: Optional[AIServiceManager] = None
        self.event_bus = KafkaManager()
        self.redis_manager = RedisManager()
    
    async def generate_cold_email(
        self,
        db: AsyncSession,
        business_idea_id: int,
        target_audience: str,
        email_purpose: str,
        value_proposition: str,
        call_to_action: str,
        tone: str
    ) -> Dict[str, Any]:
        try:
            business_idea_result = await db.execute(
                select(PurityBusinessIdea).where(PurityBusinessIdea.id == business_idea_id)
            )
            business_idea = business_idea_result.scalar_one_or_none()
            if not business_idea:
                raise ValueError("Business idea not found")
            
            cache_key = f"cold_email:{business_idea_id}:{target_audience}:{email_purpose}"
            cached_result = await self.redis_manager.get(cache_key)
            if cached_result:
                return json.loads(cached_result)
            
            prompt = self._create_cold_email_prompt(
                business_idea, target_audience, email_purpose, value_proposition, call_to_action, tone
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                from core.ai import get_ai_service_manager
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that generates cold emails. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=1500, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            email_data = json.loads(ai_response)
            
            cold_email = {
                "id": business_idea_id,
                "business_idea_id": business_idea_id,
                "target_audience": target_audience,
                "email_purpose": email_purpose,
                "value_proposition": value_proposition,
                "call_to_action": call_to_action,
                "tone": tone,
                "subject_line": email_data.get("subject_line", ""),
                "opening_line": email_data.get("opening_line", ""),
                "body_content": email_data.get("body_content", ""),
                "closing": email_data.get("closing", ""),
                "personalization_tokens": email_data.get("personalization_tokens", []),
                "email_variations": email_data.get("email_variations", []),
                "created_at": datetime.utcnow()
            }
            
            await self.redis_manager.set(cache_key, json.dumps(email_data), expire=3600)
            await self.event_bus.publish("purity.cold_email_generated", {
                "business_idea_id": business_idea_id,
                "target_audience": target_audience,
                "email_purpose": email_purpose,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return cold_email
            
        except Exception as e:
            raise e
    
    async def create_outreach_sequence(
        self,
        db: AsyncSession,
        business_idea_id: int,
        sequence_length: int,
        target_audience: str,
        sequence_goals: List[str],
        follow_up_strategy: str
    ) -> Dict[str, Any]:
        try:
            business_idea_result = await db.execute(
                select(PurityBusinessIdea).where(PurityBusinessIdea.id == business_idea_id)
            )
            business_idea = business_idea_result.scalar_one_or_none()
            if not business_idea:
                raise ValueError("Business idea not found")
            
            prompt = self._create_outreach_sequence_prompt(
                business_idea, sequence_length, target_audience, sequence_goals, follow_up_strategy
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                from core.ai import get_ai_service_manager
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that generates cold emails. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=1500, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            sequence_data = json.loads(ai_response)
            
            outreach_sequence = {
                "id": business_idea_id,
                "business_idea_id": business_idea_id,
                "sequence_length": sequence_length,
                "target_audience": target_audience,
                "sequence_goals": sequence_goals,
                "follow_up_strategy": follow_up_strategy,
                "email_sequence": sequence_data.get("email_sequence", []),
                "timing_strategy": sequence_data.get("timing_strategy", {}),
                "response_handling": sequence_data.get("response_handling", {}),
                "success_metrics": sequence_data.get("success_metrics", {}),
                "created_at": datetime.utcnow()
            }
            
            await self.event_bus.publish("purity.outreach_sequence_created", {
                "business_idea_id": business_idea_id,
                "sequence_length": sequence_length,
                "target_audience": target_audience,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return outreach_sequence
            
        except Exception as e:
            raise e
    
    async def generate_follow_up_strategy(
        self,
        db: AsyncSession,
        business_idea_id: int,
        response_type: str,
        follow_up_count: int,
        escalation_strategy: str
    ) -> Dict[str, Any]:
        try:
            business_idea_result = await db.execute(
                select(PurityBusinessIdea).where(PurityBusinessIdea.id == business_idea_id)
            )
            business_idea = business_idea_result.scalar_one_or_none()
            if not business_idea:
                raise ValueError("Business idea not found")
            
            prompt = self._create_follow_up_strategy_prompt(
                business_idea, response_type, follow_up_count, escalation_strategy
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                from core.ai import get_ai_service_manager
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that generates cold emails. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=1500, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            strategy_data = json.loads(ai_response)
            
            follow_up_strategy = {
                "id": business_idea_id,
                "business_idea_id": business_idea_id,
                "response_type": response_type,
                "follow_up_count": follow_up_count,
                "escalation_strategy": escalation_strategy,
                "follow_up_emails": strategy_data.get("follow_up_emails", []),
                "timing_intervals": strategy_data.get("timing_intervals", {}),
                "escalation_tactics": strategy_data.get("escalation_tactics", []),
                "response_templates": strategy_data.get("response_templates", {}),
                "created_at": datetime.utcnow()
            }
            
            await self.event_bus.publish("purity.follow_up_strategy_generated", {
                "business_idea_id": business_idea_id,
                "response_type": response_type,
                "follow_up_count": follow_up_count,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return follow_up_strategy
            
        except Exception as e:
            raise e
    
    async def create_personalization_templates(
        self,
        db: AsyncSession,
        business_idea_id: int,
        target_industries: List[str],
        personalization_level: str,
        research_sources: List[str]
    ) -> Dict[str, Any]:
        try:
            business_idea_result = await db.execute(
                select(PurityBusinessIdea).where(PurityBusinessIdea.id == business_idea_id)
            )
            business_idea = business_idea_result.scalar_one_or_none()
            if not business_idea:
                raise ValueError("Business idea not found")
            
            prompt = self._create_personalization_templates_prompt(
                business_idea, target_industries, personalization_level, research_sources
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                from core.ai import get_ai_service_manager
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that generates cold emails. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=1500, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            templates_data = json.loads(ai_response)
            
            personalization_templates = {
                "id": business_idea_id,
                "business_idea_id": business_idea_id,
                "target_industries": target_industries,
                "personalization_level": personalization_level,
                "research_sources": research_sources,
                "industry_templates": templates_data.get("industry_templates", {}),
                "personalization_hooks": templates_data.get("personalization_hooks", []),
                "research_guidelines": templates_data.get("research_guidelines", {}),
                "customization_tips": templates_data.get("customization_tips", []),
                "created_at": datetime.utcnow()
            }
            
            await self.event_bus.publish("purity.personalization_templates_created", {
                "business_idea_id": business_idea_id,
                "target_industries": target_industries,
                "personalization_level": personalization_level,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return personalization_templates
            
        except Exception as e:
            raise e
    
    def _create_cold_email_prompt(
        self,
        business_idea: PurityBusinessIdea,
        target_audience: str,
        email_purpose: str,
        value_proposition: str,
        call_to_action: str,
        tone: str
    ) -> str:
        return f"""
        Generate cold email for:
        - Business Idea: {business_idea.description}
        - Target Audience: {target_audience}
        - Email Purpose: {email_purpose}
        - Value Proposition: {value_proposition}
        - Call to Action: {call_to_action}
        - Tone: {tone}
        
        Create compelling cold email including:
        1. Subject line
        2. Opening line
        3. Body content
        4. Closing
        5. Personalization tokens
        6. Email variations
        
        Return the response as a JSON object with the following structure:
        {{
            "subject_line": "Compelling subject line",
            "opening_line": "Attention-grabbing opening",
            "body_content": "Main email content with value proposition",
            "closing": "Professional closing",
            "personalization_tokens": [
                "{{company_name}}",
                "{{recipient_name}}",
                "{{industry}}",
                "{{recent_achievement}}"
            ],
            "email_variations": [
                {{
                    "variation_name": "Variation 1",
                    "subject_line": "Alternative subject line",
                    "body_content": "Alternative body content"
                }}
            ]
        }}
        """
    
    def _create_outreach_sequence_prompt(
        self,
        business_idea: PurityBusinessIdea,
        sequence_length: int,
        target_audience: str,
        sequence_goals: List[str],
        follow_up_strategy: str
    ) -> str:
        return f"""
        Create outreach sequence for:
        - Business Idea: {business_idea.description}
        - Sequence Length: {sequence_length} emails
        - Target Audience: {target_audience}
        - Sequence Goals: {', '.join(sequence_goals)}
        - Follow-up Strategy: {follow_up_strategy}
        
        Develop comprehensive outreach sequence including:
        1. Email sequence
        2. Timing strategy
        3. Response handling
        4. Success metrics
        
        Return the response as a JSON object with the following structure:
        {{
            "email_sequence": [
                {{
                    "email_number": 1,
                    "subject_line": "Subject line",
                    "content": "Email content",
                    "purpose": "Email purpose",
                    "timing": "Send timing"
                }}
            ],
            "timing_strategy": {{
                "initial_email": "Day 1",
                "follow_up_1": "Day 3",
                "follow_up_2": "Day 7",
                "follow_up_3": "Day 14"
            }},
            "response_handling": {{
                "positive_response": "Response template",
                "negative_response": "Response template",
                "no_response": "Follow-up strategy"
            }},
            "success_metrics": {{
                "open_rate_target": "Target open rate",
                "reply_rate_target": "Target reply rate",
                "conversion_rate_target": "Target conversion rate"
            }}
        }}
        """
    
    def _create_follow_up_strategy_prompt(
        self,
        business_idea: PurityBusinessIdea,
        response_type: str,
        follow_up_count: int,
        escalation_strategy: str
    ) -> str:
        return f"""
        Generate follow-up strategy for:
        - Business Idea: {business_idea.description}
        - Response Type: {response_type}
        - Follow-up Count: {follow_up_count}
        - Escalation Strategy: {escalation_strategy}
        
        Create comprehensive follow-up strategy including:
        1. Follow-up emails
        2. Timing intervals
        3. Escalation tactics
        4. Response templates
        
        Return the response as a JSON object with the following structure:
        {{
            "follow_up_emails": [
                {{
                    "follow_up_number": 1,
                    "subject_line": "Follow-up subject",
                    "content": "Follow-up content",
                    "timing": "Send timing",
                    "escalation_level": "Escalation level"
                }}
            ],
            "timing_intervals": {{
                "first_follow_up": "3 days",
                "second_follow_up": "7 days",
                "third_follow_up": "14 days",
                "final_follow_up": "30 days"
            }},
            "escalation_tactics": [
                "Tactic 1: Add urgency",
                "Tactic 2: Provide additional value",
                "Tactic 3: Change communication channel"
            ],
            "response_templates": {{
                "interested": "Template for interested prospects",
                "not_interested": "Template for uninterested prospects",
                "maybe_later": "Template for maybe later responses"
            }}
        }}
        """
    
    def _create_personalization_templates_prompt(
        self,
        business_idea: PurityBusinessIdea,
        target_industries: List[str],
        personalization_level: str,
        research_sources: List[str]
    ) -> str:
        return f"""
        Create personalization templates for:
        - Business Idea: {business_idea.description}
        - Target Industries: {', '.join(target_industries)}
        - Personalization Level: {personalization_level}
        - Research Sources: {', '.join(research_sources)}
        
        Develop comprehensive personalization templates including:
        1. Industry-specific templates
        2. Personalization hooks
        3. Research guidelines
        4. Customization tips
        
        Return the response as a JSON object with the following structure:
        {{
            "industry_templates": {{
                "industry_1": {{
                    "pain_points": ["Pain point 1", "Pain point 2"],
                    "value_proposition": "Industry-specific value prop",
                    "case_studies": ["Case study 1", "Case study 2"]
                }}
            }},
            "personalization_hooks": [
                {{
                    "hook_type": "Hook type",
                    "research_method": "Research method",
                    "personalization_angle": "Personalization angle",
                    "example": "Example usage"
                }}
            ],
            "research_guidelines": {{
                "company_research": "Company research guidelines",
                "contact_research": "Contact research guidelines",
                "industry_research": "Industry research guidelines"
            }},
            "customization_tips": [
                "Tip 1: Research recent company news",
                "Tip 2: Find mutual connections",
                "Tip 3: Reference industry trends"
            ]
        }}
        """
