from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from fastapi import HTTPException, BackgroundTasks
import json
import asyncio
from enum import Enum

from ..models import (
    MobileAppUser, MobileAppSession, MobileAppOverride, MobileAppNotification,
    MobileAppDevice, MobileAppPermission, SupportTicket, CustomerInteraction
)
from ..schemas.mobile_app_monitoring import (
    CreateMobileAppUserRequest, UpdateMobileAppUserRequest,
    CreateMobileAppSessionRequest, UpdateMobileAppSessionRequest,
    CreateMobileAppOverrideRequest, UpdateMobileAppOverrideRequest,
    CreateMobileAppNotificationRequest, UpdateMobileAppNotificationRequest,
    MobileAppUserResponse, MobileAppSessionResponse, MobileAppOverrideResponse,
    MobileAppNotificationResponse, MobileAppDeviceResponse, MobileAppAnalyticsResponse
)
from ..database import get_clara_database
from ..core.config import settings
from ..core.integrations import IntegrationManager
from ..core.analytics import AnalyticsManager
from ..core.nlp import NLPUtils


class MobileAppUserRole(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    AGENT = "agent"
    VIEWER = "viewer"


class MobileAppSessionStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"


class MobileAppOverrideType(str, Enum):
    RESPONSE_OVERRIDE = "response_override"
    PRIORITY_CHANGE = "priority_change"
    AGENT_ASSIGNMENT = "agent_assignment"
    ESCALATION = "escalation"
    STATUS_UPDATE = "status_update"


class MobileAppNotificationType(str, Enum):
    URGENT_TICKET = "urgent_ticket"
    SLA_BREACH = "sla_breach"
    SYSTEM_ALERT = "system_alert"
    PERFORMANCE_UPDATE = "performance_update"
    OVERRIDE_REQUEST = "override_request"


class MobileAppMonitoringService:
    def __init__(self):
        self.integration_manager = IntegrationManager()
        self.analytics_manager = AnalyticsManager()
        # NLPUtils removed - not used in this service
        
    async def create_mobile_app_user(
        self, 
        db: Session, 
        request: CreateMobileAppUserRequest
    ) -> MobileAppUserResponse:
        """Create a new mobile app user"""
        try:
            user = MobileAppUser(
                username=request.username,
                email=request.email,
                role=request.role,
                permissions=request.permissions,
                device_ids=request.device_ids or [],
                is_active=request.is_active,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(user)
            db.commit()
            db.refresh(user)
            
            return MobileAppUserResponse(
                id=user.id,
                username=user.username,
                email=user.email,
                role=user.role,
                permissions=user.permissions,
                device_ids=user.device_ids,
                is_active=user.is_active,
                created_at=user.created_at,
                updated_at=user.updated_at
            )
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to create mobile app user: {str(e)}")
    
    async def get_mobile_app_user(
        self, 
        db: Session, 
        user_id: int
    ) -> MobileAppUserResponse:
        """Get mobile app user by ID"""
        user = db.query(MobileAppUser).filter(MobileAppUser.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Mobile app user not found")
        
        return MobileAppUserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            role=user.role,
            permissions=user.permissions,
            device_ids=user.device_ids,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
    
    async def list_mobile_app_users(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        role: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[MobileAppUserResponse]:
        """List mobile app users"""
        query = db.query(MobileAppUser)
        
        if role:
            query = query.filter(MobileAppUser.role == role)
        if is_active is not None:
            query = query.filter(MobileAppUser.is_active == is_active)
        
        users = query.offset(skip).limit(limit).all()
        
        return [
            MobileAppUserResponse(
                id=user.id,
                username=user.username,
                email=user.email,
                role=user.role,
                permissions=user.permissions,
                device_ids=user.device_ids,
                is_active=user.is_active,
                created_at=user.created_at,
                updated_at=user.updated_at
            ) for user in users
        ]
    
    async def update_mobile_app_user(
        self, 
        db: Session, 
        user_id: int, 
        request: UpdateMobileAppUserRequest
    ) -> MobileAppUserResponse:
        """Update mobile app user"""
        user = db.query(MobileAppUser).filter(MobileAppUser.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Mobile app user not found")
        
        try:
            if request.username is not None:
                user.username = request.username
            if request.email is not None:
                user.email = request.email
            if request.role is not None:
                user.role = request.role
            if request.permissions is not None:
                user.permissions = request.permissions
            if request.device_ids is not None:
                user.device_ids = request.device_ids
            if request.is_active is not None:
                user.is_active = request.is_active
            
            user.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(user)
            
            return MobileAppUserResponse(
                id=user.id,
                username=user.username,
                email=user.email,
                role=user.role,
                permissions=user.permissions,
                device_ids=user.device_ids,
                is_active=user.is_active,
                created_at=user.created_at,
                updated_at=user.updated_at
            )
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to update mobile app user: {str(e)}")
    
    async def delete_mobile_app_user(
        self, 
        db: Session, 
        user_id: int
    ) -> Dict[str, str]:
        """Delete mobile app user"""
        user = db.query(MobileAppUser).filter(MobileAppUser.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Mobile app user not found")
        
        try:
            db.delete(user)
            db.commit()
            return {"message": "Mobile app user deleted successfully"}
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to delete mobile app user: {str(e)}")
    
    async def create_mobile_app_session(
        self, 
        db: Session, 
        request: CreateMobileAppSessionRequest
    ) -> MobileAppSessionResponse:
        """Create a new mobile app session"""
        try:
            session = MobileAppSession(
                user_id=request.user_id,
                device_id=request.device_id,
                session_token=request.session_token,
                status=MobileAppSessionStatus.ACTIVE,
                last_activity=datetime.utcnow(),
                expires_at=request.expires_at or (datetime.utcnow() + timedelta(hours=24)),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(session)
            db.commit()
            db.refresh(session)
            
            return MobileAppSessionResponse(
                id=session.id,
                user_id=session.user_id,
                device_id=session.device_id,
                session_token=session.session_token,
                status=session.status,
                last_activity=session.last_activity,
                expires_at=session.expires_at,
                created_at=session.created_at,
                updated_at=session.updated_at
            )
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to create mobile app session: {str(e)}")
    
    async def get_mobile_app_session(
        self, 
        db: Session, 
        session_id: int
    ) -> MobileAppSessionResponse:
        """Get mobile app session by ID"""
        session = db.query(MobileAppSession).filter(MobileAppSession.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Mobile app session not found")
        
        return MobileAppSessionResponse(
            id=session.id,
            user_id=session.user_id,
            device_id=session.device_id,
            session_token=session.session_token,
            status=session.status,
            last_activity=session.last_activity,
            expires_at=session.expires_at,
            created_at=session.created_at,
            updated_at=session.updated_at
        )
    
    async def update_mobile_app_session(
        self, 
        db: Session, 
        session_id: int, 
        request: UpdateMobileAppSessionRequest
    ) -> MobileAppSessionResponse:
        """Update mobile app session"""
        session = db.query(MobileAppSession).filter(MobileAppSession.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Mobile app session not found")
        
        try:
            if request.status is not None:
                session.status = request.status
            if request.last_activity is not None:
                session.last_activity = request.last_activity
            else:
                session.last_activity = datetime.utcnow()
            if request.expires_at is not None:
                session.expires_at = request.expires_at
            
            session.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(session)
            
            return MobileAppSessionResponse(
                id=session.id,
                user_id=session.user_id,
                device_id=session.device_id,
                session_token=session.session_token,
                status=session.status,
                last_activity=session.last_activity,
                expires_at=session.expires_at,
                created_at=session.created_at,
                updated_at=session.updated_at
            )
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to update mobile app session: {str(e)}")
    
    async def create_mobile_app_override(
        self, 
        db: Session, 
        request: CreateMobileAppOverrideRequest
    ) -> MobileAppOverrideResponse:
        """Create a new mobile app override"""
        try:
            override = MobileAppOverride(
                user_id=request.user_id,
                ticket_id=request.ticket_id,
                override_type=request.override_type,
                original_value=request.original_value,
                new_value=request.new_value,
                reason=request.reason,
                is_approved=request.is_approved,
                approved_by=request.approved_by,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(override)
            db.commit()
            db.refresh(override)
            
            # Apply the override if approved
            if override.is_approved:
                await self._apply_override(db, override)
            
            return MobileAppOverrideResponse(
                id=override.id,
                user_id=override.user_id,
                ticket_id=override.ticket_id,
                override_type=override.override_type,
                original_value=override.original_value,
                new_value=override.new_value,
                reason=override.reason,
                is_approved=override.is_approved,
                approved_by=override.approved_by,
                created_at=override.created_at,
                updated_at=override.updated_at
            )
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to create mobile app override: {str(e)}")
    
    async def get_mobile_app_override(
        self, 
        db: Session, 
        override_id: int
    ) -> MobileAppOverrideResponse:
        """Get mobile app override by ID"""
        override = db.query(MobileAppOverride).filter(MobileAppOverride.id == override_id).first()
        if not override:
            raise HTTPException(status_code=404, detail="Mobile app override not found")
        
        return MobileAppOverrideResponse(
            id=override.id,
            user_id=override.user_id,
            ticket_id=override.ticket_id,
            override_type=override.override_type,
            original_value=override.original_value,
            new_value=override.new_value,
            reason=override.reason,
            is_approved=override.is_approved,
            approved_by=override.approved_by,
            created_at=override.created_at,
            updated_at=override.updated_at
        )
    
    async def list_mobile_app_overrides(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        user_id: Optional[int] = None,
        ticket_id: Optional[int] = None,
        override_type: Optional[str] = None,
        is_approved: Optional[bool] = None
    ) -> List[MobileAppOverrideResponse]:
        """List mobile app overrides"""
        query = db.query(MobileAppOverride)
        
        if user_id:
            query = query.filter(MobileAppOverride.user_id == user_id)
        if ticket_id:
            query = query.filter(MobileAppOverride.ticket_id == ticket_id)
        if override_type:
            query = query.filter(MobileAppOverride.override_type == override_type)
        if is_approved is not None:
            query = query.filter(MobileAppOverride.is_approved == is_approved)
        
        overrides = query.order_by(desc(MobileAppOverride.created_at)).offset(skip).limit(limit).all()
        
        return [
            MobileAppOverrideResponse(
                id=override.id,
                user_id=override.user_id,
                ticket_id=override.ticket_id,
                override_type=override.override_type,
                original_value=override.original_value,
                new_value=override.new_value,
                reason=override.reason,
                is_approved=override.is_approved,
                approved_by=override.approved_by,
                created_at=override.created_at,
                updated_at=override.updated_at
            ) for override in overrides
        ]
    
    async def approve_mobile_app_override(
        self, 
        db: Session, 
        override_id: int,
        approved_by: int
    ) -> MobileAppOverrideResponse:
        """Approve a mobile app override"""
        override = db.query(MobileAppOverride).filter(MobileAppOverride.id == override_id).first()
        if not override:
            raise HTTPException(status_code=404, detail="Mobile app override not found")
        
        try:
            override.is_approved = True
            override.approved_by = approved_by
            override.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(override)
            
            # Apply the override
            await self._apply_override(db, override)
            
            return MobileAppOverrideResponse(
                id=override.id,
                user_id=override.user_id,
                ticket_id=override.ticket_id,
                override_type=override.override_type,
                original_value=override.original_value,
                new_value=override.new_value,
                reason=override.reason,
                is_approved=override.is_approved,
                approved_by=override.approved_by,
                created_at=override.created_at,
                updated_at=override.updated_at
            )
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to approve mobile app override: {str(e)}")
    
    async def create_mobile_app_notification(
        self, 
        db: Session, 
        request: CreateMobileAppNotificationRequest
    ) -> MobileAppNotificationResponse:
        """Create a new mobile app notification"""
        try:
            notification = MobileAppNotification(
                user_id=request.user_id,
                notification_type=request.notification_type,
                title=request.title,
                message=request.message,
                data=request.data,
                is_read=request.is_read or False,
                sent_at=datetime.utcnow(),
                created_at=datetime.utcnow()
            )
            
            db.add(notification)
            db.commit()
            db.refresh(notification)
            
            # Send push notification
            await self._send_push_notification(db, notification)
            
            return MobileAppNotificationResponse(
                id=notification.id,
                user_id=notification.user_id,
                notification_type=notification.notification_type,
                title=notification.title,
                message=notification.message,
                data=notification.data,
                is_read=notification.is_read,
                sent_at=notification.sent_at,
                created_at=notification.created_at
            )
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to create mobile app notification: {str(e)}")
    
    async def get_mobile_app_notification(
        self, 
        db: Session, 
        notification_id: int
    ) -> MobileAppNotificationResponse:
        """Get mobile app notification by ID"""
        notification = db.query(MobileAppNotification).filter(MobileAppNotification.id == notification_id).first()
        if not notification:
            raise HTTPException(status_code=404, detail="Mobile app notification not found")
        
        return MobileAppNotificationResponse(
            id=notification.id,
            user_id=notification.user_id,
            notification_type=notification.notification_type,
            title=notification.title,
            message=notification.message,
            data=notification.data,
            is_read=notification.is_read,
            sent_at=notification.sent_at,
            created_at=notification.created_at
        )
    
    async def list_mobile_app_notifications(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        user_id: Optional[int] = None,
        notification_type: Optional[str] = None,
        is_read: Optional[bool] = None
    ) -> List[MobileAppNotificationResponse]:
        """List mobile app notifications"""
        query = db.query(MobileAppNotification)
        
        if user_id:
            query = query.filter(MobileAppNotification.user_id == user_id)
        if notification_type:
            query = query.filter(MobileAppNotification.notification_type == notification_type)
        if is_read is not None:
            query = query.filter(MobileAppNotification.is_read == is_read)
        
        notifications = query.order_by(desc(MobileAppNotification.created_at)).offset(skip).limit(limit).all()
        
        return [
            MobileAppNotificationResponse(
                id=notification.id,
                user_id=notification.user_id,
                notification_type=notification.notification_type,
                title=notification.title,
                message=notification.message,
                data=notification.data,
                is_read=notification.is_read,
                sent_at=notification.sent_at,
                created_at=notification.created_at
            ) for notification in notifications
        ]
    
    async def mark_notification_as_read(
        self, 
        db: Session, 
        notification_id: int
    ) -> MobileAppNotificationResponse:
        """Mark notification as read"""
        notification = db.query(MobileAppNotification).filter(MobileAppNotification.id == notification_id).first()
        if not notification:
            raise HTTPException(status_code=404, detail="Mobile app notification not found")
        
        try:
            notification.is_read = True
            
            db.commit()
            db.refresh(notification)
            
            return MobileAppNotificationResponse(
                id=notification.id,
                user_id=notification.user_id,
                notification_type=notification.notification_type,
                title=notification.title,
                message=notification.message,
                data=notification.data,
                is_read=notification.is_read,
                sent_at=notification.sent_at,
                created_at=notification.created_at
            )
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to mark notification as read: {str(e)}")
    
    async def get_mobile_app_analytics(
        self, 
        db: Session, 
        start_date: datetime,
        end_date: datetime,
        user_id: Optional[int] = None
    ) -> MobileAppAnalyticsResponse:
        """Get mobile app analytics"""
        try:
            # Build queries
            sessions_query = db.query(MobileAppSession).filter(
                and_(
                    MobileAppSession.created_at >= start_date,
                    MobileAppSession.created_at <= end_date
                )
            )
            
            overrides_query = db.query(MobileAppOverride).filter(
                and_(
                    MobileAppOverride.created_at >= start_date,
                    MobileAppOverride.created_at <= end_date
                )
            )
            
            notifications_query = db.query(MobileAppNotification).filter(
                and_(
                    MobileAppNotification.created_at >= start_date,
                    MobileAppNotification.created_at <= end_date
                )
            )
            
            if user_id:
                sessions_query = sessions_query.filter(MobileAppSession.user_id == user_id)
                overrides_query = overrides_query.filter(MobileAppOverride.user_id == user_id)
                notifications_query = notifications_query.filter(MobileAppNotification.user_id == user_id)
            
            sessions = sessions_query.all()
            overrides = overrides_query.all()
            notifications = notifications_query.all()
            
            # Calculate metrics
            total_sessions = len(sessions)
            active_sessions = len([s for s in sessions if s.status == MobileAppSessionStatus.ACTIVE])
            total_overrides = len(overrides)
            approved_overrides = len([o for o in overrides if o.is_approved])
            total_notifications = len(notifications)
            read_notifications = len([n for n in notifications if n.is_read])
            
            # Override type breakdown
            override_type_breakdown = {}
            for override in overrides:
                override_type = override.override_type
                if override_type not in override_type_breakdown:
                    override_type_breakdown[override_type] = 0
                override_type_breakdown[override_type] += 1
            
            # Notification type breakdown
            notification_type_breakdown = {}
            for notification in notifications:
                notification_type = notification.notification_type
                if notification_type not in notification_type_breakdown:
                    notification_type_breakdown[notification_type] = 0
                notification_type_breakdown[notification_type] += 1
            
            return MobileAppAnalyticsResponse(
                period_start=start_date,
                period_end=end_date,
                total_sessions=total_sessions,
                active_sessions=active_sessions,
                total_overrides=total_overrides,
                approved_overrides=approved_overrides,
                override_approval_rate=approved_overrides / total_overrides if total_overrides > 0 else 0,
                total_notifications=total_notifications,
                read_notifications=read_notifications,
                notification_read_rate=read_notifications / total_notifications if total_notifications > 0 else 0,
                override_type_breakdown=override_type_breakdown,
                notification_type_breakdown=notification_type_breakdown
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get mobile app analytics: {str(e)}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check the health of mobile app monitoring system"""
        try:
            db = next(get_db())
            user_count = db.query(MobileAppUser).count()
            session_count = db.query(MobileAppSession).count()
            override_count = db.query(MobileAppOverride).count()
            notification_count = db.query(MobileAppNotification).count()
            
            return {
                "status": "healthy",
                "database": {
                    "connected": True,
                    "users_count": user_count,
                    "sessions_count": session_count,
                    "overrides_count": override_count,
                    "notifications_count": notification_count
                },
                "last_check": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "last_check": datetime.utcnow().isoformat()
            }
    
    async def _apply_override(self, db: Session, override: MobileAppOverride):
        """Apply an approved override"""
        try:
            if override.override_type == MobileAppOverrideType.RESPONSE_OVERRIDE:
                # Update ticket response
                ticket = db.query(SupportTicket).filter(SupportTicket.id == override.ticket_id).first()
                if ticket:
                    ticket.resolution = override.new_value
                    ticket.updated_at = datetime.utcnow()
            
            elif override.override_type == MobileAppOverrideType.PRIORITY_CHANGE:
                # Update ticket priority
                ticket = db.query(SupportTicket).filter(SupportTicket.id == override.ticket_id).first()
                if ticket:
                    ticket.priority = override.new_value
                    ticket.updated_at = datetime.utcnow()
            
            elif override.override_type == MobileAppOverrideType.AGENT_ASSIGNMENT:
                # Update ticket assignment
                ticket = db.query(SupportTicket).filter(SupportTicket.id == override.ticket_id).first()
                if ticket:
                    ticket.assigned_agent_id = override.new_value
                    ticket.updated_at = datetime.utcnow()
            
            elif override.override_type == MobileAppOverrideType.STATUS_UPDATE:
                # Update ticket status
                ticket = db.query(SupportTicket).filter(SupportTicket.id == override.ticket_id).first()
                if ticket:
                    ticket.status = override.new_value
                    ticket.updated_at = datetime.utcnow()
            
            db.commit()
            
        except Exception as e:
            db.rollback()
            raise Exception(f"Failed to apply override: {str(e)}")
    
    async def _send_push_notification(self, db: Session, notification: MobileAppNotification):
        """Send push notification to mobile device"""
        try:
            # Get user's devices
            user = db.query(MobileAppUser).filter(MobileAppUser.id == notification.user_id).first()
            if user and user.device_ids:
                for device_id in user.device_ids:
                    await self.integration_manager.send_push_notification({
                        "device_id": device_id,
                        "title": notification.title,
                        "message": notification.message,
                        "data": notification.data
                    })
                    
        except Exception:
            pass  # Silently fail push notification
