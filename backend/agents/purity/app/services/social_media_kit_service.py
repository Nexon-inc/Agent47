from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Dict, Any
import json
from datetime import datetime, timedelta

from ..models import BusinessIdea, BrandIdentity, BusinessModel
from core.ai import get_ai_service_manager, AIServiceManager
from core.event_bus.kafka_manager import KafkaManager
from core.cache.redis_manager import RedisManager

class SocialMediaKitService:
    def __init__(self):
        self.ai_service_manager: Optional[AIServiceManager] = None
        self.event_bus = KafkaManager()
        self.redis_manager = RedisManager()
    
    async def create_content_calendar(
        self,
        db: AsyncSession,
        business_idea_id: int,
        platforms: List[str],
        content_themes: List[str],
        posting_frequency: str,
        calendar_duration_weeks: int
    ) -> Dict[str, Any]:
        try:
            business_idea_result = await db.execute(
                select(BusinessIdea).where(BusinessIdea.id == business_idea_id)
            )
            business_idea = business_idea_result.scalar_one_or_none()
            if not business_idea:
                raise ValueError("Business idea not found")
            
            cache_key = f"content_calendar:{business_idea_id}:{','.join(platforms)}"
            cached_result = await self.redis_manager.get(cache_key)
            if cached_result:
                return json.loads(cached_result)
            
            prompt = self._create_content_calendar_prompt(
                business_idea, platforms, content_themes, posting_frequency, calendar_duration_weeks
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                from core.ai import get_ai_service_manager
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that creates social media kits. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            calendar_data = json.loads(ai_response)
            
            content_calendar = {
                "id": business_idea_id,
                "business_idea_id": business_idea_id,
                "platforms": platforms,
                "content_themes": content_themes,
                "posting_frequency": posting_frequency,
                "calendar_duration_weeks": calendar_duration_weeks,
                "weekly_schedule": calendar_data.get("weekly_schedule", []),
                "content_pillars": calendar_data.get("content_pillars", []),
                "posting_times": calendar_data.get("posting_times", {}),
                "content_mix": calendar_data.get("content_mix", {}),
                "created_at": datetime.utcnow()
            }
            
            await self.redis_manager.set(cache_key, json.dumps(calendar_data), expire=3600)
            await self.event_bus.publish("purity.content_calendar_created", {
                "business_idea_id": business_idea_id,
                "platforms": platforms,
                "calendar_duration_weeks": calendar_duration_weeks,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return content_calendar
            
        except Exception as e:
            raise e
    
    async def generate_hashtag_strategy(
        self,
        db: AsyncSession,
        business_idea_id: int,
        target_audience: str,
        platforms: List[str],
        hashtag_categories: List[str]
    ) -> Dict[str, Any]:
        try:
            business_idea_result = await db.execute(
                select(BusinessIdea).where(BusinessIdea.id == business_idea_id)
            )
            business_idea = business_idea_result.scalar_one_or_none()
            if not business_idea:
                raise ValueError("Business idea not found")
            
            prompt = self._create_hashtag_strategy_prompt(
                business_idea, target_audience, platforms, hashtag_categories
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                from core.ai import get_ai_service_manager
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that creates social media kits. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            hashtag_data = json.loads(ai_response)
            
            hashtag_strategy = {
                "id": business_idea_id,
                "business_idea_id": business_idea_id,
                "target_audience": target_audience,
                "platforms": platforms,
                "hashtag_categories": hashtag_categories,
                "branded_hashtags": hashtag_data.get("branded_hashtags", []),
                "trending_hashtags": hashtag_data.get("trending_hashtags", []),
                "niche_hashtags": hashtag_data.get("niche_hashtags", []),
                "hashtag_combinations": hashtag_data.get("hashtag_combinations", []),
                "hashtag_performance_tips": hashtag_data.get("hashtag_performance_tips", []),
                "created_at": datetime.utcnow()
            }
            
            await self.event_bus.publish("purity.hashtag_strategy_generated", {
                "business_idea_id": business_idea_id,
                "platforms": platforms,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return hashtag_strategy
            
        except Exception as e:
            raise e
    
    async def create_social_media_strategy(
        self,
        db: AsyncSession,
        business_idea_id: int,
        target_audience: str,
        business_goals: List[str],
        budget_allocation: Dict[str, float]
    ) -> Dict[str, Any]:
        try:
            business_idea_result = await db.execute(
                select(BusinessIdea).where(BusinessIdea.id == business_idea_id)
            )
            business_idea = business_idea_result.scalar_one_or_none()
            if not business_idea:
                raise ValueError("Business idea not found")
            
            prompt = self._create_social_media_strategy_prompt(
                business_idea, target_audience, business_goals, budget_allocation
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                from core.ai import get_ai_service_manager
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that creates social media kits. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            strategy_data = json.loads(ai_response)
            
            social_media_strategy = {
                "id": business_idea_id,
                "business_idea_id": business_idea_id,
                "target_audience": target_audience,
                "business_goals": business_goals,
                "budget_allocation": budget_allocation,
                "platform_strategy": strategy_data.get("platform_strategy", {}),
                "content_strategy": strategy_data.get("content_strategy", {}),
                "engagement_strategy": strategy_data.get("engagement_strategy", {}),
                "growth_tactics": strategy_data.get("growth_tactics", []),
                "success_metrics": strategy_data.get("success_metrics", {}),
                "created_at": datetime.utcnow()
            }
            
            await self.event_bus.publish("purity.social_media_strategy_created", {
                "business_idea_id": business_idea_id,
                "business_goals": business_goals,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return social_media_strategy
            
        except Exception as e:
            raise e
    
    async def generate_post_templates(
        self,
        db: AsyncSession,
        business_idea_id: int,
        post_types: List[str],
        tone: str,
        call_to_action_types: List[str]
    ) -> Dict[str, Any]:
        try:
            business_idea_result = await db.execute(
                select(BusinessIdea).where(BusinessIdea.id == business_idea_id)
            )
            business_idea = business_idea_result.scalar_one_or_none()
            if not business_idea:
                raise ValueError("Business idea not found")
            
            prompt = self._create_post_templates_prompt(
                business_idea, post_types, tone, call_to_action_types
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                from core.ai import get_ai_service_manager
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that creates social media kits. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            templates_data = json.loads(ai_response)
            
            post_templates = {
                "id": business_idea_id,
                "business_idea_id": business_idea_id,
                "post_types": post_types,
                "tone": tone,
                "call_to_action_types": call_to_action_types,
                "template_library": templates_data.get("template_library", {}),
                "caption_formulas": templates_data.get("caption_formulas", []),
                "visual_guidelines": templates_data.get("visual_guidelines", {}),
                "engagement_prompts": templates_data.get("engagement_prompts", []),
                "created_at": datetime.utcnow()
            }
            
            await self.event_bus.publish("purity.post_templates_generated", {
                "business_idea_id": business_idea_id,
                "post_types": post_types,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return post_templates
            
        except Exception as e:
            raise e
    
    def _create_content_calendar_prompt(
        self,
        business_idea: BusinessIdea,
        platforms: List[str],
        content_themes: List[str],
        posting_frequency: str,
        calendar_duration_weeks: int
    ) -> str:
        return f"""
        Create content calendar for:
        - Business Idea: {business_idea.description}
        - Platforms: {', '.join(platforms)}
        - Content Themes: {', '.join(content_themes)}
        - Posting Frequency: {posting_frequency}
        - Calendar Duration: {calendar_duration_weeks} weeks
        
        Develop comprehensive content calendar including:
        1. Weekly posting schedule
        2. Content pillars
        3. Optimal posting times
        4. Content mix distribution
        
        Return the response as a JSON object with the following structure:
        {{
            "weekly_schedule": [
                {{
                    "week": 1,
                    "platform": "Platform name",
                    "posts": [
                        {{
                            "day": "Monday",
                            "time": "9:00 AM",
                            "content_type": "Content type",
                            "theme": "Content theme",
                            "caption": "Post caption"
                        }}
                    ]
                }}
            ],
            "content_pillars": [
                {{
                    "pillar_name": "Pillar name",
                    "description": "Pillar description",
                    "content_types": ["Type 1", "Type 2"],
                    "posting_frequency": "Frequency"
                }}
            ],
            "posting_times": {{
                "platform_1": ["Time 1", "Time 2"],
                "platform_2": ["Time 1", "Time 2"]
            }},
            "content_mix": {{
                "educational": 30,
                "entertaining": 25,
                "promotional": 20,
                "user_generated": 15,
                "behind_scenes": 10
            }}
        }}
        """
    
    def _create_hashtag_strategy_prompt(
        self,
        business_idea: BusinessIdea,
        target_audience: str,
        platforms: List[str],
        hashtag_categories: List[str]
    ) -> str:
        return f"""
        Generate hashtag strategy for:
        - Business Idea: {business_idea.description}
        - Target Audience: {target_audience}
        - Platforms: {', '.join(platforms)}
        - Hashtag Categories: {', '.join(hashtag_categories)}
        
        Create comprehensive hashtag strategy including:
        1. Branded hashtags
        2. Trending hashtags
        3. Niche hashtags
        4. Hashtag combinations
        5. Performance tips
        
        Return the response as a JSON object with the following structure:
        {{
            "branded_hashtags": [
                {{
                    "hashtag": "#BrandName",
                    "usage": "Usage description",
                    "platforms": ["Platform 1", "Platform 2"]
                }}
            ],
            "trending_hashtags": [
                {{
                    "hashtag": "#TrendingTag",
                    "volume": "High/Medium/Low",
                    "relevance": "Relevance score"
                }}
            ],
            "niche_hashtags": [
                {{
                    "hashtag": "#NicheTag",
                    "audience": "Target audience",
                    "engagement_rate": "Engagement rate"
                }}
            ],
            "hashtag_combinations": [
                {{
                    "combination": ["#Tag1", "#Tag2", "#Tag3"],
                    "use_case": "When to use",
                    "expected_reach": "Expected reach"
                }}
            ],
            "hashtag_performance_tips": [
                "Tip 1: Use 5-10 hashtags per post",
                "Tip 2: Mix popular and niche hashtags",
                "Tip 3: Research trending hashtags"
            ]
        }}
        """
    
    def _create_social_media_strategy_prompt(
        self,
        business_idea: BusinessIdea,
        target_audience: str,
        business_goals: List[str],
        budget_allocation: Dict[str, float]
    ) -> str:
        return f"""
        Create social media strategy for:
        - Business Idea: {business_idea.description}
        - Target Audience: {target_audience}
        - Business Goals: {', '.join(business_goals)}
        - Budget Allocation: {budget_allocation}
        
        Develop comprehensive social media strategy including:
        1. Platform strategy
        2. Content strategy
        3. Engagement strategy
        4. Growth tactics
        5. Success metrics
        
        Return the response as a JSON object with the following structure:
        {{
            "platform_strategy": {{
                "primary_platforms": ["Platform 1", "Platform 2"],
                "secondary_platforms": ["Platform 3", "Platform 4"],
                "platform_specific_goals": {{
                    "platform_1": "Goal for platform 1",
                    "platform_2": "Goal for platform 2"
                }}
            }},
            "content_strategy": {{
                "content_pillars": ["Pillar 1", "Pillar 2"],
                "content_mix": "Content mix breakdown",
                "posting_schedule": "Posting schedule"
            }},
            "engagement_strategy": {{
                "engagement_goals": ["Goal 1", "Goal 2"],
                "response_strategy": "Response strategy",
                "community_building": "Community building tactics"
            }},
            "growth_tactics": [
                "Tactic 1: Influencer partnerships",
                "Tactic 2: User-generated content",
                "Tactic 3: Cross-platform promotion"
            ],
            "success_metrics": {{
                "reach_metrics": ["Metric 1", "Metric 2"],
                "engagement_metrics": ["Metric 1", "Metric 2"],
                "conversion_metrics": ["Metric 1", "Metric 2"]
            }}
        }}
        """
    
    def _create_post_templates_prompt(
        self,
        business_idea: BusinessIdea,
        post_types: List[str],
        tone: str,
        call_to_action_types: List[str]
    ) -> str:
        return f"""
        Generate post templates for:
        - Business Idea: {business_idea.description}
        - Post Types: {', '.join(post_types)}
        - Tone: {tone}
        - Call to Action Types: {', '.join(call_to_action_types)}
        
        Create comprehensive post templates including:
        1. Template library
        2. Caption formulas
        3. Visual guidelines
        4. Engagement prompts
        
        Return the response as a JSON object with the following structure:
        {{
            "template_library": {{
                "post_type_1": [
                    {{
                        "template_name": "Template name",
                        "structure": "Post structure",
                        "caption_template": "Caption template",
                        "hashtag_suggestions": ["#Tag1", "#Tag2"]
                    }}
                ]
            }},
            "caption_formulas": [
                {{
                    "formula_name": "Formula name",
                    "structure": "Caption structure",
                    "example": "Example caption",
                    "best_for": "Best use cases"
                }}
            ],
            "visual_guidelines": {{
                "image_specs": "Image specifications",
                "color_palette": "Color palette",
                "branding_elements": "Branding elements",
                "composition_tips": "Composition tips"
            }},
            "engagement_prompts": [
                {{
                    "prompt_type": "Prompt type",
                    "question": "Engagement question",
                    "use_case": "When to use",
                    "expected_response": "Expected response type"
                }}
            ]
        }}
        """
