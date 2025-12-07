from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from ..services.brand_voice_service import BrandVoiceService
from ..models import ContentType, PlatformType, ToneType
from ..database import get_shakes_database

router = APIRouter(prefix="/brand-voice", tags=["Brand Voice"])

# Pydantic Models
class CreateBrandVoiceRequest(BaseModel):
    user_id: int = Field(..., description="User ID")
    brand_name: str = Field(..., description="Brand name")
    brand_description: str = Field(..., description="Brand description")
    target_audience: str = Field(..., description="Target audience")
    brand_values: List[str] = Field(..., description="Brand values")
    tone_characteristics: List[str] = Field(..., description="Tone characteristics")
    sample_content: List[str] = Field(default=[], description="Sample content for analysis")
    industry: str = Field(..., description="Industry")

class CreateBrandVoiceResponse(BaseModel):
    success: bool
    brand_voice_id: int
    brand_name: str
    voice_analysis: str
    voice_guidelines: str
    brand_values: List[str]
    tone_characteristics: List[str]
    target_audience: str
    industry: str
    timestamp: str

class ApplyBrandVoiceRequest(BaseModel):
    content_piece_id: int = Field(..., description="Content piece ID")
    brand_voice_id: int = Field(..., description="Brand voice ID")
    application_intensity: str = Field(default="moderate", description="Application intensity")

class AnalyzeConsistencyRequest(BaseModel):
    content_piece_id: int = Field(..., description="Content piece ID")
    brand_voice_id: int = Field(..., description="Brand voice ID")

class UpdateBrandVoiceRequest(BaseModel):
    brand_voice_id: int = Field(..., description="Brand voice ID")
    updates: Dict[str, Any] = Field(..., description="Updates to apply")

# Dependency
async def get_brand_voice_service() -> BrandVoiceService:
    """Get brand voice service instance"""
    service = BrandVoiceService()
    await service.initialize()
    return service

# Endpoints
@router.post("/create", response_model=CreateBrandVoiceResponse, status_code=201)
async def create_brand_voice(
    request: CreateBrandVoiceRequest,
    service: BrandVoiceService = Depends(get_brand_voice_service)
):
    """Create and define brand voice profile"""
    try:
        result = await service.create_brand_voice(
            user_id=request.user_id,
            brand_name=request.brand_name,
            brand_description=request.brand_description,
            target_audience=request.target_audience,
            brand_values=request.brand_values,
            tone_characteristics=request.tone_characteristics,
            sample_content=request.sample_content,
            industry=request.industry
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to create brand voice")
            )
        
        return CreateBrandVoiceResponse(**result)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Brand voice creation failed: {str(e)}"
        )

@router.post("/apply", response_model=Dict[str, Any], status_code=200)
async def apply_brand_voice(
    request: ApplyBrandVoiceRequest,
    service: BrandVoiceService = Depends(get_brand_voice_service)
):
    """Apply brand voice to existing content"""
    try:
        result = await service.apply_brand_voice(
            content_piece_id=request.content_piece_id,
            brand_voice_id=request.brand_voice_id,
            application_intensity=request.application_intensity
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to apply brand voice")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Brand voice application failed: {str(e)}"
        )

@router.post("/analyze-consistency", response_model=Dict[str, Any], status_code=200)
async def analyze_brand_consistency(
    request: AnalyzeConsistencyRequest,
    service: BrandVoiceService = Depends(get_brand_voice_service)
):
    """Analyze content for brand voice consistency"""
    try:
        result = await service.analyze_brand_consistency(
            content_piece_id=request.content_piece_id,
            brand_voice_id=request.brand_voice_id
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to analyze brand consistency")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Brand consistency analysis failed: {str(e)}"
        )

@router.put("/update", response_model=Dict[str, Any], status_code=200)
async def update_brand_voice(
    request: UpdateBrandVoiceRequest,
    service: BrandVoiceService = Depends(get_brand_voice_service)
):
    """Update existing brand voice profile"""
    try:
        result = await service.update_brand_voice(
            brand_voice_id=request.brand_voice_id,
            updates=request.updates
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to update brand voice")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Brand voice update failed: {str(e)}"
        )

@router.get("/tone-characteristics")
async def get_tone_characteristics():
    """Get available tone characteristics for brand voice"""
    return {
        "tone_characteristics": [
            {
                "id": "professional",
                "name": "Professional",
                "description": "Formal, business-appropriate tone",
                "attributes": ["authoritative", "credible", "respectful", "formal"],
                "best_for": ["corporate_communications", "business_documents", "professional_services"],
                "language_style": ["formal_vocabulary", "complete_sentences", "professional_terminology"]
            },
            {
                "id": "friendly",
                "name": "Friendly",
                "description": "Warm, approachable, and welcoming tone",
                "attributes": ["warm", "approachable", "welcoming", "supportive"],
                "best_for": ["customer_service", "community_building", "support_content"],
                "language_style": ["conversational", "positive_language", "encouraging_words"]
            },
            {
                "id": "authoritative",
                "name": "Authoritative",
                "description": "Expert, knowledgeable, and confident tone",
                "attributes": ["expert", "knowledgeable", "confident", "decisive"],
                "best_for": ["thought_leadership", "industry_insights", "expert_content"],
                "language_style": ["expert_terminology", "confident_statements", "data_driven"]
            },
            {
                "id": "casual",
                "name": "Casual",
                "description": "Relaxed, informal, and conversational tone",
                "attributes": ["relaxed", "informal", "conversational", "easygoing"],
                "best_for": ["social_media", "blog_posts", "personal_brands"],
                "language_style": ["contractions", "colloquialisms", "personal_pronouns"]
            },
            {
                "id": "innovative",
                "name": "Innovative",
                "description": "Forward-thinking, creative, and cutting-edge tone",
                "attributes": ["creative", "innovative", "forward_thinking", "dynamic"],
                "best_for": ["tech_companies", "startups", "creative_agencies"],
                "language_style": ["modern_terminology", "creative_expressions", "future_focused"]
            },
            {
                "id": "trustworthy",
                "name": "Trustworthy",
                "description": "Reliable, honest, and transparent tone",
                "attributes": ["reliable", "honest", "transparent", "dependable"],
                "best_for": ["financial_services", "healthcare", "consulting"],
                "language_style": ["clear_communication", "honest_language", "transparent_messaging"]
            }
        ]
    }

@router.get("/brand-values")
async def get_brand_values():
    """Get common brand values for voice definition"""
    return {
        "brand_values": [
            {
                "id": "innovation",
                "name": "Innovation",
                "description": "Commitment to new ideas and creative solutions",
                "voice_implications": ["forward_thinking", "creative", "cutting_edge"],
                "language_style": ["modern_terminology", "future_focused", "breakthrough_language"]
            },
            {
                "id": "quality",
                "name": "Quality",
                "description": "Dedication to excellence and high standards",
                "voice_implications": ["premium", "excellence", "attention_to_detail"],
                "language_style": ["premium_terminology", "quality_focused", "excellence_language"]
            },
            {
                "id": "integrity",
                "name": "Integrity",
                "description": "Honesty, transparency, and ethical behavior",
                "voice_implications": ["honest", "transparent", "ethical"],
                "language_style": ["clear_communication", "honest_language", "transparent_messaging"]
            },
            {
                "id": "customer_focus",
                "name": "Customer Focus",
                "description": "Putting customers at the center of everything",
                "voice_implications": ["customer_centric", "service_oriented", "responsive"],
                "language_style": ["customer_focused", "service_language", "supportive_tone"]
            },
            {
                "id": "sustainability",
                "name": "Sustainability",
                "description": "Commitment to environmental and social responsibility",
                "voice_implications": ["responsible", "sustainable", "conscious"],
                "language_style": ["eco_friendly_terminology", "responsible_language", "conscious_messaging"]
            },
            {
                "id": "collaboration",
                "name": "Collaboration",
                "description": "Working together and building partnerships",
                "voice_implications": ["collaborative", "partnership_focused", "team_oriented"],
                "language_style": ["inclusive_language", "partnership_terminology", "collaborative_tone"]
            }
        ]
    }

@router.get("/application-intensities")
async def get_application_intensities():
    """Get available brand voice application intensities"""
    return {
        "application_intensities": [
            {
                "id": "subtle",
                "name": "Subtle",
                "description": "Light application of brand voice characteristics",
                "changes": ["Minor tone adjustments", "Subtle language changes", "Gentle voice alignment"],
                "best_for": ["existing_content", "minimal_changes", "gradual_transition"],
                "impact": "Low impact, maintains original style"
            },
            {
                "id": "moderate",
                "name": "Moderate",
                "description": "Balanced application of brand voice",
                "changes": ["Clear tone alignment", "Language adjustments", "Voice consistency"],
                "best_for": ["standard_content", "brand_alignment", "consistent_voice"],
                "impact": "Medium impact, good balance"
            },
            {
                "id": "strong",
                "name": "Strong",
                "description": "Prominent application of brand voice characteristics",
                "changes": ["Strong tone alignment", "Significant language changes", "Clear voice identity"],
                "best_for": ["brand_content", "marketing_materials", "strong_identity"],
                "impact": "High impact, clear brand voice"
            },
            {
                "id": "complete",
                "name": "Complete",
                "description": "Full transformation to match brand voice",
                "changes": ["Complete voice transformation", "Full language alignment", "Brand voice dominance"],
                "best_for": ["new_content", "brand_launch", "complete_rebrand"],
                "impact": "Maximum impact, full brand voice"
            }
        ]
    }

@router.get("/consistency-guidelines")
async def get_consistency_guidelines():
    """Get guidelines for maintaining brand voice consistency"""
    return {
        "consistency_guidelines": [
            {
                "category": "voice_consistency",
                "title": "Voice Consistency",
                "guidelines": [
                    "Maintain consistent tone across all content",
                    "Use brand voice guidelines as reference",
                    "Regularly review content for voice alignment",
                    "Train team members on brand voice",
                    "Create voice style guides and examples"
                ]
            },
            {
                "category": "language_consistency",
                "title": "Language Consistency",
                "guidelines": [
                    "Use consistent terminology and vocabulary",
                    "Maintain brand-specific language patterns",
                    "Avoid conflicting language styles",
                    "Create and maintain a brand dictionary",
                    "Regularly update language guidelines"
                ]
            },
            {
                "category": "message_consistency",
                "title": "Message Consistency",
                "guidelines": [
                    "Align all messages with brand values",
                    "Ensure consistent brand positioning",
                    "Maintain coherent brand narrative",
                    "Regularly audit brand messaging",
                    "Update messaging as brand evolves"
                ]
            },
            {
                "category": "quality_standards",
                "title": "Quality Standards",
                "guidelines": [
                    "Establish clear quality standards",
                    "Regularly review content quality",
                    "Use consistency check tools",
                    "Provide feedback and training",
                    "Continuously improve processes"
                ]
            }
        ]
    }
