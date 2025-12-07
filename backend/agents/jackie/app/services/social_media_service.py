import asyncio
import logging
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from backend.core.ai import get_ai_service_manager, AIServiceManager
from backend.core.event_bus.kafka_manager import EventBus
from ..database import get_jackie_database
from ..models import MarketingCampaign, PlatformType

logger = logging.getLogger(__name__)

class SocialMediaService:
    def __init__(self):
        self.db = None
        self.nlp_utils = None
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

    async def create_social_post(
        self,
        user_id: int,
        platform: PlatformType,
        content: str,
        media_urls: Optional[List[str]] = None,
        scheduled_time: Optional[str] = None,
        targeting: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        try:
            optimized_content = await self._optimize_content_for_platform(content, platform)
            
            async with self.db.get_session() as session:
                campaign = MarketingCampaign(
                    user_id=user_id,
                    campaign_name=f"Social Post - {platform.value}",
                    campaign_type="social_media",
                    platform=platform,
                    content=optimized_content,
                    media_urls=media_urls or [],
                    targeting=targeting or {},
                    budget=0.0,
                    status="active",
                    scheduled_time=scheduled_time
                )

                session.add(campaign)
                await session.commit()
                await session.refresh(campaign)

                await self.event_bus.publish(
                    "marketing.social_post.created",
                    {
                        "post_id": campaign.id,
                        "user_id": user_id,
                        "platform": platform.value,
                        "content": optimized_content
                    }
                )

                return {
                    "success": True,
                    "social_post": {
                        "id": campaign.id,
                        "platform": campaign.platform.value,
                        "content": campaign.content,
                        "status": campaign.status.value,
                        "scheduled_time": campaign.scheduled_time
                    }
                }

        except Exception as e:
            logger.error(f"Failed to create social post: {e}")
            return {"success": False, "error": str(e)}

    async def create_social_campaign(
        self,
        user_id: int,
        campaign_name: str,
        platforms: List[PlatformType],
        content_template: str,
        posting_schedule: Dict[str, Any],
        budget: float
    ) -> Dict[str, Any]:
        try:
            async with self.db.get_session() as session:
                campaign = MarketingCampaign(
                    user_id=user_id,
                    campaign_name=campaign_name,
                    campaign_type="social_media",
                    platform=platforms[0],
                    content=content_template,
                    targeting=posting_schedule,
                    budget=budget,
                    status="active"
                )

                session.add(campaign)
                await session.commit()
                await session.refresh(campaign)

                await self.event_bus.publish(
                    "marketing.social_campaign.created",
                    {
                        "campaign_id": campaign.id,
                        "user_id": user_id,
                        "campaign_name": campaign_name,
                        "platforms": [p.value for p in platforms]
                    }
                )

                return {
                    "success": True,
                    "social_campaign": {
                        "id": campaign.id,
                        "campaign_name": campaign.campaign_name,
                        "platforms": [p.value for p in platforms],
                        "budget": campaign.budget,
                        "status": campaign.status.value
                    }
                }

        except Exception as e:
            logger.error(f"Failed to create social campaign: {e}")
            return {"success": False, "error": str(e)}

    async def get_social_analytics(self, campaign_id: int) -> Dict[str, Any]:
        try:
            async with self.db.get_session() as session:
                query = select(MarketingCampaign).where(MarketingCampaign.id == campaign_id)
                result = await session.execute(query)
                campaign = result.scalar_one_or_none()

                if not campaign:
                    return {"success": False, "error": "Campaign not found"}

                analytics = await self._generate_social_analytics(campaign)

                return {
                    "success": True,
                    "social_analytics": {
                        "campaign_id": campaign.id,
                        "campaign_name": campaign.campaign_name,
                        "platform": campaign.platform.value,
                        "analytics": analytics
                    }
                }

        except Exception as e:
            logger.error(f"Failed to get social analytics: {e}")
            return {"success": False, "error": str(e)}

    async def optimize_social_post(
        self,
        post_id: int,
        optimization_type: str
    ) -> Dict[str, Any]:
        try:
            async with self.db.get_session() as session:
                query = select(MarketingCampaign).where(MarketingCampaign.id == post_id)
                result = await session.execute(query)
                post = result.scalar_one_or_none()

                if not post:
                    return {"success": False, "error": "Post not found"}

                optimized_content = await self._optimize_content_for_engagement(post.content, optimization_type)

                stmt = update(MarketingCampaign).where(MarketingCampaign.id == post_id).values(
                    content=optimized_content
                )
                await session.execute(stmt)
                await session.commit()

                return {
                    "success": True,
                    "optimized_post": {
                        "id": post.id,
                        "original_content": post.content,
                        "optimized_content": optimized_content,
                        "optimization_type": optimization_type
                    }
                }

        except Exception as e:
            logger.error(f"Failed to optimize social post: {e}")
            return {"success": False, "error": str(e)}

    async def get_social_trends(self, platform: PlatformType) -> Dict[str, Any]:
        try:
            trends = await self._analyze_social_trends(platform)

            return {
                "success": True,
                "social_trends": {
                    "platform": platform.value,
                    "trends": trends
                }
            }

        except Exception as e:
            logger.error(f"Failed to get social trends: {e}")
            return {"success": False, "error": str(e)}

    async def _optimize_content_for_platform(self, content: str, platform: PlatformType) -> str:
        prompt = f"Optimize this content for {platform.value} platform:\n\n{content}"
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"Optimize content for {platform.value}"}
        ]
        
        response = await self.ai_service_manager.generate_text(
            messages=messages,
            max_tokens=300,
            temperature=0.5
        )
        
        optimized_content = response.text_content if response.success else content
        return optimized_content

    async def _optimize_content_for_engagement(self, content: str, optimization_type: str) -> str:
        prompt = f"Optimize this social media content for {optimization_type} engagement:\n\n{content}"
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"Optimize content for {platform.value}"}
        ]
        
        response = await self.ai_service_manager.generate_text(
            messages=messages,
            max_tokens=300,
            temperature=0.5
        )
        
        optimized_content = response.text_content if response.success else content
        return optimized_content

    async def _generate_social_analytics(self, campaign: MarketingCampaign) -> Dict[str, Any]:
        return {
            "impressions": 5000,
            "reach": 3000,
            "engagement": 250,
            "likes": 180,
            "shares": 45,
            "comments": 25,
            "click_through_rate": 0.05,
            "engagement_rate": 0.08
        }

    async def _analyze_social_trends(self, platform: PlatformType) -> Dict[str, Any]:
        trends = {
            "trending_hashtags": ["#marketing", "#business", "#growth"],
            "popular_content_types": ["video", "carousel", "story"],
            "optimal_posting_times": ["9:00 AM", "12:00 PM", "6:00 PM"],
            "engagement_patterns": {
                "monday": 0.12,
                "tuesday": 0.15,
                "wednesday": 0.18,
                "thursday": 0.16,
                "friday": 0.14,
                "saturday": 0.10,
                "sunday": 0.08
            }
        }
        return trends
