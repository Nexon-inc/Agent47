from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from ..services.grammar_refinement_service import GrammarRefinementService
from ..models import ContentType, PlatformType, ToneType
from ..database import get_shakes_database

router = APIRouter(prefix="/grammar-refinement", tags=["Grammar & Tone Refinement"])

# Pydantic Models
class RefineContentRequest(BaseModel):
    content_piece_id: int = Field(..., description="Content piece ID to refine")
    refinement_type: str = Field(..., description="Type of refinement")
    target_tone: str = Field(..., description="Target tone")
    refinement_goals: List[str] = Field(..., description="Refinement goals")
    preserve_style: bool = Field(default=True, description="Whether to preserve original style")

class RefineContentResponse(BaseModel):
    success: bool
    content_piece_id: int
    original_content: str
    refined_content: str
    refinement_type: str
    target_tone: str
    improvement_analysis: str
    word_count: int
    reading_time: int
    timestamp: str

class BatchRefineRequest(BaseModel):
    content_piece_ids: List[int] = Field(..., description="List of content piece IDs")
    refinement_type: str = Field(..., description="Type of refinement")
    target_tone: str = Field(..., description="Target tone")
    refinement_goals: List[str] = Field(..., description="Refinement goals")

class AnalyzeQualityRequest(BaseModel):
    content_piece_id: int = Field(..., description="Content piece ID to analyze")
    analysis_type: str = Field(default="comprehensive", description="Type of analysis")

class AdjustToneRequest(BaseModel):
    content_piece_id: int = Field(..., description="Content piece ID")
    current_tone: str = Field(..., description="Current tone")
    target_tone: str = Field(..., description="Target tone")
    tone_intensity: str = Field(default="moderate", description="Tone adjustment intensity")

# Dependency
async def get_grammar_refinement_service() -> GrammarRefinementService:
    """Get grammar refinement service instance"""
    service = GrammarRefinementService()
    await service.initialize()
    return service

# Endpoints
@router.post("/refine", response_model=RefineContentResponse, status_code=200)
async def refine_content(
    request: RefineContentRequest,
    service: GrammarRefinementService = Depends(get_grammar_refinement_service)
):
    """Refine content for grammar, tone, and style"""
    try:
        result = await service.refine_content(
            content_piece_id=request.content_piece_id,
            refinement_type=request.refinement_type,
            target_tone=request.target_tone,
            refinement_goals=request.refinement_goals,
            preserve_style=request.preserve_style
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to refine content")
            )
        
        return RefineContentResponse(**result)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Content refinement failed: {str(e)}"
        )

@router.post("/batch-refine", response_model=Dict[str, Any], status_code=200)
async def batch_refine_content(
    request: BatchRefineRequest,
    service: GrammarRefinementService = Depends(get_grammar_refinement_service)
):
    """Refine multiple content pieces in batch"""
    try:
        result = await service.batch_refine_content(
            content_piece_ids=request.content_piece_ids,
            refinement_type=request.refinement_type,
            target_tone=request.target_tone,
            refinement_goals=request.refinement_goals
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to refine content batch")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Batch content refinement failed: {str(e)}"
        )

@router.post("/analyze-quality", response_model=Dict[str, Any], status_code=200)
async def analyze_content_quality(
    request: AnalyzeQualityRequest,
    service: GrammarRefinementService = Depends(get_grammar_refinement_service)
):
    """Analyze content quality and provide improvement suggestions"""
    try:
        result = await service.analyze_content_quality(
            content_piece_id=request.content_piece_id,
            analysis_type=request.analysis_type
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to analyze content quality")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Content quality analysis failed: {str(e)}"
        )

@router.post("/adjust-tone", response_model=Dict[str, Any], status_code=200)
async def adjust_tone(
    request: AdjustToneRequest,
    service: GrammarRefinementService = Depends(get_grammar_refinement_service)
):
    """Adjust content tone while maintaining message"""
    try:
        result = await service.adjust_tone(
            content_piece_id=request.content_piece_id,
            current_tone=request.current_tone,
            target_tone=request.target_tone,
            tone_intensity=request.tone_intensity
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to adjust tone")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Tone adjustment failed: {str(e)}"
        )

@router.get("/refinement-types")
async def get_refinement_types():
    """Get available content refinement types"""
    return {
        "refinement_types": [
            {
                "id": "grammar_syntax",
                "name": "Grammar & Syntax",
                "description": "Fix grammar, spelling, and syntax issues",
                "improvements": [
                    "Grammar corrections",
                    "Spelling fixes",
                    "Syntax improvements",
                    "Punctuation corrections",
                    "Sentence structure"
                ],
                "best_for": ["professional_content", "formal_documents", "academic_writing"]
            },
            {
                "id": "tone_consistency",
                "name": "Tone Consistency",
                "description": "Ensure consistent tone throughout content",
                "improvements": [
                    "Tone alignment",
                    "Voice consistency",
                    "Style uniformity",
                    "Brand voice adherence"
                ],
                "best_for": ["brand_content", "marketing_materials", "corporate_communications"]
            },
            {
                "id": "readability_enhancement",
                "name": "Readability Enhancement",
                "description": "Improve content readability and flow",
                "improvements": [
                    "Sentence clarity",
                    "Paragraph structure",
                    "Flow improvements",
                    "Transition enhancements"
                ],
                "best_for": ["blog_posts", "articles", "educational_content"]
            },
            {
                "id": "engagement_optimization",
                "name": "Engagement Optimization",
                "description": "Optimize content for better engagement",
                "improvements": [
                    "Hook improvements",
                    "Call-to-action enhancement",
                    "Emotional appeal",
                    "Audience connection"
                ],
                "best_for": ["social_media", "marketing_content", "sales_materials"]
            },
            {
                "id": "seo_optimization",
                "name": "SEO Optimization",
                "description": "Optimize content for search engines",
                "improvements": [
                    "Keyword integration",
                    "Meta optimization",
                    "Structure improvements",
                    "Search visibility"
                ],
                "best_for": ["blog_posts", "website_content", "article_writing"]
            }
        ]
    }

@router.get("/tone-types")
async def get_tone_types():
    """Get available tone types for content refinement"""
    return {
        "tone_types": [
            {
                "id": "professional",
                "name": "Professional",
                "description": "Formal, business-appropriate tone",
                "characteristics": ["formal", "authoritative", "credible", "respectful"],
                "best_for": ["business_communications", "reports", "presentations"],
                "language_style": ["formal_vocabulary", "complete_sentences", "professional_terminology"]
            },
            {
                "id": "casual",
                "name": "Casual",
                "description": "Relaxed, conversational tone",
                "characteristics": ["friendly", "approachable", "conversational", "relaxed"],
                "best_for": ["social_media", "blog_posts", "personal_communications"],
                "language_style": ["contractions", "colloquialisms", "personal_pronouns"]
            },
            {
                "id": "authoritative",
                "name": "Authoritative",
                "description": "Expert, knowledgeable tone",
                "characteristics": ["expert", "confident", "knowledgeable", "decisive"],
                "best_for": ["expert_content", "industry_insights", "thought_leadership"],
                "language_style": ["expert_terminology", "confident_statements", "data_driven"]
            },
            {
                "id": "friendly",
                "name": "Friendly",
                "description": "Warm, approachable tone",
                "characteristics": ["warm", "welcoming", "supportive", "encouraging"],
                "best_for": ["customer_service", "community_content", "support_materials"],
                "language_style": ["positive_language", "encouraging_words", "supportive_phrases"]
            },
            {
                "id": "persuasive",
                "name": "Persuasive",
                "description": "Convincing, compelling tone",
                "characteristics": ["convincing", "compelling", "motivating", "action_oriented"],
                "best_for": ["sales_content", "marketing_materials", "call_to_actions"],
                "language_style": ["action_words", "benefit_focused", "urgency_creating"]
            }
        ]
    }

@router.get("/refinement-goals")
async def get_refinement_goals():
    """Get common refinement goals for content improvement"""
    return {
        "refinement_goals": [
            {
                "id": "improve_clarity",
                "name": "Improve Clarity",
                "description": "Make content clearer and easier to understand",
                "focus_areas": ["sentence_structure", "word_choice", "logical_flow"],
                "techniques": ["simplify_sentences", "use_active_voice", "eliminate_jargon"]
            },
            {
                "id": "enhance_engagement",
                "name": "Enhance Engagement",
                "description": "Make content more engaging and interesting",
                "focus_areas": ["hooks", "storytelling", "emotional_appeal"],
                "techniques": ["add_stories", "use_questions", "create_curiosity"]
            },
            {
                "id": "strengthen_voice",
                "name": "Strengthen Voice",
                "description": "Develop a stronger, more distinctive voice",
                "focus_areas": ["personality", "uniqueness", "authenticity"],
                "techniques": ["add_personality", "use_unique_phrases", "be_authentic"]
            },
            {
                "id": "optimize_structure",
                "name": "Optimize Structure",
                "description": "Improve content organization and flow",
                "focus_areas": ["paragraph_flow", "transition_sentences", "logical_order"],
                "techniques": ["improve_transitions", "reorganize_sections", "add_headings"]
            },
            {
                "id": "increase_persuasiveness",
                "name": "Increase Persuasiveness",
                "description": "Make content more convincing and compelling",
                "focus_areas": ["arguments", "evidence", "call_to_action"],
                "techniques": ["strengthen_arguments", "add_evidence", "improve_cta"]
            }
        ]
    }
