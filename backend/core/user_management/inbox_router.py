from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, desc, func
from datetime import datetime, timedelta
from typing import List, Optional
import logging

from ..database.connection import get_db
from ..database.models import User, InboxMessage, MessageStatus, MessageType
from ..authentication.auth_manager import get_current_active_user

logger = logging.getLogger(__name__)

inbox_router = APIRouter(prefix="/inbox", tags=["inbox"])

@inbox_router.get("/messages")
async def get_inbox_messages(
    status_filter: Optional[str] = Query(None, description="Filter by message status"),
    message_type: Optional[str] = Query(None, description="Filter by message type"),
    limit: int = Query(50, ge=1, le=100, description="Number of messages to return"),
    offset: int = Query(0, ge=0, description="Number of messages to skip"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's inbox messages with optional filtering"""
    try:
        query = db.query(InboxMessage).filter(InboxMessage.user_id == current_user.id)
        
        # Apply status filter
        if status_filter:
            try:
                status_enum = MessageStatus(status_filter)
                query = query.filter(InboxMessage.status == status_enum)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status filter: {status_filter}"
                )
        
        # Apply message type filter
        if message_type:
            try:
                type_enum = MessageType(message_type)
                query = query.filter(InboxMessage.message_type == type_enum)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid message type filter: {message_type}"
                )
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination and ordering
        messages = query.order_by(desc(InboxMessage.created_at)).offset(offset).limit(limit).all()
        
        return {
            "messages": [
                {
                    "id": msg.id,
                    "message_type": msg.message_type.value,
                    "title": msg.title,
                    "content": msg.content,
                    "status": msg.status.value,
                    "metadata": msg.message_metadata,
                    "created_at": msg.created_at,
                    "read_at": msg.read_at,
                    "archived_at": msg.archived_at
                }
                for msg in messages
            ],
            "total_count": total_count,
            "limit": limit,
            "offset": offset
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get inbox messages error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@inbox_router.get("/messages/{message_id}")
async def get_inbox_message(
    message_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific inbox message"""
    try:
        message = db.query(InboxMessage).filter(
            and_(
                InboxMessage.id == message_id,
                InboxMessage.user_id == current_user.id
            )
        ).first()
        
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )
        
        return {
            "id": message.id,
            "message_type": message.message_type.value,
            "title": message.title,
            "content": message.content,
            "status": message.status.value,
            "metadata": message.message_metadata,
            "created_at": message.created_at,
            "read_at": message.read_at,
            "archived_at": message.archived_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get inbox message error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@inbox_router.put("/messages/{message_id}/read")
async def mark_message_as_read(
    message_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Mark a message as read"""
    try:
        message = db.query(InboxMessage).filter(
            and_(
                InboxMessage.id == message_id,
                InboxMessage.user_id == current_user.id
            )
        ).first()
        
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )
        
        if message.status == MessageStatus.UNREAD:
            message.status = MessageStatus.READ
            message.read_at = datetime.utcnow()
            db.commit()
        
        return {"success": True, "message": "Message marked as read"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Mark message as read error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@inbox_router.put("/messages/{message_id}/unread")
async def mark_message_as_unread(
    message_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Mark a message as unread"""
    try:
        message = db.query(InboxMessage).filter(
            and_(
                InboxMessage.id == message_id,
                InboxMessage.user_id == current_user.id
            )
        ).first()
        
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )
        
        if message.status == MessageStatus.READ:
            message.status = MessageStatus.UNREAD
            message.read_at = None
            db.commit()
        
        return {"success": True, "message": "Message marked as unread"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Mark message as unread error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@inbox_router.put("/messages/{message_id}/archive")
async def archive_message(
    message_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Archive a message"""
    try:
        message = db.query(InboxMessage).filter(
            and_(
                InboxMessage.id == message_id,
                InboxMessage.user_id == current_user.id
            )
        ).first()
        
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )
        
        if message.status != MessageStatus.ARCHIVED:
            message.status = MessageStatus.ARCHIVED
            message.archived_at = datetime.utcnow()
            db.commit()
        
        return {"success": True, "message": "Message archived"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Archive message error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@inbox_router.put("/messages/{message_id}/unarchive")
async def unarchive_message(
    message_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Unarchive a message"""
    try:
        message = db.query(InboxMessage).filter(
            and_(
                InboxMessage.id == message_id,
                InboxMessage.user_id == current_user.id
            )
        ).first()
        
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )
        
        if message.status == MessageStatus.ARCHIVED:
            message.status = MessageStatus.READ
            message.archived_at = None
            db.commit()
        
        return {"success": True, "message": "Message unarchived"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unarchive message error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@inbox_router.delete("/messages/{message_id}")
async def delete_message(
    message_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a message"""
    try:
        message = db.query(InboxMessage).filter(
            and_(
                InboxMessage.id == message_id,
                InboxMessage.user_id == current_user.id
            )
        ).first()
        
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )
        
        db.delete(message)
        db.commit()
        
        return {"success": True, "message": "Message deleted"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete message error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@inbox_router.get("/stats")
async def get_inbox_stats(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get inbox statistics for the user"""
    try:
        # Get message counts by status
        stats = db.query(
            InboxMessage.status,
            func.count(InboxMessage.id).label('count')
        ).filter(
            InboxMessage.user_id == current_user.id
        ).group_by(InboxMessage.status).all()
        
        # Get message counts by type
        type_stats = db.query(
            InboxMessage.message_type,
            func.count(InboxMessage.id).label('count')
        ).filter(
            InboxMessage.user_id == current_user.id
        ).group_by(InboxMessage.message_type).all()
        
        # Get recent activity (last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_count = db.query(InboxMessage).filter(
            and_(
                InboxMessage.user_id == current_user.id,
                InboxMessage.created_at >= week_ago
            )
        ).count()
        
        return {
            "status_counts": {
                status.value: count for status, count in stats
            },
            "type_counts": {
                msg_type.value: count for msg_type, count in type_stats
            },
            "recent_messages": recent_count,
            "total_messages": sum(count for _, count in stats)
        }
        
    except Exception as e:
        logger.error(f"Get inbox stats error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@inbox_router.put("/messages/bulk/read")
async def mark_messages_as_read_bulk(
    message_ids: List[int],
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Mark multiple messages as read"""
    try:
        messages = db.query(InboxMessage).filter(
            and_(
                InboxMessage.id.in_(message_ids),
                InboxMessage.user_id == current_user.id,
                InboxMessage.status == MessageStatus.UNREAD
            )
        ).all()
        
        for message in messages:
            message.status = MessageStatus.READ
            message.read_at = datetime.utcnow()
        
        db.commit()
        
        return {
            "success": True,
            "message": f"{len(messages)} messages marked as read"
        }
        
    except Exception as e:
        logger.error(f"Bulk mark messages as read error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@inbox_router.put("/messages/bulk/archive")
async def archive_messages_bulk(
    message_ids: List[int],
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Archive multiple messages"""
    try:
        messages = db.query(InboxMessage).filter(
            and_(
                InboxMessage.id.in_(message_ids),
                InboxMessage.user_id == current_user.id,
                InboxMessage.status != MessageStatus.ARCHIVED
            )
        ).all()
        
        for message in messages:
            message.status = MessageStatus.ARCHIVED
            message.archived_at = datetime.utcnow()
        
        db.commit()
        
        return {
            "success": True,
            "message": f"{len(messages)} messages archived"
        }
        
    except Exception as e:
        logger.error(f"Bulk archive messages error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@inbox_router.delete("/messages/bulk")
async def delete_messages_bulk(
    message_ids: List[int],
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete multiple messages"""
    try:
        messages = db.query(InboxMessage).filter(
            and_(
                InboxMessage.id.in_(message_ids),
                InboxMessage.user_id == current_user.id
            )
        ).all()
        
        for message in messages:
            db.delete(message)
        
        db.commit()
        
        return {
            "success": True,
            "message": f"{len(messages)} messages deleted"
        }
        
    except Exception as e:
        logger.error(f"Bulk delete messages error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
