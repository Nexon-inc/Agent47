from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from .lifespan import create_app
from .routers import (
    market_trend_analysis, competitor_analysis, sentiment_tracking, keyword_research,
    consumer_behavior, industry_report, social_media_listening, data_visualization,
    data_scraping, trend_forecasting, niche_market, customer_persona, news_monitoring,
    patent_tracking, custom_research, multi_language_research, competitor_benchmarking,
    survey_creation, data_export, trend_alerts, geo_specific_research, research_summarizer,
    compliance_checker, market_intelligence, onboarding_wizard, mobile_dashboard, voice_queries,
    collaborative_workflows, historical_analysis, research_ideation, accessibility,
    social_proof_analyzer, market_opportunity, competitor_ad_tracking, research_automation,
    ethical_guidelines, cross_platform_integration, hypothesis_testing, custom_data_source,
    research_performance_analytics, joe_dashboard, joe_chat
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
    
    # Include core research routers
    app.include_router(market_trend_analysis.router, prefix="/joe/market-trends", tags=["Market Trend Analysis"])
    app.include_router(competitor_analysis.router, prefix="/joe/competitor-analysis", tags=["Competitor Analysis"])
    app.include_router(sentiment_tracking.router, prefix="/joe/sentiment-tracking", tags=["Sentiment Tracking"])
    app.include_router(keyword_research.router, prefix="/joe/keyword-research", tags=["Keyword Research"])
    app.include_router(consumer_behavior.router, prefix="/joe/consumer-behavior", tags=["Consumer Behavior"])
    app.include_router(industry_report.router, prefix="/joe/industry-report", tags=["Industry Reports"])
    
    # Include advanced research routers
    app.include_router(social_media_listening.router, prefix="/joe/social-media-listening", tags=["Social Media Listening"])
    app.include_router(data_visualization.router, prefix="/joe/data-visualization", tags=["Data Visualization"])
    app.include_router(data_scraping.router, prefix="/joe/data-scraping", tags=["Data Scraping"])
    app.include_router(trend_forecasting.router, prefix="/joe/trend-forecasting", tags=["Trend Forecasting"])
    app.include_router(niche_market.router, prefix="/joe/niche-market", tags=["Niche Market Analysis"])
    app.include_router(customer_persona.router, prefix="/joe/customer-persona", tags=["Customer Persona"])
    
    # Include specialized research routers
    app.include_router(news_monitoring.router, prefix="/joe/news-monitoring", tags=["News Monitoring"])
    app.include_router(patent_tracking.router, prefix="/joe/patent-tracking", tags=["Patent Tracking"])
    app.include_router(custom_research.router, prefix="/joe/custom-research", tags=["Custom Research"])
    app.include_router(multi_language_research.router, prefix="/joe/multi-language-research", tags=["Multi-JoeLanguage Research"])
    app.include_router(competitor_benchmarking.router, prefix="/joe/competitor-benchmarking", tags=["Competitor Benchmarking"])
    app.include_router(survey_creation.router, prefix="/joe/survey-creation", tags=["JoeSurvey Creation"])
    
    # Include data management routers
    app.include_router(data_export.router, prefix="/joe/data-export", tags=["Data Export"])
    app.include_router(trend_alerts.router, prefix="/joe/trend-alerts", tags=["Trend Alerts"])
    app.include_router(geo_specific_research.router, prefix="/joe/geo-specific-research", tags=["Geo-Specific Research"])
    app.include_router(research_summarizer.router, prefix="/joe/research-summarizer", tags=["Research Summarizer"])
    app.include_router(compliance_checker.router, prefix="/joe/compliance-checker", tags=["Compliance Checker"])
    app.include_router(market_intelligence.router, prefix="/joe/market-intelligence", tags=["Market Intelligence"])
    
    # Include user experience routers
    app.include_router(onboarding_wizard.router, prefix="/joe/onboarding-wizard", tags=["Onboarding Wizard"])
    app.include_router(mobile_dashboard.router, prefix="/joe/mobile-dashboard", tags=["Mobile Dashboard"])
    app.include_router(voice_queries.router, prefix="/joe/voice-queries", tags=["Voice Queries"])
    app.include_router(collaborative_workflows.router, prefix="/joe/collaborative-workflows", tags=["Collaborative Workflows"])
    app.include_router(historical_analysis.router, prefix="/joe/historical-analysis", tags=["Historical Analysis"])
    app.include_router(research_ideation.router, prefix="/joe/research-ideation", tags=["Research Ideation"])
    
    # Include accessibility and advanced features
    app.include_router(accessibility.router, prefix="/joe/accessibility", tags=["Accessibility"])
    app.include_router(social_proof_analyzer.router, prefix="/joe/social-proof-analyzer", tags=["Social Proof Analyzer"])
    app.include_router(market_opportunity.router, prefix="/joe/market-opportunity", tags=["Market Opportunity"])
    app.include_router(competitor_ad_tracking.router, prefix="/joe/competitor-ad-tracking", tags=["Competitor Ad Tracking"])
    app.include_router(research_automation.router, prefix="/joe/research-automation", tags=["Research Automation"])
    app.include_router(ethical_guidelines.router, prefix="/joe/ethical-guidelines", tags=["Ethical Guidelines"])
    
    # Include integration and testing routers
    app.include_router(cross_platform_integration.router, prefix="/joe/cross-platform-integration", tags=["Cross-Platform Integration"])
    app.include_router(hypothesis_testing.router, prefix="/joe/hypothesis-testing", tags=["Hypothesis Testing"])
    app.include_router(custom_data_source.router, prefix="/joe/custom-data-source", tags=["Custom Data Source"])
    app.include_router(research_performance_analytics.router, prefix="/joe/research-performance-analytics", tags=["Research Performance Analytics"])
    
    # Include dashboard router
    app.include_router(joe_dashboard.router)
    
    # Include chat router
    app.include_router(joe_chat.router)
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint to verify Joe is running"""
        return JSONResponse(
            status_code=200,
            content={
                "status": "healthy",
                "agent": "Joe",
                "version": "1.0.0",
                "features": [
                    "market_trend_analysis",
                    "competitor_analysis", 
                    "sentiment_tracking",
                    "keyword_research",
                    "consumer_behavior",
                    "industry_reports",
                    "social_media_listening",
                    "data_visualization",
                    "data_scraping",
                    "trend_forecasting",
                    "niche_market_analysis",
                    "customer_persona",
                    "news_monitoring",
                    "patent_tracking",
                    "custom_research",
                    "multi_language_research",
                    "competitor_benchmarking",
                    "survey_creation",
                    "data_export",
                    "trend_alerts",
                    "geo_specific_research",
                    "research_summarizer",
                    "compliance_checker",
                    "market_intelligence",
                    "onboarding_wizard",
                    "mobile_dashboard",
                    "voice_queries",
                    "collaborative_workflows",
                    "historical_analysis",
                    "research_ideation",
                    "accessibility",
                    "social_proof_analyzer",
                    "market_opportunity",
                    "competitor_ad_tracking",
                    "research_automation",
                    "ethical_guidelines",
                    "cross_platform_integration",
                    "hypothesis_testing",
                    "custom_data_source",
                    "research_performance_analytics"
                ]
            }
        )
    
    return app

app = build_app()

# Note: The main backend mounts this app; do not run a separate server here.