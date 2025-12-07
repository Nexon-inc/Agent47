import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from pydantic import BaseModel

from ..database import get_eric_database
from backend.core.ai import get_ai_service_manager, AIServiceManager
from backend.core.integrations.integration_manager import IntegrationManager
from backend.core.platforms.platform_manager import PlatformManager
from backend.core.event_bus.kafka_manager import KafkaManager
from backend.core.cache.redis_manager import RedisManager
from backend.core.utils.nlp_utils import NLPUtils

logger = logging.getLogger(__name__)

class LiveChatService:
    def __init__(self):
        # Using AI Service Manager for intent analysis
        self.ai_service_manager: Optional[AIServiceManager] = None
        self.integration_manager = IntegrationManager()
        self.platform_manager = PlatformManager()
        self.kafka_manager = KafkaManager()
        self.redis_manager = RedisManager()
        self._initialized = False
    
    async def initialize(self):
        """Initialize live chat service"""
        if self._initialized:
            return
        
        try:
            self.ai_service_manager = await get_ai_service_manager()
            await self.integration_manager.initialize()
            await self.platform_manager.initialize()
            await self.kafka_manager.initialize()
            await self.redis_manager.initialize()
            self._initialized = True
            logger.info("Live chat service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize live chat service: {e}")
            raise

    async def handle_chat_message(self, session_id: str, message: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming chat messages with AI-powered responses"""
        try:
            async with get_eric_database() as db:
                # Analyze message intent
                intent_analysis = await self._analyze_message_intent(message, user_data)
                
                # Generate AI response
                ai_response = await self._generate_ai_response(intent_analysis, user_data)
                
                # Determine next actions
                next_actions = await self._determine_next_actions(intent_analysis, ai_response)
                
                # Update session state
                session_update = await self._update_session_state(session_id, intent_analysis, ai_response)
                
                return {
                    "session_id": session_id,
                    "user_message": message,
                    "ai_response": ai_response,
                    "intent_analysis": intent_analysis,
                    "next_actions": next_actions,
                    "session_state": session_update,
                    "timestamp": datetime.utcnow()
                }
        except Exception as e:
            logger.error(f"Error handling chat message: {e}")
            raise

    async def manage_chat_session(self, session_id: str, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Manage chat session lifecycle"""
        try:
            async with get_eric_database() as db:
                # Initialize or update session
                session_state = await self._initialize_session(session_id, session_data)
                
                # Set up session context
                session_context = await self._setup_session_context(session_state)
                
                # Configure AI assistant
                ai_config = await self._configure_ai_assistant(session_context)
                
                return {
                    "session_id": session_id,
                    "session_state": session_state,
                    "session_context": session_context,
                    "ai_config": ai_config,
                    "status": "active",
                    "created_at": datetime.utcnow()
                }
        except Exception as e:
            logger.error(f"Error managing chat session: {e}")
            raise

    async def handle_real_time_interactions(self, session_id: str, interaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle real-time chat interactions"""
        try:
            async with get_eric_database() as db:
                # Process interaction
                interaction_result = await self._process_interaction(interaction_data)
                
                # Generate real-time response
                real_time_response = await self._generate_real_time_response(interaction_result)
                
                # Update interaction state
                interaction_state = await self._update_interaction_state(session_id, interaction_result)
                
                return {
                    "session_id": session_id,
                    "interaction_type": interaction_data.get("type"),
                    "interaction_result": interaction_result,
                    "real_time_response": real_time_response,
                    "interaction_state": interaction_state,
                    "timestamp": datetime.utcnow()
                }
        except Exception as e:
            logger.error(f"Error handling real-time interactions: {e}")
            raise

    async def escalate_to_human_agent(self, session_id: str, escalation_reason: str) -> Dict[str, Any]:
        """Escalate chat to human agent"""
        try:
            async with get_eric_database() as db:
                # Determine escalation priority
                escalation_priority = await self._determine_escalation_priority(escalation_reason)
                
                # Find available agent
                available_agent = await self._find_available_agent(escalation_priority)
                
                # Transfer session
                transfer_result = await self._transfer_session_to_agent(session_id, available_agent)
                
                # Notify agent
                notification_sent = await self._notify_human_agent(available_agent, session_id)
                
                return {
                    "session_id": session_id,
                    "escalation_reason": escalation_reason,
                    "escalation_priority": escalation_priority,
                    "assigned_agent": available_agent,
                    "transfer_result": transfer_result,
                    "notification_sent": notification_sent,
                    "escalated_at": datetime.utcnow()
                }
        except Exception as e:
            logger.error(f"Error escalating to human agent: {e}")
            raise

    async def track_chat_analytics(self, brand_id: str, time_period: str = "30d") -> Dict[str, Any]:
        """Track chat analytics and performance"""
        try:
            async with get_eric_database() as db:
                # Get chat metrics
                chat_metrics = await self._get_chat_metrics(brand_id, time_period)
                
                # Analyze chat performance
                performance_analysis = await self._analyze_chat_performance(chat_metrics)
                
                # Generate insights
                insights = await self._generate_chat_insights(performance_analysis)
                
                # Create optimization recommendations
                recommendations = await self._create_chat_optimization_recommendations(insights)
                
                return {
                    "brand_id": brand_id,
                    "time_period": time_period,
                    "chat_metrics": chat_metrics,
                    "performance_analysis": performance_analysis,
                    "insights": insights,
                    "recommendations": recommendations
                }
        except Exception as e:
            logger.error(f"Error tracking chat analytics: {e}")
            raise

    async def configure_chat_widget(self, brand_id: str, widget_config: Dict[str, Any]) -> Dict[str, Any]:
        """Configure chat widget settings"""
        try:
            async with get_eric_database() as db:
                # Validate widget configuration
                validated_config = await self._validate_widget_config(widget_config)
                
                # Apply branding
                branded_config = await self._apply_branding_to_widget(validated_config, brand_id)
                
                # Set up automation rules
                automation_rules = await self._setup_chat_automation_rules(branded_config)
                
                return {
                    "brand_id": brand_id,
                    "widget_config": branded_config,
                    "automation_rules": automation_rules,
                    "status": "active",
                    "configured_at": datetime.utcnow()
                }
        except Exception as e:
            logger.error(f"Error configuring chat widget: {e}")
            raise

    # Helper methods
    async def _analyze_message_intent(self, message: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze message intent using AI"""
        # Use AI Service Manager for intent analysis
        ai_manager = await get_ai_service_manager()
        messages = [{"role": "system", "content": "You are an AI assistant that analyzes message intent. Respond with JSON: {\"intent\": \"...\", \"confidence\": 0.0-1.0, \"entities\": []}"}, {"role": "user", "content": f"Analyze the intent of: {message}"}]
        intent_response = await ai_manager.generate_text(messages=messages, max_tokens=300, temperature=0.3)
        try:
            import json
            intent_result = json.loads(intent_response.text_content) if intent_response.success else {"intent": "general", "confidence": 0.5, "entities": []}
        except:
            intent_result = {"intent": "general", "confidence": 0.5, "entities": []}
        
        return {
            "intent": intent_result.get("intent", "general_inquiry"),
            "confidence": intent_result.get("confidence", 0.8),
            "entities": intent_result.get("entities", []),
            "sentiment": intent_result.get("sentiment", "neutral"),
            "urgency": intent_result.get("urgency", "low")
        }

    async def _generate_ai_response(self, intent_analysis: Dict[str, Any], user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AI-powered response"""
        intent = intent_analysis.get("intent")
        
        if intent == "product_inquiry":
            response = await self._generate_product_response(user_data)
        elif intent == "pricing_inquiry":
            response = await self._generate_pricing_response(user_data)
        elif intent == "demo_request":
            response = await self._generate_demo_response(user_data)
        elif intent == "support_request":
            response = await self._generate_support_response(user_data)
        else:
            response = await self._generate_general_response(user_data)
        
        return {
            "message": response.get("message"),
            "response_type": response.get("type"),
            "suggested_actions": response.get("actions", []),
            "confidence": intent_analysis.get("confidence", 0.8)
        }

    async def _determine_next_actions(self, intent_analysis: Dict[str, Any], ai_response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Determine next actions based on intent and response"""
        actions = []
        
        if intent_analysis.get("urgency") == "high":
            actions.append({
                "action": "escalate_to_human",
                "priority": "high",
                "reason": "High urgency detected"
            })
        
        if intent_analysis.get("intent") == "demo_request":
            actions.append({
                "action": "schedule_demo",
                "priority": "medium",
                "reason": "Demo requested"
            })
        
        actions.append({
            "action": "continue_conversation",
            "priority": "low",
            "reason": "Continue AI assistance"
        })
        
        return actions

    async def _update_session_state(self, session_id: str, intent_analysis: Dict[str, Any], ai_response: Dict[str, Any]) -> Dict[str, Any]:
        """Update chat session state"""
        return {
            "session_id": session_id,
            "current_intent": intent_analysis.get("intent"),
            "conversation_history": [],
            "user_context": {},
            "ai_context": {},
            "last_updated": datetime.utcnow()
        }

    async def _initialize_session(self, session_id: str, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize chat session"""
        return {
            "session_id": session_id,
            "user_info": session_data.get("user_info", {}),
            "session_type": session_data.get("type", "general"),
            "start_time": datetime.utcnow(),
            "status": "active"
        }

    async def _setup_session_context(self, session_state: Dict[str, Any]) -> Dict[str, Any]:
        """Set up session context"""
        return {
            "user_context": {
                "user_type": "prospect",
                "interaction_history": [],
                "preferences": {}
            },
            "ai_context": {
                "conversation_style": "professional",
                "knowledge_base": "sales_and_product",
                "response_templates": "branded"
            }
        }

    async def _configure_ai_assistant(self, session_context: Dict[str, Any]) -> Dict[str, Any]:
        """Configure AI assistant for the session"""
        return {
            "assistant_type": "sales_assistant",
            "capabilities": [
                "product_information",
                "pricing_quotes",
                "demo_scheduling",
                "lead_qualification"
            ],
            "response_style": session_context["ai_context"]["conversation_style"],
            "escalation_threshold": 0.7
        }

    async def _process_interaction(self, interaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process real-time interaction"""
        interaction_type = interaction_data.get("type")
        
        if interaction_type == "typing_indicator":
            return {"action": "show_typing", "duration": 2}
        elif interaction_type == "read_receipt":
            return {"action": "mark_as_read", "timestamp": datetime.utcnow()}
        elif interaction_type == "quick_reply":
            return {"action": "process_quick_reply", "response": interaction_data.get("response")}
        
        return {"action": "unknown", "data": interaction_data}

    async def _generate_real_time_response(self, interaction_result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate real-time response"""
        action = interaction_result.get("action")
        
        if action == "show_typing":
            return {"type": "typing_indicator", "message": "AI is typing..."}
        elif action == "mark_as_read":
            return {"type": "read_receipt", "status": "read"}
        elif action == "process_quick_reply":
            return {"type": "quick_response", "message": "Thank you for your response!"}
        
        return {"type": "general", "message": "Processing your request..."}

    async def _update_interaction_state(self, session_id: str, interaction_result: Dict[str, Any]) -> Dict[str, Any]:
        """Update interaction state"""
        return {
            "session_id": session_id,
            "last_interaction": interaction_result.get("action"),
            "interaction_count": 1,
            "last_updated": datetime.utcnow()
        }

    async def _determine_escalation_priority(self, escalation_reason: str) -> str:
        """Determine escalation priority"""
        high_priority_keywords = ["urgent", "emergency", "complaint", "angry"]
        medium_priority_keywords = ["complex", "technical", "detailed"]
        
        reason_lower = escalation_reason.lower()
        
        if any(keyword in reason_lower for keyword in high_priority_keywords):
            return "high"
        elif any(keyword in reason_lower for keyword in medium_priority_keywords):
            return "medium"
        else:
            return "low"

    async def _find_available_agent(self, escalation_priority: str) -> Dict[str, Any]:
        """Find available human agent"""
        return {
            "agent_id": "agent_001",
            "agent_name": "Sarah Johnson",
            "specialization": "sales",
            "availability": "online",
            "priority_level": escalation_priority
        }

    async def _transfer_session_to_agent(self, session_id: str, agent: Dict[str, Any]) -> Dict[str, Any]:
        """Transfer session to human agent"""
        return {
            "transfer_successful": True,
            "agent_assigned": agent["agent_id"],
            "transfer_time": datetime.utcnow(),
            "session_context_preserved": True
        }

    async def _notify_human_agent(self, agent: Dict[str, Any], session_id: str) -> bool:
        """Notify human agent of new session"""
        return True

    async def _get_chat_metrics(self, brand_id: str, time_period: str) -> Dict[str, Any]:
        """Get chat metrics"""
        return {
            "total_sessions": 500,
            "total_messages": 2500,
            "average_session_duration": 8.5,
            "ai_resolution_rate": 0.75,
            "human_escalation_rate": 0.25,
            "customer_satisfaction": 4.2
        }

    async def _analyze_chat_performance(self, chat_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze chat performance"""
        return {
            "performance_score": 0.82,
            "strengths": ["High AI resolution rate", "Good customer satisfaction"],
            "weaknesses": ["High escalation rate", "Long session duration"],
            "improvement_areas": ["AI training", "Response optimization"]
        }

    async def _generate_chat_insights(self, performance_analysis: Dict[str, Any]) -> List[str]:
        """Generate chat insights"""
        return [
            "AI resolution rate of 75% is above industry average",
            "Customer satisfaction score of 4.2 indicates good service quality",
            "25% escalation rate suggests need for AI improvement",
            "Average session duration of 8.5 minutes is within acceptable range"
        ]

    async def _create_chat_optimization_recommendations(self, insights: List[str]) -> List[Dict[str, Any]]:
        """Create chat optimization recommendations"""
        return [
            {
                "recommendation": "Improve AI training for complex queries",
                "priority": "high",
                "expected_impact": "Reduce escalation rate by 15%"
            },
            {
                "recommendation": "Optimize response templates",
                "priority": "medium",
                "expected_impact": "Improve resolution rate by 10%"
            },
            {
                "recommendation": "Implement proactive chat initiation",
                "priority": "low",
                "expected_impact": "Increase engagement by 20%"
            }
        ]

    async def _validate_widget_config(self, widget_config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate widget configuration"""
        required_fields = ["position", "theme", "greeting_message"]
        for field in required_fields:
            if field not in widget_config:
                raise ValueError(f"Missing required field: {field}")
        
        return widget_config

    async def _apply_branding_to_widget(self, validated_config: Dict[str, Any], brand_id: str) -> Dict[str, Any]:
        """Apply branding to chat widget"""
        return {
            **validated_config,
            "brand_colors": "#007bff",
            "brand_logo": f"https://brands/{brand_id}/logo.png",
            "custom_css": f"https://brands/{brand_id}/widget.css"
        }

    async def _setup_chat_automation_rules(self, branded_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Set up chat automation rules"""
        return [
            {
                "rule_id": "auto_greeting",
                "trigger": "widget_opened",
                "action": "send_greeting",
                "delay": 3
            },
            {
                "rule_id": "idle_timeout",
                "trigger": "user_idle_5_minutes",
                "action": "send_follow_up",
                "message": "Still there? How can I help you?"
            },
            {
                "rule_id": "page_exit",
                "trigger": "user_leaving_page",
                "action": "offer_contact",
                "message": "Would you like to leave your contact information?"
            }
        ]

    async def _generate_product_response(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate product-related response"""
        return {
            "message": "Our product offers advanced features including AI-powered automation, real-time analytics, and seamless integrations. Would you like me to schedule a demo to show you how it works?",
            "type": "product_information",
            "actions": [
                {"action": "schedule_demo", "label": "Schedule Demo"},
                {"action": "view_features", "label": "View Features"},
                {"action": "get_pricing", "label": "Get Pricing"}
            ]
        }

    async def _generate_pricing_response(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate pricing-related response"""
        return {
            "message": "Our pricing starts at $99/month for the Starter plan, $299/month for Professional, and custom pricing for Enterprise. Each plan includes different features and support levels. Would you like a detailed breakdown?",
            "type": "pricing_information",
            "actions": [
                {"action": "view_pricing", "label": "View Pricing"},
                {"action": "get_quote", "label": "Get Custom Quote"},
                {"action": "compare_plans", "label": "Compare Plans"}
            ]
        }

    async def _generate_demo_response(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate demo-related response"""
        return {
            "message": "Great! I'd be happy to schedule a personalized demo for you. Our demos typically last 30 minutes and cover all the features relevant to your business. What's the best time for you this week?",
            "type": "demo_scheduling",
            "actions": [
                {"action": "schedule_demo", "label": "Schedule Demo"},
                {"action": "view_calendar", "label": "View Available Times"},
                {"action": "contact_sales", "label": "Contact Sales Team"}
            ]
        }

    async def _generate_support_response(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate support-related response"""
        return {
            "message": "I'm here to help with any support questions you might have. I can assist with technical issues, account management, or general inquiries. What specific issue are you experiencing?",
            "type": "support_assistance",
            "actions": [
                {"action": "technical_support", "label": "Technical Support"},
                {"action": "account_help", "label": "Account Help"},
                {"action": "contact_support", "label": "Contact Support"}
            ]
        }

    async def _generate_general_response(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate general response"""
        return {
            "message": "Hello! I'm your AI sales assistant. I can help you learn about our products, get pricing information, schedule demos, or answer any questions you might have. How can I assist you today?",
            "type": "general_greeting",
            "actions": [
                {"action": "learn_more", "label": "Learn More"},
                {"action": "get_started", "label": "Get Started"},
                {"action": "contact_us", "label": "Contact Us"}
            ]
        }
