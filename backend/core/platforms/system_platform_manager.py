"""
System Platform Manager for Agent47
Manages Agent47's own platform accounts and agent access to them
"""

import asyncio
import uuid
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, TYPE_CHECKING
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, update, text
from sqlalchemy.orm import selectinload
import logging

from ..database import get_database
from ..logs import get_logger, LoggerMixin

if TYPE_CHECKING:
    from ..database import DatabaseManager
from .models import SocialPlatform, PlatformType, PlatformStatus
from .system_platform_models import (
    SystemPlatformCredential, AgentPlatformAssignment, SystemPlatformPost,
    SystemPlatformActivity, SystemPlatformConnectionStatus
)
from .oauth_service import get_oauth_service
from .platform_configs import get_platform_config_manager

logger = get_logger(__name__)

# All 7 agents
AGENT_NAMES = ["aria", "clara", "eric", "joe", "jackie", "shakes", "purity"]


class SystemPlatformManager(LoggerMixin):
    """
    Manages Agent47's own platform connections and agent access
    """
    
    def __init__(self):
        self.database: Optional[DatabaseManager] = None
        self.oauth_service = None
        self.config_manager = None
        self.logger = logger
        self._initialized = False
    
    async def initialize(self):
        """Initialize the system platform manager"""
        if self._initialized:
            return
        
        try:
            self.database = get_database()
            self.oauth_service = await get_oauth_service()
            self.config_manager = await get_platform_config_manager()
            
            await self._setup_tables()
            
            self._initialized = True
            self.logger.info("SystemPlatformManager initialized successfully")
        
        except Exception as e:
            self.logger.error(f"Failed to initialize SystemPlatformManager: {str(e)}")
            raise
    
    async def _setup_tables(self):
        """Ensure all tables exist"""
        # Tables are created via SQLAlchemy models, but we can verify here
        if not self.database:
            return
        
        async with self.database.get_session() as session:
            # Verify tables exist by checking if we can query them
            try:
                await session.execute(text("SELECT 1 FROM system_platform_credentials LIMIT 1"))
            except Exception:
                # Tables will be created by Alembic migrations
                self.logger.info("System platform tables will be created by migrations")
    
    # ============================================================================
    # PLATFORM CONNECTION MANAGEMENT
    # ============================================================================
    
    async def connect_platform(
        self,
        platform_name: str,
        account_name: str,
        account_handle: Optional[str] = None,
        credentials: Dict[str, Any] = None,
        created_by: str = None
    ) -> Dict[str, Any]:
        """
        Connect Agent47's account to a platform
        
        Args:
            platform_name: Name of the platform (twitter, linkedin, etc.)
            account_name: Display name for this account (e.g., "Agent47 Official")
            account_handle: Handle/username on the platform
            credentials: Platform credentials (access_token, refresh_token, etc.)
            created_by: Admin user who created this connection
        
        Returns:
            Connection details
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            async with self.database.get_session() as session:
                # Get platform
                platform_result = await session.execute(
                    select(SocialPlatform).where(SocialPlatform.name == platform_name)
                )
                platform = platform_result.scalar_one_or_none()
                
                if not platform:
                    return {
                        "success": False,
                        "error": f"Platform '{platform_name}' not found"
                    }
                
                # Check if connection already exists
                existing = await session.execute(
                    select(SystemPlatformCredential).where(
                        and_(
                            SystemPlatformCredential.platform_id == platform.id,
                            SystemPlatformCredential.account_name == account_name,
                            SystemPlatformCredential.is_active == True
                        )
                    )
                )
                
                if existing.scalar_one_or_none():
                    return {
                        "success": False,
                        "error": f"Active connection already exists for {account_name} on {platform_name}"
                    }
                
                # Encrypt credentials (in production, use proper encryption)
                encrypted_creds = self._encrypt_credentials(credentials or {})
                
                # Create system platform credential
                credential = SystemPlatformCredential(
                    platform_id=platform.id,
                    account_name=account_name,
                    account_handle=account_handle,
                    credential_type=credentials.get("type", "oauth2") if credentials else "oauth2",
                    access_token=encrypted_creds.get("access_token"),
                    refresh_token=encrypted_creds.get("refresh_token"),
                    api_key=encrypted_creds.get("api_key"),
                    api_secret=encrypted_creds.get("api_secret"),
                    bearer_token=encrypted_creds.get("bearer_token"),
                    expires_at=datetime.fromisoformat(credentials["expires_at"]) if credentials and credentials.get("expires_at") else None,
                    scopes=credentials.get("scopes", []) if credentials else [],
                    status=SystemPlatformConnectionStatus.CONNECTED,
                    meta_data=credentials.get("metadata", {}) if credentials else {},
                    is_active=True,
                    created_by=created_by
                )
                
                session.add(credential)
                await session.flush()
                
                # Assign all agents by default
                await self._assign_all_agents_to_credential(session, credential.id, created_by)
                
                await session.commit()
                
                self.logger.info(f"Connected Agent47 account '{account_name}' to {platform_name}")
                
                return {
                    "success": True,
                    "credential_id": credential.id,
                    "platform": platform_name,
                    "account_name": account_name,
                    "account_handle": account_handle,
                    "status": credential.status.value
                }
        
        except Exception as e:
            self.logger.error(f"Failed to connect platform: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _assign_all_agents_to_credential(
        self,
        session: AsyncSession,
        credential_id: int,
        created_by: str = None
    ):
        """Assign all 7 agents to a platform credential by default"""
        for agent_name in AGENT_NAMES:
            assignment = AgentPlatformAssignment(
                credential_id=credential_id,
                agent_name=agent_name,
                permissions={
                    "can_post": True,
                    "can_read": True,
                    "can_engage": True,
                    "can_analyze": True,
                    "can_schedule": True,
                    "can_moderate": False,
                    "can_delete": False
                },
                is_active=True,
                priority=0,
                created_by=created_by
            )
            session.add(assignment)
    
    async def disconnect_platform(self, credential_id: int, disconnected_by: str = None) -> bool:
        """Disconnect a platform connection"""
        try:
            async with self.database.get_session() as session:
                credential = await session.get(SystemPlatformCredential, credential_id)
                if not credential:
                    return False
                
                credential.is_active = False
                credential.status = SystemPlatformConnectionStatus.DISCONNECTED
                credential.updated_at = datetime.utcnow()
                
                # Deactivate all agent assignments
                await session.execute(
                    update(AgentPlatformAssignment)
                    .where(AgentPlatformAssignment.credential_id == credential_id)
                    .values(is_active=False)
                )
                
                await session.commit()
                
                self.logger.info(f"Disconnected platform credential {credential_id}")
                return True
        
        except Exception as e:
            self.logger.error(f"Failed to disconnect platform: {str(e)}")
            return False
    
    async def get_all_connections(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get all system platform connections"""
        try:
            async with self.database.get_session() as session:
                query = select(SystemPlatformCredential).options(
                    selectinload(SystemPlatformCredential.platform),
                    selectinload(SystemPlatformCredential.agent_assignments)
                )
                
                if active_only:
                    query = query.where(SystemPlatformCredential.is_active == True)
                
                result = await session.execute(query)
                credentials = result.scalars().all()
                
                connections = []
                for cred in credentials:
                    connections.append({
                        "id": cred.id,
                        "platform": cred.platform.name if cred.platform else None,
                        "platform_display_name": cred.platform.display_name if cred.platform else None,
                        "account_name": cred.account_name,
                        "account_handle": cred.account_handle,
                        "status": cred.status.value,
                        "is_active": cred.is_active,
                        "last_used": cred.last_used.isoformat() if cred.last_used else None,
                        "last_used_by_agent": cred.last_used_by_agent,
                        "assigned_agents": [
                            {
                                "agent_name": assignment.agent_name,
                                "is_active": assignment.is_active,
                                "permissions": assignment.permissions,
                                "usage_count": assignment.usage_count
                            }
                            for assignment in cred.agent_assignments
                        ],
                        "created_at": cred.created_at.isoformat() if cred.created_at else None
                    })
                
                return connections
        
        except Exception as e:
            self.logger.error(f"Failed to get connections: {str(e)}")
            return []
    
    # ============================================================================
    # AGENT-PLATFORM ASSIGNMENT
    # ============================================================================
    
    async def assign_agent_to_platform(
        self,
        credential_id: int,
        agent_name: str,
        permissions: Dict[str, bool] = None,
        priority: int = 0,
        created_by: str = None
    ) -> bool:
        """Assign an agent to a platform connection"""
        if agent_name not in AGENT_NAMES:
            return False
        
        try:
            async with self.database.get_session() as session:
                # Check if assignment already exists
                existing = await session.execute(
                    select(AgentPlatformAssignment).where(
                        and_(
                            AgentPlatformAssignment.credential_id == credential_id,
                            AgentPlatformAssignment.agent_name == agent_name
                        )
                    )
                )
                assignment = existing.scalar_one_or_none()
                
                if assignment:
                    # Update existing assignment
                    assignment.permissions = permissions or assignment.permissions
                    assignment.priority = priority
                    assignment.is_active = True
                    assignment.updated_at = datetime.utcnow()
                else:
                    # Create new assignment
                    assignment = AgentPlatformAssignment(
                        credential_id=credential_id,
                        agent_name=agent_name,
                        permissions=permissions or {
                            "can_post": True,
                            "can_read": True,
                            "can_engage": True,
                            "can_analyze": True,
                            "can_schedule": True
                        },
                        priority=priority,
                        is_active=True,
                        created_by=created_by
                    )
                    session.add(assignment)
                
                await session.commit()
                
                self.logger.info(f"Assigned agent {agent_name} to credential {credential_id}")
                return True
        
        except Exception as e:
            self.logger.error(f"Failed to assign agent: {str(e)}")
            return False
    
    async def remove_agent_from_platform(self, credential_id: int, agent_name: str) -> bool:
        """Remove an agent from a platform connection"""
        try:
            async with self.database.get_session() as session:
                await session.execute(
                    update(AgentPlatformAssignment)
                    .where(
                        and_(
                            AgentPlatformAssignment.credential_id == credential_id,
                            AgentPlatformAssignment.agent_name == agent_name
                        )
                    )
                    .values(is_active=False)
                )
                await session.commit()
                return True
        except Exception as e:
            self.logger.error(f"Failed to remove agent: {str(e)}")
            return False
    
    async def get_agent_platforms(self, agent_name: str) -> List[Dict[str, Any]]:
        """Get all platforms an agent has access to"""
        if agent_name not in AGENT_NAMES:
            return []
        
        try:
            async with self.database.get_session() as session:
                result = await session.execute(
                    select(AgentPlatformAssignment, SystemPlatformCredential, SocialPlatform)
                    .join(SystemPlatformCredential, AgentPlatformAssignment.credential_id == SystemPlatformCredential.id)
                    .join(SocialPlatform, SystemPlatformCredential.platform_id == SocialPlatform.id)
                    .where(
                        and_(
                            AgentPlatformAssignment.agent_name == agent_name,
                            AgentPlatformAssignment.is_active == True,
                            SystemPlatformCredential.is_active == True
                        )
                    )
                    .order_by(AgentPlatformAssignment.priority.desc())
                )
                
                platforms = []
                for assignment, credential, platform in result.all():
                    platforms.append({
                        "credential_id": credential.id,
                        "platform_name": platform.name,
                        "platform_display_name": platform.display_name,
                        "account_name": credential.account_name,
                        "account_handle": credential.account_handle,
                        "permissions": assignment.permissions,
                        "priority": assignment.priority,
                        "usage_count": assignment.usage_count,
                        "last_used_at": assignment.last_used_at.isoformat() if assignment.last_used_at else None
                    })
                
                return platforms
        
        except Exception as e:
            self.logger.error(f"Failed to get agent platforms: {str(e)}")
            return []
    
    # ============================================================================
    # AGENT PLATFORM OPERATIONS
    # ============================================================================
    
    async def agent_post_to_platform(
        self,
        agent_name: str,
        platform_name: str,
        content: str,
        media_urls: List[str] = None,
        scheduled_time: Optional[datetime] = None,
        account_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Allow an agent to post to Agent47's platform account
        
        Args:
            agent_name: Name of the agent (aria, clara, etc.)
            platform_name: Platform to post to
            content: Post content
            media_urls: Optional media URLs
            scheduled_time: Optional scheduled time
            account_name: Specific account name if multiple accounts exist
        
        Returns:
            Post result
        """
        if agent_name not in AGENT_NAMES:
            return {
                "success": False,
                "error": f"Invalid agent name: {agent_name}"
            }
        
        try:
            async with self.database.get_session() as session:
                # Find the credential
                query = select(SystemPlatformCredential, SocialPlatform, AgentPlatformAssignment).join(
                    SocialPlatform, SystemPlatformCredential.platform_id == SocialPlatform.id
                ).join(
                    AgentPlatformAssignment, AgentPlatformAssignment.credential_id == SystemPlatformCredential.id
                ).where(
                    and_(
                        SocialPlatform.name == platform_name,
                        SystemPlatformCredential.is_active == True,
                        AgentPlatformAssignment.agent_name == agent_name,
                        AgentPlatformAssignment.is_active == True
                    )
                )
                
                if account_name:
                    query = query.where(SystemPlatformCredential.account_name == account_name)
                
                query = query.order_by(AgentPlatformAssignment.priority.desc())
                
                result = await session.execute(query)
                row = result.first()
                
                if not row:
                    return {
                        "success": False,
                        "error": f"Agent {agent_name} does not have access to {platform_name}"
                    }
                
                credential, platform, assignment = row
                
                # Check permissions
                if not assignment.permissions.get("can_post", False):
                    return {
                        "success": False,
                        "error": f"Agent {agent_name} does not have permission to post"
                    }
                
                # Decrypt credentials
                decrypted_creds = self._decrypt_credentials(credential)
                
                # Make the actual post via platform API
                post_result = await self._make_platform_post(
                    platform,
                    decrypted_creds,
                    content,
                    media_urls,
                    scheduled_time
                )
                
                # Record the post
                platform_post = SystemPlatformPost(
                    credential_id=credential.id,
                    agent_name=agent_name,
                    platform_id=platform.id,
                    content=content,
                    media_urls=media_urls or [],
                    scheduled_time=scheduled_time,
                    posted_at=datetime.utcnow() if not scheduled_time else None,
                    platform_post_id=post_result.get("post_id"),
                    platform_post_url=post_result.get("post_url"),
                    status="posted" if post_result.get("success") else "failed",
                    error_message=post_result.get("error"),
                    meta_data=post_result.get("metadata", {})
                )
                session.add(platform_post)
                
                # Update credential and assignment usage
                credential.last_used = datetime.utcnow()
                credential.last_used_by_agent = agent_name
                assignment.last_used_at = datetime.utcnow()
                assignment.usage_count += 1
                
                # Log activity
                activity = SystemPlatformActivity(
                    credential_id=credential.id,
                    agent_name=agent_name,
                    platform_id=platform.id,
                    activity_type="post",
                    activity_data={
                        "content_length": len(content),
                        "has_media": bool(media_urls),
                        "scheduled": scheduled_time is not None
                    },
                    success=post_result.get("success", False),
                    error_message=post_result.get("error")
                )
                session.add(activity)
                
                await session.commit()
                
                return {
                    "success": post_result.get("success", False),
                    "post_id": post_result.get("post_id"),
                    "post_url": post_result.get("post_url"),
                    "platform": platform_name,
                    "account": credential.account_name,
                    "agent": agent_name
                }
        
        except Exception as e:
            self.logger.error(f"Failed to post to platform: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _make_platform_post(
        self,
        platform: SocialPlatform,
        credentials: Dict[str, Any],
        content: str,
        media_urls: List[str] = None,
        scheduled_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Make an actual post to the platform API
        Integrates with real platform APIs
        """
        try:
            import httpx
            
            platform_name = platform.name.lower()
            access_token = credentials.get('access_token')
            
            if not access_token:
                return {
                    "success": False,
                    "error": "No access token available"
                }
            
            # Route to appropriate platform API handler
            if platform_name == "twitter" or platform_name == "x":
                return await self._post_to_twitter(credentials, content, media_urls)
            elif platform_name == "linkedin":
                return await self._post_to_linkedin(credentials, content, media_urls)
            elif platform_name == "facebook":
                return await self._post_to_facebook(credentials, content, media_urls)
            elif platform_name == "instagram":
                return await self._post_to_instagram(credentials, content, media_urls)
            else:
                # Generic API call for other platforms
                return await self._post_to_generic_platform(platform, credentials, content, media_urls)
        
        except Exception as e:
            self.logger.error(f"Failed to post to {platform.name}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _post_to_twitter(self, credentials: Dict[str, Any], content: str, media_urls: List[str] = None) -> Dict[str, Any]:
        """Post to Twitter/X API"""
        try:
            import httpx
            
            access_token = credentials.get('access_token')
            api_key = credentials.get('api_key')
            api_secret = credentials.get('api_secret')
            
            # Twitter API v2 endpoint
            url = "https://api.twitter.com/2/tweets"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            payload = {"text": content}
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=payload, timeout=30.0)
                response.raise_for_status()
                data = response.json()
                
                return {
                    "success": True,
                    "post_id": data.get("data", {}).get("id"),
                    "post_url": f"https://twitter.com/i/web/status/{data.get('data', {}).get('id')}",
                    "metadata": {
                        "platform": "twitter",
                        "posted_at": datetime.utcnow().isoformat()
                    }
                }
        except httpx.HTTPStatusError as e:
            return {
                "success": False,
                "error": f"Twitter API error: {e.response.status_code} - {e.response.text}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to post to Twitter: {str(e)}"
            }
    
    async def _post_to_linkedin(self, credentials: Dict[str, Any], content: str, media_urls: List[str] = None) -> Dict[str, Any]:
        """Post to LinkedIn API"""
        try:
            import httpx
            
            access_token = credentials.get('access_token')
            
            # LinkedIn API endpoint for posts
            url = "https://api.linkedin.com/v2/ugcPosts"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "X-Restli-Protocol-Version": "2.0.0"
            }
            
            # LinkedIn requires specific format
            payload = {
                "author": f"urn:li:person:{credentials.get('user_id', '')}",
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {
                            "text": content
                        },
                        "shareMediaCategory": "NONE"
                    }
                },
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
                }
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=payload, timeout=30.0)
                response.raise_for_status()
                data = response.json()
                
                return {
                    "success": True,
                    "post_id": data.get("id", "").split(":")[-1] if data.get("id") else None,
                    "post_url": f"https://www.linkedin.com/feed/update/{data.get('id', '').split(':')[-1] if data.get('id') else ''}",
                    "metadata": {
                        "platform": "linkedin",
                        "posted_at": datetime.utcnow().isoformat()
                    }
                }
        except httpx.HTTPStatusError as e:
            return {
                "success": False,
                "error": f"LinkedIn API error: {e.response.status_code} - {e.response.text}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to post to LinkedIn: {str(e)}"
            }
    
    async def _post_to_facebook(self, credentials: Dict[str, Any], content: str, media_urls: List[str] = None) -> Dict[str, Any]:
        """Post to Facebook API"""
        try:
            import httpx
            
            access_token = credentials.get('access_token')
            page_id = credentials.get('page_id') or credentials.get('user_id')
            
            # Facebook Graph API endpoint
            url = f"https://graph.facebook.com/v18.0/{page_id}/feed"
            params = {
                "message": content,
                "access_token": access_token
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, params=params, timeout=30.0)
                response.raise_for_status()
                data = response.json()
                
                return {
                    "success": True,
                    "post_id": data.get("id"),
                    "post_url": f"https://www.facebook.com/{data.get('id', '')}",
                    "metadata": {
                        "platform": "facebook",
                        "posted_at": datetime.utcnow().isoformat()
                    }
                }
        except httpx.HTTPStatusError as e:
            return {
                "success": False,
                "error": f"Facebook API error: {e.response.status_code} - {e.response.text}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to post to Facebook: {str(e)}"
            }
    
    async def _post_to_instagram(self, credentials: Dict[str, Any], content: str, media_urls: List[str] = None) -> Dict[str, Any]:
        """Post to Instagram API"""
        try:
            import httpx
            
            access_token = credentials.get('access_token')
            page_id = credentials.get('instagram_business_account_id')
            
            if not page_id:
                return {
                    "success": False,
                    "error": "Instagram Business Account ID required"
                }
            
            # Instagram Graph API endpoint
            url = f"https://graph.facebook.com/v18.0/{page_id}/media"
            params = {
                "caption": content,
                "access_token": access_token
            }
            
            # If media URLs provided, add them
            if media_urls and len(media_urls) > 0:
                params["image_url"] = media_urls[0]
            
            async with httpx.AsyncClient() as client:
                # First, create media container
                response = await client.post(url, params=params, timeout=30.0)
                response.raise_for_status()
                container_data = response.json()
                
                # Then publish the media
                publish_url = f"https://graph.facebook.com/v18.0/{page_id}/media_publish"
                publish_params = {
                    "creation_id": container_data.get("id"),
                    "access_token": access_token
                }
                
                publish_response = await client.post(publish_url, params=publish_params, timeout=30.0)
                publish_response.raise_for_status()
                publish_data = publish_response.json()
                
                return {
                    "success": True,
                    "post_id": publish_data.get("id"),
                    "post_url": f"https://www.instagram.com/p/{publish_data.get('id', '')}",
                    "metadata": {
                        "platform": "instagram",
                        "posted_at": datetime.utcnow().isoformat()
                    }
                }
        except httpx.HTTPStatusError as e:
            return {
                "success": False,
                "error": f"Instagram API error: {e.response.status_code} - {e.response.text}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to post to Instagram: {str(e)}"
            }
    
    async def _post_to_generic_platform(
        self,
        platform: SocialPlatform,
        credentials: Dict[str, Any],
        content: str,
        media_urls: List[str] = None
    ) -> Dict[str, Any]:
        """Generic platform posting handler"""
        try:
            import httpx
            
            access_token = credentials.get('access_token')
            api_url = credentials.get('api_url') or platform.api_endpoint
            
            if not api_url:
                return {
                    "success": False,
                    "error": f"No API endpoint configured for {platform.name}"
                }
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "content": content,
                "media_urls": media_urls or []
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(api_url, headers=headers, json=payload, timeout=30.0)
                response.raise_for_status()
                data = response.json()
                
                return {
                    "success": True,
                    "post_id": data.get("id") or data.get("post_id"),
                    "post_url": data.get("url") or data.get("post_url"),
                    "metadata": {
                        "platform": platform.name,
                        "posted_at": datetime.utcnow().isoformat()
                    }
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to post to {platform.name}: {str(e)}"
            }
    
    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    
    def _encrypt_credentials(self, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """Encrypt platform credentials (placeholder - use proper encryption in production)"""
        # In production, use proper encryption like Fernet or AWS KMS
        # For now, we'll just return as-is (but mark as needing encryption)
        return credentials
    
    def _decrypt_credentials(self, credential: SystemPlatformCredential) -> Dict[str, Any]:
        """Decrypt platform credentials"""
        return {
            "access_token": credential.access_token,
            "refresh_token": credential.refresh_token,
            "api_key": credential.api_key,
            "api_secret": credential.api_secret,
            "bearer_token": credential.bearer_token,
            "type": credential.credential_type,
            "scopes": credential.scopes or []
        }
    
    async def get_platform_statistics(self, platform_name: Optional[str] = None) -> Dict[str, Any]:
        """Get statistics about platform usage"""
        try:
            async with self.database.get_session() as session:
                # Get total connections
                query = select(func.count(SystemPlatformCredential.id)).where(
                    SystemPlatformCredential.is_active == True
                )
                if platform_name:
                    query = query.join(SocialPlatform).where(SocialPlatform.name == platform_name)
                
                total_connections = (await session.execute(query)).scalar()
                
                # Get total posts
                posts_query = select(func.count(SystemPlatformPost.id))
                if platform_name:
                    posts_query = posts_query.join(SocialPlatform).where(SocialPlatform.name == platform_name)
                
                total_posts = (await session.execute(posts_query)).scalar()
                
                # Get agent usage
                agent_usage = {}
                for agent in AGENT_NAMES:
                    usage_query = select(func.sum(AgentPlatformAssignment.usage_count)).where(
                        AgentPlatformAssignment.agent_name == agent
                    )
                    agent_usage[agent] = (await session.execute(usage_query)).scalar() or 0
                
                return {
                    "total_connections": total_connections,
                    "total_posts": total_posts,
                    "agent_usage": agent_usage
                }
        
        except Exception as e:
            self.logger.error(f"Failed to get statistics: {str(e)}")
            return {}


# Global instance
_system_platform_manager: Optional[SystemPlatformManager] = None

async def get_system_platform_manager() -> SystemPlatformManager:
    """Get the global system platform manager instance"""
    global _system_platform_manager
    if not _system_platform_manager:
        _system_platform_manager = SystemPlatformManager()
        await _system_platform_manager.initialize()
    return _system_platform_manager

