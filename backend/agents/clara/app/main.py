from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from .lifespan import create_app
from .routers import (
    support, chatbot, voice, knowledge, analytics,
    predictive_analytics, gamified_performance, self_service_portal,
    proactive_chat, accessibility, offline_support, chat_widgets, geo_localization,
    crm_integration, social_media, customer_loyalty, multilingual,
    custom_response_templates, real_time_notifications, custom_workflows,
    multi_brand, customer_journey, proactive_notifications, agent_training,
    ai_faq_builder, predictive_issue_detection, multi_ticket_resolution,
    onboarding_assistance, setup_wizard, in_store_inquiry, mobile_app_monitoring, voice_sentiment_coaching,
    clara_dashboard, clara_chat
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
    
    # Include core routers
    app.include_router(support.router, prefix="/clara/support", tags=["Support"])
    app.include_router(chatbot.router, prefix="/clara/chatbot", tags=["Chatbot"])
    app.include_router(voice.router, prefix="/clara/voice", tags=["Voice"])
    app.include_router(knowledge.router, prefix="/clara/knowledge", tags=["Knowledge"])
    app.include_router(analytics.router, prefix="/clara/analytics", tags=["Analytics"])
    
    # Include advanced feature routers
    app.include_router(predictive_analytics.router, prefix="/clara/predictive", tags=["Predictive Analytics"])
    app.include_router(gamified_performance.router, prefix="/clara/gamified", tags=["Gamified Performance"])
    app.include_router(self_service_portal.router, prefix="/clara/portal", tags=["Self-Service Portal"])
    app.include_router(proactive_chat.router, prefix="/clara/proactive", tags=["Proactive Chat"])
    app.include_router(accessibility.router, prefix="/clara/accessibility", tags=["Accessibility"])
    app.include_router(offline_support.router, prefix="/clara/offline", tags=["Offline Support"])
    
    # Include new feature routers
    app.include_router(chat_widgets.router, prefix="/clara/chat-widgets", tags=["Chat Widgets"])
    app.include_router(geo_localization.router, prefix="/clara/geo-localization", tags=["Geo-Localization"])
    
    # Include additional feature routers
    app.include_router(crm_integration.router, prefix="/clara/crm", tags=["CRM Integration"])
    app.include_router(social_media.router, prefix="/clara/social", tags=["Social Media"])
    app.include_router(customer_loyalty.router, prefix="/clara/loyalty", tags=["Customer Loyalty"])
    app.include_router(multilingual.router, prefix="/clara/multilingual", tags=["Multilingual Support"])

    # Include high-priority feature routers
    app.include_router(custom_response_templates.router, prefix="/clara/templates", tags=["Custom Response Templates"])
    app.include_router(real_time_notifications.router, prefix="/clara/notifications", tags=["Real-Time Notifications"])
    app.include_router(custom_workflows.router, prefix="/clara/workflows", tags=["Custom Workflows"])
    app.include_router(multi_brand.router, prefix="/clara/multi-brand", tags=["Multi-ClaraBrand Support"])
    app.include_router(customer_journey.router, prefix="/clara/journey", tags=["Customer Journey Tracking"])

    # Include medium-priority feature routers
    app.include_router(proactive_notifications.router, prefix="/clara/proactive-notifications", tags=["Proactive Support Notifications"])
    app.include_router(agent_training.router, prefix="/clara/agent-training", tags=["Specialist Training Tools"])
    app.include_router(ai_faq_builder.router, prefix="/clara/ai-faq-builder", tags=["AI-Driven ClaraFAQ Builder"])
    app.include_router(predictive_issue_detection.router, prefix="/clara/predictive-issues", tags=["Predictive Issue Detection"])
    app.include_router(multi_ticket_resolution.router, prefix="/clara/multi-ticket-resolution", tags=["Multi-Ticket Resolution"])

    # Include low-priority feature routers
    app.include_router(onboarding_assistance.router, prefix="/clara/onboarding", tags=["Onboarding Assistance"])
    app.include_router(setup_wizard.router, prefix="/clara/setup-wizard", tags=["Setup Wizard"])
    app.include_router(in_store_inquiry.router, prefix="/clara/in-store", tags=["In-Store Inquiry Integration"])
    app.include_router(mobile_app_monitoring.router, prefix="/clara/mobile-app", tags=["Mobile App for Monitoring"])
    app.include_router(voice_sentiment_coaching.router, prefix="/clara/voice-sentiment", tags=["Voice Sentiment Coaching"])
    
    # Include dashboard router
    app.include_router(clara_dashboard.router)
    
    # Include chat router
    app.include_router(clara_chat.router)
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint to verify Clara is running"""
        return JSONResponse(
            status_code=200,
                "status": "healthy",
                "employee": "Clara",
                "version": "1.0.0",
                "features": [
                    "24_7_customer_support",
                    "multichannel_support",
                    "ai_chatbot",
                    "voice_support",
                    "ticket_management",
                    "knowledge_base",
                    "sentiment_analysis",
                    "automated_responses",
                    "human_handoff",
                    "ivr_support",
                    "predictive_analytics",
                    "gamified_performance",
                    "self_service_portal",
                    "proactive_chat",
                    "accessibility_support",
                    "offline_support",
                                              "customizable_chat_widgets",
                          "geo_targeting",
                          "multi_language_support",
                          "crm_integration",
                          "social_media_integration",
                          "customer_loyalty_program",
                          "trust_score_calculation",
                          "collaboration_inquiry_tracking",
                          "social_engagement_analytics",
                          "custom_response_templates",
                          "real_time_team_notifications",
                          "custom_ticketing_workflows",
                          "multi_brand_support",
                          "customer_journey_tracking",
                          "proactive_support_notifications",
                          "personnel_training_tools",
                          "ai_driven_faq_builder",
                          "predictive_issue_detection",
                          "multi_ticket_resolution",
                          "onboarding_assistance",
                          "setup_wizard",
                          "in_store_inquiry_integration",
                          "mobile_app_monitoring",
                          "voice_sentiment_coaching"
                ],
                "message": "Clara is running and ready to provide comprehensive customer support!"
            }
        )
    
    # Root endpoint
    @app.get("/clara")
    async def root():
        """Root endpoint with Clara information"""
        return JSONResponse(
            status_code=200,
            content={
                "message": "Welcome to Clara - AI Customer Support Specialist",
                "employee": "Clara",
                "version": "1.0.0",
                "description": "Your intelligent, 24/7 AI customer support specialist with advanced features",
                "docs": "/docs",
                "health": "/clara/health",
                "features": "24/7 support, AI chatbot, voice support, ticket management, knowledge base, sentiment analysis, predictive analytics, gamified performance, self-service portal, proactive chat, accessibility, offline support, customizable chat widgets, geo-targeting, multi-language support, and more!",
                "advanced_capabilities": [
                    "Predictive Analytics & Issue Detection",
                    "Gamified Specialist Performance",
                    "Self-Service Customer Portal",
                    "Proactive Chat Engagement",
                    "Accessibility & Screen Reader Support",
                    "Offline Support & Response Queuing",
                    "Customizable Chat Widgets for Websites & Apps",
                    "Geo-Targeting & Regional Support",
                    "Multi-Language Support & Localization",
                    "CRM Integration (Zendesk, Freshdesk, HubSpot, Salesforce)",
                    "Social Media Integration (Instagram, TikTok, Twitter, Facebook)",
                    "Customer Loyalty Program & Trust Scoring",
                    "ClaraBrand Collaboration Inquiry Tracking",
                    "Social Engagement Analytics & Prioritization"
                ]
            }
        )
    
    return app

app = build_app()

# Note: The main backend mounts this app; do not run a separate server here.

