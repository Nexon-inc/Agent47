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
                    temperature=0.2,
                    top_p=0.9
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
                logger.error(f"💥 {agent_name if 'agent_name' in locals() else 'Aria'}: EXCEPTION during LLM call: {str(e)}", exc_info=True)
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
