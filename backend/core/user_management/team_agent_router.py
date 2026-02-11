"""
Team Agent Request Router
Handles team member requests to agents and agent outputs
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from datetime import datetime
from typing import List, Optional, Dict, Any
import logging
from pydantic import BaseModel

from ..database import get_database
from ..database.models import User, Team, TeamMember, TeamAgentRequest, TeamChatMessage
from ..authentication.auth_manager import get_current_active_user
from ..user_management.team_management_router import check_team_access

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/team/agent-requests", tags=["team-agent-requests"])

async def get_db():
    """Get database session"""
    db = get_database()
    async with db.get_session() as session:
        yield session

class CreateAgentRequest(BaseModel):
    agent_key: str
    request_type: str
    request_data: Dict[str, Any]

class AgentRequestResponse(BaseModel):
    id: int
    team_id: int
    team_member_id: int
    agent_key: str
    request_type: str
    request_data: Dict[str, Any]
    status: str
    output_data: Dict[str, Any]
    created_at: datetime
    processed_at: Optional[datetime]
    completed_at: Optional[datetime]

@router.post("/create")
async def create_agent_request(
    request: CreateAgentRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new agent request from team member"""
    check_team_access(current_user)
    
    try:
        # Get user's team
        result = await db.execute(
            select(Team).where(Team.created_by == current_user.id)
        )
        team = result.scalar_one_or_none()
        
        if not team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found"
            )
        
        # Verify user is team member
        member_result = await db.execute(
            select(TeamMember).where(
                and_(
                    TeamMember.team_id == team.id,
                    TeamMember.user_id == current_user.id,
                    TeamMember.is_active == True
                )
            )
        )
        team_member = member_result.scalar_one_or_none()
        
        if not team_member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this team"
            )
        
        # Create agent request
        agent_request = TeamAgentRequest(
            team_id=team.id,
            team_member_id=current_user.id,
            agent_key=request.agent_key,
            request_type=request.request_type,
            request_data=request.request_data,
            status="pending"
        )
        
        db.add(agent_request)
        await db.commit()
        await db.refresh(agent_request)
        
        # Process request asynchronously
        # This will be handled by a background task
        from ..event_bus import get_kafka
        kafka = await get_kafka()
        await kafka.publish(
            topic="team_agent_requests",
            message={
                "request_id": agent_request.id,
                "team_id": team.id,
                "team_member_id": current_user.id,
                "agent_key": request.agent_key,
                "request_type": request.request_type,
                "request_data": request.request_data
            }
        )
        
        return {
            "success": True,
            "request_id": agent_request.id,
            "status": agent_request.status,
            "message": "Agent request created and queued for processing"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create agent request: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create agent request"
        )

@router.get("/")
async def get_team_agent_requests(
    status_filter: Optional[str] = None,
    agent_key: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all agent requests for user's team"""
    check_team_access(current_user)
    
    try:
        # Get user's team
        result = await db.execute(
            select(Team).where(Team.created_by == current_user.id)
        )
        team = result.scalar_one_or_none()
        
        if not team:
            return {"requests": [], "total": 0}
        
        # Build query
        query = select(TeamAgentRequest).where(TeamAgentRequest.team_id == team.id)
        
        if status_filter:
            query = query.where(TeamAgentRequest.status == status_filter)
        
        if agent_key:
            query = query.where(TeamAgentRequest.agent_key == agent_key)
        
        query = query.order_by(TeamAgentRequest.created_at.desc())
        
        result = await db.execute(query)
        requests = result.scalars().all()
        
        return {
            "requests": [
                {
                    "id": req.id,
                    "team_member_id": req.team_member_id,
                    "agent_key": req.agent_key,
                    "request_type": req.request_type,
                    "request_data": req.request_data,
                    "status": req.status,
                    "output_data": req.output_data,
                    "error_message": req.error_message,
                    "created_at": req.created_at.isoformat() if req.created_at else None,
                    "processed_at": req.processed_at.isoformat() if req.processed_at else None,
                    "completed_at": req.completed_at.isoformat() if req.completed_at else None
                }
                for req in requests
            ],
            "total": len(requests)
        }
        
    except Exception as e:
        logger.error(f"Failed to get agent requests: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get agent requests"
        )

@router.get("/{request_id}")
async def get_agent_request(
    request_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get specific agent request with output"""
    check_team_access(current_user)
    
    try:
        # Get request
        result = await db.execute(
            select(TeamAgentRequest).where(TeamAgentRequest.id == request_id)
        )
        request = result.scalar_one_or_none()
        
        if not request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Request not found"
            )
        
        # Verify user has access (team member or owner)
        team_result = await db.execute(
            select(Team).where(Team.id == request.team_id)
        )
        team = team_result.scalar_one_or_none()
        
        if not team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found"
            )
        
        if team.created_by != current_user.id and request.team_member_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        return {
            "id": request.id,
            "team_id": request.team_id,
            "team_member_id": request.team_member_id,
            "agent_key": request.agent_key,
            "request_type": request.request_type,
            "request_data": request.request_data,
            "status": request.status,
            "output_data": request.output_data,
            "error_message": request.error_message,
            "created_at": request.created_at.isoformat() if request.created_at else None,
            "processed_at": request.processed_at.isoformat() if request.processed_at else None,
            "completed_at": request.completed_at.isoformat() if request.completed_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get agent request: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get agent request"
        )

