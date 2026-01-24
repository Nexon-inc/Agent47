from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey, JSON, Enum, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from datetime import datetime

from core.database.models import Base

class LeadStatus(enum.Enum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    PROPOSAL_SENT = "proposal_sent"
    NEGOTIATION = "negotiation"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"
    DISQUALIFIED = "disqualified"

class LeadSource(enum.Enum):
    WEBSITE = "website"
    SOCIAL_MEDIA = "social_media"
    EMAIL_CAMPAIGN = "email_campaign"
    REFERRAL = "referral"
    COLD_OUTREACH = "cold_outreach"
    AD_CAMPAIGN = "ad_campaign"
    EVENT = "event"
    PARTNER = "partner"
    AI_GENERATED = "ai_generated"

class CommunicationChannel(enum.Enum):
    EMAIL = "email"
    SMS = "sms"
    PHONE = "phone"
    LINKEDIN = "linkedin"
    WHATSAPP = "whatsapp"
    CHAT = "chat"
    VOICE = "voice"

class SalesStage(enum.Enum):
    PROSPECTING = "prospecting"
    QUALIFICATION = "qualification"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    CLOSING = "closing"
    CLOSED = "closed"

class DealStatus(enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    WON = "won"
    LOST = "lost"
    CANCELLED = "cancelled"

class ObjectionType(enum.Enum):
    PRICE = "price"
    TIMING = "timing"
    AUTHORITY = "authority"
    NEED = "need"
    COMPETITOR = "competitor"
    BUDGET = "budget"
    FEATURE = "feature"

class EricLead(Base):
    __tablename__ = "eric_leads"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    brand_id = Column(Integer, nullable=False, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    phone = Column(String(20))
    company = Column(String(200))
    job_title = Column(String(100))
    industry = Column(String(100))
    lead_source = Column(Enum(LeadSource), default=LeadSource.WEBSITE)
    lead_status = Column(Enum(LeadStatus), default=LeadStatus.NEW)
    lead_score = Column(Float, default=0.0)
    budget = Column(Float)
    timeline = Column(String(50))
    pain_points = Column(Text)
    requirements = Column(Text)
    location = Column(String(100))
    timezone = Column(String(50))
    language = Column(String(10), default="en")
    social_profiles = Column(JSON)
    website_activity = Column(JSON)
    engagement_history = Column(JSON)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    interactions = relationship("EricLeadInteraction", back_populates="lead")
    deals = relationship("EricDeal", back_populates="lead")
    objections = relationship("EricObjection", back_populates="lead")

class EricLeadInteraction(Base):
    __tablename__ = "eric_lead_interactions"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("eric_leads.id"), nullable=False)
    interaction_type = Column(String(50), nullable=False)
    channel = Column(Enum(CommunicationChannel), nullable=False)
    content = Column(Text)
    sentiment_score = Column(Float)
    engagement_score = Column(Float)
    response_time = Column(Integer)
    outcome = Column(String(100))
    extra_metadata = Column('metadata', JSON, default={})
    created_at = Column(DateTime, default=func.now())
    
    lead = relationship("EricLead", back_populates="interactions")

class EricDeal(Base):
    __tablename__ = "eric_deals"
    
    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("eric_leads.id"), nullable=False)
    brand_id = Column(Integer, nullable=False, index=True)
    deal_name = Column(String(200), nullable=False)
    deal_value = Column(Float, nullable=False)
    currency = Column(String(3), default="USD")
    sales_stage = Column(Enum(SalesStage), default=SalesStage.PROSPECTING)
    probability = Column(Float, default=0.0)
    expected_close_date = Column(DateTime)
    actual_close_date = Column(DateTime)
    win_reason = Column(Text)
    loss_reason = Column(Text)
    sales_rep_id = Column(Integer)
    team_id = Column(Integer)
    pipeline_id = Column(Integer)
    tags = Column(JSON)
    notes = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    lead = relationship("EricLead", back_populates="deals")
    activities = relationship("EricSalesActivity", back_populates="deal")

class EricSalesActivity(Base):
    __tablename__ = "eric_sales_activities"
    
    id = Column(Integer, primary_key=True, index=True)
    deal_id = Column(Integer, ForeignKey("eric_deals.id"), nullable=False)
    activity_type = Column(String(50), nullable=False)
    subject = Column(String(200))
    description = Column(Text)
    channel = Column(Enum(CommunicationChannel))
    duration = Column(Integer)
    outcome = Column(String(100))
    next_action = Column(String(200))
    due_date = Column(DateTime)
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    
    deal = relationship("EricDeal", back_populates="activities")

class EricObjection(Base):
    __tablename__ = "eric_objections"
    
    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("eric_leads.id"), nullable=False)
    objection_type = Column(Enum(ObjectionType), nullable=False)
    objection_text = Column(Text, nullable=False)
    response_text = Column(Text)
    resolved = Column(Boolean, default=False)
    resolution_notes = Column(Text)
    created_at = Column(DateTime, default=func.now())
    
    lead = relationship("EricLead", back_populates="objections")

class EricSalesCampaign(Base):
    __tablename__ = "eric_sales_campaigns"
    
    id = Column(Integer, primary_key=True, index=True)
    brand_id = Column(Integer, nullable=False, index=True)
    campaign_name = Column(String(200), nullable=False)
    campaign_type = Column(String(50), nullable=False)
    target_audience = Column(JSON)
    messaging = Column(Text)
    channels = Column(JSON)
    budget = Column(Float)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    status = Column(String(20), default="draft")
    metrics = Column(JSON)
    created_at = Column(DateTime, default=func.now())
    
    sequences = relationship("EricEmailSequence", back_populates="campaign")

class EricEmailSequence(Base):
    __tablename__ = "eric_email_sequences"
    
    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("eric_sales_campaigns.id"), nullable=False)
    sequence_name = Column(String(200), nullable=False)
    subject_line = Column(String(200))
    email_content = Column(Text)
    delay_days = Column(Integer, default=1)
    sequence_order = Column(Integer, default=1)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    
    campaign = relationship("EricSalesCampaign", back_populates="sequences")

class EricSalesTeam(Base):
    __tablename__ = "eric_sales_teams"
    
    id = Column(Integer, primary_key=True, index=True)
    brand_id = Column(Integer, nullable=False, index=True)
    team_name = Column(String(200), nullable=False)
    team_leader_id = Column(Integer)
    team_members = Column(JSON)
    targets = Column(JSON)
    performance_metrics = Column(JSON)
    created_at = Column(DateTime, default=func.now())

class EricSalesRep(Base):
    __tablename__ = "eric_sales_reps"
    
    id = Column(Integer, primary_key=True, index=True)
    brand_id = Column(Integer, nullable=False, index=True)
    team_id = Column(Integer, ForeignKey("eric_sales_teams.id"))
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    phone = Column(String(20))
    role = Column(String(50))
    quota = Column(Float)
    performance_metrics = Column(JSON)
    skills = Column(JSON)
    created_at = Column(DateTime, default=func.now())
    
    team = relationship("EricSalesTeam")

class EricSalesAnalytics(Base):
    __tablename__ = "eric_sales_analytics"
    
    id = Column(Integer, primary_key=True, index=True)
    brand_id = Column(Integer, nullable=False, index=True)
    date = Column(DateTime, nullable=False)
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Float, nullable=False)
    metric_unit = Column(String(20))
    breakdown = Column(JSON)
    created_at = Column(DateTime, default=func.now())

class EricSalesForecast(Base):
    __tablename__ = "eric_sales_forecasts"
    
    id = Column(Integer, primary_key=True, index=True)
    brand_id = Column(Integer, nullable=False, index=True)
    forecast_date = Column(DateTime, nullable=False)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    predicted_revenue = Column(Float, nullable=False)
    confidence_level = Column(Float)
    factors = Column(JSON)
    created_at = Column(DateTime, default=func.now())

class EricCompetitorAnalysis(Base):
    __tablename__ = "eric_competitor_analysis"
    
    id = Column(Integer, primary_key=True, index=True)
    brand_id = Column(Integer, nullable=False, index=True)
    competitor_name = Column(String(200), nullable=False)
    analysis_date = Column(DateTime, nullable=False)
    pricing_analysis = Column(JSON)
    feature_comparison = Column(JSON)
    market_position = Column(String(50))
    strengths = Column(JSON)
    weaknesses = Column(JSON)
    opportunities = Column(JSON)
    threats = Column(JSON)
    created_at = Column(DateTime, default=func.now())

class EricMarketTrend(Base):
    __tablename__ = "eric_market_trends"
    
    id = Column(Integer, primary_key=True, index=True)
    brand_id = Column(Integer, nullable=False, index=True)
    trend_name = Column(String(200), nullable=False)
    trend_type = Column(String(50))
    description = Column(Text)
    impact_level = Column(String(20))
    affected_segments = Column(JSON)
    recommendations = Column(JSON)
    created_at = Column(DateTime, default=func.now())


class EricMarketInsight(Base):
    __tablename__ = "eric_market_insights"

    id = Column(Integer, primary_key=True, index=True)
    brand_id = Column(Integer, nullable=False, index=True)
    region = Column(String(100), nullable=False)
    industry = Column(String(100), nullable=False, default="general")
    market_size = Column(Float, default=0.0)
    growth_rate = Column(Float, default=0.0)
    competition_level = Column(String(50), default="unknown")
    market_maturity = Column(String(50), default="growing")
    key_opportunities = Column(JSON, default=list)
    challenges = Column(JSON, default=list)
    recommended_strategies = Column(JSON, default=list)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class EricSalesTraining(Base):
    __tablename__ = "eric_sales_training"
    
    id = Column(Integer, primary_key=True, index=True)
    brand_id = Column(Integer, nullable=False, index=True)
    training_name = Column(String(200), nullable=False)
    training_type = Column(String(50))
    content = Column(Text)
    target_audience = Column(JSON)
    duration = Column(Integer)
    completion_rate = Column(Float)
    effectiveness_score = Column(Float)
    created_at = Column(DateTime, default=func.now())

class EricSalesGamification(Base):
    __tablename__ = "eric_sales_gamification"
    
    id = Column(Integer, primary_key=True, index=True)
    brand_id = Column(Integer, nullable=False, index=True)
    rep_id = Column(Integer, nullable=False)
    challenge_name = Column(String(200), nullable=False)
    challenge_type = Column(String(50))
    target_value = Column(Float)
    current_value = Column(Float, default=0.0)
    reward = Column(String(200))
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())

class EricCustomerProfile(Base):
    __tablename__ = "eric_customer_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    brand_id = Column(Integer, nullable=False, index=True)
    customer_id = Column(String(100), nullable=False, index=True)
    first_name = Column(String(100))
    last_name = Column(String(100))
    email = Column(String(255))
    phone = Column(String(20))
    company = Column(String(200))
    job_title = Column(String(100))
    industry = Column(String(100))
    company_size = Column(String(50))
    location = Column(String(100))
    timezone = Column(String(50))
    language = Column(String(10), default="en")
    budget_range = Column(String(50))
    decision_authority = Column(String(50))
    preferred_communication = Column(String(50))
    pain_points = Column(JSON)
    requirements = Column(JSON)
    preferences = Column(JSON)
    engagement_history = Column(JSON)
    lifetime_value = Column(Float, default=0.0)
    total_deals = Column(Integer, default=0)
    avg_deal_size = Column(Float, default=0.0)
    last_purchase_date = Column(DateTime)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class EricCustomerReview(Base):
    __tablename__ = "eric_customer_reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    brand_id = Column(Integer, nullable=False, index=True)
    customer_id = Column(String(100), nullable=False, index=True)
    deal_id = Column(Integer, ForeignKey("eric_deals.id"))
    review_text = Column(Text)
    rating = Column(Integer)  # 1-5 stars
    review_type = Column(String(50))  # testimonial, case_study, reference
    approved = Column(Boolean, default=False)
    featured = Column(Boolean, default=False)
    anonymous = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    
    deal = relationship("EricDeal")


class EricTeamPerformanceMetric(Base):
    __tablename__ = "eric_team_performance_metrics"

    id = Column(Integer, primary_key=True, index=True)
    brand_id = Column(Integer, nullable=False, index=True)
    team_id = Column(Integer, nullable=False)
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Float, nullable=False)
    date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=func.now())


class EricEthicalSalesScore(Base):
    __tablename__ = "eric_ethical_sales_scores"

    id = Column(Integer, primary_key=True, index=True)
    brand_id = Column(Integer, nullable=False, index=True)
    sales_rep_id = Column(Integer, nullable=False)
    overall_score = Column(Float, nullable=False)
    transparency_score = Column(Float, nullable=False)
    pressure_tactics_score = Column(Float, nullable=False)
    honesty_score = Column(Float, nullable=False)
    customer_focus_score = Column(Float, nullable=False)
    compliance_score = Column(Float, nullable=False)
    risk_level = Column(String(50))
    recommendations = Column(JSON)
    date_range = Column(String(50), default="30d")
    created_at = Column(DateTime, default=func.now())

class EricObjectionPredictionModel(Base):
    __tablename__ = "eric_objection_prediction_models"
    
    id = Column(Integer, primary_key=True, index=True)
    brand_id = Column(Integer, nullable=False, index=True)
    model_name = Column(String(200), nullable=False)
    model_type = Column(String(50))
    model_version = Column(String(20))
    accuracy = Column(Float)
    precision = Column(Float)
    recall = Column(Float)
    f1_score = Column(Float)
    training_data_size = Column(Integer)
    last_trained = Column(DateTime)
    model_path = Column(String(500))
    parameters = Column(JSON)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class EricPredictionModel(Base):
    # Namespaced table name to avoid collisions with other agent model definitions
    __tablename__ = "eric_prediction_models"
    
    id = Column(Integer, primary_key=True, index=True)
    brand_id = Column(Integer, nullable=False, index=True)
    model_name = Column(String(200), nullable=False)
    model_type = Column(String(50))  # revenue, conversion, churn
    model_version = Column(String(20))
    accuracy = Column(Float)
    precision = Column(Float)
    recall = Column(Float)
    f1_score = Column(Float)
    training_data_size = Column(Integer)
    last_trained = Column(DateTime)
    model_path = Column(String(500))
    parameters = Column(JSON)
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class EricClosingSequence(Base):
    __tablename__ = "eric_closing_sequences"
    
    id = Column(Integer, primary_key=True, index=True)
    deal_id = Column(String(100), nullable=False, index=True)
    brand_id = Column(Integer, nullable=False, index=True)
    sequence_type = Column(String(50))
    steps = Column(JSON)
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=func.now())
    expected_completion = Column(DateTime)
    completed_at = Column(DateTime)

class EricDealClosing(Base):
    __tablename__ = "eric_deal_closings"
    
    id = Column(Integer, primary_key=True, index=True)
    deal_id = Column(String(100), nullable=False, index=True)
    brand_id = Column(Integer, nullable=False, index=True)
    customer_id = Column(String(100), nullable=False)
    deal_value = Column(Float)
    deal_stage = Column(String(50))
    closing_method = Column(String(50))
    closing_terms = Column(JSON)
    objection_type = Column(String(50))
    objection_status = Column(String(20))
    response_strategy = Column(JSON)
    last_objection_at = Column(DateTime)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class EricDealClosingStage(Base):
    __tablename__ = "eric_deal_closing_stages"
    
    id = Column(Integer, primary_key=True, index=True)
    deal_id = Column(String(100), nullable=False, index=True)
    brand_id = Column(Integer, nullable=False, index=True)
    stage_name = Column(String(100), nullable=False)
    stage_order = Column(Integer)
    status = Column(String(20), default="pending")
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=func.now())

class EricDealClosingStrategy(Base):
    __tablename__ = "eric_deal_closing_strategies"
    
    id = Column(Integer, primary_key=True, index=True)
    deal_id = Column(String(100), nullable=False, index=True)
    brand_id = Column(Integer, nullable=False, index=True)
    strategy_type = Column(String(50))
    approach = Column(String(50))
    timeline = Column(String(100))
    key_messages = Column(JSON)
    objection_handling = Column(JSON)
    created_at = Column(DateTime, default=func.now())

class EricDealClosingTemplate(Base):
    __tablename__ = "eric_deal_closing_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    brand_id = Column(Integer, nullable=False, index=True)
    template_name = Column(String(200), nullable=False)
    template_type = Column(String(50))
    content = Column(JSON)
    conditions = Column(JSON)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())

class EricDealClosingActivity(Base):
    __tablename__ = "eric_deal_closing_activities"
    
    id = Column(Integer, primary_key=True, index=True)
    deal_id = Column(String(100), nullable=False, index=True)
    brand_id = Column(Integer, nullable=False, index=True)
    activity_type = Column(String(50), nullable=False)
    activity_data = Column(JSON)
    scheduled_time = Column(DateTime)
    completed_at = Column(DateTime)
    status = Column(String(20), default="pending")
    created_at = Column(DateTime, default=func.now())
