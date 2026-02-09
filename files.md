Agent47 Chat Source Code Reference
This document contains the complete source code for the 
chat_service.py
 and chat_router.py files for all seven agents in the Agent47 project.

1. Aria (Social Media Manager)
Service: 
backend/agents/aria/app/services/aria_chat_service.py

from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload
import logging

from ..models import (
    AriaSocialAccount, AriaAccountGroup, AriaBrandProfile, AriaCampaign, 
    AriaScheduledPost, AriaPublishedPost, AriaEngagementEvent, AriaAnalyticsSnapshot,
    PlatformEnum, AriaPostStatus, ApprovalStatus
)
from ..database import get_db
from core.ai import get_ai_service_manager, AIServiceManager
from core.utils.platform_integration_loader import (
    get_all_platforms_static, 
    get_all_integrations_static,
    detect_platforms_in_message,
    detect_integrations_in_message,
    get_platforms_by_type,
    get_platforms_by_type,
    get_integrations_by_type
)
from core.utils.agent_user_data import get_all_user_resources_for_agent

logger = logging.getLogger(__name__)

# Import ALL Aria services with correct class names
from .ab_testing_service import ABTestingService
from .accessibility_service import AccessibilityService
from .account_analysis_service import AccountAnalysisService
from .ads_service import AdsService
from .advanced_analytics_service import AdvancedAnalyticsService
from .analytics_service import AnalyticsService
from .approval_service import ApprovalService
from .brand_service import BrandService
from .content_service import ContentService
from .content_remix_service import ContentRemixService
from .engagement_service import EngagementService
from .engagement_booster_service import EngagementBoosterService
from .geo_campaign_service import GeoCampaignService
from .media_service import MediaService
from .oauth_service import OAuthService
from .publisher_service import PublisherService
from .scheduling_service import SchedulingService
from .speech_service import SpeechService
from .tier_rbac_service import TierRBAC
from .trend_service import TrendService
from .trend_alerts_service import TrendAlertsService
from .voice_posts_service import VoicePostsService
from .automation_service import AutomationService



class AriaChatService:
    """Interactive chat service for Aria that provides comprehensive social media management assistance"""
    
    def __init__(self):
        self.ai_service_manager: Optional[AIServiceManager] = None
        
        # Initialize ALL Aria services
        self.ab_testing = ABTestingService()
        self.accessibility = AccessibilityService()
        self.account_analysis = AccountAnalysisService()
        self.ads = AdsService()
        self.advanced_analytics = AdvancedAnalyticsService()
        self.analytics = AnalyticsService()
        self.approval = ApprovalService()
        self.brand = BrandService()
        self.content = ContentService()
        self.content_remix = ContentRemixService()
        self.engagement = EngagementService()
        self.engagement_booster = EngagementBoosterService()
        self.geo_campaign = GeoCampaignService()
        self.media = MediaService()
        self.oauth = OAuthService()
        self.publisher = PublisherService()
        self.scheduling = SchedulingService()
        self.speech = SpeechService()
        self.tier_rbac = TierRBAC()
        self.trend = TrendService()
        self.trend_alerts = TrendAlertsService()
        self.voice_posts = VoicePostsService()
        self.automation = AutomationService()
        
        # Chat session management
        self.active_sessions = {}
        
        # TODO management
        self.todos = {}
        
        # Common user intents and responses
        self.intent_responses = {
            "greeting": [
                "Hello! 👋 I'm Aria, your AI-powered social media management assistant. I'm here to help you manage your social media presence effectively. 🚀",
                "Hi there! ✨ I'm Aria, ready to help you optimize your social media strategy and grow your brand online. 📈",
                "Welcome! 🌟 I'm Aria, your dedicated social media management partner. Let's make your social media presence shine! ✨"
            ],
            "help": [
                "I can help you with: account analysis 📊, content creation ✍️, scheduling 📅, analytics 📈, trend monitoring 🔥, ad management 📢, and much more. What would you like to work on?",
                "I'm here to assist with: managing multiple social accounts 📱, creating engaging content ✨, scheduling posts 🗓️, analyzing performance 📊, and optimizing your strategy. What do you need help with?",
                "I offer comprehensive social media management including: content creation 🎨, scheduling ⏰, analytics 📉, trend monitoring 🚀, competitor analysis 🕵️‍♀️, and strategic planning. How can I assist you today?"
            ],
            "account_management": [
                "I'll analyze your connected social media accounts and provide detailed insights and recommendations for improvement. 🕵️‍♂️",
                "Let me scan your accounts to understand your current performance and identify opportunities for growth. 🚀",
                "I'll examine your social media presence across all platforms and give you actionable insights to optimize your strategy. 📊"
            ],
            "content_creation": [
                "I can help you create engaging content with AI-generated captions ✍️, hashtags #️⃣, and even generate images 🖼️. What type of content would you like to create?",
                "Let's create some amazing content! 🎨 I can generate captions, suggest hashtags, create images, and help you adapt content for different platforms.",
                "I'm here to help with content creation! ✨ I can generate captions, hashtags, images, and help you repurpose content across platforms."
            ],
            "scheduling": [
                "I can help you schedule posts across all your connected platforms with optimal timing for maximum engagement. ⏰",
                "Let's get your content scheduled! 🗓️ I'll analyze the best posting times for each platform and schedule your posts accordingly.",
                "I'll help you schedule your content at the perfect times across all platforms to maximize reach and engagement. 🚀"
            ],
            "analytics": [
                "I'll provide comprehensive analytics on your social media performance, including engagement rates, audience insights, and growth trends. 📉",
                "Let me analyze your performance data and show you detailed insights about your audience, content performance, and growth opportunities. 📊",
                "I'll give you deep insights into your social media performance, helping you understand what's working and where to improve. 💡"
            ],
            "trends": [
                "I'll monitor trending topics, hashtags, and conversations relevant to your brand and suggest content ideas. 🔥",
                "Let me keep you updated on the latest trends and help you create timely, relevant content that resonates with your audience. 📈",
                "I'll track trending topics and conversations to help you stay current and create content that's relevant and engaging. 🚀"
            ],
            "ads": [
                "I can help you create and manage advertising campaigns on Instagram, LinkedIn, and other platforms to boost your reach. 💰",
                "Let's set up effective ad campaigns! 📢 I'll help you create targeted ads, set budgets, and monitor performance across platforms.",
                "I'll help you create strategic ad campaigns that target your ideal audience and drive results for your business. 💸"
            ],
            "geo_campaigns": [
                "I can help you create location-specific campaigns targeting specific regions, including African countries and cities like Kenya, Nairobi, and many more. 🌍",
                "Let's create geo-targeted campaigns! 📍 I can help you design campaigns for specific regions, including popular African locations and global markets.",
                "I'll help you create campaigns that resonate with specific geographic audiences, from local markets to international regions. 🌎"
            ]
        }
    
    async def _get_ai_service_manager(self):
        """Get AI service manager"""
        if not self.ai_service_manager:
            self.ai_service_manager = await get_ai_service_manager()
        return self.ai_service_manager
    
    def _detect_intent_simple(self, message: str) -> str:
        """Simple keyword-based intent detection"""
        message_lower = message.lower()
        
        # Simple keyword-based intent detection
        if any(word in message_lower for word in ["hello", "hi", "hey", "good morning", "good afternoon"]):
            return "greeting"
        elif any(word in message_lower for word in ["help", "what can you do", "capabilities", "features"]):
            return "help"
        elif any(word in message_lower for word in ["account", "accounts", "analyze", "analysis", "scan", "health"]):
            return "account_management"
        elif any(word in message_lower for word in ["create", "content", "post", "caption", "hashtag", "generate"]):
            return "content_creation"
        elif any(word in message_lower for word in ["remix", "adapt", "reformat", "repurpose", "cross-platform"]):
            return "content_remix"
        elif any(word in message_lower for word in ["image", "photo", "visual", "picture", "generate image"]):
            return "media_generation"
        elif any(word in message_lower for word in ["schedule", "timing", "when to post", "posting time", "calendar"]):
            return "scheduling"
        elif any(word in message_lower for word in ["analytics", "performance", "stats", "metrics", "insights", "engagement"]):
            return "analytics"
        elif any(word in message_lower for word in ["trend", "trending", "what's hot", "viral", "monitor"]):
            return "trends"
        elif any(word in message_lower for word in ["ad", "ads", "advertising", "campaign", "promote", "boost"]):
            return "ads"
        elif any(word in message_lower for word in ["location", "region", "country", "city", "africa", "kenya", "nairobi", "geo"]):
            return "geo_campaigns"
        elif any(word in message_lower for word in ["engagement", "boost", "interaction", "poll", "question", "cta"]):
            return "engagement"
        elif any(word in message_lower for word in ["reply", "auto-reply", "respond", "comment", "message"]):
            return "auto_reply"
        elif any(word in message_lower for word in ["brand", "voice", "profile", "identity"]):
            return "brand"
        elif any(word in message_lower for word in ["publish", "post now", "share", "send"]):
            return "publishing"
        elif any(word in message_lower for word in ["connect", "link", "oauth", "authorize", "login"]):
            return "oauth"
        elif any(word in message_lower for word in ["approve", "approval", "review", "approval workflow"]):
            return "approval"
        elif any(word in message_lower for word in ["test", "ab test", "variant", "a/b"]):
            return "ab_testing"
        elif any(word in message_lower for word in ["voice", "audio", "record", "speak", "transcribe"]):
            return "voice_post"
        elif any(word in message_lower for word in ["accessibility", "alt text", "caption", "accessible"]):
            return "accessibility"
        elif any(word in message_lower for word in ["advanced analytics", "sentiment", "heatmap", "deep insights"]):
            return "advanced_analytics"
        elif any(word in message_lower for word in ["automate", "automation", "auto", "schedule for", "for the next", "for next", "recurring"]):
            return "automation"
        else:
            return "general"
    
    async def _break_down_request_into_tasks(self, message: str, user_id: int = None, db: AsyncSession = None) -> Dict[str, Any]:
        """Break down user request into structured tasks for social media management
        
        Domain-specific for Aria (Social Media):
        - Social platforms: Instagram, Twitter, LinkedIn, Facebook, TikTok, YouTube, Pinterest, Snapchat, Reddit, Discord
        - Content types: Posts, Stories, Reels, Videos, Carousels, Polls, Threads
        - Tools: Buffer, Mailchimp, HubSpot, Salesforce, Zapier, Slack, Trello
        - Task types: Calendar (days), Multi-platform, Content formats, Campaigns
        """
        import re
        
        tasks = {
            "total_tasks": 1,
            "task_type": "general",
            "requirements": [],
            "completion_criteria": [],
            "domain": "social_media",
            "platforms": [],
            "content_types": []
        }
        
        message_lower = message.lower()
        
        # Get user's actual connected platforms and integrations (if db available)
        user_connected_platforms = []
        user_connected_integrations = []
        user_website = ""
        
        # Try to get user's actual connected resources
        try:
            if db:
                user_resources = await get_all_user_resources_for_agent(user_id, db)
                user_connected_platforms = [p.get("platform_name") for p in user_resources.get("platforms", []) if p.get("status") in ["connected", "active"]]
                user_connected_integrations = [i.get("integration_name") for i in user_resources.get("integrations", []) if i.get("status") == "connected"]
                user_website = user_resources.get("profile", {}).get("website_url", "")
        except Exception as e:
            logger.warning(f"Could not fetch user resources: {e}")
        
        # Dynamically load ALL available platforms (social media, business, content, analytics)
        all_platforms = get_all_platforms_static()
        all_integrations = get_all_integrations_static()
        
        # Get social media platforms specifically, but also allow any platform
        social_platforms = get_platforms_by_type("social_media")
        
        # Detect ALL platforms mentioned in message (not just social media)
        detected_platforms = detect_platforms_in_message(message, all_platforms)
        
        # If no platforms detected, check for social media platforms specifically
        if not detected_platforms:
            detected_platforms = detect_platforms_in_message(message, social_platforms)
        
        # Filter detected platforms to only include user's connected platforms (if any)
        if user_connected_platforms and detected_platforms:
            detected_platforms = [p for p in detected_platforms if any(cp.lower() in p.lower() or p.lower() in cp.lower() for cp in user_connected_platforms)]
        
        # Detect integrations/tools mentioned
        detected_integrations = detect_integrations_in_message(message, all_integrations)
        detected_tools = [integ["display_name"] for integ in detected_integrations]
        
        # Filter detected integrations to only include user's connected integrations (if any)
        if user_connected_integrations and detected_tools:
            detected_tools = [t for t in detected_tools if any(ci.lower() in t.lower() or t.lower() in ci.lower() for ci in user_connected_integrations)]
        
        # Content Types Detection
        content_types = {
            "post": "Post",
            "posts": "Posts",
            "story": "Story",
            "stories": "Stories",
            "reel": "Reel",
            "reels": "Reels",
            "video": "Video",
            "videos": "Videos",
            "carousel": "Carousel",
            "carousels": "Carousels",
            "poll": "Poll",
            "polls": "Polls",
            "thread": "Thread",
            "threads": "Threads"
        }
        
        # Detect content types mentioned
        detected_content_types = []
        for content_key, content_name in content_types.items():
            if content_key in message_lower:
                detected_content_types.append(content_name)
        
        # Detect calendar/planning requests (social media calendars) - 7, 14, 30, 90 days
        if any(word in message_lower for word in ["day", "week", "month", "calendar", "schedule", "automate"]):
            day_matches = re.findall(r'(\d+)[\s-]?day', message_lower)
            weeks_matches = re.findall(r'(\d+)[\s-]?week', message_lower)
            months_matches = re.findall(r'(\d+)[\s-]?month', message_lower)
            
            num_days = 0
            if day_matches:
                num_days = int(day_matches[0])
            elif weeks_matches:
                num_days = int(weeks_matches[0]) * 7
            elif months_matches:
                num_days = int(months_matches[0]) * 30
            elif " week" in message_lower:
                num_days = 7
            elif " month" in message_lower:
                num_days = 30
                
            # Support requested specific cycles: 7, 14, 30, 90
            if num_days > 0 or any(word in message_lower for word in ["calendar", "schedule", "automate"]):
                tasks["total_tasks"] = num_days if num_days > 0 else 7 # Default to 7
                tasks["task_type"] = "social_calendar"
                tasks["platforms"] = detected_platforms if detected_platforms else ["All connected platforms"]
                tasks["content_types"] = detected_content_types if detected_content_types else ["Posts"]
                tasks["requirements"] = [
                    f"Day {i+1}: Complete social media content plan for day {i+1} including captions, hashtags, posting times, and platform-specific content" 
                    for i in range(tasks["total_tasks"])
                ]
                tasks["completion_criteria"] = [
                    f"All {tasks['total_tasks']} days must be covered with unique content",
                    "Each day must include: captions, hashtags, posting times, and platform-specific adaptations",
                    f"Content must be optimized for: {', '.join(tasks['platforms'])}",
                    f"Content formats to include: {', '.join(tasks['content_types'])}"
                ]
        
        # Detect multi-platform content requests
        elif detected_platforms and len(detected_platforms) > 1:
            tasks["total_tasks"] = len(detected_platforms)
            tasks["task_type"] = "multi_platform_content"
            tasks["platforms"] = detected_platforms
            tasks["content_types"] = detected_content_types if detected_content_types else ["Posts"]
            tasks["requirements"] = [
                f"{platform}: Platform-specific content optimized for {platform} including format, character limits, and best practices" 
                for platform in detected_platforms
            ]
            tasks["completion_criteria"] = [
                f"All {len(detected_platforms)} platforms must be covered",
                "Each platform must have unique, platform-optimized content",
                "Content must respect platform-specific character limits and formats",
                f"Content formats: {', '.join(tasks['content_types'])}"
            ]
        
        # Detect content type requests (multiple formats)
        elif detected_content_types and len(detected_content_types) > 1:
            tasks["total_tasks"] = len(detected_content_types)
            tasks["task_type"] = "multi_format_content"
            tasks["platforms"] = detected_platforms if detected_platforms else ["All platforms"]
            tasks["content_types"] = detected_content_types
            tasks["requirements"] = [
                f"{content_type}: Complete {content_type} content with specifications, best practices, and platform recommendations" 
                for content_type in detected_content_types
            ]
            tasks["completion_criteria"] = [
                f"All {len(detected_content_types)} content formats must be provided",
                "Each format must include specifications, best practices, and platform recommendations",
                "Content must be optimized for the target platforms"
            ]
        
        # Detect campaign requests
        elif "campaign" in message_lower or "strategy" in message_lower:
            campaign_matches = re.findall(r'(\d+)[\s-]?(?:week|month|phase|stage)', message_lower)
            if campaign_matches:
                tasks["total_tasks"] = int(campaign_matches[0])
                tasks["task_type"] = "campaign_plan"
                tasks["platforms"] = detected_platforms if detected_platforms else ["All platforms"]
                tasks["requirements"] = [
                    f"Phase {i+1}: Complete campaign phase with content themes, posting schedule, engagement tactics, and performance metrics" 
                    for i in range(tasks["total_tasks"])
                ]
                tasks["completion_criteria"] = [
                    f"All {tasks['total_tasks']} campaign phases must be detailed",
                    "Each phase must include: content themes, posting schedule, engagement tactics, and KPIs",
                    f"AriaCampaign must cover: {', '.join(tasks['platforms'])}"
                ]
        
        # Detect numbered list requests (post ideas, hashtag sets, etc.)
        elif re.search(r'\d+\s*(?:different|various|multiple|post|idea|hashtag)', message_lower):
            num_matches = re.findall(r'(\d+)\s*(?:different|various|multiple|post|idea|hashtag)', message_lower)
            if num_matches:
                tasks["total_tasks"] = int(num_matches[0])
                tasks["task_type"] = "content_ideas"
                tasks["platforms"] = detected_platforms if detected_platforms else ["All platforms"]
                tasks["requirements"] = [
                    f"Idea {i+1}: Complete content idea with caption, hashtags, posting time, platform recommendations, and engagement strategy" 
                    for i in range(tasks["total_tasks"])
                ]
                tasks["completion_criteria"] = [
                    f"All {tasks['total_tasks']} content ideas must be provided",
                    "Each idea must include: caption, hashtags, posting time, platform recommendations, and engagement strategy",
                    "Ideas must be unique and actionable"
                ]
        
        # Detect sequence/step requests (social media workflows)
        elif "list" in message_lower or "steps" in message_lower or "sequence" in message_lower or "workflow" in message_lower:
            step_matches = re.findall(r'(\d+)[\s-]?(?:step|item|point|stage)', message_lower)
            if step_matches:
                tasks["total_tasks"] = int(step_matches[0])
                tasks["task_type"] = "social_workflow"
                tasks["requirements"] = [
                    f"Step {i+1}: Detailed social media workflow step with actions, tools, and platform integrations" 
                    for i in range(tasks["total_tasks"])
                ]
                tasks["completion_criteria"] = [
                    f"All {tasks['total_tasks']} workflow steps must be provided",
                    "Each step must include: actions, tools, and platform integrations",
                    f"Available tools: {', '.join(detected_tools) if detected_tools else 'All platform integrations'}",
                    "Steps must be actionable and include automation opportunities"
                ]
        
        return tasks
    
    def _generate_simple_response(self, intent: str, message: str) -> str:
        """Generate simple responses based on intent"""
        responses = {
            "greeting": [
                "Hello! 👋 I'm Aria, your AI-powered social media management assistant. I'm here to help you manage your social media presence effectively. 🚀",
                "Hi there! ✨ I'm Aria, ready to help you optimize your social media strategy and grow your brand online. 📈",
                "Welcome! 🌟 I'm Aria, your dedicated social media management partner. Let's make your social media presence shine! ✨"
            ],
            "help": [
                "I can help you with: account analysis 📊, content creation ✍️, scheduling 📅, analytics 📈, trend monitoring 🔥, ad management 📢, and much more. What would you like to work on?",
                "I'm here to assist with: managing multiple social accounts 📱, creating engaging content ✨, scheduling posts 🗓️, analyzing performance 📊, and optimizing your strategy. What do you need help with?",
                "I offer comprehensive social media management including: content creation 🎨, scheduling ⏰, analytics 📉, trend monitoring 🚀, competitor analysis 🕵️‍♀️, and strategic planning. How can I assist you today?"
            ],
            "account_management": [
                "I'll analyze your connected social media accounts and provide detailed insights and recommendations for improvement. 🕵️‍♂️",
                "Let me scan your accounts to understand your current performance and identify opportunities for growth. 🚀",
                "I'll examine your social media presence across all platforms and give you actionable insights to optimize your strategy. 📊"
            ],
            "content_creation": [
                "I can help you create engaging content with AI-generated captions ✍️, hashtags #️⃣, and even generate images 🖼️. What type of content would you like to create?",
                "Let's create some amazing content! 🎨 I can generate captions, suggest hashtags, create images, and help you adapt content for different platforms.",
                "I'm here to help with content creation! ✨ I can generate captions, hashtags, images, and help you repurpose content across platforms."
            ],
            "scheduling": [
                "I can help you schedule posts across all your connected platforms with optimal timing for maximum engagement. ⏰",
                "Let's get your content scheduled! 🗓️ I'll analyze the best posting times for each platform and schedule your posts accordingly.",
                "I'll help you schedule your content at the perfect times across all platforms to maximize reach and engagement. 🚀"
            ],
            "analytics": [
                "I'll provide comprehensive analytics on your social media performance, including engagement rates, audience insights, and growth trends. 📉",
                "Let me analyze your performance data and show you detailed insights about your audience, content performance, and growth opportunities. 📊",
                "I'll give you deep insights into your social media performance, helping you understand what's working and where to improve. 💡"
            ],
            "trends": [
                "I'll monitor trending topics and hashtags relevant to your industry and help you create content that capitalizes on current trends. 🔥",
                "Let me track what's trending in your niche and suggest ways to incorporate trending topics into your content strategy. 📈",
                "I'll keep you updated on trending topics and help you create timely, relevant content that resonates with your audience. 🚀"
            ],
            "ads": [
                "I can help you create and manage advertising campaigns across multiple platforms, optimize targeting, and track performance. 💰",
                "Let's set up effective ad campaigns! 📢 I'll help you create compelling ad copy, target the right audience, and optimize for better results.",
                "I'll assist you with ad campaign management, from creation to optimization, helping you get the best ROI on your advertising spend. 💸"
            ],
            "general": [
                "I'm here to help with all aspects of social media management. Feel free to ask me about content creation ✍️, scheduling 📅, analytics 📊, or any other social media needs!",
                "How can I assist you with your social media strategy today? 🤔 I'm ready to help with content, scheduling, analytics, or any other aspect of social media management.",
                "I'm Aria, your social media management assistant. What would you like to work on today? ✨"
            ]
        }
        
        import random
        return random.choice(responses.get(intent, responses["general"]))
    
    
    def _generate_thinking_steps(self, intent: str, message: str, user_id: int, db: AsyncSession = None) -> List[str]:
        """Generate thinking steps based on creative/brand intent"""
        steps = []
        
        if intent == "content_creation":
            steps = [
                "Analyzing your brand voice & style guide...",
                "Scouring connected platforms for top-performing hooks...",
                "Drafting platform-specific captions with emoji accents...",
                "Optimizing hashtag sets for maximum reach..."
            ]
        elif intent == "account_management":
            steps = [
                "Fetching latest performance metrics across all nodes...",
                "Identifying audience engagement spikes...",
                "Detecting optimal posting windows for the next 48h...",
                "Formulating growth recommendations..."
            ]
        elif intent == "scheduling":
            steps = [
                "Reviewing your content calendar for gaps...",
                "Synchronizing time-zones with platform APIs...",
                "Preparing content queue for automated publishing...",
                "Verifying media asset availability..."
            ]
        elif intent == "analytics":
            steps = [
                "Aggregating cross-platform engagement data...",
                "Calculating CTR and Conversion Velocity...",
                "Generating sentiment analysis for recent comments...",
                "Visualizing performance trends..."
            ]
        else:
            steps = [
                "Assessing platform-specific context...",
                "Checking recent social media trends...",
                "Analyzing creative brief...",
                "Reviewing brand guidelines...",
                "Checking active campaigns...",
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
            simple_intent = self._detect_intent_simple(message)
            
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
- User Name: {profile.get('full_name', 'User')}
- Brand Name: {profile.get('company', 'Not specified')}
- Industry: {profile.get('industry', 'Not specified')}
- Brand Voice: {profile.get('brand_voice', 'Professional & Friendly')}
- Target Audience: {profile.get('target_audience', 'General')}
- Connected Platforms: {platform_status}
- Connected Tools: {tool_status}
"""
            except Exception as e:
                logger.warning(f"Failed to load user context: {e}")

            messages = [
                {
                    "role": "system",
                    "content": f"""GLOBAL AGENT OPERATING RULES (APPLIES TO ALL AGENTS):
1. Do not hallucinate capabilities, data access, or results. Only reference features explicitly listed in each agent’s CAPABILITIES.
2. If a requested action requires unavailable data or permissions, clearly state the limitation and propose the closest viable alternative.
3. Prefer concrete execution plans over theory. Every recommendation must map to at least one named service.
4. Ask at most ONE clarifying question when critical information is missing; otherwise proceed with best‑practice assumptions and state them.
5. Default to measurable outcomes: define KPIs, timelines, and success criteria for all actions.
6. Maintain security, privacy, accessibility, and ethical standards in every response.
7. Be concise but complete: clarity > verbosity.
8. Always use relevant emojis in your responses to make them engaging, personality-driven, and visually appealing 🚀✨.

STRUCTURAL RULES:
1. NO REPETITIVE GREETINGS: If a conversation history exists, SKIP all introductions (e.g., "I'm Aria...", "Welcome!"). Jump straight to the task.
2. NO DEFLECTIONS: NEVER say "I'm having trouble processing".
3. CONNECTION ENFORCEMENT: Check "Connected Platforms" and "Connected Tools" before promising action.
4. STRUCTURED OUTPUT MANDATORY: One-sentence executive summary, bullets or numbered lists, end with ONE clear action.

**IDENTITY:**
You are Aria, Agent47's elite social media specialist. You manage, optimize, and grow social media presence with data-driven precision.

CORE IDENTITY:
- Expert in multi-platform social media strategy (Instagram, Twitter/X, Facebook, LinkedIn, TikTok, YouTube)
- Data analyst who turns metrics into actionable insights
- Creative strategist who balances trends with brand authenticity
- Accessibility advocate ensuring content reaches all audiences

YOUR CAPABILITIES (22 FEATURES):
Content Creation & Management: content_service, content_remix_service, media_service, voice_posts_service, speech_service
Analytics & Optimization: analytics_service, advanced_analytics_service, account_analysis_service, ab_testing_service, trend_service, trend_alerts_service
Engagement & Growth: engagement_service, engagement_booster_service, automation_service, scheduling_service, publisher_service
Advertising & Campaigns: ads_service, geo_campaign_service, brand_service
Technical & Compliance: oauth_service, accessibility_service, approval_service

RESPONSE FRAMEWORK:
1. ANALYZE: Understand the user's goal (awareness, engagement, conversions, community building)
2. STRATEGIZE: Recommend specific platforms, content types, and timing
3. EXECUTE: Provide actionable steps with specific feature usage
4. MEASURE: Define clear KPIs and tracking methods
5. OPTIMIZE: Suggest continuous improvement based on data

COMMUNICATION STYLE:
- Direct and actionable - every response should include specific next steps
- Data-informed - cite metrics, benchmarks, and best practices
- Platform-aware - tailor advice to each social network's algorithm and audience
- Creative yet strategic - balance innovation with proven tactics
- Use bullet points for clarity, but keep explanations concise

EXAMPLE INTERACTION PATTERN:
User: "I need to boost Instagram engagement"
Your Response Structure:
→ Current situation analysis (request account_analysis_service data)
→ 3-5 specific tactics with expected impact
→ Implementation timeline with scheduling_service
→ Metrics to track via analytics_service
→ A/B test recommendations using ab_testing_service

ALWAYS:
✓ Reference specific features you're using (e.g., "I'll use trend_alerts_service to monitor...")
✓ Provide platform-specific advice (Instagram ≠ LinkedIn ≠ TikTok)
✓ Include accessibility considerations (alt text, captions, readable fonts)
✓ Give time-bound action items
✓ Explain the "why" behind each recommendation

NEVER:
✗ Give generic social media advice that could apply to any platform
✗ Suggest tactics without explaining measurement methods
✗ Ignore brand voice consistency across platforms
✗ Recommend posting without testing and optimization
✗ Overlook accessibility or ethical considerations

DECISION-MAKING PRIORITY:
1. Business goals alignment
2. Audience engagement quality over vanity metrics
3. Sustainable growth over quick wins
4. Brand authenticity over trend-chasing
5. Accessibility and inclusivity in all content

When uncertain about user goals, ask ONE specific clarifying question, then proceed with best-practice recommendations.

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
            ai_manager = await self._get_ai_service_manager()
            from core.config import settings
            
            ai_response = await ai_manager.generate_text(
                messages=messages,
                max_tokens=settings.groq.groq_max_tokens,
                temperature=0.2,
                top_p=0.9
            )

            if ai_response.success and ai_response.text_content:
                response_text = ai_response.text_content
                confidence = 0.95
            else:
                logger.error(f"LLM Failure: {ai_response.error}")
                response_text = self._generate_simple_response(simple_intent, message)
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
                "session_id": session_id,
                "response": "I apologize, but I encountered an error processing your message. Please try again or rephrase your request."
            }
    
    def _fallback_intent_detection(self, message: str) -> Dict[str, Any]:
        """Fallback intent detection when NLP fails"""
        message_lower = message.lower()
        
        # Simple keyword-based intent detection
        if any(word in message_lower for word in ["hello", "hi", "hey", "good morning", "good afternoon"]):
            return {"intent": "greeting", "confidence": 0.8}
        elif any(word in message_lower for word in ["help", "what can you do", "capabilities", "features"]):
            return {"intent": "help", "confidence": 0.8}
        elif any(word in message_lower for word in ["account", "accounts", "analyze", "analysis", "scan"]):
            return {"intent": "account_management", "confidence": 0.7}
        elif any(word in message_lower for word in ["create", "content", "post", "caption", "hashtag"]):
            return {"intent": "content_creation", "confidence": 0.7}
        elif any(word in message_lower for word in ["schedule", "timing", "when to post", "posting time"]):
            return {"intent": "scheduling", "confidence": 0.7}
        elif any(word in message_lower for word in ["analytics", "performance", "stats", "metrics", "insights"]):
            return {"intent": "analytics", "confidence": 0.7}
        elif any(word in message_lower for word in ["trend", "trending", "what's hot", "viral"]):
            return {"intent": "trends", "confidence": 0.7}
        elif any(word in message_lower for word in ["ad", "advertising", "campaign", "promote"]):
            return {"intent": "ads", "confidence": 0.7}
        elif any(word in message_lower for word in ["location", "region", "country", "city", "africa", "kenya", "nairobi"]):
            return {"intent": "geo_campaigns", "confidence": 0.7}
        else:
            return {"intent": "general", "confidence": 0.5}
    
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
        elif intent == "account_management":
            return await self._handle_account_management(user_id, message, session, db)
        elif intent == "content_creation":
            return await self._handle_content_creation(user_id, message, session, db)
        elif intent == "scheduling":
            return await self._handle_scheduling(user_id, message, session, db)
        elif intent == "analytics":
            return await self._handle_analytics(user_id, message, session, db)
        elif intent == "trends":
            return await self._handle_trends(user_id, message, session, db)
        elif intent == "ads":
            return await self._handle_ads(user_id, message, session, db)
        elif intent == "geo_campaigns":
            return await self._handle_geo_campaigns(user_id, message, session, db)
        else:
            return await self._handle_general_query(user_id, message, session, db)
    
    async def _handle_account_management(
        self,
        user_id: int,
        message: str,
        session: Dict[str, Any],
        db: AsyncSession
    ) -> str:
        """Handle account management related queries"""
        try:
            # Check if user wants a full analysis
            if any(word in message.lower() for word in ["analyze", "scan", "overview", "summary", "health"]):
                # Perform account analysis
                analysis_result = await self.account_analysis.analyze_accounts(user_id, db=db)
                
                if analysis_result["success"]:

                    summary = analysis_result["analysis_summary"]
                    return f"""I've analyzed your social media accounts! Here's what I found:

📊 **Account Overview:**
• Total accounts: {summary['total_accounts']}
• Total followers: {summary['total_followers']:,}
• Total posts: {summary['total_posts']:,}
• Overall health score: {summary['overall_health_score']}/100

🎯 **Key Insights:**
• {analysis_result['recommendations']['strategic_priorities'][0] if analysis_result['recommendations'].get('strategic_priorities') else 'Focus on improving content quality and consistency'}
• {analysis_result['recommendations']['strategic_priorities'][1] if len(analysis_result['recommendations'].get('strategic_priorities', [])) > 1 else 'Implement regular posting schedules'}

Would you like me to dive deeper into any specific account or area of improvement?"""
                else:
                    return "I couldn't analyze your accounts at the moment. Please make sure you have connected social media accounts, and I'll be happy to help analyze them."
            
            # Check for specific account queries
            elif any(word in message.lower() for word in ["instagram", "linkedin", "twitter", "facebook", "tiktok"]):
                return "I can help you with specific platform optimization! Would you like me to analyze your performance on that platform, suggest content strategies, or help with posting schedules?"
            
            else:
                return self._get_random_response("account_management")
                
        except Exception as e:
            return f"I encountered an issue while analyzing your accounts: {str(e)}. Please try again or contact support if the problem persists."
    
    async def _handle_content_creation(
        self,
        user_id: int,
        message: str,
        session: Dict[str, Any],
        db: AsyncSession
    ) -> str:
        """Handle content creation related queries"""
        try:
            # Check for specific content types
            if any(word in message.lower() for word in ["caption", "text", "copy"]):
                return "I can help you create engaging captions! What's the topic or theme you'd like to write about? I'll generate compelling copy with relevant hashtags."
            
            elif any(word in message.lower() for word in ["hashtag", "tag"]):
                return "I'll help you find the perfect hashtags! What's your content about? I'll suggest relevant, trending hashtags to boost your reach."
            
            elif any(word in message.lower() for word in ["image", "photo", "visual"]):
                return "I can generate custom images for your posts! What would you like the image to show? I'll create something that matches your brand and message."
            
            elif any(word in message.lower() for word in ["video", "reel", "story"]):
                return "I can help you create engaging video content! What type of video would you like to make? I'll suggest formats and help you plan the content."
            
            elif any(word in message.lower() for word in ["remix", "adapt", "reformat"]):
                return "I can help you repurpose content across different platforms! What content would you like to adapt? I'll help you create platform-specific versions."
            
            else:
                return self._get_random_response("content_creation")
                
        except Exception as e:
            return f"I encountered an issue with content creation: {str(e)}. Please try again or let me know what specific type of content you need help with."
    
    async def _handle_scheduling(
        self,
        user_id: int,
        message: str,
        session: Dict[str, Any],
        db: AsyncSession
    ) -> str:
        """Handle scheduling related queries"""
        try:
            # Check for specific scheduling needs
            if any(word in message.lower() for word in ["when", "time", "timing", "best time"]):
                return "I'll analyze the best posting times for your audience! Let me check your engagement data and suggest optimal posting schedules for each platform."
            
            elif any(word in message.lower() for word in ["schedule", "plan", "calendar"]):
                return "I can help you schedule your content! How many posts would you like to schedule, and what type of content are you planning? I'll create an optimized posting calendar."
            
            elif any(word in message.lower() for word in ["frequency", "how often", "posting schedule"]):
                return "I'll help you determine the ideal posting frequency! Let me analyze your audience behavior and suggest how often you should post on each platform for maximum engagement."
            
            else:
                return self._get_random_response("scheduling")
                
        except Exception as e:
            return f"I encountered an issue with scheduling: {str(e)}. Please try again or let me know what specific scheduling help you need."
    
    async def _handle_analytics(
        self,
        user_id: int,
        message: str,
        session: Dict[str, Any],
        db: AsyncSession
    ) -> str:
        """Handle analytics related queries"""
        try:
            # Check for specific analytics needs
            if any(word in message.lower() for word in ["performance", "how am i doing", "stats", "metrics"]):
                return "I'll give you a comprehensive performance overview! Let me analyze your engagement rates, follower growth, content performance, and audience insights."
            
            elif any(word in message.lower() for word in ["engagement", "likes", "comments", "shares"]):
                return "I'll analyze your engagement patterns! Let me show you which content types perform best, when your audience is most active, and how to boost engagement."
            
            elif any(word in message.lower() for word in ["audience", "followers", "demographics"]):
                return "I'll provide detailed audience insights! Let me analyze your follower demographics, behavior patterns, and growth trends to help you understand your audience better."
            
            elif any(word in message.lower() for word in ["growth", "follower growth", "reach"]):
                return "I'll analyze your growth patterns! Let me show you your follower growth trends, reach expansion, and opportunities for further growth."
            
            else:
                return self._get_random_response("analytics")
                
        except Exception as e:
            return f"I encountered an issue with analytics: {str(e)}. Please try again or let me know what specific insights you're looking for."
    
    async def _handle_trends(
        self,
        user_id: int,
        message: str,
        session: Dict[str, Any],
        db: AsyncSession
    ) -> str:
        """Handle trends related queries"""
        try:
            # Check for specific trend needs
            if any(word in message.lower() for word in ["trending", "what's hot", "viral", "popular"]):
                return "I'll show you what's trending right now! Let me check the latest trending topics, hashtags, and conversations relevant to your industry."
            
            elif any(word in message.lower() for word in ["hashtag", "trending hashtag"]):
                return "I'll find trending hashtags for you! Let me check what's popular in your niche and suggest hashtags that can boost your content's reach."
            
            elif any(word in message.lower() for word in ["competitor", "what are others doing"]):
                return "I'll analyze your competitors' strategies! Let me check what content and hashtags are working well in your industry and suggest how you can stay competitive."
            
            else:
                return self._get_random_response("trends")
                
        except Exception as e:
            return f"I encountered an issue with trend analysis: {str(e)}. Please try again or let me know what specific trend information you need."
    
    async def _handle_ads(
        self,
        user_id: int,
        message: str,
        session: Dict[str, Any],
        db: AsyncSession
    ) -> str:
        """Handle advertising related queries"""
        try:
            # Check for specific ad needs
            if any(word in message.lower() for word in ["instagram ad", "facebook ad"]):
                return "I can help you create Instagram and Facebook ads! Let me know your campaign goals, target audience, and budget, and I'll help you set up effective ad campaigns."
            
            elif any(word in message.lower() for word in ["linkedin ad", "professional ad"]):
                return "I can help you create LinkedIn ads for professional audiences! Let me know your business objectives and target market, and I'll help you create compelling ad campaigns."
            
            elif any(word in message.lower() for word in ["campaign", "advertising campaign"]):
                return "I'll help you create comprehensive advertising campaigns! Let me know your goals, target audience, and budget, and I'll help you design effective ad strategies across platforms."
            
            else:
                return self._get_random_response("ads")
                
        except Exception as e:
            return f"I encountered an issue with advertising: {str(e)}. Please try again or let me know what specific ad help you need."
    
    async def _handle_geo_campaigns(
        self,
        user_id: int,
        message: str,
        session: Dict[str, Any],
        db: AsyncSession
    ) -> str:
        """Handle geo-specific campaign queries"""
        try:
            # Check for specific location needs
            if any(word in message.lower() for word in ["africa", "kenya", "nairobi", "location", "region"]):
                return "I can help you create location-specific campaigns! I have extensive data on African countries and cities, including Kenya, Nairobi, and many more. What region would you like to target?"
            
            elif any(word in message.lower() for word in ["campaign", "targeting", "local"]):
                return "I'll help you create geo-targeted campaigns! Let me know which regions you want to target, and I'll help you design campaigns that resonate with local audiences."
            
            else:
                return self._get_random_response("geo_campaigns")
                
        except Exception as e:
            return f"I encountered an issue with geo-campaigns: {str(e)}. Please try again or let me know what specific location targeting you need."
    
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
                {"role": "system", "content": "User asking general question to Aria social media assistant"},
                {"role": "user", "content": f"User message: {message}\n\nProvide a helpful, friendly response as Aria, a social media management AI assistant. Keep it conversational and offer to help with specific social media tasks."}
            ]
            
            ai_response = await ai_manager.generate_text(
                messages=messages,
                max_tokens=200,
                temperature=0.7
            )
            
            response = ai_response
            
            if response.success:
                return response.text_content
            else:
                return "I'm here to help you with all aspects of social media management! I can help with content creation, scheduling, analytics, trends, advertising, and much more. What would you like to work on today?"
                
        except Exception as e:
            return "I'm here to help you with social media management! I can assist with content creation, scheduling, analytics, trends, advertising, and account optimization. What would you like to focus on?"
    
    def _format_service_results(self, service_result: Dict[str, Any], intent: str) -> str:
        """Format service results into readable text for LLM context"""
        try:
            if intent == "account_management" and "analysis_summary" in service_result:
                summary = service_result["analysis_summary"]
                return f"""Account Analysis Results:
- Total accounts: {summary.get('total_accounts', 0)}
- Total followers: {summary.get('total_followers', 0):,}
- Total posts: {summary.get('total_posts', 0):,}
- Overall health score: {summary.get('overall_health_score', 0)}/100
- Recommendations: {service_result.get('recommendations', {})}"""
            
            elif intent == "content_creation":
                if "caption" in service_result:
                    return f"""Generated Caption:
{service_result.get('caption', '')}
Model: {service_result.get('model', 'unknown')}"""
                elif "hashtags" in service_result:
                    tags = service_result.get("hashtags", [])
                    return f"""Suggested Hashtags ({len(tags)}):
{', '.join(tags)}"""
            
            elif intent == "media_generation":
                if service_result.get("success") and "url" in service_result:
                    return f"""Image Generated Successfully:
- URL: {service_result.get('url')}
- Model: {service_result.get('model_used', 'unknown')}
- Response time: {service_result.get('response_time_ms', 0)}ms"""
                else:
                    return f"Image generation failed: {service_result.get('error', 'Unknown error')}"
            
            elif intent == "scheduling":
                if "schedules" in service_result:
                    count = service_result.get("count", 0)
                    schedules = service_result.get("schedules", [])
                    schedule_list = "\n".join([
                        f"  - Post {s.get('id')}: {s.get('platform_targets', [])} at {s.get('scheduled_at', 'N/A')}"
                        for s in schedules[:5]
                    ])
                    return f"""Scheduled Posts ({count} total):
{schedule_list}"""
                else:
                    return service_result.get("message", "Scheduling service result")
            
            elif intent == "trends":
                if "trend_data" in service_result:
                    trend_data = service_result.get("trend_data", {})
                    topic = service_result.get("topic", "unknown")
                    return f"""Trend Data for "{topic}":
{trend_data}"""
                elif "task_id" in service_result:
                    return f"""Trend Monitoring Setup:
- Task ID: {service_result.get('task_id')}
- Keywords: {service_result.get('keywords', [])}
- Platforms: {service_result.get('platforms', [])}
- Frequency: {service_result.get('alert_frequency', 'daily')}"""
                else:
                    return f"Trends: {service_result}"
            
            elif intent == "analytics":
                return f"Analytics Summary: {service_result}"
            
            elif intent == "ads":
                return f"Ad AriaCampaign: {service_result}"
            
            elif intent == "geo_campaigns":
                return f"Geo-AriaCampaign: {service_result}"
            
            elif intent == "engagement":
                if "engagement_score" in service_result:
                    return f"""Engagement Boost Suggestions:
- Engagement Score: {service_result.get('engagement_score', 0)}/100
- Poll Suggestions: {len(service_result.get('poll_suggestions', []))}
- Question Suggestions: {len(service_result.get('question_suggestions', []))}
- CTA Suggestions: {len(service_result.get('cta_suggestions', []))}"""
                else:
                    return service_result.get("message", "Engagement service result")
            
            elif intent == "content_remix":
                if "remixed_content" in service_result:
                    platforms = list(service_result.get("remixed_content", {}).keys())
                    return f"""Content Remixed for Platforms:
- Platforms: {', '.join(platforms)}
- Total variations: {len(platforms)}"""
                else:
                    return service_result.get("message", "Content remix result")
            
            elif intent == "auto_reply":
                if service_result.get("success"):
                    return f"""Auto-Reply Generated:
- Sentiment: {service_result.get('sentiment', 'neutral')}
- Reply: {service_result.get('reply', '')}
- Model: {service_result.get('ai_model_used', 'unknown')}"""
                else:
                    return f"Auto-reply failed: {service_result.get('error', 'Unknown error')}"
            
            elif intent == "brand":
                if "brand_profile" in service_result:
                    profile = service_result["brand_profile"]
                    return f"""Brand Profile:
- Voice: {profile.get('voice', {})}
- Hashtags Bank: {len(profile.get('hashtags_bank', []))} hashtags
- Banned Keywords: {len(profile.get('banned_keywords', []))} keywords"""
                else:
                    return service_result.get("message", "Brand service result")
            
            elif intent == "publishing":
                return service_result.get("message", "Publishing service result")
            
            elif intent == "oauth":
                return service_result.get("message", "OAuth service result")
            
            elif intent == "approval":
                if "approval_id" in service_result:
                    return f"""AriaApproval Request Created:
- AriaApproval ID: {service_result.get('approval_id')}
- Status: {service_result.get('status', 'pending')}"""
                elif "status" in service_result:
                    return f"AriaApproval Decision: {service_result.get('status', 'unknown')}"
                else:
                    return service_result.get("message", "AriaApproval service result")
            
            elif intent == "ab_testing":
                if "winner" in service_result:
                    return f"A/B Test Winner Selected: {service_result.get('winner', {})}"
                else:
                    return service_result.get("message", "A/B testing result")
            
            elif intent == "voice_post":
                if service_result.get("success"):
                    return f"""Voice Post Created:
- Transcription: {service_result.get('transcription', '')[:100]}...
- Enhanced Text: {service_result.get('enhanced_text', '')[:100]}...
- Hashtags: {len(service_result.get('hashtags', []))} hashtags
- Scheduled Post ID: {service_result.get('scheduled_post_id', 'N/A')}"""
                else:
                    return f"Voice post creation failed: {service_result.get('error', 'Unknown error')}"
            
            elif intent == "accessibility":
                if "guidelines" in service_result:
                    guidelines = service_result.get("guidelines", {})
                    return f"""Accessibility Guidelines for {service_result.get('platform', 'general')}:
{chr(10).join([f'- {k}: {v}' for k, v in guidelines.items()][:5])}"""
                elif "accessibility_score" in service_result:
                    return f"""Accessibility Report:
- Score: {service_result.get('accessibility_score', 0)}/100
- Features: {len(service_result.get('features', []))}
- Recommendations: {len(service_result.get('recommendations', []))}"""
                elif "alt_text" in service_result:
                    return f"Alt Text Generated: {service_result.get('alt_text', '')}"
                elif "captions" in service_result:
                    return f"Video Captions Generated: Available at {service_result.get('caption_url', 'N/A')}"
                else:
                    return service_result.get("message", "Accessibility service result")
            
            elif intent == "advanced_analytics":
                if "heatmap_data" in service_result:
                    sentiment = service_result.get("sentiment_summary", {})
                    return f"""Advanced Analytics - Sentiment Heatmap:
- Platform: {service_result.get('platform', 'unknown')}
- Date Range: {service_result.get('date_range', 'unknown')}
- Total Engagements: {sentiment.get('total_engagements', 0)}
- Positive Sentiment: {sentiment.get('positive_sentiment', 0)}
- Overall Sentiment Score: {sentiment.get('overall_sentiment_score', 0.0)}"""
                else:
                    return service_result.get("message", "Advanced analytics result")
            
            elif intent == "automation":
                if service_result.get("success"):
                    posts_created = service_result.get("posts_created", 0)
                    days = service_result.get("days", 0)
                    platforms = ", ".join(service_result.get("platforms", []))
                    return f"""✅ Automation Created Successfully!
- Duration: {days} days
- Posts Scheduled: {posts_created} posts
- Platforms: {platforms}
- Start Date: {service_result.get('start_date', 'N/A')}
- End Date: {service_result.get('end_date', 'N/A')}
- Automation Enabled: Yes

Your content will be automatically posted at optimal times each day."""
                else:
                    return f"Automation setup failed: {service_result.get('error', 'Unknown error')}"
            
            # Generic fallback - format dict nicely
            if isinstance(service_result, dict):
                if "success" in service_result:
                    result_parts = [f"Success: {service_result['success']}"]
                    for key, value in service_result.items():
                        if key != "success" and not isinstance(value, (dict, list)):
                            result_parts.append(f"{key}: {value}")
                    return "\n".join(result_parts)
                else:
                    return f"Service Result:\n{service_result}"
            return str(service_result)
        except Exception:
            return str(service_result)
    
    def _get_random_response(self, intent: str) -> str:
        """Get a random response for a given intent"""
        responses = self.intent_responses.get(intent, ["I'm here to help you with that!"])
        import random
        return random.choice(responses)
    
    def _generate_thinking_steps(self, intent: str, message: str, user_id: int, db: AsyncSession = None) -> List[str]:
        """Generate thinking steps based on intent and message context"""
        steps = []
        
        if intent == "account_management":
            if any(word in message.lower() for word in ["analyze", "scan", "overview", "summary", "health"]):
                steps = [
                    "Checking connected social media platforms...",
                    "Analyzing account health and performance metrics...",
                    "Reviewing posting history and engagement patterns...",
                    "Identifying optimization opportunities..."
                ]
            else:
                steps = [
                    "Reviewing your account configuration...",
                    "Checking platform connections...",
                    "Analyzing current settings..."
                ]
        
        elif intent == "content_creation":
            steps = [
                "Analyzing your brand voice and content preferences...",
                "Reviewing past content performance...",
                "Generating content ideas aligned with your brand...",
                "Optimizing for engagement and reach..."
            ]
        
        elif intent == "scheduling":
            steps = [
                "Analyzing optimal posting times for your audience...",
                "Reviewing engagement patterns across platforms...",
                "Creating optimal schedule based on data...",
                "Setting up automated scheduling..."
            ]
        
        elif intent == "automation":
            steps = [
                "Checking connected social media platforms...",
                "Analyzing posting history and engagement patterns...",
                "Reviewing your content preferences and brand voice...",
                "Creating automation workflow..."
            ]
        
        elif intent == "analytics":
            steps = [
                "Gathering performance data from all platforms...",
                "Analyzing engagement metrics and trends...",
                "Identifying key insights and opportunities...",
                "Preparing comprehensive analytics report..."
            ]
        
        else:
            steps = [
                "Analyzing your request...",
                "Reviewing relevant information...",
                "Preparing response..."
            ]
        
        return steps
    
    def _get_suggested_actions(self, intent: str) -> List[str]:
        """Get suggested actions based on the detected intent"""
        suggestions = {
            "greeting": ["Analyze my accounts", "Create content", "Check analytics", "View trends"],
            "help": ["Account analysis", "Content creation", "Post scheduling", "Performance analytics"],
            "account_management": ["Full account scan", "Platform-specific insights", "Health score details", "Improvement recommendations"],
            "content_creation": ["Generate captions", "Create hashtags", "Generate images", "Content remix"],
            "scheduling": ["Best posting times", "Create posting calendar", "Schedule posts", "Optimize frequency"],
            "analytics": ["Performance overview", "Engagement analysis", "Audience insights", "Growth trends"],
            "trends": ["Trending topics", "Popular hashtags", "Competitor analysis", "Content suggestions"],
            "ads": ["Instagram ads", "LinkedIn ads", "AriaCampaign creation", "Ad optimization"],
            "geo_campaigns": ["African markets", "Global regions", "Local targeting", "Cultural insights"]
        }
        
        return suggestions.get(intent, ["Get help", "Learn more", "Explore features"])
    
    async def get_chat_suggestions(self, user_id: int) -> List[str]:
        """Get personalized chat suggestions for the user"""
        return [
            "Analyze my social media accounts",
            "Create engaging content for me",
            "Show me my performance analytics",
            "What's trending in my industry?",
            "Help me schedule posts",
            "Create a geo-targeted campaign",
            "Set up advertising campaigns",
            "Optimize my posting strategy"
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

Router: 
backend/agents/aria/app/routers/aria_chat.py

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
import logging
from datetime import datetime

from ..services.aria_chat_service import AriaChatService
from ..database import get_db
from core.utils.auth import get_current_user
from core.utils.rate_limiter import RateLimiter

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize service
chat_service = AriaChatService()
rate_limiter = RateLimiter(requests_per_minute=60)

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    success: bool
    response: str
    thinking_steps: List[str] = []
    intent: Optional[str] = None
    confidence: float = 0.0
    session_id: str
    data: Optional[Dict[str, Any]] = None
    timestamp: str

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Process a chat message from the user
    """
    try:
        user_id = current_user.get("id")
        
        # Check rate limit
        await rate_limiter.check_limit(f"user_{user_id}")
        
        # Process message
        result = await chat_service.process_chat_message(
            user_id=user_id,
            message=request.message,
            session_id=request.session_id,
            db=db,
            user_resources=request.context
        )
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result.get("error", "Unknown error"))
        
        return ChatResponse(
            success=True,
            response=result["response"],
            thinking_steps=result.get("thinking_steps", []),
            intent=result.get("intent"),
            confidence=result.get("confidence", 0.0),
            session_id=result["session_id"],
            data=result.get("data"),
            timestamp=result["timestamp"]
        )
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/suggestions")
async def get_suggestions(
    current_user: Dict = Depends(get_current_user)
):
    """
    Get personalized chat suggestions
    """
    try:
        user_id = current_user.get("id")
        suggestions = await chat_service.get_chat_suggestions(user_id)
        return {"success": True, "suggestions": suggestions}
    except Exception as e:
        logger.error(f"Error getting suggestions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/session/{session_id}/end")
async def end_session(
    session_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """
    End a chat session
    """
    try:
        result = await chat_service.end_chat_session(session_id)
        if not result["success"]:
            raise HTTPException(status_code=404, detail=result.get("error", "Session not found"))
        return result
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error ending session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history")
async def get_history(
    session_id: Optional[str] = None,
    limit: int = 50,
    current_user: Dict = Depends(get_current_user)
):
    """
    Get chat history
    """
    try:
        user_id = current_user.get("id")
        result = await chat_service.get_chat_history(user_id, session_id, limit)
        return result
    except Exception as e:
        logger.error(f"Error getting history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_agent_status(
    current_user: Dict = Depends(get_current_user)
):
    """
    Get agent status and simple health check
    """
    return {
        "status": "active",
        "agent": "aria",
        "model": "llama-3.1-70b-versatile",
        "capabilities": [
            "social_media_management",
            "content_creation",
            "analytics",
            "scheduling",
            "trend_monitoring"
        ]
    }

@router.post("/demo")
async def demo_chat(
    request: ChatRequest
):
    """
    Demo endpoint without authentication for testing
    """
    try:
        # Create a mock user for demo
        user_id = 999
        
        # Process message
        # Note: We need a DB session even for demo if the service relies on it
        # For now, we'll try to process without DB if possible, or Mock it
        
        # This is a simplified path for demo purposes
        simple_intent = chat_service._detect_intent_simple(request.message)
        response_text = chat_service._generate_simple_response(simple_intent, request.message)
        thinking_steps = chat_service._generate_thinking_steps(simple_intent, request.message, user_id)
        
        return ChatResponse(
            success=True,
            response=response_text,
            thinking_steps=thinking_steps,
            intent=simple_intent,
            confidence=0.8,
            session_id=request.session_id or "demo_session",
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error in demo chat: {e}")
        return ChatResponse(
            success=False,
            response=f"I'm having trouble processing that right now. Error: {str(e)}",
            session_id="demo_error",
            timestamp=datetime.now().isoformat()
        )

@router.get("/help")
async def get_help_info():
    """
    Get help information and capabilities
    """
    return {
        "name": "Aria",
        "role": "Social Media Manager",
        "description": "I help you manage your social media presence, create content, and analyze performance.",
        "capabilities": {
            "account_management": "Analyze and optimize your social profiles",
            "content_creation": "Generate captions, hashtags, and images",
            "scheduling": "Plan and schedule your posts",
            "analytics": "Track performance and growth",
            "trends": "Monitor viral trends and topics",
            "ads": "Manage advertising campaigns",
            "geo_campaigns": "Run location-based marketing"
        },
        "sample_prompts": [
            "Analyze my Instagram account health",
            "Create a caption for a coffee shop post",
            "When is the best time to post on LinkedIn?",
            "What's trending in fashion right now?",
            "Create a marketing campaign for Nairobi"
        ]
    }

2. Clara (HR & Recruitment)
Service: 
backend/agents/clara/app/services/clara_chat_service.py

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

Router: 
backend/agents/clara/app/routers/clara_chat.py

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..services.clara_chat_service import ClaraChatService
from core.authentication.auth_manager import get_current_user
from core.database.connection import get_database as get_core_db
from core.database.models import UserSelectedAgent
from sqlalchemy import select
from ..models import ClaraSupportTicket
from ..database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/clara-chat", tags=["Clara Chat Interface"])

clara_chat_service = ClaraChatService()


from pydantic import BaseModel

class ChatMessageRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

@router.post("/message")
async def process_chat_message(
    request: ChatMessageRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Process a chat message from the user and get Clara's response"""
    try:
        # Enforce per-agent pause/automation guard for Clara
        core_db = get_core_db()
        async with core_db.get_session() as core_session:
            res = await core_session.execute(
                select(UserSelectedAgent).where(
                    UserSelectedAgent.user_id == current_user.id,
                    UserSelectedAgent.agent_key == "clara",
                )
            )
            row = res.scalar_one_or_none()
            if not row:
                raise HTTPException(status_code=403, detail="Agent Clara is not selected")
            if row.status == "paused":
                raise HTTPException(status_code=403, detail="Agent Clara is paused")

        result = await clara_chat_service.process_chat_message(
            user_id=current_user.id,
            message=request.message,
            session_id=request.session_id,
            db=db
        )
        
        if result["success"]:
            return {
                "success": True,
                "data": result,
                "agent": "Clara",
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process message: {str(e)}")


@router.get("/session/{session_id}")
async def get_session_info(
    session_id: str,
    current_user = Depends(get_current_user)
):
    """Get information about a chat session"""
    try:
        result = await clara_chat_service.get_session_info(session_id)
        return {
            "success": True,
            "data": result,
            "agent": "Clara"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get session info: {str(e)}")


@router.delete("/session/{session_id}")
async def clear_session(
    session_id: str,
    current_user = Depends(get_current_user)
):
    """Clear a chat session"""
    try:
        result = await clara_chat_service.clear_session(session_id)
        return {
            "success": True,
            "data": result,
            "agent": "Clara"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear session: {str(e)}")



# TODO Management Endpoints
@router.post("/todos")
async def create_todo(
    title: str,
    description: str = "",
    priority: str = "medium",
    current_user = Depends(get_current_user)
):
    """Create a new TODO item"""
    try:
        result = await clara_chat_service.create_todo(
            user_id=current_user.id,
            title=title,
            description=description,
            priority=priority
        )
        return {
            "success": True,
            "data": result,
            "agent": "Clara"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create TODO: {str(e)}")


@router.get("/todos")
async def get_todos(
    status: str = "all",
    current_user = Depends(get_current_user)
):
    """Get all TODOs for the user"""
    try:
        result = await clara_chat_service.get_todos(
            user_id=current_user.id,
            status=status
        )
        return {
            "success": True,
            "data": result,
            "agent": "Clara"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get TODOs: {str(e)}")


@router.put("/todos/{todo_id}")
async def update_todo(
    todo_id: str,
    updates: Dict[str, Any],
    current_user = Depends(get_current_user)
):
    """Update a TODO item"""
    try:
        result = await clara_chat_service.update_todo(
            user_id=current_user.id,
            todo_id=todo_id,
            updates=updates
        )
        return {
            "success": True,
            "data": result,
            "agent": "Clara"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update TODO: {str(e)}")


@router.delete("/todos/{todo_id}")
async def delete_todo(
    todo_id: str,
    current_user = Depends(get_current_user)
):
    """Delete a TODO item"""
    try:
        result = await clara_chat_service.delete_todo(
            user_id=current_user.id,
            todo_id=todo_id
        )
        return {
            "success": True,
            "data": result,
            "agent": "Clara"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete TODO: {str(e)}")


@router.post("/todos/{todo_id}/complete")
async def complete_todo(
    todo_id: str,
    current_user = Depends(get_current_user)
):
    """Mark a TODO as completed"""
    try:
        result = await clara_chat_service.complete_todo(
            user_id=current_user.id,
            todo_id=todo_id
        )
        return {
            "success": True,
            "data": result,
            "agent": "Clara"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to complete TODO: {str(e)}")


@router.get("/todos/stats")
async def get_todo_stats(
    current_user = Depends(get_current_user)
):
    """Get TODO statistics for the user"""
    try:
        result = await clara_chat_service.get_todo_stats(
            user_id=current_user.id
        )
        return {
            "success": True,
            "data": result,
            "agent": "Clara"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get TODO stats: {str(e)}")

@router.get("/health")
async def health_check():
    """Health check for Clara chat service"""
    return {
        "status": "healthy",
        "agent": "Clara",
        "service": "chat",
        "timestamp": datetime.now().isoformat()
    }

3. Eric (Sales & CRM)
Service: 
backend/agents/eric/app/services/eric_chat_service.py

from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload

from ..models import EricLead, EricDeal, EricInteraction
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

# Import ALL Eric services
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
from .deal_closing_assistance_service import DealClosingAssistanceService
from .deal_closing_service import DealClosingService
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
import logging

logger = logging.getLogger(__name__)



class EricChatService:
    """Interactive chat service for Eric that orchestrates all sales capabilities"""
    
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
                "Hello! 👋 I'm Eric, your AI-powered sales assistant. I'm here to help you generate leads, close deals, and grow your sales revenue. 🚀",
                "Hi there! ✨ I'm Eric, ready to help you boost your sales performance and achieve your revenue goals. 💰",
                "Welcome! 🌟 I'm Eric, your dedicated sales partner. Let's turn prospects into customers and grow your business! 📈"
            ],
            "help": [
                "I can help you with: lead generation 🎯, CRM automation 🤖, sales outreach ✉️, deal closing 🤝, forecasting 📊, customer insights 💡, and much more. What would you like to work on?",
                "I'm here to assist with: finding new prospects 🔍, nurturing leads 🌱, closing deals ✅, analyzing sales performance 📈, and optimizing your sales process. What do you need help with?",
                "I offer comprehensive sales support including: lead qualification ✅, sales forecasting 📉, customer segmentation 👥, objection handling 🛡️, and revenue optimization 🚀. How can I assist you today?"
            ],
            "lead_generation": [
                "I'll help you identify and generate high-quality leads for your business. Let me analyze your target market and create a lead generation strategy. 🎯",
                "Let me scan your CRM and market data to find new prospect opportunities and create targeted outreach campaigns. 🔍",
                "I'll examine your current lead sources and develop new strategies to attract qualified prospects to your sales funnel. 🚀"
            ],
            "deal_closing": [
                "I'll analyze your open deals and provide strategies to move them through the sales pipeline and close more deals. 🤝",
                "Let me review your deal stages and identify bottlenecks or opportunities to accelerate the closing process. ✅",
                "I'll help you overcome objections and create compelling proposals that convert prospects into customers. ✨"
            ],
            "sales_forecasting": [
                "I'll analyze your sales data and market trends to provide accurate revenue forecasts and help you plan for the future. 📊",
                "Let me examine your pipeline and historical performance to predict your sales outcomes and identify growth opportunities. 📉",
                "I'll create detailed sales projections based on your current deals, market conditions, and team performance. 🚀"
            ],
            "crm_automation": [
                "I'll help you automate your CRM processes to save time and improve your sales efficiency. 🤖",
                "Let me set up automated workflows for lead nurturing, follow-ups, and deal progression in your CRM system. ⚙️",
                "I'll optimize your CRM data management and create automated reports to track your sales performance. 📊"
            ],
            "objection_handling": [
                "I'll help you prepare responses to common sales objections and improve your closing techniques. 🛡️",
                "Let me analyze your past objections and create a comprehensive objection handling playbook for your team. 📖",
                "I'll provide you with proven strategies to overcome price, timing, and authority objections in your sales conversations. ✨"
            ],
            "general": [
                "I'm here to help you provide excellent customer support. What challenge are you facing? 🤔",
                "Let's work together to improve your customer service. What do you need assistance with? ✨",
                "I can help with any customer support task. What's your goal today? 🚀"
            ]
        }
    
    async def initialize(self):
        """Initialize explicit services"""
        # In a real app, this might connect to external APIs or load models
        self._services_initialized = True
        logger.info("EricChatService initialized")

    async def _get_ai_service_manager(self) -> AIServiceManager:
        """Get or initialize the AI service manager"""
        if not self.ai_service_manager:
            self.ai_service_manager = get_ai_service_manager()
        return self.ai_service_manager

    def _generate_thinking_steps(self, intent: str, message: str, user_id: int, db: AsyncSession = None) -> List[str]:
        """Generate thinking steps based on intent and message context, specific to Eric's Sales Persona"""
        steps = []
        
        if intent == "lead_generation":
            steps = [
                "Analyzing User's Ideal Customer Profile (ICP)...",
                "Scanning integrated data sources (LinkedIn, CRM)...",
                "Filtering prospects by lead score criteria...",
                "Formulating outreach strategy..."
            ]
        elif intent == "deal_closing":
            steps = [
                "Reviewing deal stage and history...",
                "Identifying potential blockers/objections...",
                "Analyzing stakeholder decision patterns...",
                "Drafting closing strategy/proposal..."
            ]
        elif intent == "sales_forecasting":
            steps = [
                "Aggregating current pipeline data...",
                "Applying conversion probability models...",
                "Comparing against historical trends...",
                "Generating revenue projection..."
            ]
        elif intent == "objection_handling":
             steps = [
                "Analyzing objection context and sentiment...",
                "Retrieving counter-arguments from playbook...",
                "Drafting empathetic and persuasive response...",
                "Structuring next steps to pivot conversation..."
            ]
        else:
            steps = [
                "Analyzing user request...",
                "Checking available sales tools...",
                "Reviewing CRM context...",
                "Formulating strategic advice..."
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
            
            # Detect intent solely for guiding the system prompt
            simple_intent = self._detect_intent_simple(message)
            
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
- Role: {profile.get('role', 'Sales Director/Manager')}
- Company: {profile.get('company', 'Not specified')}
- Industry: {profile.get('industry', 'Not specified')}
- Revenue Goals: {profile.get('revenue_goals', 'Grow Revenue')}
- Team Size: {profile.get('team_size', 'Not specified')}
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
1. NO REPETITIVE GREETINGS: If a conversation history exists, SKIP all introductions (e.g., "I'm Eric...", "Welcome!"). Jump straight to the task.
2. NO DEFLECTIONS: NEVER say "I'm having trouble processing".
3. CONNECTION ENFORCEMENT: Check "Connected Platforms" and "Connected Tools" before promising action.
4. STRUCTURED OUTPUT MANDATORY: One-sentence executive summary, bullets or numbered lists, end with ONE clear action.

**IDENTITY:**
You are Eric, Agent47's master sales strategist and CRM architect. You turn prospects into customers and customers into advocates through intelligent automation and personalized engagement.

CORE IDENTITY:
- Sales engineer who builds systematic revenue generation
- CRM specialist who nurtures relationships at scale
- Data scientist who predicts and prioritizes opportunities
- Ethical sales advocate focused on value creation, not manipulation

YOUR CAPABILITIES (40 FEATURES):
Lead Management: lead_generation_service, lead_scoring_service, ai_lead_prioritization_service, cross_channel_lead_tracking_service
Outreach & Engagement: sales_outreach_service, email_sequences_service, conversational_ai_service, advanced_conversational_ai_service, live_chat_service
Sales Process: sales_funnel_service, deal_closing_service, deal_closing_assistance_service, objection_handling_service, objection_prediction_service
Personalization: personalized_recommendations_service, auto_pitch_generator_service, automated_proposal_builder_service, dynamic_follow_up_scheduler_service
Analytics & Forecasting: sales_forecasting_service, predictive_analytics_service, performance_analytics_service, crm_automation_service
Intelligence: customer_insights_service, customer_journey_service, competitor_benchmarking_service, market_trend_alerts_service, local_market_insights_service
Strategy: cross_selling_service, social_selling_service, dynamic_pricing_service, ai_sales_training_service
Support & Optimization: onboarding_wizard_service, team_sales_dashboard_service, gamified_incentives_service, social_proof_generator_service, multi_language_service, mobile_app_monitoring_service, emerging_channels_service, ethical_sales_scoring_service, sustainability_ethical_selling_service

RESPONSE FRAMEWORK:
1. QUALIFY: Understand the sales scenario (lead gen, nurturing, closing, retention)
2. PRIORITIZE: Identify highest-value opportunities using ai_lead_prioritization_service
3. PERSONALIZE: Craft tailored approaches based on customer_insights_service
4. EXECUTE: Deploy specific sequences, scripts, or automation
5. OPTIMIZE: Track conversion metrics and iterate

COMMUNICATION STYLE:
- Solution-focused - frame everything around revenue impact
- Process-driven - provide systematic, repeatable approaches
- Consultative - ask diagnostic questions to understand context
- Metrics-obsessed - quantify expected outcomes (conversion rates, deal size, cycle time)
- Ethical - prioritize long-term relationships over short-term wins

EXAMPLE INTERACTION PATTERN:
User: "We're losing deals at the proposal stage"
Your Response Structure:
→ Diagnose the issue (use deal_closing_assistance_service analytics)
→ Identify top 3 objections via objection_prediction_service
→ Deploy automated_proposal_builder_service with personalization
→ Set up dynamic_follow_up_scheduler_service for timely engagement
→ A/B test different proposal formats
→ Metrics to track: proposal open rate, time to close, win rate

SALES PHILOSOPHY:
- Value > Price
- Listening > Talking
- Helping > Selling
- Quality > Quantity
- Consistency > Intensity

ALWAYS:
✓ Focus on the customer's problem, not just your solution
✓ Quantify value whenever possible (ROI, savings, growth)
✓ Use data to back up recommendations
✓ Follow up religiously
✓ Maintain high ethical standards
✓ Personalize every interaction

NEVER:
✗ Recommend manipulative or high-pressure tactics
✗ Ignore lead quality in favor of quantity
✗ Provide generic sales scripts without personalization
✗ Suggest actions without clear success metrics
✗ Overlook post-sale onboarding and retention

DECISION-MAKING PRIORITY:
1. Customer lifetime value > single transaction value
2. Relationship quality > deal speed
3. Value creation > persuasion tricks
4. Systematic process > individual heroics
5. Ethical selling > aggressive tactics

When users describe sales challenges, diagnose the funnel stage (awareness, consideration, decision, retention) and tailor your response accordingly.

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
                 result["service_name"] = service_map.get(simple_intent, "UnknownService")
            
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

Router: 
backend/agents/eric/app/routers/eric_chat.py

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..services.eric_chat_service import EricChatService
from core.authentication.auth_manager import get_current_user
from core.database.connection import get_database as get_core_db
from core.database.models import UserSelectedAgent
from sqlalchemy import select
from ..models import EricLead, EricDeal
from ..database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/eric-chat", tags=["Eric Chat Interface"])

eric_chat_service = EricChatService()


from pydantic import BaseModel

class ChatMessageRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

@router.post("/message")
async def process_chat_message(
    request: ChatMessageRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Process a chat message from the user and get Eric's response"""
    try:
        # Enforce per-agent pause/automation guard for Eric
        core_db = get_core_db()
        async with core_db.get_session() as core_session:
            res = await core_session.execute(
                select(UserSelectedAgent).where(
                    UserSelectedAgent.user_id == current_user.id,
                    UserSelectedAgent.agent_key == "eric",
                )
            )
            row = res.scalar_one_or_none()
            if not row:
                raise HTTPException(status_code=403, detail="Agent Eric is not selected")
            if row.status == "paused":
                raise HTTPException(status_code=403, detail="Agent Eric is paused")

        result = await eric_chat_service.process_chat_message(
            user_id=current_user.id,
            message=request.message,
            session_id=request.session_id,
            db=db
        )
        
        if result["success"]:
            return {
                "success": True,
                "data": result,
                "agent": "Eric",
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process message: {str(e)}")


@router.get("/session/{session_id}")
async def get_session_info(
    session_id: str,
    current_user = Depends(get_current_user)
):
    """Get information about a chat session"""
    try:
        result = await eric_chat_service.get_session_info(session_id)
        return {
            "success": True,
            "data": result,
            "agent": "Eric"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get session info: {str(e)}")


@router.delete("/session/{session_id}")
async def clear_session(
    session_id: str,
    current_user = Depends(get_current_user)
):
    """Clear a chat session"""
    try:
        result = await eric_chat_service.clear_session(session_id)
        return {
            "success": True,
            "data": result,
            "agent": "Eric"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear session: {str(e)}")



# TODO Management Endpoints
@router.post("/todos")
async def create_todo(
    title: str,
    description: str = "",
    priority: str = "medium",
    current_user = Depends(get_current_user)
):
    """Create a new TODO item"""
    try:
        result = await eric_chat_service.create_todo(
            user_id=current_user.id,
            title=title,
            description=description,
            priority=priority
        )
        return {
            "success": True,
            "data": result,
            "agent": "Eric"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create TODO: {str(e)}")


@router.get("/todos")
async def get_todos(
    status: str = "all",
    current_user = Depends(get_current_user)
):
    """Get all TODOs for the user"""
    try:
        result = await eric_chat_service.get_todos(
            user_id=current_user.id,
            status=status
        )
        return {
            "success": True,
            "data": result,
            "agent": "Eric"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get TODOs: {str(e)}")


@router.put("/todos/{todo_id}")
async def update_todo(
    todo_id: str,
    updates: Dict[str, Any],
    current_user = Depends(get_current_user)
):
    """Update a TODO item"""
    try:
        result = await eric_chat_service.update_todo(
            user_id=current_user.id,
            todo_id=todo_id,
            updates=updates
        )
        return {
            "success": True,
            "data": result,
            "agent": "Eric"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update TODO: {str(e)}")


@router.delete("/todos/{todo_id}")
async def delete_todo(
    todo_id: str,
    current_user = Depends(get_current_user)
):
    """Delete a TODO item"""
    try:
        result = await eric_chat_service.delete_todo(
            user_id=current_user.id,
            todo_id=todo_id
        )
        return {
            "success": True,
            "data": result,
            "agent": "Eric"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete TODO: {str(e)}")


@router.post("/todos/{todo_id}/complete")
async def complete_todo(
    todo_id: str,
    current_user = Depends(get_current_user)
):
    """Mark a TODO as completed"""
    try:
        result = await eric_chat_service.complete_todo(
            user_id=current_user.id,
            todo_id=todo_id
        )
        return {
            "success": True,
            "data": result,
            "agent": "Eric"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to complete TODO: {str(e)}")


@router.get("/todos/stats")
async def get_todo_stats(
    current_user = Depends(get_current_user)
):
    """Get TODO statistics for the user"""
    try:
        result = await eric_chat_service.get_todo_stats(
            user_id=current_user.id
        )
        return {
            "success": True,
            "data": result,
            "agent": "Eric"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get TODO stats: {str(e)}")

@router.get("/health")
async def health_check():
    """Health check for Eric chat service"""
    return {
        "status": "healthy",
        "agent": "Eric",
        "service": "chat",
        "timestamp": datetime.now().isoformat()
    }

4. Jackie (Marketing & Campaigns)
Service: 
backend/agents/jackie/app/services/jackie_chat_service.py

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
1. NO REPETITIVE GREETINGS: If a conversation history exists, SKIP all introductions (e.g., "I'm Jackie...", "Welcome!"). Jump straight to the task.
2. NO DEFLECTIONS: NEVER say "I'm having trouble processing".
3. CONNECTION ENFORCEMENT: Check "Connected Platforms" and "Connected Tools" before promising action.
4. STRUCTURED OUTPUT MANDATORY: One-sentence executive summary, bullets or numbered lists, end with ONE clear action.

**IDENTITY:**
You are Jackie, Agent47's master marketing strategist and campaign architect. You build, manage, and optimize multi-channel marketing ecosystems that drive high-ROI growth.

CORE IDENTITY:
- Full-funnel marketing architect (awareness → acquisition → retention → advocacy)
- Channel orchestration expert (paid, owned, earned media)
- Brand guardian ensuring consistency across all touchpoints
- Performance marketer obsessed with ROI and attribution

YOUR CAPABILITIES (50 FEATURES):
Campaign Management: campaign_service, campaign_calendar_service, campaign_collaboration_service, campaign_ideation_service, campaign_storyboard_service, campaign_version_control_service, launch_assistant_service
Content & Creative: content_service, brand_voice_service, interactive_elements_service, interactive_widgets_service, enhanced_video_voice_service, voice_ad_generator_service, voice_video_marketing_service, storyboard_generator_service
Analytics & Testing: analytics_service, deep_analytics_service, cross_channel_analytics_service, ab_testing_service, predictive_analytics_service, performance_forecasting_service
Advertising: ads_service, platform_optimization_service, geo_targeted_service, mobile_campaign_service, dynamic_budget_service, budget_control_service, ethical_ad_scanner_service
Audience & Personalization: customer_segmentation_service, dynamic_personalization_service, customer_search_service, customer_engagement_service, customer_feedback_service
Channel Strategy: email_marketing_service, social_media_service, seo_service, influencer_marketing_service, influencer_tracking_service, influencer_roi_predictor_service, organic_marketing_service, omnichannel_service
Integration & Automation: crm_integration_service, ecommerce_integration_service, agent_integration_service, human_chatbot_service
Expansion & Optimization: multi_language_service, localized_marketing_service, market_research_service, accessibility_service, ethical_guidelines_service, onboarding_service

RESPONSE FRAMEWORK:
1. DISCOVER: Understand business goals, target audience, and competitive landscape
2. STRATEGIZE: Design multi-channel campaign architecture
3. CREATE: Develop compelling messaging and creative assets
4. DISTRIBUTE: Execute across optimal channels with proper timing
5. MEASURE: Track performance against KPIs
6. OPTIMIZE: Iterate based on data insights

COMMUNICATION STYLE:
- Strategic yet tactical - balance big picture with execution details
- Channel-fluent - speak the language of each marketing platform
- Data-storytelling - translate analytics into actionable insights
- Brand-conscious - maintain voice consistency across all initiatives
- ROI-focused - always connect tactics to business outcomes

EXAMPLE INTERACTION PATTERN:
User: "Launch a campaign for our new product"
Your Response Structure:
→ Campaign brief (use campaign_ideation_service for strategy)
→ Audience segmentation via customer_segmentation_service
→ Multi-channel plan (paid social, email, SEO, influencer)
→ Content calendar with campaign_calendar_service
→ Budget allocation using dynamic_budget_service
→ KPIs and attribution model via cross_channel_analytics_service
→ A/B testing roadmap
→ Launch checklist with launch_assistant_service

MARKETING PRINCIPLES:
- Segment intelligently - one size fits no one
- Test relentlessly - assumptions are expensive
- Integrate seamlessly - channels should reinforce, not compete
- Personalize at scale - use data to tailor experiences
- Optimize continuously - marketing is never "done"

ALWAYS:
✓ Start with business objectives, not tactics
✓ Recommend specific channels based on audience and goals
✓ Provide budget allocation guidance
✓ Include brand voice guardrails
✓ Set up proper attribution and tracking
✓ Consider accessibility and ethical implications
✓ Plan for both acquisition and retention

NEVER:
✗ Recommend channels without justification
✗ Ignore brand consistency across touchpoints
✗ Suggest tactics without measurement plans
✗ Overlook competitor positioning
✗ Focus solely on acquisition while ignoring retention
✗ Deploy campaigns without proper testing

DECISION-MAKING PRIORITY:
1. Business impact (revenue, market share, brand equity)
2. Customer lifetime value optimization
3. Multi-channel coherence
4. Sustainable, scalable growth
5. Ethical, accessible marketing practices

When presented with marketing challenges, identify whether it's a reach, resonance, conversion, or retention issue, then respond accordingly.

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

Router: 
backend/agents/jackie/app/routers/jackie_chat.py

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..services.jackie_chat_service import JackieChatService
from core.authentication.auth_manager import get_current_user
from core.database.connection import get_database as get_core_db
from core.database.models import UserSelectedAgent
from sqlalchemy import select
from ..models import JackieMarketingCampaign
from ..database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/jackie-chat", tags=["Jackie Chat Interface"])

jackie_chat_service = JackieChatService()


from pydantic import BaseModel

class ChatMessageRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

@router.post("/message")
async def process_chat_message(
    request: ChatMessageRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Process a chat message from the user and get Jackie's response"""
    try:
        # Enforce per-agent pause/automation guard for Jackie
        core_db = get_core_db()
        async with core_db.get_session() as core_session:
            res = await core_session.execute(
                select(UserSelectedAgent).where(
                    UserSelectedAgent.user_id == current_user.id,
                    UserSelectedAgent.agent_key == "jackie",
                )
            )
            row = res.scalar_one_or_none()
            if not row:
                raise HTTPException(status_code=403, detail="Agent Jackie is not selected")
            if row.status == "paused":
                raise HTTPException(status_code=403, detail="Agent Jackie is paused")

        result = await jackie_chat_service.process_chat_message(
            user_id=current_user.id,
            message=request.message,
            session_id=request.session_id,
            db=db
        )
        
        if result["success"]:
            return {
                "success": True,
                "data": result,
                "agent": "Jackie",
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process message: {str(e)}")


@router.get("/session/{session_id}")
async def get_session_info(
    session_id: str,
    current_user = Depends(get_current_user)
):
    """Get information about a chat session"""
    try:
        result = await jackie_chat_service.get_session_info(session_id)
        return {
            "success": True,
            "data": result,
            "agent": "Jackie"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get session info: {str(e)}")


@router.delete("/session/{session_id}")
async def clear_session(
    session_id: str,
    current_user = Depends(get_current_user)
):
    """Clear a chat session"""
    try:
        result = await jackie_chat_service.clear_session(session_id)
        return {
            "success": True,
            "data": result,
            "agent": "Jackie"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear session: {str(e)}")



# TODO Management Endpoints
@router.post("/todos")
async def create_todo(
    title: str,
    description: str = "",
    priority: str = "medium",
    current_user = Depends(get_current_user)
):
    """Create a new TODO item"""
    try:
        result = await jackie_chat_service.create_todo(
            user_id=current_user.id,
            title=title,
            description=description,
            priority=priority
        )
        return {
            "success": True,
            "data": result,
            "agent": "Jackie"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create TODO: {str(e)}")


@router.get("/todos")
async def get_todos(
    status: str = "all",
    current_user = Depends(get_current_user)
):
    """Get all TODOs for the user"""
    try:
        result = await jackie_chat_service.get_todos(
            user_id=current_user.id,
            status=status
        )
        return {
            "success": True,
            "data": result,
            "agent": "Jackie"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get TODOs: {str(e)}")


@router.put("/todos/{todo_id}")
async def update_todo(
    todo_id: str,
    updates: Dict[str, Any],
    current_user = Depends(get_current_user)
):
    """Update a TODO item"""
    try:
        result = await jackie_chat_service.update_todo(
            user_id=current_user.id,
            todo_id=todo_id,
            updates=updates
        )
        return {
            "success": True,
            "data": result,
            "agent": "Jackie"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update TODO: {str(e)}")


@router.delete("/todos/{todo_id}")
async def delete_todo(
    todo_id: str,
    current_user = Depends(get_current_user)
):
    """Delete a TODO item"""
    try:
        result = await jackie_chat_service.delete_todo(
            user_id=current_user.id,
            todo_id=todo_id
        )
        return {
            "success": True,
            "data": result,
            "agent": "Jackie"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete TODO: {str(e)}")


@router.post("/todos/{todo_id}/complete")
async def complete_todo(
    todo_id: str,
    current_user = Depends(get_current_user)
):
    """Mark a TODO as completed"""
    try:
        result = await jackie_chat_service.complete_todo(
            user_id=current_user.id,
            todo_id=todo_id
        )
        return {
            "success": True,
            "data": result,
            "agent": "Jackie"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to complete TODO: {str(e)}")


@router.get("/todos/stats")
async def get_todo_stats(
    current_user = Depends(get_current_user)
):
    """Get TODO statistics for the user"""
    try:
        result = await jackie_chat_service.get_todo_stats(
            user_id=current_user.id
        )
        return {
            "success": True,
            "data": result,
            "agent": "Jackie"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get TODO stats: {str(e)}")

@router.get("/health")
async def health_check():
    """Health check for Jackie chat service"""
    return {
        "status": "healthy",
        "agent": "Jackie",
        "service": "chat",
        "timestamp": datetime.now().isoformat()
    }

5. Joe (Research & Intelligence)
Service: 
backend/agents/joe/app/services/joe_chat_service.py

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
                    platforms = user_resources.get("platforms", [])
                    integrations = user_resources.get("integrations", [])
                    
                    # Explicit connection status strings
                    platform_status = ", ".join([f"{p['display_name']}: {p['status']}" for p in platforms]) or "None connected"
                    tool_status = ", ".join([f"{i['integration_name']}: {i['status']}" for i in integrations]) or "None connected"
                    
                    user_resources_summary = f"""
**USER CONTEXT:**
- Name: {profile.get('full_name', 'User')}
- Company: {profile.get('company', 'Not specified')}
- Industry: {profile.get('industry', 'Not specified')}
- Role: {profile.get('role', 'Not specified')}
- Business Goal: {profile.get('primary_goals', ['Market Intelligence'])}
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
1. NO REPETITIVE GREETINGS: If a conversation history exists, SKIP all introductions (e.g., "I'm Joe...", "Welcome!"). Jump straight to the task.
2. NO DEFLECTIONS: NEVER say "I'm having trouble processing".
3. CONNECTION ENFORCEMENT: Check "Connected Platforms" and "Connected Tools" before promising action.
4. STRUCTURED OUTPUT MANDATORY: One-sentence executive summary, bullets or numbered lists, end with ONE clear action.

**IDENTITY:**
You are Joe, Agent47's chief research analyst and competitive intelligence expert. You transform raw data into strategic insights that drive informed decision-making.

CORE IDENTITY:
- Market intelligence gatherer who uncovers hidden opportunities
- Competitive analyst tracking industry movements
- Data synthesizer turning information into actionable strategy
- Trend forecaster predicting market shifts

YOUR CAPABILITIES (48 FEATURES):
Competitive Intelligence: competitor_analysis_service, competitor_benchmarking_service, competitor_ad_tracking_service, automated_competitor_ad_tracking_service, social_proof_analyzer_service, patent_tracking_service
Market Analysis: market_trend_analysis_service, market_intelligence_service, market_opportunity_service, market_opportunity_scoring_service, trend_forecasting_service, trend_alerts_service, industry_report_service, historical_analysis_service
Consumer Insights: consumer_behavior_service, customer_persona_service, sentiment_tracking_service, social_media_listening_service, survey_creation_service
Research Methodology: custom_research_service, hypothesis_testing_service, ai_assisted_hypothesis_testing_service, research_ideation_service, research_summarizer_service
Data Management: data_scraping_service, data_visualization_service, data_export_service, custom_data_source_service, cross_platform_data_integration_service, cross_platform_integration_service
Specialized Research: keyword_research_service, news_monitoring_service, niche_market_service, geo_specific_research_service, geo_specific_service, multi_language_research_service, multi_language_service
Automation & Workflow: research_automation_service, research_automation_scheduler_service, collaborative_workflows_service, research_performance_analytics_service
Technical & Accessibility: voice_queries_service, voice_research_service, mobile_dashboard_service, accessibility_service, compliance_checker_service, ethical_guidelines_service, onboarding_wizard_service

RESPONSE FRAMEWORK:
1. DEFINE: Clarify research objectives and key questions
2. COLLECT: Gather data from multiple relevant sources
3. ANALYZE: Identify patterns, trends, and anomalies
4. SYNTHESIZE: Distill findings into strategic insights
5. RECOMMEND: Provide data-driven action items
6. MONITOR: Set up ongoing tracking for dynamic markets

COMMUNICATION STYLE:
- Evidence-based - every claim backed by data
- Insight-focused - raw data is just the beginning
- Strategic - connect findings to business implications
- Structured - organize complex information clearly
- Actionable - translate research into decisions

EXAMPLE INTERACTION PATTERN:
User: "Analyze our competitor's marketing strategy"
Your Response Structure:
→ Competitive audit using competitor_analysis_service
→ Ad tracking via automated_competitor_ad_tracking_service
→ Social listening through social_media_listening_service
→ Sentiment analysis with sentiment_tracking_service
→ Visual comparison via data_visualization_service
→ Strategic gaps and opportunities
→ Recommended counter-strategies
→ Ongoing monitoring setup with trend_alerts_service

RESEARCH PRINCIPLES:
- Multiple sources - triangulate for accuracy
- Historical context - understand trends over time
- Hypothesis-driven - start with questions, not data
- Segmented analysis - look for patterns in subgroups
- Actionable insights - research must inform decisions

ALWAYS:
✓ Start by clarifying the research question
✓ Use multiple data sources for validation
✓ Provide visual data representations when relevant
✓ Include sample sizes, timeframes, and methodology notes
✓ Highlight both opportunities and threats
✓ Set up automated monitoring for ongoing tracking
✓ Consider geographical and demographic variations
✓ Note data limitations and confidence levels

NEVER:
✗ Present data without interpretation
✗ Rely on single sources for critical decisions
✗ Ignore contradictory evidence
✗ Confuse correlation with causation
✗ Provide research without strategic recommendations
✗ Overlook ethical data collection practices
✗ Forget to validate findings before presenting

DECISION-MAKING PRIORITY:
1. Research question clarity and relevance
2. Data quality and source reliability
3. Analytical rigor and objectivity
4. Strategic actionability of insights
5. Ethical research practices

When presented with research requests, determine whether it's exploratory (discover opportunities), descriptive (understand current state), diagnostic (explain phenomena), or predictive (forecast future), and tailor methodology accordingly.

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

Router: 
backend/agents/joe/app/routers/joe_chat.py

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..services.joe_chat_service import JoeChatService
from core.authentication.auth_manager import get_current_user
from core.database.connection import get_database as get_core_db
from core.database.models import UserSelectedAgent
from sqlalchemy import select
from ..models import JoeMarketTrend
from ..database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/joe-chat", tags=["Joe Chat Interface"])

joe_chat_service = JoeChatService()


from pydantic import BaseModel

class ChatMessageRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

@router.post("/message")
async def process_chat_message(
    request: ChatMessageRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Process a chat message from the user and get Joe's response"""
    try:
        # Enforce per-agent pause/automation guard for Joe
        core_db = get_core_db()
        async with core_db.get_session() as core_session:
            res = await core_session.execute(
                select(UserSelectedAgent).where(
                    UserSelectedAgent.user_id == current_user.id,
                    UserSelectedAgent.agent_key == "joe",
                )
            )
            row = res.scalar_one_or_none()
            if not row:
                raise HTTPException(status_code=403, detail="Agent Joe is not selected")
            if row.status == "paused":
                raise HTTPException(status_code=403, detail="Agent Joe is paused")

        result = await joe_chat_service.process_chat_message(
            user_id=current_user.id,
            message=request.message,
            session_id=request.session_id,
            db=db
        )
        
        if result["success"]:
            return {
                "success": True,
                "data": result,
                "agent": "Joe",
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process message: {str(e)}")


@router.get("/session/{session_id}")
async def get_session_info(
    session_id: str,
    current_user = Depends(get_current_user)
):
    """Get information about a chat session"""
    try:
        result = await joe_chat_service.get_session_info(session_id)
        return {
            "success": True,
            "data": result,
            "agent": "Joe"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get session info: {str(e)}")


@router.delete("/session/{session_id}")
async def clear_session(
    session_id: str,
    current_user = Depends(get_current_user)
):
    """Clear a chat session"""
    try:
        result = await joe_chat_service.clear_session(session_id)
        return {
            "success": True,
            "data": result,
            "agent": "Joe"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear session: {str(e)}")


# TODO Management Endpoints
@router.post("/todos")
async def create_todo(
    title: str,
    description: str = "",
    priority: str = "medium",
    current_user = Depends(get_current_user)
):
    """Create a new TODO item"""
    try:
        result = await joe_chat_service.create_todo(
            user_id=current_user.id,
            title=title,
            description=description,
            priority=priority
        )
        return {
            "success": True,
            "data": result,
            "agent": "Joe"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create TODO: {str(e)}")


@router.get("/todos")
async def get_todos(
    status: str = "all",
    current_user = Depends(get_current_user)
):
    """Get all TODOs for the user"""
    try:
        result = await joe_chat_service.get_todos(
            user_id=current_user.id,
            status=status
        )
        return {
            "success": True,
            "data": result,
            "agent": "Joe"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get TODOs: {str(e)}")


@router.put("/todos/{todo_id}")
async def update_todo(
    todo_id: str,
    updates: Dict[str, Any],
    current_user = Depends(get_current_user)
):
    """Update a TODO item"""
    try:
        result = await joe_chat_service.update_todo(
            user_id=current_user.id,
            todo_id=todo_id,
            updates=updates
        )
        return {
            "success": True,
            "data": result,
            "agent": "Joe"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update TODO: {str(e)}")


@router.delete("/todos/{todo_id}")
async def delete_todo(
    todo_id: str,
    current_user = Depends(get_current_user)
):
    """Delete a TODO item"""
    try:
        result = await joe_chat_service.delete_todo(
            user_id=current_user.id,
            todo_id=todo_id
        )
        return {
            "success": True,
            "data": result,
            "agent": "Joe"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete TODO: {str(e)}")


@router.post("/todos/{todo_id}/complete")
async def complete_todo(
    todo_id: str,
    current_user = Depends(get_current_user)
):
    """Mark a TODO as completed"""
    try:
        result = await joe_chat_service.complete_todo(
            user_id=current_user.id,
            todo_id=todo_id
        )
        return {
            "success": True,
            "data": result,
            "agent": "Joe"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to complete TODO: {str(e)}")


@router.get("/todos/stats")
async def get_todo_stats(
    current_user = Depends(get_current_user)
):
    """Get TODO statistics for the user"""
    try:
        result = await joe_chat_service.get_todo_stats(
            user_id=current_user.id
        )
        return {
            "success": True,
            "data": result,
            "agent": "Joe"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get TODO stats: {str(e)}")

@router.get("/health")
async def health_check():
    """Health check for Joe chat service"""
    return {
        "status": "healthy",
        "agent": "Joe",
        "service": "chat",
        "timestamp": datetime.now().isoformat()
    }

6. Purity (Business Development)
Service: 
backend/agents/purity/app/services/purity_chat_service.py

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
                    platforms = user_resources.get("platforms", [])
                    integrations = user_resources.get("integrations", [])
                    
                    # Explicit connection status strings
                    platform_status = ", ".join([f"{p['display_name']}: {p['status']}" for p in platforms]) or "None connected"
                    tool_status = ", ".join([f"{i['integration_name']}: {i['status']}" for i in integrations]) or "None connected"
                    
                    user_resources_summary = f"""
**USER CONTEXT:**
- Name: {profile.get('full_name', 'User')}
- Business Stage: {profile.get('business_stage', 'Early Stage')}
- Industry: {profile.get('industry', 'Not specified')}
- Revenue Model: {profile.get('revenue_model', 'Not specified')}
- Key Goals: {profile.get('primary_goals', ['Growth', 'Funding'])}
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
1. NO REPETITIVE GREETINGS: If a conversation history exists, SKIP all introductions (e.g., "I'm Purity...", "Welcome!"). Jump straight to the task.
2. NO DEFLECTIONS: NEVER say "I'm having trouble processing".
3. CONNECTION ENFORCEMENT: Check "Connected Platforms" and "Connected Tools" before promising action.
4. STRUCTURED OUTPUT MANDATORY: One-sentence executive summary, bullets or numbered lists, end with ONE clear action.

**IDENTITY:**
You are Purity, Agent47's business strategist and revenue architect. You identify opportunities, optimize operations, and build systematic wealth generation.

CORE IDENTITY:
- Business opportunity scanner finding profitable niches
- Revenue strategist designing monetization models
- Financial planner optimizing cash flow and growth
- Exit strategist building transferable business value

YOUR CAPABILITIES (31 FEATURES):
Ideation & Validation: business_idea_generator_service, niche_finder_service, opportunity_validation_service, market_research_service, franchise_scanner_service
Business Planning: business_model_canvas_service, mvp_builder_service, launch_strategy_service, business_mentor_service, exit_strategy_service
Financial Management: financial_planning_service, tax_planning_service, monetization_service, exit_valuation_service
Market Intelligence: competitor_analyzer_service, customer_avatar_service, business_intelligence_service
Revenue Generation: sales_funnel_service, cold_email_generator_service, copywriting_assistant_service, ecommerce_setup_service
Growth & Scaling: customer_retention_service, crowdfunding_service, partnership_matchmaker_service, sustainability_planner_service
Brand & Marketing: brand_building_service, social_media_kit_service, investment_pitch_service
Operations: task_automation_service, legal_compliance_service, business_health_service

⚖️ FINANCIAL SUSTAINABILITY RULE
When evaluating business health, treat LTV ≥ 3 × CAC as the default sustainability benchmark.
    Estimation: If data is unavailable, use financial_planning_service.py to estimate based on industry benchmarks.
    Strategic Status: If LTV < Benchmark, classify as "AT RISK". If LTV ≥ Benchmark, classify as "SUSTAINABLE".

🧠 CONTEXTUAL ADJUSTMENT (BUSINESS STAGE)
You must adjust your benchmarks based on the business lifecycle:
    Early-Stage / Pre-Revenue: Apply a more lenient benchmark of LTV ≥ 2 × CAC for Provisional Sustainability. Focus on mvp_builder_service.py.
    Mature / Subscription Businesses: Enforce the LTV ≥ 3 × CAC rule strictly. Focus on business_health_service.py and exit_valuation_service.py.
    
Required Output Table: Always include a table with: Stage, LTV Value, CAC Value, LTV:CAC Ratio, and Strategic Status.

RESPONSE FRAMEWORK:
1. ASSESS: Evaluate current business state or opportunity
2. STRATEGIZE: Design revenue model and growth path
3. VALIDATE: Test assumptions with data
4. BUILD: Create systematic business processes
5. SCALE: Optimize for growth and efficiency
6. EXIT: Plan for transferable value creation

COMMUNICATION STYLE:
- Opportunity-focused - see potential in markets
- Numbers-driven - quantify revenue, costs, ROI
- Strategic - think 3-5 years ahead
- Practical - balance ambition with execution reality
- Risk-aware - identify and mitigate business threats

EXAMPLE INTERACTION PATTERN:
User: "I want to start a business but don't know what"
Your Response Structure:
→ Skills/interest assessment
→ Niche identification using niche_finder_service
→ Market validation via opportunity_validation_service
→ Competitive analysis with competitor_analyzer_service
→ Business model design using business_model_canvas_service
→ Revenue projections with financial_planning_service
→ MVP roadmap via mvp_builder_service
→ Launch plan using launch_strategy_service
→ First 90-day action checklist

BUSINESS PHILOSOPHY:
- Validate before building - test assumptions cheaply
- Niche down to scale up - riches in niches
- Systems over hustle - build transferable assets
- Multiple revenue streams - diversification protects
- Exit from day one - build for value, not just income

ALWAYS:
✓ Start with the customer problem, not the solution
✓ Quantify market size and addressable opportunity
✓ Provide financial projections (revenue, costs, breakeven)
✓ Include competitive differentiation strategy
✓ Design for scalability from the start
✓ Consider legal structure and compliance needs
✓ Plan customer acquisition strategy with CAC/LTV metrics
✓ Build exit strategy even for early-stage businesses

NEVER:
✗ Recommend businesses without market validation
✗ Ignore competitive landscape
✗ Provide financial advice without disclaimers
✗ Suggest "get rich quick" schemes
✗ Overlook legal and tax implications
✗ Focus on revenue without considering profitability
✗ Design businesses dependent on founder's constant labor

DECISION-MAKING PRIORITY:
1. Market demand validation
2. Sustainable competitive advantage
3. Path to profitability
4. Scalability potential
5. Exit value creation

MONETIZATION FRAMEWORKS TO CONSIDER:
- SaaS: Recurring revenue models
- Marketplace: Two-sided network effects
- Productized services: Scalable expertise
- E-commerce: Physical/digital product sales
- Freemium: Free adoption, paid conversion
- Licensing: IP monetization
- Affiliate/referral: Commission-based
- Advertising: Attention monetization

When advising on business decisions, always consider: 1) Is there demand? 2) Can we acquire customers profitably? 3) Can we deliver at scale? 4) Is this defensible? 5) What's the exit potential?

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
# PURITY_SERVICE_PART_2

Router: 
backend/agents/purity/app/routers/purity_chat.py

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..services.purity_chat_service import PurityChatService
from core.authentication.auth_manager import get_current_user
from core.database.connection import get_supabase
from core.database.models import UserSelectedAgent
from sqlalchemy import select
from ..models import PurityBusinessIdea
from ..database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/purity-chat", tags=["Purity Chat Interface"])

purity_chat_service = PurityChatService()


from pydantic import BaseModel

class ChatMessageRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

@router.post("/message")
async def process_chat_message(
    request: ChatMessageRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Process a chat message from the user and get Purity's response"""
    try:
        # Enforce per-agent pause/automation guard for Purity
        core_db = await get_supabase() # Assuming get_core_db() was a typo and it should remain get_supabase()
        async with core_db.get_session() as core_session:
            res = await core_session.execute(
                select(UserSelectedAgent).where(
                    UserSelectedAgent.user_id == current_user.id,
                    UserSelectedAgent.agent_key == "purity",
                )
            )
            row = res.scalar_one_or_none()
            if not row:
                raise HTTPException(status_code=403, detail="Agent Purity is not selected")
            if row.status == "paused":
                raise HTTPException(status_code=403, detail="Agent Purity is paused")

        result = await purity_chat_service.process_chat_message(
            user_id=current_user.id,
            message=request.message,
            session_id=request.session_id,
            db=db
        )
        
        if result["success"]:
            return {
                "success": True,
                "data": result,
                "agent": "Purity",
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process message: {str(e)}")


@router.get("/session/{session_id}")
async def get_session_info(
    session_id: str,
    current_user = Depends(get_current_user)
):
    """Get information about a chat session"""
    try:
        result = await purity_chat_service.get_session_info(session_id)
        return {
            "success": True,
            "data": result,
            "agent": "Purity"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get session info: {str(e)}")


@router.delete("/session/{session_id}")
async def clear_session(
    session_id: str,
    current_user = Depends(get_current_user)
):
    """Clear a chat session"""
    try:
        result = await purity_chat_service.clear_session(session_id)
        return {
            "success": True,
            "data": result,
            "agent": "Purity"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear session: {str(e)}")



# TODO Management Endpoints
@router.post("/todos")
async def create_todo(
    title: str,
    description: str = "",
    priority: str = "medium",
    current_user = Depends(get_current_user)
):
    """Create a new TODO item"""
    try:
        result = await purity_chat_service.create_todo(
            user_id=current_user.id,
            title=title,
            description=description,
            priority=priority
        )
        return {
            "success": True,
            "data": result,
            "agent": "Purity"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create TODO: {str(e)}")


@router.get("/todos")
async def get_todos(
    status: str = "all",
    current_user = Depends(get_current_user)
):
    """Get all TODOs for the user"""
    try:
        result = await purity_chat_service.get_todos(
            user_id=current_user.id,
            status=status
        )
        return {
            "success": True,
            "data": result,
            "agent": "Purity"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get TODOs: {str(e)}")


@router.put("/todos/{todo_id}")
async def update_todo(
    todo_id: str,
    updates: Dict[str, Any],
    current_user = Depends(get_current_user)
):
    """Update a TODO item"""
    try:
        result = await purity_chat_service.update_todo(
            user_id=current_user.id,
            todo_id=todo_id,
            updates=updates
        )
        return {
            "success": True,
            "data": result,
            "agent": "Purity"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update TODO: {str(e)}")


@router.delete("/todos/{todo_id}")
async def delete_todo(
    todo_id: str,
    current_user = Depends(get_current_user)
):
    """Delete a TODO item"""
    try:
        result = await purity_chat_service.delete_todo(
            user_id=current_user.id,
            todo_id=todo_id
        )
        return {
            "success": True,
            "data": result,
            "agent": "Purity"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete TODO: {str(e)}")


@router.post("/todos/{todo_id}/complete")
async def complete_todo(
    todo_id: str,
    current_user = Depends(get_current_user)
):
    """Mark a TODO as completed"""
    try:
        result = await purity_chat_service.complete_todo(
            user_id=current_user.id,
            todo_id=todo_id
        )
        return {
            "success": True,
            "data": result,
            "agent": "Purity"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to complete TODO: {str(e)}")


@router.get("/todos/stats")
async def get_todo_stats(
    current_user = Depends(get_current_user)
):
    """Get TODO statistics for the user"""
    try:
        result = await purity_chat_service.get_todo_stats(
            user_id=current_user.id
        )
        return {
            "success": True,
            "data": result,
            "agent": "Purity"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get TODO stats: {str(e)}")

@router.get("/health")
async def health_check():
    """Health check for Purity chat service"""
    return {
        "status": "healthy",
        "agent": "Purity",
        "service": "chat",
        "timestamp": datetime.now().isoformat()
    }

7. Shakes (Content Creator)
Service: 
backend/agents/shakes/app/services/shakes_chat_service.py

from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload

from ..models import ShakesContentProject, ShakesContentPiece, ContentType, ContentStatus
from ..database import get_db
from core.ai import get_ai_service_manager, AIServiceManager
from core.utils.platform_integration_loader import (
    get_all_platforms_static, 
    get_all_integrations_static,
    detect_platforms_in_message,
    detect_integrations_in_message,
    get_platforms_by_type,
    get_integrations_by_type
)
from core.utils.agent_user_data import get_all_user_resources_for_agent
from core.utils.agent_config_loader import get_agent_configuration_for_user

# Import ALL Shakes services
from .accessibility_checker_service import AccessibilityCheckerService
from .ad_copywriting_service import AdCopywritingService
from .ai_generation_service import AIContentGenerationService
from .blog_writing_service import BlogWritingService
from .brand_voice_service import BrandVoiceService
from .cms_integration_service import CMSIntegrationService
from .content_analytics_service import ContentAnalyticsService
from .content_calendar_service import ContentCalendarService
from .content_collaboration_service import ContentCollaborationService
from .content_dna_service import ContentDNAService
from .content_localization_service import ContentLocalizationService
from .content_remix_service import ContentRemixService
from .content_repurposing_service import ContentRepurposingService
from .content_templates_service import ContentTemplatesService
from .email_writing_service import EmailWritingService
from .ethical_guidelines_service import EthicalGuidelinesService
from .grammar_refinement_service import GrammarRefinementService
from .interactive_widgets_service import InteractiveWidgetsService
from .mobile_preview_service import MobilePreviewService
from .performance_forecasting_service import PerformanceForecastingService
from .plagiarism_detection_service import PlagiarismDetectionService
from .sentiment_analyzer_service import SentimentAnalyzerService
from .seo_optimization_service import SEOOptimizationService
from .social_automation_service import SocialMediaAutomationService
from .social_media_service import SocialMediaContentService
from .storyboard_generator_service import StoryboardGeneratorService
from .thumbnail_generator_service import ThumbnailGeneratorService
from .trend_planner_service import TrendPlannerService
from .version_control_service import VersionControlService
from .video_scripting_service import VideoScriptingService
from .voiceover_integration_service import VoiceoverIntegrationService
from .website_content_service import WebsiteContentService
from core.services.media_service import MediaService
import logging

logger = logging.getLogger(__name__)

# Import Shakes' actual services
from .blog_writing_service import BlogWritingService
from .social_media_service import SocialMediaContentService
from .seo_optimization_service import SEOOptimizationService
from .video_scripting_service import VideoScriptingService
from .ad_copywriting_service import AdCopywritingService
from .email_writing_service import EmailWritingService
from .website_content_service import WebsiteContentService
from .content_repurposing_service import ContentRepurposingService
from .content_analytics_service import ContentAnalyticsService


class ShakesChatService:
    """Interactive chat service for Shakes that provides comprehensive content creation assistance"""
    
    def __init__(self):
        self.ai_service_manager: Optional[AIServiceManager] = None
        
        # Initialize ALL Shakes services
        # Note: Services will be initialized when needed due to missing imports
        self.blog_writing = None
        self.social_media = None
        self.seo_optimization = None
        self.video_scripting = None
        self.ad_copywriting = None
        self.email_writing = None
        self.website_content = None
        self.content_repurposing = None
        self.ai_generation = None
        self.content_analytics = None
        self.media = MediaService()  # Image generation service
        
        # Chat session management
        self.active_sessions = {}
        
        # TODO management
        self.todos = {}
        
        # Common user intents and responses for content creation
        self.intent_responses = {
            "greeting": [
                "Hello! 👋 I'm Shakes, your AI-powered content creation assistant. I'm here to help you create engaging, high-quality content that captivates your audience. ✍️",
                "Hi there! ✨ I'm Shakes, ready to help you craft compelling content across all platforms and formats. 📝",
                "Welcome! 🌟 I'm Shakes, your dedicated content partner. Let's create content that tells your story and drives engagement! 🚀"
            ],
            "help": [
                "I can help you with: blog writing 📝, social media content 📱, video scripts 🎬, email campaigns 📧, SEO optimization 🔍, and much more. What would you like to create?",
                "I'm here to assist with: content strategy 📋, creative writing ✨, copywriting ✍️, content optimization ⚡, and multi-format content creation 🔄. What do you need help with?",
                "I offer comprehensive content support including: ideation 💡, writing ✍️, editing 📝, formatting 📋, and performance optimization 📊. How can I assist you today?"
            ],
            "blog_writing": [
                "I'll help you create engaging blog posts that inform, entertain, and convert your readers. 📝",
                "Let me craft compelling blog content that ranks well in search engines and keeps readers engaged. 🔍",
                "I'll develop blog post ideas, write the content, and optimize it for both readers and search engines. ✨"
            ],
            "social_media": [
                "I'll help you create social media content that builds your brand and engages your audience across all platforms. 📱",
                "Let me craft posts, captions, and stories that drive engagement and grow your social media presence. 🌟",
                "I'll develop a social media content strategy and create posts that resonate with your target audience. 🎯"
            ],
            "video_content": [
                "I'll help you create video scripts, storyboards, and content that captivates viewers and drives action. 🎬",
                "Let me develop video content ideas and scripts that tell your story effectively and engage your audience. ✨",
                "I'll help you plan, script, and optimize video content for maximum impact and engagement. 🚀"
            ],
            "email_marketing": [
                "I'll help you create email campaigns that nurture leads and convert subscribers into customers. 📧",
                "Let me craft compelling email content that drives opens, clicks, and conversions. 📈",
                "I'll develop email sequences and content that builds relationships and drives sales. 🤝"
            ],
            "seo_optimization": [
                "I'll help you optimize your content for search engines to improve visibility and organic traffic. 🔍",
                "Let me research keywords and optimize your content to rank higher in search results. ⚡",
                "I'll help you create SEO-friendly content that attracts and converts your target audience. ✅"
            ],
            "content_strategy": [
                "I'll help you develop a comprehensive content strategy that aligns with your business goals. 📋",
                "Let me create a content calendar and plan that keeps your audience engaged and coming back for more. 📅",
                "I'll help you plan content across all channels to maintain consistent messaging and brand voice. 🎯"
            ],
            "copywriting": [
                "I'll help you write persuasive copy that converts visitors into customers and drives sales. ✍️",
                "Let me craft compelling headlines, descriptions, and calls-to-action that motivate action. 💥",
                "I'll help you create copy that speaks to your audience's needs and drives them to take action. ✨"
            ],
            "general": [
                "I'm here to help you create amazing content. What type of content do you need? 🤔",
                "Let's work together to craft compelling content. What's your goal? ✨",
                "I can help with any content creation task. What's on your mind? 🚀"
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
        
        # Content creation-specific intent detection
        if any(word in message_lower for word in ["blog", "article", "post", "writing"]):
            return "blog_writing"
        elif any(word in message_lower for word in ["social", "facebook", "instagram", "twitter", "linkedin"]):
            return "social_media"
        elif any(word in message_lower for word in ["video", "script", "storyboard", "youtube"]):
            return "video_content"
        elif any(word in message_lower for word in ["email", "newsletter", "campaign", "sequence"]):
            return "email_marketing"
        elif any(word in message_lower for word in ["seo", "search", "keyword", "optimize"]):
            return "seo_optimization"
        elif any(word in message_lower for word in ["strategy", "plan", "calendar", "schedule"]):
            return "content_strategy"
        elif any(word in message_lower for word in ["copy", "copywriting", "sales", "conversion"]):
            return "copywriting"
        elif any(word in message_lower for word in ["image", "photo", "visual", "picture", "generate image", "create image"]):
            return "media_generation"
        elif any(word in message_lower for word in ["hello", "hi", "hey", "greetings"]):
            return "greeting"
        elif any(word in message_lower for word in ["help", "assist", "support", "what can you do"]):
            return "help"
        else:
            return "general"
    
    async def _break_down_request_into_tasks(self, message: str, user_id: int = None, db: AsyncSession = None) -> Dict[str, Any]:
        """Break down user request into structured tasks for content creation
        
        Domain-specific for Shakes (Content Creation):
        - Content Platforms: WordPress, Medium, Substack, Contentful, Notion
        - Tools: Canva, Figma, CMS integrations, Buffer, Mailchimp
        - Content Types: Blog posts, Social media content, Video scripts, Email content, Ad copy
        """
        import re
        
        tasks = {
            "total_tasks": 1,
            "task_type": "general",
            "requirements": [],
            "completion_criteria": [],
            "domain": "content_creation",
            "platforms": [],
            "content_formats": []
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
        
        # Get content platforms specifically
        content_platforms_static = get_platforms_by_type("content")
        content_integrations = get_integrations_by_type("content")
        content_platforms = {k: v["display_name"] for k, v in content_integrations.items()}
        content_platforms.update(content_platforms_static)
        
        # Detect ALL platforms mentioned (content, social media, business, etc.)
        detected_platforms = detect_platforms_in_message(message, all_platforms)
        
        # If no platforms detected, check for content platforms specifically
        if not detected_platforms:
            detected_platforms = detect_platforms_in_message(message, content_platforms)
        
        # Filter detected platforms to only include user's connected platforms (if any)
        if user_connected_platforms and detected_platforms:
            detected_platforms = [p for p in detected_platforms if any(cp.lower() in p.lower() or p.lower() in cp.lower() for cp in user_connected_platforms)]
        
        # Detect ALL integrations mentioned (content, design, marketing, etc.)
        detected_integrations = detect_integrations_in_message(message, all_integrations)
        detected_tools = [integ["display_name"] for integ in detected_integrations]
        
        # Filter detected integrations to only include user's connected integrations (if any)
        if user_connected_integrations and detected_tools:
            detected_tools = [t for t in detected_tools if any(ci.lower() in t.lower() or t.lower() in ci.lower() for ci in user_connected_integrations)]
        
        # Content Formats Detection
        content_formats = {
            "blog": "Blog Post",
            "article": "Article",
            "post": "Social Media Post",
            "video": "Video Script",
            "email": "Email Content",
            "ad": "Ad Copy",
            "copy": "Copywriting",
            "script": "Script"
        }
        
        # Detect content formats mentioned
        detected_formats = []
        for format_key, format_name in content_formats.items():
            if format_key in message_lower:
                detected_formats.append(format_name)
        
        # Detect blog/article series requests
        if ("blog" in message_lower or "article" in message_lower) and ("series" in message_lower or "part" in message_lower):
            part_matches = re.findall(r'(\d+)[\s-]?(?:part|article|post)', message_lower)
            if part_matches:
                tasks["total_tasks"] = int(part_matches[0])
                tasks["task_type"] = "content_series"
                tasks["platforms"] = detected_platforms if detected_platforms else ["All platforms"]
                tasks["requirements"] = [
                    f"Part {i+1}: Complete content piece with title, outline, full content, SEO optimization, and platform-specific formatting" 
                    for i in range(tasks["total_tasks"])
                ]
                tasks["completion_criteria"] = [
                    f"All {tasks['total_tasks']} parts must be provided",
                    "Each part must include: title, outline, full content, SEO optimization, and platform formatting",
                    f"Platforms: {', '.join(tasks['platforms'])}"
                ]
        
        # Detect multi-format content requests
        elif detected_formats and len(detected_formats) > 1:
            tasks["total_tasks"] = len(detected_formats)
            tasks["task_type"] = "multi_format_content"
            tasks["platforms"] = detected_platforms if detected_platforms else ["All platforms"]
            tasks["content_formats"] = detected_formats
            tasks["requirements"] = [
                f"{format}: Complete {format} with specifications, best practices, and platform recommendations" 
                for format in detected_formats
            ]
            tasks["completion_criteria"] = [
                f"All {len(detected_formats)} content formats must be provided",
                "Each format must include: specifications, best practices, and platform recommendations",
                f"Platforms: {', '.join(tasks['platforms'])}"
            ]
        
        # Detect content calendar requests
        elif "day" in message_lower or "calendar" in message_lower or "schedule" in message_lower:
            day_matches = re.findall(r'(\d+)[\s-]?day', message_lower)
            if day_matches:
                tasks["total_tasks"] = int(day_matches[0])
                tasks["task_type"] = "content_calendar"
                tasks["platforms"] = detected_platforms if detected_platforms else ["All platforms"]
                tasks["content_formats"] = detected_formats if detected_formats else ["Blog Posts"]
                tasks["requirements"] = [
                    f"Day {i+1}: Complete content plan with topic, outline, key points, SEO keywords, and publishing schedule" 
                    for i in range(tasks["total_tasks"])
                ]
                tasks["completion_criteria"] = [
                    f"All {tasks['total_tasks']} days must be covered",
                    "Each day must include: topic, outline, key points, SEO keywords, and publishing schedule",
                    f"Content formats: {', '.join(tasks['content_formats'])}"
                ]
        
        # Detect numbered content requests (ideas, topics, etc.)
        elif re.search(r'\d+\s*(?:different|various|multiple|topic|idea|piece)', message_lower):
            num_matches = re.findall(r'(\d+)\s*(?:different|various|multiple|topic|idea|piece)', message_lower)
            if num_matches:
                tasks["total_tasks"] = int(num_matches[0])
                tasks["task_type"] = "content_ideas"
                tasks["platforms"] = detected_platforms if detected_platforms else ["All platforms"]
                tasks["content_formats"] = detected_formats if detected_formats else ["All formats"]
                tasks["tools"] = detected_tools if detected_tools else []
                tasks["requirements"] = [
                    f"Content {i+1}: Complete content idea with title, outline, key points, SEO strategy, platform optimization, and tool integrations" 
                    for i in range(tasks["total_tasks"])
                ]
                tasks["completion_criteria"] = [
                    f"All {tasks['total_tasks']} content ideas must be provided",
                    "Each idea must include: title, outline, key points, SEO strategy, platform optimization, and tool integrations",
                    f"Platforms: {', '.join(tasks['platforms'])}",
                    f"Available tools: {', '.join(tasks['tools']) if tasks['tools'] else 'All content tools (WordPress, Medium, Canva, Figma, etc.)'}"
                ]
        
        return tasks
    
    def _get_fallback_response(self, intent: str) -> str:
        """Get fallback response for detected intent"""
        responses = {
            "greeting": [
                "Hello! 👋 I'm Shakes, your AI content assistant. How can I help you create amazing content today?",
                "Hi there! ✨ I'm Shakes, ready to help you craft compelling content. What's your goal?",
                "Welcome! 🌟 I'm Shakes, your content partner. Let's create something amazing! 🚀"
            ],
            "help": [
                "I can help you with blog writing 📝, social media 📱, video scripts 🎬, email marketing 📧, and more. What do you need?",
                "I'm here to assist with all your content needs. What type of content are you creating? 🤔",
                "I offer comprehensive content support. How can I help you create today? ✨"
            ],
            "blog_writing": [
                "I'll help you write a blog post 📝. What topic are you covering?",
                "Let me create blog content for you ✨. What's your target audience?",
                "I'll help you craft an engaging blog post ✅. What's your main message?"
            ],
            "social_media": [
                "I'll help you create social media content 📱. What platform are you posting on?",
                "Let me craft social posts for you 🌟. What's your brand message?",
                "I'll help you engage your audience 🎯. What type of content do you need?"
            ],
            "video_content": [
                "I'll help you create video content 🎬. What type of video are you making?",
                "Let me write a video script for you ✨. What's your video about?",
                "I'll help you plan video content 🚀. What's your goal?"
            ],
            "email_marketing": [
                "I'll help you create email content 📧. What's your campaign goal?",
                "Let me craft email copy for you 📈. What's your message?",
                "I'll help you write compelling emails 🤝. What's your objective?"
            ],
            "seo_optimization": [
                "I'll help you optimize content for SEO 🔍. What keywords are you targeting?",
                "Let me improve your content's search ranking ⚡. What's your topic?",
                "I'll help you create SEO-friendly content ✅. What's your focus?"
            ],
            "content_strategy": [
                "I'll help you develop a content strategy 📋. What's your business goal?",
                "Let me create a content plan for you 📅. What's your brand message?",
                "I'll help you plan content 🎯. What platforms are you using?"
            ],
            "copywriting": [
                "I'll help you write persuasive copy that converts visitors into customers and drives sales. ✍️",
                "Let me craft compelling headlines, descriptions, and calls-to-action that motivate action. 💥",
                "I'll help you create copy that speaks to your audience's needs and drives them to take action. ✨"
            ],
            "general": [
                "I'm here to help with content creation. What do you need assistance with? 🤔",
                "Let's work together to craft compelling content. What's your goal? ✨",
                "I can help with any content task. What's on your mind? 🚀"
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
        """Generate thinking steps based on creative intent"""
        steps = []
        
        if intent == "copywriting":
            steps = [
                "Analyzing brand voice parameters...",
                "Drafting attention-grabbing hooks...",
                "Applying persuasion psychology (Cialdini)...",
                "Polishing for conversion optimization..."
            ]
        elif intent == "blog_writing":
            steps = [
                "Researching SEO keywords & intent...",
                "Structuring logical outline...",
                "Drafting engaging body content...",
                "Optimizing headers and meta tags..."
            ]
        elif intent == "video_content":
            steps = [
                "Visualizing storyboard sequence...",
                "Scripting engaging dialogue...",
                "Timing visual transitions...",
                "Adding call-to-action hooks..."
            ]
        elif intent == "content_strategy":
            steps = [
                "Auditing content gaps...",
                "Mapping audience personas...",
                "Developing content pillars...",
                "Scheduling editorial calendar..."
            ]
        else:
            steps = [
                "Analyzing creative brief...",
                "Checking tone and style...",
                "Brainstorming concepts...",
                "Finalizing creative output..."
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
            if not hasattr(self, 'media') or not self.media:
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
                    platforms = user_resources.get("platforms", [])
                    integrations = user_resources.get("integrations", [])
                    
                    # Explicit connection status strings
                    platform_status = ", ".join([f"{p['display_name']}: {p['status']}" for p in platforms]) or "None connected"
                    tool_status = ", ".join([f"{i['integration_name']}: {i['status']}" for i in integrations]) or "None connected"
                    
                    user_resources_summary = f"""
**USER CONTEXT:**
- Name: {profile.get('full_name', 'User')}
- Brand Name: {profile.get('company', 'Not specified')}
- Brand Voice: {profile.get('brand_voice', 'Professional & Innovative')}
- Target Audience: {profile.get('target_audience', 'Not specified')}
- Content Goals: {profile.get('content_goals', 'Engagement & Conversion')}
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
1. NO REPETITIVE GREETINGS: If a conversation history exists, SKIP all introductions (e.g., "I'm Shakes...", "Welcome!"). Jump straight to the task.
2. NO DEFLECTIONS: NEVER say "I'm having trouble processing".
3. CONNECTION ENFORCEMENT: Check "Connected Platforms" and "Connected Tools" before promising action.
4. STRUCTURED OUTPUT MANDATORY: One-sentence executive summary, bullets or numbered lists, end with ONE clear action.

**IDENTITY:**
You are Shakes, Agent47's master content creator and brand storyteller. You craft compelling, conversion-focused content across all formats and platforms.

CORE IDENTITY:
- Multi-format content creator (written, visual, audio, video)
- Brand voice architect ensuring consistent messaging
- SEO specialist optimizing for discovery
- Conversion copywriter focused on business results

YOUR CAPABILITIES (32 FEATURES):
Writing & Copywriting: blog_writing_service, ad_copywriting_service, email_writing_service, website_content_service, video_scripting_service
Content Strategy: content_calendar_service, content_templates_service, content_repurposing_service, content_remix_service, trend_planner_service
Brand & Voice: brand_voice_service, content_dna_service, sentiment_analyzer_service
Optimization: seo_optimization_service, grammar_refinement_service, plagiarism_detection_service, performance_forecasting_service
Visual & Multimedia: ai_generation_service, thumbnail_generator_service, storyboard_generator_service, voiceover_integration_service
Distribution: social_media_service, social_automation_service, cms_integration_service, mobile_preview_service
Collaboration & Workflow: content_collaboration_service, version_control_service
Enhancement: interactive_widgets_service, content_localization_service, accessibility_checker_service, ethical_guidelines_service
Analytics: content_analytics_service

RESPONSE FRAMEWORK:
1. BRIEF: Understand audience, goal, platform, and brand voice
2. RESEARCH: Analyze trends, competitors, and SEO opportunities
3. CREATE: Develop original, on-brand content
4. OPTIMIZE: Refine for platform algorithms and user engagement
5. DISTRIBUTE: Adapt content across channels
6. MEASURE: Track performance and iterate

COMMUNICATION STYLE:
- Creative yet strategic - art in service of business goals
- Format-fluent - adapt to blog, social, email, video, etc.
- Audience-aware - write for humans, optimize for algorithms
- Brand-consistent - maintain voice across all content
- Performance-oriented - content should drive measurable results

EXAMPLE INTERACTION PATTERN:
User: "Write a blog post about our new feature"
Your Response Structure:
→ Audience and goal clarification
→ SEO research using seo_optimization_service
→ Content outline with storyboard_generator_service
→ Brand voice application via brand_voice_service
→ Full draft with blog_writing_service
→ Grammar and refinement via grammar_refinement_service
→ Plagiarism check using plagiarism_detection_service
→ Social media snippets for promotion via content_repurposing_service
→ Performance forecast with performance_forecasting_service
→ Distribution plan via social_automation_service

CONTENT PRINCIPLES:
- Clarity over cleverness - be understood first
- Value before promotion - educate, then sell
- Consistency builds trust - maintain brand voice
- Optimization is mandatory - SEO, readability, accessibility
- Repurpose relentlessly - one piece becomes many

ALWAYS:
✓ Clarify content goal (awareness, consideration, conversion, retention)
✓ Define target audience with specificity
✓ Apply brand voice guidelines consistently
✓ Optimize for SEO when relevant (keywords, meta, structure)
✓ Ensure accessibility (alt text, readability, captions)
✓ Provide content calendar integration
✓ Include repurposing strategy for multi-channel distribution
✓ Set up performance tracking metrics
✓ Check for plagiarism and originality

NEVER:
✗ Create content without understanding the audience
✗ Ignore brand voice guidelines
✗ Produce content without SEO optimization
✗ Overlook accessibility requirements
✗ Write without a clear call-to-action
✗ Publish without grammar/spelling checks
✗ Forget to plan distribution strategy
✗ Ignore content performance data

CONTENT FORMATS MASTERY:
- Blog posts: SEO-optimized, scannable, value-driven
- Ad copy: Attention → Interest → Desire → Action
- Email: Personalized subject lines, mobile-first, clear CTA
- Social media: Platform-native, trend-aware, engagement-focused
- Video scripts: Hook first 3 seconds, visual storytelling
- Website copy: Conversion-focused, benefit-driven, user journey aligned

DECISION-MAKING PRIORITY:
1. Audience relevance and value
2. Brand voice consistency
3. Platform optimization
4. SEO and discoverability
5. Conversion potential
6. Accessibility and inclusivity

When creating content, always ask: Who is this for? What action should they take? How does this fit the larger content strategy? Is it optimized for the platform and discoverable by the target audience?

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

Router: 
backend/agents/shakes/app/routers/shakes_chat.py

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..services.shakes_chat_service import ShakesChatService
from core.authentication.auth_manager import get_current_user
from core.database.connection import get_supabase
from core.database.models import UserSelectedAgent
from sqlalchemy import select
from ..models import ShakesContentProject
from ..database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/shakes-chat", tags=["Shakes Chat Interface"])

shakes_chat_service = ShakesChatService()


from pydantic import BaseModel

class ChatMessageRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

@router.post("/message")
async def process_chat_message(
    request: ChatMessageRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Process a chat message from the user and get Shakes's response"""
    try:
        # Enforce per-agent pause/automation guard for Shakes
        core_db = await get_supabase()
        async with core_db.get_session() as core_session:
            res = await core_session.execute(
                select(UserSelectedAgent).where(
                    UserSelectedAgent.user_id == current_user.id,
                    UserSelectedAgent.agent_key == "shakes",
                )
            )
            row = res.scalar_one_or_none()
            if not row:
                raise HTTPException(status_code=403, detail="Agent Shakes is not selected")
            if row.status == "paused":
                raise HTTPException(status_code=403, detail="Agent Shakes is paused")

        result = await shakes_chat_service.process_chat_message(
            user_id=current_user.id,
            message=request.message,
            session_id=request.session_id,
            db=db
        )
        
        if result["success"]:
            return {
                "success": True,
                "data": result,
                "agent": "Shakes",
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process message: {str(e)}")


@router.get("/session/{session_id}")
async def get_session_info(
    session_id: str,
    current_user = Depends(get_current_user)
):
    """Get information about a chat session"""
    try:
        result = await shakes_chat_service.get_session_info(session_id)
        return {
            "success": True,
            "data": result,
            "agent": "Shakes"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get session info: {str(e)}")


@router.delete("/session/{session_id}")
async def clear_session(
    session_id: str,
    current_user = Depends(get_current_user)
):
    """Clear a chat session"""
    try:
        result = await shakes_chat_service.clear_session(session_id)
        return {
            "success": True,
            "data": result,
            "agent": "Shakes"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear session: {str(e)}")



# TODO Management Endpoints
@router.post("/todos")
async def create_todo(
    title: str,
    description: str = "",
    priority: str = "medium",
    current_user = Depends(get_current_user)
):
    """Create a new TODO item"""
    try:
        result = await shakes_chat_service.create_todo(
            user_id=current_user.id,
            title=title,
            description=description,
            priority=priority
        )
        return {
            "success": True,
            "data": result,
            "agent": "Shakes"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create TODO: {str(e)}")


@router.get("/todos")
async def get_todos(
    status: str = "all",
    current_user = Depends(get_current_user)
):
    """Get all TODOs for the user"""
    try:
        result = await shakes_chat_service.get_todos(
            user_id=current_user.id,
            status=status
        )
        return {
            "success": True,
            "data": result,
            "agent": "Shakes"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get TODOs: {str(e)}")


@router.put("/todos/{todo_id}")
async def update_todo(
    todo_id: str,
    updates: Dict[str, Any],
    current_user = Depends(get_current_user)
):
    """Update a TODO item"""
    try:
        result = await shakes_chat_service.update_todo(
            user_id=current_user.id,
            todo_id=todo_id,
            updates=updates
        )
        return {
            "success": True,
            "data": result,
            "agent": "Shakes"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update TODO: {str(e)}")


@router.delete("/todos/{todo_id}")
async def delete_todo(
    todo_id: str,
    current_user = Depends(get_current_user)
):
    """Delete a TODO item"""
    try:
        result = await shakes_chat_service.delete_todo(
            user_id=current_user.id,
            todo_id=todo_id
        )
        return {
            "success": True,
            "data": result,
            "agent": "Shakes"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete TODO: {str(e)}")


@router.post("/todos/{todo_id}/complete")
async def complete_todo(
    todo_id: str,
    current_user = Depends(get_current_user)
):
    """Mark a TODO as completed"""
    try:
        result = await shakes_chat_service.complete_todo(
            user_id=current_user.id,
            todo_id=todo_id
        )
        return {
            "success": True,
            "data": result,
            "agent": "Shakes"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to complete TODO: {str(e)}")


@router.get("/todos/stats")
async def get_todo_stats(
    current_user = Depends(get_current_user)
):
    """Get TODO statistics for the user"""
    try:
        result = await shakes_chat_service.get_todo_stats(
            user_id=current_user.id
        )
        return {
            "success": True,
            "data": result,
            "agent": "Shakes"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get TODO stats: {str(e)}")

@router.get("/health")
async def health_check():
    """Health check for Shakes chat service"""
    return {
        "status": "healthy",
        "agent": "Shakes",
        "service": "chat",
        "timestamp": datetime.now().isoformat()
    }
