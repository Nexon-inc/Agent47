from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, JSON, Text, Enum, Float, UniqueConstraint, Index
from sqlalchemy.sql import func
import enum
from core.database.models import Base


class PlatformEnum(enum.Enum):
    instagram = "instagram"
    linkedin = "linkedin"
    twitter = "twitter"
    tiktok = "tiktok"
    youtube = "youtube"
    facebook = "facebook"
    pinterest = "pinterest"
    reddit = "reddit"


class AriaPostStatus(enum.Enum):
    draft = "draft"
    scheduled = "scheduled"
    publishing = "publishing"
    published = "published"
    failed = "failed"


class ApprovalStatus(enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class AriaSocialAccount(Base):
    __tablename__ = "social_accounts"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    platform = Column(Enum(PlatformEnum), nullable=False, index=True)
    handle = Column(String(255), nullable=False)
    oauth_token_enc = Column(Text, nullable=False)
    refresh_token_enc = Column(Text)
    scopes = Column(JSON)
    rate_state = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    __table_args__ = (
        UniqueConstraint("user_id", "platform", "handle", name="uq_user_platform_handle"),
    )


class AriaAccountGroup(Base):
    __tablename__ = "account_groups"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AriaBrandProfile(Base):
    __tablename__ = "brand_profiles"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    voice = Column(JSON, nullable=False, default=dict)
    banned_keywords = Column(JSON, default=list)
    hashtags_bank = Column(JSON, default=list)
    compliance_rules = Column(JSON, default=dict)
    guidelines_url = Column(String(1024))  # Updated from s3_guidelines_url to guidelines_url
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class AriaCampaign(Base):
    __tablename__ = "campaigns"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    objective = Column(String(100), nullable=False)
    budget_cents = Column(Integer, default=0)
    start_at = Column(DateTime(timezone=True))
    end_at = Column(DateTime(timezone=True))
    status = Column(String(50), default="active")
    metrics = Column(JSON, default=dict)


class AriaScheduledPost(Base):
    __tablename__ = "scheduled_posts"
    id = Column(Integer, primary_key=True)
    idempotency_key = Column(String(255), nullable=False, unique=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"))
    account_group_id = Column(Integer, ForeignKey("account_groups.id"))
    platform_targets = Column(JSON, nullable=False)
    buffer_profile_ids = Column(JSON, default=list)
    caption = Column(Text)
    hashtags = Column(JSON, default=list)
    media_refs = Column(JSON, default=list)
    scheduled_at = Column(DateTime(timezone=True), nullable=False, index=True)
    timezone = Column(String(64), default="UTC")
    status = Column(Enum(AriaPostStatus), default=AriaPostStatus.scheduled, index=True)
    last_error = Column(Text)
    geo_lat = Column(Float)
    geo_lng = Column(Float)
    geo_place = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    __table_args__ = (
        Index("ix_user_scheduled_at", "user_id", "scheduled_at"),
    )


class AriaPostVariant(Base):
    __tablename__ = "post_variants"
    id = Column(Integer, primary_key=True)
    scheduled_post_id = Column(Integer, ForeignKey("scheduled_posts.id"), nullable=False, index=True)
    variant_key = Column(String(100), nullable=False)
    caption = Column(Text)
    hashtags = Column(JSON, default=list)
    media_refs = Column(JSON, default=list)
    status = Column(String(50), default="ready")
    metrics = Column(JSON, default=dict)


class AriaPublishedPost(Base):
    __tablename__ = "published_posts"
    id = Column(Integer, primary_key=True)
    scheduled_post_id = Column(Integer, ForeignKey("scheduled_posts.id"), nullable=False, index=True)
    platform = Column(Enum(PlatformEnum), nullable=False, index=True)
    platform_post_id = Column(String(255), nullable=False)
    published_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String(50), default="published")
    permalink = Column(String(1024))
    error = Column(Text)


class AriaApproval(Base):
    __tablename__ = "approvals"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    scheduled_post_id = Column(Integer, ForeignKey("scheduled_posts.id"), nullable=False)
    status = Column(Enum(ApprovalStatus), default=ApprovalStatus.pending)
    reviewers = Column(JSON, default=list)
    comments = Column(JSON, default=list)
    decided_at = Column(DateTime(timezone=True))


class AriaEngagementEvent(Base):
    __tablename__ = "engagement_events"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    platform = Column(Enum(PlatformEnum), nullable=False)
    source = Column(String(50), nullable=False)
    post_ref = Column(String(255), index=True)
    actor_handle = Column(String(255))
    event_type = Column(String(50), nullable=False)
    text = Column(Text)
    sentiment = Column(String(50))
    # 'metadata' is reserved on Declarative base; expose as event_metadata attribute
    event_metadata = Column('metadata', JSON, default=dict)
    occurred_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)


class AriaAnalyticsSnapshot(Base):
    __tablename__ = "analytics_snapshots"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    platform = Column(Enum(PlatformEnum), nullable=False)
    post_ref = Column(String(255), index=True)
    window = Column(String(50), default="1d")
    impressions = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    saves = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    ctr = Column(Float, default=0.0)
    sentiment_score = Column(Float, default=0.0)
    velocity_score = Column(Float, default=0.0)
    snapshot_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)


class AriaTrendSignal(Base):
    __tablename__ = "trend_signals"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    topic = Column(String(255), nullable=False)
    region = Column(String(64), default="global")
    keywords = Column(JSON, default=list)
    source = Column(String(64), nullable=False)
    score = Column(Float, default=0.0)
    freshness_minutes = Column(Integer, default=0)
    captured_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)


class AriaInfluencerLead(Base):
    __tablename__ = "influencer_leads"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    platform = Column(Enum(PlatformEnum), nullable=False)
    handle = Column(String(255), nullable=False)
    audience_size = Column(Integer, default=0)
    relevance_score = Column(Float, default=0.0)
    contact_info = Column(JSON, default=dict)
    status = Column(String(50), default="new")
    discovered_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)


class AriaWebhookEvent(Base):
    __tablename__ = "webhook_events"
    id = Column(Integer, primary_key=True)
    source = Column(String(64), nullable=False)
    signature = Column(String(512))
    payload = Column(JSON, nullable=False)
    processed = Column(Boolean, default=False)
    processed_at = Column(DateTime(timezone=True))
    retry_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)


