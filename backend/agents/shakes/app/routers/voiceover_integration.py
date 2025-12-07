from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
from ..services.voiceover_integration_service import VoiceoverIntegrationService
from ..models import ContentType, PlatformType, ToneType
from ..database import get_shakes_database

router = APIRouter(prefix="/voiceover-integration", tags=["Voiceover Integration"])

# Pydantic Models
class GenerateVoiceoverRequest(BaseModel):
    content_piece_id: int = Field(..., description="Content piece ID")
    voice_characteristics: Dict[str, Any] = Field(..., description="Voice characteristics")
    audio_settings: Dict[str, Any] = Field(..., description="Audio settings")

class GenerateMultilingualVoiceoverRequest(BaseModel):
    content_piece_id: int = Field(..., description="Content piece ID")
    target_languages: List[str] = Field(..., description="Target languages")
    voice_characteristics: Dict[str, Any] = Field(..., description="Voice characteristics")
    translation_style: str = Field(default="natural", description="Translation style")

class CustomizeVoiceCharacteristicsRequest(BaseModel):
    base_voice: str = Field(..., description="Base voice")
    customization_parameters: Dict[str, Any] = Field(..., description="Customization parameters")
    target_audience: str = Field(..., description="Target audience")

class GenerateVoiceoverScriptRequest(BaseModel):
    content_piece_id: int = Field(..., description="Content piece ID")
    script_style: str = Field(..., description="Script style")
    target_duration: int = Field(default=60, description="Target duration in seconds")

# Dependency
async def get_voiceover_integration_service() -> VoiceoverIntegrationService:
    """Get voiceover integration service instance"""
    service = VoiceoverIntegrationService()
    await service.initialize()
    return service

# Endpoints
@router.post("/generate", response_model=Dict[str, Any], status_code=200)
async def generate_voiceover(
    request: GenerateVoiceoverRequest,
    service: VoiceoverIntegrationService = Depends(get_voiceover_integration_service)
):
    """Generate AI voiceover for content"""
    try:
        result = await service.generate_voiceover(
            content_piece_id=request.content_piece_id,
            voice_characteristics=request.voice_characteristics,
            audio_settings=request.audio_settings
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to generate voiceover")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Voiceover generation failed: {str(e)}"
        )

@router.post("/multilingual", response_model=Dict[str, Any], status_code=200)
async def generate_multilingual_voiceover(
    request: GenerateMultilingualVoiceoverRequest,
    service: VoiceoverIntegrationService = Depends(get_voiceover_integration_service)
):
    """Generate voiceover in multiple languages"""
    try:
        result = await service.generate_multilingual_voiceover(
            content_piece_id=request.content_piece_id,
            target_languages=request.target_languages,
            voice_characteristics=request.voice_characteristics,
            translation_style=request.translation_style
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to generate multilingual voiceover")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Multilingual voiceover generation failed: {str(e)}"
        )

@router.post("/customize-voice", response_model=Dict[str, Any], status_code=200)
async def customize_voice_characteristics(
    request: CustomizeVoiceCharacteristicsRequest,
    service: VoiceoverIntegrationService = Depends(get_voiceover_integration_service)
):
    """Customize voice characteristics for specific audience"""
    try:
        result = await service.customize_voice_characteristics(
            base_voice=request.base_voice,
            customization_parameters=request.customization_parameters,
            target_audience=request.target_audience
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to customize voice characteristics")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Voice customization failed: {str(e)}"
        )

@router.post("/generate-script", response_model=Dict[str, Any], status_code=200)
async def generate_voiceover_script(
    request: GenerateVoiceoverScriptRequest,
    service: VoiceoverIntegrationService = Depends(get_voiceover_integration_service)
):
    """Generate optimized voiceover script"""
    try:
        result = await service.generate_voiceover_script(
            content_piece_id=request.content_piece_id,
            script_style=request.script_style,
            target_duration=request.target_duration
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to generate voiceover script")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Voiceover script generation failed: {str(e)}"
        )

@router.get("/voice-characteristics")
async def get_voice_characteristics():
    """Get available voice characteristics for voiceover generation"""
    return {
        "voice_characteristics": [
            {
                "id": "gender",
                "name": "Gender",
                "description": "Voice gender selection",
                "options": ["male", "female", "neutral"],
                "impact": "affects_audience_perception_and_engagement"
            },
            {
                "id": "age",
                "name": "Age",
                "description": "Voice age range",
                "options": ["young", "adult", "mature", "senior"],
                "impact": "influences_credibility_and_audience_connection"
            },
            {
                "id": "accent",
                "name": "Accent",
                "description": "Regional accent or pronunciation",
                "options": ["american", "british", "australian", "neutral"],
                "impact": "affects_cultural_relevance_and_audience_preference"
            },
            {
                "id": "tone",
                "name": "Tone",
                "description": "Emotional tone and delivery style",
                "options": ["professional", "friendly", "authoritative", "casual"],
                "impact": "influences_message_perception_and_engagement"
            },
            {
                "id": "pace",
                "name": "Pace",
                "description": "Speaking speed and rhythm",
                "options": ["slow", "moderate", "fast", "variable"],
                "impact": "affects_comprehension_and_engagement"
            },
            {
                "id": "pitch",
                "name": "Pitch",
                "description": "Voice pitch and frequency",
                "options": ["low", "medium", "high", "variable"],
                "impact": "influences_authority_and_audience_attention"
            }
        ]
    }

@router.get("/audio-settings")
async def get_audio_settings():
    """Get available audio settings for voiceover generation"""
    return {
        "audio_settings": [
            {
                "id": "quality",
                "name": "Audio Quality",
                "description": "Audio quality and bitrate",
                "options": ["standard", "high", "premium"],
                "impact": "affects_file_size_and_audio_quality"
            },
            {
                "id": "format",
                "name": "Audio Format",
                "description": "Audio file format",
                "options": ["mp3", "wav", "aac", "ogg"],
                "impact": "affects_compatibility_and_file_size"
            },
            {
                "id": "sample_rate",
                "name": "Sample Rate",
                "description": "Audio sample rate",
                "options": ["22050", "44100", "48000"],
                "impact": "affects_audio_quality_and_file_size"
            },
            {
                "id": "bitrate",
                "name": "Bitrate",
                "description": "Audio bitrate",
                "options": ["128", "192", "256", "320"],
                "impact": "affects_audio_quality_and_file_size"
            },
            {
                "id": "noise_reduction",
                "name": "Noise Reduction",
                "description": "Background noise reduction",
                "options": ["none", "light", "moderate", "heavy"],
                "impact": "affects_audio_cleanliness_and_naturalness"
            }
        ]
    }

@router.get("/script-styles")
async def get_script_styles():
    """Get available script styles for voiceover generation"""
    return {
        "script_styles": [
            {
                "id": "conversational",
                "name": "Conversational",
                "description": "Natural, conversational delivery style",
                "characteristics": ["natural_pauses", "informal_tone", "engaging_delivery"],
                "best_for": ["podcasts", "casual_content", "social_media"]
            },
            {
                "id": "professional",
                "name": "Professional",
                "description": "Formal, professional delivery style",
                "characteristics": ["clear_pronunciation", "formal_tone", "authoritative_delivery"],
                "best_for": ["corporate_content", "presentations", "educational_material"]
            },
            {
                "id": "dramatic",
                "name": "Dramatic",
                "description": "Expressive, dramatic delivery style",
                "characteristics": ["emotional_expression", "varied_pace", "engaging_delivery"],
                "best_for": ["storytelling", "entertainment", "creative_content"]
            },
            {
                "id": "instructional",
                "name": "Instructional",
                "description": "Clear, instructional delivery style",
                "characteristics": ["clear_pronunciation", "steady_pace", "educational_tone"],
                "best_for": ["tutorials", "how_to_content", "educational_material"]
            }
        ]
    }

@router.get("/supported-languages")
async def get_supported_languages():
    """Get supported languages for multilingual voiceover"""
    return {
        "supported_languages": [
            {
                "id": "en",
                "name": "English",
                "description": "English language support",
                "variants": ["us", "uk", "au", "ca"],
                "quality": "high"
            },
            {
                "id": "es",
                "name": "Spanish",
                "description": "Spanish language support",
                "variants": ["es", "mx", "ar", "co"],
                "quality": "high"
            },
            {
                "id": "fr",
                "name": "French",
                "description": "French language support",
                "variants": ["fr", "ca", "be", "ch"],
                "quality": "high"
            },
            {
                "id": "de",
                "name": "German",
                "description": "German language support",
                "variants": ["de", "at", "ch"],
                "quality": "high"
            },
            {
                "id": "it",
                "name": "Italian",
                "description": "Italian language support",
                "variants": ["it", "ch"],
                "quality": "medium"
            },
            {
                "id": "pt",
                "name": "Portuguese",
                "description": "Portuguese language support",
                "variants": ["pt", "br"],
                "quality": "medium"
            },
            {
                "id": "zh",
                "name": "Chinese",
                "description": "Chinese language support",
                "variants": ["zh-cn", "zh-tw"],
                "quality": "medium"
            },
            {
                "id": "ja",
                "name": "Japanese",
                "description": "Japanese language support",
                "variants": ["ja"],
                "quality": "medium"
            }
        ]
    }

@router.get("/voiceover-best-practices")
async def get_voiceover_best_practices():
    """Get best practices for voiceover generation"""
    return {
        "voiceover_best_practices": [
            {
                "category": "script_preparation",
                "title": "Script Preparation",
                "practices": [
                    "Write for spoken delivery, not reading",
                    "Use natural language and conversational tone",
                    "Include appropriate pauses and emphasis",
                    "Avoid complex sentences and jargon",
                    "Test script readability and flow"
                ]
            },
            {
                "category": "voice_selection",
                "title": "Voice Selection",
                "practices": [
                    "Match voice characteristics to target audience",
                    "Consider cultural and regional preferences",
                    "Ensure voice aligns with brand personality",
                    "Test voice with sample content",
                    "Consider accessibility requirements"
                ]
            },
            {
                "category": "audio_quality",
                "title": "Audio Quality",
                "practices": [
                    "Use appropriate audio settings for content type",
                    "Ensure consistent audio quality throughout",
                    "Apply noise reduction when necessary",
                    "Test audio on different devices",
                    "Optimize file size for distribution"
                ]
            },
            {
                "category": "multilingual_considerations",
                "title": "Multilingual Considerations",
                "practices": [
                    "Use native speakers for quality assurance",
                    "Consider cultural nuances in translation",
                    "Adapt pronunciation for local preferences",
                    "Test voiceover with target audience",
                    "Ensure consistent brand voice across languages"
                ]
            }
        ]
    }
