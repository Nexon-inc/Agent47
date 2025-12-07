from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from ..services.plagiarism_detection_service import PlagiarismDetectionService
from ..models import ContentType, PlatformType, ToneType
from ..database import get_shakes_database

router = APIRouter(prefix="/plagiarism-detection", tags=["Plagiarism Detection"])

# Pydantic Models
class CheckPlagiarismRequest(BaseModel):
    content_piece_id: int = Field(..., description="Content piece ID to check")
    check_type: str = Field(default="comprehensive", description="Type of plagiarism check")
    similarity_threshold: float = Field(default=0.8, description="Similarity threshold for detection")

class CheckPlagiarismResponse(BaseModel):
    success: bool
    content_piece_id: int
    check_type: str
    originality_score: float
    plagiarism_analysis: Dict[str, Any]
    originality_report: str
    internal_similarity: Dict[str, Any]
    similarity_threshold: float
    is_original: bool
    timestamp: str

class BatchCheckPlagiarismRequest(BaseModel):
    content_piece_ids: List[int] = Field(..., description="List of content piece IDs")
    check_type: str = Field(default="comprehensive", description="Type of plagiarism check")
    similarity_threshold: float = Field(default=0.8, description="Similarity threshold for detection")

class ImproveOriginalityRequest(BaseModel):
    content_piece_id: int = Field(..., description="Content piece ID to improve")
    target_originality_score: float = Field(default=0.9, description="Target originality score")
    improvement_focus: List[str] = Field(default=[], description="Areas to focus improvement on")

# Dependency
async def get_plagiarism_detection_service() -> PlagiarismDetectionService:
    """Get plagiarism detection service instance"""
    service = PlagiarismDetectionService()
    await service.initialize()
    return service

# Endpoints
@router.post("/check", response_model=CheckPlagiarismResponse, status_code=200)
async def check_plagiarism(
    request: CheckPlagiarismRequest,
    service: PlagiarismDetectionService = Depends(get_plagiarism_detection_service)
):
    """Check content for plagiarism and originality"""
    try:
        result = await service.check_plagiarism(
            content_piece_id=request.content_piece_id,
            check_type=request.check_type,
            similarity_threshold=request.similarity_threshold
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to check plagiarism")
            )
        
        return CheckPlagiarismResponse(**result)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Plagiarism check failed: {str(e)}"
        )

@router.post("/batch-check", response_model=Dict[str, Any], status_code=200)
async def batch_check_plagiarism(
    request: BatchCheckPlagiarismRequest,
    service: PlagiarismDetectionService = Depends(get_plagiarism_detection_service)
):
    """Check multiple content pieces for plagiarism in batch"""
    try:
        result = await service.batch_check_plagiarism(
            content_piece_ids=request.content_piece_ids,
            check_type=request.check_type,
            similarity_threshold=request.similarity_threshold
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to check plagiarism batch")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Batch plagiarism check failed: {str(e)}"
        )

@router.post("/improve-originality", response_model=Dict[str, Any], status_code=200)
async def improve_originality(
    request: ImproveOriginalityRequest,
    service: PlagiarismDetectionService = Depends(get_plagiarism_detection_service)
):
    """Improve content originality while maintaining quality"""
    try:
        result = await service.improve_originality(
            content_piece_id=request.content_piece_id,
            target_originality_score=request.target_originality_score,
            improvement_focus=request.improvement_focus
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to improve originality")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Originality improvement failed: {str(e)}"
        )

@router.get("/check-types")
async def get_check_types():
    """Get available plagiarism check types"""
    return {
        "check_types": [
            {
                "id": "comprehensive",
                "name": "Comprehensive Check",
                "description": "Full plagiarism analysis with detailed reporting",
                "features": [
                    "Grammar and syntax analysis",
                    "Common phrase detection",
                    "Template pattern recognition",
                    "Originality scoring",
                    "Improvement recommendations"
                ],
                "best_for": ["final_content", "important_documents", "publication_ready"],
                "processing_time": "2-3 minutes"
            },
            {
                "id": "quick",
                "name": "Quick Check",
                "description": "Fast plagiarism detection for basic screening",
                "features": [
                    "Basic similarity detection",
                    "Common phrase identification",
                    "Quick originality score"
                ],
                "best_for": ["draft_content", "initial_screening", "quick_validation"],
                "processing_time": "30-60 seconds"
            },
            {
                "id": "deep",
                "name": "Deep Analysis",
                "description": "Thorough analysis with detailed insights",
                "features": [
                    "Advanced pattern recognition",
                    "Semantic similarity analysis",
                    "Detailed improvement suggestions",
                    "Industry-specific analysis"
                ],
                "best_for": ["academic_content", "research_papers", "professional_documents"],
                "processing_time": "5-10 minutes"
            }
        ]
    }

@router.get("/similarity-thresholds")
async def get_similarity_thresholds():
    """Get recommended similarity thresholds for different use cases"""
    return {
        "similarity_thresholds": [
            {
                "threshold": 0.9,
                "name": "Very Strict",
                "description": "Requires 90% originality",
                "use_cases": ["academic_papers", "research_publications", "legal_documents"],
                "recommendations": ["Use for critical content", "Academic integrity", "Legal compliance"]
            },
            {
                "threshold": 0.8,
                "name": "Strict",
                "description": "Requires 80% originality",
                "use_cases": ["professional_content", "business_documents", "marketing_materials"],
                "recommendations": ["Standard for business content", "Professional standards", "Brand protection"]
            },
            {
                "threshold": 0.7,
                "name": "Moderate",
                "description": "Requires 70% originality",
                "use_cases": ["blog_posts", "social_media", "general_content"],
                "recommendations": ["Good for general content", "Balanced approach", "Content marketing"]
            },
            {
                "threshold": 0.6,
                "name": "Lenient",
                "description": "Requires 60% originality",
                "use_cases": ["draft_content", "internal_documents", "reference_materials"],
                "recommendations": ["Use for drafts", "Internal use only", "Reference content"]
            }
        ]
    }

@router.get("/improvement-focus-areas")
async def get_improvement_focus_areas():
    """Get available improvement focus areas for originality enhancement"""
    return {
        "improvement_focus_areas": [
            {
                "id": "rewrite_phrases",
                "name": "Rewrite Common Phrases",
                "description": "Replace common phrases with original expressions",
                "techniques": [
                    "Paraphrase common expressions",
                    "Use synonyms and alternatives",
                    "Create unique phrasings",
                    "Avoid clichés and overused terms"
                ],
                "best_for": ["generic_content", "template_based_writing", "common_topics"]
            },
            {
                "id": "add_original_insights",
                "name": "Add Original Insights",
                "description": "Include unique perspectives and original thoughts",
                "techniques": [
                    "Add personal experiences",
                    "Include unique observations",
                    "Provide original analysis",
                    "Share innovative ideas"
                ],
                "best_for": ["thought_leadership", "expert_content", "opinion_pieces"]
            },
            {
                "id": "restructure_content",
                "name": "Restructure Content",
                "description": "Reorganize content for better originality",
                "techniques": [
                    "Change paragraph order",
                    "Modify sentence structure",
                    "Alter content flow",
                    "Create unique organization"
                ],
                "best_for": ["structured_content", "formal_documents", "academic_writing"]
            },
            {
                "id": "enhance_voice",
                "name": "Enhance Voice",
                "description": "Develop a more distinctive writing voice",
                "techniques": [
                    "Add personality to writing",
                    "Use unique expressions",
                    "Develop distinctive style",
                    "Create authentic voice"
                ],
                "best_for": ["brand_content", "personal_writing", "creative_content"]
            },
            {
                "id": "add_examples",
                "name": "Add Original Examples",
                "description": "Include unique examples and case studies",
                "techniques": [
                    "Create original examples",
                    "Add personal case studies",
                    "Include unique scenarios",
                    "Provide specific instances"
                ],
                "best_for": ["educational_content", "how_to_guides", "tutorial_content"]
            }
        ]
    }

@router.get("/originality-guidelines")
async def get_originality_guidelines():
    """Get guidelines for maintaining content originality"""
    return {
        "originality_guidelines": [
            {
                "category": "writing_practices",
                "title": "Writing Practices",
                "guidelines": [
                    "Write from your own perspective and experience",
                    "Use original research and data when possible",
                    "Cite sources properly when referencing others' work",
                    "Avoid copying sentence structures from other content",
                    "Develop your own unique voice and style"
                ]
            },
            {
                "category": "content_creation",
                "title": "Content Creation",
                "guidelines": [
                    "Start with original ideas and concepts",
                    "Add personal insights and analysis",
                    "Include unique examples and case studies",
                    "Create original headlines and titles",
                    "Develop unique content structures"
                ]
            },
            {
                "category": "research_integration",
                "title": "Research Integration",
                "guidelines": [
                    "Synthesize information from multiple sources",
                    "Add your own analysis and interpretation",
                    "Present information in your own words",
                    "Include original conclusions and insights",
                    "Credit all sources appropriately"
                ]
            },
            {
                "category": "quality_standards",
                "title": "Quality Standards",
                "guidelines": [
                    "Maintain high standards of originality",
                    "Regularly check content for plagiarism",
                    "Use plagiarism detection tools",
                    "Review and improve content regularly",
                    "Ensure all content meets originality requirements"
                ]
            }
        ]
    }
