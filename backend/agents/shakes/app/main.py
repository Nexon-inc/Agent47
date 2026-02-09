from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from .lifespan import create_app
from .routers import (
    blog_writing, social_media, seo_optimization, video_scripting, ad_copywriting,
    email_writing, website_content, content_repurposing, ai_generation, social_automation,
    grammar_refinement, plagiarism_detection, brand_voice, content_templates, content_calendar,
    content_collaboration, content_analytics, performance_forecasting, cms_integration,
    ethical_guidelines, mobile_preview, content_dna, storyboard_generator, voiceover_integration,
    sentiment_analyzer, interactive_widgets, content_localization, version_control,
    thumbnail_generator, accessibility_checker, content_remix, trend_planner, shakes_dashboard, shakes_chat
)

def build_app() -> FastAPI:
    app = create_app()
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.backend_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include core content creation routers
    app.include_router(blog_writing.router, prefix="/shakes/blog-writing", tags=["Blog Writing"])
    app.include_router(social_media.router, prefix="/shakes/social-media", tags=["Social Media Content"])
    app.include_router(seo_optimization.router, prefix="/shakes/seo-optimization", tags=["SEO Optimization"])
    app.include_router(video_scripting.router, prefix="/shakes/video-scripting", tags=["Video Scripting"])
    app.include_router(ad_copywriting.router, prefix="/shakes/ad-copywriting", tags=["Ad Copywriting"])
    
    # Include advanced content routers
    app.include_router(email_writing.router, prefix="/shakes/email-writing", tags=["Email Writing"])
    app.include_router(website_content.router, prefix="/shakes/website-content", tags=["Website Content"])
    app.include_router(content_repurposing.router, prefix="/shakes/content-repurposing", tags=["Content Repurposing"])
    app.include_router(ai_generation.router, prefix="/shakes/ai-generation", tags=["AI Content Generation"])
    app.include_router(social_automation.router, prefix="/shakes/social-automation", tags=["Social Media Automation"])
    
    # Include content quality routers
    app.include_router(grammar_refinement.router, prefix="/shakes/grammar-refinement", tags=["Grammar Refinement"])
    app.include_router(plagiarism_detection.router, prefix="/shakes/plagiarism-detection", tags=["Plagiarism Detection"])
    app.include_router(brand_voice.router, prefix="/shakes/brand-voice", tags=["Brand Voice"])
    app.include_router(content_templates.router, prefix="/shakes/content-templates", tags=["Content Templates"])
    
    # Include content management routers
    app.include_router(content_calendar.router, prefix="/shakes/content-calendar", tags=["Content Calendar"])
    app.include_router(content_collaboration.router, prefix="/shakes/content-collaboration", tags=["Content Collaboration"])
    app.include_router(content_analytics.router, prefix="/shakes/content-analytics", tags=["Content Analytics"])
    app.include_router(performance_forecasting.router, prefix="/shakes/performance-forecasting", tags=["Performance Forecasting"])
    
    # Include integration routers
    app.include_router(cms_integration.router, prefix="/shakes/cms-integration", tags=["CMS Integration"])
    app.include_router(ethical_guidelines.router, prefix="/shakes/ethical-guidelines", tags=["Ethical Guidelines"])
    app.include_router(mobile_preview.router, prefix="/shakes/mobile-preview", tags=["Mobile Preview"])
    
    # Include advanced feature routers
    app.include_router(content_dna.router, prefix="/shakes/content-dna", tags=["Content DNA"])
    app.include_router(storyboard_generator.router, prefix="/shakes/storyboard-generator", tags=["Storyboard Generator"])
    app.include_router(voiceover_integration.router, prefix="/shakes/voiceover-integration", tags=["Voiceover Integration"])
    app.include_router(sentiment_analyzer.router, prefix="/shakes/sentiment-analyzer", tags=["Sentiment Analyzer"])
    
    # Include interactive and localization routers
    app.include_router(interactive_widgets.router, prefix="/shakes/interactive-widgets", tags=["Interactive Widgets"])
    app.include_router(content_localization.router, prefix="/shakes/content-localization", tags=["Content Localization"])
    app.include_router(version_control.router, prefix="/shakes/version-control", tags=["Version Control"])
    app.include_router(thumbnail_generator.router, prefix="/shakes/thumbnail-generator", tags=["Thumbnail Generator"])
    
    # Include final feature routers
    app.include_router(accessibility_checker.router, prefix="/shakes/accessibility-checker", tags=["Accessibility Checker"])
    app.include_router(content_remix.router, prefix="/shakes/content-remix", tags=["Content Remix"])
    app.include_router(trend_planner.router, prefix="/shakes/trend-planner", tags=["Trend Planner"])
    
    # Include dashboard router
    app.include_router(shakes_dashboard.router)
    
    # Include chat router
    app.include_router(shakes_chat.router)
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint to verify Shakes is running"""
        return JSONResponse(
            status_code=200,
            content={
                "status": "healthy",
                "employee": "Shakes",
                "version": "1.0.0",
                "features": [
                    "blog_article_writing",
                    "social_media_content",
                    "seo_optimization",
                    "video_podcast_scripting",
                    "ad_copywriting",
                    "email_newsletter_writing",
                    "website_landing_page_content",
                    "content_repurposing",
                    "ai_powered_generation",
                    "social_media_automation",
                    "grammar_tone_refinement",
                    "plagiarism_detection",
                    "brand_voice_customization",
                    "content_templates",
                    "content_calendar",
                    "content_collaboration",
                    "performance_analytics",
                    "cms_integration",
                    "ethical_guidelines",
                    "mobile_preview",
                    "content_dna",
                    "storyboard_generator",
                    "voiceover_integration",
                    "sentiment_analyzer",
                    "interactive_widgets",
                    "content_localization",
                    "version_control",
                    "thumbnail_generator",
                    "accessibility_checker",
                    "content_remix",
                    "trend_planner"
                ],
                "message": "Shakes is running and ready to create amazing content!"
            }
        )
    
    # Root endpoint
    @app.get("/shakes")
    async def root():
        """Root endpoint with Shakes information"""
        return JSONResponse(
            status_code=200,
            content={
                "message": "Welcome to Shakes - AI Content Specialist",
                "employee": "Shakes",
                "version": "1.0.0",
                "description": "Your intelligent AI content creation specialist with AI-powered writing, SEO optimization, and multi-platform content generation",
                "docs": "/docs",
                "health": "/shakes/health",
                "features": "Blog writing, social media content, SEO optimization, video scripting, ad copywriting, email writing, website content, content repurposing, AI generation, and more!",
                "advanced_capabilities": [
                    "AI-Powered Content Generation",
                    "SEO Optimization & Keyword Integration",
                    "Social Media Content Automation",
                    "Grammar & Tone Refinement",
                    "Plagiarism Detection & Originality Checking",
                    "Brand Voice Customization",
                    "Content Templates & Workflows",
                    "Content Calendar & Scheduling",
                    "Collaboration & Version Control",
                    "Performance Analytics & Forecasting",
                    "CMS & Platform Integration",
                    "Multi-Language Content Creation",
                    "Accessibility & Compliance",
                    "Interactive Content Widgets",
                    "Content Localization & Cultural Adaptation"
                ]
            }
        )
    
    return app

app = build_app()

# Note: The main backend mounts this app; do not run a separate server here.