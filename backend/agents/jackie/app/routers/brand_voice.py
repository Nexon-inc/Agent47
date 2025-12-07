from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import json

from ..database import get_db
from ..services.brand_voice_service import BrandVoiceService

router = APIRouter(prefix="/brand-voice", tags=["Brand Voice Customization"])
from pydantic import BaseModel


class CreateBrandVoiceRequest(BaseModel):
    name: str
    description: Optional[str] = None
    tone: str
    style_guide: Dict[str, Any]
    sample_texts: List[str]
    target_audience: List[str]


class UpdateBrandVoiceRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    tone: Optional[str] = None
    style_guide: Optional[Dict[str, Any]] = None
    sample_texts: Optional[List[str]] = None
    target_audience: Optional[List[str]] = None


class GenerateContentRequest(BaseModel):
    content_type: str
    topic: str
    brand_voice_id: str
    length: str = "medium"
    additional_context: Optional[Dict[str, Any]] = None


class BrandVoiceResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    tone: str
    style_guide: Dict[str, Any]
    sample_texts: List[str]
    target_audience: List[str]
    created_at: datetime

@router.post("/create", response_model=BrandVoiceResponse)
async def create_brand_voice(
    request: CreateBrandVoiceRequest,
    db: Session = Depends(get_db)
):
    service = BrandVoiceService(db)
    try:
        result = service.create_brand_voice(
            request.name,
            request.description,
            request.tone,
            request.style_guide,
            request.sample_texts,
            request.target_audience
        )
        return BrandVoiceResponse(
            id=result["id"],
            name=result["name"],
            description=result["description"],
            tone=result["tone"],
            style_guide=result["style_guide"],
            sample_texts=result["sample_texts"],
            target_audience=result["target_audience"],
            created_at=result["created_at"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{brand_voice_id}", response_model=BrandVoiceResponse)
async def get_brand_voice(brand_voice_id: str, db: Session = Depends(get_db)):
    service = BrandVoiceService(db)
    try:
        result = service.get_brand_voice(brand_voice_id)
        if not result:
            raise HTTPException(status_code=404, detail="Brand voice not found")
        return BrandVoiceResponse(
            id=result["id"],
            name=result["name"],
            description=result["description"],
            tone=result["tone"],
            style_guide=result["style_guide"],
            sample_texts=result["sample_texts"],
            target_audience=result["target_audience"],
            created_at=result["created_at"]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[BrandVoiceResponse])
async def list_brand_voices(
    tone: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    service = BrandVoiceService(db)
    try:
        results = service.list_brand_voices(tone, limit, offset)
        return [
            BrandVoiceResponse(
                id=result["id"],
                name=result["name"],
                description=result["description"],
                tone=result["tone"],
                style_guide=result["style_guide"],
                sample_texts=result["sample_texts"],
                target_audience=result["target_audience"],
                created_at=result["created_at"]
            )
            for result in results
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{brand_voice_id}")
async def update_brand_voice(
    brand_voice_id: str,
    request: UpdateBrandVoiceRequest,
    db: Session = Depends(get_db)
):
    service = BrandVoiceService(db)
    try:
        result = service.update_brand_voice(
            brand_voice_id,
            request.name,
            request.description,
            request.tone,
            request.style_guide,
            request.sample_texts,
            request.target_audience
        )
        if not result:
            raise HTTPException(status_code=404, detail="Brand voice not found")
        return {"message": "Brand voice updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{brand_voice_id}")
async def delete_brand_voice(brand_voice_id: str, db: Session = Depends(get_db)):
    service = BrandVoiceService(db)
    try:
        result = service.delete_brand_voice(brand_voice_id)
        if not result:
            raise HTTPException(status_code=404, detail="Brand voice not found")
        return {"message": "Brand voice deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-content")
async def generate_content_with_brand_voice(
    request: GenerateContentRequest,
    db: Session = Depends(get_db)
):
    service = BrandVoiceService(db)
    try:
        result = service.generate_content_with_brand_voice(
            request.content_type,
            request.topic,
            request.brand_voice_id,
            request.length,
            request.additional_context
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze-tone")
async def analyze_content_tone(
    content: str,
    target_tone: Optional[str] = None,
    db: Session = Depends(get_db)
):
    service = BrandVoiceService(db)
    try:
        result = service.analyze_content_tone(content, target_tone)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/optimize-content")
async def optimize_content_for_brand_voice(
    content: str,
    brand_voice_id: str,
    optimization_type: str = "tone",
    db: Session = Depends(get_db)
):
    service = BrandVoiceService(db)
    try:
        result = service.optimize_content_for_brand_voice(content, brand_voice_id, optimization_type)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tones/available")
async def get_available_tones(db: Session = Depends(get_db)):
    service = BrandVoiceService(db)
    try:
        tones = service.get_available_tones()
        return {"tones": tones}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tones/create-custom")
async def create_custom_tone(
    tone_name: str,
    tone_characteristics: Dict[str, Any],
    sample_content: List[str],
    db: Session = Depends(get_db)
):
    service = BrandVoiceService(db)
    try:
        result = service.create_custom_tone(tone_name, tone_characteristics, sample_content)
        return {
            "message": "Custom tone created successfully",
            "tone_id": result["tone_id"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tones/{tone_name}/characteristics")
async def get_tone_characteristics(tone_name: str, db: Session = Depends(get_db)):
    service = BrandVoiceService(db)
    try:
        characteristics = service.get_tone_characteristics(tone_name)
        if not characteristics:
            raise HTTPException(status_code=404, detail="Tone not found")
        return characteristics
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/style-guide/generate")
async def generate_style_guide(
    brand_description: str,
    industry: str,
    target_audience: List[str],
    tone_preferences: Dict[str, Any],
    db: Session = Depends(get_db)
):
    service = BrandVoiceService(db)
    try:
        result = service.generate_style_guide(brand_description, industry, target_audience, tone_preferences)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/consistency/check")
async def check_brand_voice_consistency(
    content_pieces: List[str],
    brand_voice_id: str,
    db: Session = Depends(get_db)
):
    service = BrandVoiceService(db)
    try:
        result = service.check_brand_voice_consistency(content_pieces, brand_voice_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/training/improve")
async def improve_brand_voice(
    brand_voice_id: str,
    feedback_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    service = BrandVoiceService(db)
    try:
        result = service.improve_brand_voice(brand_voice_id, feedback_data)
        return {
            "message": "Brand voice improved successfully",
            "improvements": result["improvements"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/usage")
async def get_brand_voice_usage_analytics(
    brand_voice_id: Optional[str] = None,
    timeframe: str = "30d",
    db: Session = Depends(get_db)
):
    service = BrandVoiceService(db)
    try:
        analytics = service.get_brand_voice_usage_analytics(brand_voice_id, timeframe)
        return analytics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/performance")
async def get_brand_voice_performance(
    brand_voice_id: str,
    metrics: List[str],
    timeframe: str = "30d",
    db: Session = Depends(get_db)
):
    service = BrandVoiceService(db)
    try:
        performance = service.get_brand_voice_performance(brand_voice_id, metrics, timeframe)
        return performance
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/templates/create")
async def create_brand_voice_template(
    template_name: str,
    template_data: Dict[str, Any],
    brand_voice_id: str,
    db: Session = Depends(get_db)
):
    service = BrandVoiceService(db)
    try:
        result = service.create_brand_voice_template(template_name, template_data, brand_voice_id)
        return {
            "message": "Brand voice template created successfully",
            "template_id": result["template_id"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/templates")
async def list_brand_voice_templates(
    brand_voice_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    service = BrandVoiceService(db)
    try:
        templates = service.list_brand_voice_templates(brand_voice_id, limit, offset)
        return {"templates": templates}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/localization/adapt")
async def adapt_brand_voice_for_locale(
    brand_voice_id: str,
    target_locale: str,
    cultural_context: Dict[str, Any],
    db: Session = Depends(get_db)
):
    service = BrandVoiceService(db)
    try:
        result = service.adapt_brand_voice_for_locale(brand_voice_id, target_locale, cultural_context)
        return {
            "message": "Brand voice adapted for locale successfully",
            "adapted_voice_id": result["adapted_voice_id"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/locales/supported")
async def get_supported_locales(db: Session = Depends(get_db)):
    service = BrandVoiceService(db)
    try:
        locales = service.get_supported_locales()
        return {"locales": locales}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/validation/check")
async def validate_brand_voice(
    brand_voice_id: str,
    validation_criteria: Dict[str, Any],
    db: Session = Depends(get_db)
):
    service = BrandVoiceService(db)
    try:
        result = service.validate_brand_voice(brand_voice_id, validation_criteria)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/recommendations")
async def get_brand_voice_recommendations(
    industry: Optional[str] = None,
    target_audience: Optional[List[str]] = None,
    content_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    service = BrandVoiceService(db)
    try:
        recommendations = service.get_brand_voice_recommendations(industry, target_audience, content_type)
        return {"recommendations": recommendations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
