from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Dict, Any
import json
from datetime import datetime

from ..models import BusinessIdea, CrowdfundingCampaign, BusinessModel
from backend.core.ai import get_ai_service_manager, AIServiceManager
from backend.core.event_bus.kafka_manager import KafkaManager
from backend.core.cache.redis_manager import RedisManager

class CrowdfundingService:
    def __init__(self):
        self.ai_service_manager: Optional[AIServiceManager] = None
        self.event_bus = KafkaManager()
        self.redis_manager = RedisManager()
    
    async def create_crowdfunding_campaign(
        self,
        db: AsyncSession,
        business_idea_id: int,
        platform_choice: str,
        funding_goal: float,
        campaign_duration: int,
        reward_tiers: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        try:
            business_idea_result = await db.execute(
                select(BusinessIdea).where(BusinessIdea.id == business_idea_id)
            )
            business_idea = business_idea_result.scalar_one_or_none()
            if not business_idea:
                raise ValueError("Business idea not found")
            
            cache_key = f"crowdfunding_campaign:{business_idea_id}:{platform_choice}"
            cached_result = await self.redis_manager.get(cache_key)
            if cached_result:
                return json.loads(cached_result)
            
            prompt = self._create_crowdfunding_campaign_prompt(
                business_idea, platform_choice, funding_goal, campaign_duration, reward_tiers
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                from backend.core.ai import get_ai_service_manager
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that helps with crowdfunding campaigns. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            campaign_data = json.loads(ai_response)
            
            crowdfunding_campaign = {
                "id": business_idea_id,
                "business_idea_id": business_idea_id,
                "platform_choice": platform_choice,
                "funding_goal": funding_goal,
                "campaign_duration": campaign_duration,
                "reward_tiers": reward_tiers,
                "campaign_strategy": campaign_data.get("campaign_strategy", {}),
                "marketing_plan": campaign_data.get("marketing_plan", {}),
                "reward_structure": campaign_data.get("reward_structure", []),
                "timeline_management": campaign_data.get("timeline_management", {}),
                "success_metrics": campaign_data.get("success_metrics", {}),
                "created_at": datetime.utcnow()
            }
            
            await self.redis_manager.set(cache_key, json.dumps(campaign_data), expire=3600)
            await self.event_bus.publish("purity.crowdfunding_campaign_created", {
                "business_idea_id": business_idea_id,
                "platform_choice": platform_choice,
                "funding_goal": funding_goal,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return crowdfunding_campaign
            
        except Exception as e:
            raise e
    
    async def develop_funding_strategy(
        self,
        db: AsyncSession,
        business_idea_id: int,
        target_audience: str,
        funding_sources: List[str],
        risk_assessment: Dict[str, Any]
    ) -> Dict[str, Any]:
        try:
            business_idea_result = await db.execute(
                select(BusinessIdea).where(BusinessIdea.id == business_idea_id)
            )
            business_idea = business_idea_result.scalar_one_or_none()
            if not business_idea:
                raise ValueError("Business idea not found")
            
            prompt = self._create_funding_strategy_prompt(
                business_idea, target_audience, funding_sources, risk_assessment
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                from backend.core.ai import get_ai_service_manager
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that helps with crowdfunding campaigns. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            strategy_data = json.loads(ai_response)
            
            funding_strategy = {
                "id": business_idea_id,
                "business_idea_id": business_idea_id,
                "target_audience": target_audience,
                "funding_sources": funding_sources,
                "risk_assessment": risk_assessment,
                "funding_plan": strategy_data.get("funding_plan", {}),
                "investor_outreach": strategy_data.get("investor_outreach", []),
                "pitch_materials": strategy_data.get("pitch_materials", {}),
                "due_diligence_preparation": strategy_data.get("due_diligence_preparation", []),
                "created_at": datetime.utcnow()
            }
            
            await self.event_bus.publish("purity.funding_strategy_developed", {
                "business_idea_id": business_idea_id,
                "target_audience": target_audience,
                "funding_sources_count": len(funding_sources),
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return funding_strategy
            
        except Exception as e:
            raise e
    
    async def create_campaign_marketing_plan(
        self,
        db: AsyncSession,
        business_idea_id: int,
        marketing_channels: List[str],
        target_backers: str,
        campaign_messaging: str
    ) -> Dict[str, Any]:
        try:
            business_idea_result = await db.execute(
                select(BusinessIdea).where(BusinessIdea.id == business_idea_id)
            )
            business_idea = business_idea_result.scalar_one_or_none()
            if not business_idea:
                raise ValueError("Business idea not found")
            
            prompt = self._create_campaign_marketing_prompt(
                business_idea, marketing_channels, target_backers, campaign_messaging
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                from backend.core.ai import get_ai_service_manager
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that helps with crowdfunding campaigns. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            marketing_data = json.loads(ai_response)
            
            campaign_marketing = {
                "id": business_idea_id,
                "business_idea_id": business_idea_id,
                "marketing_channels": marketing_channels,
                "target_backers": target_backers,
                "campaign_messaging": campaign_messaging,
                "marketing_strategy": marketing_data.get("marketing_strategy", {}),
                "content_calendar": marketing_data.get("content_calendar", []),
                "social_media_plan": marketing_data.get("social_media_plan", {}),
                "influencer_outreach": marketing_data.get("influencer_outreach", []),
                "email_campaigns": marketing_data.get("email_campaigns", []),
                "created_at": datetime.utcnow()
            }
            
            await self.event_bus.publish("purity.campaign_marketing_created", {
                "business_idea_id": business_idea_id,
                "marketing_channels": marketing_channels,
                "target_backers": target_backers,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return campaign_marketing
            
        except Exception as e:
            raise e
    
    async def manage_campaign_performance(
        self,
        db: AsyncSession,
        business_idea_id: int,
        campaign_metrics: Dict[str, Any],
        performance_goals: List[str],
        optimization_needs: List[str]
    ) -> Dict[str, Any]:
        try:
            business_idea_result = await db.execute(
                select(BusinessIdea).where(BusinessIdea.id == business_idea_id)
            )
            business_idea = business_idea_result.scalar_one_or_none()
            if not business_idea:
                raise ValueError("Business idea not found")
            
            prompt = self._create_campaign_performance_prompt(
                business_idea, campaign_metrics, performance_goals, optimization_needs
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                from backend.core.ai import get_ai_service_manager
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that helps with crowdfunding campaigns. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            performance_data = json.loads(ai_response)
            
            campaign_performance = {
                "id": business_idea_id,
                "business_idea_id": business_idea_id,
                "campaign_metrics": campaign_metrics,
                "performance_goals": performance_goals,
                "optimization_needs": optimization_needs,
                "performance_analysis": performance_data.get("performance_analysis", {}),
                "optimization_strategies": performance_data.get("optimization_strategies", []),
                "backer_engagement": performance_data.get("backer_engagement", {}),
                "funding_progress": performance_data.get("funding_progress", {}),
                "risk_mitigation": performance_data.get("risk_mitigation", []),
                "created_at": datetime.utcnow()
            }
            
            await self.event_bus.publish("purity.campaign_performance_analyzed", {
                "business_idea_id": business_idea_id,
                "performance_goals": performance_goals,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return campaign_performance
            
        except Exception as e:
            raise e
    
    def _create_crowdfunding_campaign_prompt(
        self,
        business_idea: BusinessIdea,
        platform_choice: str,
        funding_goal: float,
        campaign_duration: int,
        reward_tiers: List[Dict[str, Any]]
    ) -> str:
        return f"""
        Create crowdfunding campaign for:
        - Business Idea: {business_idea.description}
        - Platform Choice: {platform_choice}
        - Funding Goal: ${funding_goal:,.2f}
        - Campaign Duration: {campaign_duration} days
        - Reward Tiers: {len(reward_tiers)} tiers
        
        Develop comprehensive crowdfunding campaign including:
        1. Campaign strategy
        2. Marketing plan
        3. Reward structure
        4. Timeline management
        5. Success metrics
        
        Return the response as a JSON object with the following structure:
        {{
            "campaign_strategy": {{
                "campaign_theme": "Campaign theme and messaging",
                "target_audience": "Target audience identification",
                "unique_value_proposition": "Unique value proposition",
                "storytelling_approach": "Storytelling approach",
                "call_to_action": "Call to action strategy"
            }},
            "marketing_plan": {{
                "pre_launch_strategy": "Pre-launch marketing strategy",
                "launch_strategy": "Launch day strategy",
                "mid_campaign_tactics": "Mid-campaign tactics",
                "final_push_strategy": "Final push strategy",
                "post_campaign_plan": "Post-campaign plan"
            }},
            "reward_structure": [
                {{
                    "tier_name": "Reward tier name",
                    "pledge_amount": "Pledge amount",
                    "reward_description": "Reward description",
                    "delivery_timeline": "Delivery timeline",
                    "limited_availability": "Limited availability info"
                }}
            ],
            "timeline_management": {{
                "pre_launch_activities": ["Activity 1", "Activity 2"],
                "launch_activities": ["Activity 1", "Activity 2"],
                "mid_campaign_activities": ["Activity 1", "Activity 2"],
                "final_week_activities": ["Activity 1", "Activity 2"]
            }},
            "success_metrics": {{
                "funding_target": "Funding target percentage",
                "backer_engagement": "Backer engagement metrics",
                "social_sharing": "Social sharing metrics",
                "conversion_rate": "Conversion rate targets"
            }}
        }}
        """
    
    def _create_funding_strategy_prompt(
        self,
        business_idea: BusinessIdea,
        target_audience: str,
        funding_sources: List[str],
        risk_assessment: Dict[str, Any]
    ) -> str:
        return f"""
        Develop funding strategy for:
        - Business Idea: {business_idea.description}
        - Target Audience: {target_audience}
        - Funding Sources: {', '.join(funding_sources)}
        - Risk Assessment: {risk_assessment}
        
        Provide comprehensive funding strategy including:
        1. Funding plan
        2. Investor outreach
        3. Pitch materials
        4. Due diligence preparation
        
        Return the response as a JSON object with the following structure:
        {{
            "funding_plan": {{
                "funding_stages": ["Stage 1", "Stage 2"],
                "funding_amounts": ["Amount 1", "Amount 2"],
                "use_of_funds": "Use of funds breakdown",
                "funding_timeline": "Funding timeline",
                "success_criteria": "Success criteria"
            }},
            "investor_outreach": [
                {{
                    "investor_type": "Investor type",
                    "outreach_strategy": "Outreach strategy",
                    "pitch_approach": "Pitch approach",
                    "follow_up_plan": "Follow-up plan"
                }}
            ],
            "pitch_materials": {{
                "executive_summary": "Executive summary",
                "pitch_deck": "Pitch deck structure",
                "financial_projections": "Financial projections",
                "market_analysis": "Market analysis",
                "competitive_landscape": "Competitive landscape"
            }},
            "due_diligence_preparation": [
                "Preparation 1: Financial documentation",
                "Preparation 2: Legal documentation",
                "Preparation 3: Market research",
                "Preparation 4: Team background",
                "Preparation 5: Technology assessment"
            ]
        }}
        """
    
    def _create_campaign_marketing_prompt(
        self,
        business_idea: BusinessIdea,
        marketing_channels: List[str],
        target_backers: str,
        campaign_messaging: str
    ) -> str:
        return f"""
        Create campaign marketing plan for:
        - Business Idea: {business_idea.description}
        - Marketing Channels: {', '.join(marketing_channels)}
        - Target Backers: {target_backers}
        - Campaign Messaging: {campaign_messaging}
        
        Develop comprehensive campaign marketing including:
        1. Marketing strategy
        2. Content calendar
        3. Social media plan
        4. Influencer outreach
        5. Email campaigns
        
        Return the response as a JSON object with the following structure:
        {{
            "marketing_strategy": {{
                "campaign_theme": "Campaign theme",
                "messaging_framework": "Messaging framework",
                "target_audience_segments": ["Segment 1", "Segment 2"],
                "channel_strategy": "Channel strategy",
                "success_metrics": "Success metrics"
            }},
            "content_calendar": [
                {{
                    "week": 1,
                    "content_themes": ["Theme 1", "Theme 2"],
                    "content_types": ["Type 1", "Type 2"],
                    "distribution_channels": ["Channel 1", "Channel 2"]
                }}
            ],
            "social_media_plan": {{
                "platform_strategies": {{
                    "facebook": "Facebook strategy",
                    "twitter": "Twitter strategy",
                    "instagram": "Instagram strategy",
                    "linkedin": "LinkedIn strategy"
                }},
                "content_mix": "Content mix breakdown",
                "engagement_tactics": ["Tactic 1", "Tactic 2"],
                "hashtag_strategy": "Hashtag strategy"
            }},
            "influencer_outreach": [
                {{
                    "influencer_type": "Influencer type",
                    "outreach_strategy": "Outreach strategy",
                    "partnership_terms": "Partnership terms",
                    "success_metrics": "Success metrics"
                }}
            ],
            "email_campaigns": [
                {{
                    "campaign_name": "Email campaign name",
                    "target_audience": "Target audience",
                    "email_sequence": ["Email 1", "Email 2"],
                    "timing_strategy": "Timing strategy",
                    "conversion_goals": "Conversion goals"
                }}
            ]
        }}
        """
    
    def _create_campaign_performance_prompt(
        self,
        business_idea: BusinessIdea,
        campaign_metrics: Dict[str, Any],
        performance_goals: List[str],
        optimization_needs: List[str]
    ) -> str:
        return f"""
        Manage campaign performance for:
        - Business Idea: {business_idea.description}
        - Campaign Metrics: {campaign_metrics}
        - Performance Goals: {', '.join(performance_goals)}
        - Optimization Needs: {', '.join(optimization_needs)}
        
        Provide comprehensive campaign performance management including:
        1. Performance analysis
        2. Optimization strategies
        3. Backer engagement
        4. Funding progress
        5. Risk mitigation
        
        Return the response as a JSON object with the following structure:
        {{
            "performance_analysis": {{
                "current_performance": "Current performance assessment",
                "goal_progress": "Progress toward goals",
                "trend_analysis": "Trend analysis",
                "benchmark_comparison": "Benchmark comparison"
            }},
            "optimization_strategies": [
                "Strategy 1: Adjust reward tiers",
                "Strategy 2: Enhance marketing efforts",
                "Strategy 3: Improve campaign messaging",
                "Strategy 4: Expand outreach channels"
            ],
            "backer_engagement": {{
                "engagement_metrics": "Engagement metrics",
                "communication_strategy": "Communication strategy",
                "community_building": "Community building tactics",
                "feedback_management": "Feedback management"
            }},
            "funding_progress": {{
                "current_funding": "Current funding level",
                "funding_velocity": "Funding velocity",
                "projected_completion": "Projected completion",
                "milestone_achievements": "Milestone achievements"
            }},
            "risk_mitigation": [
                "Risk 1: Funding shortfall risk",
                "Risk 2: Campaign momentum risk",
                "Risk 3: Backer satisfaction risk",
                "Risk 4: Delivery timeline risk"
            ]
        }}
        """
