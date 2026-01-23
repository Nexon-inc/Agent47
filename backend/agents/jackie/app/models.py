from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float, ForeignKey, JSON, Enum, Table, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum
from core.database.models import Base

class CampaignStatus(enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    SCHEDULED = "scheduled"

class CampaignType(enum.Enum):
    SOCIAL_MEDIA = "social_media"
    EMAIL = "email"
    SEARCH_ADS = "search_ads"
    DISPLAY_ADS = "display_ads"
    VIDEO_ADS = "video_ads"
    INFLUENCER = "influencer"
    CONTENT_MARKETING = "content_marketing"
    SEO = "seo"
    MULTI_CHANNEL = "multi_channel"

class PlatformType(enum.Enum):
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    TWITTER = "twitter"
    LINKEDIN = "linkedin"
    TIKTOK = "tiktok"
    YOUTUBE = "youtube"
    GOOGLE_ADS = "google_ads"
    EMAIL = "email"
    WEBSITE = "website"

class ContentType(enum.Enum):
    POST = "post"
    STORY = "story"
    VIDEO = "video"
    IMAGE = "image"
    CAROUSEL = "carousel"
    REEL = "reel"
    EMAIL = "email"
    BLOG = "blog"
    AD_COPY = "ad_copy"

class ToneType(enum.Enum):
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    FRIENDLY = "friendly"
    AUTHORITATIVE = "authoritative"
    HUMOROUS = "humorous"
    INSPIRATIONAL = "inspirational"
    EDUCATIONAL = "educational"
    CONVERSATIONAL = "conversational"
    FORMAL = "formal"
    CREATIVE = "creative"

class JackieMarketingCampaign(Base):
    __tablename__ = "marketing_campaigns"
    
    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(String(50), unique=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    campaign_type = Column(Enum(CampaignType), nullable=False)
    status = Column(Enum(CampaignStatus), default=CampaignStatus.DRAFT)
    platforms = Column(JSON, default=[])
    target_audience = Column(JSON, default={})
    budget = Column(Float, default=0.0)
    spent_budget = Column(Float, default=0.0)
    start_date = Column(DateTime(timezone=True))
    end_date = Column(DateTime(timezone=True))
    goals = Column(JSON, default={})
    kpis = Column(JSON, default={})
    performance_metrics = Column(JSON, default={})
    ai_optimization_settings = Column(JSON, default={})
    brand_voice_settings = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    contents = relationship("JackieCampaignContent", back_populates="campaign", cascade="all, delete-orphan")
    ads = relationship("JackieAdCampaign", back_populates="campaign", cascade="all, delete-orphan")
    analytics = relationship("JackieCampaignAnalytics", back_populates="campaign", cascade="all, delete-orphan")
    ab_tests = relationship("JackieABTest", back_populates="campaign", cascade="all, delete-orphan")

class JackieCampaignContent(Base):
    __tablename__ = "campaign_contents"
    
    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("marketing_campaigns.id"), nullable=False)
    content_type = Column(Enum(ContentType), nullable=False)
    platform = Column(Enum(PlatformType), nullable=False)
    title = Column(String(200))
    content = Column(Text, nullable=False)
    media_urls = Column(JSON, default=[])
    hashtags = Column(JSON, default=[])
    scheduled_time = Column(DateTime(timezone=True))
    published_time = Column(DateTime(timezone=True))
    engagement_metrics = Column(JSON, default={})
    ai_generated = Column(Boolean, default=False)
    brand_voice_applied = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    campaign = relationship("JackieMarketingCampaign", back_populates="contents")

class JackieAdCampaign(Base):
    __tablename__ = "ad_campaigns"
    
    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("marketing_campaigns.id"), nullable=False)
    platform = Column(Enum(PlatformType), nullable=False)
    ad_type = Column(String(50), nullable=False)
    ad_group_name = Column(String(200))
    targeting_criteria = Column(JSON, default={})
    ad_creative = Column(JSON, default={})
    budget_allocation = Column(Float, default=0.0)
    bid_strategy = Column(String(50))
    status = Column(String(20), default="draft")
    performance_metrics = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    campaign = relationship("JackieMarketingCampaign", back_populates="ads")

class JackieCampaignAnalytics(Base):
    __tablename__ = "campaign_analytics"
    
    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("marketing_campaigns.id"), nullable=False)
    platform = Column(Enum(PlatformType), nullable=False)
    date = Column(DateTime(timezone=True), nullable=False)
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    conversions = Column(Integer, default=0)
    spend = Column(Float, default=0.0)
    ctr = Column(Float, default=0.0)
    cpc = Column(Float, default=0.0)
    cpm = Column(Float, default=0.0)
    roas = Column(Float, default=0.0)
    engagement_rate = Column(Float, default=0.0)
    reach = Column(Integer, default=0)
    frequency = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    campaign = relationship("JackieMarketingCampaign", back_populates="analytics")

class JackieABTest(Base):
    __tablename__ = "ab_tests"
    
    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("marketing_campaigns.id"), nullable=False)
    test_name = Column(String(200), nullable=False)
    test_type = Column(String(50), nullable=False)
    variant_a = Column(JSON, default={})
    variant_b = Column(JSON, default={})
    traffic_split = Column(Float, default=0.5)
    start_date = Column(DateTime(timezone=True))
    end_date = Column(DateTime(timezone=True))
    status = Column(String(20), default="running")
    results = Column(JSON, default={})
    winner = Column(String(10))
    confidence_level = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    campaign = relationship("JackieMarketingCampaign", back_populates="ab_tests")

class JackieInfluencerCampaign(Base):
    __tablename__ = "influencer_campaigns"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    influencer_name = Column(String(200), nullable=False)
    platform = Column(Enum(PlatformType), nullable=False)
    follower_count = Column(Integer, default=0)
    engagement_rate = Column(Float, default=0.0)
    campaign_brief = Column(Text)
    deliverables = Column(JSON, default=[])
    budget = Column(Float, default=0.0)
    start_date = Column(DateTime(timezone=True))
    end_date = Column(DateTime(timezone=True))
    status = Column(String(20), default="pending")
    performance_metrics = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class JackieCustomerSegment(Base):
    __tablename__ = "customer_segments"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    segment_name = Column(String(200), nullable=False)
    segment_criteria = Column(JSON, default={})
    audience_size = Column(Integer, default=0)
    demographics = Column(JSON, default={})
    interests = Column(JSON, default=[])
    behaviors = Column(JSON, default=[])
    engagement_level = Column(String(20))
    lifetime_value = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class JackieSEOProject(Base):
    __tablename__ = "seo_projects"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    project_name = Column(String(200), nullable=False)
    website_url = Column(String(500))
    target_keywords = Column(JSON, default=[])
    current_rankings = Column(JSON, default={})
    competitor_analysis = Column(JSON, default={})
    optimization_recommendations = Column(JSON, default=[])
    performance_metrics = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class JackieEmailCampaign(Base):
    __tablename__ = "email_campaigns"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    campaign_name = Column(String(200), nullable=False)
    subject_line = Column(String(200))
    sender_name = Column(String(100))
    sender_email = Column(String(200))
    recipient_list = Column(JSON, default=[])
    email_content = Column(Text)
    template_id = Column(String(100))
    scheduled_time = Column(DateTime(timezone=True))
    sent_time = Column(DateTime(timezone=True))
    status = Column(String(20), default="draft")
    performance_metrics = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class JackieLegacyBrandVoice(Base):
    __tablename__ = "brand_voices"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    brand_name = Column(String(200), nullable=False)
    tone = Column(String(50))
    style = Column(String(50))
    personality_traits = Column(JSON, default=[])
    do_dont_list = Column(JSON, default={})
    examples = Column(JSON, default=[])
    guidelines = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JackieContentGeneration(Base):
    __tablename__ = "content_generation"

    id = Column(String(36), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    prompt = Column(Text)
    generated_content = Column(Text)
    metadata_json = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JackieToneAnalysis(Base):
    __tablename__ = "tone_analyses"

    id = Column(String(36), primary_key=True)
    content = Column(Text)
    tone_scores = Column(JSON, default={})
    dominant_tone = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JackieStyleGuide(Base):
    __tablename__ = "style_guides"

    id = Column(String(36), primary_key=True)
    brand_id = Column(Integer, ForeignKey("brand_voices.id"))
    guidelines = Column(Text)
    examples = Column(JSON, default=[])
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class JackieMarketResearch(Base):
    __tablename__ = "jackie_market_research"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    research_name = Column(String(200), nullable=False)
    industry = Column(String(100), nullable=False)
    target_market = Column(JSON, default={})
    competitors = Column(JSON, default=[])
    market_size = Column(JSON, default={})
    trends = Column(JSON, default=[])
    opportunities = Column(JSON, default=[])
    threats = Column(JSON, default=[])
    insights = Column(JSON, default=[])
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class JackieBrandVoice(Base):
    __tablename__ = "jackie_brand_voices"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    tone = Column(Enum(ToneType), nullable=False)
    personality_traits = Column(JSON, default=[])
    do_words = Column(JSON, default=[])
    dont_words = Column(JSON, default=[])
    sample_content = Column(JSON, default=[])
    industry = Column(String(100))
    target_audience = Column(String(200))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", backref="jackie_brand_voices")

class PredictiveAnalytics(Base):
    __tablename__ = "predictive_analytics"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    model_name = Column(String(200), nullable=False)
    extra_metadata = Column("metadata", JSON)
    model_type = Column(String(50), nullable=False)
    target_variable = Column(String(100), nullable=False)
    features = Column(JSON, default=[])
    accuracy_score = Column(Float, default=0.0)
    predictions = Column(JSON, default=[])
    confidence_intervals = Column(JSON, default=[])
    model_performance = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class VideoMarketing(Base):
    __tablename__ = "video_marketing"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    video_name = Column(String(200), nullable=False)
    video_type = Column(String(50), nullable=False)
    platform = Column(Enum(PlatformType), nullable=False)
    video_url = Column(String(500))
    thumbnail_url = Column(String(500))
    duration = Column(Integer, default=0)
    description = Column(Text)
    tags = Column(JSON, default=[])
    target_audience = Column(JSON, default={})
    performance_metrics = Column(JSON, default={})
    ai_generated = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class JackieVoiceMarketing(Base):
    __tablename__ = "voice_marketing"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    voice_name = Column(String(200), nullable=False)
    voice_type = Column(String(50), nullable=False)
    platform = Column(String(100))
    audio_url = Column(String(500))
    script = Column(Text)
    duration = Column(Integer, default=0)
    voice_style = Column(String(50))
    target_audience = Column(JSON, default={})
    performance_metrics = Column(JSON, default={})
    ai_generated = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class VoiceContent(Base):
    __tablename__ = "voice_contents"

    id = Column(String(36), primary_key=True)
    script = Column(Text, nullable=False)
    voice_style = Column(String(50))
    language = Column(String(10), default="en")
    audio_url = Column(String(500))
    transcription = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class VideoContent(Base):
    __tablename__ = "video_contents"

    id = Column(String(36), primary_key=True)
    video_brief = Column(Text)
    target_audience = Column(JSON, default=[])
    platform = Column(String(100))
    video_url = Column(String(500))
    script = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AudioAd(Base):
    __tablename__ = "audio_ads"

    id = Column(String(36), primary_key=True)
    ad_brief = Column(Text)
    target_platform = Column(String(100))
    audio_url = Column(String(500))
    script = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class VideoAd(Base):
    __tablename__ = "video_ads"

    id = Column(String(36), primary_key=True)
    ad_brief = Column(Text)
    target_platform = Column(String(100))
    video_url = Column(String(500))
    script = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class VoiceAd(Base):
    __tablename__ = "voice_ads"

    id = Column(String(36), primary_key=True)
    ad_brief = Column(Text)
    platform = Column(String(100))
    duration = Column(String(50))
    ad_content = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AudioContent(Base):
    __tablename__ = "audio_contents"

    id = Column(String(36), primary_key=True)
    title = Column(String(200))
    url = Column(String(500))
    metadata_json = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# Accessibility models
class JackieAccessibilityContent(Base):
    __tablename__ = "jackie_accessibility_contents"

    id = Column(String(36), primary_key=True)
    content_type = Column(String(100))
    original_content = Column(Text)
    optimized_content = Column(Text)
    alt_text = Column(Text)
    accessibility_score = Column(Float, default=0.0)
    compliance_level = Column(String(50))
    recommendations = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AccessibilityAnalysis(Base):
    __tablename__ = "jackie_accessibility_analyses"

    id = Column(String(36), primary_key=True)
    content_id = Column(String(36), ForeignKey("jackie_accessibility_contents.id"))
    analysis_data = Column(JSON, default={})
    score = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AccessibilityReport(Base):
    __tablename__ = "jackie_accessibility_reports"

    id = Column(String(36), primary_key=True)
    content_url = Column(String(500))
    report_type = Column(String(100))
    report_data = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# E-commerce integration models
class JackieEcommerceConnection(Base):
    __tablename__ = "jackie_ecommerce_connections"

    id = Column(String(36), primary_key=True)
    platform = Column(String(100))
    credentials = Column(JSON, default={})
    connected_at = Column(DateTime(timezone=True), server_default=func.now())


class JackieProductSync(Base):
    __tablename__ = "jackie_product_syncs"

    id = Column(String(36), primary_key=True)
    product_id = Column(String(100))
    external_id = Column(String(100))
    sync_status = Column(String(50))
    details = Column(JSON, default={})
    synced_at = Column(DateTime(timezone=True), server_default=func.now())


class OrderSync(Base):
    __tablename__ = "jackie_order_syncs"

    id = Column(String(36), primary_key=True)
    order_id = Column(String(100))
    external_order_id = Column(String(100))
    sync_status = Column(String(50))
    details = Column(JSON, default={})
    synced_at = Column(DateTime(timezone=True), server_default=func.now())


class CustomerSync(Base):
    __tablename__ = "jackie_customer_syncs"

    id = Column(String(36), primary_key=True)
    customer_id = Column(String(100))
    external_customer_id = Column(String(100))
    sync_status = Column(String(50))
    details = Column(JSON, default={})
    synced_at = Column(DateTime(timezone=True), server_default=func.now())


class InventorySync(Base):
    __tablename__ = "jackie_inventory_syncs"

    id = Column(String(36), primary_key=True)
    sku = Column(String(100))
    external_sku = Column(String(100))
    quantity = Column(Integer, default=0)
    sync_status = Column(String(50))
    details = Column(JSON, default={})
    synced_at = Column(DateTime(timezone=True), server_default=func.now())


class VoiceScript(Base):
    __tablename__ = "voice_scripts"

    id = Column(String(36), primary_key=True)
    script_brief = Column(Text)
    voice_style = Column(String(100))
    target_audience = Column(String(200))
    script_content = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JackieAdPlatform(Base):
    __tablename__ = "ad_platforms"

    id = Column(String(36), primary_key=True)
    platform = Column(String(100))
    ad_content = Column(JSON, default={})
    platform_requirements = Column(JSON, default={})
    optimization_data = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CampaignEvent(Base):
    __tablename__ = "campaign_events"

    id = Column(String(36), primary_key=True)
    campaign_id = Column(String(50), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    start_time = Column(DateTime(timezone=True))
    end_time = Column(DateTime(timezone=True))
    location = Column(String(200))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CalendarView(Base):
    __tablename__ = "calendar_views"

    id = Column(String(36), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    view_type = Column(String(50), default="month")
    settings = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JackieTimelineEvent(Base):
    __tablename__ = "timeline_events"

    id = Column(String(36), primary_key=True)
    campaign_id = Column(String(50), nullable=False)
    event_time = Column(DateTime(timezone=True))
    summary = Column(Text)
    details = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ScheduleConflict(Base):
    __tablename__ = "schedule_conflicts"

    id = Column(String(36), primary_key=True)
    event_id = Column(String(36), nullable=False)
    conflict_with_event_id = Column(String(36), nullable=False)
    reason = Column(Text)
    resolved = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class OrganicStrategy(Base):
    __tablename__ = "organic_strategies"

    id = Column(String(36), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    strategy_name = Column(String(200), nullable=False)
    objectives = Column(JSON, default={})
    tactics = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JackieContentPiece(Base):
    __tablename__ = "jackie_content_pieces"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200))
    body = Column(Text)
    content_type = Column(String(50))
    metadata_json = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JackieSocialPost(Base):
    __tablename__ = "social_posts"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    content_piece_id = Column(Integer, ForeignKey("content_pieces.id"), nullable=False)
    platform = Column(String(100))
    scheduled_time = Column(DateTime(timezone=True))
    published_time = Column(DateTime(timezone=True))
    engagement_metrics = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JackieCommunityEngagement(Base):
    __tablename__ = "community_engagements"

    id = Column(String(36), primary_key=True)
    post_id = Column(String(36), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    engagement_type = Column(String(50))
    content = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JackieMobileCampaign(Base):
    __tablename__ = "mobile_campaigns"

    id = Column(String(36), primary_key=True)
    campaign_name = Column(String(200), nullable=False)
    app_id = Column(String(100))
    audience = Column(JSON, default={})
    push_schedule = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JackiePushNotification(Base):
    __tablename__ = "push_notifications"

    id = Column(String(36), primary_key=True)
    campaign_id = Column(String(36), nullable=False)
    title = Column(String(200))
    body = Column(Text)
    data = Column(JSON, default={})
    scheduled_time = Column(DateTime(timezone=True))
    sent_time = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class MobileContent(Base):
    __tablename__ = "mobile_contents"

    id = Column(String(36), primary_key=True)
    campaign_id = Column(String(36), nullable=False)
    content = Column(Text)
    content_type = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AppEngagement(Base):
    __tablename__ = "app_engagements"

    id = Column(String(36), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    event = Column(String(200))
    metadata_json = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JackieDeepAnalytics(Base):
    __tablename__ = "deep_analytics"

    id = Column(String(36), primary_key=True)
    campaign_id = Column(String(50), nullable=False)
    metrics = Column(JSON, default={})
    insights = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JackieSentimentAnalysis(Base):
    __tablename__ = "jackie_sentiment_analyses"

    id = Column(String(36), primary_key=True)
    text = Column(Text, nullable=False)
    sentiment = Column(String(50))
    score = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class BenchmarkData(Base):
    __tablename__ = "benchmark_data"

    id = Column(String(36), primary_key=True)
    industry = Column(String(100))
    metrics = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JackieActionableInsight(Base):
    __tablename__ = "actionable_insights"

    id = Column(String(36), primary_key=True)
    insight = Column(Text)
    score = Column(Float)
    related_metric = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JackieOnboardingSession(Base):
    __tablename__ = "jackie_onboarding_sessions"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    state = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JackieTutorialStep(Base):
    __tablename__ = "tutorial_steps"

    id = Column(String(36), primary_key=True)
    step_name = Column(String(200), nullable=False)
    description = Column(Text)
    order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JackieSetupWizard(Base):
    __tablename__ = "setup_wizards"

    id = Column(String(36), primary_key=True)
    name = Column(String(200), nullable=False)
    steps = Column(JSON, default=[])
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JackieUserProgress(Base):
    __tablename__ = "user_progress"

    id = Column(String(36), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    progress = Column(JSON, default={})
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JackieInteractivePoll(Base):
    __tablename__ = "interactive_polls"

    id = Column(String(36), primary_key=True)
    question = Column(Text, nullable=False)
    options = Column(JSON, default=[])
    results = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JackieCampaignQuiz(Base):
    __tablename__ = "campaign_quizzes"

    id = Column(String(36), primary_key=True)
    title = Column(String(200))
    questions = Column(JSON, default=[])
    results = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JackieEmailSurvey(Base):
    __tablename__ = "email_surveys"

    id = Column(String(36), primary_key=True)
    campaign_id = Column(String(50))
    survey_data = Column(JSON, default={})
    results = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JackieInteractiveContent(Base):
    __tablename__ = "interactive_contents"

    id = Column(String(36), primary_key=True)
    content_type = Column(String(50))
    payload = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JackiePlatformOptimization(Base):
    __tablename__ = "platform_optimizations"

    id = Column(String(36), primary_key=True)
    platform = Column(String(100))
    optimization_rules = Column(JSON, default={})
    metrics = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JackieEmergingChannel(Base):
    __tablename__ = "emerging_channels"

    id = Column(String(36), primary_key=True)
    name = Column(String(100))
    characteristics = Column(JSON, default={})
    adoption_rate = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JackiePlatformContent(Base):
    __tablename__ = "platform_contents"

    id = Column(String(36), primary_key=True)
    platform = Column(String(100))
    content_payload = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JackieChannelStrategy(Base):
    __tablename__ = "channel_strategies"

    id = Column(String(36), primary_key=True)
    strategy_name = Column(String(200))
    details = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JackieLaunchProject(Base):
    __tablename__ = "launch_projects"

    id = Column(String(36), primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    start_date = Column(DateTime(timezone=True))
    end_date = Column(DateTime(timezone=True))
    status = Column(String(50), default="planning")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JackieMarketingFunnel(Base):
    __tablename__ = "marketing_funnels"

    id = Column(String(36), primary_key=True)
    project_id = Column(String(36), nullable=False)
    stages = Column(JSON, default={})
    metrics = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JackieLandingPage(Base):
    __tablename__ = "landing_pages"

    id = Column(String(36), primary_key=True)
    url = Column(String(500))
    content = Column(Text)
    conversion_metrics = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JackieEmailFlow(Base):
    __tablename__ = "email_flows"

    id = Column(String(36), primary_key=True)
    project_id = Column(String(36), nullable=False)
    sequence = Column(JSON, default=[])
    metrics = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JackieCustomerSearch(Base):
    __tablename__ = "customer_searches"

    id = Column(String(36), primary_key=True)
    query = Column(Text)
    filters = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JackieSearchResult(Base):
    __tablename__ = "search_results"

    id = Column(String(36), primary_key=True)
    search_id = Column(String(36), nullable=False)
    result = Column(JSON, default={})
    score = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JackieSocialProfile(Base):
    __tablename__ = "social_profiles"

    id = Column(String(36), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    platform = Column(String(100))
    profile_data = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JackieCustomerMatch(Base):
    __tablename__ = "customer_matches"

    id = Column(String(36), primary_key=True)
    customer_id = Column(String(36), nullable=False)
    matched_profile_id = Column(String(36), nullable=False)
    confidence = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JackieChatbotConversation(Base):
    __tablename__ = "chatbot_conversations"

    id = Column(String(36), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    messages = Column(JSON, default=[])
    started_at = Column(DateTime(timezone=True))
    ended_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JackieEmpathyResponse(Base):
    __tablename__ = "empathy_responses"

    id = Column(String(36), primary_key=True)
    conversation_id = Column(String(36), nullable=False)
    response_text = Column(Text)
    score = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JackieContextSession(Base):
    __tablename__ = "context_sessions"

    id = Column(String(36), primary_key=True)
    session_data = Column(JSON, default={})
    last_active = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JackieConversationFlow(Base):
    __tablename__ = "conversation_flows"

    id = Column(String(36), primary_key=True)
    flow_definition = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JackiePersonalizationRule(Base):
    __tablename__ = "personalization_rules"

    id = Column(String(36), primary_key=True)
    rule_name = Column(String(200))
    conditions = Column(JSON, default={})
    actions = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JackieDynamicContent(Base):
    __tablename__ = "dynamic_contents"

    id = Column(String(36), primary_key=True)
    content_payload = Column(JSON, default={})
    targeting_rules = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JackieBudgetAllocation(Base):
    __tablename__ = "budget_allocations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    campaign_id = Column(Integer, ForeignKey("marketing_campaigns.id"))
    platform = Column(Enum(PlatformType), nullable=False)
    allocated_budget = Column(Float, nullable=False)
    spent_budget = Column(Float, default=0.0)
    daily_limit = Column(Float, default=0.0)
    weekly_limit = Column(Float, default=0.0)
    monthly_limit = Column(Float, default=0.0)
    optimization_rules = Column(JSON, default={})
    performance_thresholds = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class JackieCRMINtegration(Base):
    __tablename__ = "crm_integrations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    crm_platform = Column(String(100), nullable=False)
    api_key = Column(String(500))
    api_secret = Column(String(500))
    access_token = Column(String(500))
    refresh_token = Column(String(500))
    account_id = Column(String(100))
    is_active = Column(Boolean, default=True)
    sync_settings = Column(JSON, default={})
    last_sync = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

# Alias for legacy import name
CRMIntegration = JackieCRMINtegration

class JackieCustomerFeedback(Base):
    __tablename__ = "jackie_customer_feedback"
    __table_args__ = {'extend_existing': True}
    
    id = Column(String(36), primary_key=True)
    campaign_id = Column(String(50), nullable=False)
    feedback_data = Column(Text, nullable=False)
    feedback_type = Column(String(50), default="survey")
    feedback_result = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JackiePerformanceForecast(Base):
    __tablename__ = "performance_forecasts"

    id = Column(String(36), primary_key=True)
    campaign_id = Column(String(50), nullable=False)
    forecast_date = Column(DateTime(timezone=True))
    predicted_metrics = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JackieForecastModel(Base):
    __tablename__ = "forecast_models"

    id = Column(String(36), primary_key=True)
    model_name = Column(String(200))
    parameters = Column(JSON, default={})
    performance = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JackiePredictionResult(Base):
    __tablename__ = "prediction_results"

    id = Column(String(36), primary_key=True)
    forecast_id = Column(String(36), ForeignKey("performance_forecasts.id"), nullable=False)
    results = Column(JSON, default={})
    score = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JackieHistoricalData(Base):
    __tablename__ = "historical_data"

    id = Column(String(36), primary_key=True)
    data = Column(JSON, default={})
    source = Column(String(200))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JackieBudgetRule(Base):
    __tablename__ = "budget_rules"

    id = Column(String(36), primary_key=True)
    name = Column(String(200))
    conditions = Column(JSON, default={})
    actions = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JackieSpendingLimit(Base):
    __tablename__ = "spending_limits"

    id = Column(String(36), primary_key=True)
    campaign_id = Column(String(36), nullable=False)
    daily_limit = Column(Float, default=0.0)
    weekly_limit = Column(Float, default=0.0)
    monthly_limit = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JackieBudgetAlert(Base):
    __tablename__ = "budget_alerts"

    id = Column(String(36), primary_key=True)
    campaign_id = Column(String(36), nullable=False)
    threshold = Column(Float)
    triggered = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JackiePacingRule(Base):
    __tablename__ = "pacing_rules"

    id = Column(String(36), primary_key=True)
    campaign_id = Column(String(36), nullable=False)
    pacing_settings = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JackieCampaignStoryboard(Base):
    __tablename__ = "campaign_storyboards"

    id = Column(String(36), primary_key=True)
    campaign_id = Column(String(36), nullable=False)
    title = Column(String(200))
    scenes = Column(JSON, default=[])
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JackieStoryboardScene(Base):
    __tablename__ = "storyboard_scenes"

    id = Column(String(36), primary_key=True)
    storyboard_id = Column(String(36), nullable=False)
    scene_data = Column(JSON, default={})
    order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JackieFlowVisualization(Base):
    __tablename__ = "flow_visualizations"

    id = Column(String(36), primary_key=True)
    visualization_data = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JackieChannelFlow(Base):
    __tablename__ = "channel_flows"

    id = Column(String(36), primary_key=True)
    channel = Column(String(100))
    flow = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JackieInfluencerPerformance(Base):
    __tablename__ = "influencer_performances"

    id = Column(String(36), primary_key=True)
    influencer_name = Column(String(200))
    metrics = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JackiePerformanceMetric(Base):
    __tablename__ = "performance_metrics"

    id = Column(String(36), primary_key=True)
    name = Column(String(200))
    value = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JackieROIAnalysis(Base):
    __tablename__ = "roi_analyses"

    id = Column(String(36), primary_key=True)
    campaign_id = Column(String(36), nullable=False)
    roi = Column(Float)
    details = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JackieReachTracking(Base):
    __tablename__ = "reach_tracking"

    id = Column(String(36), primary_key=True)
    campaign_id = Column(String(36), nullable=False)
    reach = Column(Integer, default=0)
    impressions = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JackieAllocationRule(Base):
    __tablename__ = "allocation_rules"

    id = Column(String(36), primary_key=True)
    campaign_id = Column(String(36), nullable=False)
    rules = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JackiePerformanceThreshold(Base):
    __tablename__ = "performance_thresholds"

    id = Column(String(36), primary_key=True)
    metric = Column(String(100))
    threshold = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JackieBudgetAdjustment(Base):
    __tablename__ = "budget_adjustments"

    id = Column(String(36), primary_key=True)
    campaign_id = Column(String(36), nullable=False)
    adjustment = Column(Float)
    reason = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JackieInfluencerROIPrediction(Base):
    __tablename__ = "influencer_roi_predictions"

    id = Column(String(36), primary_key=True)
    influencer_id = Column(String(36))
    predicted_roi = Column(Float)
    confidence = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JackiePredictionModel(Base):
    __tablename__ = "jackie_prediction_models"
    __table_args__ = {'extend_existing': True}

    id = Column(String(36), primary_key=True)
    model_name = Column(String(200))
    params = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JackieHistoricalROI(Base):
    __tablename__ = "historical_roi"

    id = Column(String(36), primary_key=True)
    influencer_id = Column(String(36))
    roi_data = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JackieInfluencerMetrics(Base):
    __tablename__ = "influencer_metrics"

    id = Column(String(36), primary_key=True)
    influencer_id = Column(String(36))
    metrics = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JackieGeoTargetedAd(Base):
    __tablename__ = "geo_targeted_ads"

    id = Column(String(36), primary_key=True)
    campaign_id = Column(String(36), nullable=False)
    geo_targeting = Column(JSON, default={})
    ad_content = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JackieLocalMarket(Base):
    __tablename__ = "jackie_local_markets"

    id = Column(String(36), primary_key=True)
    name = Column(String(200))
    demographics = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JackieGeographicData(Base):
    __tablename__ = "geographic_data"

    id = Column(String(36), primary_key=True)
    region = Column(String(200))
    data = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JackieRegionalStrategy(Base):
    __tablename__ = "regional_strategies"

    id = Column(String(36), primary_key=True)
    region = Column(String(200))
    strategy = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JackieVersionChange(Base):
    __tablename__ = "version_changes"

    id = Column(String(36), primary_key=True)
    version_id = Column(String(36), nullable=False)
    change_data = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JackieCampaignRollback(Base):
    __tablename__ = "campaign_rollbacks"

    id = Column(String(36), primary_key=True)
    campaign_id = Column(String(36), nullable=False)
    target_version_id = Column(String(36), nullable=False)
    rollback_notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JackieTranslationData(Base):
    __tablename__ = "translation_data"

    id = Column(String(36), primary_key=True)
    source_text = Column(Text)
    translated_text = Column(Text)
    source_language = Column(String(10))
    target_language = Column(String(10))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JackieLanguageAnalytics(Base):
    __tablename__ = "language_analytics"

    id = Column(String(36), primary_key=True)
    language = Column(String(10))
    metrics = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class JackieSurveyData(Base):
    __tablename__ = "survey_data"
    
    id = Column(String(36), primary_key=True)
    survey_id = Column(String(50), nullable=False)
    survey_responses = Column(Text, nullable=False)
    analysis_result = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class JackieFeedbackAnalysis(Base):
    __tablename__ = "feedback_analysis"
    
    id = Column(String(36), primary_key=True)
    feedback_id = Column(String(36), nullable=False)
    analysis_data = Column(Text, nullable=False)
    insights = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class JackieCampaignRefinement(Base):
    __tablename__ = "campaign_refinements"
    
    id = Column(String(36), primary_key=True)
    campaign_id = Column(String(50), nullable=False)
    feedback_insights = Column(Text, nullable=False)
    refinement_data = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class JackieEthicalAdScan(Base):
    __tablename__ = "ethical_ad_scans"
    
    id = Column(String(36), primary_key=True)
    ad_content = Column(Text, nullable=False)
    ad_type = Column(String(50), default="general")
    platform = Column(String(50), default="all")
    scan_result = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# Campaign ideation / research models
class JackieCampaignIdea(Base):
    __tablename__ = "jackie_campaign_ideas"

    id = Column(String(36), primary_key=True)
    title = Column(String(200))
    description = Column(Text)
    author_id = Column(Integer, ForeignKey("users.id"))
    tags = Column(JSON, default=[])
    status = Column(String(50), default="draft")
    metrics = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JackieTrendAnalysis(Base):
    __tablename__ = "jackie_trend_analyses"

    id = Column(String(36), primary_key=True)
    region = Column(String(200))
    trend_type = Column(String(100))
    data = Column(JSON, default={})
    analyzed_at = Column(DateTime(timezone=True), server_default=func.now())


class JackieCompetitorAnalysis(Base):
    __tablename__ = "jackie_competitor_analyses"

    id = Column(String(36), primary_key=True)
    competitor_name = Column(String(200))
    overview = Column(Text)
    insights = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JackieBrainstormingSession(Base):
    __tablename__ = "jackie_brainstorming_sessions"

    id = Column(String(36), primary_key=True)
    session_name = Column(String(200))
    topics = Column(JSON, default=[])
    participants = Column(JSON, default=[])
    output_ideas = Column(JSON, default=[])
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class JackieComplianceCheck(Base):
    __tablename__ = "compliance_checks"
    
    id = Column(String(36), primary_key=True)
    ad_data = Column(Text, nullable=False)
    compliance_rules = Column(Text, nullable=False)
    compliance_result = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class JackieEthicalReview(Base):
    __tablename__ = "jackie_ethical_reviews"

    id = Column(String(36), primary_key=True)
    content = Column(Text, nullable=False)
    content_type = Column(String(100))
    target_audience = Column(JSON, default=[])
    industry = Column(String(100))
    review_criteria = Column(JSON, default={})
    review_result = Column(JSON, default={})
    ethical_score = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class JackieAdViolation(Base):
    __tablename__ = "ad_violations"
    
    id = Column(String(36), primary_key=True)
    ad_id = Column(String(50), nullable=False)
    violation_type = Column(String(50), nullable=False)
    violation_details = Column(Text, nullable=False)
    violation_result = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class JackieEthicalGuideline(Base):
    __tablename__ = "ethical_guidelines"
    
    id = Column(String(36), primary_key=True)
    guideline_name = Column(String(200), nullable=False)
    guideline_content = Column(Text, nullable=False)
    guideline_type = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class JackieCrossChannelAnalytics(Base):
    __tablename__ = "cross_channel_analytics"
    
    id = Column(String(36), primary_key=True)
    campaign_id = Column(String(50), nullable=False)
    channel_data = Column(Text, nullable=False)
    unified_data = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class JackieUnifiedMetrics(Base):
    __tablename__ = "unified_metrics"
    
    id = Column(String(36), primary_key=True)
    campaign_id = Column(String(50), nullable=False)
    channel_data = Column(Text, nullable=False)
    unified_data = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class JackieChannelComparison(Base):
    __tablename__ = "channel_comparisons"
    
    id = Column(String(36), primary_key=True)
    channels = Column(Text, nullable=False)
    comparison_metrics = Column(Text, nullable=False)
    comparison_data = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class JackiePerformanceInsight(Base):
    __tablename__ = "performance_insights"
    
    id = Column(String(36), primary_key=True)
    analytics_data = Column(Text, nullable=False)
    insight_focus = Column(Text, nullable=False)
    insight_data = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class JackieInteractiveWidget(Base):
    __tablename__ = "interactive_widgets"
    
    id = Column(String(36), primary_key=True)
    widget_type = Column(String(50), nullable=False)
    widget_config = Column(Text, nullable=False)
    ad_id = Column(String(50), nullable=False)
    widget_data = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class JackieAdPoll(Base):
    __tablename__ = "ad_polls"
    
    id = Column(String(36), primary_key=True)
    poll_question = Column(String(500), nullable=False)
    poll_options = Column(Text, nullable=False)
    ad_id = Column(String(50), nullable=False)
    poll_data = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class JackieCallToAction(Base):
    __tablename__ = "call_to_actions"
    
    id = Column(String(36), primary_key=True)
    cta_text = Column(String(200), nullable=False)
    cta_type = Column(String(50), nullable=False)
    action_url = Column(String(500), nullable=False)
    ad_id = Column(String(50), nullable=False)
    cta_data = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class JackieWidgetAnalytics(Base):
    __tablename__ = "widget_analytics"
    
    id = Column(String(36), primary_key=True)
    widget_id = Column(String(36), nullable=False)
    analytics_data = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class JackieCampaignVersion(Base):
    __tablename__ = "campaign_versions"
    
    id = Column(String(36), primary_key=True)
    campaign_id = Column(String(50), nullable=False)
    version_data = Column(Text, nullable=False)
    version_notes = Column(Text)
    version_result = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class JackieVersionHistory(Base):
    __tablename__ = "version_histories"
    
    id = Column(String(36), primary_key=True)
    campaign_id = Column(String(50), nullable=False)
    version_history = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class JackieChangeTracking(Base):
    __tablename__ = "change_trackings"
    
    id = Column(String(36), primary_key=True)
    campaign_id = Column(String(50), nullable=False)
    changes_made = Column(Text, nullable=False)
    change_type = Column(String(50), nullable=False)
    change_result = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class JackieRollbackAction(Base):
    __tablename__ = "rollback_actions"
    
    id = Column(String(36), primary_key=True)
    campaign_id = Column(String(50), nullable=False)
    target_version_id = Column(String(36), nullable=False)
    rollback_data = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class JackieMultiLanguageCampaign(Base):
    __tablename__ = "multi_language_campaigns"
    
    id = Column(String(36), primary_key=True)
    campaign_brief = Column(Text, nullable=False)
    target_languages = Column(Text, nullable=False)
    campaign_data = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class JackieLanguageTranslation(Base):
    __tablename__ = "language_translations"
    
    id = Column(String(36), primary_key=True)
    content = Column(Text, nullable=False)
    source_language = Column(String(10), nullable=False)
    target_language = Column(String(10), nullable=False)
    translation_data = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class JackieCulturalAdaptation(Base):
    __tablename__ = "cultural_adaptations"
    
    id = Column(String(36), primary_key=True)
    campaign_content = Column(Text, nullable=False)
    target_culture = Column(String(100), nullable=False)
    adaptation_data = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class JackieLocalizedContent(Base):
    __tablename__ = "localized_contents"
    
    id = Column(String(36), primary_key=True)
    original_content = Column(Text, nullable=False)
    localized_content = Column(Text, nullable=False)
    target_locale = Column(String(10), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JackieRegionalTrend(Base):
    __tablename__ = "jackie_regional_trends"

    id = Column(String(36), primary_key=True)
    region = Column(String(200))
    trend_data = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JackieCulturalAnalysis(Base):
    __tablename__ = "cultural_analyses"

    id = Column(String(36), primary_key=True)
    locale = Column(String(50))
    analysis = Column(JSON, default={})
    insights = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JackieTranslationProject(Base):
    __tablename__ = "translation_projects"

    id = Column(String(36), primary_key=True)
    source_language = Column(String(10))
    target_language = Column(String(10))
    content_count = Column(Integer, default=0)
    status = Column(String(50), default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class JackieVideoTemplate(Base):
    __tablename__ = "video_templates"
    
    id = Column(String(36), primary_key=True)
    template_type = Column(String(50), nullable=False)
    template_config = Column(Text, nullable=False)
    brand_guidelines = Column(Text, nullable=False)
    template_data = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class JackieVoiceTemplate(Base):
    __tablename__ = "voice_templates"
    
    id = Column(String(36), primary_key=True)
    voice_type = Column(String(50), nullable=False)
    voice_config = Column(Text, nullable=False)
    audio_style = Column(String(50), nullable=False)
    voice_data = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class JackieAnimationAsset(Base):
    __tablename__ = "animation_assets"
    
    id = Column(String(36), primary_key=True)
    animation_type = Column(String(50), nullable=False)
    animation_config = Column(Text, nullable=False)
    duration = Column(String(20), nullable=False)
    animation_data = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class JackieDesignElement(Base):
    __tablename__ = "design_elements"
    
    id = Column(String(36), primary_key=True)
    element_type = Column(String(50), nullable=False)
    element_config = Column(Text, nullable=False)
    design_style = Column(String(50), nullable=False)
    element_data = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JackieCollaborationProject(Base):
    __tablename__ = "jackie_collaboration_projects"

    id = Column(String(36), primary_key=True)
    name = Column(String(200))
    description = Column(Text)
    owner_id = Column(Integer, ForeignKey("users.id"))
    settings = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JackieTeamMember(Base):
    __tablename__ = "jackie_team_members"

    id = Column(String(36), primary_key=True)
    project_id = Column(String(36), ForeignKey("jackie_collaboration_projects.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    role = Column(String(100))
    joined_at = Column(DateTime(timezone=True), server_default=func.now())


class JackieComment(Base):
    __tablename__ = "jackie_comments"

    id = Column(String(36), primary_key=True)
    project_id = Column(String(36), ForeignKey("jackie_collaboration_projects.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    content = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JackieReview(Base):
    __tablename__ = "jackie_reviews"

    id = Column(String(36), primary_key=True)
    project_id = Column(String(36), ForeignKey("jackie_collaboration_projects.id"))
    reviewer_id = Column(Integer, ForeignKey("users.id"))
    comments = Column(JSON, default={})
    status = Column(String(50), default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JackieVersion(Base):
    __tablename__ = "jackie_versions_collaborative"

    id = Column(String(36), primary_key=True)
    project_id = Column(String(36), ForeignKey("jackie_collaboration_projects.id"))
    version_data = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JackieTask(Base):
    __tablename__ = "jackie_tasks"

    id = Column(String(36), primary_key=True)
    project_id = Column(String(36), ForeignKey("jackie_collaboration_projects.id"))
    title = Column(String(200))
    description = Column(Text)
    assignee_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String(50), default="open")
    due_date = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# Agent integration models used by agent integration service and routers
class JackieAgentConnection(Base):
    __tablename__ = "agent_connections"

    id = Column(String(36), primary_key=True)
    source_agent = Column(String(100), nullable=False)
    target_agent = Column(String(100), nullable=False)
    connection_type = Column(String(50), default="kafka")
    config = Column(JSON, default={})
    status = Column(String(50), default="connecting")
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    connected_at = Column(DateTime(timezone=True))
    disconnected_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class JackieAgentEvent(Base):
    __tablename__ = "agent_events"

    id = Column(String(36), primary_key=True)
    source_agent = Column(String(100))
    event_type = Column(String(100))
    payload = Column(JSON, default={})
    target_agents = Column(JSON, default=[])
    status = Column(String(50), default="received")
    published_count = Column(Integer, default=0)
    failed_agents = Column(JSON, default=[])
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JackieAgentSyncData(Base):
    __tablename__ = "agent_sync_data"

    id = Column(String(36), primary_key=True)
    source_agent = Column(String(100))
    target_agent = Column(String(100))
    data_type = Column(String(100))
    data = Column(JSON, default={})
    sync_config = Column(JSON, default={})
    status = Column(String(50), default="pending")
    error_message = Column(Text)
    response_data = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
