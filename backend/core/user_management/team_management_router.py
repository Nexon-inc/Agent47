from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, func
from datetime import datetime, timedelta
from typing import List, Optional
import logging

from ..database.connection import get_db
from ..database.models import User, Team, TeamMember, TeamInvite, TeamInviteStatus, UserTier, Task, TaskStatus
from ..authentication.auth_manager import get_current_active_user
from ..user_management.user_manager import UserManager

logger = logging.getLogger(__name__)

team_router = APIRouter(prefix="/team", tags=["team-management"])

# Tier-based limits
TIER_LIMITS = {
    UserTier.FREE: {"team_members": 0, "tasks_per_member": 0},
    UserTier.STARTER: {"team_members": 7, "tasks_per_member": 10},
    UserTier.PRO: {"team_members": 14, "tasks_per_member": 50}
}

def check_team_access(user: User) -> None:
    """Check if user has access to team management features"""
    if user.tier == UserTier.FREE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Team management is not available for Free tier users. Upgrade to Starter or Pro."
        )

def get_team_limits(user: User) -> dict:
    """Get team limits based on user tier"""
    return TIER_LIMITS.get(user.tier, TIER_LIMITS[UserTier.FREE])

@team_router.get("/members")
async def get_team_members(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's team members"""
    check_team_access(current_user)
    
    try:
        # Get user's team
        team = db.query(Team).filter(Team.owner_id == current_user.id).first()
        if not team:
            return {"team_members": [], "total_count": 0, "limit": get_team_limits(current_user)["team_members"]}
        
        # Get team members
        members = db.query(TeamMember).filter(TeamMember.team_id == team.id).all()
        
        return {
            "team_members": [
                {
                    "id": member.id,
                    "user_id": member.user_id,
                    "role": member.role,
                    "joined_at": member.joined_at,
                    "is_active": member.is_active,
                    "tasks_assigned": db.query(Task).filter(
                        and_(
                            Task.user_id == member.user_id,
                            Task.status != TaskStatus.COMPLETED
                        )
                    ).count()
                }
                for member in members
            ],
            "total_count": len(members),
            "limit": get_team_limits(current_user)["team_members"]
        }
    except Exception as e:
        logger.error(f"Get team members error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@team_router.post("/invite")
async def invite_team_member(
    email: str,
    role: str = "member",
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Invite a new team member"""
    check_team_access(current_user)
    
    try:
        limits = get_team_limits(current_user)
        
        # Get or create user's team
        team = db.query(Team).filter(Team.owner_id == current_user.id).first()
        if not team:
            team = Team(
                name=f"{current_user.username}'s Team",
                owner_id=current_user.id,
                created_at=datetime.utcnow()
            )
            db.add(team)
            db.commit()
            db.refresh(team)
        
        # Check current team size
        current_members = db.query(TeamMember).filter(TeamMember.team_id == team.id).count()
        if current_members >= limits["team_members"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Team limit reached. {current_user.tier.value.title()} tier allows {limits['team_members']} members."
            )
        
        # Check if user exists
        invitee = db.query(User).filter(User.email == email).first()
        if not invitee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User with this email not found"
            )
        
        # Check if already a member
        existing_member = db.query(TeamMember).filter(
            and_(
                TeamMember.team_id == team.id,
                TeamMember.user_id == invitee.id
            )
        ).first()
        
        if existing_member:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already a team member"
            )
        
        # Check for pending invite
        pending_invite = db.query(TeamInvite).filter(
            and_(
                TeamInvite.team_id == team.id,
                TeamInvite.invitee_email == email,
                TeamInvite.status == TeamInviteStatus.PENDING
            )
        ).first()
        
        if pending_invite:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invite already sent to this user"
            )
        
        # Create invite
        invite = TeamInvite(
            inviter_id=current_user.id,
            invitee_email=email,
            team_id=team.id,
            status=TeamInviteStatus.PENDING,
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
        db.add(invite)
        db.commit()
        
        # Create inbox message for invitee
        from ..database.models import InboxMessage, MessageType, MessageStatus
        message = InboxMessage(
            user_id=invitee.id,
            message_type=MessageType.TEAM_INVITE,
            title="Team Invitation",
            content=f"You have been invited to join {current_user.username}'s team as a {role}.",
            status=MessageStatus.UNREAD,
            message_metadata={
                "invite_id": invite.id,
                "team_id": team.id,
                "inviter_name": current_user.username,
                "role": role
            }
        )
        db.add(message)
        db.commit()
        
        # Broadcast notification via WebSocket
        try:
            from backend.core.realtime.websocket_router import broadcast_notification
            await broadcast_notification(invitee.id, {
                "id": message.id,
                "type": "team_invite",
                "title": "Team Invitation",
                "message": f"You have been invited to join {current_user.username}'s team as a {role}.",
                "metadata": {
                    "invite_id": invite.id,
                    "team_id": team.id,
                    "inviter_name": current_user.username,
                    "role": role
                }
            })
        except Exception as e:
            logger.warning(f"Failed to broadcast team invite notification: {e}")
        
        return {
            "success": True,
            "message": "Team invitation sent successfully",
            "invite_id": invite.id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Invite team member error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@team_router.post("/invite/{invite_id}/accept")
async def accept_team_invite(
    invite_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Accept a team invitation"""
    try:
        # Get invite
        invite = db.query(TeamInvite).filter(
            and_(
                TeamInvite.id == invite_id,
                TeamInvite.invitee_email == current_user.email,
                TeamInvite.status == TeamInviteStatus.PENDING
            )
        ).first()
        
        if not invite:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invitation not found or expired"
            )
        
        if invite.expires_at and invite.expires_at < datetime.utcnow():
            invite.status = TeamInviteStatus.EXPIRED
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invitation has expired"
            )
        
        # Add user to team
        team_member = TeamMember(
            team_id=invite.team_id,
            user_id=current_user.id,
            role="member",
            joined_at=datetime.utcnow(),
            is_active=True
        )
        db.add(team_member)
        
        # Update invite status
        invite.status = TeamInviteStatus.ACCEPTED
        invite.accepted_at = datetime.utcnow()
        
        db.commit()
        
        return {"success": True, "message": "Team invitation accepted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Accept team invite error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@team_router.post("/invite/{invite_id}/decline")
async def decline_team_invite(
    invite_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Decline a team invitation"""
    try:
        # Get invite
        invite = db.query(TeamInvite).filter(
            and_(
                TeamInvite.id == invite_id,
                TeamInvite.invitee_email == current_user.email,
                TeamInvite.status == TeamInviteStatus.PENDING
            )
        ).first()
        
        if not invite:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invitation not found"
            )
        
        # Update invite status
        invite.status = TeamInviteStatus.DECLINED
        
        db.commit()
        
        return {"success": True, "message": "Team invitation declined"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Decline team invite error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@team_router.post("/assign-task")
async def assign_task_to_member(
    member_id: int,
    task_title: str,
    task_description: str,
    agent_key: str,
    priority: str = "medium",
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Assign a task to a team member"""
    check_team_access(current_user)
    
    try:
        limits = get_team_limits(current_user)
        
        # Get team member
        team_member = db.query(TeamMember).filter(
            and_(
                TeamMember.id == member_id,
                TeamMember.is_active == True
            )
        ).first()
        
        if not team_member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team member not found"
            )
        
        # Verify team ownership
        team = db.query(Team).filter(Team.id == team_member.team_id).first()
        if not team or team.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only assign tasks to your own team members"
            )
        
        # Check member's task limit
        current_tasks = db.query(Task).filter(
            and_(
                Task.user_id == team_member.user_id,
                Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS])
            )
        ).count()
        
        if current_tasks >= limits["tasks_per_member"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Task limit reached for this member. {current_user.tier.value.title()} tier allows {limits['tasks_per_member']} tasks per member."
            )
        
        # Get agent
        agent = db.query(Agent).filter(Agent.key == agent_key).first()
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found"
            )
        
        # Create task
        from ..database.models import TaskPriority
        task = Task(
            title=task_title,
            description=task_description,
            user_id=team_member.user_id,
            agent_id=agent.id,
            status=TaskStatus.PENDING,
            priority=TaskPriority(priority),
            created_at=datetime.utcnow()
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        
        # Create inbox message for team member
        from ..database.models import InboxMessage, MessageType, MessageStatus
        message = InboxMessage(
            user_id=team_member.user_id,
            message_type=MessageType.TASK_COMPLETION,
            title="New Task Assigned",
            content=f"A new task '{task_title}' has been assigned to you by {current_user.username}.",
            status=MessageStatus.UNREAD,
            message_metadata={
                "task_id": task.id,
                "agent_key": agent_key,
                "assigner_name": current_user.username
            }
        )
        db.add(message)
        db.commit()
        
        # Broadcast notification via WebSocket
        try:
            from backend.core.realtime.websocket_router import broadcast_notification
            await broadcast_notification(team_member.user_id, {
                "id": message.id,
                "type": "task_completion",
                "title": "New Task Assigned",
                "message": f"A new task '{task_title}' has been assigned to you by {current_user.username}.",
                "metadata": {
                    "task_id": task.id,
                    "agent_key": agent_key,
                    "assigner_name": current_user.username
                }
            })
        except Exception as e:
            logger.warning(f"Failed to broadcast task assignment notification: {e}")
        
        return {
            "success": True,
            "message": "Task assigned successfully",
            "task_id": task.id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Assign task error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@team_router.get("/invites")
async def get_team_invites(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get pending team invitations for current user"""
    try:
        invites = db.query(TeamInvite).filter(
            and_(
                TeamInvite.invitee_email == current_user.email,
                TeamInvite.status == TeamInviteStatus.PENDING
            )
        ).all()
        
        return {
            "invites": [
                {
                    "id": invite.id,
                    "team_name": invite.team.name if invite.team else "Unknown Team",
                    "inviter_name": invite.inviter.username if invite.inviter else "Unknown",
                    "expires_at": invite.expires_at,
                    "created_at": invite.created_at
                }
                for invite in invites
            ]
        }
        
    except Exception as e:
        logger.error(f"Get team invites error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@team_router.delete("/members/{member_id}")
async def remove_team_member(
    member_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Remove a team member (team owner only)"""
    check_team_access(current_user)
    
    try:
        # Get team member
        team_member = db.query(TeamMember).filter(TeamMember.id == member_id).first()
        if not team_member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team member not found"
            )
        
        # Verify team ownership
        team = db.query(Team).filter(Team.id == team_member.team_id).first()
        if not team or team.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only team owners can remove members"
            )
        
        # Deactivate member
        team_member.is_active = False
        db.commit()
        
        return {"success": True, "message": "Team member removed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Remove team member error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
