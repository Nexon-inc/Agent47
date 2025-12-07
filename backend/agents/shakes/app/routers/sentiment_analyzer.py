from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
from ..services.sentiment_analyzer_service import SentimentAnalyzerService
from ..models import ContentType, PlatformType, ToneType
from ..database import get_shakes_database

router = APIRouter(prefix="/sentiment-analyzer", tags=["Sentiment Analyzer"])

# Pydantic Models
class AnalyzeContentSentimentRequest(BaseModel):
    content_piece_id: int = Field(..., description="Content piece ID")
    analysis_depth: str = Field(default="comprehensive", description="Analysis depth")
    sentiment_categories: List[str] = Field(default=[], description="Sentiment categories")

class AnalyzeAudienceSentimentRequest(BaseModel):
    content_piece_id: int = Field(..., description="Content piece ID")
    audience_segments: List[str] = Field(..., description="Audience segments")
    sentiment_metrics: List[str] = Field(default=[], description="Sentiment metrics")

class OptimizeContentSentimentRequest(BaseModel):
    content_piece_id: int = Field(..., description="Content piece ID")
    target_sentiment: str = Field(..., description="Target sentiment")
    optimization_goals: List[str] = Field(..., description="Optimization goals")

class AnalyzeSentimentTrendsRequest(BaseModel):
    user_id: int = Field(..., description="User ID")
    time_period_days: int = Field(default=30, description="Time period in days")
    trend_categories: List[str] = Field(default=[], description="Trend categories")

# Dependency
async def get_sentiment_analyzer_service() -> SentimentAnalyzerService:
    """Get sentiment analyzer service instance"""
    service = SentimentAnalyzerService()
    await service.initialize()
    return service

# Endpoints
@router.post("/analyze-content", response_model=Dict[str, Any], status_code=200)
async def analyze_content_sentiment(
    request: AnalyzeContentSentimentRequest,
    service: SentimentAnalyzerService = Depends(get_sentiment_analyzer_service)
):
    """Analyze sentiment and emotional impact of content"""
    try:
        result = await service.analyze_content_sentiment(
            content_piece_id=request.content_piece_id,
            analysis_depth=request.analysis_depth,
            sentiment_categories=request.sentiment_categories
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to analyze content sentiment")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Content sentiment analysis failed: {str(e)}"
        )

@router.post("/analyze-audience", response_model=Dict[str, Any], status_code=200)
async def analyze_audience_sentiment(
    request: AnalyzeAudienceSentimentRequest,
    service: SentimentAnalyzerService = Depends(get_sentiment_analyzer_service)
):
    """Analyze how different audience segments might perceive content"""
    try:
        result = await service.analyze_audience_sentiment(
            content_piece_id=request.content_piece_id,
            audience_segments=request.audience_segments,
            sentiment_metrics=request.sentiment_metrics
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to analyze audience sentiment")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Audience sentiment analysis failed: {str(e)}"
        )

@router.post("/optimize-sentiment", response_model=Dict[str, Any], status_code=200)
async def optimize_content_sentiment(
    request: OptimizeContentSentimentRequest,
    service: SentimentAnalyzerService = Depends(get_sentiment_analyzer_service)
):
    """Optimize content sentiment for specific goals"""
    try:
        result = await service.optimize_content_sentiment(
            content_piece_id=request.content_piece_id,
            target_sentiment=request.target_sentiment,
            optimization_goals=request.optimization_goals
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to optimize content sentiment")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Content sentiment optimization failed: {str(e)}"
        )

@router.post("/analyze-trends", response_model=Dict[str, Any], status_code=200)
async def analyze_sentiment_trends(
    request: AnalyzeSentimentTrendsRequest,
    service: SentimentAnalyzerService = Depends(get_sentiment_analyzer_service)
):
    """Analyze sentiment trends across user's content"""
    try:
        result = await service.analyze_sentiment_trends(
            user_id=request.user_id,
            time_period_days=request.time_period_days,
            trend_categories=request.trend_categories
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to analyze sentiment trends")
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Sentiment trend analysis failed: {str(e)}"
        )

@router.get("/sentiment-categories")
async def get_sentiment_categories():
    """Get available sentiment categories for analysis"""
    return {
        "sentiment_categories": [
            {
                "id": "overall",
                "name": "Overall Sentiment",
                "description": "General sentiment analysis of the content",
                "metrics": ["positive", "negative", "neutral"],
                "importance": "high"
            },
            {
                "id": "emotional_tone",
                "name": "Emotional Tone",
                "description": "Analysis of emotional tone and mood",
                "metrics": ["joy", "sadness", "anger", "fear", "surprise", "disgust"],
                "importance": "high"
            },
            {
                "id": "audience_impact",
                "name": "Audience Impact",
                "description": "Predicted impact on target audience",
                "metrics": ["engagement_likelihood", "emotional_response", "action_intent"],
                "importance": "high"
            },
            {
                "id": "brand_alignment",
                "name": "Brand Alignment",
                "description": "Alignment with brand values and voice",
                "metrics": ["brand_consistency", "value_alignment", "voice_match"],
                "importance": "medium"
            },
            {
                "id": "persuasion",
                "name": "Persuasion Elements",
                "description": "Analysis of persuasive elements",
                "metrics": ["credibility", "appeal", "call_to_action_strength"],
                "importance": "medium"
            },
            {
                "id": "clarity",
                "name": "Message Clarity",
                "description": "Clarity and understanding of the message",
                "metrics": ["readability", "comprehension", "message_clarity"],
                "importance": "medium"
            }
        ]
    }

@router.get("/analysis-depths")
async def get_analysis_depths():
    """Get available analysis depths for sentiment analysis"""
    return {
        "analysis_depths": [
            {
                "id": "basic",
                "name": "Basic Analysis",
                "description": "Quick sentiment analysis with key metrics",
                "features": ["overall_sentiment", "basic_emotions", "simple_insights"],
                "processing_time": "fast",
                "best_for": ["quick_checks", "bulk_analysis", "real_time_processing"]
            },
            {
                "id": "comprehensive",
                "name": "Comprehensive Analysis",
                "description": "Detailed sentiment analysis with multiple dimensions",
                "features": ["detailed_emotions", "audience_impact", "brand_alignment", "insights"],
                "processing_time": "medium",
                "best_for": ["content_optimization", "strategy_planning", "quality_assurance"]
            },
            {
                "id": "advanced",
                "name": "Advanced Analysis",
                "description": "Deep sentiment analysis with predictive insights",
                "features": ["predictive_insights", "trend_analysis", "optimization_recommendations", "detailed_reporting"],
                "processing_time": "slow",
                "best_for": ["strategic_planning", "research", "comprehensive_analysis"]
            }
        ]
    }

@router.get("/audience-segments")
async def get_audience_segments():
    """Get common audience segments for sentiment analysis"""
    return {
        "audience_segments": [
            {
                "id": "demographics",
                "name": "Demographics",
                "description": "Age, gender, and demographic-based segments",
                "segments": ["age_groups", "gender", "location", "education_level"],
                "analysis_focus": "demographic_preferences_and_behavior"
            },
            {
                "id": "psychographics",
                "name": "Psychographics",
                "description": "Personality, values, and lifestyle-based segments",
                "segments": ["personality_types", "values", "lifestyle", "interests"],
                "analysis_focus": "psychological_preferences_and_motivations"
            },
            {
                "id": "behavioral",
                "name": "Behavioral",
                "description": "Behavior and engagement-based segments",
                "segments": ["engagement_level", "content_preferences", "platform_usage", "purchase_behavior"],
                "analysis_focus": "behavioral_patterns_and_preferences"
            },
            {
                "id": "professional",
                "name": "Professional",
                "description": "Professional and industry-based segments",
                "segments": ["industry", "job_role", "company_size", "experience_level"],
                "analysis_focus": "professional_context_and_requirements"
            }
        ]
    }

@router.get("/sentiment-metrics")
async def get_sentiment_metrics():
    """Get available sentiment metrics for analysis"""
    return {
        "sentiment_metrics": [
            {
                "id": "emotional_response",
                "name": "Emotional Response",
                "description": "Predicted emotional response to content",
                "measurement": "emotional_intensity_and_type",
                "scale": "0-100",
                "interpretation": "higher_scores_indicate_stronger_emotional_impact"
            },
            {
                "id": "engagement_likelihood",
                "name": "Engagement Likelihood",
                "description": "Likelihood of audience engagement",
                "measurement": "probability_of_engagement",
                "scale": "0-100",
                "interpretation": "higher_scores_indicate_greater_engagement_potential"
            },
            {
                "id": "brand_perception",
                "name": "Brand Perception",
                "description": "Impact on brand perception",
                "measurement": "brand_sentiment_change",
                "scale": "-100_to_100",
                "interpretation": "positive_scores_improve_brand_perception"
            },
            {
                "id": "action_intent",
                "name": "Action Intent",
                "description": "Likelihood of desired action",
                "measurement": "action_probability",
                "scale": "0-100",
                "interpretation": "higher_scores_indicate_greater_action_likelihood"
            },
            {
                "id": "message_clarity",
                "name": "Message Clarity",
                "description": "Clarity and understanding of message",
                "measurement": "comprehension_score",
                "scale": "0-100",
                "interpretation": "higher_scores_indicate_clearer_messaging"
            }
        ]
    }

@router.get("/target-sentiments")
async def get_target_sentiments():
    """Get available target sentiments for optimization"""
    return {
        "target_sentiments": [
            {
                "id": "positive",
                "name": "Positive",
                "description": "Optimize for positive sentiment and emotions",
                "characteristics": ["uplifting", "optimistic", "encouraging", "inspiring"],
                "best_for": ["brand_building", "customer_satisfaction", "motivational_content"]
            },
            {
                "id": "neutral",
                "name": "Neutral",
                "description": "Optimize for balanced, neutral sentiment",
                "characteristics": ["objective", "informative", "balanced", "professional"],
                "best_for": ["educational_content", "news", "technical_documentation"]
            },
            {
                "id": "urgent",
                "name": "Urgent",
                "description": "Optimize for urgency and action",
                "characteristics": ["time_sensitive", "action_oriented", "compelling", "direct"],
                "best_for": ["promotions", "calls_to_action", "limited_time_offers"]
            },
            {
                "id": "trustworthy",
                "name": "Trustworthy",
                "description": "Optimize for trust and credibility",
                "characteristics": ["reliable", "credible", "authoritative", "transparent"],
                "best_for": ["brand_trust", "product_recommendations", "expert_content"]
            },
            {
                "id": "empathetic",
                "name": "Empathetic",
                "description": "Optimize for empathy and understanding",
                "characteristics": ["understanding", "compassionate", "supportive", "relatable"],
                "best_for": ["customer_support", "personal_stories", "emotional_connection"]
            }
        ]
    }

@router.get("/sentiment-insights")
async def get_sentiment_insights():
    """Get insights and recommendations for sentiment analysis"""
    return {
        "sentiment_insights": [
            {
                "category": "content_optimization",
                "title": "Content Optimization",
                "insights": [
                    "Optimize content tone for target audience preferences",
                    "Adjust emotional elements to improve engagement",
                    "Enhance message clarity for better comprehension",
                    "Align content sentiment with brand values",
                    "Improve persuasive elements for better conversion"
                ]
            },
            {
                "category": "audience_engagement",
                "title": "Audience Engagement",
                "insights": [
                    "Understand audience emotional preferences",
                    "Optimize content for different audience segments",
                    "Improve emotional connection with content",
                    "Enhance audience response and engagement",
                    "Develop audience-specific content strategies"
                ]
            },
            {
                "category": "brand_development",
                "title": "Brand Development",
                "insights": [
                    "Maintain consistent brand sentiment across content",
                    "Develop authentic brand voice and personality",
                    "Build trust and credibility through content",
                    "Enhance brand perception and reputation",
                    "Create emotional brand connections"
                ]
            },
            {
                "category": "performance_improvement",
                "title": "Performance Improvement",
                "insights": [
                    "Optimize content for better performance metrics",
                    "Improve conversion rates through sentiment optimization",
                    "Enhance audience retention and loyalty",
                    "Increase content sharing and virality",
                    "Improve overall content effectiveness"
                ]
            }
        ]
    }
