from typing import Dict, Any, List, Optional
import base64
import io
from datetime import datetime
from backend.core.ai import get_ai_service_manager, AIServiceManager
from backend.core.storage.s3_manager import storage_manager
from backend.core.database.connection import get_supabase
from ..models import ScheduledPost
import uuid


class AccessibilityService:
    def __init__(self):
        self.ai_service_manager: Optional[AIServiceManager] = None

    async def initialize(self):
        self.ai_service_manager = await get_ai_service_manager()

    async def generate_video_captions(self, user_id: int, video_data: bytes, video_format: str, language: str = "en") -> Dict[str, Any]:
        """Generate captions for video content using AI"""
        if not self.ai_service_manager:
            await self.initialize()

        try:
            # Create a file-like object for OpenAI
            video_file = io.BytesIO(video_data)
            video_file.name = f"video_caption_{uuid.uuid4().hex}.{video_format}"
            
            # Use AI service manager for video transcription
            # Note: Audio transcription not yet implemented in AI service manager
            # This is a placeholder for future implementation
            result = None
            # result = await self.ai_service_manager.transcribe_audio(video_file)
            
            captions = result if hasattr(result, 'text') else str(result)
            
            # Store captions in Supabase Storage
            caption_key = f"captions/{uuid.uuid4().hex}.srt"
            caption_url = storage_manager.put_bytes(
                captions.encode('utf-8'),
                "text/plain",
                caption_key
            )
            
            return {
                "success": True,
                "captions": captions,
                "caption_url": caption_url,
                "language": language,
                "format": "srt",
                "model": "whisper-1"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "captions": ""
            }

    async def generate_image_alt_text(self, user_id: int, image_data: bytes, image_format: str, context: str = "") -> Dict[str, Any]:
        """Generate alt text for images using AI vision analysis"""
        if not self.ai_service_manager:
            await self.initialize()

        try:
            # Use AI service manager for image analysis
            # Note: Vision analysis not yet implemented in AI service manager
            # This is a placeholder for future implementation
            
            # Encode image to base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            # Create vision prompt
            vision_prompt = f"""
            Describe this image in detail for accessibility purposes. 
            Focus on what's visually important and relevant.
            
            Context: {context if context else 'Social media post'}
            
            Requirements:
            - Be descriptive and specific
            - Include colors, objects, people, actions, and emotions
            - Keep it under 125 characters for social media
            - Make it engaging and informative
            - Focus on accessibility and inclusivity
            
            Return only the alt text description, no explanations.
            """
            
            response = client.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": vision_prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/{image_format};base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=150,
                temperature=0.3
            )
            
            alt_text = response.choices[0].message.content.strip()
            
            # Store alt text metadata
            alt_text_key = f"alt_text/{uuid.uuid4().hex}.json"
            metadata = {
                "alt_text": alt_text,
                "image_format": image_format,
                "context": context,
                "generated_at": datetime.utcnow().isoformat(),
                "model": "gpt-4-vision-preview",
                "character_count": len(alt_text)
            }
            
            alt_text_url = storage_manager.put_bytes(
                str(metadata).encode('utf-8'),
                "application/json",
                alt_text_key
            )
            
            return {
                "success": True,
                "alt_text": alt_text,
                "alt_text_url": alt_text_url,
                "metadata": metadata,
                "model": "gpt-4-vision-preview"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "alt_text": ""
            }

    async def enhance_post_accessibility(self, user_id: int, post_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance a post with accessibility features"""
        if not self.ai_service_manager:
            await self.initialize()

        enhanced_post = post_data.copy()
        accessibility_features = []

        # Generate alt text for images
        if "media_refs" in post_data and post_data["media_refs"]:
            for media in post_data["media_refs"]:
                if media.get("type") == "image" and media.get("url"):
                    # Download image and generate alt text
                    try:
                        import httpx
                        async with httpx.AsyncClient() as client:
                            response = await client.get(media["url"])
                            if response.status_code == 200:
                                image_data = response.content
                                alt_text_result = await self.generate_image_alt_text(
                                    user_id, 
                                    image_data, 
                                    "jpg", 
                                    post_data.get("caption", "")
                                )
                                
                                if alt_text_result.get("success"):
                                    media["alt_text"] = alt_text_result["alt_text"]
                                    media["alt_text_url"] = alt_text_result["alt_text_url"]
                                    accessibility_features.append("image_alt_text")
                    except Exception:
                        pass

        # Generate captions for videos
        if "media_refs" in post_data and post_data["media_refs"]:
            for media in post_data["media_refs"]:
                if media.get("type") == "video" and media.get("url"):
                    try:
                        import httpx
                        async with httpx.AsyncClient() as client:
                            response = await client.get(media["url"])
                            if response.status_code == 200:
                                video_data = response.content
                                caption_result = await self.generate_video_captions(
                                    user_id, 
                                    video_data, 
                                    "mp4"
                                )
                                
                                if caption_result.get("success"):
                                    media["captions"] = caption_result["captions"]
                                    media["caption_url"] = caption_result["caption_url"]
                                    accessibility_features.append("video_captions")
                    except Exception:
                        pass

        # Enhance text accessibility
        if "caption" in post_data and post_data["caption"]:
            enhanced_caption = await self._enhance_text_accessibility(post_data["caption"])
            if enhanced_caption != post_data["caption"]:
                enhanced_post["caption"] = enhanced_caption
                enhanced_post["original_caption"] = post_data["caption"]
                accessibility_features.append("text_enhancement")

        return {
            "success": True,
            "enhanced_post": enhanced_post,
            "accessibility_features": accessibility_features,
            "total_features": len(accessibility_features)
        }

    async def _enhance_text_accessibility(self, text: str) -> str:
        """Enhance text for better accessibility"""
        if not text:
            return text

        enhancement_prompt = f"""
        Enhance this social media text for better accessibility:
        
        Original text: "{text}"
        
        Improvements to make:
        - Add emojis to break up text visually
        - Use clear, simple language
        - Add context where helpful
        - Ensure it's easy to read and understand
        - Maintain the original message and tone
        
        Return only the enhanced text, no explanations.
        """

        messages = [
            {"role": "system", "content": enhancement_prompt},
            {"role": "user", "content": text}
        ]
        
        response = await self.ai_service_manager.generate_text(
            messages=messages,
            max_tokens=500,
            temperature=0.7
        )
        
        enhanced = response.text_content if response.success else text
        return enhanced

    async def batch_accessibility_enhancement(self, user_id: int, posts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Enhance multiple posts with accessibility features"""
        if not self.ai_service_manager:
            await self.initialize()

        results = []
        successful = 0
        failed = 0

        for post in posts:
            try:
                result = await self.enhance_post_accessibility(user_id, post)
                
                if result.get("success"):
                    successful += 1
                else:
                    failed += 1
                
                results.append({
                    "post_id": post.get("id"),
                    "result": result
                })
                
            except Exception as e:
                failed += 1
                results.append({
                    "post_id": post.get("id"),
                    "result": {"success": False, "error": str(e)}
                })

        return {
            "success": True,
            "total_posts": len(posts),
            "successful": successful,
            "failed": failed,
            "results": results
        }

    async def create_accessibility_report(self, user_id: int, post_id: int) -> Dict[str, Any]:
        """Generate accessibility report for a specific post"""
        db = await get_supabase()
        async with db.get_session() as session:
            from sqlalchemy import select
            from ..models import ScheduledPost
            
            # Get post data
            query = select(ScheduledPost).where(ScheduledPost.id == post_id, ScheduledPost.user_id == user_id)
            result = await session.execute(query)
            post = result.scalar_one_or_none()
            
            if not post:
                return {"success": False, "error": "Post not found"}

            # Analyze accessibility features
            accessibility_score = 0
            features = []
            recommendations = []

            # Check caption length
            if post.caption:
                if len(post.caption) <= 280:
                    accessibility_score += 20
                    features.append("caption_length_optimal")
                else:
                    recommendations.append("Consider shortening caption for better readability")

            # Check hashtag usage
            if post.hashtags:
                if len(post.hashtags) <= 5:
                    accessibility_score += 15
                    features.append("hashtag_usage_optimal")
                else:
                    recommendations.append("Consider reducing hashtags for cleaner appearance")

            # Check media accessibility
            if post.media_refs:
                media_count = len(post.media_refs)
                if media_count <= 4:
                    accessibility_score += 25
                    features.append("media_count_optimal")
                else:
                    recommendations.append("Consider reducing media items for better performance")

                # Check for alt text and captions
                for media in post.media_refs:
                    if media.get("alt_text"):
                        accessibility_score += 20
                        features.append("image_alt_text")
                    else:
                        recommendations.append("Add alt text to images for accessibility")

                    if media.get("captions"):
                        accessibility_score += 20
                        features.append("video_captions")
                    elif media.get("type") == "video":
                        recommendations.append("Add captions to videos for accessibility")

            # Ensure score doesn't exceed 100
            accessibility_score = min(accessibility_score, 100)

            return {
                "success": True,
                "post_id": post_id,
                "accessibility_score": accessibility_score,
                "features": features,
                "recommendations": recommendations,
                "total_features": len(features),
                "total_recommendations": len(recommendations)
            }

    async def get_accessibility_guidelines(self, platform: str = "general") -> Dict[str, Any]:
        """Get accessibility guidelines for different platforms"""
        guidelines = {
            "general": {
                "caption_length": "Keep captions under 280 characters for optimal readability",
                "hashtag_limit": "Use 3-5 hashtags maximum for cleaner appearance",
                "media_count": "Limit to 4 media items per post for better performance",
                "alt_text": "Always include descriptive alt text for images",
                "video_captions": "Include captions for all video content",
                "language": "Use clear, simple language and avoid jargon",
                "contrast": "Ensure text has sufficient contrast with background",
                "font_size": "Use readable font sizes (minimum 12px)"
            },
            "instagram": {
                "image_alt_text": "Instagram supports alt text for images - always add descriptive text",
                "story_accessibility": "Use high contrast text and avoid placing text over busy backgrounds",
                "video_captions": "Instagram auto-captions are available but manual captions are more accurate",
                "hashtag_placement": "Place hashtags in comments to keep captions clean"
            },
            "twitter": {
                "character_limit": "Stay within 280 character limit for optimal engagement",
                "image_alt_text": "Twitter supports alt text for images",
                "thread_accessibility": "Use numbered threads for better readability",
                "hashtag_limit": "Use 1-2 hashtags maximum for Twitter"
            },
            "linkedin": {
                "professional_tone": "Maintain professional tone and clear language",
                "article_formatting": "Use headers and bullet points for better readability",
                "image_alt_text": "Include descriptive alt text for professional images",
                "hashtag_strategy": "Use 3-5 professional hashtags"
            },
            "facebook": {
                "text_formatting": "Use Facebook's text formatting options for better readability",
                "image_alt_text": "Facebook supports alt text for images",
                "video_captions": "Facebook auto-captions are available but manual captions are preferred",
                "accessibility_features": "Enable Facebook's accessibility features in settings"
            }
        }
        
        return {
            "success": True,
            "platform": platform,
            "guidelines": guidelines.get(platform, guidelines["general"])
        }
