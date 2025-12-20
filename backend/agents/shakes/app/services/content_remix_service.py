from typing import Dict, Any, List, Optional
from datetime import datetime
from core.ai import get_ai_service_manager, AIServiceManager
from core.utils.database_utils import DatabaseUtils
from core.utils.cache_utils import CacheUtils
from core.utils.event_bus_utils import EventBusUtils
from core.utils.integration_utils import IntegrationUtils
from core.config import settings
from ..database import get_shakes_database

class ContentRemixService:
    """Service for automated content remixing and repurposing"""
    
    def __init__(self):
        self.db_utils = DatabaseUtils()
        self.cache_utils = CacheUtils()
        self.event_bus = EventBusUtils()
        self.integration_utils = IntegrationUtils()
        self.model_config = {"model": "grok-llm", "temperature": 0.8, "max_tokens": 2500}
        
    async def initialize(self):
        """Initialize service dependencies"""
        await self.db_utils.initialize()
        await self.cache_utils.initialize()
        await self.event_bus.initialize()
        await self.integration_utils.initialize()
    
    async def remix_content(self, source_content_id: int, target_formats: List[str],
                          remix_strategy: str, customization_options: Dict[str, Any]) -> Dict[str, Any]:
        """Remix content into different formats and platforms"""
        try:
            db = await get_shakes_database()
            async with db.get_session() as session:
                source_content = await session.get("content_pieces", source_content_id)
                if not source_content:
                    return {"success": False, "error": "Source content not found"}
                
                remixed_content = []
                for target_format in target_formats:
                    remix_result = await self._create_remix_variant(
                        source_content, target_format, remix_strategy, customization_options
                    )
                    
                    remix_metadata = {
                        "source_content_id": source_content_id,
                        "target_format": target_format,
                        "remix_strategy": remix_strategy,
                        "customization_options": customization_options,
                        "remixed_content": remix_result,
                        "created_at": datetime.utcnow()
                    }
                    
                    remix_id = await self._save_remix_content(remix_metadata, session)
                    
                    remixed_content.append({
                        "remix_id": remix_id,
                        "target_format": target_format,
                        "remixed_content": remix_result,
                        "optimization_insights": await self._get_remix_optimization_insights(
                            remix_result, target_format
                        )
                    })
                
                await self.event_bus.publish_event("content_remixed", {
                    "source_content_id": source_content_id,
                    "target_formats": target_formats,
                    "remix_count": len(remixed_content)
                })
                
                return {
                    "success": True,
                    "remixed_content": remixed_content,
                    "remix_summary": await self._generate_remix_summary(remixed_content),
                    "performance_predictions": await self._predict_remix_performance(remixed_content),
                    "optimization_recommendations": await self._generate_remix_optimization_recommendations(
                        remixed_content
                    )
                }
                
        except Exception as e:
            return {"success": False, "error": f"Content remixing failed: {str(e)}"}
    
    async def schedule_remix_automation(self, content_piece_id: int, 
                                      remix_schedule: Dict[str, Any],
                                      automation_rules: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Schedule automated content remixing"""
        try:
            db = await get_shakes_database()
            async with db.get_session() as session:
                content_piece = await session.get("content_pieces", content_piece_id)
                if not content_piece:
                    return {"success": False, "error": "Content piece not found"}
                
                automation_config = await self._create_automation_config(
                    content_piece_id, remix_schedule, automation_rules
                )
                
                scheduled_remixes = await self._schedule_remix_tasks(
                    automation_config, remix_schedule
                )
                
                automation_id = await self._save_automation_config(
                    automation_config, scheduled_remixes, session
                )
                
                await self.event_bus.publish_event("remix_automation_scheduled", {
                    "content_piece_id": content_piece_id,
                    "automation_id": automation_id,
                    "scheduled_remixes": len(scheduled_remixes)
                })
                
                return {
                    "success": True,
                    "automation_id": automation_id,
                    "scheduled_remixes": scheduled_remixes,
                    "automation_config": automation_config,
                    "next_execution": await self._get_next_execution_time(remix_schedule),
                    "automation_insights": await self._generate_automation_insights(
                        automation_config
                    )
                }
                
        except Exception as e:
            return {"success": False, "error": f"Remix automation scheduling failed: {str(e)}"}
    
    async def analyze_remix_performance(self, remix_id: int, 
                                      analysis_period_days: int,
                                      performance_metrics: List[str]) -> Dict[str, Any]:
        """Analyze performance of remixed content"""
        try:
            db = await get_shakes_database()
            async with db.get_session() as session:
                remix_content = await session.get("remixed_content", remix_id)
                if not remix_content:
                    return {"success": False, "error": "Remix content not found"}
                
                performance_data = await self._collect_remix_metrics(
                    remix_id, analysis_period_days, performance_metrics
                )
                
                performance_analysis = await self._analyze_remix_performance_data(
                    performance_data, performance_metrics
                )
                
                source_comparison = await self._compare_to_source_content(
                    remix_content, performance_analysis
                )
                
                optimization_opportunities = await self._identify_optimization_opportunities(
                    performance_analysis, source_comparison
                )
                
                await self.event_bus.publish_event("remix_performance_analyzed", {
                    "remix_id": remix_id,
                    "performance_score": performance_analysis.get("overall_score"),
                    "optimization_opportunities": len(optimization_opportunities)
                })
                
                return {
                    "success": True,
                    "performance_data": performance_data,
                    "performance_analysis": performance_analysis,
                    "source_comparison": source_comparison,
                    "optimization_opportunities": optimization_opportunities,
                    "remix_effectiveness": await self._assess_remix_effectiveness(
                        performance_analysis, source_comparison
                    )
                }
                
        except Exception as e:
            return {"success": False, "error": f"Remix performance analysis failed: {str(e)}"}
    
    async def optimize_remix_strategy(self, content_piece_id: int,
                                    current_remixes: List[Dict[str, Any]],
                                    optimization_goals: List[str]) -> Dict[str, Any]:
        """Optimize remix strategy based on performance data"""
        try:
            db = await get_shakes_database()
            async with db.get_session() as session:
                content_piece = await session.get("content_pieces", content_piece_id)
                if not content_piece:
                    return {"success": False, "error": "Content piece not found"}
                
                strategy_analysis = await self._analyze_current_remix_strategy(
                    current_remixes, optimization_goals
                )
                
                optimized_strategy = await self._generate_optimized_strategy(
                    strategy_analysis, optimization_goals
                )
                
                strategy_recommendations = await self._generate_strategy_recommendations(
                    optimized_strategy, strategy_analysis
                )
                
                implementation_plan = await self._create_implementation_plan(
                    optimized_strategy, strategy_recommendations
                )
                
                await self.event_bus.publish_event("remix_strategy_optimized", {
                    "content_piece_id": content_piece_id,
                    "optimization_goals": optimization_goals,
                    "strategy_improvements": len(strategy_recommendations)
                })
                
                return {
                    "success": True,
                    "optimized_strategy": optimized_strategy,
                    "strategy_recommendations": strategy_recommendations,
                    "implementation_plan": implementation_plan,
                    "expected_improvements": await self._predict_strategy_improvements(
                        optimized_strategy, strategy_analysis
                    ),
                    "monitoring_metrics": await self._define_monitoring_metrics(
                        optimized_strategy
                    )
                }
                
        except Exception as e:
            return {"success": False, "error": f"Remix strategy optimization failed: {str(e)}"}
    
    async def _create_remix_variant(self, source_content: Dict[str, Any], 
                                  target_format: str, remix_strategy: str,
                                  customization_options: Dict[str, Any]) -> Dict[str, Any]:
        """Create remix variant for specific format"""
        remix_prompt = await self._create_remix_prompt(
            source_content, target_format, remix_strategy, customization_options
        )
        
        remix_content = await self._generate_remix_content(remix_prompt, target_format)
        
        return {
            "content": remix_content,
            "format_optimizations": await self._apply_format_optimizations(
                remix_content, target_format
            ),
            "platform_adaptations": await self._apply_platform_adaptations(
                remix_content, target_format
            ),
            "audience_customizations": await self._apply_audience_customizations(
                remix_content, customization_options
            )
        }
    
    async def _create_remix_prompt(self, source_content: Dict[str, Any], 
                                 target_format: str, remix_strategy: str,
                                 customization_options: Dict[str, Any]) -> str:
        """Create prompt for content remixing"""
        prompt = f"""
        Remix the following content for {target_format} format:
        
        Source Content:
        Title: {source_content.get('title', '')}
        Content: {source_content.get('content', '')}
        Content Type: {source_content.get('content_type', '')}
        Platform: {source_content.get('platform', '')}
        Target Audience: {source_content.get('target_audience', '')}
        
        Remix Strategy: {remix_strategy}
        Customization Options: {customization_options}
        
        Create a {target_format} version that:
        1. Maintains the core message and value
        2. Adapts to the target format's requirements
        3. Optimizes for the target platform
        4. Engages the target audience effectively
        5. Follows the specified remix strategy
        
        Provide:
        - Adapted content structure
        - Platform-specific optimizations
        - Audience-appropriate tone and style
        - Format-specific enhancements
        - Engagement optimization elements
        """
        
        return prompt
    
    async def _generate_remix_content(self, prompt: str, target_format: str) -> Dict[str, Any]:
        """Generate remix content using AI"""
        try:
            # Use AI Service Manager instead of NLPUtils
            ai_manager = await get_ai_service_manager()
            messages = [{"role": "system", "content": "You are an AI assistant that creates remixed content."}, {"role": "user", "content": prompt}]
            ai_response = await ai_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
            response = ai_response.text_content if ai_response.success else ""
            
            return {
                "remixed_content": response,
                "format_adaptations": await self._extract_format_adaptations(response, target_format),
                "platform_optimizations": await self._extract_platform_optimizations(response, target_format),
                "engagement_elements": await self._extract_engagement_elements(response, target_format)
            }
            
        except Exception as e:
            return {"error": f"Remix content generation failed: {str(e)}"}
    
    async def _save_remix_content(self, remix_metadata: Dict[str, Any], session) -> int:
        """Save remix content to database"""
        remix_data = {
            "source_content_id": remix_metadata["source_content_id"],
            "target_format": remix_metadata["target_format"],
            "remix_strategy": remix_metadata["remix_strategy"],
            "customization_options": remix_metadata["customization_options"],
            "remixed_content": remix_metadata["remixed_content"],
            "created_at": remix_metadata["created_at"],
            "status": "active"
        }
        
        result = await session.execute(
            "INSERT INTO remixed_content (source_content_id, target_format, remix_strategy, customization_options, remixed_content, created_at, status) VALUES (:source_content_id, :target_format, :remix_strategy, :customization_options, :remixed_content, :created_at, :status) RETURNING id",
            remix_data
        )
        
        return result.scalar()
    
    async def _create_automation_config(self, content_piece_id: int,
                                      remix_schedule: Dict[str, Any],
                                      automation_rules: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create automation configuration for remixing"""
        return {
            "content_piece_id": content_piece_id,
            "remix_schedule": remix_schedule,
            "automation_rules": automation_rules,
            "target_formats": remix_schedule.get("target_formats", []),
            "frequency": remix_schedule.get("frequency", "weekly"),
            "trigger_conditions": remix_schedule.get("trigger_conditions", []),
            "customization_rules": automation_rules,
            "created_at": datetime.utcnow()
        }
    
    async def _schedule_remix_tasks(self, automation_config: Dict[str, Any],
                                  remix_schedule: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Schedule remix tasks based on automation config"""
        scheduled_tasks = []
        
        frequency = remix_schedule.get("frequency", "weekly")
        target_formats = remix_schedule.get("target_formats", [])
        
        for target_format in target_formats:
            task = {
                "target_format": target_format,
                "frequency": frequency,
                "next_execution": await self._calculate_next_execution(frequency),
                "automation_rules": automation_config.get("automation_rules", []),
                "customization_options": await self._get_customization_for_format(target_format)
            }
            scheduled_tasks.append(task)
        
        return scheduled_tasks
    
    async def _get_remix_optimization_insights(self, remix_result: Dict[str, Any],
                                             target_format: str) -> Dict[str, Any]:
        """Get optimization insights for remix"""
        return {
            "format_compliance": await self._assess_format_compliance(remix_result, target_format),
            "engagement_potential": await self._assess_engagement_potential(remix_result, target_format),
            "platform_optimization": await self._assess_platform_optimization(remix_result, target_format),
            "audience_alignment": await self._assess_audience_alignment(remix_result, target_format),
            "performance_predictions": await self._predict_remix_performance(remix_result, target_format)
        }
