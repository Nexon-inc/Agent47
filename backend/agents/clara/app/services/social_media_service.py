import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, update
from sqlalchemy.orm import selectinload
import httpx
from core.config import settings
from core.integrations.integration_manager import IntegrationManager
from core.event_bus.kafka_manager import EventBus
from ..database import get_clara_database
from ..models import (
    ClaraSupportTicket, ClaraCustomerInteraction, CustomerProfile,
    TicketPriority, TicketStatus, TicketCategory, SupportChannel
)

logger = logging.getLogger(__name__)

class SocialMediaService:
    def __init__(self):
        self.integration_manager = IntegrationManager()
        self.event_bus = EventBus()
        self._initialized = False
        self._social_clients = {}
    
    async def initialize(self):
        """Initialize social media service"""
        if self._initialized:
            return
        
        try:
            await self.integration_manager.initialize()
            await self.event_bus.initialize()
            await self._initialize_social_clients()
            self._initialized = True
            logger.info("Social media service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize social media service: {e}")
            raise
    
    async def _initialize_social_clients(self):
        """Initialize social media API clients"""
        db = await get_clara_database()
        async with db.get_session() as session:
            # Get active social media integrations
            integrations = await self.integration_manager.get_integrations_by_type("social_media")
            
            for integration in integrations:
                if integration.name == "instagram":
                    self._social_clients["instagram"] = InstagramClient(integration)
                elif integration.name == "tiktok":
                    self._social_clients["tiktok"] = TikTokClient(integration)
                elif integration.name == "twitter":
                    self._social_clients["twitter"] = TwitterClient(integration)
                elif integration.name == "facebook":
                    self._social_clients["facebook"] = FacebookClient(integration)
    
    async def prioritize_social_channels(
        self,
        customer_id: int,
        platform: str
    ) -> Dict[str, Any]:
        """Prioritize high-engagement social media channels"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_clara_database()
            async with db.get_session() as session:
                # Get customer profile
                profile_query = select(CustomerProfile).where(CustomerProfile.user_id == customer_id)
                profile_result = await session.execute(profile_query)
                profile = profile_result.scalar_one_or_none()
                
                if not profile:
                    raise ValueError(f"Customer profile {customer_id} not found")
                
                # Get social client
                social_client = self._social_clients.get(platform)
                if not social_client:
                    raise ValueError(f"Social platform {platform} not configured")
                
                # Analyze engagement level
                engagement_data = await social_client.get_engagement_metrics(customer_id)
                
                # Determine priority based on engagement
                priority_score = await self._calculate_engagement_priority(engagement_data)
                
                # Update customer profile with social priority
                profile.metadata = {
                    **profile.metadata,
                    "social_media": {
                        "platform": platform,
                        "engagement_score": priority_score,
                        "priority_level": "high" if priority_score > 0.7 else "medium" if priority_score > 0.4 else "low",
                        "last_updated": datetime.utcnow().isoformat()
                    }
                }
                
                await session.commit()
                
                return {
                    "success": True,
                    "customer_id": customer_id,
                    "platform": platform,
                    "engagement_score": priority_score,
                    "priority_level": "high" if priority_score > 0.7 else "medium" if priority_score > 0.4 else "low",
                    "engagement_data": engagement_data
                }
                
        except Exception as e:
            logger.error(f"Failed to prioritize social channels for customer {customer_id}: {e}")
            return {
                "success": False,
                "customer_id": customer_id,
                "platform": platform,
                "error": str(e)
            }
    
    async def track_collaboration_inquiries(
        self,
        customer_id: int,
        inquiry_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Track brand collaboration inquiries"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_clara_database()
            async with db.get_session() as session:
                # Create collaboration inquiry ticket
                ticket = ClaraSupportTicket(
                    ticket_number=f"COL-{datetime.now().strftime('%Y%m%d')}-{customer_id}",
                    customer_id=customer_id,
                    channel=SupportChannel.SOCIAL_MEDIA,
                    category=TicketCategory.FEATURE_REQUEST,
                    priority=TicketPriority.HIGH,
                    status=TicketStatus.OPEN,
                    subject="ClaraBrand Collaboration Inquiry",
                    description=inquiry_data.get("description", ""),
                    tags=["collaboration", "brand", "inquiry"],
                    metadata={
                        "inquiry_type": "collaboration",
                        "platform": inquiry_data.get("platform"),
                        "reach": inquiry_data.get("reach"),
                        "engagement_rate": inquiry_data.get("engagement_rate"),
                        "brand_category": inquiry_data.get("brand_category"),
                        "budget_range": inquiry_data.get("budget_range"),
                        "timeline": inquiry_data.get("timeline"),
                        "contact_preference": inquiry_data.get("contact_preference")
                    }
                )
                
                session.add(ticket)
                await session.commit()
                
                # Publish event for calendar/CRM sync
                await self.event_bus.publish(
                    "clara.collaboration.inquiry_created",
                    {
                        "ticket_id": ticket.id,
                        "customer_id": customer_id,
                        "inquiry_data": inquiry_data,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                
                return {
                    "success": True,
                    "ticket_id": ticket.id,
                    "customer_id": customer_id,
                    "message": "Collaboration inquiry tracked successfully"
                }
                
        except Exception as e:
            logger.error(f"Failed to track collaboration inquiry for customer {customer_id}: {e}")
            return {
                "success": False,
                "customer_id": customer_id,
                "error": str(e)
            }
    
    async def analyze_social_engagement(
        self,
        customer_id: int,
        platform: str,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Analyze social media engagement metrics"""
        if not self._initialized:
            await self.initialize()
        
        try:
            # Get social client
            social_client = self._social_clients.get(platform)
            if not social_client:
                raise ValueError(f"Social platform {platform} not configured")
            
            # Get engagement metrics
            metrics = await social_client.get_engagement_metrics(
                customer_id, date_from, date_to
            )
            
            # Calculate engagement rate
            engagement_rate = await self._calculate_engagement_rate(metrics)
            
            # Get DM response rate
            dm_response_rate = await social_client.get_dm_response_rate(customer_id)
            
            return {
                "success": True,
                "customer_id": customer_id,
                "platform": platform,
                "engagement_rate": engagement_rate,
                "dm_response_rate": dm_response_rate,
                "metrics": metrics,
                "analysis": {
                    "engagement_level": "high" if engagement_rate > 0.05 else "medium" if engagement_rate > 0.02 else "low",
                    "response_efficiency": "excellent" if dm_response_rate > 0.9 else "good" if dm_response_rate > 0.7 else "needs_improvement"
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze social engagement for customer {customer_id}: {e}")
            return {
                "success": False,
                "customer_id": customer_id,
                "platform": platform,
                "error": str(e)
            }
    
    async def get_social_insights(
        self,
        platform: str,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get social media insights and trends"""
        if not self._initialized:
            await self.initialize()
        
        try:
            # Get social client
            social_client = self._social_clients.get(platform)
            if not social_client:
                raise ValueError(f"Social platform {platform} not configured")
            
            # Get platform insights
            insights = await social_client.get_platform_insights(date_from, date_to)
            
            return {
                "success": True,
                "platform": platform,
                "insights": insights,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get social insights for {platform}: {e}")
            return {
                "success": False,
                "platform": platform,
                "error": str(e)
            }
    
    async def _calculate_engagement_priority(
        self,
        engagement_data: Dict[str, Any]
    ) -> float:
        """Calculate priority score based on engagement data"""
        try:
            followers = engagement_data.get("followers", 0)
            likes = engagement_data.get("likes", 0)
            comments = engagement_data.get("comments", 0)
            shares = engagement_data.get("shares", 0)
            views = engagement_data.get("views", 0)
            
            # Calculate engagement rate
            total_engagement = likes + comments + shares
            engagement_rate = total_engagement / followers if followers > 0 else 0
            
            # Calculate view rate
            view_rate = views / followers if followers > 0 else 0
            
            # Weighted priority score
            priority_score = (
                engagement_rate * 0.4 +
                view_rate * 0.3 +
                (followers / 10000) * 0.2 +  # Normalize followers
                (shares / followers) * 0.1 if followers > 0 else 0
            )
            
            return min(priority_score, 1.0)  # Cap at 1.0
            
        except Exception as e:
            logger.error(f"Error calculating engagement priority: {e}")
            return 0.0
    
    async def _calculate_engagement_rate(
        self,
        metrics: Dict[str, Any]
    ) -> float:
        """Calculate engagement rate from metrics"""
        try:
            followers = metrics.get("followers", 0)
            total_engagement = (
                metrics.get("likes", 0) +
                metrics.get("comments", 0) +
                metrics.get("shares", 0)
            )
            
            return total_engagement / followers if followers > 0 else 0
            
        except Exception as e:
            logger.error(f"Error calculating engagement rate: {e}")
            return 0.0


class InstagramClient:
    def __init__(self, integration):
        self.integration = integration
        self.base_url = integration.base_url
        self.api_key = integration.api_key
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def get_engagement_metrics(
        self,
        customer_id: int,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/users/{customer_id}/insights",
                headers=self.headers,
                params={
                    "metric": "engagement,impressions,reach",
                    "period": "day",
                    "since": date_from.isoformat() if date_from else None,
                    "until": date_to.isoformat() if date_to else None
                }
            )
            response.raise_for_status()
            return response.json()
    
    async def get_dm_response_rate(self, customer_id: int) -> float:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/users/{customer_id}/messages",
                headers=self.headers
            )
            response.raise_for_status()
            data = response.json()
            
            total_messages = data.get("total_count", 0)
            responded_messages = data.get("responded_count", 0)
            
            return responded_messages / total_messages if total_messages > 0 else 0.0
    
    async def get_platform_insights(
        self,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/insights",
                headers=self.headers,
                params={
                    "since": date_from.isoformat() if date_from else None,
                    "until": date_to.isoformat() if date_to else None
                }
            )
            response.raise_for_status()
            return response.json()


class TikTokClient:
    def __init__(self, integration):
        self.integration = integration
        self.base_url = integration.base_url
        self.api_key = integration.api_key
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def get_engagement_metrics(
        self,
        customer_id: int,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/user/{customer_id}/analytics",
                headers=self.headers,
                params={
                    "start_date": date_from.strftime("%Y-%m-%d") if date_from else None,
                    "end_date": date_to.strftime("%Y-%m-%d") if date_to else None
                }
            )
            response.raise_for_status()
            return response.json()
    
    async def get_dm_response_rate(self, customer_id: int) -> float:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/user/{customer_id}/messages",
                headers=self.headers
            )
            response.raise_for_status()
            data = response.json()
            
            total_messages = data.get("total_count", 0)
            responded_messages = data.get("responded_count", 0)
            
            return responded_messages / total_messages if total_messages > 0 else 0.0
    
    async def get_platform_insights(
        self,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/analytics",
                headers=self.headers,
                params={
                    "start_date": date_from.strftime("%Y-%m-%d") if date_from else None,
                    "end_date": date_to.strftime("%Y-%m-%d") if date_to else None
                }
            )
            response.raise_for_status()
            return response.json()


class TwitterClient:
    def __init__(self, integration):
        self.integration = integration
        self.base_url = integration.base_url
        self.api_key = integration.api_key
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def get_engagement_metrics(
        self,
        customer_id: int,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/users/{customer_id}/tweets",
                headers=self.headers,
                params={
                    "start_time": date_from.isoformat() if date_from else None,
                    "end_time": date_to.isoformat() if date_to else None,
                    "tweet.fields": "public_metrics"
                }
            )
            response.raise_for_status()
            return response.json()
    
    async def get_dm_response_rate(self, customer_id: int) -> float:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/users/{customer_id}/messages",
                headers=self.headers
            )
            response.raise_for_status()
            data = response.json()
            
            total_messages = data.get("total_count", 0)
            responded_messages = data.get("responded_count", 0)
            
            return responded_messages / total_messages if total_messages > 0 else 0.0
    
    async def get_platform_insights(
        self,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/tweets/search/recent",
                headers=self.headers,
                params={
                    "query": "support help",
                    "start_time": date_from.isoformat() if date_from else None,
                    "end_time": date_to.isoformat() if date_to else None
                }
            )
            response.raise_for_status()
            return response.json()


class FacebookClient:
    def __init__(self, integration):
        self.integration = integration
        self.base_url = integration.base_url
        self.api_key = integration.api_key
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def get_engagement_metrics(
        self,
        customer_id: int,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/{customer_id}/insights",
                headers=self.headers,
                params={
                    "metric": "page_engaged_users,page_post_engagements",
                    "period": "day",
                    "since": date_from.strftime("%Y-%m-%d") if date_from else None,
                    "until": date_to.strftime("%Y-%m-%d") if date_to else None
                }
            )
            response.raise_for_status()
            return response.json()
    
    async def get_dm_response_rate(self, customer_id: int) -> float:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/{customer_id}/conversations",
                headers=self.headers
            )
            response.raise_for_status()
            data = response.json()
            
            total_messages = data.get("total_count", 0)
            responded_messages = data.get("responded_count", 0)
            
            return responded_messages / total_messages if total_messages > 0 else 0.0
    
    async def get_platform_insights(
        self,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/insights",
                headers=self.headers,
                params={
                    "metric": "page_views_total,page_fans",
                    "period": "day",
                    "since": date_from.strftime("%Y-%m-%d") if date_from else None,
                    "until": date_to.strftime("%Y-%m-%d") if date_to else None
                }
            )
            response.raise_for_status()
            return response.json()
