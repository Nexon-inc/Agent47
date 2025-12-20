from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from core.user_management.team_manager import (
    get_team_manager,
    TeamManager,
    TeamRole,
    TeamStatus
)
from core.authentication.auth_manager import get_current_user
from core.user_management.user_manager import User

router = APIRouter(prefix="/api/teams", tags=["teams"])

class TeamCreateRequest(BaseModel):
    name: str = Field(..., description="Team name")
    description: str = Field(..., description="Team description")
    is_public: bool = Field(default=False, description="Is team public")
    max_members: Optional[int] = Field(None, description="Maximum number of members")
    tags: Optional[List[str]] = Field(None, description="Team tags")
    website: Optional[str] = Field(None, description="Team website")
    location: Optional[str] = Field(None, description="Team location")
    timezone: str = Field(default="UTC", description="Team timezone")

class TeamUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, description="Team name")
    description: Optional[str] = Field(None, description="Team description")
    is_public: Optional[bool] = Field(None, description="Is team public")
    max_members: Optional[int] = Field(None, description="Maximum number of members")
    tags: Optional[List[str]] = Field(None, description="Team tags")
    website: Optional[str] = Field(None, description="Team website")
    location: Optional[str] = Field(None, description="Team location")
    timezone: Optional[str] = Field(None, description="Team timezone")

class TeamMemberAddRequest(BaseModel):
    user_id: str = Field(..., description="User ID to add")
    role: str = Field(default="member", description="Member role")

class TeamMemberUpdateRequest(BaseModel):
    role: Optional[str] = Field(None, description="New member role")
    skills: Optional[List[str]] = Field(None, description="Member skills")
    availability: Optional[Dict[str, Any]] = Field(None, description="Member availability")

class TeamResponse(BaseModel):
    id: str
    name: str
    description: str
    owner_id: str
    status: str
    created_at: str
    updated_at: str
    member_count: int
    max_members: Optional[int]
    is_public: bool
    tags: List[str]
    settings: Dict[str, Any]
    avatar_url: Optional[str]
    banner_url: Optional[str]
    website: Optional[str]
    location: Optional[str]
    timezone: str

class TeamMemberResponse(BaseModel):
    team_id: str
    user_id: str
    role: str
    joined_at: str
    updated_at: str
    is_active: bool
    nickname: Optional[str]
    bio: Optional[str]
    permissions: List[str]
    skills: List[str]
    availability: Dict[str, Any]

class TeamStatisticsResponse(BaseModel):
    team_id: str
    name: str
    total_members: int
    max_members: Optional[int]
    role_breakdown: Dict[str, int]
    recent_joins: int
    is_public: bool
    status: str
    top_skills: Dict[str, int]
    created_at: str
    updated_at: str

@router.post("/", response_model=TeamResponse)
async def create_team(
    request: TeamCreateRequest,
    current_user: User = Depends(get_current_user),
    team_manager: TeamManager = Depends(get_team_manager)
):
    """Create a new team"""
    try:
        team = team_manager.create_team(
            name=request.name,
            description=request.description,
            owner_id=str(current_user.id),
            is_public=request.is_public,
            max_members=request.max_members,
            tags=request.tags or [],
            website=request.website,
            location=request.location,
            timezone=request.timezone
        )
        
        return TeamResponse(
            id=team.id,
            name=team.name,
            description=team.description,
            owner_id=team.owner_id,
            status=team.status.value,
            created_at=team.created_at,
            updated_at=team.updated_at,
            member_count=team.member_count,
            max_members=team.max_members,
            is_public=team.is_public,
            tags=team.tags or [],
            settings=team.settings or {},
            avatar_url=team.avatar_url,
            banner_url=team.banner_url,
            website=team.website,
            location=team.location,
            timezone=team.timezone
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create team: {str(e)}"
        )

@router.get("/", response_model=List[TeamResponse])
async def get_user_teams(
    current_user: User = Depends(get_current_user),
    team_manager: TeamManager = Depends(get_team_manager)
):
    """Get teams that the user is a member of"""
    try:
        teams = team_manager.get_user_teams(str(current_user.id))
        
        return [
            TeamResponse(
                id=team.id,
                name=team.name,
                description=team.description,
                owner_id=team.owner_id,
                status=team.status.value,
                created_at=team.created_at,
                updated_at=team.updated_at,
                member_count=team.member_count,
                max_members=team.max_members,
                is_public=team.is_public,
                tags=team.tags or [],
                settings=team.settings or {},
                avatar_url=team.avatar_url,
                banner_url=team.banner_url,
                website=team.website,
                location=team.location,
                timezone=team.timezone
            )
            for team in teams
        ]
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user teams: {str(e)}"
        )

@router.get("/{team_id}", response_model=TeamResponse)
async def get_team(
    team_id: str,
    current_user: User = Depends(get_current_user),
    team_manager: TeamManager = Depends(get_team_manager)
):
    """Get team by ID"""
    try:
        team = team_manager.get_team(team_id)
        
        if not team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found"
            )
        
        # Check if user is a member
        member = team_manager.get_member(team_id, str(current_user.id))
        if not member and not team.is_public:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        return TeamResponse(
            id=team.id,
            name=team.name,
            description=team.description,
            owner_id=team.owner_id,
            status=team.status.value,
            created_at=team.created_at,
            updated_at=team.updated_at,
            member_count=team.member_count,
            max_members=team.max_members,
            is_public=team.is_public,
            tags=team.tags or [],
            settings=team.settings or {},
            avatar_url=team.avatar_url,
            banner_url=team.banner_url,
            website=team.website,
            location=team.location,
            timezone=team.timezone
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get team: {str(e)}"
        )

@router.put("/{team_id}", response_model=TeamResponse)
async def update_team(
    team_id: str,
    request: TeamUpdateRequest,
    current_user: User = Depends(get_current_user),
    team_manager: TeamManager = Depends(get_team_manager)
):
    """Update team information"""
    try:
        updates = {}
        if request.name is not None:
            updates["name"] = request.name
        if request.description is not None:
            updates["description"] = request.description
        if request.is_public is not None:
            updates["is_public"] = request.is_public
        if request.max_members is not None:
            updates["max_members"] = request.max_members
        if request.tags is not None:
            updates["tags"] = request.tags
        if request.website is not None:
            updates["website"] = request.website
        if request.location is not None:
            updates["location"] = request.location
        if request.timezone is not None:
            updates["timezone"] = request.timezone
        
        success = team_manager.update_team(
            team_id=team_id,
            user_id=str(current_user.id),
            **updates
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found or insufficient permissions"
            )
        
        # Get updated team
        team = team_manager.get_team(team_id)
        
        return TeamResponse(
            id=team.id,
            name=team.name,
            description=team.description,
            owner_id=team.owner_id,
            status=team.status.value,
            created_at=team.created_at,
            updated_at=team.updated_at,
            member_count=team.member_count,
            max_members=team.max_members,
            is_public=team.is_public,
            tags=team.tags or [],
            settings=team.settings or {},
            avatar_url=team.avatar_url,
            banner_url=team.banner_url,
            website=team.website,
            location=team.location,
            timezone=team.timezone
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update team: {str(e)}"
        )

@router.delete("/{team_id}")
async def delete_team(
    team_id: str,
    current_user: User = Depends(get_current_user),
    team_manager: TeamManager = Depends(get_team_manager)
):
    """Delete a team"""
    try:
        success = team_manager.delete_team(
            team_id=team_id,
            user_id=str(current_user.id)
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found or insufficient permissions"
            )
        
        return {"success": True, "message": "Team deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete team: {str(e)}"
        )

@router.get("/{team_id}/members", response_model=List[TeamMemberResponse])
async def get_team_members(
    team_id: str,
    role: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    team_manager: TeamManager = Depends(get_team_manager)
):
    """Get team members"""
    try:
        # Check if user is a member
        member = team_manager.get_member(team_id, str(current_user.id))
        team = team_manager.get_team(team_id)
        
        if not member and not (team and team.is_public):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        members = team_manager.get_team_members(
            team_id=team_id,
            role=TeamRole(role.lower()) if role else None
        )
        
        return [
            TeamMemberResponse(
                team_id=member.team_id,
                user_id=member.user_id,
                role=member.role.value,
                joined_at=member.joined_at,
                updated_at=member.updated_at,
                is_active=member.is_active,
                nickname=member.nickname,
                bio=member.bio,
                permissions=member.permissions or [],
                skills=member.skills or [],
                availability=member.availability or {}
            )
            for member in members
        ]
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get team members: {str(e)}"
        )

@router.post("/{team_id}/members")
async def add_team_member(
    team_id: str,
    request: TeamMemberAddRequest,
    current_user: User = Depends(get_current_user),
    team_manager: TeamManager = Depends(get_team_manager)
):
    """Add a member to the team"""
    try:
        success = team_manager.add_member(
            team_id=team_id,
            user_id=request.user_id,
            role=TeamRole(request.role.lower()),
            added_by=str(current_user.id)
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to add member"
            )
        
        return {"success": True, "message": "Member added successfully"}
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add member: {str(e)}"
        )

@router.delete("/{team_id}/members/{user_id}")
async def remove_team_member(
    team_id: str,
    user_id: str,
    current_user: User = Depends(get_current_user),
    team_manager: TeamManager = Depends(get_team_manager)
):
    """Remove a member from the team"""
    try:
        success = team_manager.remove_member(
            team_id=team_id,
            user_id=user_id,
            removed_by=str(current_user.id)
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to remove member"
            )
        
        return {"success": True, "message": "Member removed successfully"}
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove member: {str(e)}"
        )

@router.put("/{team_id}/members/{user_id}/role")
async def update_member_role(
    team_id: str,
    user_id: str,
    new_role: str,
    current_user: User = Depends(get_current_user),
    team_manager: TeamManager = Depends(get_team_manager)
):
    """Update a member's role"""
    try:
        success = team_manager.update_member_role(
            team_id=team_id,
            user_id=user_id,
            new_role=TeamRole(new_role.lower()),
            updated_by=str(current_user.id)
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update member role"
            )
        
        return {"success": True, "message": "Member role updated successfully"}
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update member role: {str(e)}"
        )

@router.put("/{team_id}/members/{user_id}/skills")
async def update_member_skills(
    team_id: str,
    user_id: str,
    skills: List[str],
    current_user: User = Depends(get_current_user),
    team_manager: TeamManager = Depends(get_team_manager)
):
    """Update a member's skills"""
    try:
        success = team_manager.update_member_skills(
            team_id=team_id,
            user_id=user_id,
            skills=skills
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update member skills"
            )
        
        return {"success": True, "message": "Member skills updated successfully"}
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update member skills: {str(e)}"
        )

@router.get("/{team_id}/statistics", response_model=TeamStatisticsResponse)
async def get_team_statistics(
    team_id: str,
    current_user: User = Depends(get_current_user),
    team_manager: TeamManager = Depends(get_team_manager)
):
    """Get team statistics"""
    try:
        # Check if user is a member
        member = team_manager.get_member(team_id, str(current_user.id))
        team = team_manager.get_team(team_id)
        
        if not member and not (team and team.is_public):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        stats = team_manager.get_team_statistics(team_id)
        
        if not stats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found"
            )
        
        return TeamStatisticsResponse(
            team_id=stats["team_id"],
            name=stats["name"],
            total_members=stats["total_members"],
            max_members=stats["max_members"],
            role_breakdown=stats["role_breakdown"],
            recent_joins=stats["recent_joins"],
            is_public=stats["is_public"],
            status=stats["status"],
            top_skills=stats["top_skills"],
            created_at=stats["created_at"],
            updated_at=stats["updated_at"]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get team statistics: {str(e)}"
        )

@router.get("/search")
async def search_teams(
    query: str,
    limit: int = 20,
    include_private: bool = False,
    tags: Optional[List[str]] = None,
    current_user: User = Depends(get_current_user),
    team_manager: TeamManager = Depends(get_team_manager)
):
    """Search for teams"""
    try:
        teams = team_manager.search_teams(
            query=query,
            owner_id=str(current_user.id),
            limit=limit,
            include_private=include_private,
            tags=tags
        )
        
        return [
            TeamResponse(
                id=team.id,
                name=team.name,
                description=team.description,
                owner_id=team.owner_id,
                status=team.status.value,
                created_at=team.created_at,
                updated_at=team.updated_at,
                member_count=team.member_count,
                max_members=team.max_members,
                is_public=team.is_public,
                tags=team.tags or [],
                settings=team.settings or {},
                avatar_url=team.avatar_url,
                banner_url=team.banner_url,
                website=team.website,
                location=team.location,
                timezone=team.timezone
            )
            for team in teams
        ]
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search teams: {str(e)}"
        )
