from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from fastapi import HTTPException, BackgroundTasks
import json
import asyncio
from enum import Enum

from ..models import (
    InStoreKiosk, InStoreInquiry, InStoreQRCode, InStoreLocation, InStoreDevice,
    SupportTicket, CustomerInteraction, SupportAgent
)
from ..schemas.in_store_inquiry import (
    CreateInStoreKioskRequest, UpdateInStoreKioskRequest,
    CreateInStoreInquiryRequest, UpdateInStoreInquiryRequest,
    CreateInStoreQRCodeRequest, UpdateInStoreQRCodeRequest,
    CreateInStoreLocationRequest, UpdateInStoreLocationRequest,
    InStoreKioskResponse, InStoreInquiryResponse, InStoreQRCodeResponse,
    InStoreLocationResponse, InStoreDeviceResponse, InStoreAnalyticsResponse
)
from ..database import get_clara_database
from ..core.config import settings
from ..core.integrations import IntegrationManager
from ..core.analytics import AnalyticsManager
from ..core.nlp import NLPUtils


class InStoreInquiryType(str, Enum):
    PRODUCT_INFO = "product_info"
    PRICING = "pricing"
    AVAILABILITY = "availability"
    ORDER_STATUS = "order_status"
    RETURNS = "returns"
    GENERAL = "general"


class InStoreInquiryStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    CLOSED = "closed"


class InStoreDeviceType(str, Enum):
    KIOSK = "kiosk"
    TABLET = "tablet"
    MOBILE = "mobile"
    QR_CODE = "qr_code"


class InStoreInquiryService:
    def __init__(self):
        self.integration_manager = IntegrationManager()
        self.analytics_manager = AnalyticsManager()
        # NLPUtils removed - not used in this service
        
    async def create_in_store_kiosk(
        self, 
        db: Session, 
        request: CreateInStoreKioskRequest
    ) -> InStoreKioskResponse:
        """Create a new in-store kiosk"""
        try:
            kiosk = InStoreKiosk(
                name=request.name,
                description=request.description,
                location_id=request.location_id,
                device_type=request.device_type,
                device_id=request.device_id,
                capabilities=request.capabilities,
                is_active=request.is_active,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(kiosk)
            db.commit()
            db.refresh(kiosk)
            
            return InStoreKioskResponse(
                id=kiosk.id,
                name=kiosk.name,
                description=kiosk.description,
                location_id=kiosk.location_id,
                device_type=kiosk.device_type,
                device_id=kiosk.device_id,
                capabilities=kiosk.capabilities,
                is_active=kiosk.is_active,
                created_at=kiosk.created_at,
                updated_at=kiosk.updated_at
            )
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to create in-store kiosk: {str(e)}")
    
    async def get_in_store_kiosk(
        self, 
        db: Session, 
        kiosk_id: int
    ) -> InStoreKioskResponse:
        """Get in-store kiosk by ID"""
        kiosk = db.query(InStoreKiosk).filter(InStoreKiosk.id == kiosk_id).first()
        if not kiosk:
            raise HTTPException(status_code=404, detail="In-store kiosk not found")
        
        return InStoreKioskResponse(
            id=kiosk.id,
            name=kiosk.name,
            description=kiosk.description,
            location_id=kiosk.location_id,
            device_type=kiosk.device_type,
            device_id=kiosk.device_id,
            capabilities=kiosk.capabilities,
            is_active=kiosk.is_active,
            created_at=kiosk.created_at,
            updated_at=kiosk.updated_at
        )
    
    async def list_in_store_kiosks(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        location_id: Optional[int] = None,
        device_type: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[InStoreKioskResponse]:
        """List in-store kiosks"""
        query = db.query(InStoreKiosk)
        
        if location_id:
            query = query.filter(InStoreKiosk.location_id == location_id)
        if device_type:
            query = query.filter(InStoreKiosk.device_type == device_type)
        if is_active is not None:
            query = query.filter(InStoreKiosk.is_active == is_active)
        
        kiosks = query.offset(skip).limit(limit).all()
        
        return [
            InStoreKioskResponse(
                id=kiosk.id,
                name=kiosk.name,
                description=kiosk.description,
                location_id=kiosk.location_id,
                device_type=kiosk.device_type,
                device_id=kiosk.device_id,
                capabilities=kiosk.capabilities,
                is_active=kiosk.is_active,
                created_at=kiosk.created_at,
                updated_at=kiosk.updated_at
            ) for kiosk in kiosks
        ]
    
    async def update_in_store_kiosk(
        self, 
        db: Session, 
        kiosk_id: int, 
        request: UpdateInStoreKioskRequest
    ) -> InStoreKioskResponse:
        """Update in-store kiosk"""
        kiosk = db.query(InStoreKiosk).filter(InStoreKiosk.id == kiosk_id).first()
        if not kiosk:
            raise HTTPException(status_code=404, detail="In-store kiosk not found")
        
        try:
            if request.name is not None:
                kiosk.name = request.name
            if request.description is not None:
                kiosk.description = request.description
            if request.location_id is not None:
                kiosk.location_id = request.location_id
            if request.device_type is not None:
                kiosk.device_type = request.device_type
            if request.device_id is not None:
                kiosk.device_id = request.device_id
            if request.capabilities is not None:
                kiosk.capabilities = request.capabilities
            if request.is_active is not None:
                kiosk.is_active = request.is_active
            
            kiosk.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(kiosk)
            
            return InStoreKioskResponse(
                id=kiosk.id,
                name=kiosk.name,
                description=kiosk.description,
                location_id=kiosk.location_id,
                device_type=kiosk.device_type,
                device_id=kiosk.device_id,
                capabilities=kiosk.capabilities,
                is_active=kiosk.is_active,
                created_at=kiosk.created_at,
                updated_at=kiosk.updated_at
            )
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to update in-store kiosk: {str(e)}")
    
    async def delete_in_store_kiosk(
        self, 
        db: Session, 
        kiosk_id: int
    ) -> Dict[str, str]:
        """Delete in-store kiosk"""
        kiosk = db.query(InStoreKiosk).filter(InStoreKiosk.id == kiosk_id).first()
        if not kiosk:
            raise HTTPException(status_code=404, detail="In-store kiosk not found")
        
        try:
            db.delete(kiosk)
            db.commit()
            return {"message": "In-store kiosk deleted successfully"}
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to delete in-store kiosk: {str(e)}")
    
    async def create_in_store_inquiry(
        self, 
        db: Session, 
        request: CreateInStoreInquiryRequest
    ) -> InStoreInquiryResponse:
        """Create a new in-store inquiry"""
        try:
            inquiry = InStoreInquiry(
                kiosk_id=request.kiosk_id,
                location_id=request.location_id,
                inquiry_type=request.inquiry_type,
                customer_question=request.customer_question,
                customer_info=request.customer_info,
                product_info=request.product_info,
                status=InStoreInquiryStatus.PENDING,
                priority=request.priority,
                assigned_agent_id=request.assigned_agent_id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(inquiry)
            db.commit()
            db.refresh(inquiry)
            
            # Create corresponding support ticket
            ticket = SupportTicket(
                title=f"In-Store Inquiry: {request.inquiry_type}",
                description=request.customer_question,
                customer_id=request.customer_info.get("customer_id") if request.customer_info else None,
                category=request.inquiry_type,
                priority=request.priority,
                source="in_store",
                metadata={
                    "kiosk_id": request.kiosk_id,
                    "location_id": request.location_id,
                    "inquiry_id": inquiry.id
                },
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(ticket)
            db.commit()
            
            return InStoreInquiryResponse(
                id=inquiry.id,
                kiosk_id=inquiry.kiosk_id,
                location_id=inquiry.location_id,
                inquiry_type=inquiry.inquiry_type,
                customer_question=inquiry.customer_question,
                customer_info=inquiry.customer_info,
                product_info=inquiry.product_info,
                status=inquiry.status,
                priority=inquiry.priority,
                assigned_agent_id=inquiry.assigned_agent_id,
                resolution=inquiry.resolution,
                created_at=inquiry.created_at,
                updated_at=inquiry.updated_at
            )
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to create in-store inquiry: {str(e)}")
    
    async def get_in_store_inquiry(
        self, 
        db: Session, 
        inquiry_id: int
    ) -> InStoreInquiryResponse:
        """Get in-store inquiry by ID"""
        inquiry = db.query(InStoreInquiry).filter(InStoreInquiry.id == inquiry_id).first()
        if not inquiry:
            raise HTTPException(status_code=404, detail="In-store inquiry not found")
        
        return InStoreInquiryResponse(
            id=inquiry.id,
            kiosk_id=inquiry.kiosk_id,
            location_id=inquiry.location_id,
            inquiry_type=inquiry.inquiry_type,
            customer_question=inquiry.customer_question,
            customer_info=inquiry.customer_info,
            product_info=inquiry.product_info,
            status=inquiry.status,
            priority=inquiry.priority,
            assigned_agent_id=inquiry.assigned_agent_id,
            resolution=inquiry.resolution,
            created_at=inquiry.created_at,
            updated_at=inquiry.updated_at
        )
    
    async def list_in_store_inquiries(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        kiosk_id: Optional[int] = None,
        location_id: Optional[int] = None,
        inquiry_type: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[InStoreInquiryResponse]:
        """List in-store inquiries"""
        query = db.query(InStoreInquiry)
        
        if kiosk_id:
            query = query.filter(InStoreInquiry.kiosk_id == kiosk_id)
        if location_id:
            query = query.filter(InStoreInquiry.location_id == location_id)
        if inquiry_type:
            query = query.filter(InStoreInquiry.inquiry_type == inquiry_type)
        if status:
            query = query.filter(InStoreInquiry.status == status)
        
        inquiries = query.order_by(desc(InStoreInquiry.created_at)).offset(skip).limit(limit).all()
        
        return [
            InStoreInquiryResponse(
                id=inquiry.id,
                kiosk_id=inquiry.kiosk_id,
                location_id=inquiry.location_id,
                inquiry_type=inquiry.inquiry_type,
                customer_question=inquiry.customer_question,
                customer_info=inquiry.customer_info,
                product_info=inquiry.product_info,
                status=inquiry.status,
                priority=inquiry.priority,
                assigned_agent_id=inquiry.assigned_agent_id,
                resolution=inquiry.resolution,
                created_at=inquiry.created_at,
                updated_at=inquiry.updated_at
            ) for inquiry in inquiries
        ]
    
    async def update_in_store_inquiry(
        self, 
        db: Session, 
        inquiry_id: int, 
        request: UpdateInStoreInquiryRequest
    ) -> InStoreInquiryResponse:
        """Update in-store inquiry"""
        inquiry = db.query(InStoreInquiry).filter(InStoreInquiry.id == inquiry_id).first()
        if not inquiry:
            raise HTTPException(status_code=404, detail="In-store inquiry not found")
        
        try:
            if request.inquiry_type is not None:
                inquiry.inquiry_type = request.inquiry_type
            if request.customer_question is not None:
                inquiry.customer_question = request.customer_question
            if request.customer_info is not None:
                inquiry.customer_info = request.customer_info
            if request.product_info is not None:
                inquiry.product_info = request.product_info
            if request.status is not None:
                inquiry.status = request.status
            if request.priority is not None:
                inquiry.priority = request.priority
            if request.assigned_agent_id is not None:
                inquiry.assigned_agent_id = request.assigned_agent_id
            if request.resolution is not None:
                inquiry.resolution = request.resolution
            
            inquiry.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(inquiry)
            
            return InStoreInquiryResponse(
                id=inquiry.id,
                kiosk_id=inquiry.kiosk_id,
                location_id=inquiry.location_id,
                inquiry_type=inquiry.inquiry_type,
                customer_question=inquiry.customer_question,
                customer_info=inquiry.customer_info,
                product_info=inquiry.product_info,
                status=inquiry.status,
                priority=inquiry.priority,
                assigned_agent_id=inquiry.assigned_agent_id,
                resolution=inquiry.resolution,
                created_at=inquiry.created_at,
                updated_at=inquiry.updated_at
            )
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to update in-store inquiry: {str(e)}")
    
    async def create_in_store_qr_code(
        self, 
        db: Session, 
        request: CreateInStoreQRCodeRequest
    ) -> InStoreQRCodeResponse:
        """Create a new in-store QR code"""
        try:
            qr_code = InStoreQRCode(
                name=request.name,
                description=request.description,
                location_id=request.location_id,
                qr_code_data=request.qr_code_data,
                target_url=request.target_url,
                inquiry_type=request.inquiry_type,
                is_active=request.is_active,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(qr_code)
            db.commit()
            db.refresh(qr_code)
            
            return InStoreQRCodeResponse(
                id=qr_code.id,
                name=qr_code.name,
                description=qr_code.description,
                location_id=qr_code.location_id,
                qr_code_data=qr_code.qr_code_data,
                target_url=qr_code.target_url,
                inquiry_type=qr_code.inquiry_type,
                is_active=qr_code.is_active,
                created_at=qr_code.created_at,
                updated_at=qr_code.updated_at
            )
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to create in-store QR code: {str(e)}")
    
    async def get_in_store_qr_code(
        self, 
        db: Session, 
        qr_code_id: int
    ) -> InStoreQRCodeResponse:
        """Get in-store QR code by ID"""
        qr_code = db.query(InStoreQRCode).filter(InStoreQRCode.id == qr_code_id).first()
        if not qr_code:
            raise HTTPException(status_code=404, detail="In-store QR code not found")
        
        return InStoreQRCodeResponse(
            id=qr_code.id,
            name=qr_code.name,
            description=qr_code.description,
            location_id=qr_code.location_id,
            qr_code_data=qr_code.qr_code_data,
            target_url=qr_code.target_url,
            inquiry_type=qr_code.inquiry_type,
            is_active=qr_code.is_active,
            created_at=qr_code.created_at,
            updated_at=qr_code.updated_at
        )
    
    async def list_in_store_qr_codes(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        location_id: Optional[int] = None,
        inquiry_type: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[InStoreQRCodeResponse]:
        """List in-store QR codes"""
        query = db.query(InStoreQRCode)
        
        if location_id:
            query = query.filter(InStoreQRCode.location_id == location_id)
        if inquiry_type:
            query = query.filter(InStoreQRCode.inquiry_type == inquiry_type)
        if is_active is not None:
            query = query.filter(InStoreQRCode.is_active == is_active)
        
        qr_codes = query.offset(skip).limit(limit).all()
        
        return [
            InStoreQRCodeResponse(
                id=qr_code.id,
                name=qr_code.name,
                description=qr_code.description,
                location_id=qr_code.location_id,
                qr_code_data=qr_code.qr_code_data,
                target_url=qr_code.target_url,
                inquiry_type=qr_code.inquiry_type,
                is_active=qr_code.is_active,
                created_at=qr_code.created_at,
                updated_at=qr_code.updated_at
            ) for qr_code in qr_codes
        ]
    
    async def create_in_store_location(
        self, 
        db: Session, 
        request: CreateInStoreLocationRequest
    ) -> InStoreLocationResponse:
        """Create a new in-store location"""
        try:
            location = InStoreLocation(
                name=request.name,
                description=request.description,
                address=request.address,
                coordinates=request.coordinates,
                store_type=request.store_type,
                is_active=request.is_active,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(location)
            db.commit()
            db.refresh(location)
            
            return InStoreLocationResponse(
                id=location.id,
                name=location.name,
                description=location.description,
                address=location.address,
                coordinates=location.coordinates,
                store_type=location.store_type,
                is_active=location.is_active,
                created_at=location.created_at,
                updated_at=location.updated_at
            )
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to create in-store location: {str(e)}")
    
    async def get_in_store_location(
        self, 
        db: Session, 
        location_id: int
    ) -> InStoreLocationResponse:
        """Get in-store location by ID"""
        location = db.query(InStoreLocation).filter(InStoreLocation.id == location_id).first()
        if not location:
            raise HTTPException(status_code=404, detail="In-store location not found")
        
        return InStoreLocationResponse(
            id=location.id,
            name=location.name,
            description=location.description,
            address=location.address,
            coordinates=location.coordinates,
            store_type=location.store_type,
            is_active=location.is_active,
            created_at=location.created_at,
            updated_at=location.updated_at
        )
    
    async def list_in_store_locations(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        store_type: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[InStoreLocationResponse]:
        """List in-store locations"""
        query = db.query(InStoreLocation)
        
        if store_type:
            query = query.filter(InStoreLocation.store_type == store_type)
        if is_active is not None:
            query = query.filter(InStoreLocation.is_active == is_active)
        
        locations = query.offset(skip).limit(limit).all()
        
        return [
            InStoreLocationResponse(
                id=location.id,
                name=location.name,
                description=location.description,
                address=location.address,
                coordinates=location.coordinates,
                store_type=location.store_type,
                is_active=location.is_active,
                created_at=location.created_at,
                updated_at=location.updated_at
            ) for location in locations
        ]
    
    async def get_in_store_analytics(
        self, 
        db: Session, 
        start_date: datetime,
        end_date: datetime,
        location_id: Optional[int] = None
    ) -> InStoreAnalyticsResponse:
        """Get in-store analytics"""
        try:
            # Build query
            query = db.query(InStoreInquiry).filter(
                and_(
                    InStoreInquiry.created_at >= start_date,
                    InStoreInquiry.created_at <= end_date
                )
            )
            
            if location_id:
                query = query.filter(InStoreInquiry.location_id == location_id)
            
            inquiries = query.all()
            
            # Calculate metrics
            total_inquiries = len(inquiries)
            resolved_inquiries = len([i for i in inquiries if i.status == InStoreInquiryStatus.RESOLVED])
            escalated_inquiries = len([i for i in inquiries if i.status == InStoreInquiryStatus.ESCALATED])
            
            # Inquiry type breakdown
            inquiry_type_breakdown = {}
            for inquiry in inquiries:
                inquiry_type = inquiry.inquiry_type
                if inquiry_type not in inquiry_type_breakdown:
                    inquiry_type_breakdown[inquiry_type] = 0
                inquiry_type_breakdown[inquiry_type] += 1
            
            # Location breakdown
            location_breakdown = {}
            for inquiry in inquiries:
                location_id = inquiry.location_id
                if location_id not in location_breakdown:
                    location_breakdown[location_id] = 0
                location_breakdown[location_id] += 1
            
            # Average resolution time
            resolution_times = []
            for inquiry in inquiries:
                if inquiry.status == InStoreInquiryStatus.RESOLVED and inquiry.updated_at:
                    duration = (inquiry.updated_at - inquiry.created_at).total_seconds() / 60  # minutes
                    resolution_times.append(duration)
            
            avg_resolution_time = sum(resolution_times) / len(resolution_times) if resolution_times else 0
            
            return InStoreAnalyticsResponse(
                period_start=start_date,
                period_end=end_date,
                total_inquiries=total_inquiries,
                resolved_inquiries=resolved_inquiries,
                escalated_inquiries=escalated_inquiries,
                resolution_rate=resolved_inquiries / total_inquiries if total_inquiries > 0 else 0,
                escalation_rate=escalated_inquiries / total_inquiries if total_inquiries > 0 else 0,
                avg_resolution_time_minutes=avg_resolution_time,
                inquiry_type_breakdown=inquiry_type_breakdown,
                location_breakdown=location_breakdown
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get in-store analytics: {str(e)}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check the health of in-store inquiry system"""
        try:
            db = next(get_db())
            kiosk_count = db.query(InStoreKiosk).count()
            inquiry_count = db.query(InStoreInquiry).count()
            qr_code_count = db.query(InStoreQRCode).count()
            location_count = db.query(InStoreLocation).count()
            
            return {
                "status": "healthy",
                "database": {
                    "connected": True,
                    "kiosks_count": kiosk_count,
                    "inquiries_count": inquiry_count,
                    "qr_codes_count": qr_code_count,
                    "locations_count": location_count
                },
                "last_check": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "last_check": datetime.utcnow().isoformat()
            }
