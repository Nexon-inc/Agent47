from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from .lifespan import create_app
from .routers import (
    business_ideas_router,
    market_research_router,
    financial_planning_router,
    legal_compliance_router,
    brand_building_router,
    launch_strategy_router,
    investment_pitch_router,
    exit_strategy_router,
    business_health_router,
    niche_finder_router,
    crowdfunding_router,
    copywriting_assistant_router,
    customer_retention_router,
    opportunity_validation_router,
    customer_avatar_router,
    mvp_builder_router,
    business_model_canvas_router,
    tax_planning_router,
    exit_valuation_router,
    business_intelligence_router,
    business_idea_generator_router,
    purity_dashboard_router,
    sales_funnel_router,
    purity_chat
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
    
    # Include core business routers
    app.include_router(business_ideas_router, prefix="/purity/business", tags=["Business Ideas"])
    app.include_router(market_research_router, prefix="/purity/market", tags=["Market Research"])
    app.include_router(financial_planning_router, prefix="/purity/financial", tags=["Financial Planning"])
    app.include_router(legal_compliance_router, prefix="/purity/legal", tags=["Legal & Compliance"])
    
    # Include product development routers
    app.include_router(brand_building_router, prefix="/purity/brand", tags=["Brand Building"])
    app.include_router(launch_strategy_router, prefix="/purity/launch", tags=["Launch Strategy"])
    app.include_router(investment_pitch_router, prefix="/purity/investment", tags=["Investment Pitch"])
    app.include_router(exit_strategy_router, prefix="/purity/exit", tags=["Exit Strategy"])
    
    # Include analytics and monitoring routers
    app.include_router(business_health_router, prefix="/purity/health", tags=["Business Health"])
    # competitor_analysis router not present in package; competitor analysis endpoints are available via services
    app.include_router(niche_finder_router, prefix="/purity/niches", tags=["Niche Finder"])
    # monetization router not present; monetization features are served via services and other routers
    app.include_router(opportunity_validation_router, prefix="/purity/validation", tags=["Opportunity Validation"])
    
    # Include advanced feature routers
    # The following routers are intentionally omitted because their route modules are not present
    # partnership_matching, franchise_scanner, sustainability_planner, task_automation
    
    # Include AI and intelligence routers
    # business_mentor router not present; include business intelligence and copywriting routers
    app.include_router(business_intelligence_router, prefix="/purity/intelligence", tags=["Business Intelligence"])
    app.include_router(copywriting_assistant_router, prefix="/purity/copywriting", tags=["Copywriting Assistant"])
    
    # Include marketing and sales routers
    app.include_router(sales_funnel_router, prefix="/purity/sales", tags=["Sales Funnel"])
    # social_media_kit and cold_email_generator routers not present; use services or other routers
    app.include_router(customer_retention_router, prefix="/purity/retention", tags=["Customer Retention"])
    
    # Include platform-specific routers
    app.include_router(crowdfunding_router, prefix="/purity/crowdfunding", tags=["Crowdfunding"])
    
    # Include additional feature routers
    app.include_router(customer_avatar_router, prefix="/purity/avatar", tags=["Customer Avatar"])
    app.include_router(mvp_builder_router, prefix="/purity/mvp", tags=["MVP Builder"])
    app.include_router(business_model_canvas_router, prefix="/purity/canvas", tags=["Business Model Canvas"])
    app.include_router(tax_planning_router, prefix="/purity/tax", tags=["Tax Planning"])
    app.include_router(exit_valuation_router, prefix="/purity/valuation", tags=["Exit Valuation"])
    
    # Include dashboard router
    app.include_router(purity_dashboard_router)
    
    # Include chat router
    app.include_router(purity_chat.router)
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint to verify Purity is running"""
        return JSONResponse(
            status_code=200,
            content={
                "status": "healthy",
                "agent": "Purity",
                "version": "1.0.0",
                "features": [
                    "business_idea_generator",
                    "market_research",
                    "financial_planning",
                    "legal_compliance",
                    "brand_building",
                    "launch_strategy",
                    "investment_pitch",
                    "exit_strategy",
                    "business_health_monitoring",
                    "competitor_analysis",
                    "niche_finder",
                    "monetization_strategy",
                    "partnership_matching",
                    "franchise_scanner",
                    "sustainability_planner",
                    "task_automation",
                    "business_mentor",
                    "crowdfunding_campaigns",
                    "ecommerce_setup",
                    "copywriting_assistant",
                    "sales_funnel_generator",
                    "social_media_kit",
                    "cold_email_generator",
                    "customer_retention_analyzer",
                    "opportunity_validation",
                    "customer_avatar_builder",
                    "mvp_builder_blueprint",
                    "business_model_canvas",
                    "tax_planning",
                    "exit_valuation_estimator",
                    "business_intelligence"
                ]
            }
        )
    
    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint with Purity information"""
        return {
            "message": "Welcome to Purity - AI-Powered Business Creator & Money Maker",
            "version": "1.0.0",
            "description": "Your intelligent business creation and money-making partner",
            "documentation": "/docs",
            "health_check": "/health"
        }
    
    return app

app = build_app()

# Note: The main backend mounts this app; do not run a separate server here.