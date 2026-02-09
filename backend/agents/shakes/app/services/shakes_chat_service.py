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
                    temperature=0.2
                )
                
                # Log the response structure
                logger.info(f"📥 {agent_name}: Groq response type: {type(ai_response)}")
                
                # Handle response (check multiple possible keys/attributes)
                if isinstance(ai_response, dict):
                    success = ai_response.get("success", False)
                    text_content = ai_response.get("text_content") or ai_response.get("content")
                    error_msg = ai_response.get("error", "Unknown error")
                else:
                    success = getattr(ai_response, "success", False)
                    text_content = getattr(ai_response, "text_content", None) or getattr(ai_response, "content", None)
                    error_msg = getattr(ai_response, "error", "Unknown error")
                
                if success and text_content:
                    response_text = text_content
                    confidence = 0.95
                    logger.info(f"✅ {agent_name}: LLM SUCCESS - Generated {len(response_text)} characters")
                else:
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
                logger.error(f"💥 {agent_name if 'agent_name' in locals() else 'Shakes'}: EXCEPTION during LLM call: {str(e)}", exc_info=True)
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