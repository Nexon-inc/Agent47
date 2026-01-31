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


class JoeChatService:
    """Interactive chat service for Joe that provides comprehensive research assistance"""
    
    def __init__(self):
        self.ai_service_manager: Optional[AIServiceManager] = None
        
        # Initialize ALL Joe services
        self.accessibility = AccessibilityService()
        self.ai_assisted_hypothesis = AIAssistedHypothesisTestingService()
        self.automated_ad_tracking = AutomatedCompetitorAdTrackingService()
        self.collaborative_workflows = CollaborativeWorkflowsService()
        self.competitor_ad_tracking = CompetitorAdTrackingService()
        self.competitor_analysis = CompetitorAnalysisService()
        self.competitor_benchmarking = CompetitorBenchmarkingService()
        self.compliance_checker = ComplianceCheckerService()
        self.consumer_behavior = ConsumerBehaviorService()
        self.cross_platform_data = CrossPlatformDataIntegrationService()
        self.cross_platform_integration = CrossPlatformIntegrationService()
        self.custom_data_source = CustomDataSourceService()
        self.custom_research = CustomResearchService()
        self.customer_persona = CustomerPersonaService()
        self.data_export = DataExportService()
        self.data_scraping = DataScrapingService()
        self.data_visualization = DataVisualizationService()
        self.ethical_guidelines = EthicalGuidelinesService()
        self.geo_specific = GeoSpecificService()
        self.geo_specific_research = GeoSpecificResearchService()
        self.historical_analysis = HistoricalAnalysisService()
        self.hypothesis_testing = HypothesisTestingService()
        self.industry_report = IndustryReportService()
        self.keyword_research = KeywordResearchService()
        self.market_intelligence = MarketIntelligenceService()
        self.market_opportunity = MarketOpportunityService()
        self.market_opportunity_scoring = MarketOpportunityScoringService()
        self.market_trend_analysis = MarketTrendAnalysisService()
        self.mobile_dashboard = MobileDashboardService()
        self.multi_language = MultiLanguageService()
        self.multi_language_research = MultiLanguageResearchService()
        self.news_monitoring = NewsMonitoringService()
        self.niche_market = NicheMarketService()
        self.onboarding_wizard = OnboardingWizardService()
        self.patent_tracking = PatentTrackingService()
        self.research_automation = ResearchAutomationService()
        self.research_automation_scheduler = ResearchAutomationSchedulerService()
        self.research_ideation = ResearchIdeationService()
        self.research_performance = ResearchPerformanceAnalyticsService()
        self.research_summarizer = ResearchSummarizerService()
        self.sentiment_tracking = SentimentTrackingService()
        self.social_media_listening = SocialMediaListeningService()
        self.social_proof = SocialProofAnalyzerService()
        self.survey_creation = SurveyCreationService()
        self.trend_alerts = TrendAlertsService()
        self.trend_forecasting = TrendForecastingService()
        self.voice_queries = VoiceQueriesService()
        self.voice_research = VoiceResearchService()
        
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
            # ... (Keep existing responses)
        }
    
    # ... (Keep existing methods: _get_ai_service_manager, _detect_intent, _break_down_request_into_tasks, _get_fallback_response) ...

    def _generate_thinking_steps(self, intent: str, message: str, user_id: int, db: AsyncSession = None) -> List[str]:
        """Generate thinking steps based on research intent"""
        steps = []
        
        if intent == "market_research":
            steps = [
                "Scanning global market databases...",
                "Aggregating industry reports...",
                "Identifying key growth drivers...",
                "Synthesizing market insights..."
            ]
        elif intent == "competitor_analysis":
            steps = [
                "Identifying direct/indirect competitors...",
                "Analyzing capability gaps...",
                "Scraping public pricing & features...",
                "Formulating competitive advantages..."
            ]
        elif intent == "trend_analysis":
            steps = [
                "Analyzing historical data patterns...",
                "Projecting future growth trajectories...",
                "Detecting emerging viral signals...",
                "Generating trend forecast..."
            ]
        elif intent == "keyword_research":
             steps = [
                "Analyzing search volume metrics...",
                "Evaluating keyword difficulty...",
                "Mapping user intent clusters...",
                "Optimizing SEO strategy..."
            ]
        else:
            steps = [
                "Analyzing research parameters...",
                "Checking data sources...",
                "Validating hypotheses...",
                "Compiling research findings..."
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
                    
                    user_resources_summary = f"""
**USER CONTEXT:**
- Name: {profile.get('full_name', 'User')}
- Company: {profile.get('company', 'Not specified')}
- Industry: {profile.get('industry', 'Not specified')}
- Role: {profile.get('role', 'Not specified')} (Consider this for research depth)
- Business Goal: {profile.get('primary_goals', ['Market Intelligence'])}
- Connected Platforms: {summary.get('total_platforms', 0)}
- Connected Tools: {summary.get('total_integrations', 0)}
"""
            except Exception as e:
                logger.warning(f"Failed to load user context: {e}")

            messages = [
                {
                    "role": "system",
                    "content": f"""You are **Joe**, an elite **AI Research & Market Intelligence Analyst**.
{user_resources_summary}

**CORE OBJECTIVE:**
Provide deep, data-driven research, competitor analysis, and strategic market insights. You are NOT a generic assistant; you are a RESEARCH EXPERT.

**INTELLIGENCE PROTOCOL (STRICTLY FOLLOW THIS):**
1. **Data-Driven**: Always look for data points, trends, and evidence to back your claims.
2. **Context Aware**: Tailor insights to the user's specific **Industry ({profile.get('industry', 'General')})** and **Business Goals**.
3. **No Canned Responses**: synthesize a response based on the specific research query.
4. **Tool Usage**: You have access to 50+ specialized services: Competitor Analysis, Trend Forecasting, Sentiment Tracking, Patent Search, etc. USE THEM.

**CAPABILITIES:**
- **Market Research**: Size, growth, dynamics.
- **Competitor Analysis**: SWOT, feature gaps, ad tracking.
- **Trend Forecasting**: Predicting future market shifts.
- **Sentiment Analysis**: Understanding consumer voice.
- **Hypothesis Testing**: Validating business assumptions.

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