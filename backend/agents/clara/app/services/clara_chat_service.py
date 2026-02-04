from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload

from ..models import ClaraSupportTicket, ClaraCustomerInteraction, ClaraCustomerFeedback, SupportChannel
from ..database import get_db
from core.ai import get_ai_service_manager, AIServiceManager
from core.utils.platform_integration_loader import (
    get_all_platforms_static, 
    get_all_integrations_static,
    detect_platforms_in_message,
    detect_integrations_in_message,
    get_integrations_by_type
)
from core.utils.agent_user_data import get_all_user_resources_for_agent
from core.utils.agent_config_loader import get_agent_configuration_for_user

# Import ALL Clara services
from .accessibility_service import AccessibilityService
from .agent_training_service import AgentTrainingService
from .ai_faq_builder_service import AIFAQBuilderService
from .analytics_service import AnalyticsService
from .chat_widget_service import ChatWidgetService
from .chatbot_service import ChatbotService
from .crm_integration_service import CRMIntegrationService
from .custom_response_templates_service import CustomResponseTemplatesService
from .custom_workflows_service import CustomWorkflowsService
from .customer_journey_service import CustomerJourneyService
from .customer_loyalty_service import CustomerLoyaltyService
from .gamified_performance_service import GamifiedPerformanceService
from .geo_localization_service import GeoLocalizationService
from .in_store_inquiry_service import InStoreInquiryService
from .knowledge_service import KnowledgeService
from .mobile_app_monitoring_service import MobileAppMonitoringService
from .multi_brand_service import MultiBrandService
from .multi_ticket_resolution_service import MultiTicketResolutionService
from .multilingual_service import MultilingualService
from .offline_support_service import OfflineSupportService
from .onboarding_assistance_service import OnboardingAssistanceService
from .predictive_analytics_service import PredictiveAnalyticsService
from .predictive_issue_detection_service import PredictiveIssueDetectionService
from .proactive_chat_service import ProactiveChatService
from .proactive_notifications_service import ProactiveNotificationsService
from .real_time_notifications_service import RealTimeNotificationsService
from .self_service_portal_service import SelfServicePortalService
from .setup_wizard_service import SetupWizardService
from .social_media_service import SocialMediaService
from .support_service import SupportService
from .voice_sentiment_coaching_service import VoiceSentimentCoachingService
from .voice_service import VoiceService

from core.services.media_service import MediaService
import logging

logger = logging.getLogger(__name__)



class ClaraChatService:
    """Interactive chat service for Clara that provides comprehensive customer support assistance"""
    
    def __init__(self):
        self.ai_service_manager: Optional[AIServiceManager] = None
        
        # Initialize ALL Clara services
        # Note: Heavy initialization (DB, etc.) is deferred until needed or handled by the services themselves
        self.accessibility = AccessibilityService()
        self.agent_training = AgentTrainingService()
        self.ai_faq_builder = AIFAQBuilderService()
        self.analytics = AnalyticsService()
        self.chat_widget = ChatWidgetService()
        self.chatbot = ChatbotService()
        self.crm_integration = CRMIntegrationService()
        self.custom_response_templates = CustomResponseTemplatesService()
        self.custom_workflows = CustomWorkflowsService()
        self.customer_journey = CustomerJourneyService()
        self.customer_loyalty = CustomerLoyaltyService()
        self.gamified_performance = GamifiedPerformanceService()
        self.geo_localization = GeoLocalizationService()
        self.in_store_inquiry = InStoreInquiryService()
        self.knowledge = KnowledgeService()
        self.mobile_app_monitoring = MobileAppMonitoringService()
        self.multi_brand = MultiBrandService()
        self.multi_ticket_resolution = MultiTicketResolutionService()
        self.multilingual = MultilingualService()
        self.offline_support = OfflineSupportService()
        self.onboarding_assistance = OnboardingAssistanceService()
        self.predictive_analytics = PredictiveAnalyticsService()
        self.predictive_issue_detection = PredictiveIssueDetectionService()
        self.proactive_chat = ProactiveChatService()
        self.proactive_notifications = ProactiveNotificationsService()
        self.real_time_notifications = RealTimeNotificationsService()
        self.self_service_portal = SelfServicePortalService()
        self.setup_wizard = SetupWizardService()
        self.social_media = SocialMediaService()
        self.support = SupportService()
        self.voice_sentiment_coaching = VoiceSentimentCoachingService()
        self.voice = VoiceService()
        
        self.media = MediaService()  # Image generation service
        
        # Chat session management
        self.active_sessions = {}
        
        # TODO management
        self.todos = {}
        
        # Common user intents and responses for customer support
        self.intent_responses = {
            "greeting": [
                "Hello! 👋 I'm Clara, your AI-powered customer support assistant. I'm here to help you provide excellent customer service and resolve issues quickly. 🎫",
                "Hi there! ✨ I'm Clara, ready to help you manage customer inquiries, resolve tickets, and improve customer satisfaction. 📞",
                "Welcome! 🌟 I'm Clara, your dedicated customer support partner. Let's deliver exceptional service to your customers! 🤝"
            ],
            # ... (Existing intents kept for fallback)
        }
    
    # ... (Keep existing methods: _get_ai_service_manager, _detect_intent, _break_down_request_into_tasks, _get_fallback_response) ...

    def _generate_thinking_steps(self, intent: str, message: str, user_id: int, db: AsyncSession = None) -> List[str]:
        """Generate thinking steps based on intent and message context, specific to Clara's Support Persona"""
        steps = []
        
        if intent == "ticket_management":
            steps = [
                "Scanning support ticket queue...",
                "Prioritizing based on SLA/Severity...",
                "Evaluating resolution pathways...",
                "Drafting response template..."
            ]
        elif intent == "customer_inquiry":
            steps = [
                "Analyzing customer sentiment...",
                "Searching Knowledge Base...",
                "Checking customer history...",
                "Formulating empathetic reply..."
            ]
        elif intent == "escalation":
            steps = [
                "Assessing risk & complexity...",
                "Identifying Level 2/3 availability...",
                "Packaging escalation context...",
                "Routing to specialized team..."
            ]
        elif intent == "support_analytics":
             steps = [
                "Querying support metrics...",
                "Calculating CSAT/NPS...",
                "Identifying bottleneck trends...",
                "Generating performance insight..."
            ]
        else:
            steps = [
                "Analyzing support request...",
                "Checking available tools...",
                "Reviewing similar cases...",
                "Preparing solution..."
            ]
        
        return steps

    async def process_chat_message(
        self,
        user_id: int,
        message: str,
        session_id: Optional[str] = None,
        db: AsyncSession = None,
        history: Optional[List[Dict[str, Any]]] = None,
        user_resources: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process a chat message from the user and provide intelligent response"""
        try:
            # The database session should be provided by the router
            if not db:
                return {
                    "success": False,
                    "error": "Database session not available"
                }
            
            # Get or create session
            if not session_id:
                session_id = f"session_{user_id}_{datetime.now().timestamp()}"
            
            if session_id not in self.active_sessions:
                self.active_sessions[session_id] = {
                    "user_id": user_id,
                    "created_at": datetime.now(),
                    "message_count": 0,
                    "context": {},
                    "last_intent": None
                }
            
            session = self.active_sessions[session_id]
            session["message_count"] += 1
            
            # Detect intent solely for guiding the system prompt
            simple_intent = self._detect_intent(message)
            
            # Generate dynamic thinking steps
            thinking_steps = self._generate_thinking_steps(simple_intent, message, user_id, db)

            # Gather Context
            user_resources_summary = ""
            try:
                if db and user_id:
                    if not user_resources:
                        from core.utils.agent_user_data import get_all_user_resources_for_agent
                        user_resources = await get_all_user_resources_for_agent(user_id, db)
                    
                    profile = user_resources.get('profile', {})
                    business = user_resources.get('team', {}) # Using team info as proxy for business context if specific business object missing
                    summary = user_resources.get("summary", {})
                    
                    user_resources_summary = f"""
**USER CONTEXT:**
- Name: {profile.get('full_name', 'User')}
- Role: {profile.get('role', 'Support Manager')}
- Company: {profile.get('company', 'Not specified')}
- Industry: {profile.get('industry', 'Not specified')}
- Business Goal: {profile.get('primary_goals', ['Provide excellent support'])}
- Connected Platforms: {summary.get('total_platforms', 0)}
- Connected Tools: {summary.get('total_integrations', 0)} (e.g., Zendesk, Intercom)
"""
            except Exception as e:
                logger.warning(f"Failed to load user context: {e}")

            messages = [
                {
                    "role": "system",
                    "content": f"""You are **Clara**, an elite **AI Customer Support Specialist & Experience Designer**.
{user_resources_summary}

**CORE OBJECTIVE:**
Provide exceptional, empathetic, and efficient customer support. You must distinguish between **RESOLVING** an issue directly, **MANAGING** a ticket, or **EDUCATING** the user.

**CONVERSATIONAL PROTOCOL (CRITICAL):**
1. **No Repetitive Greetings**: If the conversation history exists, skip introductions like "I'm Clara...". Jump straight to the task.
2. **Handle Missing Info**: If the user asks for support analysis (e.g., tickets, feedback, satisfaction) and you don't have that data in the "USER CONTEXT" or current message, **ASK THEM**. Say: "To give you precise support guidance, could you tell me more about [what's missing]?"
3. **Rich Formatting**: Use 📅, 📊, ⚡, 📝, ✅, 🚀, and ✨ as headers for distinct sections and use bullet/numbered lists for details. Match the premium "visual life" of the landing page.
4. **Direct Links**: If a user needs to connect support or CRM tools, use this markdown link: `[Connect Platforms](/account/platforms)`.
5. **Actionable Steps**: End every response with a clear "Next Step" or a specific question to resolve the customer's need.

**CAPABILITIES:**
- **Ticket Management**: Create, prioritize, and route tickets.
- **Support Analytics**: Analyze response times and satisfaction scores.
- **Knowledge Base**: Draft articles, search FAQs.
- **Live Chat**: Optimize chat workflows.
- **CRM Integration**: Sync with Zendesk, HubSpot, etc.

Current User Intent Hint: {simple_intent}
"""
                },
                {"role": "user", "content": message}
            ]
            
            # Add history
            if history:
                history_messages = []
                for h in history[-5:]:
                    history_messages.append({
                        "role": h.get("role", "user"), 
                        "content": h.get("content", "")
                    })
                messages[1:1] = history_messages

            # Execute LLM Call
            ai_manager = await self._get_ai_service_manager()
            from core.config import settings
            
            ai_response = await ai_manager.generate_text(
                messages=messages,
                max_tokens=settings.groq.groq_max_tokens,
                temperature=0.7
            )

            if ai_response.success and ai_response.text_content:
                response_text = ai_response.text_content
                confidence = 0.95
            else:
                logger.error(f"LLM Failure: {ai_response.error}")
                response_text = self._get_fallback_response(simple_intent)
                confidence = 0.5
            
            # Update session
            session["last_intent"] = simple_intent
            
            # Form final result
            result = {
                "success": True,
                "response": response_text,
                "thinking_steps": thinking_steps,
                "intent": simple_intent,
                "confidence": confidence,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }
            
            # Update context
            session["context"]["last_message"] = message
            session["context"]["last_response"] = response_text
            session["context"]["timestamp"] = datetime.now().isoformat()
            
            return result

        except Exception as e:
            logger.error(f"Error processing chat message: {e}") 
            return {
                "success": False,
                "error": f"Failed to process chat message: {str(e)}",
                "session_id": session_id
            }
    
    async def get_session_info(self, session_id: str) -> Dict[str, Any]:
        """Get information about a chat session"""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            return {
                "session_id": session_id,
                "user_id": session["user_id"],
                "created_at": session["created_at"].isoformat(),
                "message_count": session["message_count"],
                "last_intent": session.get("last_intent"),
                "context": session.get("context", {})
            }
        else:
            return {"error": "Session not found"}
    
    # TODO Management Methods
    async def create_todo(self, user_id: int, title: str, description: str = "", priority: str = "medium") -> Dict[str, Any]:
        """Create a new TODO item for the user"""
        try:
            todo_id = f"todo_{user_id}_{datetime.now().timestamp()}"
            todo = {
                "id": todo_id,
                "user_id": user_id,
                "title": title,
                "description": description,
                "priority": priority,
                "status": "pending",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            if user_id not in self.todos:
                self.todos[user_id] = []
            
            self.todos[user_id].append(todo)
            
            return {
                "success": True,
                "todo": todo,
                "message": f"TODO '{title}' created successfully"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to create TODO: {str(e)}"
            }
    
    async def get_todos(self, user_id: int, status: str = "all") -> Dict[str, Any]:
        """Get all TODOs for a user"""
        try:
            if user_id not in self.todos:
                return {
                    "success": True,
                    "todos": [],
                    "count": 0
                }
            
            user_todos = self.todos[user_id]
            
            if status != "all":
                user_todos = [todo for todo in user_todos if todo["status"] == status]
            
            return {
                "success": True,
                "todos": user_todos,
                "count": len(user_todos)
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get TODOs: {str(e)}"
            }
    
    async def update_todo(self, user_id: int, todo_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update a TODO item"""
        try:
            if user_id not in self.todos:
                return {
                    "success": False,
                    "error": "No TODOs found for user"
                }
            
            user_todos = self.todos[user_id]
            todo_index = None
            
            for i, todo in enumerate(user_todos):
                if todo["id"] == todo_id:
                    todo_index = i
                    break
            
            if todo_index is None:
                return {
                    "success": False,
                    "error": "TODO not found"
                }
            
            # Update the TODO
            for key, value in updates.items():
                if key in ["title", "description", "priority", "status"]:
                    user_todos[todo_index][key] = value
            
            user_todos[todo_index]["updated_at"] = datetime.now().isoformat()
            
            return {
                "success": True,
                "todo": user_todos[todo_index],
                "message": "TODO updated successfully"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to update TODO: {str(e)}"
            }
    
    async def delete_todo(self, user_id: int, todo_id: str) -> Dict[str, Any]:
        """Delete a TODO item"""
        try:
            if user_id not in self.todos:
                return {
                    "success": False,
                    "error": "No TODOs found for user"
                }
            
            user_todos = self.todos[user_id]
            todo_index = None
            
            for i, todo in enumerate(user_todos):
                if todo["id"] == todo_id:
                    todo_index = i
                    break
            
            if todo_index is None:
                return {
                    "success": False,
                    "error": "TODO not found"
                }
            
            deleted_todo = user_todos.pop(todo_index)
            
            return {
                "success": True,
                "todo": deleted_todo,
                "message": "TODO deleted successfully"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to delete TODO: {str(e)}"
            }
    
    async def complete_todo(self, user_id: int, todo_id: str) -> Dict[str, Any]:
        """Mark a TODO as completed"""
        return await self.update_todo(user_id, todo_id, {"status": "completed"})
    
    async def get_todo_stats(self, user_id: int) -> Dict[str, Any]:
        """Get TODO statistics for a user"""
        try:
            if user_id not in self.todos:
                return {
                    "success": True,
                    "stats": {
                        "total": 0,
                        "pending": 0,
                        "completed": 0,
                        "in_progress": 0
                    }
                }
            
            user_todos = self.todos[user_id]
            stats = {
                "total": len(user_todos),
                "pending": len([t for t in user_todos if t["status"] == "pending"]),
                "completed": len([t for t in user_todos if t["status"] == "completed"]),
                "in_progress": len([t for t in user_todos if t["status"] == "in_progress"])
            }
            
            return {
                "success": True,
                "stats": stats
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get TODO stats: {str(e)}"
            }
    
    async def clear_session(self, session_id: str) -> Dict[str, Any]:
        """Clear a chat session"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            return {"success": True, "message": "Session cleared"}
        else:
            return {"success": False, "error": "Session not found"}