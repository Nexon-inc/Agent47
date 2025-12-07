"""
Purity Routers Package
All API route handlers for business creation and money-making features
"""
from .business_ideas import router as business_ideas_router
from .market_research import router as market_research_router
from .financial_planning import router as financial_planning_router
from .legal_compliance import router as legal_compliance_router
from .brand_building import router as brand_building_router
from .launch_strategy import router as launch_strategy_router
from .investment_pitch import router as investment_pitch_router
from .exit_strategy import router as exit_strategy_router
from .business_health import router as business_health_router
from .niche_finder import router as niche_finder_router
from .crowdfunding import router as crowdfunding_router
from .copywriting_assistant import router as copywriting_assistant_router
from .customer_retention import router as customer_retention_router
from .opportunity_validation import router as opportunity_validation_router
from .customer_avatar import router as customer_avatar_router
from .mvp_builder import router as mvp_builder_router
from .business_model_canvas import router as business_model_canvas_router
from .tax_planning import router as tax_planning_router
from .exit_valuation import router as exit_valuation_router
from .business_intelligence import router as business_intelligence_router
from .business_idea_generator import router as business_idea_generator_router
from .purity_dashboard import router as purity_dashboard_router
from .sales_funnel import router as sales_funnel_router

__all__ = [
    "business_ideas_router",
    "market_research_router",
    "financial_planning_router",
    "legal_compliance_router",
    "brand_building_router",
    "launch_strategy_router",
    "investment_pitch_router",
    "exit_strategy_router",
    "business_health_router",
    "niche_finder_router",
    "crowdfunding_router",
    "copywriting_assistant_router",
    "customer_retention_router",
    "opportunity_validation_router",
    "customer_avatar_router",
    "mvp_builder_router",
    "business_model_canvas_router",
    "tax_planning_router",
    "exit_valuation_router",
    "business_intelligence_router",
    "business_idea_generator_router",
    "purity_dashboard_router",
    "sales_funnel_router",
]
