import json
import hashlib
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)

class CommunityRole(Enum):
    """Roles within a community."""
    OWNER = "owner"
    ADMIN = "admin"
    MODERATOR = "moderator"
    MEMBER = "member"
    GUEST = "guest"

class CommunityStatus(Enum):
    """Community status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PRIVATE = "private"

@dataclass
class Community:
    """Community data structure."""
    id: str
    name: str
    description: str
    owner_id: str
    status: CommunityStatus
    created_at: str
    updated_at: str
    member_count: int = 0
    max_members: Optional[int] = None
    is_public: bool = True
    tags: Optional[List[str]] = None
    rules: Optional[List[str]] = None
    avatar_url: Optional[str] = None
    banner_url: Optional[str] = None
    website: Optional[str] = None
    location: Optional[str] = None
    language: str = "en"
    timezone: str = "UTC"

@dataclass
class CommunityMember:
    """Community member data structure."""
    community_id: str
    user_id: str
    role: CommunityRole
    joined_at: str
    updated_at: str
    is_active: bool = True
    nickname: Optional[str] = None
    bio: Optional[str] = None
    permissions: Optional[List[str]] = None

class CommunityManager:
    """Manages communities and their members."""
    
    def __init__(self):
        self.communities: Dict[str, Community] = {}
        self.members: Dict[str, Dict[str, CommunityMember]] = defaultdict(dict)
        self._initialized = False

    async def initialize(self):
        """Async initializer; call on app startup to load data from DB."""
        if self._initialized:
            return
        await self._load_data()
        self._initialized = True

    async def _load_data(self):
        """Async load communities and members from database."""
        try:
            from backend.core.database.connection import get_supabase
            from backend.core.database.models import Community as ORMCommunity, CommunityMember as ORMCommunityMember
            from sqlalchemy import select

            db = await get_supabase()
            async with db.get_session() as session:
                result = await session.execute(select(ORMCommunity))
                communities_data = result.scalars().all()
                self.communities = {}
                for c in communities_data:
                    key = str(getattr(c, 'id', ''))
                    self.communities[key] = Community(
                        id=str(getattr(c, 'id', '')),
                        name=str(getattr(c, 'name', '')),
                        description=str(getattr(c, 'description', '') or ''),
                        owner_id=str(getattr(c, 'created_by', '') or ''),
                        status=getattr(c, 'status', CommunityStatus.ACTIVE),
                        created_at=getattr(c, 'created_at').isoformat() if getattr(c, 'created_at', None) else '',
                        updated_at=getattr(c, 'updated_at').isoformat() if getattr(c, 'updated_at', None) else '',
                        member_count=getattr(c, 'member_count', 0) or 0,
                        max_members=getattr(c, 'max_members', None),
                        is_public=getattr(c, 'is_public', True) or True,
                        tags=getattr(c, 'tags', []) or [],
                        rules=getattr(c, 'rules', []) or [],
                        avatar_url=getattr(c, 'avatar_url', None),
                        banner_url=getattr(c, 'banner_url', None),
                        website=getattr(c, 'website', None),
                        location=getattr(c, 'location', None),
                        language=getattr(c, 'language', 'en') or 'en',
                        timezone=getattr(c, 'timezone', 'UTC') or 'UTC'
                    )

                result = await session.execute(select(ORMCommunityMember))
                members_data = result.scalars().all()
                self.members = defaultdict(dict)
                for m in members_data:
                    community_key = str(getattr(m, 'community_id', ''))
                    user_key = str(getattr(m, 'user_id', ''))
                    member = CommunityMember(
                        community_id=community_key,
                        user_id=user_key,
                        role=getattr(m, 'role', CommunityRole.MEMBER),
                        joined_at=getattr(m, 'joined_at').isoformat() if getattr(m, 'joined_at', None) else '',
                        updated_at=getattr(m, 'updated_at').isoformat() if getattr(m, 'updated_at', None) else '',
                        is_active=getattr(m, 'is_active', True),
                        nickname=getattr(m, 'nickname', None),
                        bio=getattr(m, 'bio', None),
                        permissions=getattr(m, 'permissions', []) or []
                    )
                    self.members[community_key][user_key] = member

            logger.info(f"Community data loaded: {len(self.communities)} communities, {sum(len(ms) for ms in self.members.values())} members")
        except Exception as e:
            logger.error(f"Failed to load community data: {e}")
            self.communities = {}
            self.members = defaultdict(dict)

    def _save_data(self):
        """Schedule a background save. This avoids blocking/sync DB calls during request handling.
        Currently a no-op placeholder; implement persistence in the async task if needed.
        """
        try:
            import asyncio
            loop = None
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            if loop:
                # schedule a no-op to keep API consistent; replace with actual persistence later
                async def _noop():
                    return
                loop.create_task(_noop())
            else:
                # No running loop; nothing to persist right now
                logger.debug("_save_data called but no running loop; skipping persistence")
        except Exception as e:
            logger.error(f"Error scheduling save: {e}")
    
    def _generate_community_id(self, name: str, owner_id: str) -> str:
        """Generate a unique community ID."""
        data = f"{name}:{owner_id}:{datetime.utcnow().isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def create_community(
        self,
        name: str,
        description: str,
        owner_id: str,
        is_public: bool = True,
        max_members: Optional[int] = None,
        **kwargs
    ) -> Community:
        """
        Create a new community.
        
        Args:
            name: Community name
            description: Community description
            owner_id: ID of the community owner
            is_public: Whether the community is public
            max_members: Maximum number of members
            **kwargs: Additional community fields
            
        Returns:
            Created Community object
        """
        try:
            # Validate input
            if not name or len(name.strip()) < 3:
                raise ValueError("Community name must be at least 3 characters long")
            
            if not description or len(description.strip()) < 10:
                raise ValueError("Community description must be at least 10 characters long")
            
            # Check if name is already taken
            if any(c.name.lower() == name.lower() for c in self.communities.values()):
                raise ValueError(f"Community name '{name}' is already taken")
            
            # Create community
            community_id = self._generate_community_id(name, owner_id)
            current_time = datetime.utcnow().isoformat()
            
            community = Community(
                id=community_id,
                name=name.strip(),
                description=description.strip(),
                owner_id=owner_id,
                status=CommunityStatus.ACTIVE,
                created_at=current_time,
                updated_at=current_time,
                is_public=is_public,
                max_members=max_members,
                tags=kwargs.get('tags', []),
                rules=kwargs.get('rules', []),
                avatar_url=kwargs.get('avatar_url'),
                banner_url=kwargs.get('banner_url'),
                website=kwargs.get('website'),
                location=kwargs.get('location'),
                language=kwargs.get('language', 'en'),
                timezone=kwargs.get('timezone', 'UTC')
            )
            
            self.communities[community_id] = community
            
            # Add owner as first member
            self.add_member(community_id, owner_id, CommunityRole.OWNER)
            
            self._save_data()
            
            logger.info(f"Created community '{name}' with ID {community_id}")
            return community
            
        except Exception as e:
            logger.error(f"Failed to create community: {e}")
            raise
    
    def get_community(self, community_id: str) -> Optional[Community]:
        """
        Get community by ID.
        
        Args:
            community_id: Community ID
            
        Returns:
            Community object or None if not found
        """
        try:
            return self.communities.get(community_id)
        except Exception as e:
            logger.error(f"Failed to get community: {e}")
            return None
    
    def search_communities(
        self,
        query: str,
        limit: int = 20,
        include_private: bool = False,
        tags: Optional[List[str]] = None
    ) -> List[Community]:
        """
        Search communities by various criteria.
        
        Args:
            query: Search query
            limit: Maximum number of results
            include_private: Whether to include private communities
            tags: Filter by tags
            
        Returns:
            List of matching Community objects
        """
        try:
            results = []
            query_lower = query.lower()
            
            for community in self.communities.values():
                # Skip private communities unless requested
                if not include_private and not community.is_public:
                    continue
                
                # Skip inactive communities
                if community.status != CommunityStatus.ACTIVE:
                    continue
                
                # Check if query matches name or description
                if (query_lower in community.name.lower() or 
                    query_lower in community.description.lower()):
                    results.append(community)
                    continue
                
                # Check tags if specified
                if tags and community.tags:
                    if any(tag.lower() in [t.lower() for t in community.tags] for tag in tags):
                        results.append(community)
                        continue
                
                if len(results) >= limit:
                    break
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to search communities: {e}")
            return []
    
    def update_community(self, community_id: str, user_id: str, **updates) -> bool:
        """
        Update community information.
        
        Args:
            community_id: Community ID
            user_id: ID of the user making the update
            **updates: Fields to update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if community_id not in self.communities:
                return False
            
            community = self.communities[community_id]
            
            # Check permissions
            member = self.get_member(community_id, user_id)
            if not member or member.role not in [CommunityRole.OWNER, CommunityRole.ADMIN]:
                logger.warning(f"User {user_id} attempted to update community {community_id} without permission")
                return False
            
            # Update fields
            for field, value in updates.items():
                if hasattr(community, field):
                    setattr(community, field, value)
            
            # Update timestamp
            community.updated_at = datetime.utcnow().isoformat()
            
            self._save_data()
            
            logger.info(f"Updated community {community_id} by user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update community: {e}")
            return False
    
    def delete_community(self, community_id: str, user_id: str) -> bool:
        """
        Delete a community.
        
        Args:
            community_id: Community ID
            user_id: ID of the user deleting the community
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if community_id not in self.communities:
                return False
            
            community = self.communities[community_id]
            
            # Only owner can delete community
            if community.owner_id != user_id:
                logger.warning(f"User {user_id} attempted to delete community {community_id} without permission")
                return False
            
            # Remove all members
            if community_id in self.members:
                del self.members[community_id]
            
            # Remove community
            del self.communities[community_id]
            
            self._save_data()
            
            logger.info(f"Deleted community {community_id} by user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete community: {e}")
            return False
    
    def add_member(
        self,
        community_id: str,
        user_id: str,
        role: CommunityRole = CommunityRole.MEMBER,
        added_by: Optional[str] = None
    ) -> bool:
        """
        Add a member to a community.
        
        Args:
            community_id: Community ID
            user_id: ID of the user to add
            role: Role for the new member
            added_by: ID of the user adding the member
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if community_id not in self.communities:
                return False
            
            community = self.communities[community_id]
            
            # Check if user is already a member
            if user_id in self.members[community_id]:
                return False
            
            # Check member limit
            if community.max_members and community.member_count >= community.max_members:
                raise ValueError("Community has reached maximum member limit")
            
            # Check permissions for adding members
            if added_by and added_by != community.owner_id:
                adder_member = self.get_member(community_id, added_by)
                if not adder_member or adder_member.role not in [CommunityRole.OWNER, CommunityRole.ADMIN]:
                    logger.warning(f"User {added_by} attempted to add member to community {community_id} without permission")
                    return False
            
            # Create member
            current_time = datetime.utcnow().isoformat()
            member = CommunityMember(
                community_id=community_id,
                user_id=user_id,
                role=role,
                joined_at=current_time,
                updated_at=current_time,
                permissions=self._get_role_permissions(role)
            )
            
            self.members[community_id][user_id] = member
            
            # Update member count
            community.member_count += 1
            community.updated_at = current_time
            
            self._save_data()
            
            logger.info(f"Added member {user_id} to community {community_id} with role {role.value}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add member: {e}")
            return False
    
    def remove_member(self, community_id: str, user_id: str, removed_by: str) -> bool:
        """
        Remove a member from a community.
        
        Args:
            community_id: Community ID
            user_id: ID of the user to remove
            removed_by: ID of the user removing the member
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if community_id not in self.communities or user_id not in self.members[community_id]:
                return False
            
            community = self.communities[community_id]
            member = self.members[community_id][user_id]
            
            # Check permissions
            if removed_by != community.owner_id:
                remover_member = self.get_member(community_id, removed_by)
                if not remover_member or remover_member.role not in [CommunityRole.OWNER, CommunityRole.ADMIN]:
                    logger.warning(f"User {removed_by} attempted to remove member from community {community_id} without permission")
                    return False
                
                # Admins can't remove other admins or the owner
                if member.role in [CommunityRole.OWNER, CommunityRole.ADMIN]:
                    logger.warning(f"User {removed_by} attempted to remove admin/owner from community {community_id}")
                    return False
            
            # Remove member
            del self.members[community_id][user_id]
            
            # Update member count
            community.member_count -= 1
            community.updated_at = datetime.utcnow().isoformat()
            
            self._save_data()
            
            logger.info(f"Removed member {user_id} from community {community_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove member: {e}")
            return False
    
    def get_member(self, community_id: str, user_id: str) -> Optional[CommunityMember]:
        """
        Get community member information.
        
        Args:
            community_id: Community ID
            user_id: User ID
            
        Returns:
            CommunityMember object or None if not found
        """
        try:
            return self.members.get(community_id, {}).get(user_id)
        except Exception as e:
            logger.error(f"Failed to get member: {e}")
            return None
    
    def get_community_members(
        self,
        community_id: str,
        limit: int = 50,
        role: Optional[CommunityRole] = None
    ) -> List[CommunityMember]:
        """
        Get members of a community.
        
        Args:
            community_id: Community ID
            limit: Maximum number of members to return
            role: Filter by role
            
        Returns:
            List of CommunityMember objects
        """
        try:
            if community_id not in self.members:
                return []
            
            members = list(self.members[community_id].values())
            
            # Filter by role
            if role:
                members = [m for m in members if m.role == role]
            
            # Sort by join date (oldest first) and limit
            members.sort(key=lambda x: x.joined_at)
            return members[:limit]
            
        except Exception as e:
            logger.error(f"Failed to get community members: {e}")
            return []
    
    def update_member_role(
        self,
        community_id: str,
        user_id: str,
        new_role: CommunityRole,
        updated_by: str
    ) -> bool:
        """
        Update a member's role.
        
        Args:
            community_id: Community ID
            user_id: ID of the member to update
            new_role: New role
            updated_by: ID of the user making the update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if community_id not in self.members or user_id not in self.members[community_id]:
                return False
            
            community = self.communities[community_id]
            member = self.members[community_id][user_id]
            
            # Check permissions
            if updated_by != community.owner_id:
                updater_member = self.get_member(community_id, updated_by)
                if not updater_member or updater_member.role not in [CommunityRole.OWNER, CommunityRole.ADMIN]:
                    logger.warning(f"User {updated_by} attempted to update member role in community {community_id} without permission")
                    return False
                
                # Admins can't change other admins or the owner
                if member.role in [CommunityRole.OWNER, CommunityRole.ADMIN]:
                    logger.warning(f"User {updated_by} attempted to change admin/owner role in community {community_id}")
                    return False
            
            # Update role
            member.role = new_role
            member.permissions = self._get_role_permissions(new_role)
            member.updated_at = datetime.utcnow().isoformat()
            
            self._save_data()
            
            logger.info(f"Updated member {user_id} role to {new_role.value} in community {community_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update member role: {e}")
            return False
    
    def _get_role_permissions(self, role: CommunityRole) -> List[str]:
        """Get permissions for a role."""
        permissions = {
            CommunityRole.OWNER: [
                "manage_community", "manage_members", "manage_roles", "delete_community",
                "moderate_content", "invite_members", "remove_members"
            ],
            CommunityRole.ADMIN: [
                "manage_members", "manage_roles", "moderate_content", "invite_members", "remove_members"
            ],
            CommunityRole.MODERATOR: [
                "moderate_content", "invite_members"
            ],
            CommunityRole.MEMBER: [
                "view_content", "create_content", "invite_members"
            ],
            CommunityRole.GUEST: [
                "view_content"
            ]
        }
        return permissions.get(role, [])
    
    def get_user_communities(self, user_id: str, limit: int = 20) -> List[Community]:
        """
        Get communities that a user is a member of.
        
        Args:
            user_id: User ID
            limit: Maximum number of communities to return
            
        Returns:
            List of Community objects
        """
        try:
            user_communities = []
            
            for community_id, members in self.members.items():
                if user_id in members:
                    community = self.communities.get(community_id)
                    if community:
                        user_communities.append(community)
            
            # Sort by member count (largest first) and limit
            user_communities.sort(key=lambda x: x.member_count, reverse=True)
            return user_communities[:limit]
            
        except Exception as e:
            logger.error(f"Failed to get user communities: {e}")
            return []
    
    def get_community_statistics(self, community_id: str) -> Dict[str, Any]:
        """
        Get statistics for a community.
        
        Args:
            community_id: Community ID
            
        Returns:
            Dictionary with community statistics
        """
        try:
            if community_id not in self.communities:
                return {}
            
            community = self.communities[community_id]
            members = self.members.get(community_id, {})
            
            # Count members by role
            role_counts = defaultdict(int)
            for member in members.values():
                role_counts[member.role.value] += 1
            
            # Calculate activity (recent joins)
            recent_joins = 0
            week_ago = datetime.utcnow() - timedelta(days=7)
            for member in members.values():
                if datetime.fromisoformat(member.joined_at) >= week_ago:
                    recent_joins += 1
            
            return {
                "community_id": community_id,
                "name": community.name,
                "total_members": community.member_count,
                "max_members": community.max_members,
                "role_breakdown": dict(role_counts),
                "recent_joins": recent_joins,
                "is_public": community.is_public,
                "status": community.status.value,
                "created_at": community.created_at,
                "updated_at": community.updated_at
            }
            
        except Exception as e:
            logger.error(f"Failed to get community statistics: {e}")
            return {}

# Global instance (initialized lazily)
community_manager = CommunityManager()

async def get_community_manager() -> CommunityManager:
    """Async getter that ensures the manager is initialized."""
    global community_manager
    if not community_manager._initialized:
        await community_manager.initialize()
    return community_manager
