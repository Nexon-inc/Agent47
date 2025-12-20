from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload
import logging

from ..models import (
    SocialAccount, AccountGroup, BrandProfile, Campaign, 
    ScheduledPost, PublishedPost, EngagementEvent, AnalyticsSnapshot,
    PlatformEnum, PostStatus, ApprovalStatus
)
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
                "Hello! I'm Aria, your AI-powered social media management assistant. I'm here to help you manage your social media presence effectively.",
                "Hi there! I'm Aria, ready to help you optimize your social media strategy and grow your brand online.",
                "Welcome! I'm Aria, your dedicated social media management partner. Let's make your social media presence shine!"
            ],
            "help": [
                "I can help you with: account analysis, content creation, scheduling, analytics, trend monitoring, ad management, and much more. What would you like to work on?",
                "I'm here to assist with: managing multiple social accounts, creating engaging content, scheduling posts, analyzing performance, and optimizing your strategy. What do you need help with?",
                "I offer comprehensive social media management including: content creation, scheduling, analytics, trend monitoring, competitor analysis, and strategic planning. How can I assist you today?"
            ],
            "account_management": [
                "I'll analyze your connected social media accounts and provide detailed insights and recommendations for improvement.",
                "Let me scan your accounts to understand your current performance and identify opportunities for growth.",
                "I'll examine your social media presence across all platforms and give you actionable insights to optimize your strategy."
            ],
            "content_creation": [
                "I can help you create engaging content with AI-generated captions, hashtags, and even generate images. What type of content would you like to create?",
                "Let's create some amazing content! I can generate captions, suggest hashtags, create images, and help you adapt content for different platforms.",
                "I'm here to help with content creation! I can generate captions, hashtags, images, and help you repurpose content across platforms."
            ],
            "scheduling": [
                "I can help you schedule posts across all your connected platforms with optimal timing for maximum engagement.",
                "Let's get your content scheduled! I'll analyze the best posting times for each platform and schedule your posts accordingly.",
                "I'll help you schedule your content at the perfect times across all platforms to maximize reach and engagement."
            ],
            "analytics": [
                "I'll provide comprehensive analytics on your social media performance, including engagement rates, audience insights, and growth trends.",
                "Let me analyze your performance data and show you detailed insights about your audience, content performance, and growth opportunities.",
                "I'll give you deep insights into your social media performance, helping you understand what's working and where to improve."
            ],
            "trends": [
                "I'll monitor trending topics, hashtags, and conversations relevant to your brand and suggest content ideas.",
                "Let me keep you updated on the latest trends and help you create timely, relevant content that resonates with your audience.",
                "I'll track trending topics and conversations to help you stay current and create content that's relevant and engaging."
            ],
            "ads": [
                "I can help you create and manage advertising campaigns on Instagram, LinkedIn, and other platforms to boost your reach.",
                "Let's set up effective ad campaigns! I can help you create targeted ads, set budgets, and monitor performance across platforms.",
                "I'll help you create strategic ad campaigns that target your ideal audience and drive results for your business."
            ],
            "geo_campaigns": [
                "I can help you create location-specific campaigns targeting specific regions, including African countries and cities like Kenya, Nairobi, and many more.",
                "Let's create geo-targeted campaigns! I can help you design campaigns for specific regions, including popular African locations and global markets.",
                "I'll help you create campaigns that resonate with specific geographic audiences, from local markets to international regions."
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
        
        # Detect calendar/planning requests (social media calendars)
        if "day" in message_lower or "calendar" in message_lower or "schedule" in message_lower:
            day_matches = re.findall(r'(\d+)[\s-]?day', message_lower)
            if day_matches:
                tasks["total_tasks"] = int(day_matches[0])
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
                    f"Campaign must cover: {', '.join(tasks['platforms'])}"
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
                "Hello! I'm Aria, your AI-powered social media management assistant. I'm here to help you manage your social media presence effectively.",
                "Hi there! I'm Aria, ready to help you optimize your social media strategy and grow your brand online.",
                "Welcome! I'm Aria, your dedicated social media management partner. Let's make your social media presence shine!"
            ],
            "help": [
                "I can help you with: account analysis, content creation, scheduling, analytics, trend monitoring, ad management, and much more. What would you like to work on?",
                "I'm here to assist with: managing multiple social accounts, creating engaging content, scheduling posts, analyzing performance, and optimizing your strategy. What do you need help with?",
                "I offer comprehensive social media management including: content creation, scheduling, analytics, trend monitoring, competitor analysis, and strategic planning. How can I assist you today?"
            ],
            "account_management": [
                "I'll analyze your connected social media accounts and provide detailed insights and recommendations for improvement.",
                "Let me scan your accounts to understand your current performance and identify opportunities for growth.",
                "I'll examine your social media presence across all platforms and give you actionable insights to optimize your strategy."
            ],
            "content_creation": [
                "I can help you create engaging content with AI-generated captions, hashtags, and even generate images. What type of content would you like to create?",
                "Let's create some amazing content! I can generate captions, suggest hashtags, create images, and help you adapt content for different platforms.",
                "I'm here to help with content creation! I can generate captions, hashtags, images, and help you repurpose content across platforms."
            ],
            "scheduling": [
                "I can help you schedule posts across all your connected platforms with optimal timing for maximum engagement.",
                "Let's get your content scheduled! I'll analyze the best posting times for each platform and schedule your posts accordingly.",
                "I'll help you schedule your content at the perfect times across all platforms to maximize reach and engagement."
            ],
            "analytics": [
                "I'll provide comprehensive analytics on your social media performance, including engagement rates, audience insights, and growth trends.",
                "Let me analyze your performance data and show you detailed insights about your audience, content performance, and growth opportunities.",
                "I'll give you deep insights into your social media performance, helping you understand what's working and where to improve."
            ],
            "trends": [
                "I'll monitor trending topics and hashtags relevant to your industry and help you create content that capitalizes on current trends.",
                "Let me track what's trending in your niche and suggest ways to incorporate trending topics into your content strategy.",
                "I'll keep you updated on trending topics and help you create timely, relevant content that resonates with your audience."
            ],
            "ads": [
                "I can help you create and manage advertising campaigns across multiple platforms, optimize targeting, and track performance.",
                "Let's set up effective ad campaigns! I'll help you create compelling ad copy, target the right audience, and optimize for better results.",
                "I'll assist you with ad campaign management, from creation to optimization, helping you get the best ROI on your advertising spend."
            ],
            "general": [
                "I'm here to help with all aspects of social media management. Feel free to ask me about content creation, scheduling, analytics, or any other social media needs!",
                "How can I assist you with your social media strategy today? I'm ready to help with content, scheduling, analytics, or any other aspect of social media management.",
                "I'm Aria, your social media management assistant. What would you like to work on today?"
            ]
        }
        
        import random
        return random.choice(responses.get(intent, responses["general"]))
    
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
            
            # Detect intent first to determine if we need to call services
            logger = logging.getLogger(__name__)
            detected_intent = self._detect_intent_simple(message)
            logger.info(f"Aria: Detected intent: {detected_intent} for message: {message[:50]}...")
            
            # Generate thinking steps based on intent and message
            thinking_steps = self._generate_thinking_steps(detected_intent, message, user_id, db)
            
            # Try to use services for specific intents, then format with LLM
            service_result = None
            try:
                # Call appropriate service based on intent
                if detected_intent == "account_management":
                    if any(word in message.lower() for word in ["analyze", "scan", "overview", "summary", "health"]):
                        service_result = await self.account_analysis.analyze_accounts(user_id, db=db)
                
                elif detected_intent == "content_creation":
                    # Extract content creation parameters
                    if any(word in message.lower() for word in ["caption", "text", "copy", "generate", "create"]):
                        # Extract topic from message (remove common words)
                        topic_keywords = ["caption", "text", "copy", "generate", "create", "for", "about", "on"]
                        topic = message
                        for keyword in topic_keywords:
                            topic = topic.replace(keyword, "", 1)
                        topic = topic.strip()
                        if not topic:
                            topic = message  # Fallback to full message
                        
                        brief = {"topic": topic, "tone": "professional"}
                        if not self.content.ai_service_manager:
                            await self.content.initialize()
                        service_result = await self.content.generate_caption(user_id, brief)
                        if service_result.get("caption"):
                            service_result["success"] = True
                    
                    elif any(word in message.lower() for word in ["hashtag", "tag", "hashtags"]):
                        if not self.content.ai_service_manager:
                            await self.content.initialize()
                        # Extract topic for hashtags
                        topic_keywords = ["hashtag", "tag", "hashtags", "tags", "for", "about", "on"]
                        topic = message
                        for keyword in topic_keywords:
                            topic = topic.replace(keyword, "", 1)
                        topic = topic.strip()
                        if not topic:
                            topic = message
                        
                        tags = await self.content.suggest_hashtags(user_id, topic, n=10)
                        service_result = {"success": True, "hashtags": tags, "topic": topic}
                
                elif detected_intent == "content_remix":
                    # Content remix - requires original content, so provide guidance for now
                    # Can be enhanced to extract content from message
                    service_result = {"success": False, "message": "To remix content, please provide the original post content"}
                
                elif detected_intent == "media_generation":
                    # Extract image generation prompt or use context
                    prompt_keywords = ["image", "photo", "visual", "picture", "generate", "create", "for", "of", "show"]
                    prompt = message
                    for keyword in prompt_keywords:
                        prompt = prompt.replace(keyword, "", 1)
                    prompt = prompt.strip()
                    if not prompt:
                        prompt = message
                    
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
                    
                    # Generate image with user tier for model selection
                    service_result = await self.media.generate_image(
                        prompt=prompt,
                        context=message,  # Use full message as context
                        user_id=user_id,
                        user_tier=user_tier,
                        auto_generate_prompt=True  # Auto-generate better prompt from user input
                    )
                    # Add image_url to service_result for frontend
                    if service_result.get("success"):
                        service_result["image_url"] = service_result.get("url")
                
                elif detected_intent == "scheduling":
                    # Scheduling - list schedules or provide guidance
                    if any(word in message.lower() for word in ["list", "show", "view", "see", "my"]):
                        if not self.scheduling.redis:
                            await self.scheduling.initialize()
                        schedules = await self.scheduling.list_user_schedules(user_id, {})
                        service_result = {"success": True, "schedules": schedules, "count": len(schedules)}
                    else:
                        # Provide scheduling guidance
                        service_result = {"success": False, "message": "To schedule a post, provide: content, platform, and scheduled time"}
                
                elif detected_intent == "analytics":
                    # Analytics - provide guidance (service methods vary by platform)
                    service_result = {"success": False, "message": "Analytics available for connected accounts"}
                
                elif detected_intent == "trends":
                    # Extract topic/keyword for trend monitoring
                    if any(word in message.lower() for word in ["monitor", "track", "alert"]):
                        # Set up trend monitoring
                        keywords = []
                        for word in message.split():
                            if word.lower() not in ["monitor", "track", "alert", "trends", "for", "about"]:
                                keywords.append(word)
                        if keywords:
                            if not self.trend_alerts.ai_service_manager:
                                await self.trend_alerts.initialize()
                            result = await self.trend_alerts.setup_trend_monitoring(
                                user_id, keywords[:5], ["twitter", "instagram"], "daily"
                            )
                            service_result = result
                    else:
                        # Get trending topics
                        topic = message.replace("trend", "").replace("trending", "").strip()
                        if topic:
                            trend_data = await self.trend.ingest_google_trends(topic)
                            service_result = {"success": True, "trend_data": trend_data, "topic": topic}
                
                elif detected_intent == "ads":
                    # Ads - provide guidance (requires campaign data)
                    service_result = {"success": False, "message": "To create ads, provide: platform, campaign goal, target audience, and budget"}
                
                elif detected_intent == "geo_campaigns":
                    # Extract regions from message
                    regions = []
                    region_keywords = ["africa", "kenya", "nairobi", "nigeria", "lagos", "south africa", "cairo", "accra"]
                    message_lower = message.lower()
                    for region in region_keywords:
                        if region in message_lower:
                            regions.append(region)
                    
                    if regions:
                        # Would need brand_id - provide guidance
                        service_result = {"success": False, "message": f"To create geo-campaign for {regions}, I need: campaign type, content theme, and budget"}
                    else:
                        service_result = {"success": False, "message": "Specify target regions (e.g., Kenya, Nigeria, Africa)"}
                
                elif detected_intent == "engagement":
                    # Engagement boost - requires post content
                    if any(word in message.lower() for word in ["suggest", "generate", "help"]):
                        # Provide engagement guidance
                        service_result = {"success": False, "message": "To boost engagement, provide your post content and I'll suggest polls, questions, and CTAs"}
                    else:
                        service_result = {"success": False, "message": "I can help boost engagement with polls, questions, CTAs, and interactive elements"}
                
                elif detected_intent == "auto_reply":
                    # Auto-reply service - extract platform and message
                    platforms = ["instagram", "facebook", "twitter", "linkedin"]
                    detected_platform = None
                    for platform in platforms:
                        if platform in message.lower():
                            detected_platform = platform
                            break
                    if not detected_platform:
                        detected_platform = "instagram"  # Default
                    
                    # Extract the message to reply to
                    reply_text = message
                    for word in ["reply", "auto-reply", "respond", "to", "message", "comment"]:
                        reply_text = reply_text.replace(word, "", 1)
                    reply_text = reply_text.strip()
                    if not reply_text:
                        reply_text = message
                    
                    service_result = await self.engagement.auto_reply(user_id, detected_platform, reply_text)
                
                elif detected_intent == "brand":
                    # Brand service - get or update brand profile
                    if any(word in message.lower() for word in ["get", "show", "view", "my"]):
                        brand_profile = await self.brand.get_or_create_profile(user_id)
                        service_result = {
                            "success": True,
                            "brand_profile": {
                                "voice": brand_profile.voice,
                                "hashtags_bank": brand_profile.hashtags_bank,
                                "banned_keywords": brand_profile.banned_keywords
                            }
                        }
                    else:
                        service_result = {"success": False, "message": "I can help manage your brand profile, voice, and settings. What would you like to update?"}
                
                elif detected_intent == "publishing":
                    # Publisher service - handle immediate publishing
                    if any(word in message.lower() for word in ["publish", "post", "send", "now"]):
                        service_result = {"success": False, "message": "To publish immediately, provide: content, platform(s), and media (optional)"}
                    else:
                        service_result = {"success": False, "message": "I can help you publish posts immediately across your connected platforms"}
                
                elif detected_intent == "oauth":
                    # OAuth service - platform connection guidance
                    platforms = ["linkedin", "facebook", "instagram", "twitter"]
                    detected_platform = None
                    for platform in platforms:
                        if platform in message.lower():
                            detected_platform = platform
                            break
                    
                    if detected_platform:
                        service_result = {"success": False, "message": f"To connect {detected_platform}, I'll need an authorization code from the OAuth flow"}
                    else:
                        service_result = {"success": False, "message": "I can help you connect social media platforms. Which platform would you like to connect?"}
                
                elif detected_intent == "approval":
                    # Approval service - workflow guidance
                    if any(word in message.lower() for word in ["request", "create", "new"]):
                        service_result = {"success": False, "message": "To request approval, provide: scheduled post ID and reviewer emails"}
                    elif any(word in message.lower() for word in ["approve", "reject", "decide"]):
                        service_result = {"success": False, "message": "To approve/reject, provide: approval ID and decision (approve/reject)"}
                    else:
                        service_result = {"success": False, "message": "I can help manage approval workflows for your scheduled posts"}
                
                elif detected_intent == "ab_testing":
                    # A/B testing service - guidance
                    if any(word in message.lower() for word in ["winner", "best", "pick"]):
                        service_result = {"success": False, "message": "To pick a winner from A/B test variants, provide the variant data with metrics"}
                    else:
                        service_result = {"success": False, "message": "I can help with A/B testing by tracking metrics and picking winners based on performance"}
                
                elif detected_intent == "voice_post":
                    # Voice post service - guidance
                    if any(word in message.lower() for word in ["create", "make", "generate"]):
                        service_result = {"success": False, "message": "To create a voice post, upload audio data and provide post configuration"}
                    else:
                        service_result = {"success": False, "message": "I can convert voice recordings into polished social media posts with transcription, enhancement, and hashtags"}
                
                elif detected_intent == "accessibility":
                    # Accessibility service - features
                    if any(word in message.lower() for word in ["alt text", "image"]):
                        service_result = {"success": False, "message": "To generate alt text, provide image data and optional context"}
                    elif any(word in message.lower() for word in ["caption", "video"]):
                        service_result = {"success": False, "message": "To generate video captions, provide video data"}
                    elif any(word in message.lower() for word in ["enhance", "improve"]):
                        service_result = {"success": False, "message": "To enhance post accessibility, provide the post data"}
                    elif any(word in message.lower() for word in ["report", "check", "analyze"]):
                        service_result = {"success": False, "message": "To generate an accessibility report, provide the post ID"}
                    elif any(word in message.lower() for word in ["guidelines", "best practices"]):
                        # Get accessibility guidelines
                        platform = "general"
                        platforms = ["instagram", "twitter", "linkedin", "facebook"]
                        for p in platforms:
                            if p in message.lower():
                                platform = p
                                break
                        guidelines_result = await self.accessibility.get_accessibility_guidelines(platform)
                        service_result = guidelines_result
                    else:
                        service_result = {"success": False, "message": "I can help with accessibility features: alt text generation, video captions, and accessibility reports"}
                
                elif detected_intent == "advanced_analytics":
                    # Advanced analytics service
                    if "sentiment" in message.lower() or "heatmap" in message.lower():
                        # Extract platform and date range
                        platforms = ["instagram", "facebook", "twitter", "linkedin"]
                        detected_platform = "instagram"  # Default
                        for p in platforms:
                            if p in message.lower():
                                detected_platform = p
                                break
                        
                        date_range = "30d"  # Default
                        if "7d" in message.lower() or "week" in message.lower():
                            date_range = "7d"
                        elif "90d" in message.lower() or "quarter" in message.lower():
                            date_range = "90d"
                        
                        if not self.advanced_analytics.ai_service_manager:
                            await self.advanced_analytics.initialize()
                        service_result = await self.advanced_analytics.generate_sentiment_heatmap(user_id, detected_platform, date_range)
                    else:
                        service_result = {"success": False, "message": "I can provide advanced analytics including sentiment heatmaps, audience insights, and predictive analytics"}
                
                elif detected_intent == "automation":
                    # Automation service - parse automation request
                    # Extract number of days
                    days = 7  # Default
                    import re
                    days_match = re.search(r'(\d+)\s*days?', message.lower())
                    if days_match:
                        days = int(days_match.group(1))
                    else:
                        # Check for week/month patterns
                        if "week" in message.lower():
                            days = 7
                        elif "month" in message.lower():
                            days = 30
                        elif "2 weeks" in message.lower() or "two weeks" in message.lower():
                            days = 14
                    
                    # Extract platforms
                    platforms = []
                    platform_keywords = ["instagram", "facebook", "twitter", "linkedin", "tiktok", "youtube"]
                    for platform in platform_keywords:
                        if platform in message.lower():
                            platforms.append(platform)
                    if not platforms:
                        platforms = ["instagram"]  # Default
                    
                    # Extract task type and topic
                    task_type = "content_creation"  # Default
                    if any(word in message.lower() for word in ["post", "publish", "share"]):
                        task_type = "posting"
                    elif any(word in message.lower() for word in ["content", "caption", "create"]):
                        task_type = "content_creation"
                    
                    # Extract topic from message
                    topic = message
                    # Remove automation keywords
                    for keyword in ["automate", "automation", "auto", "for the next", "for next", "for", "days", "day", "schedule"]:
                        topic = re.sub(rf'\b{keyword}\b', '', topic, flags=re.IGNORECASE)
                    topic = topic.strip()
                    if not topic or len(topic) < 5:
                        topic = "social media content"  # Fallback
                    
                    # Initialize automation service
                    await self.automation.initialize()
                    
                    # Create automation
                    task_config = {
                        "topic": topic,
                        "tone": "professional",
                        "hashtag_count": 10,
                        "days": days,
                        "timezone": "UTC"
                    }
                    
                    service_result = await self.automation.create_multi_day_automation(
                        user_id=user_id,
                        task_type=task_type,
                        task_config=task_config,
                        days=days,
                        platforms=platforms,
                        db=db
                    )
                
            except Exception as service_error:
                logger.warning(f"Aria: Service call failed for {detected_intent}: {service_error}")
                service_result = None
            
            # Use LLM to format response (with service results if available)
            try:
                ai_manager = await self._get_ai_service_manager()
                
                # Build context from service results
                context_text = ""
                if service_result and service_result.get("success"):
                    context_text = f"\n\nService Results:\n{self._format_service_results(service_result, detected_intent)}"
                
                # Get user's connected resources for context
                user_resources_summary = ""
                try:
                    if db and user_id:
                        user_resources = await get_all_user_resources_for_agent(user_id, db)
                        summary = user_resources.get("summary", {})
                        platforms_count = summary.get("total_platforms", 0)
                        integrations_count = summary.get("total_integrations", 0)
                        has_website = summary.get("has_website", False)
                        
                        profile = user_resources.get('profile', {})
                        
                        # Get agent's custom configuration/tweaks
                        agent_config = None
                        custom_instructions_text = ""
                        try:
                            if db and user_id:
                                agent_config = await get_agent_configuration_for_user(user_id, "aria", db)
                                if agent_config and agent_config.get("custom_instructions"):
                                    custom_instructions_text = f"""

**CUSTOM INSTRUCTIONS / TWEAKS (STRICTLY FOLLOW THESE):**
{agent_config.get("custom_instructions")}

**CRITICAL:** You MUST strictly follow the custom instructions above. These are user-specific tweaks that override default behavior. Apply them to ALL your responses and actions.
"""
                        except Exception as e:
                            logger.warning(f"Could not fetch agent configuration: {e}")
                        
                        user_resources_summary = f"""
**USER'S PROFILE & CONNECTED RESOURCES:**
- Name: {profile.get('full_name', 'Not provided')}
- Company: {profile.get('company', profile.get('business_name', 'Not provided'))}
- Industry: {profile.get('industry', 'Not specified')}
- Role: {profile.get('role', 'Not specified')}
- Website URL: {profile.get('website_url', profile.get('business_website', 'Not provided'))}
- Location: {profile.get('location', 'Not specified')}
- Business Stage: {profile.get('business_stage', 'Not specified')}
- Connected Platforms: {platforms_count} ({', '.join([p.get('display_name', p.get('platform_name', '')) for p in user_resources.get('platforms', [])[:5]])}{'...' if platforms_count > 5 else ''})
- Connected Integrations: {integrations_count} ({', '.join([i.get('integration_name', '') for i in user_resources.get('integrations', [])[:5]])}{'...' if integrations_count > 5 else ''})
{custom_instructions_text}
**IMPORTANT:** 
- Only use platforms and integrations that the user has actually connected. Do not suggest actions for platforms/integrations that are not connected.
- Use the user's website URL, company name, industry, and business stage to provide personalized, context-aware responses.
- Reference the user's business information when relevant to make your suggestions more tailored to their specific needs.
"""
                except Exception as e:
                    logger.warning(f"Could not fetch user resources summary: {e}")
                
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

**Example structure for calendar tasks:**
- Day 1: [Full details]
- Day 2: [Full details]
- ...
- Day {tasks["total_tasks"]}: [Full details] ← MUST reach this day

Remember: Completing all {tasks["total_tasks"]} tasks is more important than providing extensive detail for fewer tasks.
"""
                
                # Prepare messages for AI processing
                messages = [
                    {
                        "role": "system",
                        "content": f"""You are Aria, an AI-powered social media management assistant specializing in comprehensive social media management.
{user_resources_summary}

Your full capabilities include:

1. **Account Management**
   - Account analysis and health checks across all platforms
   - Multi-account management and optimization
   - Brand profile management

2. **Content Services**
   - AI-generated captions and copywriting
   - Hashtag suggestions and research
   - Content remixing/repurposing for cross-platform posting
   - Image generation using AI
   - Voice post creation and transcription
   - Media upload and management

3. **Scheduling & Publishing**
   - Post scheduling with optimal timing
   - Multi-platform posting
   - Calendar management
   - Automated publishing

4. **Analytics & Insights**
   - Performance analytics and metrics
   - Advanced analytics with deep insights
   - Engagement tracking
   - A/B testing for content optimization

5. **Trend Monitoring**
   - Real-time trend tracking (Google Trends, Twitter, Reddit, SEMrush)
   - Trend alerts and notifications
   - Keyword monitoring

6. **Advertising**
   - Instagram ad campaigns (via Facebook Marketing API)
   - LinkedIn ad campaigns
   - Campaign management and optimization
   - Budget tracking

7. **Engagement**
   - Auto-reply to comments/messages
   - Engagement boost suggestions (polls, questions, CTAs)
   - Interactive content recommendations

8. **Geo-Campaigns**
   - Location-specific campaign creation
   - Regional targeting (Africa, Kenya, Nigeria, etc.)
   - Multi-region campaign strategies

9. **Engagement & Interaction**
   - Auto-reply to comments and messages with sentiment analysis
   - Engagement booster with polls, questions, CTAs
   - Interaction tracking and management

10. **Brand Management**
   - Brand profile and voice management
   - Brand guidelines enforcement
   - Banned keywords and compliance rules

11. **Publishing**
   - Immediate post publishing across platforms
   - Multi-platform publishing coordination
   - Buffer integration for scheduling

12. **Platform Connections**
   - OAuth integration for Facebook, LinkedIn, Instagram, Twitter
   - Platform authorization management
   - Token management and refresh

13. **Approval Workflows**
   - Post approval requests
   - Multi-reviewer approval system
   - Approval status tracking

14. **A/B Testing**
   - Content variant testing
   - Performance metrics tracking
   - Winner selection based on engagement

15. **Voice & Audio**
   - Voice post creation from audio recordings
   - Speech-to-text transcription
   - Audio-based content enhancement

16. **Accessibility**
   - Alt text generation for images
   - Video caption generation
   - Post accessibility enhancement
   - Accessibility reporting and guidelines

17. **Advanced Analytics**
   - Sentiment heatmaps
   - Audience insights and predictive analytics
   - Deep performance analysis

18. **Automation**
   - Multi-day content automation
   - Recurring post scheduling
   - Automated content generation
   - Hands-free social media management
   - Smart scheduling at optimal times

Always be helpful, professional, and provide actionable advice. Use service results when available to give specific, data-driven responses. When service results aren't available, provide expert guidance on how to use the features.

**Response Guidelines:**
- Be comprehensive and detailed in your responses
- For content creation requests (calendars, strategies, campaigns, plans), provide complete, actionable plans with specific examples, timelines, and step-by-step implementation details
- For analysis requests, provide thorough insights with data-driven recommendations
- For instructional requests, provide complete guides with all necessary details
- Aim for thorough, in-depth responses that fully address the user's request
- Include specific examples, actionable steps, and practical implementation guidance
- Don't summarize or truncate - provide the full, complete response the user needs
- **IMPORTANT:** Use emojis and icons naturally in your responses to make them more engaging and visually appealing. Use relevant emojis like 📅 for schedules, 📊 for analytics, ✅ for completion, 📈 for growth, 🎯 for targeting, 💡 for ideas, ⚡ for automation, 🔍 for search, etc. Make your responses feel modern and polished.
{task_instructions}
Current intent detected: {detected_intent}
{context_text if context_text else "No service results available - provide expert guidance based on the user's request."}"""
                    },
                    {
                        "role": "user",
                        "content": message
                    }
                ]
                
                logger.info(f"Aria: Attempting LLM generation (with service results: {service_result is not None})...")
                
                # Generate AI response using LLM
                # Use max_tokens from settings (12k for llama-3.3-70b-versatile)
                from core.config import settings
                ai_response = await ai_manager.generate_text(
                    messages=messages,
                    max_tokens=settings.groq.groq_max_tokens,  # Use configured max_tokens (12000)
                    temperature=0.7
                )
                
                if ai_response.success and ai_response.text_content:
                    logger.info(f"Aria: LLM response successful. Service: {ai_response.service_used}")
                    response = ai_response.text_content
                    confidence = 0.9
                else:
                    # Fallback to simple response
                    logger.warning(f"Aria: LLM response failed ({ai_response.error}), using fallback template")
                    if service_result and service_result.get("success"):
                        # Format service results directly
                        response = self._format_service_results(service_result, detected_intent)
                    else:
                        response = await self._generate_simple_response(detected_intent, message)
                    confidence = 0.8
                    
            except Exception as ai_error:
                # Fallback to simple response if AI service fails
                logger = logging.getLogger(__name__)
                logger.error(f"Aria: LLM exception occurred: {ai_error}", exc_info=True)
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
                service_map = {
                    "account_management": "AccountAnalysisService",
                    "content_creation": "ContentService",
                    "content_remix": "ContentRemixService",
                    "media_generation": "MediaService",
                    "scheduling": "SchedulingService",
                    "analytics": "AnalyticsService",
                    "advanced_analytics": "AdvancedAnalyticsService",
                    "trends": "TrendService",
                    "trend_alerts": "TrendAlertsService",
                    "ads": "AdsService",
                    "geo_campaigns": "GeoCampaignService",
                    "engagement": "EngagementBoosterService",
                    "auto_reply": "EngagementService",
                    "brand": "BrandService",
                    "publishing": "PublisherService",
                    "oauth": "OAuthService",
                    "approval": "ApprovalService",
                    "ab_testing": "ABTestingService",
                    "voice_post": "VoicePostsService",
                    "accessibility": "AccessibilityService",
                    "automation": "AutomationService"
                }
                result["service_name"] = service_map.get(detected_intent, "UnknownService")
            else:
                result["service_used"] = False
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to process chat message: {str(e)}",
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
                return f"Ad Campaign: {service_result}"
            
            elif intent == "geo_campaigns":
                return f"Geo-Campaign: {service_result}"
            
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
                    return f"""Approval Request Created:
- Approval ID: {service_result.get('approval_id')}
- Status: {service_result.get('status', 'pending')}"""
                elif "status" in service_result:
                    return f"Approval Decision: {service_result.get('status', 'unknown')}"
                else:
                    return service_result.get("message", "Approval service result")
            
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
            "ads": ["Instagram ads", "LinkedIn ads", "Campaign creation", "Ad optimization"],
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
