from typing import Dict, Any, List, Optional
import base64
import io
from datetime import datetime
from core.ai import get_ai_service_manager, AIServiceManager
from core.storage.s3_manager import storage_manager
from core.database.connection import get_supabase
from ..models import ScheduledPost, PostStatus
import uuid


class VoicePostsService:
    def __init__(self):
        self.ai_service_manager: Optional[AIServiceManager] = None

    async def initialize(self):
        self.ai_service_manager = await get_ai_service_manager()

    async def create_voice_post(self, user_id: int, audio_data: bytes, audio_format: str, post_config: Dict[str, Any]) -> Dict[str, Any]:
        """Convert voice recording to a polished social media post"""
        if not self.ai_service_manager:
            await self.initialize()

        # Step 1: Transcribe audio to text
        transcription = await self._transcribe_audio(audio_data, audio_format)
        if not transcription.get("success"):
            return {"success": False, "error": "Transcription failed"}

        raw_text = transcription.get("text", "")
        
        # Step 2: Enhance and polish the text
        enhanced_text = await self._enhance_text(raw_text, post_config)
        
        # Step 3: Generate hashtags
        hashtags = await self._generate_hashtags(enhanced_text, post_config)
        
        # Step 4: Create scheduled post
        scheduled_post = await self._create_scheduled_post(user_id, enhanced_text, hashtags, post_config)
        
        return {
            "success": True,
            "transcription": raw_text,
            "enhanced_text": enhanced_text,
            "hashtags": hashtags,
            "scheduled_post_id": scheduled_post.get("id"),
            "status": scheduled_post.get("status")
        }

    async def _transcribe_audio(self, audio_data: bytes, audio_format: str) -> Dict[str, Any]:
        """Transcribe audio using Groq STT"""
        try:
            if not self.ai_service_manager:
                await self.initialize()
            
            # Use AI service manager for transcription (Groq STT)
            result = await self.ai_service_manager.transcribe_audio(
                audio_data=audio_data,
                audio_format=audio_format,
                language=None  # Auto-detect language
            )
            
            if not result.get("success"):
                return {
                    "success": False,
                    "error": result.get("error", "Transcription failed"),
                    "text": ""
                }
            
            # Extract transcription text
            text = result.get("text", "")
            confidence = result.get("confidence", 0.0)
            detected_language = result.get("language", "unknown")
            
            return {
                "success": True,
                "text": text,
                "confidence": confidence,
                "language": detected_language,
                "model": "whisper-large-v3-turbo",
                "format": audio_format
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "text": ""
            }

    async def _enhance_text(self, raw_text: str, post_config: Dict[str, Any]) -> str:
        """Enhance and polish the transcribed text"""
        if not raw_text.strip():
            return ""

        platform = post_config.get("platform", "general")
        tone = post_config.get("tone", "professional")
        max_length = post_config.get("max_length", 280)
        
        enhancement_prompt = f"""
        Enhance this transcribed voice note into a polished social media post for {platform}:
        
        Raw text: "{raw_text}"
        
        Requirements:
        - Tone: {tone}
        - Max length: {max_length} characters
        - Fix grammar and spelling
        - Make it engaging and clear
        - Maintain the original message intent
        - Add appropriate punctuation and formatting
        
        Return only the enhanced text, no explanations.
        """

        messages = [
            {"role": "system", "content": enhancement_prompt},
            {"role": "user", "content": raw_text}
        ]
        
        response = await self.ai_service_manager.generate_text(
            messages=messages,
            max_tokens=300,
            temperature=0.7
        )
        
        enhanced = response.text_content if response.success else raw_text
        
        # Ensure it fits within character limit
        if len(enhanced) > max_length:
            enhanced = enhanced[:max_length-3] + "..."
        
        return enhanced

    async def _generate_hashtags(self, text: str, post_config: Dict[str, Any]) -> List[str]:
        """Generate relevant hashtags for the post"""
        if not text:
            return []

        platform = post_config.get("platform", "general")
        max_hashtags = post_config.get("max_hashtags", 5)
        
        hashtag_prompt = f"""
        Generate {max_hashtags} relevant hashtags for this {platform} post:
        
        Post text: "{text}"
        
        Requirements:
        - Only hashtags (no explanations)
        - Relevant to the content
        - Popular and searchable
        - Format: #hashtag1 #hashtag2 #hashtag3
        - Max {max_hashtags} hashtags
        
        Return only the hashtags separated by spaces.
        """

        messages = [
            {"role": "system", "content": hashtag_prompt},
            {"role": "user", "content": text}
        ]
        
        response = await self.ai_service_manager.generate_text(
            messages=messages,
            max_tokens=100,
            temperature=0.7
        )
        
        hashtag_text = response.text_content if response.success else ""
        
        # Extract hashtags from response
        hashtags = []
        words = hashtag_text.split()
        for word in words:
            if word.startswith("#") and len(word) > 1:
                hashtags.append(word)
            elif not word.startswith("#") and len(word) > 2:
                hashtags.append(f"#{word}")
        
        return hashtags[:max_hashtags]

    async def _create_scheduled_post(self, user_id: int, text: str, hashtags: List[str], post_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a scheduled post from the voice-generated content"""
        db = await get_supabase()
        async with db.get_session() as session:
            # Create scheduled post
            scheduled_post = ScheduledPost(
                user_id=user_id,
                idempotency_key=f"voice_post_{uuid.uuid4().hex}",
                platform_targets=post_config.get("platform_targets", ["twitter"]),
                caption=text,
                hashtags=hashtags,
                media_refs=[],
                scheduled_at=post_config.get("scheduled_at", datetime.utcnow()),
                timezone=post_config.get("timezone", "UTC"),
                status=PostStatus.scheduled
            )
            
            session.add(scheduled_post)
            await session.commit()
            
            return {
                "id": scheduled_post.id,
                "status": scheduled_post.status.value,
                "scheduled_at": scheduled_post.scheduled_at.isoformat() if scheduled_post.scheduled_at else None
            }

    async def batch_voice_posts(self, user_id: int, audio_files: List[Dict[str, Any]], batch_config: Dict[str, Any]) -> Dict[str, Any]:
        """Process multiple voice recordings in batch"""
        if not self.ai_service_manager:
            await self.initialize()

        results = []
        successful = 0
        failed = 0

        for audio_file in audio_files:
            try:
                audio_data = base64.b64decode(audio_file.get("audio_data", ""))
                audio_format = audio_file.get("format", "mp3")
                post_config = audio_file.get("post_config", {})
                
                result = await self.create_voice_post(user_id, audio_data, audio_format, post_config)
                
                if result.get("success"):
                    successful += 1
                else:
                    failed += 1
                
                results.append({
                    "file_id": audio_file.get("file_id"),
                    "result": result
                })
                
            except Exception as e:
                failed += 1
                results.append({
                    "file_id": audio_file.get("file_id"),
                    "result": {"success": False, "error": str(e)}
                })

        return {
            "success": True,
            "total_processed": len(audio_files),
            "successful": successful,
            "failed": failed,
            "results": results
        }

    async def voice_post_template(self, user_id: int, template_type: str, voice_data: bytes, audio_format: str) -> Dict[str, Any]:
        """Create voice post using predefined templates"""
        if not self.ai_service_manager:
            await self.initialize()

        # Get template configuration
        template_config = self._get_template_config(template_type)
        if not template_config:
            return {"success": False, "error": "Invalid template type"}

        # Transcribe audio
        transcription = await self._transcribe_audio(voice_data, audio_format)
        if not transcription.get("success"):
            return {"success": False, "error": "Transcription failed"}

        raw_text = transcription.get("text", "")
        
        # Apply template formatting
        formatted_text = await self._apply_template(raw_text, template_config)
        
        # Generate hashtags
        hashtags = await self._generate_hashtags(formatted_text, template_config)
        
        return {
            "success": True,
            "template_type": template_type,
            "original_text": raw_text,
            "formatted_text": formatted_text,
            "hashtags": hashtags,
            "template_config": template_config
        }

    def _get_template_config(self, template_type: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific post template"""
        templates = {
            "product_announcement": {
                "tone": "excited, professional",
                "max_length": 500,
                "max_hashtags": 8,
                "format": "announcement",
                "platform": "linkedin"
            },
            "behind_scenes": {
                "tone": "casual, authentic",
                "max_length": 300,
                "max_hashtags": 5,
                "format": "story",
                "platform": "instagram"
            },
            "industry_insight": {
                "tone": "informative, authoritative",
                "max_length": 800,
                "max_hashtags": 3,
                "format": "article",
                "platform": "linkedin"
            },
            "customer_testimonial": {
                "tone": "grateful, authentic",
                "max_length": 400,
                "max_hashtags": 6,
                "format": "testimonial",
                "platform": "twitter"
            },
            "event_promotion": {
                "tone": "energetic, inviting",
                "max_length": 600,
                "max_hashtags": 10,
                "format": "promotion",
                "platform": "facebook"
            }
        }
        
        return templates.get(template_type)

    async def _apply_template(self, text: str, template_config: Dict[str, Any]) -> str:
        """Apply template formatting to the text"""
        format_type = template_config.get("format", "general")
        tone = template_config.get("tone", "professional")
        
        formatting_prompt = f"""
        Format this text as a {format_type} post with {tone} tone:
        
        Original text: "{text}"
        
        Apply appropriate formatting:
        - Add relevant emojis if appropriate
        - Structure for readability
        - Maintain the message intent
        - Make it engaging for social media
        
        Return only the formatted text.
        """

        messages = [
            {"role": "system", "content": formatting_prompt},
            {"role": "user", "content": text}
        ]
        
        response = await self.ai_service_manager.generate_text(
            messages=messages,
            max_tokens=200,
            temperature=0.7
        )
        
        return response.text_content if response.success else text

    async def get_voice_post_history(self, user_id: int, limit: int = 20) -> Dict[str, Any]:
        """Get history of voice-generated posts"""
        db = await get_supabase()
        async with db.get_session() as session:
            from sqlalchemy import select, desc
            from ..models import ScheduledPost
            
            # Get posts that were created from voice (identified by idempotency key)
            query = select(ScheduledPost).where(
                ScheduledPost.user_id == user_id,
                ScheduledPost.idempotency_key.like("voice_post_%")
            ).order_by(desc(ScheduledPost.created_at)).limit(limit)
            
            result = await session.execute(query)
            posts = result.scalars().all()
            
            history = []
            for post in posts:
                history.append({
                    "id": post.id,
                    "caption": post.caption,
                    "hashtags": post.hashtags,
                    "status": post.status.value,
                    "created_at": post.created_at.isoformat() if post.created_at else None,
                    "scheduled_at": post.scheduled_at.isoformat() if post.scheduled_at else None
                })
            
            return {
                "success": True,
                "total_posts": len(history),
                "history": history
            }
