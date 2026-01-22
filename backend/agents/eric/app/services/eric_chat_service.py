from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload
import logging

from ..models import EricLead, EricDeal, EricLeadInteraction, CommunicationChannel
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

# Import ALL Eric services with correct class names
from .advanced_conversational_ai_service import AdvancedConversationalAIService
from .ai_lead_prioritization_service import AILeadPrioritizationService
from .ai_sales_training_service import AISalesTrainingService
from .auto_pitch_generator_service import AutoPitchGeneratorService
from .automated_proposal_builder_service import AutomatedProposalBuilderService
from .competitor_benchmarking_service import CompetitorBenchmarkingService
from .conversational_ai_service import ConversationalAIService
from .crm_automation_service import CRMAutomationService
from .cross_channel_lead_tracking_service import CrossChannelLeadTrackingService
from .cross_selling_service import CrossSellingService
from .customer_insights_service import CustomerInsightsService
from .customer_journey_service import CustomerJourneyService
from .deal_closing_service import DealClosingService
from .deal_closing_assistance_service import DealClosingAssistanceService
from .dynamic_follow_up_scheduler_service import DynamicFollowUpSchedulerService
from .dynamic_pricing_service import DynamicPricingService
from .email_sequences_service import EmailSequencesService
from .emerging_channels_service import EmergingChannelsService
from .ethical_sales_scoring_service import EthicalSalesScoringService
from .gamified_incentives_service import GamifiedIncentivesService
from .lead_generation_service import LeadGenerationService
from .lead_scoring_service import LeadScoringService
from .live_chat_service import LiveChatService
from .local_market_insights_service import LocalMarketInsightsService
from .market_trend_alerts_service import MarketTrendAlertsService
from .mobile_app_monitoring_service import MobileAppMonitoringService
from .multi_language_service import MultiLanguageService
from .objection_handling_service import ObjectionHandlingService
from .objection_prediction_service import ObjectionPredictionService
from .onboarding_wizard_service import OnboardingWizardService
from .performance_analytics_service import PerformanceAnalyticsService
from .personalized_recommendations_service import PersonalizedRecommendationsService
from .predictive_analytics_service import PredictiveAnalyticsService
from .sales_forecasting_service import SalesForecastingService
from .sales_funnel_service import SalesFunnelService
from .sales_outreach_service import SalesOutreachService
from .social_proof_generator_service import SocialProofGeneratorService
from .social_selling_service import SocialSellingService
from .sustainability_ethical_selling_service import SustainabilityEthicalSellingService
from .team_sales_dashboard_service import TeamSalesDashboardService
from .tone_branding_service import ToneBrandingService
from .voice_pitch_simulator_service import VoicePitchSimulatorService
from core.services.media_service import MediaService



class EricChatService:
    """Interactive chat service for Eric that provides comprehensive sales assistance"""
    
    def __init__(self):
        self.ai_service_manager: Optional[AIServiceManager] = None
        
        # Initialize ALL Eric services
        self.advanced_conversational_ai = AdvancedConversationalAIService()
        self.ai_lead_prioritization = AILeadPrioritizationService()
        self.ai_sales_training = AISalesTrainingService()
        self.auto_pitch_generator = AutoPitchGeneratorService()
        self.automated_proposal_builder = AutomatedProposalBuilderService()
        self.competitor_benchmarking = CompetitorBenchmarkingService()
        self.conversational_ai = ConversationalAIService()
        self.crm_automation = CRMAutomationService()
        self.cross_channel_lead_tracking = CrossChannelLeadTrackingService()
        self.cross_selling = CrossSellingService()
        self.customer_insights = CustomerInsightsService()
        self.customer_journey = CustomerJourneyService()
        self.deal_closing = DealClosingService()
        self.deal_closing_assistance = DealClosingAssistanceService()
        self.dynamic_follow_up_scheduler = DynamicFollowUpSchedulerService()
        self.dynamic_pricing = DynamicPricingService()
        self.email_sequences = EmailSequencesService()
        self.emerging_channels = EmergingChannelsService()
        self.ethical_sales_scoring = EthicalSalesScoringService()
        self.gamified_incentives = GamifiedIncentivesService()
        self.lead_generation = LeadGenerationService()
        self.lead_scoring = LeadScoringService()
        self.live_chat = LiveChatService()
        self.local_market_insights = LocalMarketInsightsService()
        self.market_trend_alerts = MarketTrendAlertsService()
        self.mobile_app_monitoring = MobileAppMonitoringService()
        self.multi_language = MultiLanguageService()
        self.objection_handling = ObjectionHandlingService()
        self.objection_prediction = ObjectionPredictionService()
        self.onboarding_wizard = OnboardingWizardService()
        self.performance_analytics = PerformanceAnalyticsService()
        self.personalized_recommendations = PersonalizedRecommendationsService()
        self.predictive_analytics = PredictiveAnalyticsService()
        self.sales_forecasting = SalesForecastingService()
        self.sales_funnel = SalesFunnelService()
        self.sales_outreach = SalesOutreachService()
        self.social_proof_generator = SocialProofGeneratorService()
        self.social_selling = SocialSellingService()
        self.sustainability_ethical_selling = SustainabilityEthicalSellingService()
        self.team_sales_dashboard = TeamSalesDashboardService()
        self.tone_branding = ToneBrandingService()
        self.voice_pitch_simulator = VoicePitchSimulatorService()
        self.media = MediaService()  # Image generation service
        
        # Chat session management
        self.active_sessions = {}
        
        # TODO management
        self.todos = {}
        
        # Track initialization status
        self._services_initialized = False
        
        # Common user intents and responses for sales
        self.intent_responses = {
            "greeting": [
                "Hello! I'm Eric, your AI-powered sales assistant. I'm here to help you generate leads, close deals, and grow your sales revenue.",
                "Hi there! I'm Eric, ready to help you boost your sales performance and achieve your revenue goals.",
                "Welcome! I'm Eric, your dedicated sales partner. Let's turn prospects into customers and grow your business!"
            ],
            "help": [
                "I can help you with: lead generation, CRM automation, sales outreach, deal closing, forecasting, customer insights, and much more. What would you like to work on?",
                "I'm here to assist with: finding new prospects, nurturing leads, closing deals, analyzing sales performance, and optimizing your sales process. What do you need help with?",
                "I offer comprehensive sales support including: lead qualification, sales forecasting, customer segmentation, objection handling, and revenue optimization. How can I assist you today?"
            ],
            "lead_generation": [
                "I'll help you identify and generate high-quality leads for your business. Let me analyze your target market and create a lead generation strategy.",
                "Let me scan your CRM and market data to find new prospect opportunities and create targeted outreach campaigns.",
                "I'll examine your current lead sources and develop new strategies to attract qualified prospects to your sales funnel."
            ],
            "deal_closing": [
                "I'll analyze your open deals and provide strategies to move them through the sales pipeline and close more deals.",
                "Let me review your deal stages and identify bottlenecks or opportunities to accelerate the closing process.",
                "I'll help you overcome objections and create compelling proposals that convert prospects into customers."
            ],
            "sales_forecasting": [
                "I'll analyze your sales data and market trends to provide accurate revenue forecasts and help you plan for the future.",
                "Let me examine your pipeline and historical performance to predict your sales outcomes and identify growth opportunities.",
                "I'll create detailed sales projections based on your current deals, market conditions, and team performance."
            ],
            "crm_automation": [
                "I'll help you automate your CRM processes to save time and improve your sales efficiency.",
                "Let me set up automated workflows for lead nurturing, follow-ups, and deal progression in your CRM system.",
                "I'll optimize your CRM data management and create automated reports to track your sales performance."
            ],
            "objection_handling": [
                "I'll help you prepare responses to common sales objections and improve your closing techniques.",
                "Let me analyze your past objections and create a comprehensive objection handling playbook for your team.",
                "I'll provide you with proven strategies to overcome price, timing, and authority objections in your sales conversations."
            ],
            "general": [
                "I'm here to help you succeed in sales. What specific challenge are you facing today?",
                "Let's work together to improve your sales performance. What would you like to focus on?",
                "I can help you with any sales-related task. What do you need assistance with?"
            ]
        }
    
    async def initialize(self):
        """Initialize all Eric services"""
        if self._services_initialized:
            return
        
        try:
            logger = logging.getLogger(__name__)
            logger.info("Initializing all Eric services...")
            
            # Initialize AI service manager
            self.ai_service_manager = await get_ai_service_manager()
            
            # Initialize all services that have an initialize method
            services_to_init = [
                ("advanced_conversational_ai", self.advanced_conversational_ai),
                ("ai_lead_prioritization", self.ai_lead_prioritization),
                ("ai_sales_training", self.ai_sales_training),
                ("auto_pitch_generator", self.auto_pitch_generator),
                ("automated_proposal_builder", self.automated_proposal_builder),
                ("competitor_benchmarking", self.competitor_benchmarking),
                ("conversational_ai", self.conversational_ai),
                ("crm_automation", self.crm_automation),
                ("cross_channel_lead_tracking", self.cross_channel_lead_tracking),
                ("cross_selling", self.cross_selling),
                ("customer_insights", self.customer_insights),
                ("customer_journey", self.customer_journey),
                ("deal_closing", self.deal_closing),
                ("deal_closing_assistance", self.deal_closing_assistance),
                ("dynamic_follow_up_scheduler", self.dynamic_follow_up_scheduler),
                ("dynamic_pricing", self.dynamic_pricing),
                ("email_sequences", self.email_sequences),
                ("emerging_channels", self.emerging_channels),
                ("ethical_sales_scoring", self.ethical_sales_scoring),
                ("gamified_incentives", self.gamified_incentives),
                ("lead_generation", self.lead_generation),
                ("lead_scoring", self.lead_scoring),
                ("live_chat", self.live_chat),
                ("local_market_insights", self.local_market_insights),
                ("market_trend_alerts", self.market_trend_alerts),
                ("mobile_app_monitoring", self.mobile_app_monitoring),
                ("multi_language", self.multi_language),
                ("objection_handling", self.objection_handling),
                ("objection_prediction", self.objection_prediction),
                ("onboarding_wizard", self.onboarding_wizard),
                ("performance_analytics", self.performance_analytics),
                ("personalized_recommendations", self.personalized_recommendations),
                ("predictive_analytics", self.predictive_analytics),
                ("sales_forecasting", self.sales_forecasting),
                ("sales_funnel", self.sales_funnel),
                ("sales_outreach", self.sales_outreach),
                ("social_proof_generator", self.social_proof_generator),
                ("social_selling", self.social_selling),
                ("sustainability_ethical_selling", self.sustainability_ethical_selling),
                ("team_sales_dashboard", self.team_sales_dashboard),
                ("tone_branding", self.tone_branding),
                ("voice_pitch_simulator", self.voice_pitch_simulator),
            ]
            
            for service_name, service_instance in services_to_init:
                try:
                    if hasattr(service_instance, 'initialize'):
                        await service_instance.initialize()
                        logger.debug(f"Initialized {service_name}")
                except Exception as e:
                    logger.warning(f"Failed to initialize {service_name}: {e}")
                    # Continue with other services even if one fails
            
            self._services_initialized = True
            logger.info("All Eric services initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Eric services: {e}")
            raise
    
    async def _get_ai_service_manager(self) -> AIServiceManager:
        """Get AI service manager instance"""
        if not self.ai_service_manager:
            self.ai_service_manager = await get_ai_service_manager()
        return self.ai_service_manager
    
    def _detect_intent_simple(self, message: str) -> str:
        """Simple keyword-based intent detection for all Eric services"""
        message_lower = message.lower()
        
        # Greeting and help
        if any(word in message_lower for word in ["hello", "hi", "hey", "good morning", "good afternoon"]):
            return "greeting"
        elif any(word in message_lower for word in ["help", "what can you do", "capabilities", "features"]):
            return "help"
        
        # Core sales intents
        elif any(word in message_lower for word in ["lead", "prospect", "generate", "find customers", "persona"]):
            return "lead_generation"
        elif any(word in message_lower for word in ["score", "prioritize", "qualify", "rank leads"]):
            return "lead_scoring"
        elif any(word in message_lower for word in ["close", "deal", "sale", "revenue", "conversion", "win"]):
            return "deal_closing"
        elif any(word in message_lower for word in ["forecast", "predict", "projection", "revenue", "pipeline"]):
            return "sales_forecasting"
        elif any(word in message_lower for word in ["crm", "automate", "workflow", "sync"]):
            return "crm_automation"
        elif any(word in message_lower for word in ["objection", "resistance", "rejection", "handle", "respond to"]):
            return "objection_handling"
        elif any(word in message_lower for word in ["predict objection", "objection prediction"]):
            return "objection_prediction"
        elif any(word in message_lower for word in ["outreach", "email", "cold", "sequence", "campaign"]):
            return "sales_outreach"
        elif any(word in message_lower for word in ["email sequence", "sequence", "drip", "follow-up"]):
            return "email_sequences"
        elif any(word in message_lower for word in ["funnel", "pipeline", "stage", "sales process"]):
            return "sales_funnel"
        
        # Customer and analytics intents
        elif any(word in message_lower for word in ["customer insight", "insight", "behavior", "analytics"]):
            return "customer_insights"
        elif any(word in message_lower for word in ["journey", "customer journey", "map"]):
            return "customer_journey"
        elif any(word in message_lower for word in ["performance", "analytics", "metrics", "dashboard"]):
            return "performance_analytics"
        elif any(word in message_lower for word in ["predictive", "predict", "forecast analytics"]):
            return "predictive_analytics"
        
        # Advanced features
        elif any(word in message_lower for word in ["pitch", "generate pitch", "auto pitch"]):
            return "auto_pitch"
        elif any(word in message_lower for word in ["proposal", "build proposal", "automated proposal"]):
            return "proposal_builder"
        elif any(word in message_lower for word in ["conversational", "ai chat", "conversation"]):
            return "conversational_ai"
        elif any(word in message_lower for word in ["live chat", "chat support"]):
            return "live_chat"
        elif any(word in message_lower for word in ["image", "photo", "visual", "picture", "generate image", "create image"]):
            return "media_generation"
        elif any(word in message_lower for word in ["tone", "branding", "voice", "style"]):
            return "tone_branding"
        elif any(word in message_lower for word in ["follow-up", "schedule follow", "reminder"]):
            return "follow_up_scheduler"
        elif any(word in message_lower for word in ["recommend", "personalized", "suggest"]):
            return "personalized_recommendations"
        elif any(word in message_lower for word in ["pricing", "dynamic pricing", "price"]):
            return "dynamic_pricing"
        elif any(word in message_lower for word in ["competitor", "benchmark", "compare"]):
            return "competitor_benchmarking"
        elif any(word in message_lower for word in ["market trend", "trend alert", "trending"]):
            return "market_trend_alerts"
        elif any(word in message_lower for word in ["local market", "market insight", "regional"]):
            return "local_market_insights"
        elif any(word in message_lower for word in ["cross-sell", "upsell", "cross sell"]):
            return "cross_selling"
        elif any(word in message_lower for word in ["social proof", "testimonial", "case study"]):
            return "social_proof"
        elif any(word in message_lower for word in ["voice pitch", "pitch simulator", "practice"]):
            return "voice_pitch"
        elif any(word in message_lower for word in ["cross channel", "track", "lead tracking"]):
            return "cross_channel_tracking"
        elif any(word in message_lower for word in ["team dashboard", "team performance", "sales team"]):
            return "team_dashboard"
        elif any(word in message_lower for word in ["ethical", "sustainability", "ethical selling"]):
            return "ethical_selling"
        elif any(word in message_lower for word in ["gamify", "incentive", "reward"]):
            return "gamified_incentives"
        elif any(word in message_lower for word in ["mobile", "app", "monitoring"]):
            return "mobile_monitoring"
        elif any(word in message_lower for word in ["language", "multilanguage", "translate"]):
            return "multi_language"
        elif any(word in message_lower for word in ["onboarding", "setup", "wizard"]):
            return "onboarding_wizard"
        elif any(word in message_lower for word in ["training", "sales training", "learn"]):
            return "sales_training"
        elif any(word in message_lower for word in ["emerging channel", "new channel", "channel"]):
            return "emerging_channels"
        elif any(word in message_lower for word in ["prioritize", "ai prioritize", "rank"]):
            return "ai_lead_prioritization"
        elif any(word in message_lower for word in ["social selling", "social media sales"]):
            return "social_selling"
        else:
            return "general"
    
    def _get_fallback_response(self, intent: str) -> str:
        """Get fallback response for detected intent"""
        responses = {
            "greeting": [
                "Hello! I'm Eric, your AI sales assistant. How can I help you grow your business today?",
                "Hi there! I'm Eric, ready to help you boost your sales performance. What's your goal?",
                "Welcome! I'm Eric, your sales partner. Let's turn prospects into customers!"
            ],
            "help": [
                "I can help you with lead generation, deal closing, sales forecasting, CRM automation, and more. What do you need?",
                "I'm here to assist with all your sales needs. What challenge are you facing?",
                "I offer comprehensive sales support. How can I help you succeed today?"
            ],
            "lead_generation": [
                "I'll help you find and qualify new prospects. What's your target market?",
                "Let me create a lead generation strategy for you. What industry are you in?",
                "I'll analyze your market and find new opportunities. Tell me about your ideal customer."
            ],
            "deal_closing": [
                "I'll help you close more deals. What stage are your prospects in?",
                "Let me analyze your pipeline and identify closing opportunities.",
                "I'll provide strategies to move deals through your sales funnel."
            ],
            "sales_forecasting": [
                "I'll create accurate sales forecasts for you. What's your current pipeline?",
                "Let me analyze your sales data and predict future revenue.",
                "I'll help you plan for growth. What's your sales history?"
            ],
            "crm_automation": [
                "I'll help you automate your sales processes. What CRM do you use?",
                "Let me optimize your sales workflow and save you time.",
                "I'll set up automated follow-ups and lead nurturing for you."
            ],
            "objection_handling": [
                "I'll help you overcome sales objections. What objections do you face?",
                "Let me create objection handling strategies for your team.",
                "I'll prepare you for difficult sales conversations."
            ],
            "general": [
                "I'm here to help you succeed in sales. What do you need?",
                "Let's work together to improve your sales performance.",
                "I can help with any sales challenge. What's on your mind?"
            ]
        }
        
        import random
        return random.choice(responses.get(intent, responses["general"]))
    
    async def _break_down_request_into_tasks(self, message: str, user_id: int = None, db: AsyncSession = None) -> Dict[str, Any]:
        """Break down user request into structured tasks for sales automation
        
        Domain-specific for Eric (Sales):
        - CRM Platforms: Salesforce, HubSpot, Pipedrive, Zoho, Freshsales
        - Sales Tools: Email sequences, LinkedIn outreach, EricLead generation, EricDeal closing
        - Task types: Sales workflows, CRM pipelines, Email sequences, EricLead qualification steps
        """
        import re
        
        tasks = {
            "total_tasks": 1,
            "task_type": "general",
            "requirements": [],
            "completion_criteria": [],
            "domain": "sales",
            "crm_platforms": [],
            "sales_tools": []
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
        
        # Get CRM integrations specifically
        crm_integrations = get_integrations_by_type("crm")
        crm_platforms = {k: v["display_name"] for k, v in crm_integrations.items()}
        
        # Detect ALL platforms mentioned (including social media for outreach)
        detected_platforms = detect_platforms_in_message(message, all_platforms)
        
        # Filter detected platforms to only include user's connected platforms (if any)
        if user_connected_platforms and detected_platforms:
            detected_platforms = [p for p in detected_platforms if any(cp.lower() in p.lower() or p.lower() in cp.lower() for cp in user_connected_platforms)]
        
        # Detect CRM platforms mentioned
        detected_crms = []
        for crm_key, crm_name in crm_platforms.items():
            if crm_key in message_lower or crm_name.lower() in message_lower:
                detected_crms.append(crm_name)
        
        # Filter detected CRMs to only include user's connected integrations
        if user_connected_integrations and detected_crms:
            detected_crms = [c for c in detected_crms if any(ci.lower() in c.lower() or c.lower() in ci.lower() for ci in user_connected_integrations)]
        
        # Detect ALL integrations mentioned (CRM, marketing, automation, etc.)
        detected_integrations = detect_integrations_in_message(message, all_integrations)
        detected_tools = [integ["display_name"] for integ in detected_integrations]
        
        # Filter detected integrations to only include user's connected integrations (if any)
        if user_connected_integrations and detected_tools:
            detected_tools = [t for t in detected_tools if any(ci.lower() in t.lower() or t.lower() in ci.lower() for ci in user_connected_integrations)]
        
        # Sales-specific tool keywords (for detection even if not in integrations)
        sales_keywords = {
            "email": "Email Sequences",
            "linkedin": "LinkedIn Outreach",
            "lead": "EricLead Generation",
            "deal": "EricDeal Closing",
            "pipeline": "Pipeline Management",
            "forecast": "Sales Forecasting",
            "outreach": "Sales Outreach"
        }
        
        # Add sales-specific tools if mentioned
        for keyword, tool_name in sales_keywords.items():
            if keyword in message_lower and tool_name not in detected_tools:
                detected_tools.append(tool_name)
        
        # Detect sales pipeline/stage requests
        if "pipeline" in message_lower or "stage" in message_lower or "funnel" in message_lower:
            stage_matches = re.findall(r'(\d+)[\s-]?(?:stage|phase|step)', message_lower)
            if stage_matches:
                tasks["total_tasks"] = int(stage_matches[0])
                tasks["task_type"] = "sales_pipeline"
                tasks["crm_platforms"] = detected_crms if detected_crms else ["All CRMs"]
                tasks["sales_tools"] = detected_tools if detected_tools else ["All sales tools"]
                tasks["platforms"] = detected_platforms if detected_platforms else []
                tasks["requirements"] = [
                    f"Stage {i+1}: Complete sales pipeline stage with criteria, actions, automation rules, CRM integration, and platform outreach options" 
                    for i in range(tasks["total_tasks"])
                ]
                tasks["completion_criteria"] = [
                    f"All {tasks['total_tasks']} pipeline stages must be detailed",
                    "Each stage must include: criteria, actions, automation rules, and CRM integration",
                    f"CRM platforms: {', '.join(tasks['crm_platforms'])}",
                    f"Sales tools: {', '.join(tasks['sales_tools'])}",
                    f"Available outreach platforms: {', '.join(tasks['platforms']) if tasks['platforms'] else 'All social media platforms (Twitter, Instagram, TikTok, LinkedIn, etc.)'}"
                ]
        
        # Detect email sequence requests
        elif "email" in message_lower and ("sequence" in message_lower or "campaign" in message_lower or "drip" in message_lower):
            email_matches = re.findall(r'(\d+)[\s-]?(?:email|message|step)', message_lower)
            if email_matches:
                tasks["total_tasks"] = int(email_matches[0])
                tasks["task_type"] = "email_sequence"
                tasks["sales_tools"] = ["Email Sequences"]
                tasks["requirements"] = [
                    f"Email {i+1}: Complete email with subject, body, timing, triggers, and follow-up actions" 
                    for i in range(tasks["total_tasks"])
                ]
                tasks["completion_criteria"] = [
                    f"All {tasks['total_tasks']} emails must be provided",
                    "Each email must include: subject line, body content, send timing, triggers, and follow-up actions",
                    "Emails must be personalized and include CRM integration points"
                ]
        
        # Detect lead qualification steps
        elif "lead" in message_lower and ("qualif" in message_lower or "score" in message_lower or "step" in message_lower):
            step_matches = re.findall(r'(\d+)[\s-]?(?:step|criteria|question)', message_lower)
            if step_matches:
                tasks["total_tasks"] = int(step_matches[0])
                tasks["task_type"] = "lead_qualification"
                tasks["crm_platforms"] = detected_crms if detected_crms else ["All CRMs"]
                tasks["requirements"] = [
                    f"Step {i+1}: EricLead qualification step with criteria, scoring, automation rules, and CRM field mappings" 
                    for i in range(tasks["total_tasks"])
                ]
                tasks["completion_criteria"] = [
                    f"All {tasks['total_tasks']} qualification steps must be provided",
                    "Each step must include: criteria, scoring methodology, automation rules, and CRM field mappings",
                    f"CRM integration: {', '.join(tasks['crm_platforms'])}"
                ]
        
        # Detect sales process/workflow requests
        elif "process" in message_lower or "workflow" in message_lower or "steps" in message_lower:
            step_matches = re.findall(r'(\d+)[\s-]?(?:step|stage|phase)', message_lower)
            if step_matches:
                tasks["total_tasks"] = int(step_matches[0])
                tasks["task_type"] = "sales_workflow"
                tasks["crm_platforms"] = detected_crms if detected_crms else ["All CRMs"]
                tasks["sales_tools"] = detected_tools if detected_tools else ["All sales tools"]
                tasks["platforms"] = detected_platforms if detected_platforms else []
                tasks["requirements"] = [
                    f"Step {i+1}: Sales workflow step with actions, tools, CRM integration, platform outreach options, and automation opportunities" 
                    for i in range(tasks["total_tasks"])
                ]
                tasks["completion_criteria"] = [
                    f"All {tasks['total_tasks']} workflow steps must be provided",
                    "Each step must include: actions, tools, CRM integration points, platform outreach options, and automation opportunities",
                    f"CRM platforms: {', '.join(tasks['crm_platforms'])}",
                    f"Sales tools: {', '.join(tasks['sales_tools'])}",
                    f"Available outreach platforms: {', '.join(tasks['platforms']) if tasks['platforms'] else 'All platforms (Twitter, Instagram, TikTok, LinkedIn, Facebook, etc.)'}"
                ]
        
        # Detect deal closing strategies
        elif "deal" in message_lower and ("close" in message_lower or "strategy" in message_lower):
            strategy_matches = re.findall(r'(\d+)[\s-]?(?:strategy|tactic|approach)', message_lower)
            if strategy_matches:
                tasks["total_tasks"] = int(strategy_matches[0])
                tasks["task_type"] = "deal_closing"
                tasks["requirements"] = [
                    f"Strategy {i+1}: EricDeal closing strategy with approach, objection handling, CRM tracking, and success metrics" 
                    for i in range(tasks["total_tasks"])
                ]
                tasks["completion_criteria"] = [
                    f"All {tasks['total_tasks']} closing strategies must be provided",
                    "Each strategy must include: approach, objection handling, CRM tracking fields, and success metrics"
                ]
        
        # Detect numbered list requests (sales tactics, objection responses, etc.)
        elif re.search(r'\d+\s*(?:different|various|multiple|tactic|strategy|objection|response)', message_lower):
            num_matches = re.findall(r'(\d+)\s*(?:different|various|multiple|tactic|strategy|objection|response)', message_lower)
            if num_matches:
                tasks["total_tasks"] = int(num_matches[0])
                tasks["task_type"] = "sales_tactics"
                tasks["requirements"] = [
                    f"Tactic {i+1}: Complete sales tactic with description, use case, CRM integration, and expected outcomes" 
                    for i in range(tasks["total_tasks"])
                ]
                tasks["completion_criteria"] = [
                    f"All {tasks['total_tasks']} tactics must be provided",
                    "Each tactic must include: description, use case, CRM integration points, and expected outcomes",
                    "Tactics must be actionable and measurable"
                ]
        
        return tasks
    
    def _generate_simple_response(self, intent: str, message: str) -> str:
        """Generate simple responses based on intent"""
        return self._get_fallback_response(intent)
    
    def _generate_thinking_steps(self, intent: str, message: str, user_id: int, db: AsyncSession = None) -> List[str]:
        """Generate thinking steps based on intent and message context"""
        steps = []
        
        if intent == "lead_generation":
            steps = [
                "Analyzing lead generation requirements...",
                "Reviewing target audience and criteria...",
                "Checking available lead sources...",
                "Preparing lead generation strategy..."
            ]
        elif intent == "deal_closing":
            steps = [
                "Reviewing deal details and pipeline...",
                "Analyzing closing opportunities...",
                "Identifying potential objections...",
                "Preparing closing strategy..."
            ]
        elif intent == "sales_forecasting":
            steps = [
                "Gathering sales data and metrics...",
                "Analyzing historical performance...",
                "Calculating forecast projections...",
                "Preparing sales forecast report..."
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
            # Ensure services are initialized
            if not self._services_initialized:
                await self.initialize()
            
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
            
            # Detect intent first to determine if we need to call services
            logger = logging.getLogger(__name__)
            detected_intent = self._detect_intent_simple(message)
            logger.info(f"Eric: Detected intent: {detected_intent} for message: {message[:50]}...")
            
            # Generate thinking steps based on intent
            thinking_steps = self._generate_thinking_steps(detected_intent, message, user_id, db)
            
            # Try to use services for specific intents, then format with LLM
            service_result = None
            try:
                # Call appropriate service based on intent
                if detected_intent == "lead_generation":
                    if any(word in message.lower() for word in ["generate", "find", "create", "persona"]):
                        service_result = await self.lead_generation.generate_leads(
                            user_id=user_id,
                            criteria={},
                            db=db,
                            user_message=message
                        )
                
                elif detected_intent == "lead_scoring":
                    service_result = await self.lead_scoring.score_leads(user_id=user_id, db=db)
                
                elif detected_intent == "deal_closing":
                    if any(word in message.lower() for word in ["analyze", "review", "close"]):
                        service_result = await self.deal_closing.analyze_deals(user_id=user_id, db=db)
                    elif any(word in message.lower() for word in ["assist", "help", "strategy"]):
                        service_result = await self.deal_closing_assistance.assist_with_closing(user_id=user_id, db=db)
                
                elif detected_intent == "sales_forecasting":
                    service_result = await self.sales_forecasting.generate_forecast(user_id=user_id, db=db)
                
                elif detected_intent == "objection_handling":
                    objection_type = "general"
                    if "price" in message.lower():
                        objection_type = "price"
                    elif "time" in message.lower() or "timing" in message.lower():
                        objection_type = "timing"
                    service_result = await self.objection_handling.handle_objection(
                        user_id=user_id,
                        objection_type=objection_type,
                        context=message,
                        db=db
                    )
                
                elif detected_intent == "sales_outreach":
                    if any(word in message.lower() for word in ["email", "cold", "linkedin"]):
                        # Extract parameters from message
                        service_result = await self.sales_outreach.create_outreach_sequence(
                            user_id=user_id,
                            channel="email",  # Default, can be extracted from message
                            message=message,
                            db=db
                        )
                
                elif detected_intent == "email_sequences":
                    # Extract number of steps from message
                    import re
                    steps_match = re.search(r'(\d+)\s*step', message.lower())
                    steps = int(steps_match.group(1)) if steps_match else 6
                    service_result = await self.email_sequences.create_sequence(
                        user_id=user_id,
                        steps=steps,
                        goal="demo_booking",  # Can be extracted from message
                        db=db
                    )
                
                elif detected_intent == "customer_insights":
                    service_result = await self.customer_insights.analyze_customers(user_id=user_id, db=db)
                
                elif detected_intent == "performance_analytics":
                    service_result = await self.performance_analytics.get_analytics(user_id=user_id, db=db)
                
                elif detected_intent == "sales_funnel":
                    if "plan" in message.lower() or "create" in message.lower():
                        # Extract days from message
                        import re
                        days_match = re.search(r'(\d+)\s*day', message.lower())
                        days = int(days_match.group(1)) if days_match else 30
                        service_result = await self.sales_funnel.create_pipeline_plan(
                            user_id=user_id,
                            days=days,
                            goal="increase_conversion",  # Extract from message
                            db=db
                        )
                
                elif detected_intent == "media_generation":
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
                    service_result = await self.media.generate_image(
                        prompt=prompt,
                        context=message,
                        user_id=user_id,
                        user_tier=user_tier,
                        auto_generate_prompt=True
                    )
                    
                    # If image generation successful, add image_url to service_result for frontend
                    if service_result.get("success"):
                        service_result["image_url"] = service_result.get("url")
                
                # Add more service calls as needed for other intents
                
            except Exception as service_error:
                logger.warning(f"Eric: Service call failed for {detected_intent}: {service_error}")
                service_result = None
            
            # Use LLM to format response (with service results if available)
            try:
                ai_manager = await self._get_ai_service_manager()
                
                # Build context from service results
                context_text = ""
                if service_result and service_result.get("success"):
                    context_text = f"\n\nService Results:\n{self._format_service_results(service_result, detected_intent)}"
                
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
                        agent_config = await get_agent_configuration_for_user(user_id, "eric", db)
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
                        "content": f"""You are Eric, an AI-powered sales automation assistant specializing in comprehensive sales management.
{custom_instructions_text}
Your full capabilities include:

1. **EricLead Generation & Qualification**
   - EricLead generation from multiple sources
   - EricLead scoring and prioritization using AI
   - EricLead qualification and segmentation
   - Persona creation and targeting

2. **EricDeal Closing & Management**
   - EricDeal closing strategies and techniques
   - EricDeal closing assistance with real-time guidance
   - Pipeline management and optimization
   - Sales funnel creation and analysis

3. **Sales Forecasting & Analytics**
   - Sales forecasting and revenue prediction
   - Performance analytics and metrics
   - Predictive analytics for sales outcomes
   - Pipeline performance analysis

4. **CRM Automation**
   - CRM integration (Salesforce, HubSpot, Pipedrive)
   - Automated workflows and processes
   - Data synchronization
   - CRM analytics and insights

5. **Sales Outreach**
   - Cold email sequences
   - LinkedIn outreach automation
   - Multi-channel outreach campaigns
   - Personalized messaging at scale

6. **Email Sequences**
   - Drip campaign creation
   - Follow-up automation
   - Demo booking sequences
   - EricLead nurturing workflows

7. **EricObjection Handling**
   - EricObjection response strategies
   - EricObjection prediction using AI
   - Handling price, timing, and authority objections
   - Sales conversation optimization

8. **Customer Insights**
   - Customer behavior analysis
   - Customer journey mapping
   - Customer segmentation
   - Churn prediction and prevention

9. **Advanced Features**
   - Auto-pitch generation
   - Automated proposal building
   - Voice pitch simulation
   - Social proof generation
   - Cross-selling and upselling strategies
   - Dynamic pricing recommendations
   - Competitor benchmarking
   - Local market insights
   - Market trend alerts
   - Cross-channel lead tracking
   - Team sales dashboard
   - Ethical sales scoring
   - Gamified incentives
   - Mobile app monitoring
   - Multi-language support
   - Sales training and onboarding
   - Emerging channels integration
   - Social selling optimization
   - Personalized sales recommendations
   - Tone and branding customization
   - Advanced conversational AI
   - Live chat support
   - Dynamic follow-up scheduling
   - AI lead prioritization

Always be helpful, professional, and provide actionable advice that helps users close more deals and grow their revenue. Use service results when available to give specific, data-driven responses. When service results aren't available, provide expert guidance on how to use the features.

**IMPORTANT:** Use emojis and icons naturally in your responses to make them more engaging and visually appealing. Use relevant emojis like 💰 for sales, 📈 for growth, 🎯 for targets, 📊 for analytics, 🤝 for deals, 📧 for outreach, ✅ for success, etc. Make your responses feel modern and polished.
{task_instructions}
Current intent detected: {detected_intent}
{context_text if context_text else "No service results available - provide expert guidance based on the user's request."}"""
                    },
                    {
                        "role": "user",
                        "content": message
                    }
                ]
                
                logger.info(f"Eric: Attempting LLM generation (with service results: {service_result is not None})...")
                
                # Generate AI response using LLM (direct keyword args like Aria/Clara)
                ai_response = await ai_manager.generate_text(
                    messages=messages,
                    max_tokens=16000,
                    temperature=0.7
                )
                
                if ai_response.success and ai_response.text_content:
                    logger.info(f"Eric: LLM response successful. Service: {ai_response.service_used}")
                    response = ai_response.text_content
                    confidence = 0.9
                else:
                    # Fallback to simple response
                    logger.warning(f"Eric: LLM response failed ({ai_response.error}), using fallback template")
                    if service_result and service_result.get("success"):
                        # Format service results directly
                        response = self._format_service_results(service_result, detected_intent)
                    else:
                        response = self._generate_simple_response(detected_intent, message)
                    confidence = 0.8
                    
            except Exception as ai_error:
                # Fallback to simple response if AI service fails
                logger = logging.getLogger(__name__)
                logger.error(f"Eric: LLM exception occurred: {ai_error}", exc_info=True)
                detected_intent = self._detect_intent_simple(message)
                confidence = 0.8
                response = self._generate_simple_response(detected_intent, message)
            
            # Update session context
            session["last_intent"] = detected_intent
            
            # Build response with thinking steps and service metadata
            result = {
                "success": True,
                "response": response,
                "thinking_steps": thinking_steps,
                "intent": detected_intent,
                "confidence": confidence,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }
            
            # Add service information if services were called
            if service_result:
                result["service_used"] = True
                # Include image_url if image generation was successful
                if service_result.get("image_url"):
                    result["image_url"] = service_result.get("image_url")
                service_map = {
                    "lead_generation": "LeadGenerationService",
                    "lead_scoring": "LeadScoringService",
                    "deal_closing": "DealClosingService",
                    "sales_forecasting": "SalesForecastingService",
                    "objection_handling": "ObjectionHandlingService",
                    "sales_outreach": "SalesOutreachService",
                    "media_generation": "MediaService",
                    "email_sequences": "EmailSequencesService",
                    "customer_insights": "CustomerInsightsService",
                    "performance_analytics": "PerformanceAnalyticsService",
                    "sales_funnel": "SalesFunnelService"
                }
                result["service_name"] = service_map.get(detected_intent, "UnknownService")
            else:
                result["service_used"] = False
            
            return result
            
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Eric: Error in process_chat_message: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Failed to process chat message: {str(e)}",
                "response": "I apologize, but I encountered an error processing your message. Please try again or rephrase your request."
            }
    
    def _format_service_results(self, service_result: Dict[str, Any], intent: str) -> str:
        """Format service results into readable text for LLM context"""
        try:
            if intent == "lead_generation" and "total_leads" in service_result:
                return f"""EricLead Generation Results:
- Total leads found: {service_result.get('total_leads', 0)}
- Qualified leads: {service_result.get('qualified_leads', 0)}
- Sources: {', '.join(service_result.get('sources', []))}"""
            
            elif intent == "lead_scoring" and "high_priority" in service_result:
                return f"""EricLead Scoring Results:
- High-priority leads: {service_result.get('high_priority', 0)}
- Medium-priority leads: {service_result.get('medium_priority', 0)}
- Low-priority leads: {service_result.get('low_priority', 0)}"""
            
            elif intent == "deal_closing" and "active_deals" in service_result:
                return f"""EricDeal Analysis Results:
- Active deals: {service_result.get('active_deals', 0)}
- Deals ready to close: {service_result.get('ready_to_close', 0)}
- Deals at risk: {service_result.get('at_risk', 0)}"""
            
            elif intent == "sales_forecasting" and "forecast" in service_result:
                forecast = service_result.get('forecast', {})
                return f"""Sales Forecast:
- Projected revenue: {forecast.get('projected_revenue', 'N/A')}
- Confidence level: {forecast.get('confidence', 'N/A')}
- Time period: {forecast.get('period', 'N/A')}"""
            
            elif intent == "objection_handling" and "response" in service_result:
                return f"""EricObjection Handling Response:
{service_result.get('response', '')}
Technique: {service_result.get('technique', 'N/A')}"""
            
            elif intent == "email_sequences" and "sequence_id" in service_result:
                return f"""Email Sequence Created:
- Sequence ID: {service_result.get('sequence_id')}
- Steps: {service_result.get('steps', 0)}
- Goal: {service_result.get('goal', 'N/A')}"""
            
            elif intent == "sales_funnel" and "plan_id" in service_result:
                return f"""Sales Funnel Plan Created:
- Plan ID: {service_result.get('plan_id')}
- Duration: {service_result.get('days', 0)} days
- Goal: {service_result.get('goal', 'N/A')}"""
            
            elif intent == "customer_insights" and "insights" in service_result:
                insights = service_result.get('insights', {})
                return f"""Customer Insights:
- Total customers analyzed: {insights.get('total_customers', 0)}
- Key behaviors: {insights.get('key_behaviors', [])}
- Recommendations: {insights.get('recommendations', [])}"""
            
            elif intent == "performance_analytics" and "metrics" in service_result:
                metrics = service_result.get('metrics', {})
                return f"""Performance Metrics:
- Conversion rate: {metrics.get('conversion_rate', 'N/A')}
- Average deal size: {metrics.get('avg_deal_size', 'N/A')}
- Sales cycle length: {metrics.get('sales_cycle_days', 'N/A')} days"""
            
            else:
                # Generic formatting
                return f"Service Result: {str(service_result)[:500]}"
                
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.warning(f"Eric: Failed to format service results: {e}")
            return f"Service completed: {service_result.get('message', 'Operation successful')}"
    
    def _fallback_intent_detection(self, message: str) -> Dict[str, Any]:
        """Fallback intent detection when NLP fails"""
        message_lower = message.lower()
        
        # Sales-specific intent detection
        if any(word in message_lower for word in ["hello", "hi", "hey", "good morning", "good afternoon"]):
            return {"intent": "greeting", "confidence": 0.8}
        elif any(word in message_lower for word in ["help", "what can you do", "capabilities", "features"]):
            return {"intent": "help", "confidence": 0.8}
        elif any(word in message_lower for word in ["lead", "prospect", "generate", "find customers"]):
            return {"intent": "lead_generation", "confidence": 0.7}
        elif any(word in message_lower for word in ["close", "deal", "sale", "revenue", "conversion"]):
            return {"intent": "deal_closing", "confidence": 0.7}
        elif any(word in message_lower for word in ["forecast", "predict", "projection", "revenue"]):
            return {"intent": "sales_forecasting", "confidence": 0.7}
        elif any(word in message_lower for word in ["crm", "automate", "workflow", "process"]):
            return {"intent": "crm_automation", "confidence": 0.7}
        elif any(word in message_lower for word in ["objection", "resistance", "rejection", "no"]):
            return {"intent": "objection_handling", "confidence": 0.7}
        elif any(word in message_lower for word in ["budget", "spend", "cost", "allocation"]):
            return {"intent": "budget_management", "confidence": 0.7}
        else:
            return {"intent": "general", "confidence": 0.5}
    
    def _detect_intent_simple(self, message: str) -> str:
        """Simple intent detection"""
        return self._fallback_intent_detection(message)["intent"]
    
    def _generate_simple_response(self, intent: str, message: str) -> str:
        """Generate simple response based on intent"""
        return self._get_fallback_response(intent)
    
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
        
        if intent == "greeting":
            return self._get_random_response("greeting")
        elif intent == "help":
            return self._get_random_response("help")
        elif intent == "lead_generation":
            return await self._handle_lead_generation(user_id, message, session, db)
        elif intent == "deal_closing":
            return await self._handle_deal_closing(user_id, message, session, db)
        elif intent == "sales_forecasting":
            return await self._handle_sales_forecasting(user_id, message, session, db)
        elif intent == "crm_automation":
            return await self._handle_crm_automation(user_id, message, session, db)
        elif intent == "objection_handling":
            return await self._handle_objection_handling(user_id, message, session, db)
        elif intent == "budget_management":
            return await self._handle_budget_management(user_id, message, session, db)
        else:
            return await self._handle_general_query(user_id, message, session, db)
    
    async def _handle_lead_generation(
        self,
        user_id: int,
        message: str,
        session: Dict[str, Any],
        db: AsyncSession
    ) -> str:
        """Handle lead generation related queries"""
        try:
            if any(word in message.lower() for word in ["find", "generate", "new leads", "prospects"]):
                # Use actual lead generation service
                try:
                    lead_result = await self.lead_generation.generate_leads(
                        user_id=user_id,
                        criteria={},
                        db=db
                    )
                    
                    if lead_result.get("success"):
                        return f"""I've generated new leads for you! Here's what I found:

🎯 **EricLead Generation Results:**
• New leads found: {lead_result.get('total_leads', 0)}
• High-quality prospects: {lead_result.get('qualified_leads', 0)}
• EricLead sources: {', '.join(lead_result.get('sources', []))}

📊 **Next Steps:**
• Review the lead details in your dashboard
• Set up lead scoring for prioritization
• Create outreach sequences
• Track engagement and conversion

Would you like me to help you score these leads or create outreach campaigns?"""
                    else:
                        return "I'm working on finding new leads for you. Let me check your lead generation settings and suggest some strategies to improve your lead flow."
                except Exception as service_error:
                    return f"I'm setting up lead generation for you. Let me know what type of leads you're looking for and I'll help you create a comprehensive strategy!"
            
            elif any(word in message.lower() for word in ["qualify", "score", "prioritize"]):
                # Use actual lead scoring service
                try:
                    scoring_result = await self.lead_scoring.score_leads(
                        user_id=user_id,
                        db=db
                    )
                    
                    if scoring_result.get("success"):
                        return f"""I've scored your leads! Here's the analysis:

⭐ **EricLead Scoring Results:**
• High-priority leads: {scoring_result.get('high_priority', 0)}
• Medium-priority leads: {scoring_result.get('medium_priority', 0)}
• Low-priority leads: {scoring_result.get('low_priority', 0)}

📈 **Scoring Criteria Used:**
• Company fit and industry alignment
• Engagement with your content
• Budget and decision-making authority
• Timeline and urgency indicators

Would you like me to help you prioritize follow-up actions or create targeted outreach campaigns?"""
                    else:
                        return "I'm setting up lead scoring for you. Let me know your ideal customer criteria and I'll help you create a scoring system."
                except Exception as service_error:
                    return "I'll help you set up lead scoring! What criteria are most important for qualifying your leads?"
            
            else:
                return self._get_random_response("lead_generation")
                
        except Exception as e:
            return f"I encountered an issue with lead generation: {str(e)}. Please try again or let me know what specific lead generation help you need."
    
    async def _handle_deal_closing(
        self,
        user_id: int,
        message: str,
        session: Dict[str, Any],
        db: AsyncSession
    ) -> str:
        """Handle deal closing related queries"""
        try:
            if any(word in message.lower() for word in ["close", "deal", "conversion", "win"]):
                # Use actual deal closing service
                try:
                    closing_result = await self.deal_closing.analyze_deals(
                        user_id=user_id,
                        db=db
                    )
                    
                    if closing_result.get("success"):
                        return f"""I've analyzed your deals and here's how to close more! 

🎯 **EricDeal Analysis Results:**
• Active deals: {closing_result.get('active_deals', 0)}
• Deals ready to close: {closing_result.get('ready_to_close', 0)}
• Deals at risk: {closing_result.get('at_risk', 0)}

📊 **Closing Strategies:**
• Create urgency and scarcity
• Address final objections
• Use assumptive close techniques
• Provide social proof and testimonials
• Offer limited-time incentives

💡 **Next Steps:**
• Focus on deals ready to close
• Address objections in at-risk deals
• Follow up consistently
• Track closing metrics

What specific deal would you like help closing?"""
                    else:
                        return "I'm analyzing your deals to help you close more. Let me know what stage your deals are in and I'll provide specific closing strategies!"
                except Exception as service_error:
                    return "I'll help you close more deals! What's the current stage of your most important deal?"
            
            elif any(word in message.lower() for word in ["objection", "resistance", "concern"]):
                # Use actual objection handling service
                try:
                    objection_result = await self.objection_handling.handle_objection(
                        user_id=user_id,
                        objection_type="general",
                        context=message,
                        db=db
                    )
                    
                    if objection_result.get("success"):
                        return f"""I'll help you handle that objection! Here's my approach:

🛡️ **EricObjection Response:**
{objection_result.get('response', 'Let me help you address this concern professionally.')}

💬 **Key Points:**
• Listen to understand their concern
• Acknowledge their position
• Ask clarifying questions
• Provide specific solutions
• Confirm the objection is resolved

Would you like me to help you practice this response or address other objections?"""
                    else:
                        return "I'll help you handle objections like a pro! What specific objection are you facing? I'll provide a tailored response strategy."
                except Exception as service_error:
                    return "I'll help you handle objections! What's the specific concern your prospect raised?"
            
            else:
                return self._get_random_response("deal_closing")
                
        except Exception as e:
            return f"I encountered an issue with deal closing: {str(e)}. Please try again or let me know what specific closing help you need."
    
    async def _handle_sales_forecasting(
        self,
        user_id: int,
        message: str,
        session: Dict[str, Any],
        db: AsyncSession
    ) -> str:
        """Handle sales forecasting related queries"""
        try:
            if any(word in message.lower() for word in ["forecast", "predict", "projection", "revenue"]):
                return """I'll help you create accurate sales forecasts! Here's my approach:

📊 **Forecasting Methods:**
• Historical data analysis
• Pipeline stage analysis
• EricLead conversion rates
• Seasonal trend adjustments
• Market condition factors

🎯 **Key Metrics to Track:**
• Average deal size
• Sales cycle length
• Win/loss rates
• EricLead velocity
• Activity metrics

📈 **Forecast Benefits:**
• Better resource planning
• Improved goal setting
• Early warning systems
• Performance optimization
• Revenue predictability

What's your current pipeline looking like? I'll help you create a detailed forecast!"""
            
            else:
                return self._get_random_response("sales_forecasting")
                
        except Exception as e:
            return f"I encountered an issue with sales forecasting: {str(e)}. Please try again or let me know what specific forecasting help you need."
    
    async def _handle_crm_automation(
        self,
        user_id: int,
        message: str,
        session: Dict[str, Any],
        db: AsyncSession
    ) -> str:
        """Handle CRM automation related queries"""
        try:
            if any(word in message.lower() for word in ["automate", "workflow", "process", "efficiency"]):
                return """I'll help you automate your CRM processes! Here's what I can set up:

🤖 **CRM Automation Features:**
• EricLead scoring and routing
• Follow-up sequences
• Task and reminder automation
• Email and call logging
• Pipeline stage progression

⚡ **Automation Benefits:**
• Save time on repetitive tasks
• Ensure consistent follow-up
• Reduce human error
• Improve data quality
• Increase productivity

🛠️ **Common Automations:**
• New lead notifications
• Follow-up reminders
• EricDeal stage updates
• Email sequences
• Report generation

What CRM system are you using? I'll help you set up the perfect automation!"""
            
            else:
                return self._get_random_response("crm_automation")
                
        except Exception as e:
            return f"I encountered an issue with CRM automation: {str(e)}. Please try again or let me know what specific automation help you need."
    
    async def _handle_objection_handling(
        self,
        user_id: int,
        message: str,
        session: Dict[str, Any],
        db: AsyncSession
    ) -> str:
        """Handle objection handling related queries"""
        try:
            if any(word in message.lower() for word in ["objection", "resistance", "concern", "pushback"]):
                return """I'll help you master objection handling! Here's my proven system:

🎯 **The LAER Method:**
• **Listen** - Hear them out completely
• **Acknowledge** - Validate their concern
• **Explore** - Ask questions to understand
• **Respond** - Address with solutions

💪 **Top EricObjection Responses:**
• "Price too high" → "I understand budget is important. Let me show you the ROI..."
• "Need to think" → "What specific concerns do you have about moving forward?"
• "Not ready" → "What would need to happen for you to be ready?"
• "Check with team" → "Who else is involved in this decision?"

🛡️ **Pro Tips:**
• Prepare responses for common objections
• Use "feel, felt, found" technique
• Turn objections into questions
• Always follow up after addressing

What objection are you facing? I'll help you craft the perfect response!"""
            
            else:
                return self._get_random_response("objection_handling")
                
        except Exception as e:
            return f"I encountered an issue with objection handling: {str(e)}. Please try again or let me know what specific objection help you need."
    
    async def _handle_budget_management(
        self,
        user_id: int,
        message: str,
        session: Dict[str, Any],
        db: AsyncSession
    ) -> str:
        """Handle budget management related queries"""
        try:
            if any(word in message.lower() for word in ["budget", "cost", "price", "investment"]):
                return """I'll help you manage your sales budget effectively! Here's my approach:

💰 **Budget Management Strategies:**
• Track cost per lead and acquisition
• Optimize spend across channels
• Measure ROI on sales activities
• Plan for seasonal variations
• Allocate resources efficiently

📊 **Key Budget Metrics:**
• Customer Acquisition Cost (CAC)
• Lifetime Value (LTV)
• Cost per opportunity
• Sales efficiency ratios
• Marketing spend attribution

🎯 **Budget Optimization:**
• Focus on high-converting channels
• Eliminate low-performing activities
• Test and scale successful campaigns
• Negotiate better rates
• Leverage free/low-cost tools

What's your current budget situation? I'll help you optimize it for maximum results!"""
            
            else:
                return self._get_random_response("budget_management")
                
        except Exception as e:
            return f"I encountered an issue with budget management: {str(e)}. Please try again or let me know what specific budget help you need."
    
    async def _handle_general_query(
        self,
        user_id: int,
        message: str,
        session: Dict[str, Any],
        db: AsyncSession
    ) -> str:
        """Handle general queries and provide helpful guidance"""
        try:
            # Use AI service manager to generate a contextual response
            ai_manager = await self._get_ai_service_manager()
            messages = [
                {"role": "system", "content": "User asking general question to Eric sales assistant"},
                {"role": "user", "content": f"User message: {message}\n\nProvide a helpful, friendly response as Eric, a sales AI assistant. Keep it conversational and offer to help with specific sales tasks."}
            ]
            
            response = await ai_manager.generate_text(
                messages=messages,
                max_tokens=200,
                temperature=0.7
            )
            
            if response.success:
                return response.text_content
            else:
                return "I'm here to help you with all aspects of sales! I can help with lead generation, deal closing, forecasting, CRM automation, objection handling, and much more. What would you like to work on today?"
                
        except Exception as e:
            return "I'm here to help you with sales! I can assist with lead generation, deal closing, forecasting, CRM automation, and objection handling. What would you like to focus on?"
    
    def _get_random_response(self, intent: str) -> str:
        """Get a random response for a given intent"""
        responses = self.intent_responses.get(intent, ["I'm here to help you with that!"])
        import random
        return random.choice(responses)
    
    def _get_suggested_actions(self, intent: str) -> List[str]:
        """Get suggested actions based on the detected intent"""
        suggestions = {
            "greeting": ["Generate leads", "Close deals", "Check forecast", "Automate CRM"],
            "help": ["EricLead generation", "EricDeal closing", "Sales forecasting", "CRM automation"],
            "lead_generation": ["Find prospects", "Qualify leads", "Create outreach", "Score leads"],
            "deal_closing": ["Close techniques", "Handle objections", "Create urgency", "Follow up"],
            "sales_forecasting": ["Create forecast", "Analyze pipeline", "Track metrics", "Predict revenue"],
            "crm_automation": ["Set up workflows", "Automate tasks", "Create sequences", "Optimize processes"],
            "objection_handling": ["Handle objections", "Prepare responses", "Practice techniques", "Build confidence"],
            "budget_management": ["Track costs", "Optimize spend", "Measure ROI", "Plan budget"]
        }
        
        return suggestions.get(intent, ["Get help", "Learn more", "Explore features"])
    
    async def get_chat_suggestions(self, user_id: int) -> List[str]:
        """Get personalized chat suggestions for the user"""
        return [
            "Help me generate more leads",
            "Show me how to close deals better",
            "Create a sales forecast for me",
            "Set up CRM automation",
            "Help me handle objections",
            "Optimize my sales budget",
            "Analyze my sales performance",
            "Plan my sales strategy"
        ]
    
    async def end_chat_session(self, session_id: str) -> Dict[str, Any]:
        """End a chat session and clean up"""
        try:
            if session_id in self.active_sessions:
                session = self.active_sessions.pop(session_id)
                return {
                    "success": True,
                    "message": "Chat session ended successfully",
                    "session_duration": (datetime.now() - session["created_at"]).total_seconds(),
                    "total_messages": session["message_count"]
                }
            else:
                return {
                    "success": False,
                    "error": "Session not found"
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to end session: {str(e)}"
            }
    
    async def get_chat_history(
        self,
        user_id: int,
        session_id: Optional[str] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """Get chat history for a user or specific session"""
        try:
            if session_id and session_id in self.active_sessions:
                session = self.active_sessions[session_id]
                return {
                    "success": True,
                    "session_id": session_id,
                    "history": [
                        {
                            "timestamp": session["created_at"].isoformat(),
                            "message_count": session["message_count"],
                            "last_intent": session["last_intent"]
                        }
                    ]
                }
            else:
                # Return all sessions for user
                user_sessions = [
                    {
                        "session_id": sid,
                        "created_at": session["created_at"].isoformat(),
                        "message_count": session["message_count"],
                        "last_intent": session["last_intent"]
                    }
                    for sid, session in self.active_sessions.items()
                    if session["user_id"] == user_id
                ]
                
                return {
                    "success": True,
                    "user_id": user_id,
                    "total_sessions": len(user_sessions),
                    "sessions": user_sessions[:limit]
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get chat history: {str(e)}"
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
    
    async def clear_session(self, session_id: str) -> Dict[str, Any]:
        """Clear a chat session"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            return {"success": True, "message": "Session cleared"}
        else:
            return {"success": False, "error": "Session not found"}
    
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
