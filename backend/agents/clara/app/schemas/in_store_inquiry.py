from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class InStoreInquiryRequest(BaseModel):
    product_id: Optional[int] = None
    inquiry_type: Optional[str] = None
    details: Optional[Dict[str, Any]] = {}

class InStoreInquiryResponse(BaseModel):
    id: int
    product_id: Optional[int] = None
    inquiry_type: Optional[str] = None
    details: Optional[Dict[str, Any]] = {}
    created_at: Optional[datetime] = None


class CreateInStoreKioskRequest(BaseModel):
    name: str
    description: Optional[str] = None
    location_id: Optional[int] = None
    device_type: Optional[str] = None
    device_id: Optional[str] = None
    capabilities: Optional[Dict[str, Any]] = {}
    is_active: bool = True


class UpdateInStoreKioskRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    location_id: Optional[int] = None
    device_type: Optional[str] = None
    device_id: Optional[str] = None
    capabilities: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class CreateInStoreInquiryRequest(BaseModel):
    product_id: Optional[int] = None
    inquiry_type: Optional[str] = None
    details: Optional[Dict[str, Any]] = {}


class UpdateInStoreInquiryRequest(BaseModel):
    product_id: Optional[int] = None
    inquiry_type: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class CreateInStoreQRCodeRequest(BaseModel):
    location_id: int
    data: Dict[str, Any]


class UpdateInStoreQRCodeRequest(BaseModel):
    data: Optional[Dict[str, Any]] = None


class CreateInStoreLocationRequest(BaseModel):
    name: str
    address: Optional[str] = None


class UpdateInStoreLocationRequest(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None


class InStoreKioskResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    location_id: Optional[int] = None
    device_type: Optional[str] = None
    device_id: Optional[str] = None
    capabilities: Optional[Dict[str, Any]] = {}
    is_active: bool = True
    created_at: Optional[datetime] = None


class InStoreQRCodeResponse(BaseModel):
    id: int
    location_id: int
    data: Dict[str, Any]
    created_at: Optional[datetime] = None


class InStoreLocationResponse(BaseModel):
    id: int
    name: str
    address: Optional[str] = None
    created_at: Optional[datetime] = None


class InStoreDeviceResponse(BaseModel):
    id: int
    device_id: str
    device_type: str
    created_at: Optional[datetime] = None


class InStoreAnalyticsResponse(BaseModel):
    total_inquiries: int
    resolved_inquiries: int
    average_response_time: float


class CreateInStoreDeviceRequest(BaseModel):
    device_id: str
    device_type: str
    location_id: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


class UpdateInStoreDeviceRequest(BaseModel):
    device_type: Optional[str] = None
    location_id: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None
