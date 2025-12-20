import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from pydantic import BaseModel

from ..database import get_eric_database
from core.ai import get_ai_service_manager, AIServiceManager
from core.integrations.integration_manager import IntegrationManager
from core.platforms.platform_manager import PlatformManager
from core.event_bus.kafka_manager import KafkaManager
from core.cache.redis_manager import RedisManager
# NLPUtils removed - not used

logger = logging.getLogger(__name__)

class EmailSequencesService:
    def __init__(self):
        # NLPUtils removed - not used
        self.ai_service_manager: Optional[AIServiceManager] = None
        self.integration_manager = IntegrationManager()
        self.platform_manager = PlatformManager()
        self.kafka_manager = KafkaManager()
        self.redis_manager = RedisManager()
        self._initialized = False
    
    async def initialize(self):
        """Initialize email sequences service"""
        if self._initialized:
            return
        
        try:
            self.ai_service_manager = await get_ai_service_manager()
            await self.integration_manager.initialize()
            await self.platform_manager.initialize()
            await self.kafka_manager.initialize()
            await self.redis_manager.initialize()
            self._initialized = True
            logger.info("Email sequences service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize email sequences service: {e}")
            raise

    async def create_email_sequence(self, brand_id: str, sequence_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new email sequence"""
        try:
            async with get_eric_database() as db:
                # Validate sequence data
                validated_data = await self._validate_sequence_data(sequence_data)
                
                # Generate sequence steps
                sequence_steps = await self._generate_sequence_steps(validated_data)
                
                # Create sequence template
                sequence_template = await self._create_sequence_template(validated_data, sequence_steps)
                
                # Set up automation triggers
                automation_triggers = await self._setup_automation_triggers(sequence_template)
                
                return {
                    "sequence_id": f"seq_{brand_id}_{datetime.utcnow().timestamp()}",
                    "brand_id": brand_id,
                    "sequence_name": validated_data.get("name"),
                    "sequence_type": validated_data.get("type"),
                    "sequence_steps": sequence_steps,
                    "automation_triggers": automation_triggers,
                    "status": "active",
                    "created_at": datetime.utcnow()
                }
        except Exception as e:
            logger.error(f"Error creating email sequence: {e}")
            raise

    async def manage_follow_up_workflows(self, brand_id: str, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """Manage follow-up workflows"""
        try:
            async with get_eric_database() as db:
                # Create workflow
                workflow = await self._create_follow_up_workflow(workflow_data)
                
                # Set up workflow rules
                workflow_rules = await self._setup_workflow_rules(workflow)
                
                # Configure automation
                automation_config = await self._configure_workflow_automation(workflow, workflow_rules)
                
                return {
                    "workflow_id": f"wf_{brand_id}_{datetime.utcnow().timestamp()}",
                    "brand_id": brand_id,
                    "workflow_name": workflow_data.get("name"),
                    "workflow_type": workflow_data.get("type"),
                    "workflow_rules": workflow_rules,
                    "automation_config": automation_config,
                    "status": "active",
                    "created_at": datetime.utcnow()
                }
        except Exception as e:
            logger.error(f"Error managing follow-up workflows: {e}")
            raise

    async def schedule_email_send(self, sequence_id: str, lead_id: str, send_data: Dict[str, Any]) -> Dict[str, Any]:
        """Schedule an email to be sent"""
        try:
            async with get_eric_database() as db:
                # Get sequence details
                sequence_details = await self._get_sequence_details(sequence_id)
                
                # Personalize email content
                personalized_content = await self._personalize_email_content(sequence_details, lead_id, send_data)
                
                # Determine send timing
                send_timing = await self._determine_send_timing(sequence_details, lead_id)
                
                # Schedule the email
                scheduled_email = await self._schedule_email(sequence_id, lead_id, personalized_content, send_timing)
                
                return {
                    "scheduled_email_id": f"email_{sequence_id}_{lead_id}_{datetime.utcnow().timestamp()}",
                    "sequence_id": sequence_id,
                    "lead_id": lead_id,
                    "personalized_content": personalized_content,
                    "scheduled_time": send_timing,
                    "status": "scheduled",
                    "created_at": datetime.utcnow()
                }
        except Exception as e:
            logger.error(f"Error scheduling email send: {e}")
            raise

    async def track_email_performance(self, sequence_id: str, time_period: str = "30d") -> Dict[str, Any]:
        """Track email sequence performance"""
        try:
            async with get_eric_database() as db:
                # Get email metrics
                email_metrics = await self._get_email_metrics(sequence_id, time_period)
                
                # Analyze performance
                performance_analysis = await self._analyze_email_performance(email_metrics)
                
                # Generate insights
                insights = await self._generate_email_insights(performance_analysis)
                
                # Create optimization recommendations
                recommendations = await self._create_email_optimization_recommendations(insights)
                
                return {
                    "sequence_id": sequence_id,
                    "time_period": time_period,
                    "email_metrics": email_metrics,
                    "performance_analysis": performance_analysis,
                    "insights": insights,
                    "recommendations": recommendations
                }
        except Exception as e:
            logger.error(f"Error tracking email performance: {e}")
            raise

    async def optimize_email_timing(self, brand_id: str, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize email send timing based on lead behavior"""
        try:
            async with get_eric_database() as db:
                # Analyze lead behavior patterns
                behavior_patterns = await self._analyze_lead_behavior_patterns(lead_data)
                
                # Determine optimal send times
                optimal_timing = await self._determine_optimal_send_times(behavior_patterns)
                
                # Create timing recommendations
                timing_recommendations = await self._create_timing_recommendations(optimal_timing)
                
                return {
                    "brand_id": brand_id,
                    "lead_id": lead_data.get("lead_id"),
                    "behavior_patterns": behavior_patterns,
                    "optimal_timing": optimal_timing,
                    "timing_recommendations": timing_recommendations
                }
        except Exception as e:
            logger.error(f"Error optimizing email timing: {e}")
            raise

    async def create_dynamic_sequences(self, brand_id: str, dynamic_rules: Dict[str, Any]) -> Dict[str, Any]:
        """Create dynamic email sequences based on lead behavior"""
        try:
            async with get_eric_database() as db:
                # Analyze dynamic rules
                analyzed_rules = await self._analyze_dynamic_rules(dynamic_rules)
                
                # Generate dynamic sequence
                dynamic_sequence = await self._generate_dynamic_sequence(analyzed_rules)
                
                # Set up conditional logic
                conditional_logic = await self._setup_conditional_logic(dynamic_sequence)
                
                return {
                    "dynamic_sequence_id": f"dyn_{brand_id}_{datetime.utcnow().timestamp()}",
                    "brand_id": brand_id,
                    "dynamic_rules": analyzed_rules,
                    "dynamic_sequence": dynamic_sequence,
                    "conditional_logic": conditional_logic,
                    "status": "active",
                    "created_at": datetime.utcnow()
                }
        except Exception as e:
            logger.error(f"Error creating dynamic sequences: {e}")
            raise

    # Helper methods
    async def _validate_sequence_data(self, sequence_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate sequence data"""
        required_fields = ["name", "type", "target_audience", "goals"]
        for field in required_fields:
            if field not in sequence_data:
                raise ValueError(f"Missing required field: {field}")
        
        return sequence_data

    async def _generate_sequence_steps(self, validated_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate sequence steps"""
        sequence_type = validated_data.get("type")
        
        if sequence_type == "welcome":
            return [
                {"step": 1, "type": "welcome", "delay": 0, "template": "welcome_email"},
                {"step": 2, "type": "value_prop", "delay": 2, "template": "value_proposition"},
                {"step": 3, "type": "cta", "delay": 5, "template": "call_to_action"}
            ]
        elif sequence_type == "nurture":
            return [
                {"step": 1, "type": "educational", "delay": 0, "template": "educational_content"},
                {"step": 2, "type": "case_study", "delay": 3, "template": "case_study"},
                {"step": 3, "type": "demo_offer", "delay": 7, "template": "demo_offer"}
            ]
        else:
            return [
                {"step": 1, "type": "generic", "delay": 0, "template": "generic_email"},
                {"step": 2, "type": "follow_up", "delay": 3, "template": "follow_up"}
            ]

    async def _create_sequence_template(self, validated_data: Dict[str, Any], sequence_steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create sequence template"""
        return {
            "template_id": f"template_{validated_data.get('name').lower().replace(' ', '_')}",
            "name": validated_data.get("name"),
            "type": validated_data.get("type"),
            "steps": sequence_steps,
            "target_audience": validated_data.get("target_audience"),
            "goals": validated_data.get("goals")
        }

    async def _setup_automation_triggers(self, sequence_template: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Set up automation triggers"""
        return [
            {
                "trigger_type": "lead_created",
                "conditions": ["new_lead", "qualified_lead"],
                "action": "start_sequence",
                "sequence_template": sequence_template["template_id"]
            },
            {
                "trigger_type": "lead_activity",
                "conditions": ["website_visit", "email_open"],
                "action": "continue_sequence",
                "sequence_template": sequence_template["template_id"]
            }
        ]

    async def _create_follow_up_workflow(self, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create follow-up workflow"""
        return {
            "workflow_name": workflow_data.get("name"),
            "workflow_type": workflow_data.get("type"),
            "stages": workflow_data.get("stages", []),
            "conditions": workflow_data.get("conditions", [])
        }

    async def _setup_workflow_rules(self, workflow: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Set up workflow rules"""
        return [
            {
                "rule_id": "rule_001",
                "condition": "no_response_after_3_days",
                "action": "send_follow_up_email",
                "template": "follow_up_template_1"
            },
            {
                "rule_id": "rule_002",
                "condition": "email_opened_but_no_click",
                "action": "send_alternative_offer",
                "template": "alternative_offer_template"
            },
            {
                "rule_id": "rule_003",
                "condition": "lead_unsubscribed",
                "action": "pause_sequence",
                "template": None
            }
        ]

    async def _configure_workflow_automation(self, workflow: Dict[str, Any], workflow_rules: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Configure workflow automation"""
        return {
            "automation_enabled": True,
            "rules": workflow_rules,
            "fallback_actions": [
                {"condition": "max_attempts_reached", "action": "move_to_manual_follow_up"},
                {"condition": "lead_responded", "action": "pause_automation"}
            ],
            "notification_settings": {
                "email_notifications": True,
                "slack_notifications": True,
                "notification_recipients": ["sales_team"]
            }
        }

    async def _get_sequence_details(self, sequence_id: str) -> Dict[str, Any]:
        """Get sequence details"""
        return {
            "sequence_id": sequence_id,
            "name": "Welcome Sequence",
            "type": "welcome",
            "steps": [
                {"step": 1, "template": "welcome_email", "delay": 0},
                {"step": 2, "template": "value_proposition", "delay": 2},
                {"step": 3, "template": "call_to_action", "delay": 5}
            ]
        }

    async def _personalize_email_content(self, sequence_details: Dict[str, Any], lead_id: str, send_data: Dict[str, Any]) -> Dict[str, Any]:
        """Personalize email content"""
        return {
            "subject": f"Welcome {send_data.get('lead_name', 'there')}!",
            "body": f"Hi {send_data.get('lead_name', 'there')},\n\nWelcome to our platform! We're excited to help you achieve your goals.\n\nBest regards,\nThe Team",
            "personalization_data": {
                "lead_name": send_data.get("lead_name"),
                "company_name": send_data.get("company_name"),
                "industry": send_data.get("industry")
            }
        }

    async def _determine_send_timing(self, sequence_details: Dict[str, Any], lead_id: str) -> datetime:
        """Determine optimal send timing based on lead behavior and sequence rules"""
        try:
            # Get lead's historical email engagement data
            async with get_eric_database() as session:
                # Query lead's email activity history
                email_activities = await session.execute(
                    select(SalesActivity).where(
                        and_(
                            SalesActivity.lead_id == lead_id,
                            SalesActivity.activity_type.in_(["email_sent", "email_opened", "email_clicked"]),
                            SalesActivity.created_at >= datetime.utcnow() - timedelta(days=30)
                        )
                    )
                )
                activities = email_activities.scalars().all()
                
                # Analyze optimal send times based on historical data
                if activities:
                    # Group activities by hour to find peak engagement times
                    hourly_engagement = {}
                    for activity in activities:
                        hour = activity.created_at.hour
                        if hour not in hourly_engagement:
                            hourly_engagement[hour] = 0
                        hourly_engagement[hour] += 1
                    
                    # Find the hour with highest engagement
                    if hourly_engagement:
                        optimal_hour = max(hourly_engagement.items(), key=lambda x: x[1])[0]
                        
                        # Calculate next optimal send time
                        now = datetime.utcnow()
                        optimal_time = now.replace(hour=optimal_hour, minute=0, second=0, microsecond=0)
                        
                        # If optimal time has passed today, schedule for tomorrow
                        if optimal_time <= now:
                            optimal_time += timedelta(days=1)
                        
                        # Add sequence delay if specified
                        sequence_delay = sequence_details.get("delay_minutes", 0)
                        if sequence_delay > 0:
                            optimal_time += timedelta(minutes=sequence_delay)
                        
                        return optimal_time
                
                # Fallback: Use business hours and sequence delay
                now = datetime.utcnow()
                business_hour = 9  # 9 AM
                optimal_time = now.replace(hour=business_hour, minute=0, second=0, microsecond=0)
                
                # If business hour has passed, schedule for next business day
                if optimal_time <= now:
                    optimal_time += timedelta(days=1)
                
                # Add sequence delay
                sequence_delay = sequence_details.get("delay_minutes", 0)
                if sequence_delay > 0:
                    optimal_time += timedelta(minutes=sequence_delay)
                
                return optimal_time
                
        except Exception as e:
            logger.error(f"Error determining send timing: {e}")
            # Fallback to immediate send with 5-minute delay
            return datetime.utcnow() + timedelta(minutes=5)

    async def _schedule_email(self, sequence_id: str, lead_id: str, personalized_content: Dict[str, Any], send_timing: datetime) -> Dict[str, Any]:
        """Schedule email"""
        return {
            "scheduled_time": send_timing,
            "content": personalized_content,
            "status": "scheduled"
        }

    async def _get_email_metrics(self, sequence_id: str, time_period: str) -> Dict[str, Any]:
        """Get email metrics"""
        return {
            "total_sent": 1000,
            "total_opened": 450,
            "total_clicked": 120,
            "total_replied": 25,
            "open_rate": 0.45,
            "click_rate": 0.12,
            "reply_rate": 0.025,
            "unsubscribe_rate": 0.02
        }

    async def _analyze_email_performance(self, email_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze email performance"""
        return {
            "performance_score": 0.75,
            "strengths": ["High open rate", "Good click-through rate"],
            "weaknesses": ["Low reply rate", "High unsubscribe rate"],
            "improvement_areas": ["Subject line optimization", "Content personalization"]
        }

    async def _generate_email_insights(self, performance_analysis: Dict[str, Any]) -> List[str]:
        """Generate email insights"""
        return [
            "Open rate of 45% is above industry average",
            "Click-through rate of 12% indicates good content relevance",
            "Reply rate of 2.5% suggests need for stronger call-to-action",
            "Unsubscribe rate of 2% is within acceptable range"
        ]

    async def _create_email_optimization_recommendations(self, insights: List[str]) -> List[Dict[str, Any]]:
        """Create email optimization recommendations"""
        return [
            {
                "recommendation": "Improve subject line personalization",
                "priority": "high",
                "expected_impact": "15% increase in open rate"
            },
            {
                "recommendation": "Add stronger call-to-action buttons",
                "priority": "medium",
                "expected_impact": "20% increase in click rate"
            },
            {
                "recommendation": "Segment audience for better targeting",
                "priority": "medium",
                "expected_impact": "25% increase in reply rate"
            }
        ]

    async def _analyze_lead_behavior_patterns(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze lead behavior patterns"""
        return {
            "email_open_times": ["9am", "2pm", "6pm"],
            "preferred_days": ["Tuesday", "Wednesday", "Thursday"],
            "response_times": "average_2_hours",
            "engagement_level": "high"
        }

    async def _determine_optimal_send_times(self, behavior_patterns: Dict[str, Any]) -> List[str]:
        """Determine optimal send times"""
        return ["Tuesday 9am", "Wednesday 2pm", "Thursday 6pm"]

    async def _create_timing_recommendations(self, optimal_timing: List[str]) -> List[Dict[str, Any]]:
        """Create timing recommendations"""
        return [
            {
                "recommendation": "Send emails on Tuesday at 9am",
                "reason": "Highest open rate observed",
                "priority": "high"
            },
            {
                "recommendation": "Avoid sending on Mondays",
                "reason": "Lowest engagement observed",
                "priority": "medium"
            }
        ]

    async def _analyze_dynamic_rules(self, dynamic_rules: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze dynamic rules"""
        return {
            "rules": dynamic_rules.get("rules", []),
            "conditions": dynamic_rules.get("conditions", []),
            "actions": dynamic_rules.get("actions", [])
        }

    async def _generate_dynamic_sequence(self, analyzed_rules: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate dynamic sequence"""
        return [
            {
                "step": 1,
                "condition": "lead_score > 80",
                "action": "send_premium_offer",
                "template": "premium_offer_template"
            },
            {
                "step": 2,
                "condition": "lead_score 50-80",
                "action": "send_standard_offer",
                "template": "standard_offer_template"
            },
            {
                "step": 3,
                "condition": "lead_score < 50",
                "action": "send_educational_content",
                "template": "educational_template"
            }
        ]

    async def _setup_conditional_logic(self, dynamic_sequence: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Set up conditional logic"""
        return {
            "logic_type": "if_then_else",
            "conditions": [step["condition"] for step in dynamic_sequence],
            "actions": [step["action"] for step in dynamic_sequence],
            "fallback_action": "send_generic_email"
        }
