from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from ..services.seo_optimization_service import SEOOptimizationService
from ..models import ContentType, PlatformType
from ..database import get_shakes_database

router = APIRouter()

# Pydantic models for request/response
class SEOOptimizationRequest(BaseModel):
    target_keywords: List[str] = Field(..., min_items=1, max_items=20, description="Target keywords for optimization")
    content_type: str = Field(..., description="Type of content being optimized")
    platform: str = Field(..., description="Platform where content will be published")

class KeywordStrategyRequest(BaseModel):
    topic: str = Field(..., description="Main topic for keyword research")
    industry: str = Field(..., description="Industry or business sector")
    target_audience: str = Field(..., description="Target audience for the content")
    content_type: str = Field(..., description="Type of content being created")

class ContentSEOAnalysisRequest(BaseModel):
    content: str = Field(..., description="Content to analyze for SEO")
    target_keywords: List[str] = Field(..., min_items=1, max_items=20, description="Target keywords for analysis")

class LocalizedSEORequest(BaseModel):
    content: str = Field(..., description="Content to localize")
    target_keywords: List[str] = Field(..., min_items=1, max_items=20, description="Target keywords for localization")
    location: str = Field(..., description="Target location for localization")
    language: str = Field(..., description="Target language for localization")

class SEOOptimizationResponse(BaseModel):
    optimized_content: str
    seo_analysis: Dict[str, Any]
    optimization_tips: List[str]
    timestamp: str

class KeywordStrategyResponse(BaseModel):
    keyword_strategy: str
    longtail_keywords: List[str]
    semantic_keywords: List[str]
    keyword_difficulty_analysis: Dict[str, Any]
    content_optimization_tips: List[str]
    timestamp: str

class ContentSEOAnalysisResponse(BaseModel):
    seo_metrics: Dict[str, Any]
    optimization_recommendations: List[str]
    keyword_opportunities: List[str]
    timestamp: str

class LocalizedSEOResponse(BaseModel):
    localized_keywords: List[str]
    localized_content: str
    local_schema_markup: str
    local_seo_tips: List[str]
    timestamp: str

# Dependency
async def get_seo_optimization_service() -> SEOOptimizationService:
    service = SEOOptimizationService()
    await service.initialize()
    return service

@router.post("/{content_piece_id}/optimize", response_model=Dict[str, Any])
async def optimize_content_seo(
    content_piece_id: int,
    request: SEOOptimizationRequest,
    service: SEOOptimizationService = Depends(get_seo_optimization_service)
):
    """Optimize content for SEO with target keywords"""
    try:
        result = await service.optimize_content_seo(
            content_piece_id=content_piece_id,
            target_keywords=request.target_keywords,
            content_type=request.content_type,
            platform=request.platform
        )
        
        if result["success"]:
            return {
                "status": "success",
                "message": f"Content optimized for SEO with {len(request.target_keywords)} keywords",
                "data": {
                    "optimized_content": result["optimized_content"],
                    "seo_analysis": result["seo_analysis"],
                    "optimization_tips": result["optimization_tips"],
                    "timestamp": result["timestamp"]
                }
            }
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/keyword-strategy", response_model=Dict[str, Any])
async def generate_keyword_strategy(
    request: KeywordStrategyRequest,
    service: SEOOptimizationService = Depends(get_seo_optimization_service)
):
    """Generate comprehensive keyword strategy for content"""
    try:
        result = await service.generate_keyword_strategy(
            topic=request.topic,
            industry=request.industry,
            target_audience=request.target_audience,
            content_type=request.content_type
        )
        
        if result["success"]:
            return {
                "status": "success",
                "message": "Keyword strategy generated successfully",
                "data": {
                    "keyword_strategy": result["keyword_strategy"],
                    "longtail_keywords": result["longtail_keywords"],
                    "semantic_keywords": result["semantic_keywords"],
                    "keyword_difficulty_analysis": result["keyword_difficulty_analysis"],
                    "content_optimization_tips": result["content_optimization_tips"],
                    "timestamp": result["timestamp"]
                }
            }
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze", response_model=Dict[str, Any])
async def analyze_content_seo(
    request: ContentSEOAnalysisRequest,
    service: SEOOptimizationService = Depends(get_seo_optimization_service)
):
    """Analyze content for SEO performance"""
    try:
        result = await service.analyze_content_seo(
            content=request.content,
            target_keywords=request.target_keywords
        )
        
        if result["success"]:
            return {
                "status": "success",
                "message": "Content SEO analysis completed successfully",
                "data": {
                    "seo_metrics": result["seo_metrics"],
                    "optimization_recommendations": result["optimization_recommendations"],
                    "keyword_opportunities": result["keyword_opportunities"],
                    "timestamp": result["timestamp"]
                }
            }
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/localize", response_model=Dict[str, Any])
async def generate_localized_seo(
    request: LocalizedSEORequest,
    service: SEOOptimizationService = Depends(get_seo_optimization_service)
):
    """Generate localized SEO optimization for regional markets"""
    try:
        result = await service.generate_localized_seo(
            content=request.content,
            target_keywords=request.target_keywords,
            location=request.location,
            language=request.language
        )
        
        if result["success"]:
            return {
                "status": "success",
                "message": f"Localized SEO generated for {request.location} in {request.language}",
                "data": {
                    "localized_keywords": result["localized_keywords"],
                    "localized_content": result["localized_content"],
                    "local_schema_markup": result["local_schema_markup"],
                    "local_seo_tips": result["local_seo_tips"],
                    "timestamp": result["timestamp"]
                }
            }
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/seo-tools")
async def get_seo_tools():
    """Get list of recommended SEO tools and resources"""
    seo_tools = [
        {
            "category": "Keyword Research",
            "tools": [
                {
                    "name": "Google Keyword Planner",
                    "description": "Free keyword research tool from Google Ads",
                    "features": ["Search volume", "Competition", "Keyword ideas"],
                    "cost": "Free",
                    "best_for": "Basic keyword research and planning"
                },
                {
                    "name": "Ahrefs",
                    "description": "Comprehensive SEO tool with keyword research",
                    "features": ["Keyword difficulty", "Search volume", "Competitor analysis"],
                    "cost": "Paid",
                    "best_for": "Advanced keyword research and competitive analysis"
                },
                {
                    "name": "SEMrush",
                    "description": "All-in-one SEO and marketing platform",
                    "features": ["Keyword research", "Site audit", "Position tracking"],
                    "cost": "Paid",
                    "best_for": "Comprehensive SEO management"
                }
            ]
        },
        {
            "category": "Content Optimization",
            "tools": [
                {
                    "name": "Yoast SEO",
                    "description": "WordPress plugin for on-page SEO",
                    "features": ["Readability analysis", "SEO scoring", "Meta optimization"],
                    "cost": "Free/Paid",
                    "best_for": "WordPress content optimization"
                },
                {
                    "name": "Grammarly",
                    "description": "Writing assistant with SEO features",
                    "features": ["Grammar check", "Readability score", "Writing suggestions"],
                    "cost": "Free/Paid",
                    "best_for": "Content quality and readability"
                },
                {
                    "name": "Clearscope",
                    "description": "AI-powered content optimization platform",
                    "features": ["Content grading", "Keyword optimization", "Competitor analysis"],
                    "cost": "Paid",
                    "best_for": "Advanced content optimization"
                }
            ]
        },
        {
            "category": "Technical SEO",
            "tools": [
                {
                    "name": "Google Search Console",
                    "description": "Free tool for monitoring search performance",
                    "features": ["Search analytics", "Indexing status", "Mobile usability"],
                    "cost": "Free",
                    "best_for": "Search performance monitoring"
                },
                {
                    "name": "Screaming Frog",
                    "description": "Technical SEO audit tool",
                    "features": ["Site crawling", "Technical issues", "SEO audit"],
                    "cost": "Free/Paid",
                    "best_for": "Technical SEO analysis"
                },
                {
                    "name": "GTmetrix",
                    "description": "Website performance and speed testing",
                    "features": ["Page speed", "Performance scores", "Optimization suggestions"],
                    "cost": "Free/Paid",
                    "best_for": "Page speed optimization"
                }
            ]
        }
    ]
    
    return {
        "status": "success",
        "data": seo_tools,
        "message": f"Retrieved {len(seo_tools)} SEO tool categories"
    }

@router.get("/seo-best-practices")
async def get_seo_best_practices():
    """Get comprehensive SEO best practices guide"""
    best_practices = {
        "on_page_seo": {
            "title_tags": [
                "Keep titles under 60 characters",
                "Include primary keyword near the beginning",
                "Make titles compelling and click-worthy",
                "Avoid keyword stuffing"
            ],
            "meta_descriptions": [
                "Keep descriptions under 160 characters",
                "Include primary and secondary keywords",
                "Add call-to-action when appropriate",
                "Make descriptions unique for each page"
            ],
            "headings": [
                "Use H1 for main page title only",
                "Use H2 for main sections",
                "Use H3 for subsections",
                "Include keywords in headings naturally"
            ],
            "content": [
                "Create high-quality, valuable content",
                "Use proper keyword density (1-2%)",
                "Include internal and external links",
                "Optimize images with alt text"
            ]
        },
        "technical_seo": {
            "site_speed": [
                "Optimize image sizes and formats",
                "Minimize CSS and JavaScript",
                "Use browser caching",
                "Enable compression"
            ],
            "mobile_friendly": [
                "Use responsive design",
                "Test mobile usability",
                "Optimize for mobile-first indexing",
                "Ensure touch-friendly elements"
            ],
            "site_structure": [
                "Create logical URL structure",
                "Use XML sitemaps",
                "Implement breadcrumb navigation",
                "Fix broken links regularly"
            ]
        },
        "content_seo": {
            "keyword_research": [
                "Research relevant, high-intent keywords",
                "Use long-tail keyword variations",
                "Analyze keyword difficulty and competition",
                "Consider user search intent"
            ],
            "content_optimization": [
                "Write for users first, search engines second",
                "Create comprehensive, authoritative content",
                "Update content regularly",
                "Use schema markup where appropriate"
            ],
            "internal_linking": [
                "Link related content together",
                "Use descriptive anchor text",
                "Create topic clusters",
                "Link to high-authority pages"
            ]
        }
    }
    
    return {
        "status": "success",
        "data": best_practices,
        "message": "Retrieved comprehensive SEO best practices guide"
    }

@router.get("/seo-metrics")
async def get_seo_metrics_explanation():
    """Get explanation of key SEO metrics and their importance"""
    seo_metrics = {
        "keyword_density": {
            "description": "Percentage of times a keyword appears in content relative to total word count",
            "optimal_range": "1-2% per keyword",
            "importance": "High - indicates topical relevance to search engines",
            "calculation": "Number of keyword occurrences / Total word count × 100"
        },
        "readability_score": {
            "description": "Flesch Reading Ease score indicating how easy content is to read",
            "optimal_range": "60-80 (easier to read)",
            "importance": "Medium - affects user experience and engagement",
            "calculation": "206.835 - (1.015 × average sentence length) - (84.6 × average syllables per word)"
        },
        "seo_score": {
            "description": "Overall SEO optimization score based on multiple factors",
            "optimal_range": "80-100 (excellent)",
            "importance": "High - comprehensive measure of SEO effectiveness",
            "calculation": "Combined score from keyword optimization, content structure, readability, and technical factors"
        },
        "heading_structure": {
            "description": "Organization of content using H1, H2, H3 tags",
            "optimal_range": "1 H1, 2-5 H2, 5-15 H3 per page",
            "importance": "High - helps search engines understand content hierarchy",
            "calculation": "Count of each heading type and their keyword optimization"
        },
        "meta_optimization": {
            "description": "Effectiveness of title tags and meta descriptions",
            "optimal_range": "Title: 50-60 chars, Description: 150-160 chars",
            "importance": "High - affects click-through rates and search visibility",
            "calculation": "Length, keyword inclusion, and compelling nature of meta elements"
        }
    }
    
    return {
        "status": "success",
        "data": seo_metrics,
        "message": "Retrieved SEO metrics explanation and importance levels"
    }
