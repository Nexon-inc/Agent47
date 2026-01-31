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

# Import essential Clara services (only the ones that exist and work)
from .support_service import SupportService
from .chatbot_service import ChatbotService
from .knowledge_service import KnowledgeService
from .analytics_service import AnalyticsService
from core.services.media_service import MediaService
import logging

logger = logging.getLogger(__name__)



class ClaraChatService:
    """Interactive chat service for Clara that provides comprehensive customer support assistance"""
    
    def __init__(self):
        self.ai_service_manager: Optional[AIServiceManager] = None
        
        # Initialize essential Clara services
        self.support = SupportService()
        self.chatbot = ChatbotService()
        self.knowledge = KnowledgeService()
        self.analytics = AnalyticsService()
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
            "help": [
                "I can help you with: ticket management 🎫, customer inquiries 📞, knowledge base 📚, live chat 💬, support analytics 📊, and much more. What would you like to work on?",
                "I'm here to assist with: resolving customer issues ✅, managing support tickets 📋, improving response times ⏰, and enhancing customer experience 👥. What do you need help with?",
                "I offer comprehensive customer support including: ticket routing 🔀, automated responses 🤖, customer insights 💡, and support optimization 🚀. How can I assist you today?"
            ],
            "ticket_management": [
                "I'll help you manage support tickets efficiently, prioritize issues, and ensure timely resolution for your customers. 📋",
                "Let me organize your support queue, categorize tickets, and help you respond to customer inquiries faster. 🗂️",
                "I'll streamline your ticket workflow and help you track resolution progress for better customer satisfaction. ✅"
            ],
            "customer_inquiry": [
                "I'll help you handle customer inquiries professionally and provide accurate, helpful responses to common questions. 📞",
                "Let me assist you in responding to customer questions with empathy and expertise to resolve their concerns. 🤝",
                "I'll help you craft responses that address customer needs and maintain positive relationships. ✨"
            ],
            "knowledge_base": [
                "I'll help you build and maintain a comprehensive knowledge base with answers to frequently asked questions. 📚",
                "Let me organize your support documentation and create helpful resources for both customers and support agents. 🔍",
                "I'll help you create searchable knowledge articles that reduce support ticket volume and improve self-service. 📖"
            ],
            "live_chat": [
                "I'll help you manage live chat interactions, provide real-time support, and ensure quick response times. 💬",
                "Let me assist you in handling live chat conversations and routing complex issues to the right team members. 🔀",
                "I'll help you provide instant support through live chat and improve customer engagement. ✨"
            ],
            "support_analytics": [
                "I'll analyze your support metrics, identify trends, and help you improve your customer service performance. 📊",
                "Let me track response times, resolution rates, and customer satisfaction to optimize your support operations. 📈",
                "I'll provide insights into support performance and help you make data-driven improvements. 💡"
            ],
            "escalation": [
                "I'll help you identify when to escalate issues to senior support staff or specialized teams. ⚠️",
                "Let me assist you in determining escalation criteria and routing complex problems to the right experts. 🔀",
                "I'll help you manage escalations effectively to ensure critical issues get proper attention. 🚨"
            ],
            "general": [
                "I'm here to help you provide excellent customer support. What challenge are you facing? 🤔",
                "Let's work together to improve your customer service. What do you need assistance with? ✨",
                "I can help with any customer support task. What's your goal today? 🚀"
            ]
        }
    
    async def _get_ai_service_manager(self) -> AIServiceManager:
        """Get AI service manager instance"""
        if not self.ai_service_manager:
            self.ai_service_manager = await get_ai_service_manager()
        return self.ai_service_manager
    
    def _detect_intent(self, message: str) -> str:
        """Detect user intent from message"""
        message_lower = message.lower()
        
        # Customer support-specific intent detection
        if any(word in message_lower for word in ["ticket", "issue", "problem", "complaint"]):
            return "ticket_management"
        elif any(word in message_lower for word in ["customer", "inquiry", "question", "help"]):
            return "customer_inquiry"
        elif any(word in message_lower for word in ["knowledge", "faq", "documentation", "article"]):
            return "knowledge_base"
        elif any(word in message_lower for word in ["chat", "live", "real-time", "instant"]):
            return "live_chat"
        elif any(word in message_lower for word in ["analytics", "metrics", "report", "performance"]):
            return "support_analytics"
        elif any(word in message_lower for word in ["escalate", "escalation", "senior", "manager"]):
            return "escalation"
        elif any(word in message_lower for word in ["image", "photo", "visual", "picture", "generate image", "create image"]):
            return "media_generation"
        elif any(word in message_lower for word in ["hello", "hi", "hey", "greetings"]):
            return "greeting"
        elif any(word in message_lower for word in ["help", "assist", "support", "what can you do"]):
            return "help"
        else:
            return "general"
    
    async def _break_down_request_into_tasks(self, message: str, user_id: int = None, db: AsyncSession = None) -> Dict[str, Any]:
        """Break down user request into structured tasks for customer support
        
        Domain-specific for Clara (Customer Support):
        - Support Channels: Email, Chat, Voice, SMS, Slack, Discord, Telegram, WhatsApp
        - Tools: Knowledge base, ClaraFAQ, Ticket management, Live chat
        - Task types: Support tickets, ClaraFAQ items, Response templates, Escalation workflows
        """
        import re
        
        tasks = {
            "total_tasks": 1,
            "task_type": "general",
            "requirements": [],
            "completion_criteria": [],
            "domain": "customer_support",
            "channels": [],
            "support_tools": []
        }
        
        message_lower = message.lower()
        
        # Get user's actual connected platforms and integrations (if db available)
        user_connected_platforms = []
        user_connected_integrations = []
        user_website = ""
        
        # Try to get user's actual connected resources
        try:
            if db and user_id:
                user_resources = await get_all_user_resources_for_agent(user_id, db)
                user_connected_platforms = [p.get("platform_name") for p in user_resources.get("platforms", []) if p.get("status") in ["connected", "active"]]
                user_connected_integrations = [i.get("integration_name") for i in user_resources.get("integrations", []) if i.get("status") == "connected"]
                user_website = user_resources.get("profile", {}).get("website_url", "")
        except Exception as e:
            logger.warning(f"Could not fetch user resources: {e}")
        
        # Dynamically load ALL available platforms and integrations
        all_platforms = get_all_platforms_static()
        all_integrations = get_all_integrations_static()
        
        # Support Channels Detection (communication platforms)
        communication_integrations = get_integrations_by_type("communication")
        support_channels = {
            "email": "Email",
            "chat": "Live Chat",
            "voice": "Voice",
            "sms": "SMS",
            "slack": "Slack",
            "discord": "Discord",
            "telegram": "Telegram",
            "whatsapp": "WhatsApp"
        }
        # Add communication integrations
        for comm_key, comm_info in communication_integrations.items():
            support_channels[comm_key] = comm_info["display_name"]
        
        # Detect ALL platforms mentioned (for multi-channel support)
        detected_platforms = detect_platforms_in_message(message, all_platforms)
        
        # Filter detected platforms to only include user's connected platforms (if any)
        if user_connected_platforms and detected_platforms:
            detected_platforms = [p for p in detected_platforms if any(cp.lower() in p.lower() or p.lower() in cp.lower() for cp in user_connected_platforms)]
        
        # Detect channels mentioned
        detected_channels = []
        for channel_key, channel_name in support_channels.items():
            if channel_key in message_lower or channel_name.lower() in message_lower:
                detected_channels.append(channel_name)
        
        # Detect ALL integrations mentioned (productivity, communication, etc.)
        detected_integrations = detect_integrations_in_message(message, all_integrations)
        detected_integration_names = [integ["display_name"] for integ in detected_integrations]
        
        # Filter detected integrations to only include user's connected integrations (if any)
        if user_connected_integrations and detected_integration_names:
            detected_integration_names = [t for t in detected_integration_names if any(ci.lower() in t.lower() or t.lower() in ci.lower() for ci in user_connected_integrations)]
        
        # Support Tools Detection
        support_tools = {
            "ticket": "Ticket Management",
            "faq": "ClaraFAQ",
            "knowledge": "Knowledge Base",
            "template": "Response Templates",
            "escalation": "Escalation Workflows"
        }
        
        # Detect support tools mentioned
        detected_tools = []
        for tool_key, tool_name in support_tools.items():
            if tool_key in message_lower:
                detected_tools.append(tool_name)
        
        # Add detected integrations to tools
        detected_tools.extend(detected_integration_names)
        
        # Detect ticket management requests
        if "ticket" in message_lower or "issue" in message_lower:
            ticket_matches = re.findall(r'(\d+)[\s-]?(?:ticket|issue|case)', message_lower)
            if ticket_matches:
                tasks["total_tasks"] = int(ticket_matches[0])
                tasks["task_type"] = "ticket_management"
                tasks["channels"] = detected_channels if detected_channels else ["All channels"]
                tasks["requirements"] = [
                    f"Ticket {i+1}: Complete ticket handling workflow with categorization, priority, response template, and resolution steps" 
                    for i in range(tasks["total_tasks"])
                ]
                tasks["completion_criteria"] = [
                    f"All {tasks['total_tasks']} tickets must be handled",
                    "Each ticket must include: categorization, priority, response template, and resolution steps",
                    f"Support channels: {', '.join(tasks['channels'])}"
                ]
        
        # Detect ClaraFAQ creation requests
        elif "faq" in message_lower or "question" in message_lower and "answer" in message_lower:
            faq_matches = re.findall(r'(\d+)[\s-]?(?:faq|question|q&a)', message_lower)
            if faq_matches:
                tasks["total_tasks"] = int(faq_matches[0])
                tasks["task_type"] = "faq_creation"
                tasks["support_tools"] = ["ClaraFAQ", "Knowledge Base"]
                tasks["requirements"] = [
                    f"ClaraFAQ {i+1}: Complete ClaraFAQ entry with question, answer, category, tags, and related articles" 
                    for i in range(tasks["total_tasks"])
                ]
                tasks["completion_criteria"] = [
                    f"All {tasks['total_tasks']} ClaraFAQ entries must be provided",
                    "Each ClaraFAQ must include: question, detailed answer, category, tags, and related articles",
                    "FAQs must be searchable and categorized"
                ]
        
        # Detect response template requests
        elif "template" in message_lower or "response" in message_lower:
            template_matches = re.findall(r'(\d+)[\s-]?(?:template|response|reply)', message_lower)
            if template_matches:
                tasks["total_tasks"] = int(template_matches[0])
                tasks["task_type"] = "response_templates"
                tasks["channels"] = detected_channels if detected_channels else ["All channels"]
                tasks["requirements"] = [
                    f"Template {i+1}: Complete response template with content, personalization points, channel optimization, and escalation triggers" 
                    for i in range(tasks["total_tasks"])
                ]
                tasks["completion_criteria"] = [
                    f"All {tasks['total_tasks']} templates must be provided",
                    "Each template must include: content, personalization points, channel optimization, and escalation triggers",
                    f"Templates must be optimized for: {', '.join(tasks['channels'])}"
                ]
        
        # Detect escalation workflow requests
        elif "escalation" in message_lower or "workflow" in message_lower:
            workflow_matches = re.findall(r'(\d+)[\s-]?(?:step|stage|level)', message_lower)
            if workflow_matches:
                tasks["total_tasks"] = int(workflow_matches[0])
                tasks["task_type"] = "escalation_workflow"
                tasks["requirements"] = [
                    f"Level {i+1}: Escalation level with criteria, actions, notifications, and handoff procedures" 
                    for i in range(tasks["total_tasks"])
                ]
                tasks["completion_criteria"] = [
                    f"All {tasks['total_tasks']} escalation levels must be detailed",
                    "Each level must include: criteria, actions, notifications, and handoff procedures",
                    "Workflow must include automation and integration points"
                ]
        
        # Detect support process steps
        elif "process" in message_lower or "workflow" in message_lower or "steps" in message_lower:
            step_matches = re.findall(r'(\d+)[\s-]?(?:step|stage|phase)', message_lower)
            if step_matches:
                tasks["total_tasks"] = int(step_matches[0])
                tasks["task_type"] = "support_process"
                tasks["channels"] = detected_channels if detected_channels else ["All channels"]
                tasks["support_tools"] = detected_tools if detected_tools else ["All support tools"]
                tasks["platforms"] = detected_platforms if detected_platforms else []
                tasks["requirements"] = [
                    f"Step {i+1}: Support process step with actions, tools, channel integration, platform options, and automation opportunities" 
                    for i in range(tasks["total_tasks"])
                ]
                tasks["completion_criteria"] = [
                    f"All {tasks['total_tasks']} process steps must be provided",
                    "Each step must include: actions, tools, channel integration, platform options, and automation opportunities",
                    f"Support channels: {', '.join(tasks['channels'])}",
                    f"Support tools: {', '.join(tasks['support_tools'])}",
                    f"Available platforms: {', '.join(tasks['platforms']) if tasks['platforms'] else 'All platforms (Slack, Discord, WhatsApp, Telegram, etc.)'}"
                ]
        
        return tasks
    
    def _generate_thinking_steps(self, intent: str, message: str, user_id: int, db: AsyncSession = None) -> List[str]:
        """Generate thinking steps based on intent and message context"""
        steps = []
        
        if intent == "ticket_management":
            steps = [
                "Reviewing customer support tickets...",
                "Analyzing ticket priority and status...",
                "Checking resolution history...",
                "Preparing response strategy..."
            ]
        elif intent == "customer_inquiry":
            steps = [
                "Analyzing customer inquiry...",
                "Searching knowledge base for solutions...",
                "Reviewing similar past cases...",
                "Formulating helpful response..."
            ]
        elif intent == "escalation":
            steps = [
                "Assessing issue complexity...",
                "Determining appropriate escalation level...",
                "Identifying available support resources...",
                "Preparing escalation details..."
            ]
        else:
            steps = [
                "Analyzing your request...",
                "Reviewing relevant information...",
                "Preparing response..."
            ]
        
        return steps
    
    def _get_fallback_response(self, intent: str) -> str:
        """Get fallback response for detected intent"""
        responses = {
            "greeting": [
                "Hello! 👋 I'm Clara, your AI customer support assistant. How can I help you serve your customers today?",
                "Hi there! ✨ I'm Clara, ready to help you provide excellent customer service. What's your goal?",
                "Welcome! 🌟 I'm Clara, your support partner. Let's deliver great customer experiences!"
            ],
            "help": [
                "I can help you with ticket management 🎫, customer inquiries 📞, knowledge base 📚, and more. What do you need?",
                "I'm here to assist with all your customer support needs. What challenge are you facing? 🤔",
                "I offer comprehensive support tools. How can I help you improve customer service today? 🚀"
            ],
            "ticket_management": [
                "I'll help you manage support tickets 📋. What type of issues are you dealing with?",
                "Let me assist with ticket organization 🗂️. How many tickets do you have pending?",
                "I'll help streamline your ticket workflow ✅. What's your current process?"
            ],
            "customer_inquiry": [
                "I'll help you handle customer inquiries 📞. What questions are customers asking?",
                "Let me assist with customer responses 🤝. What type of inquiry are you dealing with?",
                "I'll help you provide great customer service ✨. What's the customer's concern?"
            ],
            "knowledge_base": [
                "I'll help you build a knowledge base 📚. What topics do customers ask about most?",
                "Let me assist with documentation 🔍. What information do customers need?",
                "I'll help create helpful resources 📖. What questions should I help answer?"
            ],
            "live_chat": [
                "I'll help you manage live chat 💬. What chat platform are you using?",
                "Let me assist with real-time support ⏰. How many concurrent chats do you handle?",
                "I'll help improve chat responses ✨. What challenges are you facing?"
            ],
            "support_analytics": [
                "I'll help you analyze support metrics 📊. What data do you want to track?",
                "Let me assist with performance analysis 📈. What metrics are important to you?",
                "I'll help you measure success 💡. What KPIs do you want to improve?"
            ],
            "escalation": [
                "I'll help you manage escalations ⚠️. What criteria do you use for escalation?",
                "Let me assist with issue routing 🔀. What types of problems need escalation?",
                "I'll help you handle complex issues 🚨. What's your escalation process?"
            ],
            "general": [
                "I'm here to help with customer support. What do you need assistance with? 🤔",
                "Let's work together to improve customer service. What's your goal? ✨",
                "I can help with any support task. What's on your mind? 🚀"
            ]
        }
        
        import random
        return random.choice(responses.get(intent, responses["general"]))
    
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
            
            # Detect intent for thinking steps
            intent = self._detect_intent(message)
            
            # Generate thinking steps based on intent
            thinking_steps = self._generate_thinking_steps(intent, message, user_id, db)
            
            # Try to use AI service for better responses
            try:
                ai_manager = await self._get_ai_service_manager()
                
                # Break down request into tasks
                tasks = await self._break_down_request_into_tasks(message, user_id, db)
                
                # Build task-based instructions
                task_instructions = ""
                if tasks["total_tasks"] > 1:
                    task_instructions = f"""

**TASK BREAKDOWN AND COMPLETION REQUIREMENTS:**
The user's request requires completing {tasks["total_tasks"]} {tasks["task_type"]} tasks.

**Required Tasks:**
{chr(10).join(f"- {req}" for req in tasks["requirements"])}

**Completion Criteria:**
{chr(10).join(f"- {criteria}" for criteria in tasks["completion_criteria"])}

**CRITICAL INSTRUCTIONS FOR TASK COMPLETION:**
1. You MUST complete ALL {tasks["total_tasks"]} tasks before finishing your response
2. Work through each task systematically and completely
3. Do not skip any tasks - every single one must be addressed
4. Do not summarize or abbreviate - provide full, detailed content for each task
5. Track your progress explicitly: "Task 1 of {tasks["total_tasks"]}", "Task 2 of {tasks["total_tasks"]}", etc.
6. Only finish your response when you have completed all {tasks["total_tasks"]} tasks
7. If you're running out of space, prioritize completing all tasks over detailed explanations
8. Count down as you complete each task to ensure you don't miss any

Remember: Completing all {tasks["total_tasks"]} tasks is more important than providing extensive detail for fewer tasks.
"""
                
                # Get user's connected resources for context
                user_resources_summary = ""
                try:
                    if db and user_id:
                        if not user_resources:
                            from core.utils.agent_user_data import get_all_user_resources_for_agent
                            user_resources = await get_all_user_resources_for_agent(user_id, db)
                        
                        summary = user_resources.get("summary", {})
                        platforms_count = summary.get("total_platforms", 0)
                        integrations_count = summary.get("total_integrations", 0)
                        profile = user_resources.get('profile', {})
                        team_info = user_resources.get('team', {})
                        
                        user_resources_summary = f"""
**USER'S PROFILE & BUSINESS CONTEXT:**
- Name: {profile.get('full_name', 'Not provided')}
- Company: {profile.get('company', profile.get('business_name', 'Not provided'))}
- Industry: {profile.get('industry', 'Not specified')}
- Role: {profile.get('role', 'Not specified')}
- Team: {team_info.get('team_name', 'None')} ({team_info.get('total_members', 0)} members)

**SUPPORT CONTEXT:**
- Connected Tools: {integrations_count} ({', '.join([i.get('integration_name', '') for i in user_resources.get('integrations', [])[:5]])})

**PLATFORM NAVIGATION:**
- Support Settings: Dashboard -> Settings
- Team Members: Dashboard -> Members
"""
                except Exception as e:
                    logger.warning(f"Could not fetch user resources: {e}")

                # Get agent's custom configuration/tweaks
                custom_instructions_text = ""
                try:
                    if db and user_id:
                        from core.utils.agent_user_data import get_agent_configuration_for_user
                        agent_config = await get_agent_configuration_for_user(user_id, "clara", db)
                        if agent_config and agent_config.get("custom_instructions"):
                            custom_instructions_text = f"""

**CUSTOM INSTRUCTIONS / TWEAKS (STRICTLY FOLLOW THESE):**
{agent_config.get("custom_instructions")}

**CRITICAL:** You MUST strictly follow the custom instructions above. These are user-specific tweaks that override default behavior. Apply them to ALL your responses and actions.
"""
                except Exception as e:
                    logger.warning(f"Could not fetch agent configuration: {e}")
                
                # Prepare messages for AI processing
                messages = [
                    {
                        "role": "system",
                        "content": f"""You are Clara, an AI-powered customer support assistant specializing in comprehensive customer service management.
{user_resources_summary}
{custom_instructions_text}

**Response Guidelines:**
- Be a proactive, empathetic collaborator. Focus on resolving customer issues effectively.
- Use the chat history to maintain context.
- Use emojis naturally (🎫, 📞, ✅, 💬, etc.) to keep the tone friendly and professional.
- If the user asks how to do something, provide platform navigation guidance.
"""
                    }
                ]
                
                # Add history if available
                if history:
                    for h_msg in history[-5:]:
                        messages.append({
                            "role": h_msg.get("role", "user"),
                            "content": h_msg.get("content", ""),
                            "name": h_msg.get("name")
                        })
                
                # Add current user message
                messages.append({
                    "role": "user",
                    "content": message
                })
                
                # Check for image generation intent before AI response
                if intent == "media_generation":
                    # Get user tier from database
                    user_tier = None
                    try:
                        from sqlalchemy import select
                        from core.database.models import User
                        result = await db.execute(select(User).where(User.id == user_id))
                        user = result.scalar_one_or_none()
                        if user:
                            user_tier = user.tier
                    except Exception as e:
                        logger.warning(f"Failed to get user tier: {e}")
                    
                    # Extract image generation prompt or use context
                    prompt_keywords = ["image", "photo", "visual", "picture", "generate", "create", "for", "of", "show"]
                    prompt = message
                    for keyword in prompt_keywords:
                        prompt = prompt.replace(keyword, "", 1)
                    prompt = prompt.strip()
                    if not prompt:
                        prompt = message
                    
                    # Generate image with user tier for model selection
                    image_result = await self.media.generate_image(
                        prompt=prompt,
                        context=message,
                        user_id=user_id,
                        user_tier=user_tier,
                        auto_generate_prompt=True
                    )
                    
                    if image_result.get("success"):
                        image_url = image_result.get('url')
                        ai_response = f"I've generated an image for you! 🎨\n\nYou can use this image in your support materials, help articles, or tutorials."
                        # Include image_url in response metadata for frontend
                        return {
                            "success": True,
                            "response": ai_response,
                            "image_url": image_url,  # Add image URL for frontend display
                            "thinking_steps": thinking_steps,
                            "session_id": session_id,
                            "intent": "media_generation",
                            "message_count": session["message_count"],
                            "timestamp": datetime.now().isoformat()
                        }
                    else:
                        ai_response = f"I couldn't generate the image: {image_result.get('error', 'Unknown error')}"
                else:
                    # Generate AI response
                    response = await ai_manager.generate_text(
                        messages=messages,
                        max_tokens=500,
                        temperature=0.7
                    )                
                if response.success and response.text_content:
                    ai_response = response.text_content
                else:
                    # Fallback to intent-based response
                    intent = self._detect_intent(message)
                    ai_response = self._get_fallback_response(intent)
                    session["last_intent"] = intent
                
            except Exception as e:
                # Fallback to intent-based response
                intent = self._detect_intent(message)
                ai_response = self._get_fallback_response(intent)
                session["last_intent"] = intent
            
            # Update session context
            session["context"]["last_message"] = message
            session["context"]["last_response"] = ai_response
            session["context"]["timestamp"] = datetime.now().isoformat()
            
            return {
                "success": True,
                "response": ai_response,
                "thinking_steps": thinking_steps,
                "session_id": session_id,
                "intent": session.get("last_intent", "general"),
                "message_count": session["message_count"],
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
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