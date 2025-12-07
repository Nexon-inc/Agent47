import json
import hashlib
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)

class TeamRole(Enum):
    """Roles within a team."""
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    GUEST = "guest"
    VIEWER = "viewer"

class TeamStatus(Enum):
    """Team status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"
    SUSPENDED = "suspended"

@dataclass
class Team:
    """Team data structure."""
    id: str
    name: str
    description: str
    owner_id: str
    status: TeamStatus
    created_at: str
    updated_at: str
    member_count: int = 0
    max_members: Optional[int] = None
    is_public: bool = False
    tags: Optional[List[str]] = None
    settings: Optional[Dict[str, Any]] = None
    avatar_url: Optional[str] = None
    banner_url: Optional[str] = None
    website: Optional[str] = None
    location: Optional[str] = None
    timezone: str = "UTC"

@dataclass
class TeamMember:
    """Team member data structure."""
    team_id: str
    user_id: str
    role: TeamRole
    joined_at: str
    updated_at: str
    is_active: bool = True
    nickname: Optional[str] = None
    bio: Optional[str] = None
    permissions: Optional[List[str]] = None
    skills: Optional[List[str]] = None
    availability: Optional[Dict[str, Any]] = None

class TeamManager:
    """Manages teams and their members."""
    
    def __init__(self):
        self.teams: Dict[str, Team] = {}
        self.members: Dict[str, Dict[str, TeamMember]] = defaultdict(dict)
        self._initialized = False

    async def initialize(self):
        """Async initializer; call on app startup to load data from DB."""
        if self._initialized:
            return
        await self._load_data()
        self._initialized = True
    
    async def _load_data(self):
        """Async load teams and members from database."""
        try:
            from backend.core.database.connection import get_supabase
            from backend.core.database.models import Team as ORMTeam, TeamMember as ORMTeamMember
            from sqlalchemy import select

            db = await get_supabase()
            async with db.get_session() as session:
                result = await session.execute(select(ORMTeam))
                teams_data = result.scalars().all()
                # Convert ORM models to dataclass Team instances
                self.teams = {}
                for t in teams_data:
                    key = str(getattr(t, 'id', ''))
                    self.teams[key] = Team(
                        id=str(getattr(t, 'id', '')),
                        name=str(getattr(t, 'name', '')),
                        description=str(getattr(t, 'description', '') or ''),
                        owner_id=str(getattr(t, 'created_by', '') or ''),
                        status=getattr(t, 'status', TeamStatus.ACTIVE),
                        created_at=getattr(t, 'created_at').isoformat() if getattr(t, 'created_at', None) else '',
                        updated_at=getattr(t, 'updated_at').isoformat() if getattr(t, 'updated_at', None) else '',
                        member_count=getattr(t, 'member_count', 0) or 0,
                        max_members=getattr(t, 'max_members', None),
                        is_public=getattr(t, 'is_public', False) or False,
                        tags=getattr(t, 'tags', []) or [],
                        settings=getattr(t, 'settings', {}) or {},
                        avatar_url=getattr(t, 'avatar_url', None),
                        banner_url=getattr(t, 'banner_url', None),
                        website=getattr(t, 'website', None),
                        location=getattr(t, 'location', None),
                        timezone=getattr(t, 'timezone', 'UTC')
                    )

                # Load team members
                result = await session.execute(select(ORMTeamMember))
                members_data = result.scalars().all()
                self.members = defaultdict(dict)
                for m in members_data:
                    team_key = str(getattr(m, 'team_id', ''))
                    user_key = str(getattr(m, 'user_id', ''))
                    member = TeamMember(
                        team_id=team_key,
                        user_id=user_key,
                        role=getattr(m, 'role', TeamRole.MEMBER),
                        joined_at=getattr(m, 'joined_at').isoformat() if getattr(m, 'joined_at', None) else '',
                        updated_at=getattr(m, 'updated_at').isoformat() if getattr(m, 'updated_at', None) else '',
                        is_active=getattr(m, 'is_active', True),
                        nickname=getattr(m, 'nickname', None),
                        bio=getattr(m, 'bio', None),
                        permissions=getattr(m, 'permissions', []) or [],
                        skills=getattr(m, 'skills', []) or [],
                        availability=getattr(m, 'availability', {}) or {}
                    )
                    self.members[team_key][user_key] = member

            logger.info(f"Team data loaded successfully: {len(self.teams)} teams, {sum(len(members) for members in self.members.values())} members")
        except Exception as e:
            logger.error(f"Failed to load team data: {e}")
            # fallback
            self.teams = {}
            self.members = defaultdict(dict)
    
    def _save_data(self):
        """Schedule a non-blocking save placeholder (implement real persistence later)."""
        try:
            import asyncio
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            if loop:
                async def _noop():
                    return
                loop.create_task(_noop())
            else:
                logger.debug("_save_data called but no running loop; skipping persistence")
        except Exception as e:
            logger.error(f"Failed to schedule save: {e}")
    
    def _generate_team_id(self, name: str, owner_id: str) -> str:
        """Generate a unique team ID."""
        data = f"{name}:{owner_id}:{datetime.utcnow().isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def create_team(
        self,
        name: str,
        description: str,
        owner_id: str,
        is_public: bool = False,
        max_members: Optional[int] = None,
        **kwargs
    ) -> Team:
        """
        Create a new team.
        
        Args:
            name: Team name
            description: Team description
            owner_id: ID of the team owner
            is_public: Whether the team is public
            max_members: Maximum number of members
            **kwargs: Additional team fields
            
        Returns:
            Created Team object
        """
        try:
            # Validate input
            if not name or len(name.strip()) < 2:
                raise ValueError("Team name must be at least 2 characters long")
            
            if not description or len(description.strip()) < 5:
                raise ValueError("Team description must be at least 5 characters long")
            
            # Check if name is already taken by the same owner
            if any(t.name.lower() == name.lower() and t.owner_id == owner_id for t in self.teams.values()):
                raise ValueError(f"Team name '{name}' is already taken by you")
            
            # Create team
            team_id = self._generate_team_id(name, owner_id)
            current_time = datetime.utcnow().isoformat()
            
            team = Team(
                id=team_id,
                name=name.strip(),
                description=description.strip(),
                owner_id=owner_id,
                status=TeamStatus.ACTIVE,
                created_at=current_time,
                updated_at=current_time,
                is_public=is_public,
                max_members=max_members,
                tags=kwargs.get('tags', []),
                settings=kwargs.get('settings', {}),
                avatar_url=kwargs.get('avatar_url'),
                banner_url=kwargs.get('banner_url'),
                website=kwargs.get('website'),
                location=kwargs.get('location'),
                timezone=kwargs.get('timezone', 'UTC')
            )
            
            self.teams[team_id] = team
            
            # Add owner as first member
            self.add_member(team_id, owner_id, TeamRole.OWNER)
            
            self._save_data()
            
            logger.info(f"Created team '{name}' with ID {team_id}")
            return team
            
        except Exception as e:
            logger.error(f"Failed to create team: {e}")
            raise
    
    def get_team(self, team_id: str) -> Optional[Team]:
        """
        Get team by ID.
        
        Args:
            team_id: Team ID
            
        Returns:
            Team object or None if not found
        """
        try:
            return self.teams.get(team_id)
        except Exception as e:
            logger.error(f"Failed to get team: {e}")
            return None
    
    def search_teams(
        self,
        query: str,
        owner_id: Optional[str] = None,
        limit: int = 20,
        include_private: bool = False,
        tags: Optional[List[str]] = None
    ) -> List[Team]:
        """
        Search teams by various criteria.
        
        Args:
            query: Search query
            owner_id: Filter by team owner
            limit: Maximum number of results
            include_private: Whether to include private teams
            tags: Filter by tags
            
        Returns:
            List of matching Team objects
        """
        try:
            results = []
            query_lower = query.lower()
            
            for team in self.teams.values():
                # Skip private teams unless requested or user is owner
                if not include_private and not team.is_public and team.owner_id != owner_id:
                    continue
                
                # Skip inactive teams
                if team.status != TeamStatus.ACTIVE:
                    continue
                
                # Filter by owner if specified
                if owner_id and team.owner_id != owner_id:
                    continue
                
                # Check if query matches name or description
                if (query_lower in team.name.lower() or 
                    query_lower in team.description.lower()):
                    results.append(team)
                    continue
                
                # Check tags if specified
                if tags and team.tags:
                    if any(tag.lower() in [t.lower() for t in team.tags] for tag in tags):
                        results.append(team)
                        continue
                
                if len(results) >= limit:
                    break
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to search teams: {e}")
            return []
    
    def update_team(self, team_id: str, user_id: str, **updates) -> bool:
        """
        Update team information.
        
        Args:
            team_id: Team ID
            user_id: ID of the user making the update
            **updates: Fields to update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if team_id not in self.teams:
                return False
            
            team = self.teams[team_id]
            
            # Check permissions
            member = self.get_member(team_id, user_id)
            if not member or member.role not in [TeamRole.OWNER, TeamRole.ADMIN]:
                logger.warning(f"User {user_id} attempted to update team {team_id} without permission")
                return False
            
            # Update fields
            for field, value in updates.items():
                if hasattr(team, field):
                    setattr(team, field, value)
            
            # Update timestamp
            team.updated_at = datetime.utcnow().isoformat()
            
            self._save_data()
            
            logger.info(f"Updated team {team_id} by user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update team: {e}")
            return False
    
    def delete_team(self, team_id: str, user_id: str) -> bool:
        """
        Delete a team.
        
        Args:
            team_id: Team ID
            user_id: ID of the user deleting the team
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if team_id not in self.teams:
                return False
            
            team = self.teams[team_id]
            
            # Only owner can delete team
            if team.owner_id != user_id:
                logger.warning(f"User {user_id} attempted to delete team {team_id} without permission")
                return False
            
            # Remove all members
            if team_id in self.members:
                del self.members[team_id]
            
            # Remove team
            del self.teams[team_id]
            
            self._save_data()
            
            logger.info(f"Deleted team {team_id} by user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete team: {e}")
            return False
    
    def add_member(
        self,
        team_id: str,
        user_id: str,
        role: TeamRole = TeamRole.MEMBER,
        added_by: Optional[str] = None
    ) -> bool:
        """
        Add a member to a team.
        
        Args:
            team_id: Team ID
            user_id: ID of the user to add
            role: Role for the new member
            added_by: ID of the user adding the member
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if team_id not in self.teams:
                return False
            
            team = self.teams[team_id]
            
            # Check if user is already a member
            if user_id in self.members[team_id]:
                return False
            
            # Check member limit
            if team.max_members and team.member_count >= team.max_members:
                raise ValueError("Team has reached maximum member limit")
            
            # Check permissions for adding members
            if added_by and added_by != team.owner_id:
                adder_member = self.get_member(team_id, added_by)
                if not adder_member or adder_member.role not in [TeamRole.OWNER, TeamRole.ADMIN]:
                    logger.warning(f"User {added_by} attempted to add member to team {team_id} without permission")
                    return False
            
            # Create member
            current_time = datetime.utcnow().isoformat()
            member = TeamMember(
                team_id=team_id,
                user_id=user_id,
                role=role,
                joined_at=current_time,
                updated_at=current_time,
                permissions=self._get_role_permissions(role),
                skills=[],
                availability={}
            )
            
            self.members[team_id][user_id] = member
            
            # Update member count
            team.member_count += 1
            team.updated_at = current_time
            
            self._save_data()
            
            logger.info(f"Added member {user_id} to team {team_id} with role {role.value}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add member: {e}")
            return False
    
    def remove_member(self, team_id: str, user_id: str, removed_by: str) -> bool:
        """
        Remove a member from a team.
        
        Args:
            team_id: Team ID
            user_id: ID of the user to remove
            removed_by: ID of the user removing the member
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if team_id not in self.members or user_id not in self.members[team_id]:
                return False
            
            team = self.teams[team_id]
            member = self.members[team_id][user_id]
            
            # Check permissions
            if removed_by != team.owner_id:
                remover_member = self.get_member(team_id, removed_by)
                if not remover_member or remover_member.role not in [TeamRole.OWNER, TeamRole.ADMIN]:
                    logger.warning(f"User {removed_by} attempted to remove member from team {team_id} without permission")
                    return False
                
                # Admins can't remove other admins or the owner
                if member.role in [TeamRole.OWNER, TeamRole.ADMIN]:
                    logger.warning(f"User {removed_by} attempted to remove admin/owner from team {team_id}")
                    return False
            
            # Remove member
            del self.members[team_id][user_id]
            
            # Update member count
            team.member_count -= 1
            team.updated_at = datetime.utcnow().isoformat()
            
            self._save_data()
            
            logger.info(f"Removed member {user_id} from team {team_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove member: {e}")
            return False
    
    def get_member(self, team_id: str, user_id: str) -> Optional[TeamMember]:
        """
        Get team member information.
        
        Args:
            team_id: Team ID
            user_id: User ID
            
        Returns:
            TeamMember object or None if not found
        """
        try:
            return self.members.get(team_id, {}).get(user_id)
        except Exception as e:
            logger.error(f"Failed to get member: {e}")
            return None
    
    def get_team_members(
        self,
        team_id: str,
        limit: int = 50,
        role: Optional[TeamRole] = None
    ) -> List[TeamMember]:
        """
        Get members of a team.
        
        Args:
            team_id: Team ID
            limit: Maximum number of members to return
            role: Filter by role
            
        Returns:
            List of TeamMember objects
        """
        try:
            if team_id not in self.members:
                return []
            
            members = list(self.members[team_id].values())
            
            # Filter by role
            if role:
                members = [m for m in members if m.role == role]
            
            # Sort by join date (oldest first) and limit
            members.sort(key=lambda x: x.joined_at)
            return members[:limit]
            
        except Exception as e:
            logger.error(f"Failed to get team members: {e}")
            return []
    
    def update_member_role(
        self,
        team_id: str,
        user_id: str,
        new_role: TeamRole,
        updated_by: str
    ) -> bool:
        """
        Update a member's role.
        
        Args:
            team_id: Team ID
            user_id: ID of the member to update
            new_role: New role
            updated_by: ID of the user making the update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if team_id not in self.members or user_id not in self.members[team_id]:
                return False
            
            team = self.teams[team_id]
            member = self.members[team_id][user_id]
            
            # Check permissions
            if updated_by != team.owner_id:
                updater_member = self.get_member(team_id, updated_by)
                if not updater_member or updater_member.role not in [TeamRole.OWNER, TeamRole.ADMIN]:
                    logger.warning(f"User {updated_by} attempted to update member role in team {team_id} without permission")
                    return False
                
                # Admins can't change other admins or the owner
                if member.role in [TeamRole.OWNER, TeamRole.ADMIN]:
                    logger.warning(f"User {updated_by} attempted to change admin/owner role in team {team_id}")
                    return False
            
            # Update role
            member.role = new_role
            member.permissions = self._get_role_permissions(new_role)
            member.updated_at = datetime.utcnow().isoformat()
            
            self._save_data()
            
            logger.info(f"Updated member {user_id} role to {new_role.value} in team {team_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update member role: {e}")
            return False
    
    def update_member_skills(
        self,
        team_id: str,
        user_id: str,
        skills: List[str]
    ) -> bool:
        """
        Update a member's skills.
        
        Args:
            team_id: Team ID
            user_id: ID of the member
            skills: List of skills
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if team_id not in self.members or user_id not in self.members[team_id]:
                return False
            
            member = self.members[team_id][user_id]
            member.skills = skills
            member.updated_at = datetime.utcnow().isoformat()
            
            self._save_data()
            
            logger.info(f"Updated skills for member {user_id} in team {team_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update member skills: {e}")
            return False
    
    def update_member_availability(
        self,
        team_id: str,
        user_id: str,
        availability: Dict[str, Any]
    ) -> bool:
        """
        Update a member's availability.
        
        Args:
            team_id: Team ID
            user_id: ID of the member
            availability: Availability information
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if team_id not in self.members or user_id not in self.members[team_id]:
                return False
            
            member = self.members[team_id][user_id]
            member.availability = availability
            member.updated_at = datetime.utcnow().isoformat()
            
            self._save_data()
            
            logger.info(f"Updated availability for member {user_id} in team {team_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update member availability: {e}")
            return False
    
    def _get_role_permissions(self, role: TeamRole) -> List[str]:
        """Get permissions for a role."""
        permissions = {
            TeamRole.OWNER: [
                "manage_team", "manage_members", "manage_roles", "delete_team",
                "invite_members", "remove_members", "view_analytics"
            ],
            TeamRole.ADMIN: [
                "manage_members", "manage_roles", "invite_members", "remove_members",
                "view_analytics"
            ],
            TeamRole.MEMBER: [
                "view_content", "create_content", "invite_members", "view_analytics"
            ],
            TeamRole.GUEST: [
                "view_content", "create_content"
            ],
            TeamRole.VIEWER: [
                "view_content"
            ]
        }
        return permissions.get(role, [])
    
    def get_user_teams(self, user_id: str, limit: int = 20) -> List[Team]:
        """
        Get teams that a user is a member of.
        
        Args:
            user_id: User ID
            limit: Maximum number of teams to return
            
        Returns:
            List of Team objects
        """
        try:
            user_teams = []
            
            for team_id, members in self.members.items():
                if user_id in members:
                    team = self.teams.get(team_id)
                    if team:
                        user_teams.append(team)
            
            # Sort by member count (largest first) and limit
            user_teams.sort(key=lambda x: x.member_count, reverse=True)
            return user_teams[:limit]
            
        except Exception as e:
            logger.error(f"Failed to get user teams: {e}")
            return []
    
    def get_team_statistics(self, team_id: str) -> Dict[str, Any]:
        """
        Get statistics for a team.
        
        Args:
            team_id: Team ID
            
        Returns:
            Dictionary with team statistics
        """
        try:
            if team_id not in self.teams:
                return {}
            
            team = self.teams[team_id]
            members = self.members.get(team_id, {})
            
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
            
            # Calculate skills distribution
            all_skills = []
            for member in members.values():
                if member.skills:
                    all_skills.extend(member.skills)
            
            skill_counts = defaultdict(int)
            for skill in all_skills:
                skill_counts[skill] += 1
            
            return {
                "team_id": team_id,
                "name": team.name,
                "total_members": team.member_count,
                "max_members": team.max_members,
                "role_breakdown": dict(role_counts),
                "recent_joins": recent_joins,
                "is_public": team.is_public,
                "status": team.status.value,
                "top_skills": dict(sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
                "created_at": team.created_at,
                "updated_at": team.updated_at
            }
            
        except Exception as e:
            logger.error(f"Failed to get team statistics: {e}")
            return {}

# Global instance
team_manager = TeamManager()

async def get_team_manager() -> TeamManager:
    """Async getter that ensures the manager is initialized."""
    global team_manager
    if not team_manager._initialized:
        await team_manager.initialize()
    return team_manager
