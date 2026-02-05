from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload

from ..models import JackieMarketingCampaign, JackieCampaignContent, JackieAdCampaign, CampaignStatus
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

# Import ALL Jackie services
from .ab_testing_service import ABTestingService
from .accessibility_service import AccessibilityService
from .ads_service import AdsService
from .agent_integration_service import AgentIntegrationService
from .analytics_service import AnalyticsService
from .brand_voice_service import BrandVoiceService
from .budget_control_service import BudgetControlService
from .campaign_service import CampaignService
from .campaign_calendar_service import CampaignCalendarService
from .campaign_collaboration_service import CampaignCollaborationService
from .campaign_ideation_service import CampaignIdeationService
from .campaign_storyboard_service import CampaignStoryboardService
from .campaign_version_control_service import CampaignVersionControlService
from .content_service import ContentService
from .crm_integration_service import CRMIntegrationService
from .cross_channel_analytics_service import CrossChannelAnalyticsService
from .customer_engagement_service import CustomerEngagementService
from .customer_feedback_service import CustomerFeedbackService
from .customer_search_service import CustomerSearchService
from .customer_segmentation_service import CustomerSegmentationService
from .deep_analytics_service import DeepAnalyticsService
from .dynamic_budget_service import DynamicBudgetService
from .dynamic_personalization_service import DynamicPersonalizationService
from .ecommerce_integration_service import EcommerceIntegrationService
from .email_marketing_service import EmailMarketingService
from .enhanced_video_voice_service import EnhancedVideoVoiceService
from .ethical_ad_scanner_service import EthicalAdScannerService
from .ethical_guidelines_service import EthicalGuidelinesService
from .geo_targeted_service import GeoTargetedService
from .human_chatbot_service import HumanChatbotService
from .influencer_marketing_service import InfluencerMarketingService
from .influencer_roi_predictor_service import InfluencerROIPredictorService
from .influencer_tracking_service import InfluencerTrackingService
from .interactive_elements_service import InteractiveElementsService
from .interactive_widgets_service import InteractiveWidgetsService
from .launch_assistant_service import LaunchAssistantService
from .localized_marketing_service import LocalizedMarketingService
from .market_research_service import MarketResearchService
from .mobile_campaign_service import MobileCampaignService
from .multi_language_service import MultiLanguageService
from .omnichannel_service import OmnichannelService
from .onboarding_service import OnboardingService
from .organic_marketing_service import OrganicMarketingService
from .performance_forecasting_service import PerformanceForecastingService
from .platform_optimization_service import PlatformOptimizationService
from .predictive_analytics_service import PredictiveAnalyticsService
from .seo_service import SEOService
from .social_media_service import SocialMediaService
from .voice_ad_generator_service import VoiceAdGeneratorService
from .voice_video_marketing_service import VoiceVideoMarketingService
from core.services.media_service import MediaService
import logging

logger = logging.getLogger(__name__)



class JackieChatService:
    """Interactive chat service for Jackie that provides comprehensive marketing campaign assistance"""
    
    def __init__(self):
        self.ai_service_manager: Optional[AIServiceManager] = None
        
        # Initialize ALL Jackie services with database session
        self._initialize_services()
        
        # Chat session management
        self.active_sessions = {}
        
        # TODO management
        self.todos = {}
        
        # Common user intents and responses for marketing campaigns
        self.intent_responses = {
            "greeting": [
                "Hello! 👋 I'm Jackie, your AI-powered marketing campaign assistant. I'm here to help you create, manage, and optimize marketing campaigns that drive results. 📈",
                "Hi there! ✨ I'm Jackie, ready to help you launch successful marketing campaigns and grow your brand awareness. 🎯",
                "Welcome! 🌟 I'm Jackie, your dedicated marketing partner. Let's create campaigns that captivate your audience and boost your business! 🚀"
            ],
            "help": [
                "I can help you with: campaign creation 📈, content strategy 🎨, ad optimization 🎯, audience targeting 👥, performance analytics 📊, and much more. What would you like to work on?",
                "I'm here to assist with: designing marketing campaigns 📋, creating compelling content ✍️, managing ad spend 💰, and analyzing campaign performance ✅. What do you need help with?",
                "I offer comprehensive marketing support including: campaign planning 📅, creative development 🎨, audience research 🔍, and ROI optimization 📈. How can I assist you today?"
            ],
            "campaign_creation": [
                "I'll help you create comprehensive marketing campaigns that align with your business goals and target audience. 📋",
                "Let me design a multi-channel campaign strategy that maximizes your reach and engagement across all platforms. 🔀",
                "I'll develop a complete campaign plan including messaging, creative direction, and execution timeline. 📅"
            ],
            "content_strategy": [
                "I'll help you develop a content strategy that resonates with your audience and supports your marketing goals. 🎨",
                "Let me create compelling content ideas and messaging that drives engagement and conversions. ✍️",
                "I'll help you plan content across all channels to maintain consistent brand voice and messaging. ✨"
            ],
            "ad_optimization": [
                "I'll help you optimize your advertising campaigns for better performance and higher ROI. 🎯",
                "Let me analyze your ad performance and suggest improvements to increase click-through rates and conversions. 📈",
                "I'll help you A/B test different ad variations and optimize your targeting for better results. ✅"
            ],
            "audience_targeting": [
                "I'll help you identify and target the right audience for your marketing campaigns. 👥",
                "Let me analyze your customer data and create detailed buyer personas for better targeting. 🔍",
                "I'll help you segment your audience and create personalized campaigns for each group. ✨"
            ],
            "performance_analytics": [
                "I'll help you track and analyze your campaign performance to identify what's working and what needs improvement. 📊",
                "Let me create comprehensive reports that show your campaign ROI and key performance metrics. 📉",
                "I'll help you set up tracking and measurement systems to monitor your marketing success. ✅"
            ],
            "budget_management": [
                "I'll help you allocate your marketing budget effectively across different channels and campaigns. 💰",
                "Let me create a budget plan that maximizes your ROI and ensures optimal spend distribution. 📉",
                "I'll help you track spending and adjust budgets based on performance data. ⚙️"
            ],
            "general": [
                "I'm here to help you succeed in marketing. What campaign challenge are you facing? 🤔",
                "Let's work together to create amazing marketing campaigns. What's your goal? ✨",
                "I can help with any marketing task. What do you need assistance with? 🚀"
            ]
        }
    
    async def _get_ai_service_manager(self) -> AIServiceManager:
        """Get AI service manager instance"""
        if not self.ai_service_manager:
            self.ai_service_manager = await get_ai_service_manager()
        return self.ai_service_manager
    
    def _initialize_services(self):
        """Initialize all Jackie services"""
        # Initialize all services as None for now (will be created when needed)
        self.ab_testing = None
        self.accessibility = None
        self.ads = None
        self.agent_integration = None
        self.analytics = None
        self.brand_voice = None
        self.budget_control = None
        self.campaign = None
        self.campaign_calendar = None
        self.campaign_collaboration = None
        self.campaign_ideation = None
        self.campaign_storyboard = None
        self.campaign_version_control = None
        self.content = None
        self.crm_integration = None
        self.cross_channel_analytics = None
        self.customer_engagement = None
        self.customer_feedback = None
        self.customer_search = None
        self.customer_segmentation = None
        self.deep_analytics = None
        self.dynamic_budget = None
        self.dynamic_personalization = None
        self.ecommerce_integration = None
        self.email_marketing = None
        self.enhanced_video_voice = None
        self.ethical_ad_scanner = None
        self.ethical_guidelines = None
        self.geo_targeted = None
        self.human_chatbot = None
        self.influencer_marketing = None
        self.influencer_roi_predictor = None
        self.influencer_tracking = None
        self.interactive_elements = None
        self.interactive_widgets = None
        self.launch_assistant = None
        self.localized_marketing = None
        self.market_research = None
        self.mobile_campaign = None
        self.multi_language = None
        self.omnichannel = None
        self.onboarding = None
        self.organic_marketing = None
        self.performance_forecasting = None
        self.platform_optimization = None
        self.predictive_analytics = None
        self.seo = None
        self.social_media = None
        self.voice_ad_generator = None
        self.voice_video_marketing = None
        self.media = MediaService()  # Image generation service
    
    def _detect_intent(self, message: str) -> str:
        """Detect user intent from message"""
        message_lower = message.lower()
        
        # Marketing campaign-specific intent detection
        if any(word in message_lower for word in ["campaign", "launch", "create", "design"]):
            return "campaign_creation"
        elif any(word in message_lower for word in ["content", "creative", "message", "copy"]):
            return "content_strategy"
        elif any(word in message_lower for word in ["ad", "advertising", "optimize", "performance"]):
            return "ad_optimization"
        elif any(word in message_lower for word in ["audience", "target", "segment", "persona"]):
            return "audience_targeting"
        elif any(word in message_lower for word in ["analytics", "metrics", "report", "roi"]):
            return "performance_analytics"
        elif any(word in message_lower for word in ["budget", "spend", "cost", "allocation"]):
            return "budget_management"
        elif any(word in message_lower for word in ["image", "photo", "visual", "picture", "generate image", "create image"]):
            return "media_generation"
        elif any(word in message_lower for word in ["hello", "hi", "hey", "greetings"]):
            return "greeting"
        elif any(word in message_lower for word in ["help", "assist", "support", "what can you do"]):
            return "help"
        else:
            return "general"
    
    async def _break_down_request_into_tasks(self, message: str, user_id: int = None, db: AsyncSession = None) -> Dict[str, Any]:
        """Break down user request into structured tasks for marketing campaigns
        
        Domain-specific for Jackie (Marketing):
        - Marketing Tools: Mailchimp, ConvertKit, Klaviyo, Marketing automation
        - JackieCampaign Types: Email campaigns, Ad campaigns, Social campaigns, Content campaigns
        - Task types: JackieCampaign phases, Marketing strategies, Ad variations, Audience segments
        """
        import re
        
        tasks = {
            "total_tasks": 1,
            "task_type": "general",
            "requirements": [],
            "completion_criteria": [],
            "domain": "marketing",
            "marketing_tools": [],
            "campaign_types": []
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
        
        # Get marketing integrations specifically
        marketing_integrations = get_integrations_by_type("marketing")
        marketing_tools_static = {k: v["display_name"] for k, v in marketing_integrations.items()}
        
        # Detect ALL platforms mentioned (for multi-channel campaigns)
        detected_platforms = detect_platforms_in_message(message, all_platforms)
        
        # Filter detected platforms to only include user's connected platforms (if any)
        if user_connected_platforms and detected_platforms:
            detected_platforms = [p for p in detected_platforms if any(cp.lower() in p.lower() or p.lower() in cp.lower() for cp in user_connected_platforms)]
        
        # Detect ALL integrations mentioned (marketing, automation, analytics, etc.)
        detected_integrations = detect_integrations_in_message(message, all_integrations)
        detected_tools = [integ["display_name"] for integ in detected_integrations]
        
        # Filter detected integrations to only include user's connected integrations (if any)
        if user_connected_integrations and detected_tools:
            detected_tools = [t for t in detected_tools if any(ci.lower() in t.lower() or t.lower() in ci.lower() for ci in user_connected_integrations)]
        
        # Add marketing tools if mentioned
        for tool_key, tool_name in marketing_tools_static.items():
            if tool_key in message_lower or tool_name.lower() in message_lower:
                if tool_name not in detected_tools:
                    detected_tools.append(tool_name)
        
        # Add marketing automation keyword
        if "automation" in message_lower and "Marketing Automation" not in detected_tools:
            detected_tools.append("Marketing Automation")
        
        # JackieCampaign Types Detection
        campaign_types = {
            "email": "Email JackieCampaign",
            "ad": "Ad JackieCampaign",
            "social": "Social JackieCampaign",
            "content": "Content JackieCampaign",
            "retargeting": "Retargeting JackieCampaign"
        }
        
        # Detect campaign types mentioned
        detected_campaigns = []
        for campaign_key, campaign_name in campaign_types.items():
            if campaign_key in message_lower:
                detected_campaigns.append(campaign_name)
        
        # Detect campaign phase requests
        if "campaign" in message_lower or "phase" in message_lower:
            phase_matches = re.findall(r'(\d+)[\s-]?(?:phase|stage|week|month)', message_lower)
            if phase_matches:
                tasks["total_tasks"] = int(phase_matches[0])
                tasks["task_type"] = "campaign_phases"
                tasks["marketing_tools"] = detected_tools if detected_tools else ["All marketing tools"]
                tasks["campaign_types"] = detected_campaigns if detected_campaigns else ["All campaign types"]
                tasks["platforms"] = detected_platforms if detected_platforms else []
                tasks["requirements"] = [
                    f"Phase {i+1}: Complete campaign phase with objectives, tactics, content, channels, platforms, budget, and KPIs" 
                    for i in range(tasks["total_tasks"])
                ]
                tasks["completion_criteria"] = [
                    f"All {tasks['total_tasks']} campaign phases must be detailed",
                    "Each phase must include: objectives, tactics, content, channels, platforms, budget allocation, and KPIs",
                    f"Marketing tools: {', '.join(tasks['marketing_tools'])}",
                    f"Available platforms: {', '.join(tasks['platforms']) if tasks['platforms'] else 'All platforms (social media, email, advertising platforms, etc.)'}"
                ]
        
        # Detect marketing strategy requests
        elif "strategy" in message_lower:
            strategy_matches = re.findall(r'(\d+)[\s-]?(?:strategy|tactic|approach)', message_lower)
            if strategy_matches:
                tasks["total_tasks"] = int(strategy_matches[0])
                tasks["task_type"] = "marketing_strategy"
                tasks["requirements"] = [
                    f"Strategy {i+1}: Complete marketing strategy with goals, target audience, channels, messaging, and success metrics" 
                    for i in range(tasks["total_tasks"])
                ]
                tasks["completion_criteria"] = [
                    f"All {tasks['total_tasks']} strategies must be provided",
                    "Each strategy must include: goals, target audience, channels, messaging, and success metrics"
                ]
        
        # Detect ad variation requests
        elif "ad" in message_lower and ("variation" in message_lower or "version" in message_lower):
            ad_matches = re.findall(r'(\d+)[\s-]?(?:ad|variation|version)', message_lower)
            if ad_matches:
                tasks["total_tasks"] = int(ad_matches[0])
                tasks["task_type"] = "ad_variations"
                tasks["requirements"] = [
                    f"Ad {i+1}: Complete ad variation with headline, copy, visuals, targeting, and performance optimization" 
                    for i in range(tasks["total_tasks"])
                ]
                tasks["completion_criteria"] = [
                    f"All {tasks['total_tasks']} ad variations must be provided",
                    "Each ad must include: headline, copy, visuals, targeting parameters, and performance optimization"
                ]
        
        # Detect audience segment requests
        elif "audience" in message_lower or "segment" in message_lower:
            segment_matches = re.findall(r'(\d+)[\s-]?(?:segment|audience|persona)', message_lower)
            if segment_matches:
                tasks["total_tasks"] = int(segment_matches[0])
                tasks["task_type"] = "audience_segments"
                tasks["requirements"] = [
                    f"Segment {i+1}: Complete audience segment with demographics, psychographics, behaviors, messaging, and channel preferences" 
                    for i in range(tasks["total_tasks"])
                ]
                tasks["completion_criteria"] = [
                    f"All {tasks['total_tasks']} segments must be provided",
                    "Each segment must include: demographics, psychographics, behaviors, messaging, and channel preferences"
                ]
        
        return tasks
    
    def _get_fallback_response(self, intent: str) -> str:
        """Get fallback response for detected intent"""
        responses = {
            "greeting": [
                "Hello! 👋 I'm Jackie, your AI marketing assistant. How can I help you create amazing campaigns today?",
                "Hi there! ✨ I'm Jackie, ready to help you boost your marketing. What's your campaign goal?",
                "Welcome! 🌟 I'm Jackie, your marketing partner. Let's create campaigns that convert! 🚀"
            ],
            "help": [
                "I can help you with campaign creation 📈, content strategy 🎨, ad optimization 🎯, and more. What do you need?",
                "I'm here to assist with all your marketing needs. What challenge are you facing? 🤔",
                "I offer comprehensive marketing support. How can I help you succeed today? ✨"
            ],
            "campaign_creation": [
                "I'll help you create a marketing campaign 📋. What's your business goal?",
                "Let me design a campaign for you 📊. What product or service are you promoting?",
                "I'll help you launch a successful campaign 🚀. What's your target audience?"
            ],
            "content_strategy": [
                "I'll help you develop content strategy 🎨. What type of content do you need?",
                "Let me create content ideas for you ✍️. What's your brand message?",
                "I'll help you plan content ✨. What platforms are you using?"
            ],
            "ad_optimization": [
                "I'll help you optimize your ads 🎯. What platform are you advertising on?",
                "Let me improve your ad performance 📈. What's your current CTR?",
                "I'll help you boost ad results ✅. What's your campaign objective?"
            ],
            "audience_targeting": [
                "I'll help you target the right audience 👥. What's your ideal customer?",
                "Let me create buyer personas for you 🔍. What industry are you in?",
                "I'll help you segment your audience ✨. What data do you have?"
            ],
            "performance_analytics": [
                "I'll help you analyze campaign performance 📊. What metrics are you tracking?",
                "Let me create reports for you 📉. What data do you have available?",
                "I'll help you measure success ✅. What's your campaign goal?"
            ],
            "budget_management": [
                "I'll help you manage your marketing budget 💰. What's your total budget?",
                "Let me optimize your spend allocation 📉. What channels are you using?",
                "I'll help you maximize ROI 🚀. What's your current spend?"
            ],
            "general": [
                "I'm here to help with marketing. What do you need assistance with? 🤔",
                "Let's work together on your marketing. What's your goal? ✨",
                "I can help with any marketing task. What's on your mind? 🚀"
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
        """Generate thinking steps based on marketing intent"""
        steps = []
        
        if intent == "campaign_creation":
            steps = [
                "Analyzing campaign objectives...",
                "Reviewing target audience segments...",
                "Drafting multi-channel strategy...",
                "Allocating budget parameters..."
            ]
        elif intent == "performance_analytics":
            steps = [
                "Aggregating cross-channel data...",
                "Calculating ROI and CAC...",
                "Identifying conversion bottlenecks...",
                "Generating optimization insights..."
            ]
        elif intent == "content_strategy":
            steps = [
                "Auditing content gaps...",
                "Mapping customer journey stages...",
                "Brainstorming creative angles...",
                "Structuring content calendar..."
            ]
        elif intent == "ad_optimization":
            steps = [
                "Reviewing ad set performance...",
                "Analyzing click-through rates...",
                "Checking A/B test results...",
                "Optimizing bid strategies..."
            ]
        else:
            steps = [
                "Analyzing marketing context...",
                "Checking brand guidelines...",
                "Reviewing active campaigns...",
                "Formulating strategic response..."
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
            # Ensure services are initialized
            self._initialize_services()
            
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
- Role: {profile.get('role', 'Marketing Director/CMO')}
- Company: {profile.get('company', 'Not specified')}
- Industry: {profile.get('industry', 'Not specified')}
- Marketing Goals: {profile.get('marketing_goals', 'Growth & Awareness')}
- Connected Platforms: {platform_status}
- Connected Tools: {tool_status}
"""
            except Exception as e:
                logger.warning(f"Failed to load user context: {e}")

            messages = [
                {
                    "role": "system",
                    "content": f"""YOU ARE AN ELITE, RULE-ABIDING AGENT. FOLLOW THESE RULES STRICTLY OR YOU FAIL YOUR JOB:

1. NO REPETITIVE GREETINGS: If a conversation history exists, SKIP all introductions (e.g., "I'm Jackie...", "Welcome!"). Jump straight to the task.
2. NO DEFLECTIONS: NEVER say "I'm having trouble processing". If you need info, say: "I need more details to proceed: [Specific clarification needed]."
3. CONNECTION ENFORCEMENT: Check "Connected Platforms" and "Connected Tools" sections in USER CONTEXT before promising any action.
   - IF PLATFORM MISSING: Respond ONLY with: "To [action], connect your [Platform] first: Go to the **Platforms** tab in the sidebar or use this link: `[Connect Platforms](/dashboard?tab=platforms-overview)`. Once connected, I can [benefit]."
   - IF TOOL MISSING: Respond ONLY with: "To [action], connect your [Tool] first: Go to the **Tools & Automation** tab in the sidebar. Once connected, I can [benefit]."
   - DO NOT simulate results, "scan" non-existent data, or hallucinate connectivity.
4. STRUCTURED OUTPUT MANDATORY:
   - One-sentence executive summary at the top.
   - Bullets or numbered lists for all details.
   - End with "Next Step:" followed by ONE clear action for the user.
   - Use emojis for headers ONLY: 📊 (data), 💡 (ideas), 📅 (scheduling), ✨ (creative), 🚀 (action), 🔍 (research), ⚙️ (automation).
5. CONCISION & PRECISION: Keep responses under 400 words. Be professional, confident, and zero-fluff.
6. MENTAL MODEL (Step-by-Step): Intent -> Connection Check -> Info Check -> Plan -> Format.

**IDENTITY:**
You are **Jackie**, the elite **Marketing Agent** for Agent47. Your personality is analytical, data-obsessed, and strategic.
Your primary goal is to build high-ROI multi-channel campaigns and maximize marketing performance.

{user_resources_summary}

**CAPABILITIES:**
- Campaign Management: planning and executing multi-channel campaigns.
- Ad Optimization: managing budgets and bid strategies.
- Content Strategy: mapping content to the customer journey.
- Analytics: deep dive into performance metrics.

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
            ai_manager = await self._get_ai_service_manager()
            from core.config import settings
            
            ai_response = await ai_manager.generate_text(
                messages=messages,
                max_tokens=settings.groq.groq_max_tokens,
                temperature=0.2
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
