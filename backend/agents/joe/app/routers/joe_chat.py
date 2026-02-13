from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..services.joe_chat_service import JoeChatService
from core.authentication.auth_manager import get_current_user
from core.database.connection import get_database as get_core_db
from core.database.models import UserSelectedAgent
from sqlalchemy import select
from ..models import JoeMarketTrend
from ..database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/joe-chat", tags=["Joe Chat Interface"])

joe_chat_service = JoeChatService()


from pydantic import BaseModel

class ChatMessageRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

@router.post("/message")
async def process_chat_message(
    request: ChatMessageRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Process a chat message from the user and get Joe's response"""
    try:
        # Enforce per-agent pause/automation guard for Joe
        core_db = get_core_db()
        async with core_db.get_session() as core_session:
            res = await core_session.execute(
                select(UserSelectedAgent).where(
                    UserSelectedAgent.user_id == current_user.id,
                    UserSelectedAgent.agent_key == "joe",
                )
            )
            row = res.scalar_one_or_none()
            if not row:
                raise HTTPException(status_code=403, detail="Agent Joe is not selected")
            if row.status == "paused":
                raise HTTPException(status_code=403, detail="Agent Joe is paused")

        result = await joe_chat_service.process_chat_message(
            user_id=current_user.id,
            message=request.message,
            session_id=request.session_id,
            db=db
        )
        
        if result["success"]:
            return {
                "success": True,
                "data": result,
                "agent": "Joe",
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process message: {str(e)}")


@router.get("/session/{session_id}")
async def get_session_info(
    session_id: str,
    current_user = Depends(get_current_user)
):
    """Get information about a chat session"""
    try:
        result = await joe_chat_service.get_session_info(session_id)
        return {
            "success": True,
            "data": result,
            "agent": "Joe"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get session info: {str(e)}")


@router.delete("/session/{session_id}")
async def clear_session(
    session_id: str,
    current_user = Depends(get_current_user)
):
    """Clear a chat session"""
    try:
        result = await joe_chat_service.clear_session(session_id)
        return {
            "success": True,
            "data": result,
            "agent": "Joe"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear session: {str(e)}")



# TODO Management Endpoints
@router.post("/todos")
async def create_todo(
    title: str,
    description: str = "",
    priority: str = "medium",
    current_user = Depends(get_current_user)
):
    """Create a new TODO item"""
    try:
        result = await joe_chat_service.create_todo(
            user_id=current_user.id,
            title=title,
            description=description,
            priority=priority
        )
        return {
            "success": True,
            "data": result,
            "agent": "Joe"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create TODO: {str(e)}")


@router.get("/todos")
async def get_todos(
    status: str = "all",
    current_user = Depends(get_current_user)
):
    """Get all TODOs for the user"""
    try:
        result = await joe_chat_service.get_todos(
            user_id=current_user.id,
            status=status
        )
        return {
            "success": True,
            "data": result,
            "agent": "Joe"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get TODOs: {str(e)}")


@router.put("/todos/{todo_id}")
async def update_todo(
    todo_id: str,
    updates: Dict[str, Any],
    current_user = Depends(get_current_user)
):
    """Update a TODO item"""
    try:
        result = await joe_chat_service.update_todo(
            user_id=current_user.id,
            todo_id=todo_id,
            updates=updates
        )
        return {
            "success": True,
            "data": result,
            "agent": "Joe"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update TODO: {str(e)}")


@router.delete("/todos/{todo_id}")
async def delete_todo(
    todo_id: str,
    current_user = Depends(get_current_user)
):
    """Delete a TODO item"""
    try:
        result = await joe_chat_service.delete_todo(
            user_id=current_user.id,
            todo_id=todo_id
        )
        return {
            "success": True,
            "data": result,
            "agent": "Joe"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete TODO: {str(e)}")


@router.post("/todos/{todo_id}/complete")
async def complete_todo(
    todo_id: str,
    current_user = Depends(get_current_user)
):
    """Mark a TODO as completed"""
    try:
        result = await joe_chat_service.complete_todo(
            user_id=current_user.id,
            todo_id=todo_id
        )
        return {
            "success": True,
            "data": result,
            "agent": "Joe"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to complete TODO: {str(e)}")


@router.get("/todos/stats")
async def get_todo_stats(
    current_user = Depends(get_current_user)
):
    """Get TODO statistics for the user"""
    try:
        result = await joe_chat_service.get_todo_stats(
            user_id=current_user.id
        )
        return {
            "success": True,
            "data": result,
            "agent": "Joe"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get TODO stats: {str(e)}")

@router.get("/health")
async def health_check():
    """Health check for Joe chat service"""
    return {
        "status": "healthy",
        "agent": "Joe",
        "service": "chat",
        "timestamp": datetime.now().isoformat()
    }
