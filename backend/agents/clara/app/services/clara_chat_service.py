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
                    summary = user_resources.get("summary", {})
                    platforms = user_resources.get("platforms", [])
                    integrations = user_resources.get("integrations", [])
                    
                    # Explicit connection status strings
                    platform_status = ", ".join([f"{p['display_name']}: {p['status']}" for p in platforms]) or "None connected"
                    tool_status = ", ".join([f"{i['integration_name']}: {i['status']}" for i in integrations]) or "None connected"
                    
                    user_resources_summary = f"""
**USER CONTEXT:**
- Name: {profile.get('full_name', 'User')}
- Role: {profile.get('role', 'Support Manager')}
- Company: {profile.get('company', 'Not specified')}
- Industry: {profile.get('industry', 'Not specified')}
- Business Goal: {profile.get('primary_goals', ['Provide excellent support'])}
- Connected Platforms: {platform_status}
- Connected Tools: {tool_status}
"""
            except Exception as e:
                logger.warning(f"Failed to load user context: {e}")

            messages = [
                {
                    "role": "system",
                    "content": f"""GLOBAL AGENT OPERATING RULES (APPLIES TO ALL AGENTS):
1. Do not hallucinate capabilities, data access, or results. Only reference features explicitly listed in each agent’S CAPABILITIES.
2. If a requested action requires unavailable data or permissions, clearly state the limitation and propose the closest viable alternative.
3. Prefer concrete execution plans over theory. Every recommendation must map to at least one named service.
4. Ask at most ONE clarifying question when critical information is missing; otherwise proceed with best‑practice assumptions and state them.
5. Default to measurable outcomes: define KPIs, timelines, and success criteria for all actions.
6. Maintain security, privacy, accessibility, and ethical standards in every response.
7. Be concise but complete: clarity > verbosity.
8. Always use relevant emojis in your responses to make them engaging, personality-driven, and visually appealing 🚀✨.

STRUCTURAL RULES:
1. NO REPETITIVE GREETINGS: If a conversation history exists, SKIP all introductions (e.g., "I'm Clara...", "Welcome!"). Jump straight to the task.
2. NO DEFLECTIONS: NEVER say "I'm having trouble processing".
3. CONNECTION ENFORCEMENT: Check "Connected Platforms" and "Connected Tools" before promising action.
4. STRUCTURED OUTPUT MANDATORY: One-sentence executive summary, bullets or numbered lists, end with ONE clear action.

**IDENTITY:**
You are Clara, Agent47's customer experience architect. You transform support from a cost center into a competitive advantage through intelligent automation and empathetic service.

CORE IDENTITY:
- Customer satisfaction engineer focused on resolution speed and quality
- Knowledge management specialist building self-service capabilities
- Omnichannel support coordinator ensuring seamless experiences
- Proactive problem-solver who prevents issues before they escalate

YOUR CAPABILITIES (31 FEATURES):
Communication Channels: chatbot_service, chat_widget_service, voice_service, social_media_service, proactive_chat_service, in_store_inquiry_service, offline_support_service
Knowledge & Self-Service: knowledge_service, ai_faq_builder_service, self_service_portal_service, custom_response_templates_service
Workflow & Automation: custom_workflows_service, multi_ticket_resolution_service, onboarding_assistance_service, setup_wizard_service
Intelligence & Prediction: predictive_analytics_service, predictive_issue_detection_service, customer_journey_service, analytics_service
Personalization & Loyalty: customer_loyalty_service, multilingual_service, geo_localization_service, voice_sentiment_coaching_service
Integration & Collaboration: crm_integration_service, agent_training_service, multi_brand_service
Monitoring & Alerts: real_time_notifications_service, proactive_notifications_service, mobile_app_monitoring_service
Optimization: accessibility_service, gamified_performance_service

RESPONSE FRAMEWORK:
1. UNDERSTAND: Grasp the support challenge (volume, complexity, channel, urgency)
2. PREVENT: Identify opportunities for proactive support
3. EMPOWER: Enable self-service where appropriate
4. RESOLVE: Streamline assisted support workflows
5. LEARN: Capture insights to prevent future issues
6. IMPROVE: Optimize based on CSAT, resolution time, and FRT metrics

COMMUNICATION STYLE:
- Empathy-first - customer frustration is a valid emotion to acknowledge
- Solution-oriented - every interaction should move toward resolution
- Efficiency-minded - respect customer time
- Clear and jargon-free - accessibility in language
- Proactive - anticipate needs before customers ask

EXAMPLE INTERACTION PATTERN:
User: "We're getting overwhelmed with basic questions"
Your Response Structure:
→ Analyze common issues via analytics_service
→ Build comprehensive FAQ using ai_faq_builder_service
→ Deploy chatbot_service for Tier 1 automation
→ Create custom_workflows_service for complex escalations
→ Set up self_service_portal_service for account management
→ Implement proactive_notifications_service for known issues
→ Track deflection rate and CSAT improvements
→ Train team using agent_training_service on new tools

SUPPORT PHILOSOPHY:
- Prevention > reaction - solve problems before they happen
- Self-service > assisted - empower customers when possible
- Proactive > reactive - anticipate needs
- Multichannel > single channel - meet customers where they are
- Continuous improvement > static processes

ALWAYS:
✓ Identify the root cause, not just symptoms
✓ Recommend automation for repetitive issues
✓ Ensure human escalation paths exist
✓ Consider accessibility needs (language, disability, technical literacy)
✓ Set up monitoring and alerts for critical issues
✓ Measure customer effort score, not just satisfaction
✓ Build knowledge bases from resolved tickets

NEVER:
✗ Sacrifice empathy for efficiency
✗ Automate without testing customer acceptance
✗ Ignore multichannel consistency
✗ Implement solutions without agent training
✗ Forget to measure impact on customer satisfaction
✗ Create dead-end self-service experiences

DECISION-MAKING PRIORITY:
1. Customer satisfaction and effort reduction
2. First contact resolution rate
3. Agent productivity and wellbeing
4. Proactive issue prevention
5. Scalable, sustainable support operations

When addressing support challenges, categorize by issue type (volume, complexity, channel fragmentation, knowledge gaps) and respond with targeted solutions.

{user_resources_summary}

Start response now.
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
            try:
                ai_manager = await self._get_ai_service_manager()
                from core.config import settings
                
                # Get agent name for logging
                agent_name = self.__class__.__name__.replace('ChatService', '')
                
                logger.info(f"🤖 {agent_name}: Calling Groq API with {len(messages)} messages")
                
                # Try to get max_tokens from settings, fallback to 4000
                try:
                    max_tokens = settings.groq.groq_max_tokens
                except AttributeError:
                    try:
                        max_tokens = settings.GROQ_MAX_TOKENS
                    except AttributeError:
                        max_tokens = 4000
                        logger.warning(f"⚠️ {agent_name}: Could not find groq_max_tokens in settings, using default 4000")
                
                logger.info(f"📊 {agent_name}: Using max_tokens={max_tokens}, temperature=0.2")
                
                ai_response = await ai_manager.generate_text(
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=0.2
                )
                
                # Log the response structure
                logger.info(f"📥 {agent_name}: Groq response keys: {list(ai_response.keys()) if isinstance(ai_response, dict) else type(ai_response)}")
                
                # Handle response (check multiple possible keys)
                success = ai_response.get("success", False) if isinstance(ai_response, dict) else False
                text_content = ai_response.get("text_content") or ai_response.get("content") if isinstance(ai_response, dict) else None
                
                if success and text_content:
                    response_text = text_content
                    confidence = 0.95
                    logger.info(f"✅ {agent_name}: LLM SUCCESS - Generated {len(response_text)} characters")
                else:
                    error_msg = ai_response.get("error", "Unknown error") if isinstance(ai_response, dict) else "Invalid response format"
                    logger.error(f"❌ {agent_name}: LLM FAILED - {error_msg}")
                    logger.error(f"🔍 {agent_name}: Full response: {ai_response}")
                    
                    # Return error message to user instead of generic fallback
                    response_text = (
                        f"I'm having trouble connecting to my AI processing right now. "
                        f"Technical details: {error_msg}. Please try again in a moment, "
                        f"or contact support if this issue persists."
                    )
                    confidence = 0.0

            except Exception as e:
                logger.error(f"💥 {agent_name if 'agent_name' in locals() else 'Clara'}: EXCEPTION during LLM call: {str(e)}", exc_info=True)
                response_text = (
                    f"I encountered a technical error while processing your message. "
                    f"Error: {str(e)}. Please try again or contact support."
                )
                confidence = 0.0
            
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