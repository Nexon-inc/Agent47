import httpx
import json
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, update
from sqlalchemy.orm import selectinload
import logging
from ..config import settings
from ..database.connection import get_database
from ..billing import get_billing
from .models import (
    SocialPlatform, PlatformCredential, PlatformMetrics,
    PlatformType, PlatformStatus, CredentialStatus
)

logger = logging.getLogger(__name__)

class PlatformManager:
    def __init__(self):
        self._initialized = False
        self._platform_clients = {}
        
    async def initialize(self):
        """Initialize platform management system"""
        try:
            db = get_database()
            async with db.get_session() as session:
                await self._create_default_platforms(session)
            self._initialized = True
            logger.info("Platform manager initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize platform manager: {e}")
            raise
    
    async def _create_default_platforms(self, session: AsyncSession):
        """Create default social media platforms if they don't exist"""
        existing_platforms = await session.execute(select(SocialPlatform))
        if existing_platforms.scalars().first():
            return
        
        default_platforms = [
            SocialPlatform(
                name="twitter",
                display_name="Twitter (X)",
                platform_type=PlatformType.SOCIAL_MEDIA,
                description="Microblogging and social networking platform",
                api_version="2.0",
                base_url="https://api.twitter.com/2",
                api_documentation_url="https://developer.twitter.com/en/docs",
                rate_limits={
                    "requests_per_minute": 300,
                    "requests_per_hour": 3000,
                    "requests_per_day": 300000
                },
                supported_features={
                    "posting": True,
                    "analytics": True,
                    "engagement": True,
                    "scheduling": True,
                    "automation": True
                },
                authentication_methods={
                    "oauth2": True,
                    "api_key": False,
                    "bearer_token": True
                }
            ),
            SocialPlatform(
                name="instagram",
                display_name="Instagram",
                platform_type=PlatformType.SOCIAL_MEDIA,
                description="Photo and video sharing social network",
                api_version="18.0",
                base_url="https://graph.instagram.com",
                api_documentation_url="https://developers.facebook.com/docs/instagram-basic-display-api",
                rate_limits={
                    "requests_per_minute": 200,
                    "requests_per_hour": 1000,
                    "requests_per_day": 10000
                },
                supported_features={
                    "posting": True,
                    "analytics": True,
                    "engagement": True,
                    "scheduling": False,
                    "automation": True
                },
                authentication_methods={
                    "oauth2": True,
                    "api_key": False,
                    "bearer_token": False
                }
            ),
            SocialPlatform(
                name="linkedin",
                display_name="LinkedIn",
                platform_type=PlatformType.SOCIAL_MEDIA,
                description="Professional networking platform",
                api_version="2.0",
                base_url="https://api.linkedin.com/v2",
                api_documentation_url="https://developer.linkedin.com/docs",
                rate_limits={
                    "requests_per_minute": 100,
                    "requests_per_hour": 500,
                    "requests_per_day": 5000
                },
                supported_features={
                    "posting": True,
                    "analytics": True,
                    "engagement": True,
                    "scheduling": True,
                    "automation": True
                },
                authentication_methods={
                    "oauth2": True,
                    "api_key": False,
                    "bearer_token": False
                }
            ),
            SocialPlatform(
                name="facebook",
                display_name="Facebook",
                platform_type=PlatformType.SOCIAL_MEDIA,
                description="Social networking platform",
                api_version="18.0",
                base_url="https://graph.facebook.com",
                api_documentation_url="https://developers.facebook.com/docs",
                rate_limits={
                    "requests_per_minute": 200,
                    "requests_per_hour": 1000,
                    "requests_per_day": 10000
                },
                supported_features={
                    "posting": True,
                    "analytics": True,
                    "engagement": True,
                    "scheduling": True,
                    "automation": True
                },
                authentication_methods={
                    "oauth2": True,
                    "api_key": False,
                    "bearer_token": False
                }
            ),
            SocialPlatform(
                name="youtube",
                display_name="YouTube",
                platform_type=PlatformType.SOCIAL_MEDIA,
                description="Video sharing platform",
                api_version="3.0",
                base_url="https://www.googleapis.com/youtube/v3",
                api_documentation_url="https://developers.google.com/youtube/v3",
                rate_limits={
                    "requests_per_minute": 300,
                    "requests_per_hour": 10000,
                    "requests_per_day": 100000
                },
                supported_features={
                    "posting": True,
                    "analytics": True,
                    "engagement": True,
                    "scheduling": True,
                    "automation": True
                },
                authentication_methods={
                    "oauth2": True,
                    "api_key": True,
                    "bearer_token": False
                }
            ),
            SocialPlatform(
                name="tiktok",
                display_name="TikTok",
                platform_type=PlatformType.SOCIAL_MEDIA,
                description="Short-form video platform",
                api_version="1.0",
                base_url="https://open.tiktokapis.com/v2",
                api_documentation_url="https://developers.tiktok.com/doc",
                rate_limits={
                    "requests_per_minute": 100,
                    "requests_per_hour": 1000,
                    "requests_per_day": 10000
                },
                supported_features={
                    "posting": True,
                    "analytics": True,
                    "engagement": True,
                    "scheduling": False,
                    "automation": True
                },
                authentication_methods={
                    "oauth2": True,
                    "api_key": False,
                    "bearer_token": False
                }
            ),
            SocialPlatform(
                name="pinterest",
                display_name="Pinterest",
                platform_type=PlatformType.SOCIAL_MEDIA,
                description="Visual discovery engine",
                api_version="5.0",
                base_url="https://api.pinterest.com/v5",
                api_documentation_url="https://developers.pinterest.com/docs",
                rate_limits={
                    "requests_per_minute": 100,
                    "requests_per_hour": 1000,
                    "requests_per_day": 10000
                },
                supported_features={
                    "posting": True,
                    "analytics": True,
                    "engagement": True,
                    "scheduling": True,
                    "automation": True
                },
                authentication_methods={
                    "oauth2": True,
                    "api_key": False,
                    "bearer_token": False
                }
            )
        ]
        
        for platform in default_platforms:
            session.add(platform)
        await session.commit()
        logger.info("Default social media platforms created")
    
    async def get_platform(self, platform_name: str) -> Optional[Dict[str, Any]]:
        """Get platform information by name"""
        try:
            db = get_database()
            async with db.get_session() as session:
                platform = await session.execute(
                    select(SocialPlatform).where(SocialPlatform.name == platform_name)
                )
                platform = platform.scalar_one_or_none()
                
                if platform:
                    return {
                        "id": platform.id,
                        "name": platform.name,
                        "display_name": platform.display_name,
                        "platform_type": platform.platform_type.value,
                        "description": platform.description,
                        "api_version": platform.api_version,
                        "base_url": platform.base_url,
                        "rate_limits": platform.rate_limits,
                        "supported_features": platform.supported_features,
                        "authentication_methods": platform.authentication_methods,
                        "status": platform.status.value,
                        "is_available": platform.is_available
                    }
                return None
                
        except Exception as e:
            logger.error(f"Failed to get platform: {e}")
            return None
    
    async def get_all_platforms(self, platform_type: PlatformType = None) -> List[Dict[str, Any]]:
        """Get all available platforms"""
        try:
            db = get_database()
            async with db.get_session() as session:
                query = select(SocialPlatform).where(SocialPlatform.is_available == True)
                
                if platform_type:
                    query = query.where(SocialPlatform.platform_type == platform_type)
                
                platforms = await session.execute(query)
                result = []
                
                for platform in platforms.scalars():
                    result.append({
                        "id": platform.id,
                        "name": platform.name,
                        "display_name": platform.display_name,
                        "platform_type": platform.platform_type.value,
                        "description": platform.description,
                        "status": platform.status.value
                    })
                
                return result
                
        except Exception as e:
            logger.error(f"Failed to get all platforms: {e}")
            return []
    
    async def store_platform_credentials(
        self, 
        user_id: int, 
        platform_name: str, 
        credentials_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Store platform credentials for a user"""
        try:
            db = get_database()
            async with db.get_session() as session:
                platform = await session.execute(
                    select(SocialPlatform).where(SocialPlatform.name == platform_name)
                )
                platform = platform.scalar_one_or_none()
                
                if not platform:
                    return {"success": False, "error": "Platform not found"}
                
                # Check if credentials already exist
                existing_credentials = await session.execute(
                    select(PlatformCredential).where(
                        and_(
                            PlatformCredential.user_id == user_id,
                            PlatformCredential.platform_id == platform.id
                        )
                    )
                )
                existing_credentials = existing_credentials.scalar_one_or_none()
                
                if existing_credentials:
                    # Update existing credentials
                    for key, value in credentials_data.items():
                        if hasattr(existing_credentials, key):
                            setattr(existing_credentials, key, value)
                    existing_credentials.updated_at = datetime.utcnow()
                    existing_credentials.status = CredentialStatus.VALID
                    credentials = existing_credentials
                else:
                    # Create new credentials
                    credentials = PlatformCredential(
                        user_id=user_id,
                        platform_id=platform.id,
                        **credentials_data
                    )
                    session.add(credentials)
                
                await session.commit()
                
                return {
                    "success": True,
                    "credentials_id": credentials.id,
                    "message": "Platform credentials stored successfully"
                }
                
        except Exception as e:
            logger.error(f"Failed to store platform credentials: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_user_platform_credentials(self, user_id: int, platform_name: str = None) -> List[Dict[str, Any]]:
        """Get platform credentials for a user"""
        try:
            db = get_database()
            async with db.get_session() as session:
                query = select(PlatformCredential, SocialPlatform).join(SocialPlatform)
                
                if platform_name:
                    query = query.where(SocialPlatform.name == platform_name)
                
                query = query.where(PlatformCredential.user_id == user_id)
                
                credentials = await session.execute(query)
                result = []
                
                for cred, platform in credentials:
                    result.append({
                        "id": cred.id,
                        "platform_name": platform.name,
                        "platform_display_name": platform.display_name,
                        "credential_type": cred.credential_type,
                        "status": cred.status.value,
                        "expires_at": cred.expires_at.isoformat() if cred.expires_at else None,
                        "last_used": cred.last_used.isoformat() if cred.last_used else None,
                        "scopes": cred.scopes
                    })
                
                return result
                
        except Exception as e:
            logger.error(f"Failed to get user platform credentials: {e}")
            return []
    
    async def validate_platform_credentials(self, user_id: int, platform_name: str) -> Dict[str, Any]:
        """Validate platform credentials for a user"""
        try:
            db = get_database()
            async with db.get_session() as session:
                credentials = await session.execute(
                    select(PlatformCredential, SocialPlatform)
                    .join(SocialPlatform)
                    .where(
                        and_(
                            SocialPlatform.name == platform_name,
                            PlatformCredential.user_id == user_id,
                            PlatformCredential.status == CredentialStatus.VALID
                        )
                    )
                )
                result = credentials.first()
                
                if not result:
                    return {"valid": False, "error": "No valid credentials found"}
                
                cred, platform = result
                
                # Check if credentials are expired
                if cred.expires_at and cred.expires_at < datetime.utcnow():
                    cred.status = CredentialStatus.EXPIRED
                    await session.commit()
                    return {"valid": False, "error": "Credentials have expired"}
                
                # Test API connection
                api_test = await self._test_platform_api(platform, cred)
                
                if api_test["success"]:
                    cred.last_used = datetime.utcnow()
                    await session.commit()
                    return {"valid": True, "message": "Credentials are valid"}
                else:
                    cred.status = CredentialStatus.INVALID
                    await session.commit()
                    return {"valid": False, "error": api_test["error"]}
                
        except Exception as e:
            logger.error(f"Failed to validate platform credentials: {e}")
            return {"valid": False, "error": str(e)}
    
    async def _test_platform_api(self, platform: SocialPlatform, credentials: PlatformCredential) -> Dict[str, Any]:
        """Test platform API connection"""
        try:
            headers = {}
            
            if credentials.bearer_token:
                headers["Authorization"] = f"Bearer {credentials.bearer_token}"
            elif credentials.access_token:
                headers["Authorization"] = f"Bearer {credentials.access_token}"
            elif credentials.api_key:
                headers["X-API-Key"] = credentials.api_key
            
            async with httpx.AsyncClient() as client:
                if platform.name == "twitter":
                    response = await client.get(
                        f"{platform.base_url}/users/me",
                        headers=headers,
                        timeout=10.0
                    )
                elif platform.name == "instagram":
                    response = await client.get(
                        f"{platform.base_url}/me",
                        params={"access_token": credentials.access_token},
                        timeout=10.0
                    )
                elif platform.name == "linkedin":
                    response = await client.get(
                        f"{platform.base_url}/me",
                        headers=headers,
                        timeout=10.0
                    )
                elif platform.name == "facebook":
                    response = await client.get(
                        f"{platform.base_url}/me",
                        params={"access_token": credentials.access_token},
                        timeout=10.0
                    )
                elif platform.name == "youtube":
                    response = await client.get(
                        f"{platform.base_url}/channels",
                        params={"part": "snippet", "mine": "true", "key": credentials.api_key},
                        timeout=10.0
                    )
                else:
                    # Generic test for other platforms
                    response = await client.get(
                        f"{platform.base_url}/me",
                        headers=headers,
                        timeout=10.0
                    )
                
                if response.status_code == 200:
                    return {"success": True, "message": "API connection successful"}
                else:
                    return {"success": False, "error": f"API returned status {response.status_code}"}
                    
        except Exception as e:
            logger.error(f"Platform API test failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def post_to_platform(
        self, 
        user_id: int, 
        platform_name: str, 
        content: str, 
        media_urls: List[str] = None,
        scheduled_time: datetime = None
    ) -> Dict[str, Any]:
        """Post content to a social media platform"""
        try:
            # Check user billing limits
            billing = await get_billing()
            limit_check = await billing.check_user_limits(user_id, api_call=True)
            
            if not limit_check["allowed"]:
                return {"success": False, "error": limit_check["reason"]}
            
            # Get platform credentials
            db = get_database()
            async with db.get_session() as session:
                credentials = await session.execute(
                    select(PlatformCredential, SocialPlatform)
                    .join(SocialPlatform)
                    .where(
                        and_(
                            SocialPlatform.name == platform_name,
                            PlatformCredential.user_id == user_id,
                            PlatformCredential.status == CredentialStatus.VALID
                        )
                    )
                )
                result = credentials.first()
                
                if not result:
                    return {"success": False, "error": "No valid credentials found for this platform"}
                
                cred, platform = result
                
                # Check if platform supports posting
                if not platform.supported_features.get("posting", False):
                    return {"success": False, "error": "This platform does not support posting"}
                
                # Make the actual API call to post
                post_result = await self._make_platform_post(platform, cred, content, media_urls, scheduled_time)
                
                if post_result["success"]:
                    # Record usage
                    await billing.record_usage(user_id, api_call=True)
                    
                    # Log activity
                    from ..user_management import get_user_manager
                    user_mgr = await get_user_manager()
                    await user_mgr.log_user_activity(
                        user_id=user_id,
                        activity_type="agent_access",
                        description=f"Posted to {platform.display_name}",
                        metadata={
                            "platform": platform_name,
                            "content_length": len(content),
                            "media_count": len(media_urls) if media_urls else 0,
                            "scheduled": scheduled_time is not None
                        }
                    )
                
                return post_result
                
        except Exception as e:
            logger.error(f"Failed to post to platform: {e}")
            return {"success": False, "error": str(e)}
    
    async def _make_platform_post(
        self, 
        platform: SocialPlatform, 
        credentials: PlatformCredential, 
        content: str, 
        media_urls: List[str] = None,
        scheduled_time: datetime = None
    ) -> Dict[str, Any]:
        """Make the actual API call to post content"""
        try:
            headers = {}
            params = {}
            
            if credentials.bearer_token:
                headers["Authorization"] = f"Bearer {credentials.bearer_token}"
            elif credentials.access_token:
                headers["Authorization"] = f"Bearer {credentials.access_token}"
            elif credentials.api_key:
                headers["X-API-Key"] = credentials.api_key
            
            post_data = {"text": content}
            
            if media_urls:
                post_data["media"] = {"media_ids": media_urls}
            
            if scheduled_time:
                post_data["scheduled_at"] = scheduled_time.isoformat()
            
            async with httpx.AsyncClient() as client:
                if platform.name == "twitter":
                    response = await client.post(
                        f"{platform.base_url}/tweets",
                        json=post_data,
                        headers=headers,
                        timeout=30.0
                    )
                elif platform.name == "linkedin":
                    response = await client.post(
                        f"{platform.base_url}/ugcPosts",
                        json=post_data,
                        headers=headers,
                        timeout=30.0
                    )
                elif platform.name == "facebook":
                    response = await client.post(
                        f"{platform.base_url}/me/feed",
                        params={"access_token": credentials.access_token, "message": content},
                        timeout=30.0
                    )
                else:
                    # Generic post for other platforms
                    response = await client.post(
                        f"{platform.base_url}/posts",
                        json=post_data,
                        headers=headers,
                        timeout=30.0
                    )
                
                if response.status_code in [200, 201]:
                    return {
                        "success": True,
                        "message": f"Successfully posted to {platform.display_name}",
                        "post_id": response.json().get("id"),
                        "response": response.json()
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Platform API returned status {response.status_code}",
                        "response": response.text
                    }
                    
        except Exception as e:
            logger.error(f"Platform post failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_platform_analytics(
        self, 
        user_id: int, 
        platform_name: str, 
        metric_type: str,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """Get analytics data from a platform"""
        try:
            # Check user billing limits
            billing = await get_billing()
            limit_check = await billing.check_user_limits(user_id, api_call=True)
            
            if not limit_check["allowed"]:
                return {"success": False, "error": limit_check["reason"]}
            
            # Get platform credentials
            db = get_database()
            async with db.get_session() as session:
                credentials = await session.execute(
                    select(PlatformCredential, SocialPlatform)
                    .join(SocialPlatform)
                    .where(
                        and_(
                            SocialPlatform.name == platform_name,
                            PlatformCredential.user_id == user_id,
                            PlatformCredential.status == CredentialStatus.VALID
                        )
                    )
                )
                result = credentials.first()
                
                if not result:
                    return {"success": False, "error": "No valid credentials found for this platform"}
                
                cred, platform = result
                
                # Check if platform supports analytics
                if not platform.supported_features.get("analytics", False):
                    return {"success": False, "error": "This platform does not support analytics"}
                
                # Make the actual API call to get analytics
                analytics_result = await self._get_platform_analytics(platform, cred, metric_type, start_date, end_date)
                
                if analytics_result["success"]:
                    # Record usage
                    await billing.record_usage(user_id, api_call=True)
                    
                    # Store metrics in database
                    await self._store_platform_metrics(
                        session, platform.id, user_id, metric_type, 
                        analytics_result["data"], start_date
                    )
                
                return analytics_result
                
        except Exception as e:
            logger.error(f"Failed to get platform analytics: {e}")
            return {"success": False, "error": str(e)}
    
    async def _get_platform_analytics(
        self, 
        platform: SocialPlatform, 
        credentials: PlatformCredential, 
        metric_type: str,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """Get analytics data from platform API"""
        try:
            headers = {}
            
            if credentials.bearer_token:
                headers["Authorization"] = f"Bearer {credentials.bearer_token}"
            elif credentials.access_token:
                headers["Authorization"] = f"Bearer {credentials.access_token}"
            elif credentials.api_key:
                headers["X-API-Key"] = credentials.api_key
            
            async with httpx.AsyncClient() as client:
                if platform.name == "twitter":
                    response = await client.get(
                        f"{platform.base_url}/users/me",
                        headers=headers,
                        timeout=10.0
                    )
                elif platform.name == "instagram":
                    response = await client.get(
                        f"{platform.base_url}/me/media",
                        params={"access_token": credentials.access_token},
                        timeout=10.0
                    )
                else:
                    # Generic analytics endpoint
                    response = await client.get(
                        f"{platform.base_url}/analytics",
                        params={"metric": metric_type, "start_date": start_date, "end_date": end_date},
                        headers=headers,
                        timeout=10.0
                    )
                
                if response.status_code == 200:
                    return {
                        "success": True,
                        "data": response.json(),
                        "message": f"Analytics data retrieved from {platform.display_name}"
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Platform API returned status {response.status_code}",
                        "response": response.text
                    }
                    
        except Exception as e:
            logger.error(f"Platform analytics failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _store_platform_metrics(
        self, 
        session: AsyncSession, 
        platform_id: int, 
        user_id: int, 
        metric_type: str, 
        value: float, 
        date: str
    ):
        """Store platform metrics in database"""
        try:
            # Get previous value for change calculation
            previous_metric = await session.execute(
                select(PlatformMetrics).where(
                    and_(
                        PlatformMetrics.platform_id == platform_id,
                        PlatformMetrics.user_id == user_id,
                        PlatformMetrics.metric_type == metric_type
                    )
                ).order_by(PlatformMetrics.date.desc()).limit(1)
            )
            previous_metric = previous_metric.scalar_one_or_none()
            
            previous_value = previous_metric.value if previous_metric else 0.0
            change_percentage = ((value - previous_value) / previous_value * 100) if previous_value > 0 else 0.0
            
            metric = PlatformMetrics(
                platform_id=platform_id,
                user_id=user_id,
                date=date,
                metric_type=metric_type,
                value=value,
                previous_value=previous_value,
                change_percentage=change_percentage
            )
            
            session.add(metric)
            await session.commit()
            
        except Exception as e:
            logger.error(f"Failed to store platform metrics: {e}")
    
    async def health_check(self) -> bool:
        """Check platform management system health"""
        try:
            if not self._initialized:
                return False
            
            db = get_database()
            async with db.get_session() as session:
                await session.execute(select(SocialPlatform).limit(1))
            
            return True
        except Exception as e:
            logger.error(f"Platform management health check failed: {e}")
            return False

platform_manager = PlatformManager()

async def get_platform_manager() -> PlatformManager:
    return platform_manager

async def init_platforms():
    await platform_manager.initialize()
