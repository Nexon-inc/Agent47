from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from ..services.content_collaboration_service import ContentCollaborationService
from ..models import ContentType, PlatformType, ToneType
from ..database import get_shakes_database

router = APIRouter(prefix="/content-collaboration", tags=["Content Collaboration"])

# Pydantic Models
class CreateCollaborationSessionRequest(BaseModel):
    user_id: int = Field(..., description="User ID")
    content_piece_id: int = Field(..., description="Content piece ID")
    collaboration_type: str = Field(..., description="Collaboration type")
    team_members: List[int] = Field(..., description="Team member IDs")
    collaboration_goals: List[str] = Field(..., description="Collaboration goals")
    deadline: Optional[str] = Field(default=None, description="Collaboration deadline")

class CreateCollaborationSessionResponse(BaseModel):
    success: bool
    collaboration_id: int
    content_piece_id: int
    collaboration_type: str
    team_members: List[int]
    collaboration_goals: List[str]
    collaboration_guidelines: str
    status: str
    deadline: Optional[str]
    timestamp: str

class AddCommentRequest(BaseModel):
    collaboration_id: int = Field(..., description="Collaboration ID")
    user_id: int = Field(..., description="User ID")
    comment_type: str = Field(..., description="Comment type")
    content: str = Field(..., description="Comment content")
    parent_comment_id: Optional[int] = Field(default=None, description="Parent comment ID")

class UpdateCollaborationStatusRequest(BaseModel):
    collaboration_id: int = Field(..., description="Collaboration ID")
    new_status: str = Field(..., description="New status")
    status_notes: str = Field(default="", description="Status update notes")

# Dependency
async def get_content_collaboration_service() -> ContentCollaborationService:
    """Get content collaboration service instance"""
    service = ContentCollaborationService()
    await service.initialize()
    return service

# Endpoints
@router.post("/create-session", response_model=CreateCollaborationSessionResponse, status_code=201)
async def create_collaboration_session(
    request: CreateCollaborationSessionRequest,
    service: ContentCollaborationService = Depends(get_content_collaboration_service)
):
    """Create a collaboration session for content"""
    try:
        result = await service.create_collaboration_session(
            user_id=request.user_id,
            content_piece_id=request.content_piece_id,
            collaboration_type=request.collaboration_type,
            team_members=request.team_members,
            collaboration_goals=request.collaboration_goals,
            deadline=request.deadline
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to create collaboration session")
            )
        
        return CreateCollaborationSessionResponse(**result)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Collaboration session creation failed: {str(e)}"
        )

@router.post("/add-comment", response_model=Dict[str, Any], status_code=201)
async def add_comment(
    request: AddCommentRequest,
    service: ContentCollaborationService = Depends(get_content_collaboration_service)
):
    """Add comment to collaboration session"""
    try:
        result = await service.add_comment(
            collaboration_id=request.collaboration_id,
            user_id=request.user_id,
            comment_type=request.comment_type,
            content=request.content,
            parent_comment_id=request.parent_comment_id
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to add comment")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Comment addition failed: {str(e)}"
        )

@router.get("/thread/{collaboration_id}", response_model=Dict[str, Any], status_code=200)
async def get_collaboration_thread(
    collaboration_id: int,
    service: ContentCollaborationService = Depends(get_content_collaboration_service)
):
    """Get collaboration thread with all comments"""
    try:
        result = await service.get_collaboration_thread(
            collaboration_id=collaboration_id
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to get collaboration thread")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Collaboration thread retrieval failed: {str(e)}"
        )

@router.put("/update-status", response_model=Dict[str, Any], status_code=200)
async def update_collaboration_status(
    request: UpdateCollaborationStatusRequest,
    service: ContentCollaborationService = Depends(get_content_collaboration_service)
):
    """Update collaboration session status"""
    try:
        result = await service.update_collaboration_status(
            collaboration_id=request.collaboration_id,
            new_status=request.new_status,
            status_notes=request.status_notes
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to update collaboration status")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Collaboration status update failed: {str(e)}"
        )

@router.post("/generate-summary/{collaboration_id}", response_model=Dict[str, Any], status_code=200)
async def generate_collaboration_summary(
    collaboration_id: int,
    service: ContentCollaborationService = Depends(get_content_collaboration_service)
):
    """Generate summary of collaboration session"""
    try:
        result = await service.generate_collaboration_summary(
            collaboration_id=collaboration_id
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to generate collaboration summary")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Collaboration summary generation failed: {str(e)}"
        )

@router.get("/collaboration-types")
async def get_collaboration_types():
    """Get available collaboration types"""
    return {
        "collaboration_types": [
            {
                "id": "content_review",
                "name": "Content Review",
                "description": "Review and feedback on content quality",
                "best_for": ["quality_assurance", "content_improvement", "team_feedback"],
                "typical_duration": "1-3 days",
                "key_activities": ["content_review", "feedback_providing", "revision_suggestions"]
            },
            {
                "id": "content_creation",
                "name": "Content Creation",
                "description": "Collaborative content creation and development",
                "best_for": ["team_writing", "brainstorming", "content_development"],
                "typical_duration": "3-7 days",
                "key_activities": ["idea_generation", "content_writing", "collaborative_editing"]
            },
            {
                "id": "content_optimization",
                "name": "Content Optimization",
                "description": "Optimize content for performance and engagement",
                "best_for": ["seo_optimization", "performance_improvement", "engagement_enhancement"],
                "typical_duration": "2-5 days",
                "key_activities": ["seo_analysis", "performance_review", "optimization_implementation"]
            },
            {
                "id": "content_approval",
                "name": "Content Approval",
                "description": "Approval process for content publication",
                "best_for": ["final_review", "approval_workflow", "publication_readiness"],
                "typical_duration": "1-2 days",
                "key_activities": ["final_review", "approval_decision", "publication_clearance"]
            }
        ]
    }

@router.get("/comment-types")
async def get_comment_types():
    """Get available comment types for collaboration"""
    return {
        "comment_types": [
            {
                "id": "feedback",
                "name": "Feedback",
                "description": "General feedback and suggestions",
                "best_for": ["content_improvement", "quality_assurance", "team_communication"],
                "format": "text",
                "examples": ["Great work!", "Consider adding more examples", "This section needs clarification"]
            },
            {
                "id": "suggestion",
                "name": "Suggestion",
                "description": "Specific suggestions for improvement",
                "best_for": ["content_enhancement", "optimization", "creative_input"],
                "format": "text",
                "examples": ["Add a call-to-action here", "Use bullet points for better readability", "Include a relevant statistic"]
            },
            {
                "id": "question",
                "name": "Question",
                "description": "Questions about content or approach",
                "best_for": ["clarification", "discussion", "decision_making"],
                "format": "text",
                "examples": ["What is the target audience for this section?", "Should we include more technical details?", "How does this align with our brand voice?"]
            },
            {
                "id": "approval",
                "name": "Approval",
                "description": "Approval or rejection of content",
                "best_for": ["final_review", "approval_workflow", "decision_making"],
                "format": "text",
                "examples": ["Approved for publication", "Needs revision before approval", "Ready for next stage"]
            },
            {
                "id": "revision",
                "name": "Revision",
                "description": "Specific revision requests",
                "best_for": ["content_changes", "improvement_requests", "quality_control"],
                "format": "text",
                "examples": ["Please revise this paragraph", "Update the statistics", "Change the tone to be more professional"]
            }
        ]
    }

@router.get("/collaboration-best-practices")
async def get_collaboration_best_practices():
    """Get best practices for content collaboration"""
    return {
        "collaboration_best_practices": [
            {
                "category": "communication",
                "title": "Communication Best Practices",
                "practices": [
                    "Be clear and specific in feedback",
                    "Use constructive language",
                    "Provide context for suggestions",
                    "Respond promptly to comments",
                    "Ask clarifying questions when needed"
                ]
            },
            {
                "category": "workflow",
                "title": "Workflow Best Practices",
                "practices": [
                    "Set clear deadlines and expectations",
                    "Define roles and responsibilities",
                    "Use consistent review processes",
                    "Track progress and milestones",
                    "Document decisions and changes"
                ]
            },
            {
                "category": "quality",
                "title": "Quality Best Practices",
                "practices": [
                    "Focus on content quality and accuracy",
                    "Ensure brand voice consistency",
                    "Check for grammar and style",
                    "Verify facts and sources",
                    "Test content on different devices"
                ]
            },
            {
                "category": "teamwork",
                "title": "Teamwork Best Practices",
                "practices": [
                    "Respect different perspectives",
                    "Encourage diverse viewpoints",
                    "Provide positive reinforcement",
                    "Learn from feedback",
                    "Celebrate successful collaborations"
                ]
            }
        ]
    }
