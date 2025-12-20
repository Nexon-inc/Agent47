from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float, ForeignKey, JSON, Enum, Table, Index, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum
from core.database.models import Base

class BusinessStage(enum.Enum):
    IDEA = "idea"
    VALIDATION = "validation"
    MVP = "mvp"
    LAUNCH = "launch"
    GROWTH = "growth"
    SCALE = "scale"
    EXIT = "exit"

class IndustryType(enum.Enum):
    TECHNOLOGY = "technology"
    HEALTHCARE = "healthcare"
    FINANCE = "finance"
    EDUCATION = "education"
    RETAIL = "retail"
    MANUFACTURING = "manufacturing"
    SERVICES = "services"
    ENTERTAINMENT = "entertainment"
    FOOD_BEVERAGE = "food_beverage"
    REAL_ESTATE = "real_estate"
    TRANSPORTATION = "transportation"
    ENERGY = "energy"
    OTHER = "other"

class RevenueModel(enum.Enum):
    SUBSCRIPTION = "subscription"
    FREEMIUM = "freemium"
    MARKETPLACE = "marketplace"
    AFFILIATE = "affiliate"
    ADVERTISING = "advertising"
    LICENSING = "licensing"
    FRANCHISE = "franchise"
    ECOMMERCE = "ecommerce"
    SAAS = "saas"
    CONSULTING = "consulting"

class ValidationStatus(enum.Enum):
    PENDING = "pending"
    VALIDATED = "validated"
    INVALID = "invalid"
    NEEDS_MORE_DATA = "needs_more_data"

class BusinessIdea(Base):
    __tablename__ = "business_ideas"
    __table_args__ = {"extend_existing": True}
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    industry = Column(Enum(IndustryType), nullable=False)
    target_market = Column(String(500))
    unique_value_proposition = Column(Text)
    revenue_potential = Column(Float)
    startup_cost = Column(Float)
    time_to_market = Column(Integer)  # in months
    competition_level = Column(String(50))
    market_size = Column(String(100))
    validation_score = Column(Float, default=0.0)
    status = Column(Enum(ValidationStatus), default=ValidationStatus.PENDING)
    tags = Column(JSON, default=list)
    metadata_json = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    business_models = relationship("BusinessModel", back_populates="idea")
    market_research = relationship("PurityMarketResearch", back_populates="idea")
    customer_avatars = relationship("CustomerAvatar", back_populates="idea")

class BusinessModel(Base):
    __tablename__ = "business_models"
    __table_args__ = {"extend_existing": True}
    
    id = Column(Integer, primary_key=True, index=True)
    idea_id = Column(Integer, ForeignKey("business_ideas.id"), nullable=False)
    key_partners = Column(JSON, default=[])
    key_activities = Column(JSON, default=[])
    key_resources = Column(JSON, default=[])
    value_propositions = Column(JSON, default=[])
    customer_relationships = Column(JSON, default=[])
    channels = Column(JSON, default=[])
    customer_segments = Column(JSON, default=[])
    cost_structure = Column(JSON, default=[])
    revenue_streams = Column(JSON, default=[])
    revenue_model = Column(Enum(RevenueModel))
    pricing_strategy = Column(Text)
    competitive_advantage = Column(Text)
    scalability_factors = Column(JSON, default=[])
    risk_factors = Column(JSON, default=[])
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    idea = relationship("BusinessIdea", back_populates="business_models")

class PurityMarketResearch(Base):
    __tablename__ = "purity_market_research"
    
    id = Column(Integer, primary_key=True, index=True)
    idea_id = Column(Integer, ForeignKey("business_ideas.id"), nullable=False)
    market_size = Column(Float)  # in billions USD
    market_growth_rate = Column(Float)  # percentage
    target_market_size = Column(Float)
    market_trends = Column(JSON, default=[])
    competitor_analysis = Column(JSON, default=[])
    customer_pain_points = Column(JSON, default=[])
    market_opportunities = Column(JSON, default=[])
    market_risks = Column(JSON, default=[])
    regulatory_environment = Column(Text)
    technology_trends = Column(JSON, default=[])
    social_trends = Column(JSON, default=[])
    economic_factors = Column(JSON, default=[])
    research_sources = Column(JSON, default=[])
    confidence_score = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    idea = relationship("BusinessIdea", back_populates="market_research")

class CustomerAvatar(Base):
    __tablename__ = "customer_avatars"
    __table_args__ = {"extend_existing": True}
    
    id = Column(Integer, primary_key=True, index=True)
    idea_id = Column(Integer, ForeignKey("business_ideas.id"), nullable=False)
    name = Column(String(100), nullable=False)
    age_range = Column(String(50))
    gender = Column(String(20))
    income_level = Column(String(50))
    education_level = Column(String(50))
    occupation = Column(String(100))
    location = Column(String(100))
    interests = Column(JSON, default=[])
    pain_points = Column(JSON, default=[])
    goals = Column(JSON, default=[])
    buying_behavior = Column(Text)
    preferred_channels = Column(JSON, default=[])
    decision_factors = Column(JSON, default=[])
    objections = Column(JSON, default=[])
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    idea = relationship("BusinessIdea", back_populates="customer_avatars")

class FinancialForecast(Base):
    __tablename__ = "financial_forecasts"
    __table_args__ = {"extend_existing": True}
    
    id = Column(Integer, primary_key=True, index=True)
    idea_id = Column(Integer, ForeignKey("business_ideas.id"), nullable=False)
    forecast_period = Column(Integer)  # in months
    revenue_projections = Column(JSON, default=[])
    cost_projections = Column(JSON, default=[])
    profit_projections = Column(JSON, default=[])
    cash_flow_projections = Column(JSON, default=[])
    break_even_analysis = Column(JSON, default={})
    funding_requirements = Column(JSON, default=[])
    roi_projections = Column(JSON, default=[])
    sensitivity_analysis = Column(JSON, default=[])
    assumptions = Column(JSON, default=[])
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    idea = relationship("BusinessIdea")

class LegalRequirement(Base):
    __tablename__ = "legal_requirements"
    __table_args__ = {"extend_existing": True}
    
    id = Column(Integer, primary_key=True, index=True)
    idea_id = Column(Integer, ForeignKey("business_ideas.id"), nullable=False)
    jurisdiction = Column(String(100), nullable=False)
    business_structure = Column(String(100))
    required_licenses = Column(JSON, default=[])
    permits_needed = Column(JSON, default=[])
    tax_obligations = Column(JSON, default=[])
    compliance_requirements = Column(JSON, default=[])
    intellectual_property = Column(JSON, default=[])
    employment_law = Column(JSON, default=[])
    data_protection = Column(JSON, default=[])
    industry_regulations = Column(JSON, default=[])
    estimated_costs = Column(Float)
    timeline = Column(Integer)  # in days
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    idea = relationship("BusinessIdea")

class BrandIdentity(Base):
    __tablename__ = "brand_identities"
    __table_args__ = {"extend_existing": True}
    
    id = Column(Integer, primary_key=True, index=True)
    idea_id = Column(Integer, ForeignKey("business_ideas.id"), nullable=False)
    brand_name = Column(String(100))
    brand_story = Column(Text)
    mission_statement = Column(Text)
    vision_statement = Column(Text)
    core_values = Column(JSON, default=[])
    brand_personality = Column(JSON, default=[])
    color_scheme = Column(JSON, default=[])
    typography = Column(JSON, default=[])
    logo_concepts = Column(JSON, default=[])
    taglines = Column(JSON, default=[])
    brand_voice = Column(Text)
    target_audience_alignment = Column(Text)
    competitive_differentiation = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    idea = relationship("BusinessIdea")

class LaunchStrategy(Base):
    __tablename__ = "launch_strategies"
    __table_args__ = {"extend_existing": True}
    
    id = Column(Integer, primary_key=True, index=True)
    idea_id = Column(Integer, ForeignKey("business_ideas.id"), nullable=False)
    launch_date = Column(DateTime)
    launch_phases = Column(JSON, default=[])
    marketing_channels = Column(JSON, default=[])
    content_strategy = Column(JSON, default=[])
    social_media_plan = Column(JSON, default=[])
    influencer_strategy = Column(JSON, default=[])
    pr_strategy = Column(JSON, default=[])
    advertising_budget = Column(Float)
    kpi_targets = Column(JSON, default=[])
    risk_mitigation = Column(JSON, default=[])
    success_metrics = Column(JSON, default=[])
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    idea = relationship("BusinessIdea")

class InvestmentPitch(Base):
    __tablename__ = "investment_pitches"
    __table_args__ = {"extend_existing": True}
    
    id = Column(Integer, primary_key=True, index=True)
    idea_id = Column(Integer, ForeignKey("business_ideas.id"), nullable=False)
    pitch_deck_url = Column(String(500))
    executive_summary = Column(Text)
    problem_statement = Column(Text)
    solution_description = Column(Text)
    market_opportunity = Column(Text)
    business_model = Column(Text)
    competitive_landscape = Column(Text)
    go_to_market_strategy = Column(Text)
    financial_projections = Column(JSON, default=[])
    funding_ask = Column(Float)
    use_of_funds = Column(JSON, default=[])
    team_bios = Column(JSON, default=[])
    traction_metrics = Column(JSON, default=[])
    risk_factors = Column(JSON, default=[])
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    idea = relationship("BusinessIdea")

class ExitStrategy(Base):
    __tablename__ = "exit_strategies"
    __table_args__ = {"extend_existing": True}
    
    id = Column(Integer, primary_key=True, index=True)
    idea_id = Column(Integer, ForeignKey("business_ideas.id"), nullable=False)
    exit_type = Column(String(50))  # acquisition, ipo, merger, etc.
    timeline = Column(Integer)  # in years
    target_valuation = Column(Float)
    potential_buyers = Column(JSON, default=[])
    preparation_requirements = Column(JSON, default=[])
    legal_considerations = Column(JSON, default=[])
    financial_implications = Column(JSON, default=[])
    market_conditions = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    idea = relationship("BusinessIdea")

class BusinessHealth(Base):
    __tablename__ = "business_health"
    __table_args__ = {"extend_existing": True}
    
    id = Column(Integer, primary_key=True, index=True)
    idea_id = Column(Integer, ForeignKey("business_ideas.id"), nullable=False)
    stage = Column(Enum(BusinessStage), nullable=False)
    health_score = Column(Float, default=0.0)
    kpi_metrics = Column(JSON, default=[])
    performance_indicators = Column(JSON, default=[])
    risk_assessment = Column(JSON, default=[])
    growth_metrics = Column(JSON, default=[])
    customer_metrics = Column(JSON, default=[])
    financial_metrics = Column(JSON, default=[])
    operational_metrics = Column(JSON, default=[])
    recommendations = Column(JSON, default=[])
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    idea = relationship("BusinessIdea")

class PurityCompetitorAnalysis(Base):
    __tablename__ = "purity_competitor_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    idea_id = Column(Integer, ForeignKey("business_ideas.id"), nullable=False)
    competitor_name = Column(String(200), nullable=False)
    competitor_url = Column(String(500))
    market_position = Column(String(100))
    strengths = Column(JSON, default=[])
    weaknesses = Column(JSON, default=[])
    opportunities = Column(JSON, default=[])
    threats = Column(JSON, default=[])
    pricing_strategy = Column(Text)
    marketing_strategy = Column(Text)
    technology_stack = Column(JSON, default=[])
    customer_base = Column(Text)
    revenue_estimate = Column(Float)
    competitive_advantage = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    idea = relationship("BusinessIdea")

class OpportunityValidation(Base):
    __tablename__ = "opportunity_validations"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    idea_id = Column(Integer, ForeignKey("business_ideas.id"), nullable=False)
    validation_score = Column(Float, default=0.0)
    market_viability = Column(JSON, default=dict)
    competitive_analysis = Column(JSON, default=dict)
    seo_opportunity = Column(JSON, default=dict)
    risk_assessment = Column(JSON, default=list)
    recommendations = Column(JSON, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    idea = relationship("BusinessIdea")

class NicheOpportunity(Base):
    __tablename__ = "niche_opportunities"
    __table_args__ = {"extend_existing": True}
    
    id = Column(Integer, primary_key=True, index=True)
    idea_id = Column(Integer, ForeignKey("business_ideas.id"), nullable=False)
    niche_name = Column(String(200), nullable=False)
    niche_description = Column(Text)
    market_size = Column(Float)
    competition_level = Column(String(50))
    entry_barriers = Column(JSON, default=[])
    growth_potential = Column(Float)
    profitability_score = Column(Float)
    customer_pain_points = Column(JSON, default=[])
    monetization_opportunities = Column(JSON, default=[])
    marketing_channels = Column(JSON, default=[])
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    idea = relationship("BusinessIdea")

class MonetizationStrategy(Base):
    __tablename__ = "monetization_strategies"
    __table_args__ = {"extend_existing": True}
    
    id = Column(Integer, primary_key=True, index=True)
    idea_id = Column(Integer, ForeignKey("business_ideas.id"), nullable=False)
    primary_model = Column(Enum(RevenueModel), nullable=False)
    secondary_models = Column(JSON, default=[])
    pricing_strategy = Column(Text)
    pricing_tiers = Column(JSON, default=[])
    revenue_streams = Column(JSON, default=[])
    customer_lifetime_value = Column(Float)
    customer_acquisition_cost = Column(Float)
    conversion_rates = Column(JSON, default=[])
    revenue_projections = Column(JSON, default=[])
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    idea = relationship("BusinessIdea")

class PartnershipOpportunity(Base):
    __tablename__ = "partnership_opportunities"
    __table_args__ = {"extend_existing": True}
    
    id = Column(Integer, primary_key=True, index=True)
    idea_id = Column(Integer, ForeignKey("business_ideas.id"), nullable=False)
    partner_name = Column(String(200), nullable=False)
    partner_type = Column(String(100))  # co-founder, investor, supplier, etc.
    partner_description = Column(Text)
    value_proposition = Column(Text)
    contact_info = Column(JSON, default={})
    partnership_terms = Column(JSON, default=[])
    mutual_benefits = Column(JSON, default=[])
    risk_factors = Column(JSON, default=[])
    status = Column(String(50), default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    idea = relationship("BusinessIdea")

class FranchiseOpportunity(Base):
    __tablename__ = "franchise_opportunities"
    __table_args__ = {"extend_existing": True}
    
    id = Column(Integer, primary_key=True, index=True)
    idea_id = Column(Integer, ForeignKey("business_ideas.id"), nullable=False)
    franchise_name = Column(String(200), nullable=False)
    franchise_description = Column(Text)
    initial_investment = Column(Float)
    ongoing_fees = Column(JSON, default=[])
    territory_availability = Column(JSON, default=[])
    training_provided = Column(Boolean, default=False)
    support_services = Column(JSON, default=[])
    success_rate = Column(Float)
    time_to_profitability = Column(Integer)  # in months
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    idea = relationship("BusinessIdea")

class MVPBlueprint(Base):
    __tablename__ = "mvp_blueprints"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    idea_id = Column(Integer, ForeignKey("business_ideas.id"), nullable=False)
    features = Column(JSON, default=list)
    user_stories = Column(JSON, default=list)
    acceptance_criteria = Column(JSON, default=list)
    timelines = Column(JSON, default=dict)
    tech_stack = Column(JSON, default=list)
    cost_estimates = Column(JSON, default=dict)
    validation_notes = Column(JSON, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    idea = relationship("BusinessIdea")

class BusinessModelCanvas(Base):
    __tablename__ = "business_model_canvases"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    idea_id = Column(Integer, ForeignKey("business_ideas.id"), nullable=False)
    key_partners = Column(JSON, default=list)
    key_activities = Column(JSON, default=list)
    key_resources = Column(JSON, default=list)
    value_propositions = Column(JSON, default=list)
    customer_relationships = Column(JSON, default=list)
    channels = Column(JSON, default=list)
    customer_segments = Column(JSON, default=list)
    cost_structure = Column(JSON, default=list)
    revenue_streams = Column(JSON, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    idea = relationship("BusinessIdea")

class SustainabilityPlan(Base):
    __tablename__ = "sustainability_plans"
    __table_args__ = {"extend_existing": True}
    
    id = Column(Integer, primary_key=True, index=True)
    idea_id = Column(Integer, ForeignKey("business_ideas.id"), nullable=False)
    environmental_impact = Column(JSON, default=[])
    social_responsibility = Column(JSON, default=[])
    governance_practices = Column(JSON, default=[])
    sustainability_goals = Column(JSON, default=[])
    implementation_strategy = Column(Text)
    cost_benefit_analysis = Column(JSON, default=[])
    stakeholder_engagement = Column(JSON, default=[])
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    idea = relationship("BusinessIdea")

class TaskAutomation(Base):
    __tablename__ = "task_automations"
    __table_args__ = {"extend_existing": True}
    
    id = Column(Integer, primary_key=True, index=True)
    idea_id = Column(Integer, ForeignKey("business_ideas.id"), nullable=False)
    task_name = Column(String(200), nullable=False)
    task_description = Column(Text)
    automation_tool = Column(String(100))
    workflow_steps = Column(JSON, default=[])
    integration_details = Column(JSON, default=[])
    time_saved = Column(Integer)  # in hours per week
    cost_savings = Column(Float)
    implementation_status = Column(String(50), default="planned")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    idea = relationship("BusinessIdea")

class BusinessMentor(Base):
    __tablename__ = "business_mentors"
    __table_args__ = {"extend_existing": True}
    
    id = Column(Integer, primary_key=True, index=True)
    idea_id = Column(Integer, ForeignKey("business_ideas.id"), nullable=False)
    mentor_name = Column(String(200), nullable=False)
    mentor_expertise = Column(JSON, default=[])
    mentorship_areas = Column(JSON, default=[])
    availability = Column(JSON, default=[])
    contact_info = Column(JSON, default={})
    mentorship_goals = Column(JSON, default=[])
    progress_tracking = Column(JSON, default=[])
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    idea = relationship("BusinessIdea")

class CrowdfundingCampaign(Base):
    __tablename__ = "crowdfunding_campaigns"
    __table_args__ = {"extend_existing": True}
    
    id = Column(Integer, primary_key=True, index=True)
    idea_id = Column(Integer, ForeignKey("business_ideas.id"), nullable=False)
    platform = Column(String(100))  # kickstarter, indiegogo, etc.
    campaign_title = Column(String(200), nullable=False)
    campaign_description = Column(Text)
    funding_goal = Column(Float)
    campaign_duration = Column(Integer)  # in days
    rewards_tiers = Column(JSON, default=[])
    marketing_strategy = Column(JSON, default=[])
    video_content = Column(JSON, default=[])
    social_proof = Column(JSON, default=[])
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    idea = relationship("BusinessIdea")

class EcommerceSetup(Base):
    __tablename__ = "ecommerce_setups"
    __table_args__ = {"extend_existing": True}
    
    id = Column(Integer, primary_key=True, index=True)
    idea_id = Column(Integer, ForeignKey("business_ideas.id"), nullable=False)
    platform = Column(String(100))  # shopify, woocommerce, etc.
    store_name = Column(String(200), nullable=False)
    store_url = Column(String(500))
    product_catalog = Column(JSON, default=[])
    payment_gateways = Column(JSON, default=[])
    shipping_options = Column(JSON, default=[])
    inventory_management = Column(JSON, default=[])
    marketing_tools = Column(JSON, default=[])
    analytics_setup = Column(JSON, default=[])
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    idea = relationship("BusinessIdea")



class TaxStrategy(Base):
    __tablename__ = "tax_strategies"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    idea_id = Column(Integer, ForeignKey("business_ideas.id"), nullable=False)
    tax_type = Column(String(100))  # e.g., income, VAT, sales, corporate
    jurisdiction = Column(String(200))
    estimated_tax_liability = Column(Float)
    credits_and_deductions = Column(JSON, default=list)
    compliance_requirements = Column(JSON, default=list)
    optimization_recommendations = Column(Text)
    effective_date = Column(DateTime)
    expires_on = Column(DateTime)
    metadata_json = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    idea = relationship("BusinessIdea")

class ExitValuation(Base):
    __tablename__ = "exit_valuations"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    idea_id = Column(Integer, ForeignKey("business_ideas.id"), nullable=False)
    valuation_method = Column(String(100))  # e.g., dcf, comparables, precedent
    projected_valuation = Column(Float)
    revenue_multiplier = Column(Float)
    ebitda_multiplier = Column(Float)
    assumptions = Column(JSON, default=list)
    comparable_companies = Column(JSON, default=list)
    sensitivity_analysis = Column(JSON, default=list)
    recommended_exit_path = Column(String(200))  # acquisition, IPO, strategic partnership
    legal_considerations = Column(JSON, default=list)
    tax_implications = Column(JSON, default=list)
    notes = Column(Text)
    metadata_json = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    idea = relationship("BusinessIdea")
