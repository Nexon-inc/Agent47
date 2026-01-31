from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload

from ..models import JoeMarketTrend, JoeCompetitorAnalysis, JoeSentimentAnalysis, JoeKeywordResearch
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
from core.event_bus.kafka_manager import EventBus
from core.cache.redis_manager import RedisManager

# Import ALL Joe services
from .accessibility_service import AccessibilityService
from .ai_assisted_hypothesis_testing_service import AIAssistedHypothesisTestingService
from .automated_competitor_ad_tracking_service import AutomatedCompetitorAdTrackingService
from .collaborative_workflows_service import CollaborativeWorkflowsService
from .competitor_ad_tracking_service import CompetitorAdTrackingService
from .competitor_analysis_service import CompetitorAnalysisService
from .competitor_benchmarking_service import CompetitorBenchmarkingService
from .compliance_checker_service import ComplianceCheckerService
from .consumer_behavior_service import ConsumerBehaviorService
from .cross_platform_data_integration_service import CrossPlatformDataIntegrationService
from .cross_platform_integration_service import CrossPlatformIntegrationService
from .custom_data_source_service import CustomDataSourceService
from .custom_research_service import CustomResearchService
from .customer_persona_service import CustomerPersonaService
from .data_export_service import DataExportService
from .data_scraping_service import DataScrapingService
from .data_visualization_service import DataVisualizationService
from .ethical_guidelines_service import EthicalGuidelinesService
from .geo_specific_service import GeoSpecificService
from .geo_specific_research_service import GeoSpecificResearchService
from .historical_analysis_service import HistoricalAnalysisService
from .hypothesis_testing_service import HypothesisTestingService
from .industry_report_service import IndustryReportService
from .keyword_research_service import KeywordResearchService
from .market_intelligence_service import MarketIntelligenceService
from .market_opportunity_service import MarketOpportunityService
from .market_opportunity_scoring_service import MarketOpportunityScoringService
from .market_trend_analysis_service import MarketTrendAnalysisService
from .mobile_dashboard_service import MobileDashboardService
from .multi_language_service import MultiLanguageService
from .multi_language_research_service import MultiLanguageResearchService
from .news_monitoring_service import NewsMonitoringService
from .niche_market_service import NicheMarketService
from .onboarding_wizard_service import OnboardingWizardService
from .patent_tracking_service import PatentTrackingService
from .research_automation_service import ResearchAutomationService
from .research_automation_scheduler_service import ResearchAutomationSchedulerService
from .research_ideation_service import ResearchIdeationService
from .research_performance_analytics_service import ResearchPerformanceAnalyticsService
from .research_summarizer_service import ResearchSummarizerService
from .sentiment_tracking_service import SentimentTrackingService
from .social_media_listening_service import SocialMediaListeningService
from .social_proof_analyzer_service import SocialProofAnalyzerService
from .survey_creation_service import SurveyCreationService
from .trend_alerts_service import TrendAlertsService
from .trend_forecasting_service import TrendForecastingService
from .voice_queries_service import VoiceQueriesService
from .voice_research_service import VoiceResearchService
from core.services.media_service import MediaService
import logging

logger = logging.getLogger(__name__)

# Import Joe's actual services
from .market_trend_analysis_service import MarketTrendAnalysisService
from .competitor_analysis_service import CompetitorAnalysisService
from .sentiment_tracking_service import SentimentTrackingService
from .keyword_research_service import KeywordResearchService
from .consumer_behavior_service import ConsumerBehaviorService
from .industry_report_service import IndustryReportService
from .data_visualization_service import DataVisualizationService
from .trend_forecasting_service import TrendForecastingService
from .research_automation_service import ResearchAutomationService
from .market_intelligence_service import MarketIntelligenceService


class JoeChatService:
    """Interactive chat service for Joe that provides comprehensive research assistance"""
    
    def __init__(self):
        self.ai_service_manager: Optional[AIServiceManager] = None
        
        # Initialize ALL Joe services
        # Note: Services requiring db, event_bus, redis will be initialized when needed
        # For now, we'll initialize them as None and create them when needed
        self.accessibility = None
        self.ai_assisted_hypothesis_testing = None
        self.automated_competitor_ad_tracking = None
        self.collaborative_workflows = None
        self.competitor_ad_tracking = None
        self.competitor_analysis = None
        self.competitor_benchmarking = None
        self.compliance_checker = None
        self.consumer_behavior = None
        self.cross_platform_data_integration = None
        self.cross_platform_integration = None
        self.custom_data_source = None
        self.custom_research = None
        self.customer_persona = None
        self.data_export = None
        self.data_scraping = None
        self.data_visualization = None
        self.ethical_guidelines = None
        self.geo_specific = None
        self.geo_specific_research = None
        self.historical_analysis = None
        self.hypothesis_testing = None
        self.industry_report = None
        self.keyword_research = None
        self.market_intelligence = None
        self.market_opportunity = None
        self.market_opportunity_scoring = None
        self.market_trend_analysis = None
        self.mobile_dashboard = None
        self.multi_language = None
        self.multi_language_research = None
        self.news_monitoring = None
        self.niche_market = None
        self.onboarding_wizard = None
        self.patent_tracking = None
        self.research_automation = None
        self.research_automation_scheduler = None
        self.research_ideation = None
        self.research_performance_analytics = None
        self.research_summarizer = None
        self.sentiment_tracking = None
        self.social_media_listening = None
        self.social_proof_analyzer = None
        self.survey_creation = None
        self.trend_alerts = None
        self.trend_forecasting = None
        self.voice_queries = None
        self.voice_research = None
        self.media = MediaService()  # Image generation service
        
        # Chat session management
        self.active_sessions = {}
        
        # TODO management
        self.todos = {}
        
        # Common user intents and responses for research
        self.intent_responses = {
            "greeting": [
                "Hello! 👋 I'm Joe, your AI-powered research assistant. I'm here to help you gather market intelligence, analyze trends, and make data-driven decisions. 📊",
                "Hi there! ✨ I'm Joe, ready to help you research markets, competitors, and opportunities for your business. 🔍",
                "Welcome! 🌟 I'm Joe, your dedicated research partner. Let's uncover insights that drive your business forward! 🚀"
            ],
            "help": [
                "I can help you with: market research 🔍, competitor analysis 🏢, trend forecasting 📈, sentiment analysis 💬, keyword research 🔑, and much more. What would you like to explore?",
                "I'm here to assist with: gathering market intelligence 💡, analyzing industry trends 📊, tracking competitors 🕵️‍♂️, and finding business opportunities 🚀. What do you need to research?",
                "I offer comprehensive research support including: market analysis 📋, competitive intelligence 🔍, trend prediction 📉, and strategic insights ✨. How can I help you today?"
            ],
            "market_research": [
                "I'll help you conduct comprehensive market research to understand your industry, target audience, and market opportunities. 📋",
                "Let me analyze market data, industry reports, and consumer trends to provide you with actionable market insights. 💡",
                "I'll examine market size, growth rates, and key players to help you make informed business decisions. 📊"
            ],
            "competitor_analysis": [
                "I'll analyze your competitors' strategies, strengths, weaknesses, and market positioning to help you stay competitive. 🏢",
                "Let me research your competitors' products, pricing, marketing, and business models to identify opportunities. 🔍",
                "I'll track competitor activities and provide insights to help you differentiate and win in the market. 🏆"
            ],
            "trend_analysis": [
                "I'll identify and analyze emerging trends in your industry to help you stay ahead of the curve. 📈",
                "Let me track market trends, consumer behavior, and technological developments that could impact your business. 📉",
                "I'll forecast future trends and help you prepare for upcoming changes in your market. 🚀"
            ],
            "sentiment_analysis": [
                "I'll analyze customer sentiment, reviews, and social media mentions to understand how people feel about your brand. 💬",
                "Let me track brand sentiment across different channels and identify areas for improvement. ✨",
                "I'll monitor public opinion and help you manage your brand reputation effectively. 🛡️"
            ],
            "keyword_research": [
                "I'll help you find the right keywords to improve your SEO and reach your target audience. 🔑",
                "Let me research high-value keywords, search volumes, and competition levels for your content strategy. 📈",
                "I'll identify keyword opportunities and help you optimize your content for better search visibility. ✅"
            ],
            "data_analysis": [
                "I'll help you analyze research data, identify patterns, and extract meaningful insights for your business. 📊",
                "Let me process your data and create visualizations that make complex information easy to understand. 📉",
                "I'll turn raw data into actionable intelligence that drives your decision-making process. 💡"
            ],
            "general": [
                "I'm here to help you with all your research needs. What information are you looking for? 🤔",
                "Let's dive deep into research and find the insights you need. What's your research goal? ✨",
                "I can help with any research task. What do you need to know? 🚀"
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
        
        # Research-specific intent detection
        if any(word in message_lower for word in ["market", "industry", "sector", "market size"]):
            return "market_research"
        elif any(word in message_lower for word in ["competitor", "competition", "rival", "opponent"]):
            return "competitor_analysis"
        elif any(word in message_lower for word in ["trend", "forecast", "prediction", "future"]):
            return "trend_analysis"
        elif any(word in message_lower for word in ["sentiment", "opinion", "review", "feedback"]):
            return "sentiment_analysis"
        elif any(word in message_lower for word in ["keyword", "seo", "search", "ranking"]):
            return "keyword_research"
        elif any(word in message_lower for word in ["data", "analysis", "insight", "pattern"]):
            return "data_analysis"
        elif any(word in message_lower for word in ["image", "photo", "visual", "picture", "generate image", "create image"]):
            return "media_generation"
        elif any(word in message_lower for word in ["hello", "hi", "hey", "greetings"]):
            return "greeting"
        elif any(word in message_lower for word in ["help", "assist", "support", "what can you do"]):
            return "help"
        else:
            return "general"
    
    async def _break_down_request_into_tasks(self, message: str, user_id: int = None, db: AsyncSession = None) -> Dict[str, Any]:
        """Break down user request into structured tasks for research and analytics
        
        Domain-specific for Joe (Research):
        - Analytics Tools: Google Analytics, Mixpanel, Amplitude
        - Research Types: Market research, Competitor analysis, Trend forecasting, Sentiment analysis
        - Task types: Research reports, Data analysis, Competitor comparisons, Trend reports
        """
        import re
        
        tasks = {
            "total_tasks": 1,
            "task_type": "general",
            "requirements": [],
            "completion_criteria": [],
            "domain": "research",
            "analytics_tools": [],
            "research_types": []
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
        
        # Get analytics integrations specifically
        analytics_integrations = get_integrations_by_type("analytics")
        analytics_tools_static = {k: v["display_name"] for k, v in analytics_integrations.items()}
        
        # Detect ALL platforms mentioned (for data sources)
        detected_platforms = detect_platforms_in_message(message, all_platforms)
        
        # Filter detected platforms to only include user's connected platforms (if any)
        if user_connected_platforms and detected_platforms:
            detected_platforms = [p for p in detected_platforms if any(cp.lower() in p.lower() or p.lower() in cp.lower() for cp in user_connected_platforms)]
        
        # Detect ALL integrations mentioned (analytics, research, etc.)
        detected_integrations = detect_integrations_in_message(message, all_integrations)
        detected_tools = [integ["display_name"] for integ in detected_integrations]
        
        # Filter detected integrations to only include user's connected integrations (if any)
        if user_connected_integrations and detected_tools:
            detected_tools = [t for t in detected_tools if any(ci.lower() in t.lower() or t.lower() in ci.lower() for ci in user_connected_integrations)]
        
        # Add analytics tools if mentioned
        for tool_key, tool_name in analytics_tools_static.items():
            if tool_key in message_lower or tool_name.lower() in message_lower:
                if tool_name not in detected_tools:
                    detected_tools.append(tool_name)
        
        # Research Types Detection
        research_types = {
            "market": "Market Research",
            "competitor": "Competitor Analysis",
            "trend": "Trend Analysis",
            "sentiment": "Sentiment Analysis",
            "keyword": "Keyword Research",
            "data": "Data Analysis"
        }
        
        # Detect research types mentioned
        detected_research = []
        for research_key, research_name in research_types.items():
            if research_key in message_lower:
                detected_research.append(research_name)
        
        # Detect research report requests
        if "report" in message_lower or "analysis" in message_lower:
            section_matches = re.findall(r'(\d+)[\\s-]?(?:section|part|chapter)', message_lower)
            if section_matches:
                tasks["total_tasks"] = int(section_matches[0])
                tasks["task_type"] = "research_report"
                tasks["analytics_tools"] = detected_tools if detected_tools else ["All analytics tools"]
                tasks["research_types"] = detected_research if detected_research else ["Comprehensive Research"]
                tasks["requirements"] = [
                    f"Section {i+1}: Complete research section with data analysis, insights, visualizations, and actionable recommendations" 
                    for i in range(tasks["total_tasks"])
                ]
                tasks["completion_criteria"] = [
                    f"All {tasks['total_tasks']} sections must be provided",
                    "Each section must include: data analysis, insights, visualizations, and actionable recommendations",
                    f"Analytics tools: {', '.join(tasks['analytics_tools'])}"
                ]
        
        # Detect competitor analysis requests
        elif "competitor" in message_lower:
            competitor_matches = re.findall(r'(\d+)[\\s-]?(?:competitor|company|brand)', message_lower)
            if competitor_matches:
                tasks["total_tasks"] = int(competitor_matches[0])
                tasks["task_type"] = "competitor_analysis"
                tasks["requirements"] = [
                    f"Competitor {i+1}: Complete competitor analysis with strengths, weaknesses, strategies, market position, and recommendations" 
                    for i in range(tasks["total_tasks"])
                ]
                tasks["completion_criteria"] = [
                    f"All {tasks['total_tasks']} competitors must be analyzed",
                    "Each analysis must include: strengths, weaknesses, strategies, market position, and recommendations"
                ]
        
        # Detect trend analysis requests
        elif "trend" in message_lower:
            trend_matches = re.findall(r'(\d+)[\\s-]?(?:trend|pattern|forecast)', message_lower)
            if trend_matches:
                tasks["total_tasks"] = int(trend_matches[0])
                tasks["task_type"] = "trend_analysis"
                tasks["requirements"] = [
                    f"Trend {i+1}: Complete trend analysis with description, data points, timeline, impact assessment, and action items" 
                    for i in range(tasks["total_tasks"])
                ]
                tasks["completion_criteria"] = [
                    f"All {tasks['total_tasks']} trends must be analyzed",
                    "Each trend must include: description, data points, timeline, impact assessment, and action items"
                ]
        
        # Detect research methodology steps
        elif "methodology" in message_lower or "process" in message_lower or "steps" in message_lower:
            step_matches = re.findall(r'(\d+)[\\s-]?(?:step|stage|phase)', message_lower)
            if step_matches:
                tasks["total_tasks"] = int(step_matches[0])
                tasks["task_type"] = "research_methodology"
                tasks["analytics_tools"] = detected_tools if detected_tools else ["All analytics tools"]
                tasks["platforms"] = detected_platforms if detected_platforms else []
                tasks["requirements"] = [
                    f"Step {i+1}: Research methodology step with data sources, analysis methods, tools, platform integrations, and output format" 
                    for i in range(tasks["total_tasks"])
                ]
                tasks["completion_criteria"] = [
                    f"All {tasks['total_tasks']} methodology steps must be provided",
                    "Each step must include: data sources, analysis methods, tools, platform integrations, and output format",
                    f"Analytics tools: {', '.join(tasks['analytics_tools'])}",
                    f"Available data platforms: {', '.join(tasks['platforms']) if tasks['platforms'] else 'All platforms (Google Analytics, social media, business platforms, etc.)'}"
                ]
        
        return tasks
    
    def _get_fallback_response(self, intent: str) -> str:
        """Get fallback response for detected intent"""
        responses = {
            "greeting": [
                "Hello! 👋 I'm Joe, your AI research assistant. How can I help you gather insights today?",
                "Hi there! ✨ I'm Joe, ready to help you research and analyze. What's your research goal?",
                "Welcome! 🌟 I'm Joe, your research partner. Let's uncover valuable insights together! 🚀"
            ],
            "help": [
                "I can help you with market research 🔍, competitor analysis 🏢, trend forecasting 📈, and more. What do you need to research?",
                "I'm here to assist with all your research needs. What information are you looking for? 🤔",
                "I offer comprehensive research support. How can I help you gather intelligence today? ✨"
            ],
            "market_research": [
                "I'll help you research your market 📋. What industry or sector are you interested in?",
                "Let me analyze market data for you 📊. What specific market information do you need?",
                "I'll conduct market research 🔍. What's your target market or industry?"
            ],
            "competitor_analysis": [
                "I'll help you analyze your competitors 🏢. Who are your main competitors?",
                "Let me research your competition 🕵️‍♂️. What companies should I analyze?",
                "I'll conduct competitor analysis 🔍. What industry are you in?"
            ],
            "trend_analysis": [
                "I'll help you identify trends 📈. What industry or topic are you interested in?",
                "Let me analyze trends for you 📉. What trends are you looking to track?",
                "I'll forecast trends 🚀. What market or industry should I focus on?"
            ],
            "sentiment_analysis": [
                "I'll help you analyze sentiment 💬. What brand or topic should I analyze?",
                "Let me track sentiment for you ✨. What are you looking to monitor?",
                "I'll conduct sentiment analysis 🛡️. What brand or product should I research?"
            ],
            "keyword_research": [
                "I'll help you with keyword research 🔑. What's your business or content topic?",
                "Let me find keywords for you 📈. What industry or niche are you in?",
                "I'll research keywords ✅. What content or products are you promoting?"
            ],
            "data_analysis": [
                "I'll help you analyze data 📊. What data do you have or need to analyze?",
                "Let me process your data 📉. What insights are you looking for?",
                "I'll turn your data into insights 💡. What information do you have?"
            ],
            "general": [
                "I'm here to help you with all your research needs. What information are you looking for? 🤔",
                "Let's research together ✨. What information are you looking for?",
                "I can help with any research task. What's your goal? 🚀"
            ]
        }
        
        import random
        return random.choice(responses.get(intent, responses["general"]))
    
    def _generate_thinking_steps(self, intent: str, message: str, user_id: int, db: AsyncSession = None) -> List[str]:
        """Generate thinking steps based on intent and message context"""
        steps = []
        
        if intent == "market_research":
            steps = [
                "Gathering market data and insights...",
                "Analyzing industry trends and patterns...",
                "Reviewing competitor information...",
                "Preparing comprehensive research report..."
            ]
        elif intent == "competitor_analysis":
            steps = [
                "Identifying key competitors...",
                "Analyzing competitor strategies...",
                "Comparing market positioning...",
                "Preparing competitive analysis..."
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

**RESEARCH CONTEXT:**
- Data Sources: {platforms_count} ({', '.join([p.get('display_name', '') for p in user_resources.get('platforms', [])[:5]])})
- Connected Tools: {integrations_count} ({', '.join([i.get('integration_name', '') for i in user_resources.get('integrations', [])[:5]])})

**PLATFORM NAVIGATION:**
- Analytics Dashboard: Dashboard -> Analytics
- Market Reports: Dashboard -> Reports
"""
                except Exception as e:
                    logger.warning(f"Could not fetch user resources: {e}")

                # Get agent's custom configuration/tweaks
                custom_instructions_text = ""
                try:
                    if db and user_id:
                        from core.utils.agent_user_data import get_agent_configuration_for_user
                        agent_config = await get_agent_configuration_for_user(user_id, "joe", db)
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
                        "content": f"""You are Joe, an AI-powered research and analytics assistant specializing in comprehensive market intelligence and data analysis.
{user_resources_summary}
{custom_instructions_text}

**Response Guidelines:**
- Be a proactive, analytical collaborator. Focus on providing data-driven insights.
- Use the chat history to maintain context.
- Use emojis naturally (🔍, 📊, 📈, 💡, etc.) to keep the tone modern and engaging.
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
                        ai_response = f"I've generated an image for your research! 🎨\n\nYou can use this image in your reports, presentations, or research materials."
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