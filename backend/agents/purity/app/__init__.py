"""
Purity - AI-Powered Business Creator & Money Maker
Main application package
"""

from .main import app
from .lifespan import create_app
from .database import get_purity_database, init_purity_database
from .models import (
    BusinessIdea, BusinessModel, PurityMarketResearch, CustomerAvatar,
    FinancialForecast, LegalRequirement, BrandIdentity, LaunchStrategy,
    InvestmentPitch, ExitStrategy, BusinessHealth, PurityCompetitorAnalysis,
    NicheOpportunity, MonetizationStrategy, PartnershipOpportunity,
    FranchiseOpportunity, SustainabilityPlan, TaskAutomation,
    BusinessMentor, CrowdfundingCampaign, EcommerceSetup
)

__all__ = [
    "app",
    "create_app",
    "get_purity_database",
    "init_purity_database",
    "BusinessIdea",
    "BusinessModel", 
    "PurityMarketResearch",
    "CustomerAvatar",
    "FinancialForecast",
    "LegalRequirement",
    "BrandIdentity",
    "LaunchStrategy",
    "InvestmentPitch",
    "ExitStrategy",
    "BusinessHealth",
    "PurityCompetitorAnalysis",
    "NicheOpportunity",
    "MonetizationStrategy",
    "PartnershipOpportunity",
    "FranchiseOpportunity",
    "SustainabilityPlan",
    "TaskAutomation",
    "BusinessMentor",
    "CrowdfundingCampaign",
    "EcommerceSetup"
]
