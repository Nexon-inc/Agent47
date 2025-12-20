from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from core.notifications.notification_service import (
    get_notification_service,
    NotificationService,
    NotificationType,
    NotificationStatus,
    NotificationPriority
)
from core.authentication.auth_manager import get_current_user
from core.user_management.user_manager import User

router = APIRouter(prefix="/api/notifications", tags=["notifications"])

class NotificationResponse(BaseModel):
    id: str
    user_id: int
    agent_id: Optional[str]
    type: str
    priority: str
    title: str
    message: str
    timestamp: datetime
    status: str
    metadata: Optional[Dict[str, Any]] = None
    read_at: Optional[datetime] = None
    archived_at: Optional[datetime] = None

class NotificationSummaryResponse(BaseModel):
    total_notifications: int
    unread_count: int
    starred_count: int
    by_type: Dict[str, int]
    by_priority: Dict[str, int]
    recent_notifications: List[NotificationResponse]

class MarkNotificationRequest(BaseModel):
    notification_id: str

@router.get("/", response_model=List[NotificationResponse])
async def get_notifications(
    limit: int = Query(50, description="Number of notifications to return"),
    offset: int = Query(0, description="Number of notifications to skip"),
    filter_type: Optional[str] = Query(None, description="Filter by notification type"),
    filter_status: Optional[str] = Query(None, description="Filter by notification status"),
    filter_agent: Optional[str] = Query(None, description="Filter by agent"),
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service)
):
    """Get notifications for the current user"""
    try:
        # Validate filter parameters
        filter_type_enum = None
        if filter_type:
            try:
                filter_type_enum = NotificationType(filter_type.lower())
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid notification type: {filter_type}"
                )
        
        filter_status_enum = None
        if filter_status:
            try:
                filter_status_enum = NotificationStatus(filter_status.lower())
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid notification status: {filter_status}"
                )
        
        notifications = await notification_service.get_user_notifications(
            user_id=current_user.id,
            limit=limit,
            offset=offset,
            filter_type=filter_type_enum,
            filter_status=filter_status_enum,
            filter_agent=filter_agent
        )
        
        return [
            NotificationResponse(
                id=notif.id,
                user_id=notif.user_id,
                agent_id=notif.agent_id,
                type=notif.type.value,
                priority=notif.priority.value,
                title=notif.title,
                message=notif.message,
                timestamp=notif.timestamp,
                status=notif.status.value,
                metadata=notif.metadata,
                read_at=notif.read_at,
                archived_at=notif.archived_at
            )
            for notif in notifications
        ]
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get notifications: {str(e)}"
        )

@router.get("/summary", response_model=NotificationSummaryResponse)
async def get_notification_summary(
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service)
):
    """Get notification summary for the current user"""
    try:
        summary = await notification_service.get_notification_summary(current_user.id)
        
        return NotificationSummaryResponse(
            total_notifications=summary.total_notifications,
            unread_count=summary.unread_count,
            starred_count=summary.starred_count,
            by_type=summary.by_type,
            by_priority=summary.by_priority,
            recent_notifications=[
                NotificationResponse(
                    id=notif.id,
                    user_id=notif.user_id,
                    agent_id=notif.agent_id,
                    type=notif.type.value,
                    priority=notif.priority.value,
                    title=notif.title,
                    message=notif.message,
                    timestamp=notif.timestamp,
                    status=notif.status.value,
                    metadata=notif.metadata,
                    read_at=notif.read_at,
                    archived_at=notif.archived_at
                )
                for notif in summary.recent_notifications
            ]
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get notification summary: {str(e)}"
        )

@router.post("/mark-read")
async def mark_notification_read(
    request: MarkNotificationRequest,
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service)
):
    """Mark a notification as read"""
    try:
        success = await notification_service.mark_notification_read(
            notification_id=request.notification_id,
            user_id=current_user.id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found or access denied"
            )
        
        return {
            "success": True,
            "message": "Notification marked as read"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark notification as read: {str(e)}"
        )

@router.post("/mark-starred")
async def mark_notification_starred(
    request: MarkNotificationRequest,
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service)
):
    """Mark a notification as starred"""
    try:
        success = await notification_service.mark_notification_starred(
            notification_id=request.notification_id,
            user_id=current_user.id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found or access denied"
            )
        
        return {
            "success": True,
            "message": "Notification marked as starred"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark notification as starred: {str(e)}"
        )

@router.post("/archive")
async def archive_notification(
    request: MarkNotificationRequest,
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service)
):
    """Archive a notification"""
    try:
        success = await notification_service.archive_notification(
            notification_id=request.notification_id,
            user_id=current_user.id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found or access denied"
            )
        
        return {
            "success": True,
            "message": "Notification archived"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to archive notification: {str(e)}"
        )

@router.post("/mark-all-read")
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service)
):
    """Mark all notifications as read for the current user"""
    try:
        count = await notification_service.mark_all_read(current_user.id)
        
        return {
            "success": True,
            "message": f"Marked {count} notifications as read"
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark all notifications as read: {str(e)}"
        )

@router.post("/generate-mock-data")
async def generate_mock_notifications(
    count: int = Query(20, description="Number of mock notifications to generate"),
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service)
):
    """Generate mock notifications for demonstration"""
    try:
        await notification_service.generate_mock_notifications(
            user_id=current_user.id,
            count=count
        )
        
        return {
            "success": True,
            "message": f"Generated {count} mock notifications",
            "user_id": current_user.id
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate mock notifications: {str(e)}"
        )

@router.post("/create")
async def create_notification(
    notification_type: str,
    title: str,
    message: str,
    agent_id: Optional[str] = None,
    priority: str = "medium",
    metadata: Optional[Dict[str, Any]] = None,
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service)
):
    """Create a new notification"""
    try:
        # Validate notification type
        try:
            type_enum = NotificationType(notification_type.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid notification type: {notification_type}"
            )
        
        # Validate priority
        try:
            priority_enum = NotificationPriority(priority.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid priority: {priority}"
            )
        
        notification = await notification_service.create_notification(
            user_id=current_user.id,
            notification_type=type_enum,
            title=title,
            message=message,
            agent_id=agent_id,
            priority=priority_enum,
            metadata=metadata
        )
        
        return {
            "success": True,
            "notification_id": notification.id,
            "message": "Notification created successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create notification: {str(e)}"
        )
