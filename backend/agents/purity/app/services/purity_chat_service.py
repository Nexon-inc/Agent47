from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload

from ..models import PurityBusinessIdea, PurityBusinessModel, PurityCustomerAvatar, BusinessStage
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
import logging

logger = logging.getLogger(__name__)



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
                "Hello! 👋 I'm Purity, your AI-powered business development assistant. I'm here to help you build, grow, and scale your business successfully. 💼",
                "Hi there! ✨ I'm Purity, ready to help you develop your business idea, create strategies, and achieve your entrepreneurial goals. 📈",
                "Welcome! 🌟 I'm Purity, your dedicated business partner. Let's turn your vision into a thriving, profitable business! 🚀"
            ],
            "help": [
                "I can help you with: business planning 📊, market research 🔍, financial planning 💰, investment strategies 🎯, growth planning 📈, and much more. What would you like to work on?",
                "I'm here to assist with: business ideation 💡, market validation ✅, financial modeling 📉, strategic planning 📋, and scaling operations 🚀. What do you need help with?",
                "I offer comprehensive business support including: business model development 🏗️, funding strategies 💵, market analysis 📋, and growth optimization 📈. How can I assist you today?"
            ],
            "business_planning": [
                "I'll help you create a comprehensive business plan that outlines your vision, strategy, and path to success. 📋",
                "Let me guide you through developing a solid business plan with market analysis, financial projections, and operational strategies. 📊",
                "I'll help you structure your business idea into a professional plan that investors and stakeholders will understand and support. ✨"
            ],
            "market_research": [
                "I'll help you conduct thorough market research to understand your industry, competitors, and target customers. 🔍",
                "Let me analyze market trends, customer needs, and competitive landscape to validate your business opportunity. 💡",
                "I'll help you gather market intelligence that informs your business strategy and positioning decisions. 📊"
            ],
            "financial_planning": [
                "I'll help you create financial projections, budgets, and funding strategies for your business. 💰",
                "Let me guide you through financial planning including revenue models, cost structures, and investment requirements. 📉",
                "I'll help you develop a solid financial foundation that supports your business growth and sustainability. ✅"
            ],
            "investment_strategy": [
                "I'll help you prepare for investment opportunities and create compelling pitches for investors. 🎯",
                "Let me guide you through the funding process and help you identify the right investors for your business. 💵",
                "I'll help you develop investment strategies and prepare materials that attract funding and support. ✨"
            ],
            "growth_planning": [
                "I'll help you plan and execute strategies for scaling your business and expanding into new markets. 📈",
                "Let me guide you through growth planning including market expansion, team building, and operational scaling. 🚀",
                "I'll help you develop a roadmap for sustainable growth that maximizes your business potential. ✅"
            ],
            "business_model": [
                "I'll help you design and refine your business model to ensure profitability and sustainability. 🏗️",
                "Let me guide you through business model development including value proposition, revenue streams, and cost structure. 💰",
                "I'll help you create a business model that delivers value to customers while generating sustainable profits. ✨"
            ],
            "general": [
                "I'm here to help you build a successful business. What challenge are you facing? 🤔",
                "Let's work together to grow your business. What's your goal? ✨",
                "I can help with any business development task. What do you need assistance with? 🚀"
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
            section_matches = re.findall(r'(\d+)[\\s-]?(?:section|chapter|part)', message_lower)
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
            period_matches = re.findall(r'(\d+)[\\s-]?(?:month|year|quarter|period)', message_lower)
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
            phase_matches = re.findall(r'(\d+)[\\s-]?(?:phase|stage|milestone)', message_lower)
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
            round_matches = re.findall(r'(\d+)[\\s-]?(?:round|stage|phase)', message_lower)
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
                "Hello! 👋 I'm Purity, your AI business assistant. How can I help you build your business today?",
                "Hi there! ✨ I'm Purity, ready to help you grow your business. What's your goal?",
                "Welcome! 🌟 I'm Purity, your business partner. Let's build something amazing! 🚀"
            ],
            "help": [
                "I can help you with business planning 📊, market research 🔍, financial planning 💰, and more. What do you need?",
                "I'm here to assist with all your business needs. What challenge are you facing? 🤔",
                "I offer comprehensive business support. How can I help you succeed today? ✨"
            ],
            "business_planning": [
                "I'll help you create a business plan 📋. What's your business idea?",
                "Let me guide you through business planning 📊. What's your vision?",
                "I'll help you develop a strategy ✨. What's your business goal?"
            ],
            "market_research": [
                "I'll help you research your market 🔍. What industry are you in?",
                "Let me analyze your market 💡. What's your target audience?",
                "I'll help you understand your market 📊. What's your business focus?"
            ],
            "financial_planning": [
                "I'll help you with financial planning 💰. What's your budget?",
                "Let me guide you through finances 📉. What are your funding needs?",
                "I'll help you plan your finances ✅. What's your revenue goal?"
            ],
            "investment_strategy": [
                "I'll help you with investment strategy 🎯. What's your funding goal?",
                "Let me guide you through funding 💵. What type of investment do you need?",
                "I'll help you attract investors ✨. What's your business stage?"
            ],
            "growth_planning": [
                "I'll help you plan for growth 📈. What's your current stage?",
                "Let me guide you through scaling 🚀. What's your growth goal?",
                "I'll help you expand your business ✅. What's your target market?"
            ],
            "business_model": [
                "I'll help you design your business model 🏗️. What's your value proposition?",
                "Let me guide you through business modeling 💰. What's your revenue model?",
                "I'll help you refine your business model ✨. What's your competitive advantage?"
            ],
            "general": [
                "I'm here to help with business development. What do you need assistance with? 🤔",
                "Let's work together to grow your business. What's your goal? ✨",
                "I can help with any business task. What's on your mind? 🚀"
            ]
        }
        
        import random
        return random.choice(responses.get(intent, responses["general"]))
    
    async def _handle_intent(
        self,
        user_id: int,
        message: str,
        intent_analysis: Dict[str, Any],
        session: Dict[str, Any],
        db: AsyncSession
    ) -> str:
        """Handle different user intents and provide appropriate responses"""
        intent = intent_analysis.get("intent", "general")
        return self._get_fallback_response(intent)

    def _generate_thinking_steps(self, intent: str, message: str, user_id: int, db: AsyncSession = None) -> List[str]:
        """Generate thinking steps based on business development intent"""
        steps = []
        
        if intent == "business_planning":
            steps = [
                "Analyzing business model viability...",
                "Scanning market competition...",
                "Drafting operational roadmap...",
                "Projecting financial milestones..."
            ]
        elif intent == "financial_planning":
            steps = [
                "Calculating burn rate & runway...",
                "Forecasting revenue scenarios...",
                "Optimizing cost structure...",
                "Structuring investment deck..."
            ]
        elif intent == "legal_compliance":
            steps = [
                "Scanning regulatory frameworks...",
                "Identifying compliance risks...",
                "Drafting legal safeguards...",
                "Validating operational boundaries..."
            ]
        elif intent == "growth_planning":
            steps = [
                "Identifying extensive growth levers...",
                "Analyzing scaling bottlenecks...",
                "Mapping market entry strategy...",
                "Designing retention loops..."
            ]
        else:
            steps = [
                "Analyzing business context...",
                "Checking strategic alignment...",
                "Reviewing resources...",
                "Formulating advice..."
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
             # Ensure services are initialized (lazy load logic if implemented, or call specific init)
            # In previous files we relied on __init__ but let's be safe
            if not hasattr(self, 'brand_building') or not self.brand_building:
                 # Re-init if needed or assume initialized in __init__
                 pass 

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
                    
                    user_resources_summary = f"""
**USER CONTEXT:**
- Name: {profile.get('full_name', 'User')}
- Business Stage: {profile.get('business_stage', 'Early Stage')}
- Industry: {profile.get('industry', 'Not specified')}
- Revenue Model: {profile.get('revenue_model', 'Not specified')}
- Key Goals: {profile.get('primary_goals', ['Growth', 'Funding'])}
- Connected Platforms: {summary.get('total_platforms', 0)}
- Connected Tools: {summary.get('total_integrations', 0)} (Finance, Legal, etc.)
"""
            except Exception as e:
                logger.warning(f"Failed to load user context: {e}")

            messages = [
                {
                    "role": "system",
                    "content": f"""You are **Purity**, an elite **AI Business Architect & Strategy Consultant**.
{user_resources_summary}

**CORE OBJECTIVE:**
Help the user **Build**, **Scale**, and **Secure** their business. You think like a **Startup Founder** combined with a **CFO** and **Legal Counsel**.

**INTELLIGENCE PROTOCOL (STRICTLY FOLLOW THIS):**
1. **Viability First**: Always assess if an idea is profitable and scalable.
2. **Risk Aware**: Proactively highlight legal, financial, or operational risks.
3. **Structured Thinking**: Break down complex problems into "Phases" or "Modules".
4. **Tool Usage**: You have access to Business Planning, Financial Modeling, and Legal Compliance services. Use them.

**CAPABILITIES:**
- **Business Strategy**: Lean canvas, business plans, pivot analysis.
- **Finance**: Runway calculation, unit economics, fundraising logic.
- **Legal/Compliance**: Risk assessment, entity structure, IP protection advice.
- **Growth**: Go-to-market strategy, partnership ecosystem.

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
            
            # Add images if generated
            if simple_intent == "media_generation" and "image_url" in locals():
                 result["image_url"] = locals().get("image_url")  
                 
             # Add service info
            if simple_intent and simple_intent != "general":
                 result["service_used"] = True

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