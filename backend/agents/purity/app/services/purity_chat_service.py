from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload

from ..models import BusinessIdea, BusinessModel, CustomerAvatar, BusinessStage
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

# Import ALL Purity services
from .brand_building_service import BrandBuildingService
from .business_health_service import BusinessHealthService
from .business_idea_generator_service import BusinessIdeaGeneratorService
from .business_intelligence_service import BusinessIntelligenceService
from .business_mentor_service import BusinessMentorService
from .business_model_canvas_service import BusinessModelCanvasService
from .cold_email_generator_service import ColdEmailGeneratorService
from .competitor_analyzer_service import CompetitorAnalyzerService
from .copywriting_assistant_service import CopywritingAssistantService
from .crowdfunding_service import CrowdfundingService
from .customer_avatar_service import CustomerAvatarService
from .customer_retention_service import CustomerRetentionService
from .ecommerce_setup_service import EcommerceSetupService
from .exit_strategy_service import ExitStrategyService
from .exit_valuation_service import ExitValuationService
from .financial_planning_service import FinancialPlanningService
from .franchise_scanner_service import FranchiseScannerService
from .investment_pitch_service import InvestmentPitchService
from .launch_strategy_service import LaunchStrategyService
from .legal_compliance_service import LegalComplianceService
from .market_research_service import MarketResearchService
from .monetization_service import MonetizationService
from .mvp_builder_service import MVPBuilderService
from .niche_finder_service import NicheFinderService
from .opportunity_validation_service import OpportunityValidationService
from .partnership_matchmaker_service import PartnershipMatchmakerService
from .sales_funnel_service import SalesFunnelService
from .social_media_kit_service import SocialMediaKitService
from .sustainability_planner_service import SustainabilityPlannerService
from .task_automation_service import TaskAutomationService
from .tax_planning_service import TaxPlanningService
from core.services.media_service import MediaService



class PurityChatService:
    """Interactive chat service for Purity that provides comprehensive business development assistance"""
    
    def __init__(self):
        self.ai_service_manager: Optional[AIServiceManager] = None
        
        # Initialize ALL Purity services
        self.brand_building = BrandBuildingService()
        self.business_health = BusinessHealthService()
        self.business_idea_generator = BusinessIdeaGeneratorService()
        self.business_intelligence = BusinessIntelligenceService()
        self.business_mentor = BusinessMentorService()
        self.business_model_canvas = BusinessModelCanvasService()
        self.cold_email_generator = ColdEmailGeneratorService()
        self.competitor_analyzer = CompetitorAnalyzerService()
        self.copywriting_assistant = CopywritingAssistantService()
        self.crowdfunding = CrowdfundingService()
        self.customer_avatar = CustomerAvatarService()
        self.customer_retention = CustomerRetentionService()
        self.ecommerce_setup = EcommerceSetupService()
        self.exit_strategy = ExitStrategyService()
        self.exit_valuation = ExitValuationService()
        self.financial_planning = FinancialPlanningService()
        self.franchise_scanner = FranchiseScannerService()
        self.investment_pitch = InvestmentPitchService()
        self.launch_strategy = LaunchStrategyService()
        self.legal_compliance = LegalComplianceService()
        self.market_research = MarketResearchService()
        self.monetization = MonetizationService()
        self.mvp_builder = MVPBuilderService()
        self.niche_finder = NicheFinderService()
        self.opportunity_validation = OpportunityValidationService()
        self.partnership_matchmaker = PartnershipMatchmakerService()
        self.sales_funnel = SalesFunnelService()
        self.social_media_kit = SocialMediaKitService()
        self.sustainability_planner = SustainabilityPlannerService()
        self.task_automation = TaskAutomationService()
        self.tax_planning = TaxPlanningService()
        self.media = MediaService()  # Image generation service
        
        # Chat session management
        self.active_sessions = {}
        
        # TODO management
        self.todos = {}
        
        # Common user intents and responses for business development
        self.intent_responses = {
            "greeting": [
                "Hello! I'm Purity, your AI-powered business development assistant. I'm here to help you build, grow, and scale your business successfully.",
                "Hi there! I'm Purity, ready to help you develop your business idea, create strategies, and achieve your entrepreneurial goals.",
                "Welcome! I'm Purity, your dedicated business partner. Let's turn your vision into a thriving, profitable business!"
            ],
            "help": [
                "I can help you with: business planning, market research, financial planning, investment strategies, growth planning, and much more. What would you like to work on?",
                "I'm here to assist with: business ideation, market validation, financial modeling, strategic planning, and scaling operations. What do you need help with?",
                "I offer comprehensive business support including: business model development, funding strategies, market analysis, and growth optimization. How can I assist you today?"
            ],
            "business_planning": [
                "I'll help you create a comprehensive business plan that outlines your vision, strategy, and path to success.",
                "Let me guide you through developing a solid business plan with market analysis, financial projections, and operational strategies.",
                "I'll help you structure your business idea into a professional plan that investors and stakeholders will understand and support."
            ],
            "market_research": [
                "I'll help you conduct thorough market research to understand your industry, competitors, and target customers.",
                "Let me analyze market trends, customer needs, and competitive landscape to validate your business opportunity.",
                "I'll help you gather market intelligence that informs your business strategy and positioning decisions."
            ],
            "financial_planning": [
                "I'll help you create financial projections, budgets, and funding strategies for your business.",
                "Let me guide you through financial planning including revenue models, cost structures, and investment requirements.",
                "I'll help you develop a solid financial foundation that supports your business growth and sustainability."
            ],
            "investment_strategy": [
                "I'll help you prepare for investment opportunities and create compelling pitches for investors.",
                "Let me guide you through the funding process and help you identify the right investors for your business.",
                "I'll help you develop investment strategies and prepare materials that attract funding and support."
            ],
            "growth_planning": [
                "I'll help you plan and execute strategies for scaling your business and expanding into new markets.",
                "Let me guide you through growth planning including market expansion, team building, and operational scaling.",
                "I'll help you develop a roadmap for sustainable growth that maximizes your business potential."
            ],
            "business_model": [
                "I'll help you design and refine your business model to ensure profitability and sustainability.",
                "Let me guide you through business model development including value proposition, revenue streams, and cost structure.",
                "I'll help you create a business model that delivers value to customers while generating sustainable profits."
            ],
            "general": [
                "I'm here to help you build a successful business. What challenge are you facing?",
                "Let's work together to grow your business. What's your goal?",
                "I can help with any business development task. What do you need assistance with?"
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
        
        # Business development-specific intent detection
        if any(word in message_lower for word in ["plan", "planning", "strategy", "roadmap"]):
            return "business_planning"
        elif any(word in message_lower for word in ["market", "research", "analysis", "competitor"]):
            return "market_research"
        elif any(word in message_lower for word in ["financial", "budget", "money", "funding", "investment"]):
            return "financial_planning"
        elif any(word in message_lower for word in ["investor", "funding", "capital", "raise"]):
            return "investment_strategy"
        elif any(word in message_lower for word in ["growth", "scale", "expand", "grow"]):
            return "growth_planning"
        elif any(word in message_lower for word in ["model", "business model", "revenue", "profit"]):
            return "business_model"
        elif any(word in message_lower for word in ["image", "photo", "visual", "picture", "generate image", "create image"]):
            return "media_generation"
        elif any(word in message_lower for word in ["hello", "hi", "hey", "greetings"]):
            return "greeting"
        elif any(word in message_lower for word in ["help", "assist", "support", "what can you do"]):
            return "help"
        else:
            return "general"
    
    async def _break_down_request_into_tasks(self, message: str, user_id: int = None, db: AsyncSession = None) -> Dict[str, Any]:
        """Break down user request into structured tasks for business development
        
        Domain-specific for Purity (Business Development):
        - Business Tools: Stripe, PayPal, Business planning, Funding strategies
        - Planning Types: Business plans, Financial models, Growth strategies, Investment pitches
        - Task types: Business plan sections, Financial projections, Growth phases, Funding rounds
        """
        import re
        
        tasks = {
            "total_tasks": 1,
            "task_type": "general",
            "requirements": [],
            "completion_criteria": [],
            "domain": "business_development",
            "business_tools": [],
            "planning_types": []
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
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Could not fetch user resources: {e}")
        
        # Dynamically load ALL available platforms and integrations
        all_platforms = get_all_platforms_static()
        all_integrations = get_all_integrations_static()
        
        # Get finance integrations specifically
        finance_integrations = get_integrations_by_type("finance")
        business_tools_static = {k: v["display_name"] for k, v in finance_integrations.items()}
        
        # Detect ALL platforms mentioned (for business operations)
        detected_platforms = detect_platforms_in_message(message, all_platforms)
        
        # Filter detected platforms to only include user's connected platforms (if any)
        if user_connected_platforms and detected_platforms:
            detected_platforms = [p for p in detected_platforms if any(cp.lower() in p.lower() or p.lower() in cp.lower() for cp in user_connected_platforms)]
        
        # Detect ALL integrations mentioned (finance, business, productivity, etc.)
        detected_integrations = detect_integrations_in_message(message, all_integrations)
        detected_tools = [integ["display_name"] for integ in detected_integrations]
        
        # Filter detected integrations to only include user's connected integrations (if any)
        if user_connected_integrations and detected_tools:
            detected_tools = [t for t in detected_tools if any(ci.lower() in t.lower() or t.lower() in ci.lower() for ci in user_connected_integrations)]
        
        # Add finance/business tools if mentioned
        for tool_key, tool_name in business_tools_static.items():
            if tool_key in message_lower or tool_name.lower() in message_lower:
                if tool_name not in detected_tools:
                    detected_tools.append(tool_name)
        
        # Business-specific tool keywords
        business_keywords = {
            "payment": "Payment Processing",
            "funding": "Funding Platforms"
        }
        for keyword, tool_name in business_keywords.items():
            if keyword in message_lower and tool_name not in detected_tools:
                detected_tools.append(tool_name)
        
        # Planning Types Detection
        planning_types = {
            "business plan": "Business Plan",
            "financial": "Financial Model",
            "growth": "Growth Strategy",
            "funding": "Funding Strategy",
            "pitch": "Investment Pitch"
        }
        
        # Detect planning types mentioned
        detected_planning = []
        for planning_key, planning_name in planning_types.items():
            if planning_key in message_lower:
                detected_planning.append(planning_name)
        
        # Detect business plan section requests
        if "business plan" in message_lower or "plan" in message_lower:
            section_matches = re.findall(r'(\d+)[\s-]?(?:section|chapter|part)', message_lower)
            if section_matches:
                tasks["total_tasks"] = int(section_matches[0])
                tasks["task_type"] = "business_plan"
                tasks["requirements"] = [
                    f"Section {i+1}: Complete business plan section with analysis, strategies, financial projections, and actionable steps" 
                    for i in range(tasks["total_tasks"])
                ]
                tasks["completion_criteria"] = [
                    f"All {tasks['total_tasks']} sections must be provided",
                    "Each section must include: analysis, strategies, financial projections, and actionable steps",
                    "Plan must be comprehensive and investor-ready"
                ]
        
        # Detect financial model requests
        elif "financial" in message_lower or "model" in message_lower or "projection" in message_lower:
            period_matches = re.findall(r'(\d+)[\s-]?(?:month|year|quarter|period)', message_lower)
            if period_matches:
                tasks["total_tasks"] = int(period_matches[0])
                tasks["task_type"] = "financial_model"
                tasks["business_tools"] = detected_tools if detected_tools else ["All financial tools"]
                tasks["platforms"] = detected_platforms if detected_platforms else []
                tasks["requirements"] = [
                    f"Period {i+1}: Complete financial projection with revenue, expenses, cash flow, platform integrations, and key metrics" 
                    for i in range(tasks["total_tasks"])
                ]
                tasks["completion_criteria"] = [
                    f"All {tasks['total_tasks']} periods must be projected",
                    "Each period must include: revenue, expenses, cash flow, platform integrations, and key financial metrics",
                    f"Financial tools: {', '.join(tasks['business_tools'])}",
                    f"Available platforms: {', '.join(tasks['platforms']) if tasks['platforms'] else 'All business platforms (Stripe, PayPal, Shopify, etc.)'}"
                ]
        
        # Detect growth strategy phase requests
        elif "growth" in message_lower or "strategy" in message_lower:
            phase_matches = re.findall(r'(\d+)[\s-]?(?:phase|stage|milestone)', message_lower)
            if phase_matches:
                tasks["total_tasks"] = int(phase_matches[0])
                tasks["task_type"] = "growth_strategy"
                tasks["requirements"] = [
                    f"Phase {i+1}: Complete growth phase with objectives, strategies, metrics, resources, and timeline" 
                    for i in range(tasks["total_tasks"])
                ]
                tasks["completion_criteria"] = [
                    f"All {tasks['total_tasks']} growth phases must be detailed",
                    "Each phase must include: objectives, strategies, success metrics, required resources, and timeline"
                ]
        
        # Detect funding round requests
        elif "funding" in message_lower or "round" in message_lower or "investment" in message_lower:
            round_matches = re.findall(r'(\d+)[\s-]?(?:round|stage|phase)', message_lower)
            if round_matches:
                tasks["total_tasks"] = int(round_matches[0])
                tasks["task_type"] = "funding_strategy"
                tasks["business_tools"] = detected_tools if detected_tools else ["All funding tools"]
                tasks["requirements"] = [
                    f"Round {i+1}: Complete funding round strategy with amount, valuation, use of funds, investor profile, and pitch materials" 
                    for i in range(tasks["total_tasks"])
                ]
                tasks["completion_criteria"] = [
                    f"All {tasks['total_tasks']} funding rounds must be detailed",
                    "Each round must include: amount, valuation, use of funds, investor profile, and pitch materials",
                    f"Funding tools: {', '.join(tasks['business_tools'])}"
                ]
        
        return tasks
    
    def _get_fallback_response(self, intent: str) -> str:
        """Get fallback response for detected intent"""
        responses = {
            "greeting": [
                "Hello! I'm Purity, your AI business assistant. How can I help you build your business today?",
                "Hi there! I'm Purity, ready to help you grow your business. What's your goal?",
                "Welcome! I'm Purity, your business partner. Let's build something amazing!"
            ],
            "help": [
                "I can help you with business planning, market research, financial planning, and more. What do you need?",
                "I'm here to assist with all your business needs. What challenge are you facing?",
                "I offer comprehensive business support. How can I help you succeed today?"
            ],
            "business_planning": [
                "I'll help you create a business plan. What's your business idea?",
                "Let me guide you through business planning. What's your vision?",
                "I'll help you develop a strategy. What's your business goal?"
            ],
            "market_research": [
                "I'll help you research your market. What industry are you in?",
                "Let me analyze your market. What's your target audience?",
                "I'll help you understand your market. What's your business focus?"
            ],
            "financial_planning": [
                "I'll help you with financial planning. What's your budget?",
                "Let me guide you through finances. What are your funding needs?",
                "I'll help you plan your finances. What's your revenue goal?"
            ],
            "investment_strategy": [
                "I'll help you with investment strategy. What's your funding goal?",
                "Let me guide you through funding. What type of investment do you need?",
                "I'll help you attract investors. What's your business stage?"
            ],
            "growth_planning": [
                "I'll help you plan for growth. What's your current stage?",
                "Let me guide you through scaling. What's your growth goal?",
                "I'll help you expand your business. What's your target market?"
            ],
            "business_model": [
                "I'll help you design your business model. What's your value proposition?",
                "Let me guide you through business modeling. What's your revenue model?",
                "I'll help you refine your business model. What's your competitive advantage?"
            ],
            "general": [
                "I'm here to help with business development. What do you need assistance with?",
                "Let's work together on your business. What's your goal?",
                "I can help with any business task. What's on your mind?"
            ]
        }
        
        import random
        return random.choice(responses.get(intent, responses["general"]))
    
    def _generate_thinking_steps(self, intent: str, message: str, user_id: int, db: AsyncSession = None) -> List[str]:
        """Generate thinking steps based on intent and message context"""
        steps = []
        
        if intent == "business_planning":
            steps = [
                "Analyzing business requirements...",
                "Reviewing market opportunities...",
                "Designing business model...",
                "Preparing comprehensive business plan..."
            ]
        elif intent == "funding_strategy":
            steps = [
                "Reviewing funding requirements...",
                "Analyzing funding options...",
                "Preparing pitch materials...",
                "Designing funding strategy..."
            ]
        else:
            steps = [
                "Analyzing your request...",
                "Reviewing relevant information...",
                "Preparing response..."
            ]
        
        return steps
    
    async def process_chat_message(
        self,
        user_id: int,
        message: str,
        session_id: Optional[str] = None,
        db: AsyncSession = None
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
                
                # Get agent's custom configuration/tweaks
                custom_instructions_text = ""
                try:
                    if db and user_id:
                        agent_config = await get_agent_configuration_for_user(user_id, "purity", db)
                        if agent_config and agent_config.get("custom_instructions"):
                            custom_instructions_text = f"""

**CUSTOM INSTRUCTIONS / TWEAKS (STRICTLY FOLLOW THESE):**
{agent_config.get("custom_instructions")}

**CRITICAL:** You MUST strictly follow the custom instructions above. These are user-specific tweaks that override default behavior. Apply them to ALL your responses and actions.
"""
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Could not fetch agent configuration: {e}")
                
                # Prepare messages for AI processing
                messages = [
                    {
                        "role": "system",
                        "content": f"""You are Purity, an AI-powered business development assistant specializing in comprehensive business strategy and growth.
{custom_instructions_text}
                        You help users with business development tasks including:
                        - Business planning and strategy development
                        - Market research and competitive analysis
                        - Financial planning and funding strategies
                        - Investment preparation and pitch development
                        - Growth planning and scaling strategies
                        - Business model design and optimization
                        - Entrepreneurial guidance and mentorship
                        - Strategic decision making and planning
                        
                        Always provide strategic, data-driven, and actionable advice that helps users build successful, sustainable businesses.
                        Be professional, insightful, and focused on long-term business success and growth.
                        
                        **IMPORTANT:** Use emojis and icons naturally in your responses to make them more engaging and visually appealing. Use relevant emojis like 💼 for business, 📈 for growth, 💰 for funding, 🎯 for strategy, 📊 for planning, ✅ for milestones, 🚀 for launch, etc. Make your responses feel modern and polished.
{task_instructions}"""
                    },
                    {
                        "role": "user",
                        "content": f"User message: {message}\n\nContext: {session.get('context', {})}"
                    }
                ]
                
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
                        import logging
                        logger = logging.getLogger(__name__)
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
                        ai_response = f"I've generated an image for your business! 🎨\n\nYou can use this image in your business plans, presentations, or marketing materials."
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
