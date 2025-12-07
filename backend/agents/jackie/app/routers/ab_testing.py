from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json

from ..database import get_db
from ..services.ab_testing_service import ABTestingService
from ..models import ABTest
from pydantic import BaseModel
from typing import Dict, Any

router = APIRouter(prefix="/ab-testing", tags=["A/B Testing"])

class CreateTestRequest(BaseModel):
    name: str
    description: str
    test_type: str
    variants: List[Dict[str, Any]]
    traffic_split: Dict[str, float]
    duration_days: int
    success_metrics: List[str]

class UpdateTestRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    traffic_split: Optional[Dict[str, float]] = None

class AddVariantRequest(BaseModel):
    variant_name: str
    variant_data: Dict[str, Any]
    traffic_percentage: float

class ABTestResponse(BaseModel):
    id: int
    name: str
    description: str
    test_type: str
    status: str
    variants: List[Dict[str, Any]]
    traffic_split: Dict[str, float]
    success_metrics: List[str]
    start_date: datetime
    end_date: datetime
    created_at: datetime

@router.post("/tests", response_model=ABTestResponse)
async def create_test(
    request: CreateTestRequest,
    db: Session = Depends(get_db)
):
    service = ABTestingService(db)
    try:
        result = service.create_test(
            request.name,
            request.description,
            request.test_type,
            request.variants,
            request.traffic_split,
            request.duration_days,
            request.success_metrics
        )
        return ABTestResponse(
            id=result["id"],
            name=result["name"],
            description=result["description"],
            test_type=result["test_type"],
            status=result["status"],
            variants=result["variants"],
            traffic_split=result["traffic_split"],
            success_metrics=result["success_metrics"],
            start_date=result["start_date"],
            end_date=result["end_date"],
            created_at=result["created_at"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tests/{test_id}", response_model=ABTestResponse)
async def get_test(test_id: int, db: Session = Depends(get_db)):
    service = ABTestingService(db)
    try:
        result = service.get_test(test_id)
        if not result:
            raise HTTPException(status_code=404, detail="Test not found")
        return ABTestResponse(
            id=result["id"],
            name=result["name"],
            description=result["description"],
            test_type=result["test_type"],
            status=result["status"],
            variants=result["variants"],
            traffic_split=result["traffic_split"],
            success_metrics=result["success_metrics"],
            start_date=result["start_date"],
            end_date=result["end_date"],
            created_at=result["created_at"]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tests", response_model=List[ABTestResponse])
async def list_tests(
    status: Optional[str] = None,
    test_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    service = ABTestingService(db)
    try:
        results = service.list_tests(status, test_type, limit, offset)
        return [
            ABTestResponse(
                id=result["id"],
                name=result["name"],
                description=result["description"],
                test_type=result["test_type"],
                status=result["status"],
                variants=result["variants"],
                traffic_split=result["traffic_split"],
                success_metrics=result["success_metrics"],
                start_date=result["start_date"],
                end_date=result["end_date"],
                created_at=result["created_at"]
            )
            for result in results
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/tests/{test_id}", response_model=ABTestResponse)
async def update_test(
    test_id: int,
    request: UpdateTestRequest,
    db: Session = Depends(get_db)
):
    service = ABTestingService(db)
    try:
        result = service.update_test(test_id, request.name, request.description, request.status, request.traffic_split)
        if not result:
            raise HTTPException(status_code=404, detail="Test not found")
        return ABTestResponse(
            id=result["id"],
            name=result["name"],
            description=result["description"],
            test_type=result["test_type"],
            status=result["status"],
            variants=result["variants"],
            traffic_split=result["traffic_split"],
            success_metrics=result["success_metrics"],
            start_date=result["start_date"],
            end_date=result["end_date"],
            created_at=result["created_at"]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/tests/{test_id}")
async def delete_test(test_id: int, db: Session = Depends(get_db)):
    service = ABTestingService(db)
    try:
        success = service.delete_test(test_id)
        if not success:
            raise HTTPException(status_code=404, detail="Test not found")
        return {"message": "Test deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tests/{test_id}/start")
async def start_test(test_id: int, db: Session = Depends(get_db)):
    service = ABTestingService(db)
    try:
        result = service.start_test(test_id)
        if not result:
            raise HTTPException(status_code=404, detail="Test not found")
        return {"message": "Test started successfully", "start_date": result["start_date"]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tests/{test_id}/stop")
async def stop_test(test_id: int, db: Session = Depends(get_db)):
    service = ABTestingService(db)
    try:
        result = service.stop_test(test_id)
        if not result:
            raise HTTPException(status_code=404, detail="Test not found")
        return {"message": "Test stopped successfully", "end_date": result["end_date"]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tests/{test_id}/variants")
async def add_variant(
    test_id: int,
    request: AddVariantRequest,
    db: Session = Depends(get_db)
):
    service = ABTestingService(db)
    try:
        result = service.add_variant(test_id, request.variant_name, request.variant_data, request.traffic_percentage)
        if not result:
            raise HTTPException(status_code=404, detail="Test not found")
        return {"message": "Variant added successfully", "variant": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/tests/{test_id}/variants/{variant_name}")
async def remove_variant(test_id: int, variant_name: str, db: Session = Depends(get_db)):
    service = ABTestingService(db)
    try:
        result = service.remove_variant(test_id, variant_name)
        if not result:
            raise HTTPException(status_code=404, detail="Test or variant not found")
        return {"message": "Variant removed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tests/{test_id}/results")
async def get_test_results(test_id: int, db: Session = Depends(get_db)):
    service = ABTestingService(db)
    try:
        result = service.get_test_results(test_id)
        if not result:
            raise HTTPException(status_code=404, detail="Test not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tests/{test_id}/track")
async def track_conversion(
    test_id: int,
    variant_name: str,
    conversion_type: str,
    user_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    service = ABTestingService(db)
    try:
        result = service.track_conversion(test_id, variant_name, conversion_type, user_id)
        if not result:
            raise HTTPException(status_code=404, detail="Test or variant not found")
        return {"message": "Conversion tracked successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tests/{test_id}/winner")
async def determine_winner(test_id: int, confidence_level: float = 0.95, db: Session = Depends(get_db)):
    service = ABTestingService(db)
    try:
        result = service.determine_winner(test_id, confidence_level)
        if not result:
            raise HTTPException(status_code=404, detail="Test not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tests/{test_id}/apply-winner")
async def apply_winner(test_id: int, db: Session = Depends(get_db)):
    service = ABTestingService(db)
    try:
        result = service.apply_winner(test_id)
        if not result:
            raise HTTPException(status_code=404, detail="Test not found")
        return {"message": "Winner applied successfully", "winner": result["winner"]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tests/{test_id}/statistical-significance")
async def check_statistical_significance(test_id: int, confidence_level: float = 0.95, db: Session = Depends(get_db)):
    service = ABTestingService(db)
    try:
        result = service.check_statistical_significance(test_id, confidence_level)
        if not result:
            raise HTTPException(status_code=404, detail="Test not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tests/{test_id}/sample-size-calculator")
async def calculate_sample_size(
    test_id: int,
    baseline_conversion_rate: float,
    minimum_detectable_effect: float,
    confidence_level: float = 0.95,
    power: float = 0.8,
    db: Session = Depends(get_db)
):
    service = ABTestingService(db)
    try:
        result = service.calculate_sample_size(test_id, baseline_conversion_rate, minimum_detectable_effect, confidence_level, power)
        if not result:
            raise HTTPException(status_code=404, detail="Test not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
