from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Dict, Any
import json
from datetime import datetime

from ..models import BusinessIdea, BusinessModel, CustomerAvatar
from backend.core.ai import get_ai_service_manager, AIServiceManager
from backend.core.event_bus.kafka_manager import KafkaManager
from backend.core.cache.redis_manager import RedisManager

class BusinessMentorService:
    def __init__(self):
        self.ai_service_manager: Optional[AIServiceManager] = None
        self.event_bus = KafkaManager()
        self.redis_manager = RedisManager()
    
    async def create_business_roadmap(
        self,
        db: AsyncSession,
        business_idea_id: int,
        entrepreneur_profile: Dict[str, Any],
        business_stage: str,
        goals: List[str],
        timeline_preference: str
    ) -> Dict[str, Any]:
        try:
            business_idea_result = await db.execute(
                select(BusinessIdea).where(BusinessIdea.id == business_idea_id)
            )
            business_idea = business_idea_result.scalar_one_or_none()
            if not business_idea:
                raise ValueError("Business idea not found")
            
            cache_key = f"business_roadmap:{business_idea_id}:{business_stage}"
            cached_result = await self.redis_manager.get(cache_key)
            if cached_result:
                return json.loads(cached_result)
            
            prompt = self._create_business_roadmap_prompt(
                business_idea, entrepreneur_profile, business_stage, goals, timeline_preference
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                from backend.core.ai import get_ai_service_manager
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI business mentor. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            roadmap_data = json.loads(ai_response)
            
            business_roadmap = {
                "id": business_idea_id,
                "business_idea_id": business_idea_id,
                "entrepreneur_profile": entrepreneur_profile,
                "business_stage": business_stage,
                "goals": goals,
                "timeline_preference": timeline_preference,
                "roadmap_phases": roadmap_data.get("roadmap_phases", []),
                "milestones": roadmap_data.get("milestones", []),
                "action_items": roadmap_data.get("action_items", []),
                "resource_requirements": roadmap_data.get("resource_requirements", {}),
                "success_metrics": roadmap_data.get("success_metrics", {}),
                "created_at": datetime.utcnow()
            }
            
            await self.redis_manager.set(cache_key, json.dumps(roadmap_data), expire=3600)
            await self.event_bus.publish("purity.business_roadmap_created", {
                "business_idea_id": business_idea_id,
                "business_stage": business_stage,
                "goals_count": len(goals),
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return business_roadmap
            
        except Exception as e:
            raise e
    
    async def provide_step_by_step_guidance(
        self,
        db: AsyncSession,
        business_idea_id: int,
        current_step: str,
        challenges: List[str],
        progress_level: str
    ) -> Dict[str, Any]:
        try:
            business_idea_result = await db.execute(
                select(BusinessIdea).where(BusinessIdea.id == business_idea_id)
            )
            business_idea = business_idea_result.scalar_one_or_none()
            if not business_idea:
                raise ValueError("Business idea not found")
            
            prompt = self._create_step_guidance_prompt(
                business_idea, current_step, challenges, progress_level
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                from backend.core.ai import get_ai_service_manager
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI business mentor. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            guidance_data = json.loads(ai_response)
            
            step_guidance = {
                "id": business_idea_id,
                "business_idea_id": business_idea_id,
                "current_step": current_step,
                "challenges": challenges,
                "progress_level": progress_level,
                "next_steps": guidance_data.get("next_steps", []),
                "action_plan": guidance_data.get("action_plan", {}),
                "resources_needed": guidance_data.get("resources_needed", []),
                "expert_advice": guidance_data.get("expert_advice", []),
                "common_pitfalls": guidance_data.get("common_pitfalls", []),
                "success_tips": guidance_data.get("success_tips", []),
                "created_at": datetime.utcnow()
            }
            
            await self.event_bus.publish("purity.step_guidance_provided", {
                "business_idea_id": business_idea_id,
                "current_step": current_step,
                "progress_level": progress_level,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return step_guidance
            
        except Exception as e:
            raise e
    
    async def track_milestones(
        self,
        db: AsyncSession,
        business_idea_id: int,
        milestone_data: Dict[str, Any],
        completion_status: str,
        feedback: Optional[str] = None
    ) -> Dict[str, Any]:
        try:
            business_idea_result = await db.execute(
                select(BusinessIdea).where(BusinessIdea.id == business_idea_id)
            )
            business_idea = business_idea_result.scalar_one_or_none()
            if not business_idea:
                raise ValueError("Business idea not found")
            
            prompt = self._create_milestone_tracking_prompt(
                business_idea, milestone_data, completion_status, feedback
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                from backend.core.ai import get_ai_service_manager
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI business mentor. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            tracking_data = json.loads(ai_response)
            
            milestone_tracking = {
                "id": business_idea_id,
                "business_idea_id": business_idea_id,
                "milestone_data": milestone_data,
                "completion_status": completion_status,
                "feedback": feedback,
                "progress_assessment": tracking_data.get("progress_assessment", {}),
                "next_milestones": tracking_data.get("next_milestones", []),
                "adjustments_needed": tracking_data.get("adjustments_needed", []),
                "celebration_points": tracking_data.get("celebration_points", []),
                "created_at": datetime.utcnow()
            }
            
            await self.event_bus.publish("purity.milestone_tracked", {
                "business_idea_id": business_idea_id,
                "completion_status": completion_status,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return milestone_tracking
            
        except Exception as e:
            raise e
    
    async def provide_personalized_advice(
        self,
        db: AsyncSession,
        business_idea_id: int,
        entrepreneur_questions: List[str],
        business_context: Dict[str, Any],
        advice_type: str
    ) -> Dict[str, Any]:
        try:
            business_idea_result = await db.execute(
                select(BusinessIdea).where(BusinessIdea.id == business_idea_id)
            )
            business_idea = business_idea_result.scalar_one_or_none()
            if not business_idea:
                raise ValueError("Business idea not found")
            
            prompt = self._create_personalized_advice_prompt(
                business_idea, entrepreneur_questions, business_context, advice_type
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                from backend.core.ai import get_ai_service_manager
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI business mentor. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            advice_data = json.loads(ai_response)
            
            personalized_advice = {
                "id": business_idea_id,
                "business_idea_id": business_idea_id,
                "entrepreneur_questions": entrepreneur_questions,
                "business_context": business_context,
                "advice_type": advice_type,
                "mentor_insights": advice_data.get("mentor_insights", []),
                "strategic_recommendations": advice_data.get("strategic_recommendations", []),
                "actionable_steps": advice_data.get("actionable_steps", []),
                "risk_warnings": advice_data.get("risk_warnings", []),
                "opportunity_highlights": advice_data.get("opportunity_highlights", []),
                "created_at": datetime.utcnow()
            }
            
            await self.event_bus.publish("purity.personalized_advice_provided", {
                "business_idea_id": business_idea_id,
                "advice_type": advice_type,
                "questions_count": len(entrepreneur_questions),
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return personalized_advice
            
        except Exception as e:
            raise e
    
    def _create_business_roadmap_prompt(
        self,
        business_idea: BusinessIdea,
        entrepreneur_profile: Dict[str, Any],
        business_stage: str,
        goals: List[str],
        timeline_preference: str
    ) -> str:
        return f"""
        Create business roadmap for:
        - Business Idea: {business_idea.description}
        - Entrepreneur Profile: {entrepreneur_profile}
        - Business Stage: {business_stage}
        - Goals: {', '.join(goals)}
        - Timeline Preference: {timeline_preference}
        
        Develop comprehensive business roadmap including:
        1. Roadmap phases
        2. Milestones
        3. Action items
        4. Resource requirements
        5. Success metrics
        
        Return the response as a JSON object with the following structure:
        {{
            "roadmap_phases": [
                {{
                    "phase_name": "Phase name",
                    "duration": "Phase duration",
                    "description": "Phase description",
                    "key_objectives": ["Objective 1", "Objective 2"],
                    "deliverables": ["Deliverable 1", "Deliverable 2"]
                }}
            ],
            "milestones": [
                {{
                    "milestone_name": "Milestone name",
                    "target_date": "Target date",
                    "description": "Milestone description",
                    "success_criteria": ["Criteria 1", "Criteria 2"],
                    "dependencies": ["Dependency 1", "Dependency 2"]
                }}
            ],
            "action_items": [
                {{
                    "action_name": "Action name",
                    "priority": "High/Medium/Low",
                    "timeline": "Timeline",
                    "responsible_party": "Responsible party",
                    "resources_needed": ["Resource 1", "Resource 2"]
                }}
            ],
            "resource_requirements": {{
                "financial_resources": "Financial requirements",
                "human_resources": "Human resource needs",
                "technical_resources": "Technical requirements",
                "time_commitment": "Time commitment needed"
            }},
            "success_metrics": {{
                "key_performance_indicators": ["KPI 1", "KPI 2"],
                "progress_tracking": "Progress tracking method",
                "success_definition": "Definition of success"
            }}
        }}
        """
    
    def _create_step_guidance_prompt(
        self,
        business_idea: BusinessIdea,
        current_step: str,
        challenges: List[str],
        progress_level: str
    ) -> str:
        return f"""
        Provide step-by-step guidance for:
        - Business Idea: {business_idea.description}
        - Current Step: {current_step}
        - Challenges: {', '.join(challenges)}
        - Progress Level: {progress_level}
        
        Provide comprehensive guidance including:
        1. Next steps
        2. Action plan
        3. Resources needed
        4. Expert advice
        5. Common pitfalls
        6. Success tips
        
        Return the response as a JSON object with the following structure:
        {{
            "next_steps": [
                {{
                    "step_name": "Step name",
                    "description": "Step description",
                    "priority": "High/Medium/Low",
                    "estimated_time": "Estimated time",
                    "dependencies": ["Dependency 1", "Dependency 2"]
                }}
            ],
            "action_plan": {{
                "immediate_actions": ["Action 1", "Action 2"],
                "short_term_goals": ["Goal 1", "Goal 2"],
                "long_term_strategy": "Long-term strategy"
            }},
            "resources_needed": [
                {{
                    "resource_type": "Resource type",
                    "description": "Resource description",
                    "where_to_find": "Where to find",
                    "cost_estimate": "Cost estimate"
                }}
            ],
            "expert_advice": [
                "Advice 1: Focus on customer validation",
                "Advice 2: Build MVP quickly",
                "Advice 3: Iterate based on feedback"
            ],
            "common_pitfalls": [
                "Pitfall 1: Over-engineering the solution",
                "Pitfall 2: Ignoring market feedback",
                "Pitfall 3: Underestimating costs"
            ],
            "success_tips": [
                "Tip 1: Start small and scale",
                "Tip 2: Focus on solving real problems",
                "Tip 3: Build strong relationships"
            ]
        }}
        """
    
    def _create_milestone_tracking_prompt(
        self,
        business_idea: BusinessIdea,
        milestone_data: Dict[str, Any],
        completion_status: str,
        feedback: Optional[str]
    ) -> str:
        return f"""
        Track milestone progress for:
        - Business Idea: {business_idea.description}
        - Milestone Data: {milestone_data}
        - Completion Status: {completion_status}
        - Feedback: {feedback if feedback else 'None provided'}
        
        Provide milestone tracking analysis including:
        1. Progress assessment
        2. Next milestones
        3. Adjustments needed
        4. Celebration points
        
        Return the response as a JSON object with the following structure:
        {{
            "progress_assessment": {{
                "overall_progress": "Overall progress percentage",
                "milestone_status": "Milestone status assessment",
                "timeline_adherence": "Timeline adherence analysis",
                "quality_metrics": "Quality metrics assessment"
            }},
            "next_milestones": [
                {{
                    "milestone_name": "Next milestone name",
                    "target_date": "Target date",
                    "preparation_needed": ["Preparation 1", "Preparation 2"],
                    "success_criteria": ["Criteria 1", "Criteria 2"]
                }}
            ],
            "adjustments_needed": [
                "Adjustment 1: Timeline adjustment",
                "Adjustment 2: Resource reallocation",
                "Adjustment 3: Strategy refinement"
            ],
            "celebration_points": [
                "Achievement 1: Milestone completed successfully",
                "Achievement 2: Progress ahead of schedule",
                "Achievement 3: Quality standards met"
            ]
        }}
        """
    
    def _create_personalized_advice_prompt(
        self,
        business_idea: BusinessIdea,
        entrepreneur_questions: List[str],
        business_context: Dict[str, Any],
        advice_type: str
    ) -> str:
        return f"""
        Provide personalized advice for:
        - Business Idea: {business_idea.description}
        - Entrepreneur Questions: {', '.join(entrepreneur_questions)}
        - Business Context: {business_context}
        - Advice Type: {advice_type}
        
        Provide comprehensive personalized advice including:
        1. Mentor insights
        2. Strategic recommendations
        3. Actionable steps
        4. Risk warnings
        5. Opportunity highlights
        
        Return the response as a JSON object with the following structure:
        {{
            "mentor_insights": [
                "Insight 1: Market timing is crucial",
                "Insight 2: Customer feedback is gold",
                "Insight 3: Focus on execution over perfection"
            ],
            "strategic_recommendations": [
                {{
                    "recommendation": "Strategic recommendation",
                    "rationale": "Reasoning behind recommendation",
                    "implementation": "Implementation approach",
                    "expected_outcome": "Expected outcome"
                }}
            ],
            "actionable_steps": [
                {{
                    "step": "Actionable step",
                    "timeline": "Timeline for completion",
                    "resources": "Resources needed",
                    "success_metric": "Success metric"
                }}
            ],
            "risk_warnings": [
                "Risk 1: Market saturation risk",
                "Risk 2: Cash flow management risk",
                "Risk 3: Team scaling risk"
            ],
            "opportunity_highlights": [
                "Opportunity 1: Untapped market segment",
                "Opportunity 2: Technology advantage",
                "Opportunity 3: Strategic partnership potential"
            ]
        }}
        """
