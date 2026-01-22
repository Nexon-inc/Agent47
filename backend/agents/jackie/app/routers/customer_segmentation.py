from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import json

from ..database import get_db
from ..services.customer_segmentation_service import CustomerSegmentationService
from ..models import JackieCustomerSegment
from pydantic import BaseModel
from typing import Dict, Any

router = APIRouter(prefix="/customer-segmentation", tags=["Customer Segmentation"])

class CreateSegmentRequest(BaseModel):
    name: str
    description: str
    criteria: Dict[str, Any]
    segment_type: str = "behavioral"

class UpdateSegmentRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    criteria: Optional[Dict[str, Any]] = None
    segment_type: Optional[str] = None

class CustomerBehaviorRequest(BaseModel):
    customer_ids: List[str]
    behavior_metrics: List[str]
    timeframe: str = "30d"

class SegmentationStrategyRequest(BaseModel):
    business_goals: List[str]
    customer_data: Dict[str, Any]
    segmentation_method: str = "clustering"

class CustomerSegmentResponse(BaseModel):
    id: int
    name: str
    description: str
    criteria: Dict[str, Any]
    segment_type: str
    customer_count: int
    created_at: datetime
    updated_at: datetime

@router.post("/segments", response_model=CustomerSegmentResponse)
async def create_segment(
    request: CreateSegmentRequest,
    db: Session = Depends(get_db)
):
    service = CustomerSegmentationService(db)
    try:
        result = service.create_segment(request.name, request.description, request.criteria, request.segment_type)
        return CustomerSegmentResponse(
            id=result["id"],
            name=result["name"],
            description=result["description"],
            criteria=result["criteria"],
            segment_type=result["segment_type"],
            customer_count=result["customer_count"],
            created_at=result["created_at"],
            updated_at=result["updated_at"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/segments/{segment_id}", response_model=CustomerSegmentResponse)
async def get_segment(segment_id: int, db: Session = Depends(get_db)):
    service = CustomerSegmentationService(db)
    try:
        result = service.get_segment(segment_id)
        if not result:
            raise HTTPException(status_code=404, detail="Segment not found")
        return CustomerSegmentResponse(
            id=result["id"],
            name=result["name"],
            description=result["description"],
            criteria=result["criteria"],
            segment_type=result["segment_type"],
            customer_count=result["customer_count"],
            created_at=result["created_at"],
            updated_at=result["updated_at"]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/segments", response_model=List[CustomerSegmentResponse])
async def list_segments(
    segment_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    service = CustomerSegmentationService(db)
    try:
        results = service.list_segments(segment_type, limit, offset)
        return [
            CustomerSegmentResponse(
                id=result["id"],
                name=result["name"],
                description=result["description"],
                criteria=result["criteria"],
                segment_type=result["segment_type"],
                customer_count=result["customer_count"],
                created_at=result["created_at"],
                updated_at=result["updated_at"]
            )
            for result in results
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/segments/{segment_id}", response_model=CustomerSegmentResponse)
async def update_segment(
    segment_id: int,
    request: UpdateSegmentRequest,
    db: Session = Depends(get_db)
):
    service = CustomerSegmentationService(db)
    try:
        result = service.update_segment(segment_id, request.name, request.description, request.criteria, request.segment_type)
        if not result:
            raise HTTPException(status_code=404, detail="Segment not found")
        return CustomerSegmentResponse(
            id=result["id"],
            name=result["name"],
            description=result["description"],
            criteria=result["criteria"],
            segment_type=result["segment_type"],
            customer_count=result["customer_count"],
            created_at=result["created_at"],
            updated_at=result["updated_at"]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/segments/{segment_id}")
async def delete_segment(segment_id: int, db: Session = Depends(get_db)):
    service = CustomerSegmentationService(db)
    try:
        success = service.delete_segment(segment_id)
        if not success:
            raise HTTPException(status_code=404, detail="Segment not found")
        return {"message": "Segment deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze-behavior")
async def analyze_customer_behavior(
    request: CustomerBehaviorRequest,
    db: Session = Depends(get_db)
):
    service = CustomerSegmentationService(db)
    try:
        result = service.analyze_customer_behavior(request.customer_ids, request.behavior_metrics, request.timeframe)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create-strategy")
async def create_segmentation_strategy(
    request: SegmentationStrategyRequest,
    db: Session = Depends(get_db)
):
    service = CustomerSegmentationService(db)
    try:
        result = service.create_segmentation_strategy(request.business_goals, request.customer_data, request.segmentation_method)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/segments/{segment_id}/customers")
async def get_segment_customers(
    segment_id: int,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    service = CustomerSegmentationService(db)
    try:
        result = service.get_segment_customers(segment_id, limit, offset)
        if not result:
            raise HTTPException(status_code=404, detail="Segment not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/segments/{segment_id}/add-customers")
async def add_customers_to_segment(
    segment_id: int,
    customer_ids: List[str],
    db: Session = Depends(get_db)
):
    service = CustomerSegmentationService(db)
    try:
        result = service.add_customers_to_segment(segment_id, customer_ids)
        if not result:
            raise HTTPException(status_code=404, detail="Segment not found")
        return {"message": f"Added {len(customer_ids)} customers to segment"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/segments/{segment_id}/remove-customers")
async def remove_customers_from_segment(
    segment_id: int,
    customer_ids: List[str],
    db: Session = Depends(get_db)
):
    service = CustomerSegmentationService(db)
    try:
        result = service.remove_customers_from_segment(segment_id, customer_ids)
        if not result:
            raise HTTPException(status_code=404, detail="Segment not found")
        return {"message": f"Removed {len(customer_ids)} customers from segment"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/segments/{segment_id}/analytics")
async def get_segment_analytics(
    segment_id: int,
    db: Session = Depends(get_db)
):
    service = CustomerSegmentationService(db)
    try:
        result = service.get_segment_analytics(segment_id)
        if not result:
            raise HTTPException(status_code=404, detail="Segment not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/auto-segment")
async def auto_create_segments(
    customer_data: Dict[str, Any],
    segment_count: int = 5,
    db: Session = Depends(get_db)
):
    service = CustomerSegmentationService(db)
    try:
        result = service.auto_create_segments(customer_data, segment_count)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
