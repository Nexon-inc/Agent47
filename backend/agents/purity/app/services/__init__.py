"""
Purity Services Package
All business creation and money-making services
"""

from .business_intelligence_service import BusinessIntelligenceService
from .market_research_service import MarketResearchService
from .financial_planning_service import FinancialPlanningService
from .legal_compliance_service import LegalComplianceService
from .brand_building_service import BrandBuildingService
from .launch_strategy_service import LaunchStrategyService
from .investment_pitch_service import InvestmentPitchService
from .exit_strategy_service import ExitStrategyService
from .business_health_service import BusinessHealthService
# The implementation file is named competitor_analyzer_service.py; export it under the
# historical name `CompetitorAnalysisService` to avoid breaking imports elsewhere.
from .competitor_analyzer_service import CompetitorAnalyzerService as CompetitorAnalysisService
from .niche_finder_service import NicheFinderService
from .monetization_service import MonetizationService
# The file is partnership_matchmaker_service.py; provide an alias for the expected name
from .partnership_matchmaker_service import PartnershipMatchmakerService as PartnershipMatchingService
from .franchise_scanner_service import FranchiseScannerService
from .sustainability_planner_service import SustainabilityPlannerService
from .task_automation_service import TaskAutomationService
from .business_mentor_service import BusinessMentorService
from .crowdfunding_service import CrowdfundingService
from .ecommerce_setup_service import EcommerceSetupService
from .copywriting_assistant_service import CopywritingAssistantService
from .sales_funnel_service import SalesFunnelService
from .social_media_kit_service import SocialMediaKitService
from .cold_email_generator_service import ColdEmailGeneratorService
from .customer_retention_service import CustomerRetentionService

__all__ = [
    "BusinessIntelligenceService",
    "MarketResearchService",
    "FinancialPlanningService",
    "LegalComplianceService",
    "BrandBuildingService",
    "LaunchStrategyService",
    "InvestmentPitchService",
    "ExitStrategyService",
    "BusinessHealthService",
    "CompetitorAnalysisService",
    "NicheFinderService",
    "MonetizationService",
    "PartnershipMatchingService",
    "FranchiseScannerService",
    "SustainabilityPlannerService",
    "TaskAutomationService",
    "BusinessMentorService",
    "CrowdfundingService",
    "EcommerceSetupService",
    "CopywritingAssistantService",
    "SalesFunnelService",
    "SocialMediaKitService",
    "ColdEmailGeneratorService",
    "CustomerRetentionService"
]
