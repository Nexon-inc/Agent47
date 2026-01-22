from typing import Dict, Any, List, Optional
from core.ai import get_ai_service_manager, AIServiceManager
from core.database.connection import get_supabase
from ..models import AriaPostVariant, PlatformEnum
import json


class ContentRemixService:
    def __init__(self):
        self.ai_service_manager: Optional[AIServiceManager] = None

    async def initialize(self):
        self.ai_service_manager = await get_ai_service_manager()

    async def remix_content(self, user_id: int, original_content: Dict[str, Any], target_platforms: List[str]) -> Dict[str, Any]:
        """Remix one post into multiple formats for different platforms"""
        if not self.ai_service_manager:
            await self.initialize()

        remixed_content = {}
        
        for platform in target_platforms:
            platform_enum = self._get_platform_enum(platform)
            if not platform_enum:
                continue
                
            remixed = await self._adapt_for_platform(
                original_content, 
                platform_enum, 
                user_id
            )
            remixed_content[platform] = remixed

        return {
            "success": True,
            "original_content": original_content,
            "remixed_content": remixed_content,
            "platforms_processed": list(remixed_content.keys())
        }

    async def _adapt_for_platform(self, content: Dict[str, Any], platform: PlatformEnum, user_id: int) -> Dict[str, Any]:
        """Adapt content for a specific platform"""
        platform_rules = self._get_platform_rules(platform)
        
        # Adapt caption
        adapted_caption = await self._adapt_caption(
            content.get("caption", ""),
            platform_rules,
            platform.value
        )
        
        # Adapt hashtags
        adapted_hashtags = await self._adapt_hashtags(
            content.get("hashtags", []),
            platform_rules,
            platform.value
        )
        
        # Adapt media format
        adapted_media = await self._adapt_media(
            content.get("media_refs", []),
            platform_rules,
            platform.value
        )

        return {
            "caption": adapted_caption,
            "hashtags": adapted_hashtags,
            "media_refs": adapted_media,
            "platform": platform.value,
            "character_count": len(adapted_caption),
            "hashtag_count": len(adapted_hashtags),
            "media_count": len(adapted_media)
        }

    async def _adapt_caption(self, caption: str, rules: Dict[str, Any], platform: str) -> str:
        """Adapt caption for platform-specific requirements"""
        if not caption:
            return ""

        prompt = f"""
        Adapt this social media caption for {platform} platform:
        
        Original caption: {caption}
        
        Platform rules:
        - Max characters: {rules.get('max_characters', 280)}
        - Tone: {rules.get('tone', 'professional')}
        - Call-to-action style: {rules.get('cta_style', 'subtle')}
        - Emoji usage: {rules.get('emoji_usage', 'moderate')}
        
        Return only the adapted caption, no explanations.
        """

        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": caption}
        ]
        
        response = await self.ai_service_manager.generate_text(
            messages=messages,
            max_tokens=200,
            temperature=0.7
        )
        
        adapted_caption = response.text_content if response.success else caption
        return adapted_caption[:rules.get('max_characters', 280)]

    async def _adapt_hashtags(self, hashtags: List[str], rules: Dict[str, Any], platform: str) -> List[str]:
        """Adapt hashtags for platform-specific requirements"""
        if not hashtags:
            return []

        max_hashtags = rules.get('max_hashtags', 30)
        if len(hashtags) <= max_hashtags:
            return hashtags

        # Use AI to select the most relevant hashtags
        prompt = f"""
        Select the top {max_hashtags} most relevant hashtags from this list for {platform}:
        
        Hashtags: {', '.join(hashtags)}
        
        Return only a JSON array of selected hashtags, no explanations.
        """

        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": "hashtag selection"}
        ]
        
        response = await self.ai_service_manager.generate_text(
            messages=messages,
            max_tokens=100,
            temperature=0.3
        )
        
        try:
            selected = json.loads(response.text_content) if response.success else "[]"
            return selected[:max_hashtags] if isinstance(selected, list) else hashtags[:max_hashtags]
        except:
            return hashtags[:max_hashtags]

    async def _adapt_media(self, media_refs: List[Dict[str, Any]], rules: Dict[str, Any], platform: str) -> List[Dict[str, Any]]:
        """Adapt media for platform-specific requirements"""
        if not media_refs:
            return []

        adapted_media = []
        max_media = rules.get('max_media', 10)
        
        for media in media_refs[:max_media]:
            adapted = {
                "url": media.get("url"),
                "type": media.get("type", "image"),
                "platform": platform,
                "dimensions": rules.get('media_dimensions', {}),
                "format": rules.get('media_format', 'auto')
            }
            adapted_media.append(adapted)

        return adapted_media

    def _get_platform_enum(self, platform_name: str) -> Optional[PlatformEnum]:
        """Get platform enum from string name"""
        try:
            return PlatformEnum(platform_name.lower())
        except ValueError:
            return None

    def _get_platform_rules(self, platform: PlatformEnum) -> Dict[str, Any]:
        """Get platform-specific content rules"""
        rules = {
            PlatformEnum.instagram: {
                "max_characters": 2200,
                "max_hashtags": 30,
                "max_media": 10,
                "tone": "visual, engaging",
                "cta_style": "subtle",
                "emoji_usage": "moderate",
                "media_dimensions": {"width": 1080, "height": 1080},
                "media_format": "square"
            },
            PlatformEnum.twitter: {
                "max_characters": 280,
                "max_hashtags": 2,
                "max_media": 4,
                "tone": "concise, conversational",
                "cta_style": "direct",
                "emoji_usage": "minimal",
                "media_dimensions": {"width": 1200, "height": 675},
                "media_format": "landscape"
            },
            PlatformEnum.linkedin: {
                "max_characters": 3000,
                "max_hashtags": 5,
                "max_media": 9,
                "tone": "professional, informative",
                "cta_style": "professional",
                "emoji_usage": "minimal",
                "media_dimensions": {"width": 1200, "height": 627},
                "media_format": "landscape"
            },
            PlatformEnum.facebook: {
                "max_characters": 63206,
                "max_hashtags": 30,
                "max_media": 10,
                "tone": "friendly, community-focused",
                "cta_style": "engaging",
                "emoji_usage": "moderate",
                "media_dimensions": {"width": 1200, "height": 630},
                "media_format": "landscape"
            },
            PlatformEnum.tiktok: {
                "max_characters": 150,
                "max_hashtags": 20,
                "max_media": 1,
                "tone": "trendy, youthful",
                "cta_style": "trendy",
                "emoji_usage": "high",
                "media_dimensions": {"width": 1080, "height": 1920},
                "media_format": "vertical"
            },
            PlatformEnum.youtube: {
                "max_characters": 5000,
                "max_hashtags": 15,
                "max_media": 1,
                "tone": "informative, engaging",
                "cta_style": "clear",
                "emoji_usage": "moderate",
                "media_dimensions": {"width": 1280, "height": 720},
                "media_format": "landscape"
            },
            PlatformEnum.pinterest: {
                "max_characters": 500,
                "max_hashtags": 20,
                "max_media": 1,
                "tone": "inspirational, visual",
                "cta_style": "subtle",
                "emoji_usage": "moderate",
                "media_dimensions": {"width": 1000, "height": 1500},
                "media_format": "vertical"
            },
            PlatformEnum.reddit: {
                "max_characters": 40000,
                "max_hashtags": 0,
                "max_media": 1,
                "tone": "community-focused, authentic",
                "cta_style": "none",
                "emoji_usage": "minimal",
                "media_dimensions": {"width": 1200, "height": 675},
                "media_format": "landscape"
            }
        }
        
        return rules.get(platform, {
            "max_characters": 1000,
            "max_hashtags": 10,
            "max_media": 5,
            "tone": "professional",
            "cta_style": "subtle",
            "emoji_usage": "moderate",
            "media_dimensions": {"width": 1200, "height": 630},
            "media_format": "auto"
        })

    async def create_remix_variants(self, user_id: int, scheduled_post_id: int, remixed_content: Dict[str, Any]) -> Dict[str, Any]:
        """Create AriaPostVariant records for remixed content"""
        db = await get_supabase()
        async with db.get_session() as session:
            variants_created = []
            
            for platform, content in remixed_content.items():
                variant = AriaPostVariant(
                    scheduled_post_id=scheduled_post_id,
                    variant_key=f"remix_{platform}",
                    caption=content.get("caption"),
                    hashtags=content.get("hashtags"),
                    media_refs=content.get("media_refs"),
                    status="ready",
                    metrics={"platform": platform}
                )
                session.add(variant)
                variants_created.append(variant)
            
            await session.commit()
            
            return {
                "success": True,
                "variants_created": len(variants_created),
                "platforms": list(remixed_content.keys())
            }
