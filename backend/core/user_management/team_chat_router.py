"""
Team Chat Router (Discord-style)
Handles team chat messages including agent outputs
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from datetime import datetime
from typing import List, Optional, Dict, Any
import logging
import asyncio
from pydantic import BaseModel

from ..database import get_database
from ..database.models import User, Team, TeamMember, TeamChatMessage, UserTier
from ..authentication.auth_manager import get_current_active_user
from ..user_management.team_management_router import check_team_access
from ..storage import get_chroma

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/team/chat", tags=["team-chat"])

async def get_db():
    """Get database session"""
    db = await get_database()
    async with db.get_session() as session:
        yield session

class ChatMessageRequest(BaseModel):
    content: str
    message_type: str = "text"
    reply_to_message_id: Optional[int] = None
    agent_key: Optional[str] = None

class ChatMessageResponse(BaseModel):
    id: int
    team_id: int
    user_id: int
    user_name: str
    agent_key: Optional[str]
    message_type: str
    content: str
    audio_url: Optional[str]
    file_url: Optional[str]
    file_name: Optional[str]
    reply_to_message_id: Optional[int]
    created_at: datetime

@router.post("/message")
async def send_chat_message(
    request: ChatMessageRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Send a chat message to team (Discord-style)"""
    try:
        # Get user's team (check if user is owner or member)
        team_result = await db.execute(
            select(Team).where(
                or_(
                    Team.created_by == current_user.id,
                    Team.owner_id == current_user.id
                )
            )
        )
        team = team_result.scalar_one_or_none()
        
        # If not owner, check if user is a member
        if not team:
            member_check = await db.execute(
                select(TeamMember).where(
                    and_(
                        TeamMember.user_id == current_user.id,
                        TeamMember.is_active == True
                    )
                )
            )
            member = member_check.scalar_one_or_none()
            if member:
                team_result = await db.execute(
                    select(Team).where(Team.id == member.team_id)
                )
                team = team_result.scalar_one_or_none()
        
        if not team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found"
            )
        
        # Check team owner's tier (not individual member's tier)
        # Team owner is the user who created the team (created_by field)
        owner_id = team.owner_id if hasattr(team, 'owner_id') and team.owner_id else team.created_by
        owner_result = await db.execute(
            select(User).where(User.id == owner_id)
        )
        team_owner = owner_result.scalar_one_or_none()
        
        if not team_owner:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team owner not found"
            )
        
        # Check if team owner has Starter/Pro tier (team members inherit access)
        if team_owner.tier == UserTier.FREE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Team chat is only available for teams owned by Starter or Pro tier users"
            )
        
        # Verify user is team member or owner
        is_owner = (hasattr(team, 'owner_id') and team.owner_id == current_user.id) or team.created_by == current_user.id
        if not is_owner:
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
        
        # Create chat message
        chat_message = TeamChatMessage(
            team_id=team.id,
            user_id=current_user.id,
            agent_key=request.agent_key,
            message_type=request.message_type,
            content=request.content,
            reply_to_message_id=request.reply_to_message_id
        )
        
        db.add(chat_message)
        await db.commit()
        await db.refresh(chat_message)
        
        # Broadcast to team members via WebSocket
        try:
            from core.realtime.websocket_router import broadcast_team_chat_message
            await broadcast_team_chat_message(team.id, {
                "id": chat_message.id,
                "team_id": chat_message.team_id,
                "user_id": chat_message.user_id,
                "user_name": current_user.username,
                "agent_key": chat_message.agent_key,
                "message_type": chat_message.message_type,
                "content": chat_message.content,
                "created_at": chat_message.created_at.isoformat() if chat_message.created_at else None
            })
        except Exception as e:
            logger.warning(f"Failed to broadcast team chat message: {e}")

        # --- DYNAMIC DISPATCH LOGIC ---
        # If no agent was specified, check if intercommunication is enabled and trigger a dispatcher
        if not chat_message.agent_key and current_user.intercommunication_enabled:
            try:
                from ..event_bus.intercommunication_service import get_intercommunication_service
                intercomm_service = await get_intercommunication_service()
                
                # We trigger the intercommunication analysis in the background
                # This will look at the message, decide the best agent, and create an agent-request
                asyncio.create_task(intercomm_service.dynamic_dispatch(
                    user_id=current_user.id,
                    team_id=team.id,
                    message_content=chat_message.content,
                    db=db
                ))
            except Exception as e:
                logger.error(f"Failed to trigger dynamic dispatch: {e}")
        # -----------------------------
        
        return {
            "success": True,
            "message": {
                "id": chat_message.id,
                "team_id": chat_message.team_id,
                "user_id": chat_message.user_id,
                "user_name": current_user.username,
                "agent_key": chat_message.agent_key,
                "message_type": chat_message.message_type,
                "content": chat_message.content,
                "created_at": chat_message.created_at.isoformat() if chat_message.created_at else None
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send chat message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send chat message"
        )

@router.post("/message/voice")
async def send_voice_message(
    audio_file: UploadFile = File(...),
    reply_to_message_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Send a voice message to team"""
    check_team_access(current_user)
    
    try:
        # Read audio file
        audio_data = await audio_file.read()
        
        # Upload to storage
        storage = await get_chroma()
        # Actually use Supabase Storage
        from ..storage.s3_manager import storage_manager
        file_key = f"team_chat_voice/{current_user.id}/{datetime.utcnow().timestamp()}.{audio_file.filename.split('.')[-1]}"
        audio_url = storage_manager.put_bytes(audio_data, "audio", file_key)
        
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
        
        # Create voice message
        chat_message = TeamChatMessage(
            team_id=team.id,
            user_id=current_user.id,
            message_type="voice",
            content="[Voice Message]",
            audio_url=audio_url,
            file_name=audio_file.filename,
            file_size=len(audio_data),
            reply_to_message_id=reply_to_message_id
        )
        
        db.add(chat_message)
        await db.commit()
        await db.refresh(chat_message)
        
        # Broadcast to team members via WebSocket
        try:
            from core.realtime.websocket_router import broadcast_team_chat_message
            await broadcast_team_chat_message(team.id, {
                "id": chat_message.id,
                "team_id": chat_message.team_id,
                "user_id": chat_message.user_id,
                "user_name": current_user.username,
                "message_type": "voice",
                "audio_url": chat_message.audio_url,
                "created_at": chat_message.created_at.isoformat() if chat_message.created_at else None
            })
        except Exception as e:
            logger.warning(f"Failed to broadcast team chat message: {e}")
        
        return {
            "success": True,
            "message": {
                "id": chat_message.id,
                "team_id": chat_message.team_id,
                "user_id": chat_message.user_id,
                "user_name": current_user.username,
                "message_type": "voice",
                "audio_url": chat_message.audio_url,
                "created_at": chat_message.created_at.isoformat() if chat_message.created_at else None
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send voice message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send voice message"
        )

@router.get("/messages")
async def get_chat_messages(
    limit: int = 50,
    before_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get team chat messages (Discord-style pagination)"""
    check_team_access(current_user)
    
    try:
        # Get user's team
        result = await db.execute(
            select(Team).where(Team.created_by == current_user.id)
        )
        team = result.scalar_one_or_none()
        
        if not team:
            return {"messages": [], "total": 0}
        
        # Build query
        query = select(TeamChatMessage).where(
            and_(
                TeamChatMessage.team_id == team.id,
                TeamChatMessage.deleted_at.is_(None)
            )
        )
        
        if before_id:
            query = query.where(TeamChatMessage.id < before_id)
        
        query = query.order_by(TeamChatMessage.created_at.desc()).limit(limit)
        
        result = await db.execute(query)
        messages = result.scalars().all()
        
        # Get user names
        user_ids = {msg.user_id for msg in messages}
        users_result = await db.execute(
            select(User).where(User.id.in_(user_ids))
        )
        users = {user.id: user for user in users_result.scalars().all()}
        
        return {
            "messages": [
                {
                    "id": msg.id,
                    "team_id": msg.team_id,
                    "user_id": msg.user_id,
                    "user_name": users.get(msg.user_id, {}).username if msg.user_id in users else "Unknown",
                    "agent_key": msg.agent_key,
                    "message_type": msg.message_type,
                    "content": msg.content,
                    "audio_url": msg.audio_url,
                    "file_url": msg.file_url,
                    "file_name": msg.file_name,
                    "reply_to_message_id": msg.reply_to_message_id,
                    "created_at": msg.created_at.isoformat() if msg.created_at else None
                }
                for msg in reversed(messages)  # Reverse to show oldest first
            ],
            "total": len(messages),
            "has_more": len(messages) == limit
        }
        
    except Exception as e:
        logger.error(f"Failed to get chat messages: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get chat messages"
        )

@router.post("/agent-output")
async def post_agent_output(
    agent_key: str,
    content: str,
    request_id: Optional[int] = None,
    audio_url: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Post agent output to team chat (called when agent completes request)"""
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
        
        # Create agent output message
        chat_message = TeamChatMessage(
            team_id=team.id,
            user_id=current_user.id,  # Team owner or system
            agent_key=agent_key,
            message_type="agent_output",
            content=content,
            audio_url=audio_url,
            metadata={
                "request_id": request_id,
                "posted_at": datetime.utcnow().isoformat()
            }
        )
        
        db.add(chat_message)
        await db.commit()
        await db.refresh(chat_message)
        
        # Update agent request if request_id provided
        if request_id:
            from ..database.models import TeamAgentRequest
            request_result = await db.execute(
                select(TeamAgentRequest).where(TeamAgentRequest.id == request_id)
            )
            agent_request = request_result.scalar_one_or_none()
            if agent_request:
                agent_request.status = "completed"
                agent_request.completed_at = datetime.utcnow()
                agent_request.output_data = {
                    "message_id": chat_message.id,
                    "content": content,
                    "audio_url": audio_url
                }
                await db.commit()
        
        return {
            "success": True,
            "message_id": chat_message.id,
            "message": "Agent output posted to team chat"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to post agent output: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to post agent output"
        )
