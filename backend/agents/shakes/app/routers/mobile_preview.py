from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from ..services.mobile_preview_service import MobilePreviewService
from ..models import ContentType, PlatformType, ToneType
from ..database import get_shakes_database

router = APIRouter(prefix="/mobile-preview", tags=["Mobile Preview"])

# Pydantic Models
class GenerateMobilePreviewRequest(BaseModel):
    content_piece_id: int = Field(..., description="Content piece ID")
    device_types: List[str] = Field(default=[], description="Device types for preview")
    preview_options: Dict[str, Any] = Field(default={}, description="Preview options")

class OptimizeContentForMobileRequest(BaseModel):
    content_piece_id: int = Field(..., description="Content piece ID")
    optimization_goals: List[str] = Field(default=[], description="Optimization goals")

class AnalyzeMobilePerformanceRequest(BaseModel):
    content_piece_id: int = Field(..., description="Content piece ID")
    performance_metrics: List[str] = Field(default=[], description="Performance metrics")

class GenerateMobileMetadataRequest(BaseModel):
    content_piece_id: int = Field(..., description="Content piece ID")
    metadata_types: List[str] = Field(default=[], description="Metadata types")

# Dependency
async def get_mobile_preview_service() -> MobilePreviewService:
    """Get mobile preview service instance"""
    service = MobilePreviewService()
    await service.initialize()
    return service

# Endpoints
@router.post("/generate-preview", response_model=Dict[str, Any], status_code=200)
async def generate_mobile_preview(
    request: GenerateMobilePreviewRequest,
    service: MobilePreviewService = Depends(get_mobile_preview_service)
):
    """Generate mobile preview for content"""
    try:
        result = await service.generate_mobile_preview(
            content_piece_id=request.content_piece_id,
            device_types=request.device_types,
            preview_options=request.preview_options
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to generate mobile preview")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Mobile preview generation failed: {str(e)}"
        )

@router.post("/optimize-content", response_model=Dict[str, Any], status_code=200)
async def optimize_content_for_mobile(
    request: OptimizeContentForMobileRequest,
    service: MobilePreviewService = Depends(get_mobile_preview_service)
):
    """Optimize content for mobile devices"""
    try:
        result = await service.optimize_content_for_mobile(
            content_piece_id=request.content_piece_id,
            optimization_goals=request.optimization_goals
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to optimize content for mobile")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Mobile content optimization failed: {str(e)}"
        )

@router.post("/analyze-performance", response_model=Dict[str, Any], status_code=200)
async def analyze_mobile_performance(
    request: AnalyzeMobilePerformanceRequest,
    service: MobilePreviewService = Depends(get_mobile_preview_service)
):
    """Analyze mobile performance of content"""
    try:
        result = await service.analyze_mobile_performance(
            content_piece_id=request.content_piece_id,
            performance_metrics=request.performance_metrics
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to analyze mobile performance")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Mobile performance analysis failed: {str(e)}"
        )

@router.post("/generate-metadata", response_model=Dict[str, Any], status_code=200)
async def generate_mobile_metadata(
    request: GenerateMobileMetadataRequest,
    service: MobilePreviewService = Depends(get_mobile_preview_service)
):
    """Generate mobile-specific metadata"""
    try:
        result = await service.generate_mobile_metadata(
            content_piece_id=request.content_piece_id,
            metadata_types=request.metadata_types
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to generate mobile metadata")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Mobile metadata generation failed: {str(e)}"
        )

@router.get("/device-types")
async def get_device_types():
    """Get available device types for mobile preview"""
    return {
        "device_types": [
            {
                "id": "mobile",
                "name": "Mobile",
                "description": "Smartphone devices",
                "screen_sizes": ["320px", "375px", "414px", "480px"],
                "characteristics": [
                    "Touch interface",
                    "Small screen size",
                    "Portrait orientation",
                    "Limited bandwidth"
                ],
                "optimization_focus": ["readability", "touch_friendly", "fast_loading", "simplified_navigation"]
            },
            {
                "id": "tablet",
                "name": "Tablet",
                "description": "Tablet devices",
                "screen_sizes": ["768px", "1024px", "1366px"],
                "characteristics": [
                    "Touch interface",
                    "Medium screen size",
                    "Portrait and landscape",
                    "Better bandwidth"
                ],
                "optimization_focus": ["responsive_design", "touch_optimization", "content_layout", "interactive_elements"]
            },
            {
                "id": "mobile_landscape",
                "name": "Mobile Landscape",
                "description": "Mobile devices in landscape orientation",
                "screen_sizes": ["568px", "667px", "736px"],
                "characteristics": [
                    "Touch interface",
                    "Wide screen format",
                    "Landscape orientation",
                    "Limited height"
                ],
                "optimization_focus": ["horizontal_layout", "compact_design", "swipe_gestures", "efficient_space_use"]
            }
        ]
    }

@router.get("/mobile-optimization-goals")
async def get_mobile_optimization_goals():
    """Get available mobile optimization goals"""
    return {
        "mobile_optimization_goals": [
            {
                "id": "readability",
                "name": "Readability",
                "description": "Improve content readability on mobile devices",
                "techniques": [
                    "Optimize font sizes",
                    "Improve line spacing",
                    "Enhance contrast",
                    "Simplify language"
                ],
                "metrics": ["reading_time", "comprehension_score", "user_engagement"]
            },
            {
                "id": "performance",
                "name": "Performance",
                "description": "Optimize content performance on mobile devices",
                "techniques": [
                    "Reduce file sizes",
                    "Optimize images",
                    "Minimize HTTP requests",
                    "Use efficient code"
                ],
                "metrics": ["load_time", "page_speed", "bandwidth_usage"]
            },
            {
                "id": "engagement",
                "name": "Engagement",
                "description": "Increase user engagement on mobile devices",
                "techniques": [
                    "Interactive elements",
                    "Touch-friendly buttons",
                    "Swipe gestures",
                    "Mobile-specific features"
                ],
                "metrics": ["click_through_rate", "time_on_page", "interaction_rate"]
            },
            {
                "id": "accessibility",
                "name": "Accessibility",
                "description": "Ensure content is accessible on mobile devices",
                "techniques": [
                    "Screen reader compatibility",
                    "Voice control support",
                    "High contrast mode",
                    "Large touch targets"
                ],
                "metrics": ["accessibility_score", "usability_rating", "inclusive_design_score"]
            }
        ]
    }

@router.get("/mobile-performance-metrics")
async def get_mobile_performance_metrics():
    """Get available mobile performance metrics"""
    return {
        "mobile_performance_metrics": [
            {
                "id": "load_time",
                "name": "Load Time",
                "description": "Time taken for content to load on mobile devices",
                "measurement": "seconds",
                "target": "< 3 seconds",
                "factors": ["file_size", "network_speed", "server_response", "rendering_time"]
            },
            {
                "id": "readability",
                "name": "Readability",
                "description": "How easy content is to read on mobile devices",
                "measurement": "score (0-100)",
                "target": "> 80",
                "factors": ["font_size", "line_spacing", "contrast", "content_length"]
            },
            {
                "id": "engagement",
                "name": "Engagement",
                "description": "User interaction with content on mobile devices",
                "measurement": "percentage",
                "target": "> 70%",
                "factors": ["click_through_rate", "scroll_depth", "time_on_page", "interaction_rate"]
            },
            {
                "id": "accessibility",
                "name": "Accessibility",
                "description": "How accessible content is on mobile devices",
                "measurement": "score (0-100)",
                "target": "> 90",
                "factors": ["screen_reader_compatibility", "touch_target_size", "color_contrast", "keyboard_navigation"]
            },
            {
                "id": "usability",
                "name": "Usability",
                "description": "How easy content is to use on mobile devices",
                "measurement": "score (0-100)",
                "target": "> 85",
                "factors": ["navigation_ease", "content_findability", "user_satisfaction", "task_completion"]
            }
        ]
    }

@router.get("/mobile-metadata-types")
async def get_mobile_metadata_types():
    """Get available mobile metadata types"""
    return {
        "mobile_metadata_types": [
            {
                "id": "meta_tags",
                "name": "Meta Tags",
                "description": "HTML meta tags optimized for mobile",
                "examples": [
                    "viewport meta tag",
                    "mobile-optimized title",
                    "description meta tag",
                    "keywords meta tag"
                ],
                "purpose": "SEO and mobile optimization"
            },
            {
                "id": "open_graph",
                "name": "Open Graph",
                "description": "Open Graph tags for social media sharing",
                "examples": [
                    "og:title",
                    "og:description",
                    "og:image",
                    "og:url"
                ],
                "purpose": "Social media optimization"
            },
            {
                "id": "twitter_cards",
                "name": "Twitter Cards",
                "description": "Twitter Card metadata for enhanced tweets",
                "examples": [
                    "twitter:card",
                    "twitter:title",
                    "twitter:description",
                    "twitter:image"
                ],
                "purpose": "Twitter optimization"
            },
            {
                "id": "structured_data",
                "name": "Structured Data",
                "description": "Schema.org structured data for search engines",
                "examples": [
                    "Article schema",
                    "BreadcrumbList schema",
                    "Organization schema",
                    "WebPage schema"
                ],
                "purpose": "Search engine optimization"
            }
        ]
    }

@router.get("/mobile-optimization-tips")
async def get_mobile_optimization_tips():
    """Get tips for mobile content optimization"""
    return {
        "mobile_optimization_tips": [
            {
                "category": "content_structure",
                "title": "Content Structure",
                "tips": [
                    "Use short paragraphs for better readability",
                    "Include clear headings and subheadings",
                    "Break up long content with bullet points",
                    "Use white space effectively",
                    "Keep important information above the fold"
                ]
            },
            {
                "category": "visual_design",
                "title": "Visual Design",
                "tips": [
                    "Use large, readable fonts (16px minimum)",
                    "Ensure high contrast between text and background",
                    "Optimize images for mobile viewing",
                    "Use touch-friendly button sizes (44px minimum)",
                    "Implement responsive design principles"
                ]
            },
            {
                "category": "performance",
                "title": "Performance",
                "tips": [
                    "Compress images and use appropriate formats",
                    "Minimize HTTP requests",
                    "Use efficient CSS and JavaScript",
                    "Implement lazy loading for images",
                    "Optimize for 3G and 4G networks"
                ]
            },
            {
                "category": "user_experience",
                "title": "User Experience",
                "tips": [
                    "Design for thumb navigation",
                    "Implement swipe gestures where appropriate",
                    "Provide clear call-to-action buttons",
                    "Ensure forms are mobile-friendly",
                    "Test on actual mobile devices"
                ]
            }
        ]
    }
