from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float, ForeignKey, JSON, Enum, Table, Index, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum
from core.database.models import Base

class ResearchType(enum.Enum):
    MARKET_TREND = "market_trend"
    COMPETITOR_ANALYSIS = "competitor_analysis"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    KEYWORD_RESEARCH = "keyword_research"
    CONSUMER_BEHAVIOR = "consumer_behavior"
    INDUSTRY_REPORT = "industry_report"
    SOCIAL_MEDIA_LISTENING = "social_media_listening"
    DATA_SCRAPING = "data_scraping"
    TREND_FORECASTING = "trend_forecasting"
    NICHE_MARKET = "niche_market"
    CUSTOMER_PERSONA = "customer_persona"
    NEWS_MONITORING = "news_monitoring"
    PATENT_TRACKING = "patent_tracking"
    CUSTOM_QUERY = "custom_query"

class ResearchStatus(enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class DataSource(enum.Enum):
    GOOGLE_TRENDS = "google_trends"
    BRANDWATCH = "brandwatch"
    SEMRUSH = "semrush"
    SIMILARWEB = "similarweb"
    AHREFS = "ahrefs"
    SURVEYMONKEY = "surveymonkey"
    CANVA = "canva"
    HOOTSUITE = "hootsuite"
    TABLEAU = "tableau"
    GOOGLE_NEWS = "google_news"
    GOOGLE_PATENTS = "google_patents"
    TYPEFORM = "typeform"
    SLACK = "slack"
    NOTION = "notion"
    CUSTOM_API = "custom_api"


class PlatformType(enum.Enum):
    TWITTER = "twitter"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    LINKEDIN = "linkedin"
    TIKTOK = "tiktok"
    YOUTUBE = "youtube"
    REDDIT = "reddit"
    PINTEREST = "pinterest"
    SNAPCHAT = "snapchat"


class MentionType(enum.Enum):
    DIRECT = "direct"
    INDIRECT = "indirect"
    HASHTAG = "hashtag"
    USER_MENTION = "user_mention"
    RETWEET = "retweet"

class JoeMarketTrend(Base):
    __tablename__ = "joe_market_trends"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    keyword = Column(String(200), nullable=False)
    region = Column(String(100))
    time_period = Column(String(50))
    trend_data = Column(JSON, nullable=False)
    insights = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])

class JoeCompetitorAnalysis(Base):
    __tablename__ = "joe_competitor_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    competitor_name = Column(String(200), nullable=False)
    competitor_url = Column(String(500))
    analysis_type = Column(String(100))  # website, social_media, pricing
    analysis_data = Column(JSON, nullable=False)
    insights = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])

class JoeSentimentAnalysis(Base):
    __tablename__ = "joe_sentiment_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    brand_name = Column(String(200), nullable=False)
    platform = Column(String(100))  # twitter, facebook, instagram, etc.
    sentiment_data = Column(JSON, nullable=False)
    overall_sentiment = Column(Float)  # -1 to 1 scale
    volume = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])

class KeywordResearch(Base):
    __tablename__ = "keyword_research"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    keyword = Column(String(200), nullable=False)
    search_volume = Column(Integer)
    competition_level = Column(String(50))
    cpc = Column(Float)
    keyword_data = Column(JSON, nullable=False)
    suggestions = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])

class ConsumerBehavior(Base):
    __tablename__ = "consumer_behavior"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    industry = Column(String(200), nullable=False)
    data_source = Column(String(100))
    behavior_data = Column(JSON, nullable=False)
    insights = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])

class JoeIndustryReport(Base):
    __tablename__ = "industry_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    industry = Column(String(200), nullable=False)
    report_title = Column(String(500), nullable=False)
    report_data = Column(JSON, nullable=False)
    visualizations = Column(JSON)
    insights = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])

class JoeSocialMediaListening(Base):
    __tablename__ = "social_media_listening"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    brand_name = Column(String(200), nullable=False)
    platform = Column(String(100))
    hashtags = Column(JSON)
    mentions_data = Column(JSON, nullable=False)
    engagement_metrics = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])

class JoeDataScraping(Base):
    __tablename__ = "data_scraping"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    target_url = Column(String(500), nullable=False)
    scraping_type = Column(String(100))  # website, social_media, forum
    scraped_data = Column(JSON, nullable=False)
    compliance_status = Column(String(50))  # gdpr_compliant, pending_review
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])

class JoeTrendForecast(Base):
    __tablename__ = "trend_forecasts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    trend_name = Column(String(200), nullable=False)
    industry = Column(String(200))
    historical_data = Column(JSON, nullable=False)
    forecast_data = Column(JSON, nullable=False)
    confidence_level = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])

class JoeNicheMarket(Base):
    __tablename__ = "niche_markets"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    niche_name = Column(String(200), nullable=False)
    market_size = Column(String(100))
    growth_potential = Column(Float)
    competition_level = Column(String(50))
    niche_data = Column(JSON, nullable=False)
    opportunities = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])

class JoeCustomerPersona(Base):
    __tablename__ = "customer_personas"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    persona_name = Column(String(200), nullable=False)
    demographics = Column(JSON)
    psychographics = Column(JSON)
    behavior_patterns = Column(JSON)
    pain_points = Column(JSON)
    goals = Column(JSON)
    persona_data = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])

class JoeNewsMonitoring(Base):
    __tablename__ = "news_monitoring"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    topic = Column(String(200), nullable=False)
    keywords = Column(JSON)
    news_data = Column(JSON, nullable=False)
    sentiment = Column(Float)
    relevance_score = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])

class JoePatentTracking(Base):
    __tablename__ = "patent_tracking"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    technology_area = Column(String(200), nullable=False)
    patent_data = Column(JSON, nullable=False)
    innovation_trends = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])

class JoeCustomResearchQuery(Base):
    __tablename__ = "custom_research_queries"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    query = Column(Text, nullable=False)
    query_type = Column(String(100))
    result_data = Column(JSON, nullable=False)
    insights = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])

class JoeResearchProject(Base):
    __tablename__ = "research_projects"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    project_name = Column(String(200), nullable=False)
    description = Column(Text)
    research_type = Column(Enum(ResearchType), nullable=False)
    status = Column(Enum(ResearchStatus), default=ResearchStatus.PENDING)
    data_sources = Column(JSON)
    project_data = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])

class JoeResearchAlert(Base):
    __tablename__ = "research_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    alert_name = Column(String(200), nullable=False)
    alert_type = Column(String(100))  # trend, competitor, keyword
    trigger_conditions = Column(JSON, nullable=False)
    notification_channels = Column(JSON)  # email, slack, etc.
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])

class JoeResearchDashboard(Base):
    __tablename__ = "research_dashboards"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    dashboard_name = Column(String(200), nullable=False)
    dashboard_type = Column(String(100))  # market, competitor, sentiment
    widgets = Column(JSON, nullable=False)
    layout = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])

class JoeSurvey(Base):
    __tablename__ = "surveys"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    survey_name = Column(String(200), nullable=False)
    survey_type = Column(String(100))  # customer, market, product
    questions = Column(JSON, nullable=False)
    responses = Column(JSON)
    analysis_results = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])

class JoeCompetitorBenchmark(Base):
    __tablename__ = "competitor_benchmarks"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    competitor_name = Column(String(200), nullable=False)
    benchmark_metrics = Column(JSON, nullable=False)
    performance_comparison = Column(JSON)
    insights = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])

class JoeMarketOpportunity(Base):
    __tablename__ = "market_opportunities"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    opportunity_name = Column(String(200), nullable=False)
    market_size = Column(String(100))
    competition_level = Column(String(50))
    growth_potential = Column(Float)
    viability_score = Column(Float)
    opportunity_data = Column(JSON, nullable=False)
    recommendations = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])

class JoeResearchAutomation(Base):
    __tablename__ = "research_automations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    automation_name = Column(String(200), nullable=False)
    automation_type = Column(String(100))  # scheduled, trigger_based
    schedule = Column(JSON)
    trigger_conditions = Column(JSON)
    is_active = Column(Boolean, default=True)
    last_run = Column(DateTime(timezone=True))
    next_run = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])


class IntelligenceType(enum.Enum):
    MARKET_SENTIMENT = "market_sentiment"
    COMPETITOR_MOVES = "competitor_moves"
    REGULATORY_CHANGE = "regulatory_change"
    DEMAND_SHIFT = "demand_shift"
    TECHNOLOGY_ADOPTION = "technology_adoption"


class JoeMarketIntelligence(Base):
    __tablename__ = "market_intelligence"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(300), nullable=False)
    intelligence_type = Column(Enum(IntelligenceType), nullable=False)
    source = Column(String(200))
    data = Column(JSON, nullable=False)
    insights = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", foreign_keys=[user_id])


class JoeMarketInsight(Base):
    __tablename__ = "joe_market_insights"

    id = Column(Integer, primary_key=True, index=True)
    intelligence_id = Column(Integer, ForeignKey("market_intelligence.id"), nullable=False, index=True)
    summary = Column(Text, nullable=False)
    impact_score = Column(Float)
    evidence = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    intelligence = relationship("JoeMarketIntelligence", foreign_keys=[intelligence_id])


class JoeLanguage(Base):
    __tablename__ = "languages"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(10), nullable=False, unique=True, index=True)  # e.g. 'en', 'fr'
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<JoeLanguage {self.code}:{self.name}>"


class JoeResearchContext(Base):
    __tablename__ = "research_contexts"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    settings = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "settings": self.settings,
        }


class JoeMultiLanguageResearch(Base):
    __tablename__ = "multi_language_researches"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    research_id = Column(Integer, ForeignKey("research_projects.id"), nullable=True, index=True)
    language_id = Column(Integer, ForeignKey("languages.id"), nullable=False, index=True)
    content = Column(JSON, nullable=False)  # localized content and metadata
    summary = Column(Text)
    context_id = Column(Integer, ForeignKey("research_contexts.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    research = relationship("JoeResearchProject", foreign_keys=[research_id])
    language = relationship("JoeLanguage", foreign_keys=[language_id])
    context = relationship("JoeResearchContext", foreign_keys=[context_id])

    def as_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "research_id": self.research_id,
            "language": getattr(self.language, 'code', None),
            "content": self.content,
            "summary": self.summary,
        }


class Region(Base):
    __tablename__ = "regions"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    code = Column(String(20), nullable=True)
    region_metadata = Column("metadata", JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JoeLocalMarket(Base):
    __tablename__ = "joe_local_markets"

    id = Column(Integer, primary_key=True, index=True)
    region_id = Column(Integer, ForeignKey("regions.id"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    economic_indicators = Column(JSON)
    market_size = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    region = relationship("Region", foreign_keys=[region_id])


class JoeRegionalTrend(Base):
    __tablename__ = "joe_regional_trends"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    region_id = Column(Integer, ForeignKey("regions.id"), nullable=False, index=True)
    trend_data = Column(JSON, nullable=False)
    insights = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    region_rel = relationship("Region", foreign_keys=[region_id])


class GeoSpecificResearch(Base):
    __tablename__ = "geo_specific_research"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    region_id = Column(Integer, ForeignKey("regions.id"), nullable=True)
    market_id = Column(Integer, ForeignKey("joe_local_markets.id"), nullable=True)
    query = Column(Text, nullable=False)
    results = Column(JSON, nullable=False)
    insights = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", foreign_keys=[user_id])
    region_rel = relationship("Region", foreign_keys=[region_id])
    market_rel = relationship("JoeLocalMarket", foreign_keys=[market_id])
