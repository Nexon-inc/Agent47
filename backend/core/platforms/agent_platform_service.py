"""
Agent Platform Service - Easy interface for agents to post on Agent47's platform accounts
This service provides a simple interface for agents to interact with Agent47's own platform accounts
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from .system_platform_manager import get_system_platform_manager, SystemPlatformManager

logger = logging.getLogger(__name__)


class AgentPlatformService:
    """
    Service for agents to easily post and interact with Agent47's platform accounts
    """
    
    def __init__(self, agent_name: str):
        """
        Initialize the service for a specific agent
        
        Args:
            agent_name: Name of the agent (aria, clara, eric, joe, jackie, shakes, purity)
        """
        if agent_name not in ["aria", "clara", "eric", "joe", "jackie", "shakes", "purity"]:
            raise ValueError(f"Invalid agent name: {agent_name}")
        
        self.agent_name = agent_name
        self.system_manager: Optional[SystemPlatformManager] = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize the service"""
        if self._initialized:
            return
        
        self.system_manager = await get_system_platform_manager()
        self._initialized = True
        logger.info(f"AgentPlatformService initialized for agent: {self.agent_name}")
    
    async def get_available_platforms(self) -> List[Dict[str, Any]]:
        """
        Get all platforms this agent has access to
        
        Returns:
            List of platforms with permissions
        """
        if not self._initialized:
            await self.initialize()
        
        return await self.system_manager.get_agent_platforms(self.agent_name)
    
    async def post(
        self,
        platform_name: str,
        content: str,
        media_urls: List[str] = None,
        scheduled_time: Optional[datetime] = None,
        account_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Post content to Agent47's platform account
        
        Args:
            platform_name: Platform to post to (twitter, linkedin, instagram, etc.)
            content: Post content
            media_urls: Optional list of media URLs
            scheduled_time: Optional scheduled time for the post
            account_name: Specific account name if multiple accounts exist
        
        Returns:
            Post result with success status and post details
        """
        if not self._initialized:
            await self.initialize()
        
        return await self.system_manager.agent_post_to_platform(
            agent_name=self.agent_name,
            platform_name=platform_name,
            content=content,
            media_urls=media_urls,
            scheduled_time=scheduled_time,
            account_name=account_name
        )
    
    async def can_post_to(self, platform_name: str) -> bool:
        """
        Check if this agent can post to a platform
        
        Args:
            platform_name: Platform to check
        
        Returns:
            True if agent can post, False otherwise
        """
        platforms = await self.get_available_platforms()
        for platform in platforms:
            if platform["platform_name"] == platform_name:
                return platform.get("permissions", {}).get("can_post", False)
        return False
    
    async def get_platform_info(self, platform_name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific platform
        
        Args:
            platform_name: Platform name
        
        Returns:
            Platform information or None if not accessible
        """
        platforms = await self.get_available_platforms()
        for platform in platforms:
            if platform["platform_name"] == platform_name:
                return platform
        return None


# Convenience function for agents
async def get_agent_platform_service(agent_name: str) -> AgentPlatformService:
    """
    Get an AgentPlatformService instance for an agent
    
    Args:
        agent_name: Name of the agent
    
    Returns:
        AgentPlatformService instance
    """
    service = AgentPlatformService(agent_name)
    await service.initialize()
    return service
