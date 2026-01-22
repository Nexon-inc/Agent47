"""
Purity - AI-Powered Business Creator & Money Maker
Main application package
"""

from .main import app
from .lifespan import create_app
from .database import get_purity_database, init_purity_database
from .models import (
    PurityBusinessIdea, PurityBusinessModel, PurityMarketResearch, PurityCustomerAvatar,
    PurityFinancialForecast, PurityLegalRequirement, PurityBrandIdentity, PurityLaunchStrategy,
    PurityInvestmentPitch, PurityExitStrategy, PurityBusinessHealth, PurityCompetitorAnalysis,
    PurityNicheOpportunity, PurityMonetizationStrategy, PurityPartnershipOpportunity,
    PurityFranchiseOpportunity, PuritySustainabilityPlan, PurityTaskAutomation,
    PurityBusinessMentor, PurityCrowdfundingCampaign, PurityEcommerceSetup
)

__all__ = [
    "app",
    "create_app",
    "get_purity_database",
    "init_purity_database",
    "PurityBusinessIdea",
    "PurityBusinessModel", 
    "PurityMarketResearch",
    "PurityCustomerAvatar",
    "PurityFinancialForecast",
    "PurityLegalRequirement",
    "PurityBrandIdentity",
    "PurityLaunchStrategy",
    "PurityInvestmentPitch",
    "PurityExitStrategy",
    "PurityBusinessHealth",
    "PurityCompetitorAnalysis",
    "PurityNicheOpportunity",
    "PurityMonetizationStrategy",
    "PurityPartnershipOpportunity",
    "PurityFranchiseOpportunity",
    "PuritySustainabilityPlan",
    "PurityTaskAutomation",
    "PurityBusinessMentor",
    "PurityCrowdfundingCampaign",
    "PurityEcommerceSetup"
]
