from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from ..services.video_scripting_service import VideoScriptingService
from ..models import ContentType, PlatformType
from ..database import get_shakes_database

router = APIRouter()

# Pydantic models for request/response
class CreateVideoScriptRequest(BaseModel):
    video_type: str = Field(..., description="Type of video to create")
    topic: str = Field(..., min_length=1, max_length=200, description="Main topic of the video")
    target_audience: str = Field(..., description="Target audience for the video")
    duration: int = Field(..., ge=1, le=120, description="Duration in minutes")
    tone: str = Field(..., description="Desired tone for the video")
    call_to_action: str = Field(..., description="Call-to-action for the video")
    include_visuals: bool = Field(default=True, description="Include visual storyboard")
    include_music_cues: bool = Field(default=True, description="Include music cues and timing")

class CreatePodcastScriptRequest(BaseModel):
    podcast_type: str = Field(..., description="Type of podcast to create")
    topic: str = Field(..., min_length=1, max_length=200, description="Main topic of the podcast")
    target_audience: str = Field(..., description="Target audience for the podcast")
    duration: int = Field(..., ge=5, le=180, description="Duration in minutes")
    tone: str = Field(..., description="Desired tone for the podcast")
    include_guest_sections: bool = Field(default=False, description="Include guest interview sections")
    include_q_a: bool = Field(default=False, description="Include Q&A format")

class ScriptEnhancementRequest(BaseModel):
    enhancement_type: str = Field(..., description="Type of enhancement to apply")
    enhancement_params: Dict[str, Any] = Field(default={}, description="Parameters for enhancement")

class VideoScriptResponse(BaseModel):
    project_id: int
    content_piece_id: int
    video_script: str
    script_outline: str
    storyboard: str
    production_notes: str
    estimated_duration: int
    word_count: int
    timestamp: str

class PodcastScriptResponse(BaseModel):
    project_id: int
    content_piece_id: int
    podcast_script: str
    podcast_outline: str
    episode_notes: str
    estimated_duration: int
    word_count: int
    timestamp: str

class EnhancementResponse(BaseModel):
    enhanced_script: str
    word_count: int
    timestamp: str

# Dependency
async def get_video_scripting_service() -> VideoScriptingService:
    service = VideoScriptingService()
    await service.initialize()
    return service

@router.post("/video-script", response_model=Dict[str, Any])
async def create_video_script(
    request: CreateVideoScriptRequest,
    service: VideoScriptingService = Depends(get_video_scripting_service)
):
    """Create comprehensive video script with AI-powered storytelling"""
    try:
        result = await service.create_video_script(
            user_id=1,  # TODO: Get from authentication
            video_type=request.video_type,
            topic=request.topic,
            target_audience=request.target_audience,
            duration=request.duration,
            tone=request.tone,
            call_to_action=request.call_to_action,
            include_visuals=request.include_visuals,
            include_music_cues=request.include_music_cues
        )
        
        if result["success"]:
            return {
                "status": "success",
                "message": f"Video script for '{request.topic}' created successfully",
                "data": {
                    "project_id": result["project_id"],
                    "content_piece_id": result["content_piece_id"],
                    "video_script": result["video_script"],
                    "script_outline": result["script_outline"],
                    "storyboard": result["storyboard"],
                    "production_notes": result["production_notes"],
                    "estimated_duration": result["estimated_duration"],
                    "word_count": result["word_count"],
                    "timestamp": result["timestamp"]
                }
            }
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/podcast-script", response_model=Dict[str, Any])
async def create_podcast_script(
    request: CreatePodcastScriptRequest,
    service: VideoScriptingService = Depends(get_video_scripting_service)
):
    """Create podcast script with AI-powered content structure"""
    try:
        result = await service.create_podcast_script(
            user_id=1,  # TODO: Get from authentication
            podcast_type=request.podcast_type,
            topic=request.topic,
            target_audience=request.target_audience,
            duration=request.duration,
            tone=request.tone,
            include_guest_sections=request.include_guest_sections,
            include_q_a=request.include_q_a
        )
        
        if result["success"]:
            return {
                "status": "success",
                "message": f"Podcast script for '{request.topic}' created successfully",
                "data": {
                    "project_id": result["project_id"],
                    "content_piece_id": result["content_piece_id"],
                    "podcast_script": result["podcast_script"],
                    "podcast_outline": result["podcast_outline"],
                    "episode_notes": result["episode_notes"],
                    "estimated_duration": result["estimated_duration"],
                    "word_count": result["word_count"],
                    "timestamp": result["timestamp"]
                }
            }
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{content_piece_id}/enhance", response_model=Dict[str, Any])
async def enhance_script(
    content_piece_id: int,
    request: ScriptEnhancementRequest,
    service: VideoScriptingService = Depends(get_video_scripting_service)
):
    """Enhance existing script with additional features"""
    try:
        result = await service.enhance_script(
            content_piece_id=content_piece_id,
            enhancement_type=request.enhancement_type,
            enhancement_params=request.enhancement_params
        )
        
        if result["success"]:
            return {
                "status": "success",
                "message": f"Script enhanced successfully with {request.enhancement_type}",
                "data": {
                    "enhanced_script": result["enhanced_script"],
                    "word_count": result["word_count"],
                    "timestamp": result["timestamp"]
                }
            }
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/video-types")
async def get_video_types():
    """Get available video types for scripting"""
    video_types = [
        {
            "value": "explainer",
            "label": "Explainer Video",
            "description": "Educational content that explains complex topics",
            "typical_duration": "2-5 minutes",
            "best_for": ["Product demos", "How-to guides", "Concept explanations"],
            "script_elements": ["Clear introduction", "Step-by-step breakdown", "Visual examples", "Summary"]
        },
        {
            "value": "promotional",
            "label": "Promotional Video",
            "description": "Marketing content to promote products or services",
            "typical_duration": "30 seconds - 2 minutes",
            "best_for": ["Product launches", "Service promotion", "Brand awareness"],
            "script_elements": ["Hook", "Problem statement", "Solution presentation", "Call-to-action"]
        },
        {
            "value": "testimonial",
            "label": "Testimonial Video",
            "description": "Customer success stories and reviews",
            "typical_duration": "1-3 minutes",
            "best_for": ["Social proof", "Customer stories", "Case studies"],
            "script_elements": ["Customer introduction", "Problem faced", "Solution provided", "Results achieved"]
        },
        {
            "value": "tutorial",
            "label": "Tutorial Video",
            "description": "Step-by-step instructional content",
            "typical_duration": "5-15 minutes",
            "best_for": ["Skill development", "Process training", "Software tutorials"],
            "script_elements": ["Overview", "Prerequisites", "Step-by-step instructions", "Practice exercises"]
        },
        {
            "value": "storytelling",
            "label": "Storytelling Video",
            "description": "Narrative content that tells a compelling story",
            "typical_duration": "3-10 minutes",
            "best_for": ["Brand stories", "Personal experiences", "Case studies"],
            "script_elements": ["Character introduction", "Conflict/problem", "Journey", "Resolution"]
        },
        {
            "value": "interview",
            "label": "Interview Video",
            "description": "Conversational content with experts or customers",
            "typical_duration": "10-30 minutes",
            "best_for": ["Expert insights", "Customer interviews", "Panel discussions"],
            "script_elements": ["Introduction", "Background questions", "Main discussion", "Conclusion"]
        }
    ]
    
    return {
        "status": "success",
        "data": video_types,
        "message": f"Retrieved {len(video_types)} video types"
    }

@router.get("/podcast-types")
async def get_podcast_types():
    """Get available podcast types for scripting"""
    podcast_types = [
        {
            "value": "educational",
            "label": "Educational Podcast",
            "description": "Informative content that teaches listeners",
            "typical_duration": "20-45 minutes",
            "best_for": ["Skill development", "Industry insights", "Academic topics"],
            "script_elements": ["Introduction", "Main concepts", "Examples", "Key takeaways"]
        },
        {
            "value": "interview",
            "label": "Interview Podcast",
            "description": "Conversations with guests and experts",
            "typical_duration": "30-60 minutes",
            "best_for": ["Expert insights", "Industry leaders", "Success stories"],
            "script_elements": ["Guest introduction", "Background questions", "Main discussion", "Conclusion"]
        },
        {
            "value": "storytelling",
            "label": "Storytelling Podcast",
            "description": "Narrative content that tells compelling stories",
            "typical_duration": "15-40 minutes",
            "best_for": ["Personal experiences", "Case studies", "Brand stories"],
            "script_elements": ["Hook", "Character introduction", "Story development", "Resolution"]
        },
        {
            "value": "news_analysis",
            "label": "News Analysis Podcast",
            "description": "Current events and news commentary",
            "typical_duration": "15-30 minutes",
            "best_for": ["Current events", "Industry news", "Market analysis"],
            "script_elements": ["Headlines", "Background context", "Analysis", "Implications"]
        },
        {
            "value": "conversational",
            "label": "Conversational Podcast",
            "description": "Casual discussions between hosts",
            "typical_duration": "30-90 minutes",
            "best_for": ["Entertainment", "Casual discussions", "Community building"],
            "script_elements": ["Topic introduction", "Discussion points", "Audience interaction", "Wrap-up"]
        },
        {
            "value": "q_and_a",
            "label": "Q&A Podcast",
            "description": "Answering listener questions and concerns",
            "typical_duration": "20-40 minutes",
            "best_for": ["Audience engagement", "Problem solving", "Expert advice"],
            "script_elements": ["Question introduction", "Background context", "Answer", "Additional resources"]
        }
    ]
    
    return {
        "status": "success",
        "data": podcast_types,
        "message": f"Retrieved {len(podcast_types)} podcast types"
    }

@router.get("/scripting-tips")
async def get_scripting_tips():
    """Get comprehensive scripting tips and best practices"""
    scripting_tips = {
        "video_scripting": {
            "structure": [
                "Start with a compelling hook (first 10 seconds)",
                "Use clear, concise language",
                "Include visual descriptions and camera directions",
                "End with a strong call-to-action"
            ],
            "pacing": [
                "Vary sentence length for natural rhythm",
                "Include pauses for visual transitions",
                "Use active voice and present tense",
                "Keep paragraphs short for readability"
            ],
            "engagement": [
                "Ask questions to involve viewers",
                "Use storytelling techniques",
                "Include humor where appropriate",
                "Create emotional connections"
            ]
        },
        "podcast_scripting": {
            "conversation": [
                "Write for speaking, not reading",
                "Use natural language and contractions",
                "Include conversation starters",
                "Plan for guest interactions"
            ],
            "flow": [
                "Create smooth transitions between topics",
                "Use signposts to guide listeners",
                "Include recap sections for long episodes",
                "Plan natural breaks and segments"
            ],
            "audience_connection": [
                "Address listeners directly",
                "Include personal anecdotes",
                "Use inclusive language",
                "Create community feeling"
            ]
        },
        "general_tips": {
            "research": [
                "Research your topic thoroughly",
                "Understand your target audience",
                "Study successful examples in your genre",
                "Keep up with industry trends"
            ],
            "revision": [
                "Read your script aloud",
                "Get feedback from others",
                "Edit for clarity and conciseness",
                "Practice timing and pacing"
            ],
            "production": [
                "Plan for post-production needs",
                "Include technical notes and cues",
                "Consider accessibility requirements",
                "Prepare backup content"
            ]
        }
    }
    
    return {
        "status": "success",
        "data": scripting_tips,
        "message": "Retrieved comprehensive scripting tips and best practices"
    }

@router.get("/enhancement-types")
async def get_enhancement_types():
    """Get available enhancement types for scripts"""
    enhancement_types = [
        {
            "value": "add_transitions",
            "label": "Add Transitions",
            "description": "Include smooth transitions between sections",
            "parameters": {
                "transition_style": ["smooth", "energetic", "professional", "casual"],
                "frequency": ["minimal", "moderate", "frequent"]
            }
        },
        {
            "value": "improve_hooks",
            "label": "Improve Hooks",
            "description": "Enhance opening sections for better engagement",
            "parameters": {
                "hook_type": ["question", "story", "statistic", "problem", "benefit"],
                "target_audience": ["beginners", "intermediate", "advanced", "general"]
            }
        },
        {
            "value": "add_call_to_action",
            "label": "Add Call-to-Action",
            "description": "Include compelling call-to-action elements",
            "parameters": {
                "cta_type": ["subscribe", "download", "contact", "purchase", "share"],
                "placement": ["beginning", "middle", "end", "throughout"]
            }
        },
        {
            "value": "optimize_pacing",
            "label": "Optimize Pacing",
            "description": "Adjust script pacing for better engagement",
            "parameters": {
                "target_duration": ["shorter", "longer", "maintain current"],
                "pacing_style": ["fast", "balanced", "slow", "varied"]
            }
        }
    ]
    
    return {
        "status": "success",
        "data": enhancement_types,
        "message": f"Retrieved {len(enhancement_types)} enhancement types"
    }
