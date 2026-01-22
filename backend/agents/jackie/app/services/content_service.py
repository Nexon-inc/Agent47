import asyncio
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from core.ai import get_ai_service_manager, AIServiceManager
from core.event_bus.kafka_manager import EventBus
from ..database import get_jackie_database
from ..models import JackieCampaignContent, ContentType, PlatformType

logger = logging.getLogger(__name__)

class ContentService:
    def __init__(self):
        self.db = None
        self.ai_service_manager: Optional[AIServiceManager] = None
        self.event_bus = None
        self._initialized = False
    
    async def initialize(self):
        if self._initialized:
            return
        
        self.db = await get_jackie_database()
        self.ai_service_manager = await get_ai_service_manager()
        self.event_bus = EventBus()
        await self.event_bus.initialize()
        self._initialized = True
    
    async def generate_content(
        self,
        user_id: int,
        content_type: ContentType,
        platform: PlatformType,
        topic: str,
        brand_voice_id: Optional[int] = None,
        target_audience: Optional[Dict[str, Any]] = None,
        keywords: Optional[List[str]] = None,
        tone: Optional[str] = None,
        length: Optional[str] = None,
        call_to_action: Optional[str] = None
    ) -> Dict[str, Any]:
        try:
            async with self.db.get_session() as session:
                generated_content = await self._generate_ai_content(
                    content_type=content_type,
                    platform=platform,
                    topic=topic,
                    target_audience=target_audience,
                    keywords=keywords,
                    tone=tone,
                    length=length,
                    call_to_action=call_to_action
                )
                
                content = JackieCampaignContent(
                    campaign_id=None,
                    content_type=content_type,
                    platform=platform,
                    title=generated_content.get("title"),
                    content=generated_content["content"],
                    media_urls=generated_content.get("media_urls", []),
                    hashtags=generated_content.get("hashtags", []),
                    scheduled_time=None,
                    published_time=None,
                    engagement_metrics={},
                    ai_generated=True,
                    brand_voice_applied=brand_voice_id is not None
                )
                
                session.add(content)
                await session.commit()
                await session.refresh(content)
                
                await self.event_bus.publish(
                    "marketing.content.generated",
                    {
                        "content_id": content.id,
                        "user_id": user_id,
                        "content_type": content_type.value,
                        "platform": platform.value,
                        "ai_generated": True
                    }
                )
                
                return {
                    "success": True,
                    "content": {
                        "id": content.id,
                        "content_type": content.content_type.value,
                        "platform": content.platform.value,
                        "title": content.title,
                        "content": content.content,
                        "hashtags": content.hashtags,
                        "ai_generated": content.ai_generated,
                        "brand_voice_applied": content.brand_voice_applied,
                        "created_at": content.created_at.isoformat()
                    }
                }
                
        except Exception as e:
            logger.error(f"Failed to generate content: {e}")
            return {"success": False, "error": str(e)}
    
    async def create_ad_copy(
        self,
        user_id: int,
        platform: PlatformType,
        product_name: str,
        product_description: str,
        target_audience: Dict[str, Any],
        ad_type: str,
        budget: float,
        brand_voice_id: Optional[int] = None,
        keywords: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        try:
            async with self.db.get_session() as session:
                ad_copy = await self._generate_ad_copy(
                    platform=platform,
                    product_name=product_name,
                    product_description=product_description,
                    target_audience=target_audience,
                    ad_type=ad_type,
                    budget=budget,
                    keywords=keywords
                )
                
                content = JackieCampaignContent(
                    campaign_id=None,
                    content_type=ContentType.AD_COPY,
                    platform=platform,
                    title=f"Ad Copy for {product_name}",
                    content=ad_copy["content"],
                    media_urls=ad_copy.get("media_urls", []),
                    hashtags=ad_copy.get("hashtags", []),
                    scheduled_time=None,
                    published_time=None,
                    engagement_metrics={},
                    ai_generated=True,
                    brand_voice_applied=brand_voice_id is not None
                )
                
                session.add(content)
                await session.commit()
                await session.refresh(content)
                
                return {
                    "success": True,
                    "ad_copy": {
                        "id": content.id,
                        "platform": content.platform.value,
                        "content": content.content,
                        "hashtags": content.hashtags,
                        "ai_generated": content.ai_generated,
                        "created_at": content.created_at.isoformat()
                    }
                }
                
        except Exception as e:
            logger.error(f"Failed to create ad copy: {e}")
            return {"success": False, "error": str(e)}
    
    async def create_social_post(
        self,
        user_id: int,
        platform: PlatformType,
        topic: str,
        content_type: ContentType,
        hashtags: Optional[List[str]] = None,
        brand_voice_id: Optional[int] = None,
        target_audience: Optional[Dict[str, Any]] = None,
        call_to_action: Optional[str] = None
    ) -> Dict[str, Any]:
        try:
            async with self.db.get_session() as session:
                social_post = await self._generate_social_post(
                    platform=platform,
                    topic=topic,
                    content_type=content_type,
                    hashtags=hashtags,
                    target_audience=target_audience,
                    call_to_action=call_to_action
                )
                
                content = JackieCampaignContent(
                    campaign_id=None,
                    content_type=content_type,
                    platform=platform,
                    title=social_post.get("title"),
                    content=social_post["content"],
                    media_urls=social_post.get("media_urls", []),
                    hashtags=social_post.get("hashtags", []),
                    scheduled_time=None,
                    published_time=None,
                    engagement_metrics={},
                    ai_generated=True,
                    brand_voice_applied=brand_voice_id is not None
                )
                
                session.add(content)
                await session.commit()
                await session.refresh(content)
                
                return {
                    "success": True,
                    "social_post": {
                        "id": content.id,
                        "platform": content.platform.value,
                        "content_type": content.content_type.value,
                        "content": content.content,
                        "hashtags": content.hashtags,
                        "ai_generated": content.ai_generated,
                        "created_at": content.created_at.isoformat()
                    }
                }
                
        except Exception as e:
            logger.error(f"Failed to create social post: {e}")
            return {"success": False, "error": str(e)}
    
    async def create_email_template(
        self,
        user_id: int,
        email_type: str,
        subject_line: str,
        target_audience: Dict[str, Any],
        brand_voice_id: Optional[int] = None,
        personalization_fields: Optional[List[str]] = None,
        call_to_action: Optional[str] = None
    ) -> Dict[str, Any]:
        try:
            async with self.db.get_session() as session:
                email_template = await self._generate_email_template(
                    email_type=email_type,
                    subject_line=subject_line,
                    target_audience=target_audience,
                    personalization_fields=personalization_fields,
                    call_to_action=call_to_action
                )
                
                content = JackieCampaignContent(
                    campaign_id=None,
                    content_type=ContentType.EMAIL,
                    platform=PlatformType.EMAIL,
                    title=subject_line,
                    content=email_template["content"],
                    media_urls=email_template.get("media_urls", []),
                    hashtags=[],
                    scheduled_time=None,
                    published_time=None,
                    engagement_metrics={},
                    ai_generated=True,
                    brand_voice_applied=brand_voice_id is not None
                )
                
                session.add(content)
                await session.commit()
                await session.refresh(content)
                
                return {
                    "success": True,
                    "email_template": {
                        "id": content.id,
                        "email_type": email_type,
                        "subject_line": content.title,
                        "content": content.content,
                        "personalization_fields": personalization_fields,
                        "ai_generated": content.ai_generated,
                        "created_at": content.created_at.isoformat()
                    }
                }
                
        except Exception as e:
            logger.error(f"Failed to create email template: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_content_details(self, content_id: int) -> Dict[str, Any]:
        try:
            async with self.db.get_session() as session:
                query = select(JackieCampaignContent).where(JackieCampaignContent.id == content_id)
                result = await session.execute(query)
                content = result.scalar_one_or_none()
                
                if not content:
                    return {"success": False, "error": "Content not found"}
                
                return {
                    "success": True,
                    "content": {
                        "id": content.id,
                        "content_type": content.content_type.value,
                        "platform": content.platform.value,
                        "title": content.title,
                        "content": content.content,
                        "media_urls": content.media_urls,
                        "hashtags": content.hashtags,
                        "scheduled_time": content.scheduled_time.isoformat() if content.scheduled_time else None,
                        "published_time": content.published_time.isoformat() if content.published_time else None,
                        "engagement_metrics": content.engagement_metrics,
                        "ai_generated": content.ai_generated,
                        "brand_voice_applied": content.brand_voice_applied,
                        "created_at": content.created_at.isoformat()
                    }
                }
                
        except Exception as e:
            logger.error(f"Failed to get content details: {e}")
            return {"success": False, "error": str(e)}
    
    async def update_content(
        self,
        content_id: int,
        content: str,
        title: Optional[str] = None,
        hashtags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        try:
            async with self.db.get_session() as session:
                update_data = {"content": content}
                if title is not None:
                    update_data["title"] = title
                if hashtags is not None:
                    update_data["hashtags"] = hashtags
                
                stmt = update(JackieCampaignContent).where(JackieCampaignContent.id == content_id).values(**update_data)
                await session.execute(stmt)
                await session.commit()
                
                return {"success": True, "message": "Content updated successfully"}
                
        except Exception as e:
            logger.error(f"Failed to update content: {e}")
            return {"success": False, "error": str(e)}
    
    async def delete_content(self, content_id: int) -> Dict[str, Any]:
        try:
            async with self.db.get_session() as session:
                stmt = delete(JackieCampaignContent).where(JackieCampaignContent.id == content_id)
                await session.execute(stmt)
                await session.commit()
                
                return {"success": True, "message": "Content deleted successfully"}
                
        except Exception as e:
            logger.error(f"Failed to delete content: {e}")
            return {"success": False, "error": str(e)}
    
    async def list_content(
        self,
        user_id: int,
        content_type: Optional[ContentType] = None,
        platform: Optional[PlatformType] = None,
        limit: int = 10,
        offset: int = 0
    ) -> Dict[str, Any]:
        try:
            async with self.db.get_session() as session:
                query = select(JackieCampaignContent)
                
                if content_type:
                    query = query.where(JackieCampaignContent.content_type == content_type)
                if platform:
                    query = query.where(JackieCampaignContent.platform == platform)
                
                query = query.offset(offset).limit(limit)
                result = await session.execute(query)
                contents = result.scalars().all()
                
                content_list = []
                for content in contents:
                    content_list.append({
                        "id": content.id,
                        "content_type": content.content_type.value,
                        "platform": content.platform.value,
                        "title": content.title,
                        "content": content.content[:200] + "..." if len(content.content) > 200 else content.content,
                        "hashtags": content.hashtags,
                        "ai_generated": content.ai_generated,
                        "created_at": content.created_at.isoformat()
                    })
                
                return {
                    "success": True,
                    "contents": content_list,
                    "total": len(content_list),
                    "limit": limit,
                    "offset": offset
                }
                
        except Exception as e:
            logger.error(f"Failed to list content: {e}")
            return {"success": False, "error": str(e)}
    
    async def optimize_content(self, content_id: int, optimization_type: str) -> Dict[str, Any]:
        try:
            async with self.db.get_session() as session:
                query = select(JackieCampaignContent).where(JackieCampaignContent.id == content_id)
                result = await session.execute(query)
                content = result.scalar_one_or_none()
                
                if not content:
                    return {"success": False, "error": "Content not found"}
                
                optimized_content = await self._optimize_content_ai(
                    content=content.content,
                    optimization_type=optimization_type,
                    platform=content.platform,
                    content_type=content.content_type
                )
                
                stmt = update(JackieCampaignContent).where(JackieCampaignContent.id == content_id).values(
                    content=optimized_content["content"],
                    title=optimized_content.get("title", content.title)
                )
                await session.execute(stmt)
                await session.commit()
                
                return {
                    "success": True,
                    "optimized_content": optimized_content
                }
                
        except Exception as e:
            logger.error(f"Failed to optimize content: {e}")
            return {"success": False, "error": str(e)}
    
    async def translate_content(self, content_id: int, target_language: str) -> Dict[str, Any]:
        try:
            async with self.db.get_session() as session:
                query = select(JackieCampaignContent).where(JackieCampaignContent.id == content_id)
                result = await session.execute(query)
                content = result.scalar_one_or_none()
                
                if not content:
                    return {"success": False, "error": "Content not found"}
                
                translated_content = await self._translate_content_ai(
                    content=content.content,
                    target_language=target_language
                )
                
                stmt = update(JackieCampaignContent).where(JackieCampaignContent.id == content_id).values(
                    content=translated_content["content"]
                )
                await session.execute(stmt)
                await session.commit()
                
                return {
                    "success": True,
                    "translated_content": translated_content
                }
                
        except Exception as e:
            logger.error(f"Failed to translate content: {e}")
            return {"success": False, "error": str(e)}
    
    async def schedule_content(
        self,
        content_id: int,
        scheduled_time: str,
        platform: PlatformType
    ) -> Dict[str, Any]:
        try:
            scheduled_dt = datetime.fromisoformat(scheduled_time)
            
            async with self.db.get_session() as session:
                stmt = update(JackieCampaignContent).where(JackieCampaignContent.id == content_id).values(
                    scheduled_time=scheduled_dt,
                    platform=platform
                )
                await session.execute(stmt)
                await session.commit()
                
                return {"success": True, "message": "Content scheduled successfully"}
                
        except Exception as e:
            logger.error(f"Failed to schedule content: {e}")
            return {"success": False, "error": str(e)}
    
    async def bulk_generate_content(
        self,
        user_id: int,
        content_briefs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        try:
            generated_contents = []
            
            for brief in content_briefs:
                result = await self.generate_content(
                    user_id=user_id,
                    content_type=ContentType(brief["content_type"]),
                    platform=PlatformType(brief["platform"]),
                    topic=brief["topic"],
                    brand_voice_id=brief.get("brand_voice_id"),
                    target_audience=brief.get("target_audience"),
                    keywords=brief.get("keywords"),
                    tone=brief.get("tone"),
                    length=brief.get("length"),
                    call_to_action=brief.get("call_to_action")
                )
                
                if result["success"]:
                    generated_contents.append(result["content"])
            
            return {
                "success": True,
                "generated_contents": generated_contents,
                "total_generated": len(generated_contents)
            }
            
        except Exception as e:
            logger.error(f"Failed to bulk generate content: {e}")
            return {"success": False, "error": str(e)}
    
    async def _generate_ai_content(
        self,
        content_type: ContentType,
        platform: PlatformType,
        topic: str,
        target_audience: Optional[Dict[str, Any]] = None,
        keywords: Optional[List[str]] = None,
        tone: Optional[str] = None,
        length: Optional[str] = None,
        call_to_action: Optional[str] = None
    ) -> Dict[str, Any]:
        prompt = f"Generate {content_type.value} content for {platform.value} platform about: {topic}"
        
        if target_audience:
            prompt += f"\nTarget audience: {target_audience}"
        if keywords:
            prompt += f"\nKeywords: {', '.join(keywords)}"
        if tone:
            prompt += f"\nTone: {tone}"
        if length:
            prompt += f"\nLength: {length}"
        if call_to_action:
            prompt += f"\nCall to action: {call_to_action}"
        
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"Generate {content_type.value} content for {platform.value}"}
        ]
        
        response = await self.ai_service_manager.generate_text(
            messages=messages,
            max_tokens=500,
            temperature=0.7
        )
        
        generated_content = response.text_content if response.success else ""
        
        hashtags = []
        if keywords:
            hashtags = [f"#{keyword.replace(' ', '')}" for keyword in keywords[:5]]
        
        return {
            "content": generated_content,
            "title": f"{topic.title()} - {platform.value.title()}",
            "hashtags": hashtags,
            "media_urls": []
        }
    
    async def _generate_ad_copy(
        self,
        platform: PlatformType,
        product_name: str,
        product_description: str,
        target_audience: Dict[str, Any],
        ad_type: str,
        budget: float,
        keywords: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        prompt = f"Create compelling ad copy for {product_name} on {platform.value} platform. Product: {product_description}. Target audience: {target_audience}. Ad type: {ad_type}. Budget: ${budget}"
        
        if keywords:
            prompt += f"\nKeywords: {', '.join(keywords)}"
        
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"Generate ad copy for {platform.value}"}
        ]
        
        response = await self.ai_service_manager.generate_text(
            messages=messages,
            max_tokens=300,
            temperature=0.7
        )
        
        ad_copy = response.text_content if response.success else ""
        
        hashtags = []
        if keywords:
            hashtags = [f"#{keyword.replace(' ', '')}" for keyword in keywords[:3]]
        
        return {
            "content": ad_copy,
            "hashtags": hashtags,
            "media_urls": []
        }
    
    async def _generate_social_post(
        self,
        platform: PlatformType,
        topic: str,
        content_type: ContentType,
        hashtags: Optional[List[str]] = None,
        target_audience: Optional[Dict[str, Any]] = None,
        call_to_action: Optional[str] = None
    ) -> Dict[str, Any]:
        prompt = f"Create a {content_type.value} social media post for {platform.value} about: {topic}"
        
        if target_audience:
            prompt += f"\nTarget audience: {target_audience}"
        if call_to_action:
            prompt += f"\nCall to action: {call_to_action}"
        
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"Generate social media post for {platform.value}"}
        ]
        
        response = await self.ai_service_manager.generate_text(
            messages=messages,
            max_tokens=200,
            temperature=0.7
        )
        
        social_post = response.text_content if response.success else ""
        
        if not hashtags:
            hashtags = [f"#{topic.replace(' ', '')}", f"#{platform.value}"]
        
        return {
            "content": social_post,
            "title": f"{topic.title()} - {platform.value.title()}",
            "hashtags": hashtags,
            "media_urls": []
        }
    
    async def _generate_email_template(
        self,
        email_type: str,
        subject_line: str,
        target_audience: Dict[str, Any],
        personalization_fields: Optional[List[str]] = None,
        call_to_action: Optional[str] = None
    ) -> Dict[str, Any]:
        prompt = f"Create an {email_type} email template with subject: {subject_line}. Target audience: {target_audience}"
        
        if personalization_fields:
            prompt += f"\nPersonalization fields: {', '.join(personalization_fields)}"
        if call_to_action:
            prompt += f"\nCall to action: {call_to_action}"
        
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": "Generate email marketing content"}
        ]
        
        response = await self.ai_service_manager.generate_text(
            messages=messages,
            max_tokens=400,
            temperature=0.7
        )
        
        email_content = response.text_content if response.success else ""
        
        return {
            "content": email_content,
            "media_urls": []
        }
    
    async def _optimize_content_ai(
        self,
        content: str,
        optimization_type: str,
        platform: PlatformType,
        content_type: ContentType
    ) -> Dict[str, Any]:
        prompt = f"Optimize this {content_type.value} content for {platform.value} platform with focus on {optimization_type}:\n\n{content}"
        
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"Optimize content for {optimization_type}"}
        ]
        
        response = await self.ai_service_manager.generate_text(
            messages=messages,
            max_tokens=300,
            temperature=0.5
        )
        
        optimized_content = response.text_content if response.success else content
        
        return {
            "content": optimized_content,
            "optimization_type": optimization_type
        }
    
    async def _translate_content_ai(
        self,
        content: str,
        target_language: str
    ) -> Dict[str, Any]:
        prompt = f"Translate this content to {target_language}:\n\n{content}"
        
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"Translate content to {target_language}"}
        ]
        
        response = await self.ai_service_manager.generate_text(
            messages=messages,
            max_tokens=400,
            temperature=0.3
        )
        
        translated_content = response.text_content if response.success else content
        
        return {
            "content": translated_content,
            "target_language": target_language
        }
