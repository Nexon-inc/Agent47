from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import logging

from ..services.tone_branding_service import ToneBrandingService, ToneProfile, BrandingProfile
from ..database import get_eric_database
from core.cache.redis_manager import RedisManager

router = APIRouter(prefix="/tone-branding", tags=["Tone & Branding"])
tone_branding_service = ToneBrandingService()
redis_manager = RedisManager()

logger = logging.getLogger(__name__)

# Request/Response Models
class ToneProfileCreate(BaseModel):
    name: str
    description: str
    tone_characteristics: Dict[str, Any]
    language_style: str
    formality_level: str
    personality_traits: List[str]
    industry_specific: bool
    target_audience: List[str]

class ToneProfileUpdate(BaseModel):
    name: str = None
    description: str = None
    tone_characteristics: Dict[str, Any] = None
    language_style: str = None
    formality_level: str = None
    personality_traits: List[str] = None
    industry_specific: bool = None
    target_audience: List[str] = None

class BrandingProfileCreate(BaseModel):
    name: str
    description: str
    brand_voice: str
    brand_values: List[str]
    color_scheme: Dict[str, str]
    logo_url: str = None
    tagline: str = None
    company_info: Dict[str, Any]

class BrandingProfileUpdate(BaseModel):
    name: str = None
    description: str = None
    brand_voice: str = None
    brand_values: List[str] = None
    color_scheme: Dict[str, str] = None
    logo_url: str = None
    tagline: str = None
    company_info: Dict[str, Any] = None

class ContentModificationRequest(BaseModel):
    content: str
    tone_profile_id: int
    branding_profile_id: int

class ContentModificationResponse(BaseModel):
    original_content: str
    modified_content: str
    tone_profile_id: int
    branding_profile_id: int
    modifications_applied: List[str]

# Tone Profile Endpoints
@router.post("/tone-profiles", response_model=ToneProfile, summary="Create Tone Profile")
async def create_tone_profile(tone_data: ToneProfileCreate):
    """Create a new tone profile for sales outreach"""
    try:
        tone_profile = ToneProfile(**tone_data.dict())
        created_profile = await tone_branding_service.create_tone_profile(tone_profile)
        return created_profile
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create tone profile: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/tone-profiles", response_model=List[ToneProfile], summary="Get All Tone Profiles")
async def get_tone_profiles():
    """Get all tone profiles"""
    try:
        # Try cache first
        cached_profiles = await redis_manager.get_cache("tone_profiles_list")
        if cached_profiles:
            return cached_profiles
        
        profiles = await tone_branding_service.get_tone_profiles()
        
        # Cache for 1 hour
        await redis_manager.set_cache(
            "tone_profiles_list",
            [profile.dict() for profile in profiles],
            expire=3600
        )
        
        return profiles
    except Exception as e:
        logger.error(f"Failed to get tone profiles: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/tone-profiles/{profile_id}", response_model=ToneProfile, summary="Get Tone Profile")
async def get_tone_profile(profile_id: int):
    """Get a specific tone profile by ID"""
    try:
        profiles = await tone_branding_service.get_tone_profiles()
        profile = next((p for p in profiles if p.id == profile_id), None)
        
        if not profile:
            raise HTTPException(status_code=404, detail="Tone profile not found")
        
        return profile
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get tone profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/tone-profiles/{profile_id}", response_model=ToneProfile, summary="Update Tone Profile")
async def update_tone_profile(profile_id: int, updates: ToneProfileUpdate):
    """Update an existing tone profile"""
    try:
        # Filter out None values
        update_data = {k: v for k, v in updates.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No valid updates provided")
        
        updated_profile = await tone_branding_service.update_tone_profile(profile_id, update_data)
        
        # Clear cache
        await redis_manager.delete_cache("tone_profiles_list")
        
        return updated_profile
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update tone profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/tone-profiles/{profile_id}", summary="Delete Tone Profile")
async def delete_tone_profile(profile_id: int):
    """Delete a tone profile"""
    try:
        success = await tone_branding_service.delete_tone_profile(profile_id)
        
        if success:
            # Clear cache
            await redis_manager.delete_cache("tone_profiles_list")
            return {"message": "Tone profile deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Tone profile not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to delete tone profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Branding Profile Endpoints
@router.post("/branding-profiles", response_model=BrandingProfile, summary="Create Branding Profile")
async def create_branding_profile(branding_data: BrandingProfileCreate):
    """Create a new branding profile for sales outreach"""
    try:
        branding_profile = BrandingProfile(**branding_data.dict())
        created_profile = await tone_branding_service.create_branding_profile(branding_profile)
        return created_profile
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create branding profile: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/branding-profiles", response_model=List[BrandingProfile], summary="Get All Branding Profiles")
async def get_branding_profiles():
    """Get all branding profiles"""
    try:
        # Try cache first
        cached_profiles = await redis_manager.get_cache("branding_profiles_list")
        if cached_profiles:
            return cached_profiles
        
        profiles = await tone_branding_service.get_branding_profiles()
        
        # Cache for 1 hour
        await redis_manager.set_cache(
            "branding_profiles_list",
            [profile.dict() for profile in profiles],
            expire=3600
        )
        
        return profiles
    except Exception as e:
        logger.error(f"Failed to get branding profiles: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/branding-profiles/{profile_id}", response_model=BrandingProfile, summary="Get Branding Profile")
async def get_branding_profile(profile_id: int):
    """Get a specific branding profile by ID"""
    try:
        profiles = await tone_branding_service.get_branding_profiles()
        profile = next((p for p in profiles if p.id == profile_id), None)
        
        if not profile:
            raise HTTPException(status_code=404, detail="Branding profile not found")
        
        return profile
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get branding profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/branding-profiles/{profile_id}", response_model=BrandingProfile, summary="Update Branding Profile")
async def update_branding_profile(profile_id: int, updates: BrandingProfileUpdate):
    """Update an existing branding profile"""
    try:
        # Filter out None values
        update_data = {k: v for k, v in updates.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No valid updates provided")
        
        updated_profile = await tone_branding_service.update_branding_profile(profile_id, update_data)
        
        # Clear cache
        await redis_manager.delete_cache("branding_profiles_list")
        
        return updated_profile
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update branding profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/branding-profiles/{profile_id}", summary="Delete Branding Profile")
async def delete_branding_profile(profile_id: int):
    """Delete a branding profile"""
    try:
        success = await tone_branding_service.delete_branding_profile(profile_id)
        
        if success:
            # Clear cache
            await redis_manager.delete_cache("branding_profiles_list")
            return {"message": "Branding profile deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Branding profile not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to delete branding profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Content Modification Endpoints
@router.post("/modify-content", response_model=ContentModificationResponse, summary="Apply Tone and Branding to Content")
async def modify_content(request: ContentModificationRequest):
    """Apply tone and branding profiles to content"""
    try:
        modified_content = await tone_branding_service.apply_tone_branding_to_content(
            request.content,
            request.tone_profile_id,
            request.branding_profile_id
        )
        
        # Determine what modifications were applied
        modifications = []
        if len(modified_content) != len(request.content):
            modifications.append("Content length changed")
        if modified_content != request.content:
            modifications.append("Tone and branding applied")
        
        return ContentModificationResponse(
            original_content=request.content,
            modified_content=modified_content,
            tone_profile_id=request.tone_profile_id,
            branding_profile_id=request.branding_profile_id,
            modifications_applied=modifications
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to modify content: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Analytics Endpoints
@router.get("/analytics", summary="Get Tone and Branding Analytics")
async def get_tone_branding_analytics():
    """Get analytics for tone and branding usage"""
    try:
        analytics = await tone_branding_service.get_tone_branding_analytics()
        return analytics
    except Exception as e:
        logger.error(f"Failed to get tone branding analytics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Utility Endpoints
@router.get("/tone-characteristics", summary="Get Available Tone Characteristics")
async def get_tone_characteristics():
    """Get available tone characteristics and their valid values"""
    return {
        "formality": ["low", "medium", "high"],
        "confidence": ["low", "medium", "high"],
        "empathy": ["low", "medium", "high"],
        "enthusiasm": ["low", "medium", "high"]
    }

@router.get("/language-styles", summary="Get Available Language Styles")
async def get_language_styles():
    """Get available language styles"""
    return {
        "styles": ["formal", "casual", "professional", "friendly", "authoritative", "conversational"]
    }

@router.get("/formality-levels", summary="Get Available Formality Levels")
async def get_formality_levels():
    """Get available formality levels"""
    return {
        "levels": ["low", "medium", "high"]
    }

@router.get("/target-audiences", summary="Get Common Target Audiences")
async def get_target_audiences():
    """Get common target audiences for tone profiles"""
    return {
        "audiences": [
            "enterprise",
            "small_business",
            "startups",
            "executives",
            "managers",
            "individuals",
            "technical",
            "non_technical"
        ]
    }
