from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session

from ..database import get_clara_database, get_db
from ..services.in_store_inquiry_service import InStoreInquiryService
from ..schemas.in_store_inquiry import (
    CreateInStoreKioskRequest, UpdateInStoreKioskRequest,
    CreateInStoreInquiryRequest, UpdateInStoreInquiryRequest,
    CreateInStoreQRCodeRequest, UpdateInStoreQRCodeRequest,
    CreateInStoreLocationRequest, UpdateInStoreLocationRequest,
    CreateInStoreDeviceRequest, UpdateInStoreDeviceRequest,
    InStoreKioskResponse, InStoreInquiryResponse, InStoreQRCodeResponse,
    InStoreLocationResponse, InStoreDeviceResponse, InStoreAnalyticsResponse
)

router = APIRouter()
in_store_service = InStoreInquiryService()


@router.post("/kiosks", response_model=InStoreKioskResponse)
async def create_in_store_kiosk(
    request: CreateInStoreKioskRequest,
    db: Session = Depends(get_db)
):
    """Create a new in-store kiosk"""
    return await in_store_service.create_in_store_kiosk(db, request)


@router.get("/kiosks/{kiosk_id}", response_model=InStoreKioskResponse)
async def get_in_store_kiosk(
    kiosk_id: int,
    db: Session = Depends(get_db)
):
    """Get in-store kiosk by ID"""
    return await in_store_service.get_in_store_kiosk(db, kiosk_id)


@router.get("/kiosks", response_model=List[InStoreKioskResponse])
async def list_in_store_kiosks(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    location_id: Optional[int] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    """List in-store kiosks"""
    return await in_store_service.list_in_store_kiosks(
        db, skip=skip, limit=limit, location_id=location_id, is_active=is_active
    )


@router.put("/kiosks/{kiosk_id}", response_model=InStoreKioskResponse)
async def update_in_store_kiosk(
    kiosk_id: int,
    request: UpdateInStoreKioskRequest,
    db: Session = Depends(get_db)
):
    """Update in-store kiosk"""
    return await in_store_service.update_in_store_kiosk(db, kiosk_id, request)


@router.delete("/kiosks/{kiosk_id}")
async def delete_in_store_kiosk(
    kiosk_id: int,
    db: Session = Depends(get_db)
):
    """Delete in-store kiosk"""
    return await in_store_service.delete_in_store_kiosk(db, kiosk_id)


@router.post("/kiosks/{kiosk_id}/activate")
async def activate_kiosk(
    kiosk_id: int,
    db: Session = Depends(get_db)
):
    """Activate in-store kiosk"""
    return await in_store_service.activate_kiosk(db, kiosk_id)


@router.post("/kiosks/{kiosk_id}/deactivate")
async def deactivate_kiosk(
    kiosk_id: int,
    db: Session = Depends(get_db)
):
    """Deactivate in-store kiosk"""
    return await in_store_service.deactivate_kiosk(db, kiosk_id)


@router.post("/inquiries", response_model=InStoreInquiryResponse)
async def create_in_store_inquiry(
    request: CreateInStoreInquiryRequest,
    db: Session = Depends(get_db)
):
    """Create a new in-store inquiry"""
    return await in_store_service.create_in_store_inquiry(db, request)


@router.get("/inquiries/{inquiry_id}", response_model=InStoreInquiryResponse)
async def get_in_store_inquiry(
    inquiry_id: int,
    db: Session = Depends(get_db)
):
    """Get in-store inquiry by ID"""
    return await in_store_service.get_in_store_inquiry(db, inquiry_id)


@router.get("/inquiries", response_model=List[InStoreInquiryResponse])
async def list_in_store_inquiries(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    kiosk_id: Optional[int] = Query(None),
    location_id: Optional[int] = Query(None),
    inquiry_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List in-store inquiries"""
    return await in_store_service.list_in_store_inquiries(
        db, skip=skip, limit=limit, kiosk_id=kiosk_id, location_id=location_id,
        inquiry_type=inquiry_type, status=status
    )


@router.put("/inquiries/{inquiry_id}", response_model=InStoreInquiryResponse)
async def update_in_store_inquiry(
    inquiry_id: int,
    request: UpdateInStoreInquiryRequest,
    db: Session = Depends(get_db)
):
    """Update in-store inquiry"""
    return await in_store_service.update_in_store_inquiry(db, inquiry_id, request)


@router.delete("/inquiries/{inquiry_id}")
async def delete_in_store_inquiry(
    inquiry_id: int,
    db: Session = Depends(get_db)
):
    """Delete in-store inquiry"""
    return await in_store_service.delete_in_store_inquiry(db, inquiry_id)


@router.post("/inquiries/{inquiry_id}/resolve")
async def resolve_inquiry(
    inquiry_id: int,
    resolution_notes: str = Query(...),
    db: Session = Depends(get_db)
):
    """Resolve in-store inquiry"""
    return await in_store_service.resolve_inquiry(db, inquiry_id, resolution_notes)


@router.post("/qr-codes", response_model=InStoreQRCodeResponse)
async def create_in_store_qr_code(
    request: CreateInStoreQRCodeRequest,
    db: Session = Depends(get_db)
):
    """Create a new in-store QR code"""
    return await in_store_service.create_in_store_qr_code(db, request)


@router.get("/qr-codes/{qr_code_id}", response_model=InStoreQRCodeResponse)
async def get_in_store_qr_code(
    qr_code_id: int,
    db: Session = Depends(get_db)
):
    """Get in-store QR code by ID"""
    return await in_store_service.get_in_store_qr_code(db, qr_code_id)


@router.get("/qr-codes", response_model=List[InStoreQRCodeResponse])
async def list_in_store_qr_codes(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    location_id: Optional[int] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    """List in-store QR codes"""
    return await in_store_service.list_in_store_qr_codes(
        db, skip=skip, limit=limit, location_id=location_id, is_active=is_active
    )


@router.put("/qr-codes/{qr_code_id}", response_model=InStoreQRCodeResponse)
async def update_in_store_qr_code(
    qr_code_id: int,
    request: UpdateInStoreQRCodeRequest,
    db: Session = Depends(get_db)
):
    """Update in-store QR code"""
    return await in_store_service.update_in_store_qr_code(db, qr_code_id, request)


@router.delete("/qr-codes/{qr_code_id}")
async def delete_in_store_qr_code(
    qr_code_id: int,
    db: Session = Depends(get_db)
):
    """Delete in-store QR code"""
    return await in_store_service.delete_in_store_qr_code(db, qr_code_id)


@router.get("/qr-codes/{qr_code_id}/scan")
async def scan_qr_code(
    qr_code_id: int,
    customer_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """Scan in-store QR code"""
    return await in_store_service.scan_qr_code(db, qr_code_id, customer_id)


@router.post("/locations", response_model=InStoreLocationResponse)
async def create_in_store_location(
    request: CreateInStoreLocationRequest,
    db: Session = Depends(get_db)
):
    """Create a new in-store location"""
    return await in_store_service.create_in_store_location(db, request)


@router.get("/locations/{location_id}", response_model=InStoreLocationResponse)
async def get_in_store_location(
    location_id: int,
    db: Session = Depends(get_db)
):
    """Get in-store location by ID"""
    return await in_store_service.get_in_store_location(db, location_id)


@router.get("/locations", response_model=List[InStoreLocationResponse])
async def list_in_store_locations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    store_id: Optional[int] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    """List in-store locations"""
    return await in_store_service.list_in_store_locations(
        db, skip=skip, limit=limit, store_id=store_id, is_active=is_active
    )


@router.put("/locations/{location_id}", response_model=InStoreLocationResponse)
async def update_in_store_location(
    location_id: int,
    request: UpdateInStoreLocationRequest,
    db: Session = Depends(get_db)
):
    """Update in-store location"""
    return await in_store_service.update_in_store_location(db, location_id, request)


@router.delete("/locations/{location_id}")
async def delete_in_store_location(
    location_id: int,
    db: Session = Depends(get_db)
):
    """Delete in-store location"""
    return await in_store_service.delete_in_store_location(db, location_id)


@router.post("/devices", response_model=InStoreDeviceResponse)
async def create_in_store_device(
    request: CreateInStoreDeviceRequest,
    db: Session = Depends(get_db)
):
    """Create a new in-store device"""
    return await in_store_service.create_in_store_device(db, request)


@router.get("/devices/{device_id}", response_model=InStoreDeviceResponse)
async def get_in_store_device(
    device_id: int,
    db: Session = Depends(get_db)
):
    """Get in-store device by ID"""
    return await in_store_service.get_in_store_device(db, device_id)


@router.get("/devices", response_model=List[InStoreDeviceResponse])
async def list_in_store_devices(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    location_id: Optional[int] = Query(None),
    device_type: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    """List in-store devices"""
    return await in_store_service.list_in_store_devices(
        db, skip=skip, limit=limit, location_id=location_id,
        device_type=device_type, is_active=is_active
    )


@router.put("/devices/{device_id}", response_model=InStoreDeviceResponse)
async def update_in_store_device(
    device_id: int,
    request: UpdateInStoreDeviceRequest,
    db: Session = Depends(get_db)
):
    """Update in-store device"""
    return await in_store_service.update_in_store_device(db, device_id, request)


@router.delete("/devices/{device_id}")
async def delete_in_store_device(
    device_id: int,
    db: Session = Depends(get_db)
):
    """Delete in-store device"""
    return await in_store_service.delete_in_store_device(db, device_id)


@router.get("/analytics", response_model=InStoreAnalyticsResponse)
async def get_in_store_analytics(
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    location_id: Optional[int] = Query(None),
    kiosk_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """Get in-store analytics"""
    return await in_store_service.get_in_store_analytics(db, start_date, end_date, location_id, kiosk_id)


@router.get("/health")
async def health_check():
    """Check the health of in-store inquiry system"""
    return await in_store_service.health_check()
