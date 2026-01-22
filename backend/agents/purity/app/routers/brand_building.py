from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import json

from ..database import get_purity_database
from ..models import PurityBusinessIdea, PurityBrandIdentity, PurityBusinessModel
from ..services.brand_building_service import BrandBuildingService

router = APIRouter(prefix="/brand-building", tags=["Brand Building"])

class BrandIdentityRequest(BaseModel):
    business_idea_id: int
    brand_name: str
    industry: str
    target_audience: str
    brand_personality: str
    brand_values: List[str]
    color_preferences: Optional[List[str]] = None
    style_preferences: Optional[str] = None

class BrandIdentityResponse(BaseModel):
    id: int
    business_idea_id: int
    brand_name: str
    industry: str
    target_audience: str
    brand_personality: str
    brand_values: List[str]
    brand_story: str
    brand_mission: str
    brand_vision: str
    brand_positioning: str
    created_at: datetime
    updated_at: datetime

class LogoGenerationRequest(BaseModel):
    brand_identity_id: int
    logo_style: str
    color_scheme: List[str]
    logo_type: str
    additional_requirements: Optional[str] = None

class LogoGenerationResponse(BaseModel):
    id: int
    brand_identity_id: int
    logo_concepts: List[dict]
    logo_files: List[str]
    color_palette: List[str]
    typography_suggestions: List[str]
    logo_guidelines: str
    created_at: datetime

class SloganDevelopmentRequest(BaseModel):
    brand_identity_id: int
    tone: str
    length_preference: str
    key_message: str
    target_emotion: str

class SloganDevelopmentResponse(BaseModel):
    id: int
    brand_identity_id: int
    slogan_options: List[str]
    tagline_variations: List[str]
    messaging_framework: dict
    brand_voice_guidelines: str
    created_at: datetime

class StyleGuideRequest(BaseModel):
    brand_identity_id: int
    include_logo_usage: bool = True
    include_color_palette: bool = True
    include_typography: bool = True
    include_imagery: bool = True
    include_voice_tone: bool = True

class StyleGuideResponse(BaseModel):
    id: int
    brand_identity_id: int
    logo_usage_guidelines: dict
    color_palette: dict
    typography_guide: dict
    imagery_guidelines: dict
    voice_tone_guide: dict
    brand_guidelines_document: str
    created_at: datetime

@router.post("/identity", response_model=BrandIdentityResponse)
async def create_brand_identity(
    request: BrandIdentityRequest,
    db: AsyncSession = Depends(get_purity_database)
):
    try:
        service = BrandBuildingService()
        brand_identity = await service.create_brand_identity(
            db=db,
            business_idea_id=request.business_idea_id,
            brand_name=request.brand_name,
            industry=request.industry,
            target_audience=request.target_audience,
            brand_personality=request.brand_personality,
            brand_values=request.brand_values,
            color_preferences=request.color_preferences,
            style_preferences=request.style_preferences
        )
        return BrandIdentityResponse(
            id=brand_identity.id,
            business_idea_id=brand_identity.business_idea_id,
            brand_name=brand_identity.brand_name,
            industry=brand_identity.industry,
            target_audience=brand_identity.target_audience,
            brand_personality=brand_identity.brand_personality,
            brand_values=json.loads(brand_identity.brand_values),
            brand_story=brand_identity.brand_story,
            brand_mission=brand_identity.brand_mission,
            brand_vision=brand_identity.brand_vision,
            brand_positioning=brand_identity.brand_positioning,
            created_at=brand_identity.created_at,
            updated_at=brand_identity.updated_at
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/logo", response_model=LogoGenerationResponse)
async def generate_logo_concepts(
    request: LogoGenerationRequest,
    db: AsyncSession = Depends(get_purity_database)
):
    try:
        service = BrandBuildingService()
        logo_concepts = await service.generate_logo_concepts(
            db=db,
            brand_identity_id=request.brand_identity_id,
            logo_style=request.logo_style,
            color_scheme=request.color_scheme,
            logo_type=request.logo_type,
            additional_requirements=request.additional_requirements
        )
        return LogoGenerationResponse(
            id=logo_concepts.id,
            brand_identity_id=logo_concepts.brand_identity_id,
            logo_concepts=json.loads(logo_concepts.logo_concepts),
            logo_files=json.loads(logo_concepts.logo_files),
            color_palette=json.loads(logo_concepts.color_palette),
            typography_suggestions=json.loads(logo_concepts.typography_suggestions),
            logo_guidelines=logo_concepts.logo_guidelines,
            created_at=logo_concepts.created_at
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/slogan", response_model=SloganDevelopmentResponse)
async def develop_brand_slogan(
    request: SloganDevelopmentRequest,
    db: AsyncSession = Depends(get_purity_database)
):
    try:
        service = BrandBuildingService()
        slogan_options = await service.develop_brand_slogan(
            db=db,
            brand_identity_id=request.brand_identity_id,
            tone=request.tone,
            length_preference=request.length_preference,
            key_message=request.key_message,
            target_emotion=request.target_emotion
        )
        return SloganDevelopmentResponse(
            id=slogan_options.id,
            brand_identity_id=slogan_options.brand_identity_id,
            slogan_options=json.loads(slogan_options.slogan_options),
            tagline_variations=json.loads(slogan_options.tagline_variations),
            messaging_framework=json.loads(slogan_options.messaging_framework),
            brand_voice_guidelines=slogan_options.brand_voice_guidelines,
            created_at=slogan_options.created_at
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/style-guide", response_model=StyleGuideResponse)
async def create_style_guide(
    request: StyleGuideRequest,
    db: AsyncSession = Depends(get_purity_database)
):
    try:
        service = BrandBuildingService()
        style_guide = await service.create_style_guide(
            db=db,
            brand_identity_id=request.brand_identity_id,
            include_logo_usage=request.include_logo_usage,
            include_color_palette=request.include_color_palette,
            include_typography=request.include_typography,
            include_imagery=request.include_imagery,
            include_voice_tone=request.include_voice_tone
        )
        return StyleGuideResponse(
            id=style_guide.id,
            brand_identity_id=style_guide.brand_identity_id,
            logo_usage_guidelines=json.loads(style_guide.logo_usage_guidelines),
            color_palette=json.loads(style_guide.color_palette),
            typography_guide=json.loads(style_guide.typography_guide),
            imagery_guidelines=json.loads(style_guide.imagery_guidelines),
            voice_tone_guide=json.loads(style_guide.voice_tone_guide),
            brand_guidelines_document=style_guide.brand_guidelines_document,
            created_at=style_guide.created_at
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/identity/{identity_id}", response_model=BrandIdentityResponse)
async def get_brand_identity(
    identity_id: int,
    db: AsyncSession = Depends(get_purity_database)
):
    try:
        result = await db.execute(select(PurityBrandIdentity).where(PurityBrandIdentity.id == identity_id))
        brand_identity = result.scalar_one_or_none()
        if not brand_identity:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand identity not found")
        return BrandIdentityResponse(
            id=brand_identity.id,
            business_idea_id=brand_identity.business_idea_id,
            brand_name=brand_identity.brand_name,
            industry=brand_identity.industry,
            target_audience=brand_identity.target_audience,
            brand_personality=brand_identity.brand_personality,
            brand_values=json.loads(brand_identity.brand_values),
            brand_story=brand_identity.brand_story,
            brand_mission=brand_identity.brand_mission,
            brand_vision=brand_identity.brand_vision,
            brand_positioning=brand_identity.brand_positioning,
            created_at=brand_identity.created_at,
            updated_at=brand_identity.updated_at
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/identity/business/{business_idea_id}", response_model=List[BrandIdentityResponse])
async def get_business_brand_identities(
    business_idea_id: int,
    db: AsyncSession = Depends(get_purity_database)
):
    try:
        result = await db.execute(select(PurityBrandIdentity).where(PurityBrandIdentity.business_idea_id == business_idea_id))
        brand_identities = result.scalars().all()
        return [
            BrandIdentityResponse(
                id=brand_identity.id,
                business_idea_id=brand_identity.business_idea_id,
                brand_name=brand_identity.brand_name,
                industry=brand_identity.industry,
                target_audience=brand_identity.target_audience,
                brand_personality=brand_identity.brand_personality,
                brand_values=json.loads(brand_identity.brand_values),
                brand_story=brand_identity.brand_story,
                brand_mission=brand_identity.brand_mission,
                brand_vision=brand_identity.brand_vision,
                brand_positioning=brand_identity.brand_positioning,
                created_at=brand_identity.created_at,
                updated_at=brand_identity.updated_at
            )
            for brand_identity in brand_identities
        ]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.put("/identity/{identity_id}", response_model=BrandIdentityResponse)
async def update_brand_identity(
    identity_id: int,
    request: BrandIdentityRequest,
    db: AsyncSession = Depends(get_purity_database)
):
    try:
        result = await db.execute(select(PurityBrandIdentity).where(PurityBrandIdentity.id == identity_id))
        brand_identity = result.scalar_one_or_none()
        if not brand_identity:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand identity not found")
        
        service = BrandBuildingService()
        updated_identity = await service.update_brand_identity(
            db=db,
            identity_id=identity_id,
            brand_name=request.brand_name,
            industry=request.industry,
            target_audience=request.target_audience,
            brand_personality=request.brand_personality,
            brand_values=request.brand_values,
            color_preferences=request.color_preferences,
            style_preferences=request.style_preferences
        )
        return BrandIdentityResponse(
            id=updated_identity.id,
            business_idea_id=updated_identity.business_idea_id,
            brand_name=updated_identity.brand_name,
            industry=updated_identity.industry,
            target_audience=updated_identity.target_audience,
            brand_personality=updated_identity.brand_personality,
            brand_values=json.loads(updated_identity.brand_values),
            brand_story=updated_identity.brand_story,
            brand_mission=updated_identity.brand_mission,
            brand_vision=updated_identity.brand_vision,
            brand_positioning=updated_identity.brand_positioning,
            created_at=updated_identity.created_at,
            updated_at=updated_identity.updated_at
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.delete("/identity/{identity_id}")
async def delete_brand_identity(
    identity_id: int,
    db: AsyncSession = Depends(get_purity_database)
):
    try:
        result = await db.execute(select(PurityBrandIdentity).where(PurityBrandIdentity.id == identity_id))
        brand_identity = result.scalar_one_or_none()
        if not brand_identity:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand identity not found")
        await db.delete(brand_identity)
        await db.commit()
        return {"message": "Brand identity deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/logo/{logo_id}", response_model=LogoGenerationResponse)
async def get_logo_concepts(
    logo_id: int,
    db: AsyncSession = Depends(get_purity_database)
):
    try:
        result = await db.execute(select(PurityBrandIdentity).where(PurityBrandIdentity.id == logo_id))
        logo_concepts = result.scalar_one_or_none()
        if not logo_concepts:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Logo concepts not found")
        return LogoGenerationResponse(
            id=logo_concepts.id,
            brand_identity_id=logo_concepts.brand_identity_id,
            logo_concepts=json.loads(logo_concepts.logo_concepts),
            logo_files=json.loads(logo_concepts.logo_files),
            color_palette=json.loads(logo_concepts.color_palette),
            typography_suggestions=json.loads(logo_concepts.typography_suggestions),
            logo_guidelines=logo_concepts.logo_guidelines,
            created_at=logo_concepts.created_at
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/slogan/{slogan_id}", response_model=SloganDevelopmentResponse)
async def get_brand_slogan(
    slogan_id: int,
    db: AsyncSession = Depends(get_purity_database)
):
    try:
        result = await db.execute(select(PurityBrandIdentity).where(PurityBrandIdentity.id == slogan_id))
        slogan_options = result.scalar_one_or_none()
        if not slogan_options:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand slogan not found")
        return SloganDevelopmentResponse(
            id=slogan_options.id,
            brand_identity_id=slogan_options.brand_identity_id,
            slogan_options=json.loads(slogan_options.slogan_options),
            tagline_variations=json.loads(slogan_options.tagline_variations),
            messaging_framework=json.loads(slogan_options.messaging_framework),
            brand_voice_guidelines=slogan_options.brand_voice_guidelines,
            created_at=slogan_options.created_at
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/style-guide/{guide_id}", response_model=StyleGuideResponse)
async def get_style_guide(
    guide_id: int,
    db: AsyncSession = Depends(get_purity_database)
):
    try:
        result = await db.execute(select(PurityBrandIdentity).where(PurityBrandIdentity.id == guide_id))
        style_guide = result.scalar_one_or_none()
        if not style_guide:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Style guide not found")
        return StyleGuideResponse(
            id=style_guide.id,
            brand_identity_id=style_guide.brand_identity_id,
            logo_usage_guidelines=json.loads(style_guide.logo_usage_guidelines),
            color_palette=json.loads(style_guide.color_palette),
            typography_guide=json.loads(style_guide.typography_guide),
            imagery_guidelines=json.loads(style_guide.imagery_guidelines),
            voice_tone_guide=json.loads(style_guide.voice_tone_guide),
            brand_guidelines_document=style_guide.brand_guidelines_document,
            created_at=style_guide.created_at
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
