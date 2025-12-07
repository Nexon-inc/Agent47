from typing import Dict, Any, Optional
from backend.core.ai import get_ai_service_manager, AIServiceManager
from backend.core.storage.s3_manager import storage_manager
from backend.core.database.models import UserTier
import base64


class MediaService:
    def __init__(self):
        self.storage = storage_manager
        self.ai_service_manager: Optional[AIServiceManager] = None

    async def _get_ai_service_manager(self):
        """Get AI service manager"""
        if not self.ai_service_manager:
            self.ai_service_manager = await get_ai_service_manager()
        return self.ai_service_manager

    async def generate_image_prompt(
        self, 
        context: str, 
        user_id: Optional[int] = None,
        user_tier: Optional[UserTier] = None
    ) -> str:
        """Generate an image prompt from context using AI
        
        Args:
            context: Context or description for the image
            user_id: User ID (optional)
            user_tier: User tier (optional)
        
        Returns:
            Generated image prompt string
        """
        try:
            ai_manager = await self._get_ai_service_manager()
            
            # Create a prompt to generate an image generation prompt
            system_prompt = """You are an expert at creating detailed, high-quality image generation prompts. 
            Given a context or description, create a comprehensive prompt that will generate a beautiful, 
            professional image. Include details about style, composition, lighting, colors, and mood.
            Return only the prompt, no explanations."""
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Create an image generation prompt for: {context}"}
            ]
            
            result = await ai_manager.generate_text(
                messages=messages,
                max_tokens=200,
                temperature=0.7,
                user_id=user_id,
                user_tier=user_tier
            )
            
            if result.success and result.text_content:
                return result.text_content.strip()
            else:
                # Fallback: return the context as-is
                return context
                
        except Exception as e:
            # Fallback: return the context as-is
            return context

    async def generate_image(
        self, 
        prompt: Optional[str] = None,
        context: Optional[str] = None,
        user_id: Optional[int] = None,
        user_tier: Optional[UserTier] = None,
        width: int = 1024,
        height: int = 1024,
        auto_generate_prompt: bool = False
    ) -> Dict[str, Any]:
        """Generate images using Google Gemini via the unified AI service manager
        
        Args:
            prompt: Direct image generation prompt (optional if context provided)
            context: Context/description to generate prompt from (optional)
            user_id: User ID for tier lookup
            user_tier: User tier (FREE, STARTER, PRO) - required for tier-based model selection
            width: Image width (default: 1024)
            height: Image height (default: 1024)
            auto_generate_prompt: If True and prompt is None, generate prompt from context
        
        Returns:
            Dict with success, url, model_used, response_time_ms, or error
        """
        try:
            # If no prompt provided, generate one from context
            if not prompt and context:
                if auto_generate_prompt:
                    prompt = await self.generate_image_prompt(context, user_id, user_tier)
                else:
                    prompt = context
            
            if not prompt:
                return {
                    "success": False,
                    "error": "Either prompt or context must be provided"
                }
            
            ai_manager = await self._get_ai_service_manager()
            
            # Use the AI service manager for image generation with tier-based model selection
            result = await ai_manager.generate_image(
                prompt=prompt,
                width=width,
                height=height,
                num_images=1,
                steps=20,
                guidance_scale=7.5,
                user_id=user_id,
                user_tier=user_tier
            )
            
            if result.success and result.images:
                # Get the first image (base64 encoded)
                image_b64 = result.images[0]
                
                # Decode and upload to Supabase Storage
                raw = base64.b64decode(image_b64)
                url = self.storage.put_bytes(raw, "image/png")
                
                return {
                    "success": True,
                    "url": url,
                    "model_used": result.service_used,
                    "response_time_ms": result.response_time_ms,
                    "prompt_used": prompt
                }
            else:
                return {
                    "success": False,
                    "error": result.error or "Image generation failed"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Image generation error: {str(e)}"
            }

    async def upload_media(self, file_data: bytes, content_type: str, filename: str) -> Dict[str, Any]:
        """Upload media files to Supabase Storage"""
        try:
            url = self.storage.put_bytes(file_data, content_type, f"media/{filename}")
            return {
                "success": True,
                "url": url,
                "filename": filename,
                "content_type": content_type
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def delete_media(self, media_url: str) -> Dict[str, Any]:
        """Delete media from Supabase Storage"""
        try:
            # Extract key from URL and delete
            # Extract the file key from the Supabase Storage URL
            if "/storage/v1/object/public/" in media_url:
                key = media_url.split("/storage/v1/object/public/")[1]
                success = self.storage.delete_file(key)
                if success:
                    return {
                        "success": True,
                        "message": "Media deleted successfully"
                    }
                else:
                    return {
                        "success": False,
                        "error": "Failed to delete media file"
                    }
            else:
                return {
                    "success": False,
                    "error": "Invalid media URL format"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


