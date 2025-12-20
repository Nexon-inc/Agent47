from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float, ForeignKey, JSON, Enum, Table, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum
from core.database.models import Base

class ContentType(enum.Enum):
    BLOG_POST = "blog_post"
    SOCIAL_MEDIA = "social_media"
    EMAIL = "email"
    AD_COPY = "ad_copy"
    VIDEO_SCRIPT = "video_script"
    PODCAST_SCRIPT = "podcast_script"
    WEBSITE_CONTENT = "website_content"
    LANDING_PAGE = "landing_page"
    NEWSLETTER = "newsletter"
    PRODUCT_DESCRIPTION = "product_description"

class PlatformType(enum.Enum):
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    TWITTER = "twitter"
    LINKEDIN = "linkedin"
    TIKTOK = "tiktok"
    YOUTUBE = "youtube"
    PINTEREST = "pinterest"
    SNAPCHAT = "snapchat"
    THREADS = "threads"
    EMAIL = "email"
    WEBSITE = "website"
    BLOG = "blog"

class ContentStatus(enum.Enum):
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    REJECTED = "rejected"

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

class SEOStatus(enum.Enum):
    NOT_OPTIMIZED = "not_optimized"
    BASIC_OPTIMIZED = "basic_optimized"
    FULLY_OPTIMIZED = "fully_optimized"
    EXPERT_OPTIMIZED = "expert_optimized"

class ContentProject(Base):
    __tablename__ = "content_projects"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    content_type = Column(Enum(ContentType), nullable=False)
    platform = Column(Enum(PlatformType), nullable=False)
    target_audience = Column(String(200))
    brand_voice = Column(String(100))
    tone = Column(Enum(ToneType), default=ToneType.PROFESSIONAL)
    keywords = Column(JSON, default=[])
    seo_status = Column(Enum(SEOStatus), default=SEOStatus.NOT_OPTIMIZED)
    status = Column(Enum(ContentStatus), default=ContentStatus.DRAFT)
    word_count_target = Column(Integer)
    deadline = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    published_at = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("User", backref="content_projects")
    content_pieces = relationship("backend.agents.shakes.app.models.ContentPiece", back_populates="project", cascade="all, delete-orphan")
    seo_analysis = relationship("SEOAnalysis", back_populates="project", uselist=False)
    performance_metrics = relationship("ContentPerformance", back_populates="project", cascade="all, delete-orphan")

class ContentPiece(Base):
    __tablename__ = "shakes_content_pieces"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("content_projects.id"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    content_type = Column(Enum(ContentType), nullable=False)
    platform = Column(Enum(PlatformType), nullable=False)
    word_count = Column(Integer)
    character_count = Column(Integer)
    reading_time = Column(Integer)  # in minutes
    status = Column(Enum(ContentStatus), default=ContentStatus.DRAFT)
    version = Column(Integer, default=1)
    ai_generated = Column(Boolean, default=True)
    plagiarism_score = Column(Float)
    grammar_score = Column(Float)
    tone_score = Column(Float)
    seo_score = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    published_at = Column(DateTime(timezone=True))
    
    # Relationships
    project = relationship("ContentProject", back_populates="content_pieces")
    versions = relationship("ContentVersion", back_populates="content_piece", cascade="all, delete-orphan")
    seo_analysis = relationship("SEOAnalysis", back_populates="content_piece", uselist=False)
    performance_metrics = relationship("ContentPerformance", back_populates="content_piece", cascade="all, delete-orphan")

class ContentVersion(Base):
    __tablename__ = "content_versions"
    
    id = Column(Integer, primary_key=True, index=True)
    content_piece_id = Column(Integer, ForeignKey("shakes_content_pieces.id"), nullable=False, index=True)
    version_number = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    changes_summary = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    content_piece = relationship("backend.agents.shakes.app.models.ContentPiece", back_populates="versions")
    creator = relationship("User", foreign_keys=[created_by])

class SEOAnalysis(Base):
    __tablename__ = "seo_analysis"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("content_projects.id"), index=True)
    content_piece_id = Column(Integer, ForeignKey("shakes_content_pieces.id"), index=True)
    keyword_density = Column(JSON)  # {keyword: density_percentage}
    readability_score = Column(Float)
    seo_score = Column(Float)
    meta_title = Column(String(60))
    meta_description = Column(String(160))
    h1_tags = Column(JSON)
    h2_tags = Column(JSON)
    h3_tags = Column(JSON)
    internal_links = Column(JSON)
    external_links = Column(JSON)
    image_alt_tags = Column(JSON)
    schema_markup = Column(JSON)
    mobile_friendly = Column(Boolean, default=True)
    page_speed_score = Column(Float)
    analyzed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    project = relationship("ContentProject", back_populates="seo_analysis")
    content_piece = relationship("backend.agents.shakes.app.models.ContentPiece", back_populates="seo_analysis")

class ContentPerformance(Base):
    __tablename__ = "content_performance"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("content_projects.id"), index=True)
    content_piece_id = Column(Integer, ForeignKey("shakes_content_pieces.id"), index=True)
    platform = Column(Enum(PlatformType), nullable=False)
    views = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    engagement_rate = Column(Float, default=0.0)
    reach = Column(Integer, default=0)
    impressions = Column(Integer, default=0)
    ctr = Column(Float, default=0.0)  # Click-through rate
    bounce_rate = Column(Float, default=0.0)
    time_on_page = Column(Float, default=0.0)  # in seconds
    conversion_rate = Column(Float, default=0.0)
    revenue_generated = Column(Float, default=0.0)
    measured_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    project = relationship("ContentProject", back_populates="performance_metrics")
    content_piece = relationship("backend.agents.shakes.app.models.ContentPiece", back_populates="performance_metrics")

class BrandVoice(Base):
    __tablename__ = "shakes_brand_voices"
    
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
    user = relationship("User", backref="brand_voices")

class ContentTemplate(Base):
    __tablename__ = "content_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    content_type = Column(Enum(ContentType), nullable=False)
    platform = Column(Enum(PlatformType), nullable=False)
    template_structure = Column(JSON, nullable=False)
    variables = Column(JSON, default=[])
    is_public = Column(Boolean, default=False)
    usage_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", backref="content_templates")

class ContentCalendar(Base):
    __tablename__ = "content_calendars"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    timezone = Column(String(50), default="UTC")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", backref="content_calendars")
    scheduled_content = relationship("ScheduledContent", back_populates="calendar", cascade="all, delete-orphan")

class ScheduledContent(Base):
    __tablename__ = "scheduled_content"
    
    id = Column(Integer, primary_key=True, index=True)
    calendar_id = Column(Integer, ForeignKey("content_calendars.id"), nullable=False, index=True)
    content_piece_id = Column(Integer, ForeignKey("shakes_content_pieces.id"), nullable=False, index=True)
    scheduled_time = Column(DateTime(timezone=True), nullable=False)
    platform = Column(Enum(PlatformType), nullable=False)
    status = Column(String(20), default="scheduled")  # scheduled, published, failed
    published_at = Column(DateTime(timezone=True))
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    calendar = relationship("ContentCalendar", back_populates="scheduled_content")
    content_piece = relationship("backend.agents.shakes.app.models.ContentPiece")

class ContentCollaboration(Base):
    __tablename__ = "content_collaboration"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("content_projects.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    role = Column(String(50), nullable=False)  # writer, editor, reviewer, approver
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    status = Column(String(20), default="assigned")  # assigned, in_progress, completed, overdue
    
    # Relationships
    project = relationship("ContentProject")
    user = relationship("User")

class ContentComment(Base):
    __tablename__ = "content_comments"
    
    id = Column(Integer, primary_key=True, index=True)
    content_piece_id = Column(Integer, ForeignKey("shakes_content_pieces.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    comment = Column(Text, nullable=False)
    parent_comment_id = Column(Integer, ForeignKey("content_comments.id"), index=True)
    resolved = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    content_piece = relationship("backend.agents.shakes.app.models.ContentPiece")
    user = relationship("User")
    parent_comment = relationship("ContentComment", remote_side=[id])
    replies = relationship("ContentComment", back_populates="parent_comment")

class ContentAnalytics(Base):
    __tablename__ = "content_analytics"
    
    id = Column(Integer, primary_key=True, index=True)
    content_piece_id = Column(Integer, ForeignKey("shakes_content_pieces.id"), nullable=False, index=True)
    date = Column(DateTime(timezone=True), nullable=False)
    views = Column(Integer, default=0)
    unique_views = Column(Integer, default=0)
    engagement_time = Column(Float, default=0.0)  # in seconds
    bounce_rate = Column(Float, default=0.0)
    conversion_rate = Column(Float, default=0.0)
    social_shares = Column(Integer, default=0)
    backlinks = Column(Integer, default=0)
    organic_traffic = Column(Integer, default=0)
    paid_traffic = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    content_piece = relationship("backend.agents.shakes.app.models.ContentPiece")

# Indexes for performance
Index("idx_content_projects_user_status", ContentProject.user_id, ContentProject.status)
Index("idx_content_pieces_project_status", ContentPiece.project_id, ContentPiece.status)
Index("idx_seo_analysis_project", SEOAnalysis.project_id)
Index("idx_content_performance_piece", ContentPerformance.content_piece_id)
Index("idx_scheduled_content_time", ScheduledContent.scheduled_time)
Index("idx_content_collaboration_user", ContentCollaboration.user_id)
Index("idx_content_comments_piece", ContentComment.content_piece_id)
Index("idx_content_analytics_date", ContentAnalytics.date)
