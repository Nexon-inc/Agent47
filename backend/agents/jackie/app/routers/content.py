from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from ..services.content_service import ContentService
from ..models import ContentType, PlatformType
from ..database import get_jackie_database

router = APIRouter()

class GenerateContentRequest(BaseModel):
    user_id: int
    content_type: ContentType
    platform: PlatformType
    topic: str
    brand_voice_id: Optional[int] = None
    target_audience: Optional[Dict[str, Any]] = None
    keywords: Optional[List[str]] = None
    tone: Optional[str] = None
    length: Optional[str] = None
    call_to_action: Optional[str] = None

class CreateAdCopyRequest(BaseModel):
    user_id: int
    platform: PlatformType
    product_name: str
    product_description: str
    target_audience: Dict[str, Any]
    ad_type: str
    budget: float
    brand_voice_id: Optional[int] = None
    keywords: Optional[List[str]] = None

class CreateSocialPostRequest(BaseModel):
    user_id: int
    platform: PlatformType
    topic: str
    content_type: ContentType
    hashtags: Optional[List[str]] = None
    brand_voice_id: Optional[int] = None
    target_audience: Optional[Dict[str, Any]] = None
    call_to_action: Optional[str] = None

class CreateEmailTemplateRequest(BaseModel):
    user_id: int
    email_type: str
    subject_line: str
    target_audience: Dict[str, Any]
    brand_voice_id: Optional[int] = None
    personalization_fields: Optional[List[str]] = None
    call_to_action: Optional[str] = None

class ContentResponse(BaseModel):
    id: int
    content_type: str
    platform: str
    title: Optional[str]
    content: str
    media_urls: List[str]
    hashtags: List[str]
    ai_generated: bool
    brand_voice_applied: bool
    created_at: str

async def get_content_service() -> ContentService:
    service = ContentService()
    await service.initialize()
    return service

@router.post("/generate", response_model=Dict[str, Any])
async def generate_content(
    request: GenerateContentRequest,
    service: ContentService = Depends(get_content_service)
):
    try:
        result = await service.generate_content(
            user_id=request.user_id,
            content_type=request.content_type,
            platform=request.platform,
            topic=request.topic,
            brand_voice_id=request.brand_voice_id,
            target_audience=request.target_audience,
            keywords=request.keywords,
            tone=request.tone,
            length=request.length,
            call_to_action=request.call_to_action
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/copywriting", response_model=Dict[str, Any])
async def create_ad_copy(
    request: CreateAdCopyRequest,
    service: ContentService = Depends(get_content_service)
):
    try:
        result = await service.create_ad_copy(
            user_id=request.user_id,
            platform=request.platform,
            product_name=request.product_name,
            product_description=request.product_description,
            target_audience=request.target_audience,
            ad_type=request.ad_type,
            budget=request.budget,
            brand_voice_id=request.brand_voice_id,
            keywords=request.keywords
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/social-posts", response_model=Dict[str, Any])
async def create_social_post(
    request: CreateSocialPostRequest,
    service: ContentService = Depends(get_content_service)
):
    try:
        result = await service.create_social_post(
            user_id=request.user_id,
            platform=request.platform,
            topic=request.topic,
            content_type=request.content_type,
            hashtags=request.hashtags,
            brand_voice_id=request.brand_voice_id,
            target_audience=request.target_audience,
            call_to_action=request.call_to_action
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/email-templates", response_model=Dict[str, Any])
async def create_email_template(
    request: CreateEmailTemplateRequest,
    service: ContentService = Depends(get_content_service)
):
    try:
        result = await service.create_email_template(
            user_id=request.user_id,
            email_type=request.email_type,
            subject_line=request.subject_line,
            target_audience=request.target_audience,
            brand_voice_id=request.brand_voice_id,
            personalization_fields=request.personalization_fields,
            call_to_action=request.call_to_action
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{content_id}", response_model=Dict[str, Any])
async def get_content(
    content_id: int,
    service: ContentService = Depends(get_content_service)
):
    try:
        result = await service.get_content_details(content_id)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=404, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{content_id}", response_model=Dict[str, Any])
async def update_content(
    content_id: int,
    content: str = Body(...),
    title: Optional[str] = Body(None),
    hashtags: Optional[List[str]] = Body(None),
    service: ContentService = Depends(get_content_service)
):
    try:
        result = await service.update_content(
            content_id=content_id,
            content=content,
            title=title,
            hashtags=hashtags
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{content_id}", response_model=Dict[str, Any])
async def delete_content(
    content_id: int,
    service: ContentService = Depends(get_content_service)
):
    try:
        result = await service.delete_content(content_id)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=Dict[str, Any])
async def list_content(
    user_id: int = Query(...),
    content_type: Optional[ContentType] = Query(None),
    platform: Optional[PlatformType] = Query(None),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: ContentService = Depends(get_content_service)
):
    try:
        result = await service.list_content(
            user_id=user_id,
            content_type=content_type,
            platform=platform,
            limit=limit,
            offset=offset
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{content_id}/optimize", response_model=Dict[str, Any])
async def optimize_content(
    content_id: int,
    optimization_type: str = Body(...),
    service: ContentService = Depends(get_content_service)
):
    try:
        result = await service.optimize_content(content_id, optimization_type)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{content_id}/translate", response_model=Dict[str, Any])
async def translate_content(
    content_id: int,
    target_language: str = Body(...),
    service: ContentService = Depends(get_content_service)
):
    try:
        result = await service.translate_content(content_id, target_language)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{content_id}/schedule", response_model=Dict[str, Any])
async def schedule_content(
    content_id: int,
    scheduled_time: str = Body(...),
    platform: PlatformType = Body(...),
    service: ContentService = Depends(get_content_service)
):
    try:
        result = await service.schedule_content(
            content_id=content_id,
            scheduled_time=scheduled_time,
            platform=platform
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/bulk-generate", response_model=Dict[str, Any])
async def bulk_generate_content(
    user_id: int = Body(...),
    content_briefs: List[Dict[str, Any]] = Body(...),
    service: ContentService = Depends(get_content_service)
):
    try:
        result = await service.bulk_generate_content(user_id, content_briefs)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
