from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
from ..services.interactive_widgets_service import InteractiveWidgetsService
from ..models import ContentType, PlatformType, ToneType
from ..database import get_shakes_database

router = APIRouter(prefix="/interactive-widgets", tags=["Interactive Widgets"])

# Pydantic Models
class CreateInteractiveWidgetRequest(BaseModel):
    content_piece_id: int = Field(..., description="Content piece ID")
    widget_type: str = Field(..., description="Widget type")
    widget_config: Dict[str, Any] = Field(..., description="Widget configuration")
    placement_options: Dict[str, Any] = Field(default={}, description="Placement options")

class EmbedWidgetRequest(BaseModel):
    widget_id: int = Field(..., description="Widget ID")
    target_platform: str = Field(..., description="Target platform")
    embedding_options: Dict[str, Any] = Field(default={}, description="Embedding options")

class AnalyzeWidgetPerformanceRequest(BaseModel):
    widget_id: int = Field(..., description="Widget ID")
    analysis_period_days: int = Field(default=30, description="Analysis period in days")
    performance_metrics: List[str] = Field(default=[], description="Performance metrics")

class OptimizeWidgetRequest(BaseModel):
    widget_id: int = Field(..., description="Widget ID")
    optimization_goals: List[str] = Field(..., description="Optimization goals")
    target_metrics: Dict[str, Any] = Field(default={}, description="Target metrics")

# Dependency
async def get_interactive_widgets_service() -> InteractiveWidgetsService:
    """Get interactive widgets service instance"""
    service = InteractiveWidgetsService()
    await service.initialize()
    return service

# Endpoints
@router.post("/create", response_model=Dict[str, Any], status_code=201)
async def create_interactive_widget(
    request: CreateInteractiveWidgetRequest,
    service: InteractiveWidgetsService = Depends(get_interactive_widgets_service)
):
    """Create interactive widget for content"""
    try:
        result = await service.create_interactive_widget(
            content_piece_id=request.content_piece_id,
            widget_type=request.widget_type,
            widget_config=request.widget_config,
            placement_options=request.placement_options
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to create interactive widget")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Interactive widget creation failed: {str(e)}"
        )

@router.post("/embed", response_model=Dict[str, Any], status_code=200)
async def embed_widget(
    request: EmbedWidgetRequest,
    service: InteractiveWidgetsService = Depends(get_interactive_widgets_service)
):
    """Embed widget in target platform"""
    try:
        result = await service.embed_widget(
            widget_id=request.widget_id,
            target_platform=request.target_platform,
            embedding_options=request.embedding_options
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to embed widget")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Widget embedding failed: {str(e)}"
        )

@router.post("/analyze-performance", response_model=Dict[str, Any], status_code=200)
async def analyze_widget_performance(
    request: AnalyzeWidgetPerformanceRequest,
    service: InteractiveWidgetsService = Depends(get_interactive_widgets_service)
):
    """Analyze widget performance and engagement"""
    try:
        result = await service.analyze_widget_performance(
            widget_id=request.widget_id,
            analysis_period_days=request.analysis_period_days,
            performance_metrics=request.performance_metrics
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to analyze widget performance")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Widget performance analysis failed: {str(e)}"
        )

@router.post("/optimize", response_model=Dict[str, Any], status_code=200)
async def optimize_widget(
    request: OptimizeWidgetRequest,
    service: InteractiveWidgetsService = Depends(get_interactive_widgets_service)
):
    """Optimize widget for better performance"""
    try:
        result = await service.optimize_widget(
            widget_id=request.widget_id,
            optimization_goals=request.optimization_goals,
            target_metrics=request.target_metrics
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to optimize widget")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Widget optimization failed: {str(e)}"
        )

@router.get("/widget-types")
async def get_widget_types():
    """Get available widget types for content"""
    return {
        "widget_types": [
            {
                "id": "quiz",
                "name": "Quiz Widget",
                "description": "Interactive quiz for audience engagement",
                "features": ["multiple_choice", "scoring", "results_sharing", "customization"],
                "best_for": ["educational_content", "brand_awareness", "lead_generation"],
                "engagement_level": "high"
            },
            {
                "id": "poll",
                "name": "Poll Widget",
                "description": "Quick polls for audience feedback",
                "features": ["real_time_results", "voting_options", "result_visualization"],
                "best_for": ["audience_engagement", "feedback_collection", "interactive_content"],
                "engagement_level": "medium"
            },
            {
                "id": "calculator",
                "name": "Calculator Widget",
                "description": "Interactive calculators for utility",
                "features": ["custom_formulas", "input_validation", "result_formatting"],
                "best_for": ["financial_content", "health_content", "educational_tools"],
                "engagement_level": "high"
            },
            {
                "id": "survey",
                "name": "Survey Widget",
                "description": "Comprehensive surveys for data collection",
                "features": ["multiple_question_types", "conditional_logic", "data_export"],
                "best_for": ["market_research", "customer_feedback", "data_collection"],
                "engagement_level": "medium"
            },
            {
                "id": "countdown",
                "name": "Countdown Widget",
                "description": "Countdown timers for urgency",
                "features": ["custom_timing", "visual_styling", "event_triggers"],
                "best_for": ["promotions", "events", "limited_time_offers"],
                "engagement_level": "medium"
            },
            {
                "id": "social_proof",
                "name": "Social Proof Widget",
                "description": "Display social proof and testimonials",
                "features": ["testimonial_rotation", "social_media_integration", "customization"],
                "best_for": ["conversion_optimization", "trust_building", "social_validation"],
                "engagement_level": "low"
            }
        ]
    }

@router.get("/platform-integrations")
async def get_platform_integrations():
    """Get available platform integrations for widgets"""
    return {
        "platform_integrations": [
            {
                "id": "wordpress",
                "name": "WordPress",
                "description": "WordPress plugin integration",
                "features": ["shortcode_support", "theme_compatibility", "seo_optimization"],
                "embedding_method": "shortcode",
                "compatibility": "high"
            },
            {
                "id": "shopify",
                "name": "Shopify",
                "description": "Shopify app integration",
                "features": ["theme_integration", "product_showcase", "checkout_optimization"],
                "embedding_method": "liquid_template",
                "compatibility": "high"
            },
            {
                "id": "webflow",
                "name": "Webflow",
                "description": "Webflow custom code integration",
                "features": ["custom_code_embedding", "responsive_design", "interaction_triggers"],
                "embedding_method": "custom_code",
                "compatibility": "medium"
            },
            {
                "id": "squarespace",
                "name": "Squarespace",
                "description": "Squarespace code block integration",
                "features": ["code_block_embedding", "responsive_design", "seo_optimization"],
                "embedding_method": "code_block",
                "compatibility": "medium"
            },
            {
                "id": "email",
                "name": "Email Platforms",
                "description": "Email marketing platform integration",
                "features": ["html_embedding", "responsive_design", "tracking_support"],
                "embedding_method": "html_embed",
                "compatibility": "high"
            },
            {
                "id": "social_media",
                "name": "Social Media",
                "description": "Social media platform integration",
                "features": ["link_sharing", "preview_optimization", "engagement_tracking"],
                "embedding_method": "link_sharing",
                "compatibility": "medium"
            }
        ]
    }

@router.get("/performance-metrics")
async def get_performance_metrics():
    """Get available performance metrics for widgets"""
    return {
        "performance_metrics": [
            {
                "id": "engagement",
                "name": "Engagement Metrics",
                "description": "Widget engagement and interaction metrics",
                "metrics": ["interaction_rate", "completion_rate", "time_spent", "click_through_rate"],
                "measurement": "percentage_and_duration",
                "importance": "high"
            },
            {
                "id": "conversion",
                "name": "Conversion Metrics",
                "description": "Widget conversion and goal achievement metrics",
                "metrics": ["conversion_rate", "goal_completion", "revenue_impact", "lead_generation"],
                "measurement": "percentage_and_value",
                "importance": "high"
            },
            {
                "id": "user_behavior",
                "name": "User Behavior Metrics",
                "description": "User behavior and interaction patterns",
                "metrics": ["user_flow", "drop_off_points", "interaction_patterns", "return_visits"],
                "measurement": "behavioral_data",
                "importance": "medium"
            },
            {
                "id": "technical",
                "name": "Technical Metrics",
                "description": "Technical performance and reliability metrics",
                "metrics": ["load_time", "error_rate", "uptime", "mobile_compatibility"],
                "measurement": "technical_indicators",
                "importance": "medium"
            }
        ]
    }

@router.get("/optimization-goals")
async def get_optimization_goals():
    """Get available optimization goals for widgets"""
    return {
        "optimization_goals": [
            {
                "id": "engagement",
                "name": "Increase Engagement",
                "description": "Optimize widget for higher engagement rates",
                "target_metrics": ["interaction_rate", "completion_rate", "time_spent"],
                "optimization_strategies": ["improve_design", "enhance_interactivity", "optimize_content"]
            },
            {
                "id": "conversion",
                "name": "Improve Conversion",
                "description": "Optimize widget for better conversion rates",
                "target_metrics": ["conversion_rate", "goal_completion", "revenue_impact"],
                "optimization_strategies": ["streamline_flow", "improve_cta", "enhance_trust"]
            },
            {
                "id": "user_experience",
                "name": "Enhance User Experience",
                "description": "Optimize widget for better user experience",
                "target_metrics": ["user_satisfaction", "ease_of_use", "accessibility"],
                "optimization_strategies": ["improve_usability", "enhance_accessibility", "optimize_performance"]
            },
            {
                "id": "mobile_optimization",
                "name": "Mobile Optimization",
                "description": "Optimize widget for mobile devices",
                "target_metrics": ["mobile_engagement", "mobile_conversion", "mobile_usability"],
                "optimization_strategies": ["responsive_design", "touch_optimization", "mobile_performance"]
            }
        ]
    }

@router.get("/widget-templates")
async def get_widget_templates():
    """Get available widget templates for quick setup"""
    return {
        "widget_templates": [
            {
                "id": "lead_generation_quiz",
                "name": "Lead Generation Quiz",
                "description": "Quiz template for lead generation",
                "widget_type": "quiz",
                "features": ["lead_capture", "scoring", "results_sharing", "email_integration"],
                "use_cases": ["marketing_qualification", "customer_segmentation", "lead_nurturing"]
            },
            {
                "id": "product_recommendation",
                "name": "Product Recommendation",
                "description": "Interactive product recommendation tool",
                "widget_type": "calculator",
                "features": ["product_matching", "recommendation_engine", "purchase_links"],
                "use_cases": ["ecommerce", "product_discovery", "personalized_shopping"]
            },
            {
                "id": "brand_awareness_poll",
                "name": "Brand Awareness Poll",
                "description": "Poll template for brand awareness",
                "widget_type": "poll",
                "features": ["brand_questions", "result_sharing", "social_integration"],
                "use_cases": ["brand_research", "market_awareness", "social_engagement"]
            },
            {
                "id": "customer_satisfaction_survey",
                "name": "Customer Satisfaction Survey",
                "description": "Survey template for customer feedback",
                "widget_type": "survey",
                "features": ["satisfaction_metrics", "feedback_collection", "reporting"],
                "use_cases": ["customer_feedback", "service_improvement", "satisfaction_tracking"]
            }
        ]
    }
