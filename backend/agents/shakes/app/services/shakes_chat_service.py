from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload

from ..models import ContentProject, ContentPiece, ContentType, ContentStatus
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
                "Hello! I'm Shakes, your AI-powered content creation assistant. I'm here to help you create engaging, high-quality content that captivates your audience.",
                "Hi there! I'm Shakes, ready to help you craft compelling content across all platforms and formats.",
                "Welcome! I'm Shakes, your dedicated content partner. Let's create content that tells your story and drives engagement!"
            ],
            "help": [
                "I can help you with: blog writing, social media content, video scripts, email campaigns, SEO optimization, and much more. What would you like to create?",
                "I'm here to assist with: content strategy, creative writing, copywriting, content optimization, and multi-format content creation. What do you need help with?",
                "I offer comprehensive content support including: ideation, writing, editing, formatting, and performance optimization. How can I assist you today?"
            ],
            "blog_writing": [
                "I'll help you create engaging blog posts that inform, entertain, and convert your readers.",
                "Let me craft compelling blog content that ranks well in search engines and keeps readers engaged.",
                "I'll develop blog post ideas, write the content, and optimize it for both readers and search engines."
            ],
            "social_media": [
                "I'll help you create social media content that builds your brand and engages your audience across all platforms.",
                "Let me craft posts, captions, and stories that drive engagement and grow your social media presence.",
                "I'll develop a social media content strategy and create posts that resonate with your target audience."
            ],
            "video_content": [
                "I'll help you create video scripts, storyboards, and content that captivates viewers and drives action.",
                "Let me develop video content ideas and scripts that tell your story effectively and engage your audience.",
                "I'll help you plan, script, and optimize video content for maximum impact and engagement."
            ],
            "email_marketing": [
                "I'll help you create email campaigns that nurture leads and convert subscribers into customers.",
                "Let me craft compelling email content that drives opens, clicks, and conversions.",
                "I'll develop email sequences and content that builds relationships and drives sales."
            ],
            "seo_optimization": [
                "I'll help you optimize your content for search engines to improve visibility and organic traffic.",
                "Let me research keywords and optimize your content to rank higher in search results.",
                "I'll help you create SEO-friendly content that attracts and converts your target audience."
            ],
            "content_strategy": [
                "I'll help you develop a comprehensive content strategy that aligns with your business goals.",
                "Let me create a content calendar and plan that keeps your audience engaged and coming back for more.",
                "I'll help you plan content across all channels to maintain consistent messaging and brand voice."
            ],
            "copywriting": [
                "I'll help you write persuasive copy that converts visitors into customers and drives sales.",
                "Let me craft compelling headlines, descriptions, and calls-to-action that motivate action.",
                "I'll help you create copy that speaks to your audience's needs and drives them to take action."
            ],
            "general": [
                "I'm here to help you create amazing content. What type of content do you need?",
                "Let's work together to craft compelling content. What's your goal?",
                "I can help with any content creation task. What do you need assistance with?"
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
            import logging
            logger = logging.getLogger(__name__)
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
                "Hello! I'm Shakes, your AI content assistant. How can I help you create amazing content today?",
                "Hi there! I'm Shakes, ready to help you craft compelling content. What's your goal?",
                "Welcome! I'm Shakes, your content partner. Let's create something amazing!"
            ],
            "help": [
                "I can help you with blog writing, social media, video scripts, email marketing, and more. What do you need?",
                "I'm here to assist with all your content needs. What type of content are you creating?",
                "I offer comprehensive content support. How can I help you create today?"
            ],
            "blog_writing": [
                "I'll help you write a blog post. What topic are you covering?",
                "Let me create blog content for you. What's your target audience?",
                "I'll help you craft an engaging blog post. What's your main message?"
            ],
            "social_media": [
                "I'll help you create social media content. What platform are you posting on?",
                "Let me craft social posts for you. What's your brand message?",
                "I'll help you engage your audience. What type of content do you need?"
            ],
            "video_content": [
                "I'll help you create video content. What type of video are you making?",
                "Let me write a video script for you. What's your video about?",
                "I'll help you plan video content. What's your goal?"
            ],
            "email_marketing": [
                "I'll help you create email content. What's your campaign goal?",
                "Let me craft email copy for you. What's your message?",
                "I'll help you write compelling emails. What's your objective?"
            ],
            "seo_optimization": [
                "I'll help you optimize content for SEO. What keywords are you targeting?",
                "Let me improve your content's search ranking. What's your topic?",
                "I'll help you create SEO-friendly content. What's your focus?"
            ],
            "content_strategy": [
                "I'll help you develop a content strategy. What's your business goal?",
                "Let me create a content plan for you. What's your brand message?",
                "I'll help you plan content. What platforms are you using?"
            ],
            "copywriting": [
                "I'll help you write persuasive copy. What are you promoting?",
                "Let me craft compelling copy for you. What's your call-to-action?",
                "I'll help you create sales copy. What's your product or service?"
            ],
            "general": [
                "I'm here to help with content creation. What do you need assistance with?",
                "Let's work together on your content. What's your goal?",
                "I can help with any content task. What's on your mind?"
            ]
        }
        
        import random
        return random.choice(responses.get(intent, responses["general"]))
    
    def _generate_thinking_steps(self, intent: str, message: str, user_id: int, db: AsyncSession = None) -> List[str]:
        """Generate thinking steps based on intent and message context"""
        steps = []
        
        if intent == "content_creation":
            steps = [
                "Analyzing content requirements...",
                "Reviewing brand voice and style...",
                "Generating content ideas...",
                "Optimizing for SEO and engagement..."
            ]
        elif intent == "content_optimization":
            steps = [
                "Reviewing existing content...",
                "Analyzing performance metrics...",
                "Identifying optimization opportunities...",
                "Preparing optimization recommendations..."
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
                        agent_config = await get_agent_configuration_for_user(user_id, "shakes", db)
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
                        "content": f"""You are Shakes, an AI-powered content creation assistant specializing in comprehensive content generation and optimization.
{custom_instructions_text}
                        You help users with content creation tasks including:
                        - Blog writing and article creation
                        - Social media content and posts
                        - Video scripts and storyboards
                        - Email marketing campaigns
                        - SEO optimization and keyword research
                        - Content strategy and planning
                        - Copywriting and sales content
                        - Multi-format content creation
                        
                        Always provide creative, engaging, and well-structured content that resonates with the target audience.
                        Be innovative, persuasive, and focused on creating content that drives engagement and conversions.
                        
                        **IMPORTANT:** Use emojis and icons naturally in your responses to make them more engaging and visually appealing. Use relevant emojis like ✍️ for writing, 📝 for content, 🔍 for SEO, 💡 for ideas, ⚡ for optimization, 📊 for performance, ✅ for completion, etc. Make your responses feel modern and polished.
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
                        ai_response = f"I've generated an image for your content! 🎨\n\nYou can use this image in your blog posts, social media content, or marketing materials."
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
