"""
Admin Panel Manager for Agent47's Platform Connections
Provides admin interface for managing Agent47's own platform accounts
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy import text

from backend.core.database import get_database, DatabaseManager
from backend.core.logs import get_logger, LoggerMixin
from backend.core.platforms.system_platform_manager import get_system_platform_manager, SystemPlatformManager
from backend.core.platforms.models import SocialPlatform

logger = get_logger(__name__)

class Agent47PlatformManager(LoggerMixin):
    """
    Admin panel interface for managing Agent47's platform connections
    """
    
    def __init__(self):
        self.database: Optional[DatabaseManager] = None
        self.system_manager: Optional[SystemPlatformManager] = None
        self.logger = logger
        self._initialized = False
    
    async def initialize(self) -> bool:
        try:
            self.logger.info("Initializing Agent47PlatformManager...")
            
            self.database = get_database()
            self.system_manager = await get_system_platform_manager()
            
            self._initialized = True
            self.logger.info("Agent47PlatformManager initialized successfully")
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to initialize Agent47PlatformManager: {str(e)}")
            return False
    
    async def connect_platform(
        self,
        platform_name: str,
        account_name: str,
        account_handle: Optional[str] = None,
        credentials: Dict[str, Any] = None,
        admin_user_id: str = None
    ) -> Dict[str, Any]:
        """Connect Agent47 to a platform"""
        if not self._initialized:
            await self.initialize()
        
        return await self.system_manager.connect_platform(
            platform_name=platform_name,
            account_name=account_name,
            account_handle=account_handle,
            credentials=credentials,
            created_by=admin_user_id
        )
    
    async def disconnect_platform(self, credential_id: int, admin_user_id: str = None) -> bool:
        """Disconnect Agent47 from a platform"""
        if not self._initialized:
            await self.initialize()
        
        return await self.system_manager.disconnect_platform(credential_id, admin_user_id)
    
    async def get_all_connections(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get all Agent47 platform connections"""
        if not self._initialized:
            await self.initialize()
        
        return await self.system_manager.get_all_connections(active_only)
    
    async def assign_agent_to_platform(
        self,
        credential_id: int,
        agent_name: str,
        permissions: Dict[str, bool] = None,
        priority: int = 0,
        admin_user_id: str = None
    ) -> bool:
        """Assign an agent to a platform"""
        if not self._initialized:
            await self.initialize()
        
        return await self.system_manager.assign_agent_to_platform(
            credential_id=credential_id,
            agent_name=agent_name,
            permissions=permissions,
            priority=priority,
            created_by=admin_user_id
        )
    
    async def remove_agent_from_platform(self, credential_id: int, agent_name: str) -> bool:
        """Remove an agent from a platform"""
        if not self._initialized:
            await self.initialize()
        
        return await self.system_manager.remove_agent_from_platform(credential_id, agent_name)
    
    async def get_agent_platforms(self, agent_name: str) -> List[Dict[str, Any]]:
        """Get all platforms an agent has access to"""
        if not self._initialized:
            await self.initialize()
        
        return await self.system_manager.get_agent_platforms(agent_name)
    
    async def get_all_agents_platforms(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get platforms for all agents"""
        if not self._initialized:
            await self.initialize()
        
        agents_platforms = {}
        for agent_name in ["aria", "clara", "eric", "joe", "jackie", "shakes", "purity"]:
            agents_platforms[agent_name] = await self.system_manager.get_agent_platforms(agent_name)
        
        return agents_platforms
    
    async def get_platform_statistics(self, platform_name: Optional[str] = None) -> Dict[str, Any]:
        """Get platform usage statistics"""
        if not self._initialized:
            await self.initialize()
        
        return await self.system_manager.get_platform_statistics(platform_name)
    
    async def get_available_platforms(self) -> List[Dict[str, Any]]:
        """Get all available platforms that can be connected"""
        if not self.database:
            return []
        
        try:
            async with self.database.get_session() as session:
                result = await session.execute(
                    text("""
                        SELECT id, name, display_name, platform_type, description,
                               supported_features, authentication_methods, status
                        FROM social_platforms
                        WHERE is_available = TRUE
                        ORDER BY display_name
                    """)
                )
                
                platforms = []
                for row in result.fetchall():
                    platforms.append({
                        "id": row[0],
                        "name": row[1],
                        "display_name": row[2],
                        "platform_type": row[3],
                        "description": row[4],
                        "supported_features": row[5] if row[5] else {},
                        "authentication_methods": row[6] if row[6] else {},
                        "status": row[7]
                    })
                
                return platforms
        
        except Exception as e:
            self.logger.error(f"Failed to get available platforms: {str(e)}")
            return []
    
    async def update_agent_permissions(
        self,
        credential_id: int,
        agent_name: str,
        permissions: Dict[str, bool],
        admin_user_id: str = None
    ) -> bool:
        """Update agent permissions for a platform"""
        if not self._initialized:
            await self.initialize()
        
        return await self.system_manager.assign_agent_to_platform(
            credential_id=credential_id,
            agent_name=agent_name,
            permissions=permissions,
            created_by=admin_user_id
        )


# Global instance
_agent47_platform_manager: Optional[Agent47PlatformManager] = None

async def init_agent47_platform_manager() -> Agent47PlatformManager:
    global _agent47_platform_manager
    if not _agent47_platform_manager:
        _agent47_platform_manager = Agent47PlatformManager()
        await _agent47_platform_manager.initialize()
    return _agent47_platform_manager

async def get_agent47_platform_manager() -> Agent47PlatformManager:
    global _agent47_platform_manager
    if not _agent47_platform_manager:
        _agent47_platform_manager = await init_agent47_platform_manager()
    return _agent47_platform_manager

