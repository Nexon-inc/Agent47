import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime
from core.ai import get_ai_service_manager, AIServiceManager
from core.integrations.integration_manager import IntegrationManager
from core.event_bus.kafka_manager import EventBus
from ..database import get_shakes_database
from ..models import ShakesContentProject, ShakesContentPiece

logger = logging.getLogger(__name__)

class VideoScriptingService:
    """Service for AI-powered video and podcast script creation with storyboarding"""
    
    def __init__(self):
        self.integration_manager = IntegrationManager()
        self.event_bus = EventBus()
        self._initialized = False
    
    async def initialize(self):
        """Initialize video scripting service"""
        if self._initialized:
            return
        
        try:
            await self.integration_manager.initialize()
            await self.event_bus.initialize()
            self._initialized = True
            logger.info("Video scripting service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize video scripting service: {e}")
            raise
    
    async def create_video_script(
        self,
        user_id: int,
        video_type: str,
        topic: str,
        target_audience: str,
        duration: int,
        tone: str,
        call_to_action: str,
        include_visuals: bool = True,
        include_music_cues: bool = True
    ) -> Dict[str, Any]:
        """Create comprehensive video script with AI-powered storytelling"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_shakes_database()
            async with db.get_session() as session:
                # Create content project
                project = ShakesContentProject(
                    user_id=user_id,
                    title=f"Video Script: {topic}",
                    description=f"AI-generated {video_type} script about {topic}",
                    content_type="video_script",
                    platform="video",
                    target_audience=target_audience,
                    tone=tone,
                    status="draft"
                )
                session.add(project)
                await session.flush()
                
                # Generate script outline
                outline_prompt = self._create_script_outline_prompt(
                    video_type, topic, target_audience, duration, tone
                )
                # Use AI Service Manager instead of NLPUtils
                ai_manager = await get_ai_service_manager()
                messages = [
                    {"role": "system", "content": "You are an AI assistant that creates video script outlines."},
                    {"role": "user", "content": outline_prompt}
                ]
                ai_response = await ai_manager.generate_text(messages=messages, max_tokens=1000, temperature=0.7)
                script_outline = ai_response.text_content if ai_response.success else ""
                
                # Generate full video script
                script_prompt = self._create_video_script_prompt(
                    video_type, topic, target_audience, duration, tone, call_to_action,
                    include_visuals, include_music_cues, script_outline
                )
                messages = [
                    {"role": "system", "content": "You are an AI assistant that creates video scripts."},
                    {"role": "user", "content": script_prompt}
                ]
                ai_response = await ai_manager.generate_text(messages=messages, max_tokens=4000, temperature=0.7)
                video_script = ai_response.text_content if ai_response.success else ""
                
                # Generate storyboard if visuals requested
                storyboard = ""
                if include_visuals:
                    storyboard_prompt = self._create_storyboard_prompt(
                        video_type, topic, duration, script_outline
                    )
                    messages = [
                        {"role": "system", "content": "You are an AI assistant that creates video storyboards."},
                        {"role": "user", "content": storyboard_prompt}
                    ]
                    ai_response = await ai_manager.generate_text(messages=messages, max_tokens=1500, temperature=0.7)
                    storyboard = ai_response.text_content if ai_response.success else ""
                
                # Generate production notes
                production_prompt = self._create_production_notes_prompt(
                    video_type, duration, include_visuals, include_music_cues
                )
                messages = [
                    {"role": "system", "content": "You are an AI assistant that creates production notes for videos."},
                    {"role": "user", "content": production_prompt}
                ]
                ai_response = await ai_manager.generate_text(messages=messages, max_tokens=1000, temperature=0.7)
                production_notes = ai_response.text_content if ai_response.success else ""
                
                # Create content piece
                content_piece = ShakesContentPiece(
                    project_id=project.id,
                    title=topic,
                    content=video_script,
                    content_type="video_script",
                    platform="video",
                    word_count=len(video_script.split()),
                    character_count=len(video_script),
                    reading_time=duration,
                    status="draft",
                    ai_generated=True
                )
                session.add(content_piece)
                await session.flush()
                
                await session.commit()
                
                # Publish event
                await self.event_bus.publish("shakes.video_script_created", {
                    "project_id": project.id,
                    "content_piece_id": content_piece.id,
                    "user_id": user_id,
                    "video_type": video_type,
                    "topic": topic,
                    "duration": duration,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                return {
                    "success": True,
                    "project_id": project.id,
                    "content_piece_id": content_piece.id,
                    "video_script": video_script,
                    "script_outline": script_outline,
                    "storyboard": storyboard,
                    "production_notes": production_notes,
                    "estimated_duration": duration,
                    "word_count": content_piece.word_count,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Video script creation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def create_podcast_script(
        self,
        user_id: int,
        podcast_type: str,
        topic: str,
        target_audience: str,
        duration: int,
        tone: str,
        include_guest_sections: bool = False,
        include_q_a: bool = False
    ) -> Dict[str, Any]:
        """Create podcast script with AI-powered content structure"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_shakes_database()
            async with db.get_session() as session:
                # Create content project
                project = ShakesContentProject(
                    user_id=user_id,
                    title=f"Podcast Script: {topic}",
                    description=f"AI-generated {podcast_type} script about {topic}",
                    content_type="podcast_script",
                    platform="podcast",
                    target_audience=target_audience,
                    tone=tone,
                    status="draft"
                )
                session.add(project)
                await session.flush()
                
                # Generate podcast outline
                outline_prompt = self._create_podcast_outline_prompt(
                    podcast_type, topic, target_audience, duration, tone,
                    include_guest_sections, include_q_a
                )
                # Use AI Service Manager instead of NLPUtils
                ai_manager = await get_ai_service_manager()
                messages = [{"role": "system", "content": "You are an AI assistant that creates podcast outlines."}, {"role": "user", "content": outline_prompt}]
                ai_response = await ai_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
                podcast_outline = ai_response.text_content if ai_response.success else ""
                
                # Generate full podcast script
                script_prompt = self._create_podcast_script_prompt(
                    podcast_type, topic, target_audience, duration, tone,
                    include_guest_sections, include_q_a, podcast_outline
                )
                messages = [{"role": "system", "content": "You are an AI assistant that creates podcast scripts."}, {"role": "user", "content": script_prompt}]
                ai_response = await ai_manager.generate_text(messages=messages, max_tokens=4000, temperature=0.7)
                podcast_script = ai_response.text_content if ai_response.success else ""
                
                # Generate episode notes
                notes_prompt = self._create_episode_notes_prompt(
                    topic, podcast_outline, include_guest_sections
                )
                messages = [{"role": "system", "content": "You are an AI assistant that creates episode notes."}, {"role": "user", "content": notes_prompt}]
                ai_response = await ai_manager.generate_text(messages=messages, max_tokens=1000, temperature=0.7)
                episode_notes = ai_response.text_content if ai_response.success else ""
                
                # Create content piece
                content_piece = ShakesContentPiece(
                    project_id=project.id,
                    title=topic,
                    content=podcast_script,
                    content_type="podcast_script",
                    platform="podcast",
                    word_count=len(podcast_script.split()),
                    character_count=len(podcast_script),
                    reading_time=duration,
                    status="draft",
                    ai_generated=True
                )
                session.add(content_piece)
                await session.flush()
                
                await session.commit()
                
                return {
                    "success": True,
                    "project_id": project.id,
                    "content_piece_id": content_piece.id,
                    "podcast_script": podcast_script,
                    "podcast_outline": podcast_outline,
                    "episode_notes": episode_notes,
                    "estimated_duration": duration,
                    "word_count": content_piece.word_count,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Podcast script creation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def enhance_script(
        self,
        content_piece_id: int,
        enhancement_type: str,
        enhancement_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enhance existing script with additional features"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_shakes_database()
            async with db.get_session() as session:
                # Get content piece
                content_result = await session.execute(
                    select(ShakesContentPiece).where(ShakesContentPiece.id == content_piece_id)
                )
                content_piece = content_result.scalar_one_or_none()
                
                if not content_piece:
                    return {"success": False, "error": "Content piece not found"}
                
                enhanced_script = content_piece.content
                
                if enhancement_type == "add_transitions":
                    enhanced_script = await self._add_transitions(enhanced_script, enhancement_params)
                elif enhancement_type == "improve_hooks":
                    enhanced_script = await self._improve_hooks(enhanced_script, enhancement_params)
                elif enhancement_type == "add_call_to_action":
                    enhanced_script = await self._add_call_to_action(enhanced_script, enhancement_params)
                elif enhancement_type == "optimize_pacing":
                    enhanced_script = await self._optimize_pacing(enhanced_script, enhancement_params)
                
                # Update content piece
                content_piece.content = enhanced_script
                content_piece.word_count = len(enhanced_script.split())
                content_piece.character_count = len(enhanced_script)
                content_piece.updated_at = datetime.utcnow()
                
                await session.commit()
                
                return {
                    "success": True,
                    "enhanced_script": enhanced_script,
                    "word_count": content_piece.word_count,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Script enhancement failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _create_script_outline_prompt(
        self, video_type: str, topic: str, target_audience: str, duration: int, tone: str
    ) -> str:
        """Create prompt for video script outline generation"""
        return f"""
        Create a detailed outline for a {video_type} video about "{topic}".
        
        Target Audience: {target_audience}
        Duration: {duration} minutes
        Tone: {tone}
        
        Include:
        1. Hook/Introduction (30 seconds)
        2. Main content sections with timing
        3. Key talking points for each section
        4. Visual elements and transitions
        5. Call-to-action placement
        6. Estimated timing for each section
        
        Format as a structured outline with clear sections and timing.
        """
    
    def _create_video_script_prompt(
        self, video_type: str, topic: str, target_audience: str, duration: int,
        tone: str, call_to_action: str, include_visuals: bool, include_music_cues: bool, script_outline: str
    ) -> str:
        """Create prompt for full video script generation"""
        return f"""
        Create a complete {video_type} video script based on this outline:
        {script_outline}
        
        Requirements:
        - Topic: {topic}
        - Target Audience: {target_audience}
        - Duration: {duration} minutes
        - Tone: {tone}
        - Call-to-Action: {call_to_action}
        - Include Visuals: {include_visuals}
        - Include Music Cues: {include_music_cues}
        
        Format the script with:
        - Clear speaker directions
        - Visual descriptions (if visuals enabled)
        - Music cues and timing (if music enabled)
        - Natural dialogue and flow
        - Proper pacing for {duration} minutes
        - Engaging hooks and transitions
        
        Write the complete video script with proper formatting and timing.
        """
    
    def _create_storyboard_prompt(
        self, video_type: str, topic: str, duration: int, script_outline: str
    ) -> str:
        """Create prompt for storyboard generation"""
        return f"""
        Create a visual storyboard for this {video_type} video:
        
        Topic: {topic}
        Duration: {duration} minutes
        Script Outline: {script_outline}
        
        Include:
        1. Scene descriptions with timing
        2. Visual elements and composition
        3. Camera angles and movements
        4. Text overlays and graphics
        5. Color schemes and mood
        6. Transition effects
        
        Format as a detailed storyboard with scene-by-scene breakdown.
        """
    
    def _create_production_notes_prompt(
        self, video_type: str, duration: int, include_visuals: bool, include_music_cues: bool
    ) -> str:
        """Create prompt for production notes generation"""
        return f"""
        Create production notes for a {video_type} video:
        
        Duration: {duration} minutes
        Include Visuals: {include_visuals}
        Include Music Cues: {include_music_cues}
        
        Include:
        1. Equipment recommendations
        2. Lighting setup suggestions
        3. Audio recording tips
        4. Visual effects requirements
        5. Music and sound design notes
        6. Post-production workflow
        7. Estimated production time
        8. Budget considerations
        
        Format as comprehensive production guidelines.
        """
    
    def _create_podcast_outline_prompt(
        self, podcast_type: str, topic: str, target_audience: str, duration: int,
        tone: str, include_guest_sections: bool, include_q_a: bool
    ) -> str:
        """Create prompt for podcast outline generation"""
        return f"""
        Create a detailed outline for a {podcast_type} podcast episode about "{topic}".
        
        Target Audience: {target_audience}
        Duration: {duration} minutes
        Tone: {tone}
        Include Guest Sections: {include_guest_sections}
        Include Q&A: {include_q_a}
        
        Include:
        1. Introduction and hook (2-3 minutes)
        2. Main content sections with timing
        3. Guest interview structure (if applicable)
        4. Q&A format and questions (if applicable)
        5. Key talking points and examples
        6. Call-to-action and conclusion
        7. Estimated timing for each section
        
        Format as a structured podcast outline with clear sections and timing.
        """
    
    def _create_podcast_script_prompt(
        self, podcast_type: str, topic: str, target_audience: str, duration: int,
        tone: str, include_guest_sections: bool, include_q_a: bool, podcast_outline: str
    ) -> str:
        """Create prompt for full podcast script generation"""
        return f"""
        Create a complete {podcast_type} podcast script based on this outline:
        {podcast_outline}
        
        Requirements:
        - Topic: {topic}
        - Target Audience: {target_audience}
        - Duration: {duration} minutes
        - Tone: {tone}
        - Include Guest Sections: {include_guest_sections}
        - Include Q&A: {include_q_a}
        
        Format the script with:
        - Natural conversation flow
        - Host dialogue and guest interactions
        - Q&A format and questions
        - Proper pacing for {duration} minutes
        - Engaging hooks and transitions
        - Call-to-action and conclusion
        
        Write the complete podcast script with proper formatting and timing.
        """
    
    def _create_episode_notes_prompt(
        self, topic: str, podcast_outline: str, include_guest_sections: bool
    ) -> str:
        """Create prompt for episode notes generation"""
        return f"""
        Create episode notes for a podcast about "{topic}":
        
        Podcast Outline: {podcast_outline}
        Include Guest Sections: {include_guest_sections}
        
        Include:
        1. Episode summary and key takeaways
        2. Main discussion points
        3. Guest information and bio (if applicable)
        4. Resources and links mentioned
        5. Follow-up questions for listeners
        6. Social media hashtags
        7. Next episode preview
        
        Format as comprehensive episode notes for listeners.
        """
    
    async def _add_transitions(self, script: str, params: Dict[str, Any]) -> str:
        """Add smooth transitions to script"""
        transition_prompt = f"""
        Add smooth transitions to this video/podcast script:
        
        {script}
        
        Transition style: {params.get('transition_style', 'smooth')}
        Transition frequency: {params.get('frequency', 'moderate')}
        
        Add natural transitions between sections to improve flow and engagement.
        """
        
        # Use AI Service Manager instead of NLPUtils
        ai_manager = await get_ai_service_manager()
        messages = [{"role": "system", "content": "You are an AI assistant that creates video script transitions."}, {"role": "user", "content": transition_prompt}]
        ai_response = await ai_manager.generate_text(messages=messages, max_tokens=1000, temperature=0.7)
        return ai_response.text_content if ai_response.success else ""
    
    async def _improve_hooks(self, script: str, params: Dict[str, Any]) -> str:
        """Improve hooks and opening sections"""
        hook_prompt = f"""
        Improve the hooks and opening sections of this script:
        
        {script}
        
        Hook type: {params.get('hook_type', 'engaging')}
        Target audience: {params.get('target_audience', 'general')}
        
        Make the opening more compelling and hook the audience immediately.
        """
        
        # Use AI Service Manager instead of NLPUtils
        ai_manager = await get_ai_service_manager()
        messages = [{"role": "system", "content": "You are an AI assistant that improves video script hooks."}, {"role": "user", "content": hook_prompt}]
        ai_response = await ai_manager.generate_text(messages=messages, max_tokens=1500, temperature=0.7)
        return ai_response.text_content if ai_response.success else ""
    
    async def _add_call_to_action(self, script: str, params: Dict[str, Any]) -> str:
        """Add compelling call-to-action to script"""
        cta_prompt = f"""
        Add a compelling call-to-action to this script:
        
        {script}
        
        CTA type: {params.get('cta_type', 'general')}
        CTA placement: {params.get('placement', 'end')}
        
        Include a clear, actionable call-to-action that encourages viewer/listener engagement.
        """
        
        # Use AI Service Manager instead of NLPUtils
        ai_manager = await get_ai_service_manager()
        messages = [{"role": "system", "content": "You are an AI assistant that creates video script call-to-action sections."}, {"role": "user", "content": cta_prompt}]
        ai_response = await ai_manager.generate_text(messages=messages, max_tokens=1000, temperature=0.7)
        return ai_response.text_content if ai_response.success else ""
    
    async def _optimize_pacing(self, script: str, params: Dict[str, Any]) -> str:
        """Optimize script pacing for better engagement"""
        pacing_prompt = f"""
        Optimize the pacing of this script for better engagement:
        
        {script}
        
        Target duration: {params.get('target_duration', 'maintain current')}
        Pacing style: {params.get('pacing_style', 'balanced')}
        
        Adjust pacing to maintain audience interest throughout the content.
        """
        
        # Use AI Service Manager instead of NLPUtils
        ai_manager = await get_ai_service_manager()
        messages = [{"role": "system", "content": "You are an AI assistant that optimizes video script pacing."}, {"role": "user", "content": pacing_prompt}]
        ai_response = await ai_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
        return ai_response.text_content if ai_response.success else ""
