from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Dict, Any
import json
from datetime import datetime

from ..models import BusinessIdea, LaunchStrategy, BusinessModel, PurityMarketResearch
from backend.core.ai import get_ai_service_manager, AIServiceManager
from backend.core.event_bus.kafka_manager import KafkaManager
from backend.core.cache.redis_manager import RedisManager

class LaunchStrategyService:
    def __init__(self):
        self.ai_service_manager: Optional[AIServiceManager] = None
        self.event_bus = KafkaManager()
        self.redis_manager = RedisManager()
    
    async def create_launch_strategy(
        self,
        db: AsyncSession,
        business_idea_id: int,
        target_market: str,
        launch_budget: float,
        timeline_months: int,
        launch_channels: List[str],
        success_metrics: List[str],
        risk_factors: Optional[List[str]] = None
    ) -> LaunchStrategy:
        try:
            business_idea_result = await db.execute(
                select(BusinessIdea).where(BusinessIdea.id == business_idea_id)
            )
            business_idea = business_idea_result.scalar_one_or_none()
            if not business_idea:
                raise ValueError("Business idea not found")
            
            cache_key = f"launch_strategy:{business_idea_id}:{target_market}"
            cached_result = await self.redis_manager.get(cache_key)
            if cached_result:
                return json.loads(cached_result)
            
            prompt = self._create_launch_strategy_prompt(
                business_idea, target_market, launch_budget, timeline_months,
                launch_channels, success_metrics, risk_factors
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                from backend.core.ai import get_ai_service_manager
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that creates launch strategies. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            strategy_data = json.loads(ai_response)
            
            launch_strategy = LaunchStrategy(
                business_idea_id=business_idea_id,
                target_market=target_market,
                launch_budget=launch_budget,
                timeline_months=timeline_months,
                launch_channels=json.dumps(launch_channels),
                success_metrics=json.dumps(success_metrics),
                mvp_blueprint=json.dumps(strategy_data.get("mvp_blueprint", {})),
                go_to_market_strategy=json.dumps(strategy_data.get("go_to_market_strategy", {})),
                launch_timeline=json.dumps(strategy_data.get("launch_timeline", [])),
                risk_mitigation_plan=json.dumps(strategy_data.get("risk_mitigation_plan", {})),
                launch_roi_projection=strategy_data.get("launch_roi_projection", 0.0)
            )
            
            db.add(launch_strategy)
            await db.commit()
            await db.refresh(launch_strategy)
            
            await self.redis_manager.set(cache_key, json.dumps(strategy_data), expire=3600)
            await self.event_bus.publish("purity.launch_strategy_created", {
                "business_idea_id": business_idea_id,
                "target_market": target_market,
                "launch_budget": launch_budget,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return launch_strategy
            
        except Exception as e:
            await db.rollback()
            raise e
    
    async def create_mvp_blueprint(
        self,
        db: AsyncSession,
        business_idea_id: int,
        development_budget: float,
        timeline_weeks: int,
        core_features: List[str],
        technical_requirements: Optional[List[str]] = None,
        platform_preferences: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        try:
            business_idea_result = await db.execute(
                select(BusinessIdea).where(BusinessIdea.id == business_idea_id)
            )
            business_idea = business_idea_result.scalar_one_or_none()
            if not business_idea:
                raise ValueError("Business idea not found")
            
            prompt = self._create_mvp_blueprint_prompt(
                business_idea, development_budget, timeline_weeks, core_features,
                technical_requirements, platform_preferences
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                from backend.core.ai import get_ai_service_manager
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that creates launch strategies. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            blueprint_data = json.loads(ai_response)
            
            mvp_blueprint = {
                "id": business_idea_id,
                "business_idea_id": business_idea_id,
                "development_budget": development_budget,
                "timeline_weeks": timeline_weeks,
                "core_features": core_features,
                "feature_prioritization": blueprint_data.get("feature_prioritization", []),
                "technical_stack": blueprint_data.get("technical_stack", []),
                "development_phases": blueprint_data.get("development_phases", []),
                "resource_requirements": blueprint_data.get("resource_requirements", {}),
                "estimated_development_cost": blueprint_data.get("estimated_development_cost", 0.0),
                "created_at": datetime.utcnow()
            }
            
            await self.event_bus.publish("purity.mvp_blueprint_created", {
                "business_idea_id": business_idea_id,
                "development_budget": development_budget,
                "timeline_weeks": timeline_weeks,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return mvp_blueprint
            
        except Exception as e:
            raise e
    
    async def create_go_to_market_strategy(
        self,
        db: AsyncSession,
        business_idea_id: int,
        target_customer_segments: List[str],
        value_proposition: str,
        pricing_strategy: str,
        distribution_channels: List[str],
        marketing_channels: List[str]
    ) -> Dict[str, Any]:
        try:
            business_idea_result = await db.execute(
                select(BusinessIdea).where(BusinessIdea.id == business_idea_id)
            )
            business_idea = business_idea_result.scalar_one_or_none()
            if not business_idea:
                raise ValueError("Business idea not found")
            
            prompt = self._create_go_to_market_prompt(
                business_idea, target_customer_segments, value_proposition,
                pricing_strategy, distribution_channels, marketing_channels
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                from backend.core.ai import get_ai_service_manager
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that creates launch strategies. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            gtm_data = json.loads(ai_response)
            
            gtm_strategy = {
                "id": business_idea_id,
                "business_idea_id": business_idea_id,
                "target_customer_segments": target_customer_segments,
                "value_proposition": value_proposition,
                "pricing_strategy": pricing_strategy,
                "distribution_channels": distribution_channels,
                "marketing_channels": marketing_channels,
                "customer_acquisition_strategy": gtm_data.get("customer_acquisition_strategy", {}),
                "pricing_model": gtm_data.get("pricing_model", {}),
                "marketing_campaign_plan": gtm_data.get("marketing_campaign_plan", {}),
                "sales_process": gtm_data.get("sales_process", {}),
                "created_at": datetime.utcnow()
            }
            
            await self.event_bus.publish("purity.gtm_strategy_created", {
                "business_idea_id": business_idea_id,
                "target_customer_segments": target_customer_segments,
                "pricing_strategy": pricing_strategy,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return gtm_strategy
            
        except Exception as e:
            raise e
    
    async def create_launch_timeline(
        self,
        db: AsyncSession,
        business_idea_id: int,
        launch_date: datetime,
        pre_launch_activities: List[str],
        launch_activities: List[str],
        post_launch_activities: List[str],
        milestone_dates: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        try:
            business_idea_result = await db.execute(
                select(BusinessIdea).where(BusinessIdea.id == business_idea_id)
            )
            business_idea = business_idea_result.scalar_one_or_none()
            if not business_idea:
                raise ValueError("Business idea not found")
            
            prompt = self._create_launch_timeline_prompt(
                business_idea, launch_date, pre_launch_activities,
                launch_activities, post_launch_activities, milestone_dates
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                from backend.core.ai import get_ai_service_manager
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that creates launch strategies. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            timeline_data = json.loads(ai_response)
            
            launch_timeline = {
                "id": business_idea_id,
                "business_idea_id": business_idea_id,
                "launch_date": launch_date,
                "pre_launch_activities": pre_launch_activities,
                "launch_activities": launch_activities,
                "post_launch_activities": post_launch_activities,
                "detailed_timeline": timeline_data.get("detailed_timeline", []),
                "milestone_tracking": timeline_data.get("milestone_tracking", {}),
                "resource_allocation": timeline_data.get("resource_allocation", {}),
                "created_at": datetime.utcnow()
            }
            
            await self.event_bus.publish("purity.launch_timeline_created", {
                "business_idea_id": business_idea_id,
                "launch_date": launch_date.isoformat(),
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return launch_timeline
            
        except Exception as e:
            raise e
    
    async def update_launch_strategy(
        self,
        db: AsyncSession,
        strategy_id: int,
        target_market: str,
        launch_budget: float,
        timeline_months: int,
        launch_channels: List[str],
        success_metrics: List[str],
        risk_factors: Optional[List[str]] = None
    ) -> LaunchStrategy:
        try:
            result = await db.execute(
                select(LaunchStrategy).where(LaunchStrategy.id == strategy_id)
            )
            launch_strategy = result.scalar_one_or_none()
            if not launch_strategy:
                raise ValueError("Launch strategy not found")
            
            business_idea_result = await db.execute(
                select(BusinessIdea).where(BusinessIdea.id == launch_strategy.business_idea_id)
            )
            business_idea = business_idea_result.scalar_one_or_none()
            
            prompt = self._create_launch_strategy_prompt(
                business_idea, target_market, launch_budget, timeline_months,
                launch_channels, success_metrics, risk_factors
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                from backend.core.ai import get_ai_service_manager
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that creates launch strategies. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            strategy_data = json.loads(ai_response)
            
            launch_strategy.target_market = target_market
            launch_strategy.launch_budget = launch_budget
            launch_strategy.timeline_months = timeline_months
            launch_strategy.launch_channels = json.dumps(launch_channels)
            launch_strategy.success_metrics = json.dumps(success_metrics)
            launch_strategy.mvp_blueprint = json.dumps(strategy_data.get("mvp_blueprint", {}))
            launch_strategy.go_to_market_strategy = json.dumps(strategy_data.get("go_to_market_strategy", {}))
            launch_strategy.launch_timeline = json.dumps(strategy_data.get("launch_timeline", []))
            launch_strategy.risk_mitigation_plan = json.dumps(strategy_data.get("risk_mitigation_plan", {}))
            launch_strategy.launch_roi_projection = strategy_data.get("launch_roi_projection", 0.0)
            launch_strategy.updated_at = datetime.utcnow()
            
            await db.commit()
            await db.refresh(launch_strategy)
            
            await self.event_bus.publish("purity.launch_strategy_updated", {
                "strategy_id": strategy_id,
                "target_market": target_market,
                "launch_budget": launch_budget,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return launch_strategy
            
        except Exception as e:
            await db.rollback()
            raise e
    
    def _create_launch_strategy_prompt(
        self,
        business_idea: BusinessIdea,
        target_market: str,
        launch_budget: float,
        timeline_months: int,
        launch_channels: List[str],
        success_metrics: List[str],
        risk_factors: Optional[List[str]]
    ) -> str:
        return f"""
        Create a comprehensive launch strategy for:
        - Business Idea: {business_idea.description}
        - Target Market: {target_market}
        - Launch Budget: ${launch_budget:,.2f}
        - Timeline: {timeline_months} months
        - Launch Channels: {', '.join(launch_channels)}
        - Success Metrics: {', '.join(success_metrics)}
        - Risk Factors: {', '.join(risk_factors) if risk_factors else 'None specified'}
        
        Develop a complete launch strategy including:
        1. MVP Blueprint
        2. Go-to-Market Strategy
        3. Launch Timeline
        4. Risk Mitigation Plan
        5. Launch ROI Projection
        
        Return the response as a JSON object with the following structure:
        {{
            "mvp_blueprint": {{
                "core_features": ["Feature 1", "Feature 2"],
                "development_phases": ["Phase 1", "Phase 2"],
                "technical_requirements": ["Requirement 1", "Requirement 2"],
                "estimated_cost": 50000.0
            }},
            "go_to_market_strategy": {{
                "customer_segments": ["Segment 1", "Segment 2"],
                "value_proposition": "Clear value proposition",
                "pricing_model": "Pricing strategy",
                "marketing_channels": ["Channel 1", "Channel 2"],
                "sales_process": "Sales process description"
            }},
            "launch_timeline": [
                {{
                    "phase": "Phase Name",
                    "duration": "Duration",
                    "activities": ["Activity 1", "Activity 2"],
                    "milestones": ["Milestone 1", "Milestone 2"]
                }}
            ],
            "risk_mitigation_plan": {{
                "identified_risks": ["Risk 1", "Risk 2"],
                "mitigation_strategies": ["Strategy 1", "Strategy 2"],
                "contingency_plans": ["Plan 1", "Plan 2"]
            }},
            "launch_roi_projection": 150.0
        }}
        """
    
    def _create_mvp_blueprint_prompt(
        self,
        business_idea: BusinessIdea,
        development_budget: float,
        timeline_weeks: int,
        core_features: List[str],
        technical_requirements: Optional[List[str]],
        platform_preferences: Optional[List[str]]
    ) -> str:
        return f"""
        Create an MVP blueprint for:
        - Business Idea: {business_idea.description}
        - Development Budget: ${development_budget:,.2f}
        - Timeline: {timeline_weeks} weeks
        - Core Features: {', '.join(core_features)}
        - Technical Requirements: {', '.join(technical_requirements) if technical_requirements else 'None specified'}
        - Platform Preferences: {', '.join(platform_preferences) if platform_preferences else 'None specified'}
        
        Develop a comprehensive MVP blueprint including:
        1. Feature prioritization
        2. Technical stack recommendations
        3. Development phases
        4. Resource requirements
        5. Cost estimation
        
        Return the response as a JSON object with the following structure:
        {{
            "feature_prioritization": [
                {{
                    "feature": "Feature Name",
                    "priority": "high/medium/low",
                    "effort": "effort level",
                    "value": "business value"
                }}
            ],
            "technical_stack": ["Technology 1", "Technology 2", "Technology 3"],
            "development_phases": [
                {{
                    "phase": "Phase Name",
                    "duration": "Duration",
                    "features": ["Feature 1", "Feature 2"],
                    "deliverables": ["Deliverable 1", "Deliverable 2"]
                }}
            ],
            "resource_requirements": {{
                "team_size": 5,
                "roles": ["Role 1", "Role 2"],
                "tools": ["Tool 1", "Tool 2"],
                "infrastructure": "Infrastructure requirements"
            }},
            "estimated_development_cost": 45000.0
        }}
        """
    
    def _create_go_to_market_prompt(
        self,
        business_idea: BusinessIdea,
        target_customer_segments: List[str],
        value_proposition: str,
        pricing_strategy: str,
        distribution_channels: List[str],
        marketing_channels: List[str]
    ) -> str:
        return f"""
        Create a go-to-market strategy for:
        - Business Idea: {business_idea.description}
        - Target Customer Segments: {', '.join(target_customer_segments)}
        - Value Proposition: {value_proposition}
        - Pricing Strategy: {pricing_strategy}
        - Distribution Channels: {', '.join(distribution_channels)}
        - Marketing Channels: {', '.join(marketing_channels)}
        
        Develop a comprehensive go-to-market strategy including:
        1. Customer acquisition strategy
        2. Pricing model
        3. Marketing campaign plan
        4. Sales process
        
        Return the response as a JSON object with the following structure:
        {{
            "customer_acquisition_strategy": {{
                "target_segments": ["Segment 1", "Segment 2"],
                "acquisition_channels": ["Channel 1", "Channel 2"],
                "conversion_funnel": "Funnel description",
                "acquisition_cost_target": 50.0
            }},
            "pricing_model": {{
                "pricing_strategy": "Strategy description",
                "price_points": ["Point 1", "Point 2"],
                "pricing_tiers": ["Tier 1", "Tier 2"],
                "pricing_psychology": "Psychology factors"
            }},
            "marketing_campaign_plan": {{
                "campaign_phases": ["Phase 1", "Phase 2"],
                "messaging_strategy": "Messaging approach",
                "creative_elements": ["Element 1", "Element 2"],
                "budget_allocation": "Budget breakdown"
            }},
            "sales_process": {{
                "sales_funnel": "Funnel stages",
                "lead_qualification": "Qualification criteria",
                "sales_techniques": ["Technique 1", "Technique 2"],
                "closing_strategies": ["Strategy 1", "Strategy 2"]
            }}
        }}
        """
    
    def _create_launch_timeline_prompt(
        self,
        business_idea: BusinessIdea,
        launch_date: datetime,
        pre_launch_activities: List[str],
        launch_activities: List[str],
        post_launch_activities: List[str],
        milestone_dates: Optional[Dict[str, Any]]
    ) -> str:
        return f"""
        Create a detailed launch timeline for:
        - Business Idea: {business_idea.description}
        - Launch Date: {launch_date.strftime('%Y-%m-%d')}
        - Pre-launch Activities: {', '.join(pre_launch_activities)}
        - Launch Activities: {', '.join(launch_activities)}
        - Post-launch Activities: {', '.join(post_launch_activities)}
        - Milestone Dates: {milestone_dates if milestone_dates else 'None specified'}
        
        Develop a comprehensive launch timeline including:
        1. Detailed timeline breakdown
        2. Milestone tracking
        3. Resource allocation
        
        Return the response as a JSON object with the following structure:
        {{
            "detailed_timeline": [
                {{
                    "week": 1,
                    "activities": ["Activity 1", "Activity 2"],
                    "milestones": ["Milestone 1"],
                    "resources": ["Resource 1", "Resource 2"],
                    "dependencies": ["Dependency 1"]
                }}
            ],
            "milestone_tracking": {{
                "key_milestones": ["Milestone 1", "Milestone 2"],
                "success_criteria": ["Criteria 1", "Criteria 2"],
                "tracking_metrics": ["Metric 1", "Metric 2"]
            }},
            "resource_allocation": {{
                "team_assignments": ["Assignment 1", "Assignment 2"],
                "budget_allocation": "Budget breakdown",
                "tool_requirements": ["Tool 1", "Tool 2"],
                "external_resources": ["Resource 1", "Resource 2"]
            }}
        }}
        """
