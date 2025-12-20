from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from .lifespan import create_app
from .routers import (
    campaigns, content, seo, analytics, ads, social_media, email_marketing,
    influencer_marketing, market_research, customer_segmentation, ab_testing, crm_integration,
    customer_engagement, omnichannel, predictive_analytics, voice_video_marketing,
    agent_integration, brand_voice, localized_marketing, campaign_collaboration, campaign_calendar,
    campaign_ideation, accessibility, ecommerce_integration, ethical_guidelines,
    organic_marketing, mobile_campaign, deep_analytics, onboarding, interactive_elements,
    platform_optimization, launch_assistant, customer_search, human_chatbot, dynamic_personalization,
    performance_forecasting, budget_control, campaign_storyboard, influencer_tracking,
    dynamic_budget, influencer_roi_predictor, voice_ad_generator, geo_targeted,
    customer_feedback, ethical_ad_scanner, cross_channel_analytics, interactive_widgets,
    campaign_version_control, multi_language, enhanced_video_voice, jackie_dashboard, jackie_chat
)

def build_app() -> FastAPI:
    app = create_app()
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.backend_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    app.include_router(campaigns.router, prefix="/jackie/campaigns", tags=["Campaign Management"])
    app.include_router(content.router, prefix="/jackie/content", tags=["Content Creation"])
    app.include_router(seo.router, prefix="/jackie/seo", tags=["SEO Optimization"])
    app.include_router(analytics.router, prefix="/jackie/analytics", tags=["Analytics"])
    app.include_router(ads.router, prefix="/jackie/ads", tags=["Ad Management"])
    app.include_router(social_media.router, prefix="/jackie/social", tags=["Social Media"])
    app.include_router(email_marketing.router, prefix="/jackie/email", tags=["Email Marketing"])
    app.include_router(influencer_marketing.router, prefix="/jackie/influencer", tags=["Influencer Marketing"])
    app.include_router(market_research.router, prefix="/jackie/market-research", tags=["Market Research"])
    app.include_router(customer_segmentation.router, prefix="/jackie/customer-segmentation", tags=["Customer Segmentation"])
    app.include_router(ab_testing.router, prefix="/jackie/ab-testing", tags=["A/B Testing"])
    app.include_router(crm_integration.router, prefix="/jackie/crm-integration", tags=["CRM Integration"])
    app.include_router(customer_engagement.router, prefix="/jackie/customer-engagement", tags=["Customer Engagement"])
    app.include_router(omnichannel.router, prefix="/jackie/omnichannel", tags=["Omnichannel Marketing"])
    app.include_router(predictive_analytics.router, prefix="/jackie/predictive-analytics", tags=["Predictive Analytics"])
    app.include_router(voice_video_marketing.router, prefix="/jackie/voice-video", tags=["Voice & Video Marketing"])
    app.include_router(agent_integration.router, prefix="/jackie/agent-integration", tags=["Agent Integration"])
    app.include_router(brand_voice.router, prefix="/jackie/brand-voice", tags=["Brand Voice Customization"])
    app.include_router(localized_marketing.router, prefix="/jackie/localized-marketing", tags=["Localized Marketing"])
    app.include_router(campaign_collaboration.router, prefix="/jackie/campaign-collaboration", tags=["Campaign Collaboration"])
    app.include_router(campaign_calendar.router, prefix="/jackie/campaign-calendar", tags=["Campaign Calendar"])
    app.include_router(campaign_ideation.router, prefix="/jackie/campaign-ideation", tags=["AI Campaign Ideation"])
    app.include_router(accessibility.router, prefix="/jackie/accessibility", tags=["Accessibility Optimization"])
    app.include_router(ecommerce_integration.router, prefix="/jackie/ecommerce", tags=["E-commerce Integration"])
    app.include_router(ethical_guidelines.router, prefix="/jackie/ethical-guidelines", tags=["Ethical Guidelines"])
    app.include_router(organic_marketing.router, prefix="/jackie/organic-marketing", tags=["Organic Marketing"])
    app.include_router(mobile_campaign.router, prefix="/jackie/mobile-campaign", tags=["Mobile Campaign Management"])
    app.include_router(deep_analytics.router, prefix="/jackie/deep-analytics", tags=["Deep Campaign Analytics"])
    app.include_router(onboarding.router, prefix="/jackie/onboarding", tags=["Streamlined Onboarding"])
    app.include_router(interactive_elements.router, prefix="/jackie/interactive-elements", tags=["Interactive Campaign Elements"])
    app.include_router(platform_optimization.router, prefix="/jackie/platform-optimization", tags=["Platform-Specific Optimization"])
    app.include_router(launch_assistant.router, prefix="/jackie/launch-assistant", tags=["Launch Assistant"])
    app.include_router(customer_search.router, prefix="/jackie/customer-search", tags=["Customer Search"])
    app.include_router(human_chatbot.router, prefix="/jackie/human-chatbot", tags=["Human-Like Chatbot Responses"])
    app.include_router(dynamic_personalization.router, prefix="/jackie/dynamic-personalization", tags=["Dynamic Customer Personalization"])
    app.include_router(performance_forecasting.router, prefix="/jackie/performance-forecasting", tags=["Campaign Performance Forecasting"])
    app.include_router(budget_control.router, prefix="/jackie/budget-control", tags=["Real-Time Budget Control"])
    app.include_router(campaign_storyboard.router, prefix="/jackie/campaign-storyboard", tags=["AI Campaign Storyboard"])
    app.include_router(influencer_tracking.router, prefix="/jackie/influencer-tracking", tags=["Influencer Performance Tracking"])
    app.include_router(dynamic_budget.router, prefix="/jackie/dynamic-budget", tags=["Dynamic Budget Allocator"])
    app.include_router(influencer_roi_predictor.router, prefix="/jackie/influencer-roi-predictor", tags=["Influencer ROI Predictor"])
    app.include_router(voice_ad_generator.router, prefix="/jackie/voice-ad-generator", tags=["Voice Ad Generator"])
    app.include_router(geo_targeted.router, prefix="/jackie/geo-targeted", tags=["Geo-Targeted Ad Planner"])
    app.include_router(customer_feedback.router, prefix="/jackie/customer-feedback", tags=["Customer Feedback Loop"])
    app.include_router(ethical_ad_scanner.router, prefix="/jackie/ethical-ad-scanner", tags=["Ethical Ad Scanner"])
    app.include_router(cross_channel_analytics.router, prefix="/jackie/cross-channel-analytics", tags=["Cross-Channel Analytics"])
    app.include_router(interactive_widgets.router, prefix="/jackie/interactive-widgets", tags=["Interactive Ad Widgets"])
    app.include_router(campaign_version_control.router, prefix="/jackie/campaign-version-control", tags=["Campaign Version Control"])
    app.include_router(multi_language.router, prefix="/jackie/multi-language", tags=["Multi-Language Campaign Creation"])
    app.include_router(enhanced_video_voice.router, prefix="/jackie/enhanced-video-voice", tags=["Enhanced Video & Voice Design Tools"])
    
    # Include dashboard router
    app.include_router(jackie_dashboard.router)
    
    # Include chat router
    app.include_router(jackie_chat.router)
    
    @app.get("/health")
    async def health_check():
        return JSONResponse(
            status_code=200,
            content={
                "status": "healthy",
                "agent": "Jackie",
                "version": "1.0.0",
                "features": [
                    "automated_marketing_campaigns",
                    "multi_channel_marketing",
                    "ai_powered_optimization",
                    "predictive_analytics",
                    "campaign_planning",
                    "ab_testing_automation",
                    "budget_management",
                    "performance_tracking",
                    "ai_powered_copywriting",
                    "content_creation",
                    "video_voice_marketing",
                    "brand_voice_customization",
                    "seo_optimization",
                    "social_media_marketing",
                    "email_marketing",
                    "ad_management",
                    "market_research",
                    "influencer_marketing",
                    "customer_segmentation",
                    "cross_channel_analytics",
                    "campaign_performance_forecasting",
                    "crm_integration",
                    "team_collaboration",
                    "multi_brand_support",
                    "custom_workflows",
                    "advanced_brand_voice_customization",
                    "enhanced_video_voice_design_tools",
                    "localized_marketing_optimization",
                    "deep_campaign_analytics",
                    "streamlined_onboarding_experience",
                    "interactive_campaign_elements",
                    "platform_specific_optimization",
                    "human_like_chatbot_responses",
                    "multi_language_campaign_creation",
                    "campaign_collaboration_tools",
                    "dynamic_customer_personalization",
                    "campaign_calendar_integration",
                    "ai_powered_campaign_ideation",
                    "accessibility_optimization",
                    "campaign_performance_forecasting",
                    "ecommerce_design_integration",
                    "ethical_campaign_guidelines",
                    "mobile_campaign_management",
                    "organic_marketing",
                    "deep_campaign_analytics",
                    "streamlined_onboarding_experience",
                    "interactive_campaign_elements",
                    "platform_specific_optimization",
                    "launch_assistant",
                    "customer_search",
                    "influencer_performance_tracking",
                    "real_time_budget_control",
                    "launch_assistant",
                    "customer_search",
                    "ai_campaign_storyboard",
                    "dynamic_budget_allocator",
                    "influencer_roi_predictor",
                    "voice_ad_generator",
                    "geo_targeted_ad_planner",
                    "customer_feedback_loop",
                    "ethical_ad_scanner",
                    "cross_channel_analytics",
                    "interactive_ad_widgets",
                                         "campaign_version_control",
                     "customer_feedback_loop",
                     "ethical_ad_scanner",
                     "cross_channel_analytics",
                     "interactive_ad_widgets",
                     "multi_language_campaign_creation",
                     "enhanced_video_voice_design_tools",
                     "customer_engagement_chatbots",
                     "omnichannel_marketing",
                     "predictive_analytics_forecasting"
                ],
                "message": "Jackie is running and ready to optimize your marketing campaigns!"
            }
        )

    @app.get("/jackie")
    async def root():
        return JSONResponse(
            status_code=200,
            content={
                "agent": "Jackie",
                "description": "AI-Powered Marketing Automation Agent",
                "version": "1.0.0",
                "endpoints": {
                    "health": "/jackie/health",
                    "campaigns": "/jackie/campaigns",
                    "content": "/jackie/content",
                    "seo": "/jackie/seo",
                    "analytics": "/jackie/analytics",
                    "ads": "/jackie/ads",
                    "social_media": "/jackie/social",
                    "email_marketing": "/jackie/email",
                    "influencer_marketing": "/jackie/influencer",
                    "market_research": "/jackie/market-research",
                    "customer_segmentation": "/jackie/customer-segmentation",
                    "ab_testing": "/jackie/ab-testing",
                    "crm_integration": "/jackie/crm-integration",
                    "customer_engagement": "/jackie/customer-engagement",
                    "omnichannel": "/jackie/omnichannel",
                    "predictive_analytics": "/jackie/predictive-analytics",
                    "voice_video_marketing": "/jackie/voice-video",
                    "agent_integration": "/jackie/agent-integration",
                    "brand_voice": "/jackie/brand-voice",
                    "localized_marketing": "/jackie/localized-marketing",
                    "campaign_collaboration": "/jackie/campaign-collaboration",
                    "campaign_calendar": "/jackie/campaign-calendar",
                    "campaign_ideation": "/jackie/campaign-ideation",
                    "accessibility": "/jackie/accessibility",
                    "ecommerce_integration": "/jackie/ecommerce",
                    "ethical_guidelines": "/jackie/ethical-guidelines",
                    "organic_marketing": "/jackie/organic-marketing",
                    "mobile_campaign": "/jackie/mobile-campaign",
                    "deep_analytics": "/jackie/deep-analytics",
                    "onboarding": "/jackie/onboarding",
                    "interactive_elements": "/jackie/interactive-elements",
                    "platform_optimization": "/jackie/platform-optimization",
                    "launch_assistant": "/jackie/launch-assistant",
                    "customer_search": "/jackie/customer-search",
                    "human_chatbot": "/jackie/human-chatbot",
                    "dynamic_personalization": "/jackie/dynamic-personalization",
                    "performance_forecasting": "/jackie/performance-forecasting",
                    "budget_control": "/jackie/budget-control",
                    "campaign_storyboard": "/jackie/campaign-storyboard",
                    "influencer_tracking": "/jackie/influencer-tracking",
                    "dynamic_budget": "/jackie/dynamic-budget",
                    "influencer_roi_predictor": "/jackie/influencer-roi-predictor",
                                         "voice_ad_generator": "/jackie/voice-ad-generator",
                     "geo_targeted": "/jackie/geo-targeted",
                     "customer_feedback": "/jackie/customer-feedback",
                     "ethical_ad_scanner": "/jackie/ethical-ad-scanner",
                     "cross_channel_analytics": "/jackie/cross-channel-analytics",
                     "interactive_widgets": "/jackie/interactive-widgets",
                     "campaign_version_control": "/jackie/campaign-version-control",
                     "multi_language": "/jackie/multi-language",
                     "enhanced_video_voice": "/jackie/enhanced-video-voice"
                },
                "message": "Welcome to Jackie - Your AI Marketing Assistant!"
            }
        )

    return app

app = build_app()

# Note: The main backend mounts this app; do not run a separate server here.
