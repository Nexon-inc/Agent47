from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import sys
import os

# Add the backend directory to Python path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

try:
    from .lifespan import create_app
    from .routers import (
        scheduling, nlp, content, analytics, webhooks, brand, trends, media,
        engagement, approvals, ab_testing, groups, ads, integrations, speech, oauth,
        content_remix, trend_alerts, voice_posts, accessibility, engagement_booster, advanced_analytics, geo_campaign, account_analysis, aria_chat, aria_dashboard
    )
except ImportError:
    # Fallback for direct execution
    from lifespan import create_app
    from routers import (
        scheduling, nlp, content, analytics, webhooks, brand, trends, media,
        engagement, approvals, ab_testing, groups, ads, integrations, speech, oauth,
        content_remix, trend_alerts, voice_posts, accessibility, engagement_booster, advanced_analytics, geo_campaign, account_analysis, aria_chat, aria_dashboard
    )


def build_app() -> FastAPI:
    app = create_app()
    
    # Core functionality routers
    app.include_router(scheduling.router)
    app.include_router(nlp.router)
    app.include_router(content.router)
    app.include_router(analytics.router)
    app.include_router(webhooks.router)
    app.include_router(brand.router)
    app.include_router(trends.router)
    app.include_router(media.router)
    app.include_router(engagement.router)
    app.include_router(approvals.router)
    app.include_router(ab_testing.router)
    app.include_router(groups.router)
    app.include_router(ads.router)
    app.include_router(integrations.router)
    app.include_router(speech.router)
    app.include_router(oauth.router)
    
    # Advanced feature routers
    app.include_router(content_remix.router)
    app.include_router(trend_alerts.router)
    app.include_router(voice_posts.router)
    app.include_router(accessibility.router)
    app.include_router(engagement_booster.router)
    app.include_router(advanced_analytics.router)
    app.include_router(geo_campaign.router)
    app.include_router(account_analysis.router)
    app.include_router(aria_chat.router)
    app.include_router(aria_dashboard.router)
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint to verify Aria is running"""
        return JSONResponse(
            status_code=200,
            content={
                "status": "healthy",
                "agent": "Aria",
                "version": "1.0.0",
                "features": [
                    "social_media_management",
                    "ai_content_creation",
                    "smart_scheduling",
                    "trend_monitoring",
                    "geo_campaigns",
                    "analytics",
                    "chat_interface",
                    "voice_interaction"
                ],
                "message": "Aria is running and ready to manage your social media presence!"
            }
        )
    
    @app.get("/")
    async def root():
        """Root endpoint with Aria information"""
        return JSONResponse(
            status_code=200,
            content={
                "message": "Welcome to Aria - AI-Powered Social Media Management",
                "agent": "Aria",
                "version": "1.0.0",
                "description": "Your intelligent, autonomous social media management partner",
                "docs": "/docs",
                "health": "/health",
                "features": "Multi-platform posting, AI content creation, smart scheduling, trend monitoring, geo-targeting, analytics, and more!"
            }
        )
    
    return app


app = build_app()

# Note: The main backend mounts this app; do not run a separate server here.
