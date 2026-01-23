from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float, ForeignKey, JSON, Enum, Table, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum
from core.database.models import Base, UserProfile as CustomerProfile
 

class TicketPriority(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"

class TicketStatus(enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    WAITING_CUSTOMER = "waiting_customer"
    WAITING_AGENT = "waiting_agent"
    RESOLVED = "resolved"
    CLOSED = "closed"
    ESCALATED = "escalated"

class TicketCategory(enum.Enum):
    TECHNICAL = "technical"
    BILLING = "billing"
    GENERAL = "general"
    FEATURE_REQUEST = "feature_request"
    BUG_REPORT = "bug_report"
    ACCOUNT_ISSUE = "account_issue"
    ORDER_TRACKING = "order_tracking"
    PRODUCT_SUPPORT = "product_support"
    INTEGRATION = "integration"
    SECURITY = "security"

class SupportChannel(enum.Enum):
    CHAT = "chat"
    EMAIL = "email"
    PHONE = "phone"
    SOCIAL_MEDIA = "social_media"
    WEB_FORM = "web_form"
    IVR = "ivr"
    MOBILE_APP = "mobile_app"
    IN_STORE = "in_store"

class SentimentType(enum.Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    FRUSTRATED = "frustrated"
    SATISFIED = "satisfied"

class InteractionType(enum.Enum):
    CUSTOMER_MESSAGE = "customer_message"
    AGENT_RESPONSE = "agent_response"
    AUTOMATED_RESPONSE = "automated_response"
    SYSTEM_NOTIFICATION = "system_notification"
    ESCALATION = "escalation"
    RESOLUTION = "resolution"

class ClaraSupportTicket(Base):
    __tablename__ = "clara_support_tickets"
    
    id = Column(Integer, primary_key=True, index=True)
    ticket_number = Column(String(50), unique=True, index=True)
    customer_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    assigned_agent_id = Column(Integer, ForeignKey("users.id"), index=True)
    channel = Column(Enum(SupportChannel), nullable=False)
    priority = Column(Enum(TicketPriority), default=TicketPriority.MEDIUM)
    status = Column(Enum(TicketStatus), default=TicketStatus.OPEN)
    category = Column(Enum(TicketCategory), nullable=False)
    subject = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    sentiment_score = Column(Float, default=0.0)
    satisfaction_score = Column(Integer)  # 1-5 rating
    estimated_resolution_time = Column(Integer)  # in minutes
    actual_resolution_time = Column(Integer)  # in minutes
    first_response_time = Column(Integer)  # in minutes
    sla_breach = Column(Boolean, default=False)
    tags = Column(JSON, default=[])
    extra_metadata = Column('metadata', JSON, default={})
    crm_case_id = Column(String(100))  # External CRM case ID
    source_url = Column(String(500))
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    resolved_at = Column(DateTime(timezone=True))
    closed_at = Column(DateTime(timezone=True))
    
    # Relationships
    customer = relationship("User", foreign_keys=[customer_id], backref="support_tickets")
    assigned_agent = relationship("User", foreign_keys=[assigned_agent_id], backref="assigned_tickets")
    interactions = relationship("ClaraCustomerInteraction", back_populates="ticket", cascade="all, delete-orphan")
    attachments = relationship("ClaraTicketAttachment", back_populates="ticket", cascade="all, delete-orphan")
    escalations = relationship("ClaraTicketEscalation", back_populates="ticket", cascade="all, delete-orphan")
    # Use direct class reference via callable to avoid ambiguity with other CustomerFeedback models
    feedback = relationship(lambda: ClaraCustomerFeedback, back_populates="ticket", uselist=False)

class ClaraCustomerInteraction(Base):
    __tablename__ = "clara_customer_interactions"
    
    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("clara_support_tickets.id"), nullable=False)
    interaction_type = Column(Enum(InteractionType), nullable=False)
    channel = Column(Enum(SupportChannel), nullable=False)
    message = Column(Text, nullable=False)
    response = Column(Text)
    sentiment = Column(Enum(SentimentType), default=SentimentType.NEUTRAL)
    sentiment_score = Column(Float, default=0.0)
    satisfaction_score = Column(Integer)  # 1-5 rating
    is_automated = Column(Boolean, default=False)
    processing_time_ms = Column(Integer)
    agent_id = Column(Integer, ForeignKey("users.id"))
    extra_metadata = Column('metadata', JSON, default={})
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    ticket = relationship("ClaraSupportTicket", back_populates="interactions")
    agent = relationship("User", foreign_keys=[agent_id])

class ClaraTicketAttachment(Base):
    __tablename__ = "clara_ticket_attachments"
    
    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("clara_support_tickets.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer)  # in bytes
    mime_type = Column(String(100))
    description = Column(String(500))
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    ticket = relationship("ClaraSupportTicket", back_populates="attachments")
    user = relationship("User", foreign_keys=[uploaded_by])

class ClaraTicketEscalation(Base):
    __tablename__ = "clara_ticket_escalations"
    
    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("clara_support_tickets.id"), nullable=False)
    escalated_from_agent_id = Column(Integer, ForeignKey("users.id"))
    escalated_to_agent_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reason = Column(Text, nullable=False)
    priority_increase = Column(Boolean, default=False)
    sla_extension = Column(Integer)  # in minutes
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    ticket = relationship("ClaraSupportTicket", back_populates="escalations")
    escalated_from_agent = relationship("User", foreign_keys=[escalated_from_agent_id])
    escalated_to_agent = relationship("User", foreign_keys=[escalated_to_agent_id])

class ClaraCustomerFeedback(Base):
    __tablename__ = "clara_customer_feedback"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("clara_support_tickets.id"), nullable=False, unique=True)
    overall_satisfaction = Column(Integer, nullable=False)  # 1-5 rating
    response_time_rating = Column(Integer)  # 1-5 rating
    solution_quality_rating = Column(Integer)  # 1-5 rating
    agent_friendliness_rating = Column(Integer)  # 1-5 rating
    comments = Column(Text)
    would_recommend = Column(Boolean)
    follow_up_required = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    ticket = relationship("ClaraSupportTicket", back_populates="feedback")


# Chat session models
class ClaraChatSession(Base):
    __tablename__ = "clara_chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_id = Column(String(100), unique=True, nullable=False)
    start_time = Column(DateTime(timezone=True), server_default=func.now())
    end_time = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True)
    extra_metadata = Column('metadata', JSON, default={})

    # Relationships
    customer = relationship("User", foreign_keys=[customer_id])


class ClaraChatMessage(Base):
    __tablename__ = "clara_chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("clara_chat_sessions.id"), nullable=False)
    sender_type = Column(String(50))  # customer, agent, system
    sender_id = Column(Integer)  # user id for agents/customers
    content = Column(Text, nullable=False)
    content_type = Column(String(50), default="text")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("ClaraChatSession", back_populates="messages")

# Link back messages relationship
ClaraChatSession.messages = relationship("ClaraChatMessage", back_populates="session", cascade="all, delete-orphan")

class ClaraKnowledgeBase(Base):
    __tablename__ = "clara_knowledge_base"
    
    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(100), nullable=False, index=True)
    subcategory = Column(String(100), index=True)
    title = Column(String(200), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    tags = Column(JSON, default=[])
    keywords = Column(JSON, default=[])
    usage_count = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)
    helpful_count = Column(Integer, default=0)
    not_helpful_count = Column(Integer, default=0)
    last_updated = Column(DateTime(timezone=True), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))
    is_public = Column(Boolean, default=True)
    language = Column(String(10), default="en")
    
    # Vector embedding for semantic search
    embedding = Column(Text)  # JSON string of vector
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by])

class ClaraSupportAgent(Base):
    __tablename__ = "clara_support_agents"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    agent_code = Column(String(50), unique=True, nullable=False)
    skills = Column(JSON, default=[])
    specializations = Column(JSON, default=[])
    availability_status = Column(String(50), default="available")  # available, busy, offline, training
    max_concurrent_tickets = Column(Integer, default=5)
    current_ticket_count = Column(Integer, default=0)
    performance_score = Column(Float, default=0.0)
    # NOTE: This file previously contained a duplicated copy of the models (the whole
    # file was repeated). The duplicate half has been removed so each table is
    # defined only once. Keep model definitions below as the canonical Clara models.
# (Earlier duplicate definitions removed — canonical definitions exist later in the file.)
# Additional Enums for Advanced Features
class FAQSourceType(enum.Enum):
    CUSTOMER_INTERACTION = "customer_interaction"
    WEBSITE_CONTENT = "website_content"
    KNOWLEDGE_BASE = "knowledge_base"
    MANUAL_ENTRY = "manual_entry"
    AI_GENERATED = "ai_generated"

class OnboardingStepType(enum.Enum):
    WELCOME = "welcome"
    PROFILE_SETUP = "profile_setup"
    PREFERENCES = "preferences"
    INTEGRATION = "integration"
    TESTING = "testing"
    COMPLETION = "completion"

class OnboardingStatus(enum.Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"

class SetupWizardStepType(enum.Enum):
    WELCOME = "welcome"
    BRAND_SETUP = "brand_setup"
    INTEGRATION_SETUP = "integration_setup"
    TEAM_SETUP = "team_setup"
    WORKFLOW_SETUP = "workflow_setup"
    TESTING = "testing"
    COMPLETION = "completion"

class SetupWizardStatus(enum.Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    VALIDATION_FAILED = "validation_failed"

class SetupWizardValidationType(enum.Enum):
    EMAIL = "email"
    API_KEY = "api_key"
    WEBHOOK = "webhook"
    DATABASE = "database"
    INTEGRATION = "integration"

class InStoreInquiryType(enum.Enum):
    PRODUCT_INFO = "product_info"
    PRICING = "pricing"
    AVAILABILITY = "availability"
    TECHNICAL_SUPPORT = "technical_support"
    GENERAL = "general"

class InStoreInquiryStatus(enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    CLOSED = "closed"

class InStoreDeviceType(enum.Enum):
    KIOSK = "kiosk"
    TABLET = "tablet"
    MOBILE = "mobile"
    DESKTOP = "desktop"

class MobileAppUserRole(enum.Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    AGENT = "agent"
    VIEWER = "viewer"

class MobileAppSessionStatus(enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"
    SUSPENDED = "suspended"

class MobileAppOverrideType(enum.Enum):
    RESPONSE = "response"
    ESCALATION = "escalation"
    PRIORITY = "priority"
    ASSIGNMENT = "assignment"

class MobileAppNotificationType(enum.Enum):
    TICKET_ALERT = "ticket_alert"
    ESCALATION = "escalation"
    PERFORMANCE = "performance"
    SYSTEM = "system"

class VoiceSentimentType(enum.Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    FRUSTRATED = "frustrated"
    SATISFIED = "satisfied"

class VoiceSentimentSessionStatus(enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ANALYZED = "analyzed"
    COACHED = "coached"

class VoiceSentimentCoachingType(enum.Enum):
    TONE = "tone"
    PACE = "pace"
    EMPATHY = "empathy"
    CLARITY = "clarity"
    CONFIDENCE = "confidence"

class VoiceSentimentScenarioType(enum.Enum):
    CUSTOMER_COMPLAINT = "customer_complaint"
    TECHNICAL_SUPPORT = "technical_support"
    SALES_INQUIRY = "sales_inquiry"
    GENERAL_INQUIRY = "general_inquiry"

# Multi-ClaraBrand Support Models
class ClaraBrand(Base):
    __tablename__ = "clara_brands"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text)
    logo_url = Column(String(500))
    primary_color = Column(String(7))  # Hex color code
    secondary_color = Column(String(7))  # Hex color code
    tone_of_voice = Column(String(50), default="professional")
    industry = Column(String(100))
    target_audience = Column(String(200))
    contact_info = Column(JSON, default={})
    social_media_handles = Column(JSON, default={})
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class ClaraBrandConfiguration(Base):
    __tablename__ = "clara_brand_configurations"
    
    id = Column(Integer, primary_key=True, index=True)
    brand_id = Column(Integer, ForeignKey("clara_brands.id"), nullable=False)
    config_type = Column(String(50), nullable=False)  # response_templates, workflows, integrations
    config_key = Column(String(100), nullable=False)
    config_value = Column(JSON, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    brand = relationship("ClaraBrand")

class ClaraBrandTemplate(Base):
    __tablename__ = "clara_brand_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    brand_id = Column(Integer, ForeignKey("clara_brands.id"), nullable=False)
    template_type = Column(String(50), nullable=False)  # email, chat, sms, notification
    template_name = Column(String(100), nullable=False)
    subject = Column(String(200))
    content = Column(Text, nullable=False)
    variables = Column(JSON, default=[])
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    brand = relationship("ClaraBrand")

# Customer Journey Tracking Models
class ClaraCustomerJourney(Base):
    __tablename__ = "clara_customer_journeys"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    journey_type = Column(String(100), nullable=False)  # support, onboarding, purchase
    description = Column(Text)
    current_stage = Column(String(50), default="started")
    status = Column(String(50), default="active")  # active, completed, abandoned
    extra_metadata = Column('metadata', JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    customer = relationship("User", foreign_keys=[customer_id])
    events = relationship("ClaraJourneyEvent", back_populates="journey", cascade="all, delete-orphan")
    stages = relationship("ClaraJourneyStage", back_populates="journey", cascade="all, delete-orphan")

class ClaraJourneyEvent(Base):
    __tablename__ = "clara_journey_events"
    
    id = Column(Integer, primary_key=True, index=True)
    journey_id = Column(Integer, ForeignKey("clara_customer_journeys.id"), nullable=False)
    event_type = Column(String(100), nullable=False)  # ticket_created, response_sent, resolved
    event_data = Column(JSON, nullable=False)
    channel = Column(Enum(SupportChannel))
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    journey = relationship("ClaraCustomerJourney", back_populates="events")

class ClaraJourneyStage(Base):
    __tablename__ = "clara_journey_stages"
    
    id = Column(Integer, primary_key=True, index=True)
    journey_id = Column(Integer, ForeignKey("clara_customer_journeys.id"), nullable=False)
    stage_name = Column(String(100), nullable=False)
    stage_order = Column(Integer, nullable=False)
    status = Column(String(50), default="pending")  # pending, active, completed, skipped
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    extra_metadata = Column('metadata', JSON, default={})
    
    # Relationships
    journey = relationship("ClaraCustomerJourney", back_populates="stages")

# Proactive Support Notifications Models
class ClaraProactiveNotification(Base):
    __tablename__ = "clara_proactive_notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    notification_type = Column(String(50), nullable=False)  # issue_detected, update_available, reminder
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    channel = Column(Enum(SupportChannel), nullable=False)
    priority = Column(Enum(TicketPriority), default=TicketPriority.MEDIUM)
    status = Column(String(50), default="pending")  # pending, sent, delivered, read, failed
    scheduled_at = Column(DateTime(timezone=True))
    sent_at = Column(DateTime(timezone=True))
    read_at = Column(DateTime(timezone=True))
    extra_metadata = Column('metadata', JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    customer = relationship("User", foreign_keys=[customer_id])

class ClaraNotificationRule(Base):
    __tablename__ = "clara_notification_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    trigger_conditions = Column(JSON, nullable=False)  # Conditions that trigger the notification
    notification_template_id = Column(Integer, ForeignKey("clara_notification_templates.id"))
    channels = Column(JSON, default=[])  # List of channels to send to
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    template = relationship("ClaraNotificationTemplate")

class ClaraNotificationTemplate(Base):
    __tablename__ = "clara_notification_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    template_type = Column(String(50), nullable=False)  # email, sms, push, in_app
    subject = Column(String(200))
    content = Column(Text, nullable=False)
    variables = Column(JSON, default=[])
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

# Support workflow model for Clara (custom workflows engine)
class ClaraSupportWorkflow(Base):
    __tablename__ = "clara_support_workflows"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    category = Column(Enum(TicketCategory), nullable=False)
    priority = Column(Enum(TicketPriority), nullable=False)
    steps = Column(JSON, default=[])
    auto_assign = Column(Boolean, default=False)
    auto_assign_agent_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    sla_target = Column(Integer)  # in minutes
    escalation_rules = Column(JSON, default={})
    conditions = Column(JSON, default={})
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    agent = relationship("User", foreign_keys=[auto_assign_agent_id])

# Agent Training Tools Models
class ClaraAgentTraining(Base):
    __tablename__ = "clara_agent_training"
    
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    training_type = Column(String(50), nullable=False)  # onboarding, skill_development, certification
    status = Column(String(50), default="not_started")  # not_started, in_progress, completed, failed
    progress_percentage = Column(Float, default=0.0)
    start_date = Column(DateTime(timezone=True))
    completion_date = Column(DateTime(timezone=True))
    score = Column(Float)
    feedback = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    agent = relationship("User", foreign_keys=[agent_id])

class ClaraTrainingModule(Base):
    __tablename__ = "clara_training_modules"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    content = Column(Text, nullable=False)
    difficulty_level = Column(String(20), default="beginner")  # beginner, intermediate, advanced
    estimated_duration = Column(Integer)  # in minutes
    skills_covered = Column(JSON, default=[])
    prerequisites = Column(JSON, default=[])
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class ClaraTrainingSession(Base):
    __tablename__ = "clara_training_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    module_id = Column(Integer, ForeignKey("clara_training_modules.id"), nullable=False)
    status = Column(String(50), default="not_started")  # not_started, in_progress, completed, paused
    start_time = Column(DateTime(timezone=True))
    end_time = Column(DateTime(timezone=True))
    duration = Column(Integer)  # in minutes
    progress = Column(Float, default=0.0)
    score = Column(Float)
    feedback = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    agent = relationship("User", foreign_keys=[agent_id])
    module = relationship("ClaraTrainingModule")

class ClaraAgentPerformance(Base):
    __tablename__ = "clara_agent_performance"
    
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    tickets_resolved = Column(Integer, default=0)
    average_resolution_time = Column(Float)  # in minutes
    customer_satisfaction = Column(Float)  # 1-5 rating
    first_contact_resolution_rate = Column(Float)  # percentage
    training_completion_rate = Column(Float)  # percentage
    performance_score = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    agent = relationship("User", foreign_keys=[agent_id])

class ClaraTrainingAssessment(Base):
    __tablename__ = "clara_training_assessments"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("clara_training_sessions.id"), nullable=False)
    assessment_type = Column(String(50), nullable=False)  # quiz, practical, simulation
    questions = Column(JSON, nullable=False)
    answers = Column(JSON, default={})
    score = Column(Float)
    max_score = Column(Float)
    passed = Column(Boolean)
    feedback = Column(Text)
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    session = relationship("ClaraTrainingSession")

# AI-Driven ClaraFAQ Builder Models
class ClaraFAQCategory(Base):
    __tablename__ = "clara_faq_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    parent_category_id = Column(Integer, ForeignKey("clara_faq_categories.id"))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    parent = relationship("ClaraFAQCategory", remote_side=[id])
    entries = relationship("ClaraFAQEntry", back_populates="category")

class ClaraFAQEntry(Base):
    __tablename__ = "clara_faq_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("clara_faq_categories.id"), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    keywords = Column(JSON, default=[])
    tags = Column(JSON, default=[])
    usage_count = Column(Integer, default=0)
    helpful_count = Column(Integer, default=0)
    not_helpful_count = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    category = relationship("ClaraFAQCategory", back_populates="entries")

class ClaraFAQSource(Base):
    __tablename__ = "clara_faq_sources"
    
    id = Column(Integer, primary_key=True, index=True)
    source_type = Column(Enum(FAQSourceType), nullable=False)
    source_name = Column(String(100), nullable=False)
    source_url = Column(String(500))
    content = Column(Text)
    processed = Column(Boolean, default=False)
    faq_entries_generated = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class ClaraFAQAnalytics(Base):
    __tablename__ = "clara_faq_analytics"
    
    id = Column(Integer, primary_key=True, index=True)
    entry_id = Column(Integer, ForeignKey("clara_faq_entries.id"), nullable=False)
    date = Column(DateTime, nullable=False)
    views = Column(Integer, default=0)
    helpful_votes = Column(Integer, default=0)
    not_helpful_votes = Column(Integer, default=0)
    search_rankings = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    entry = relationship("ClaraFAQEntry")


class ClaraSupportAnalytics(Base):
    __tablename__ = "clara_support_analytics"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(100), nullable=False)
    event_data = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Lightweight relation fields if needed by queries
    ticket_id = Column(Integer, ForeignKey("clara_support_tickets.id"), nullable=True)
    session_id = Column(Integer, ForeignKey("clara_chat_sessions.id"), nullable=True)

    ticket = relationship("ClaraSupportTicket", foreign_keys=[ticket_id])
    session = relationship("ClaraChatSession", foreign_keys=[session_id])

# Predictive Issue Detection Models
class ClaraPredictionModel(Base):
    __tablename__ = "clara_prediction_models"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    model_type = Column(String(50), nullable=False)  # ticket_volume, issue_detection, churn_prediction
    algorithm = Column(String(50), nullable=False)
    parameters = Column(JSON, default={})
    accuracy = Column(Float)
    is_active = Column(Boolean, default=True)
    last_trained = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class ClaraAlertRule(Base):
    __tablename__ = "clara_alert_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    conditions = Column(JSON, nullable=False)
    severity = Column(Enum(TicketPriority), default=TicketPriority.MEDIUM)
    notification_channels = Column(JSON, default=[])
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class ClaraSystemMetric(Base):
    __tablename__ = "clara_system_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Float, nullable=False)
    metric_unit = Column(String(20))
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    extra_metadata = Column('metadata', JSON, default={})

class ClaraIssuePrediction(Base):
    __tablename__ = "clara_issue_predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    prediction_type = Column(String(50), nullable=False)  # ticket_spike, system_issue, customer_churn
    confidence_score = Column(Float, nullable=False)
    predicted_value = Column(Float)
    predicted_timestamp = Column(DateTime(timezone=True))
    actual_value = Column(Float)
    actual_timestamp = Column(DateTime(timezone=True))
    accuracy = Column(Float)
    extra_metadata = Column('metadata', JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ClaraIssuePattern(Base):
    __tablename__ = "clara_issue_patterns"

    id = Column(Integer, primary_key=True, index=True)
    pattern_name = Column(String(200), nullable=False)
    pattern_type = Column(String(100), nullable=False)  # spike, trend, recurring_error
    description = Column(Text)
    indicators = Column(JSON, default=[])  # list of indicator strings or metric names
    confidence_score = Column(Float, default=0.0)
    frequency = Column(Integer, default=0)
    impact_level = Column(String(50), default="medium")  # low, medium, high, critical
    mitigation_strategies = Column(JSON, default=[])  # list of suggested mitigations
    extra_metadata = Column('metadata', JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

# Multi-Ticket Resolution Models
class ClaraTicketGroup(Base):
    __tablename__ = "clara_ticket_groups"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    group_type = Column(String(50), nullable=False)  # similar_issues, same_customer, related_products
    criteria = Column(JSON, nullable=False)
    ticket_ids = Column(JSON, default=[])
    status = Column(String(50), default="active")  # active, resolved, closed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class ClaraBulkAction(Base):
    __tablename__ = "clara_bulk_actions"
    
    id = Column(Integer, primary_key=True, index=True)
    action_type = Column(String(50), nullable=False)  # status_update, assign, escalate, close
    ticket_ids = Column(JSON, nullable=False)
    parameters = Column(JSON, default={})
    status = Column(String(50), default="pending")  # pending, in_progress, completed, failed
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    completed_at = Column(DateTime(timezone=True))
    results = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by])

class ClaraResolutionTemplate(Base):
    __tablename__ = "clara_resolution_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    category = Column(Enum(TicketCategory), nullable=False)
    template_content = Column(Text, nullable=False)
    variables = Column(JSON, default=[])
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class ClaraTicketCluster(Base):
    __tablename__ = "clara_ticket_clusters"
    
    id = Column(Integer, primary_key=True, index=True)
    cluster_name = Column(String(100), nullable=False)
    cluster_type = Column(String(50), nullable=False)  # topic, sentiment, urgency
    ticket_ids = Column(JSON, default=[])
    centroid_data = Column(JSON, default={})
    similarity_threshold = Column(Float, default=0.8)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class ClaraResolutionBatch(Base):
    __tablename__ = "clara_resolution_batches"
    
    id = Column(Integer, primary_key=True, index=True)
    batch_name = Column(String(100), nullable=False)
    ticket_ids = Column(JSON, nullable=False)
    template_id = Column(Integer, ForeignKey("clara_resolution_templates.id"))
    status = Column(String(50), default="pending")  # pending, processing, completed, failed
    processed_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    completed_at = Column(DateTime(timezone=True))
    results = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    template = relationship("ClaraResolutionTemplate")
    creator = relationship("User", foreign_keys=[created_by])

# Onboarding Assistance Models
class ClaraOnboardingStep(Base):
    __tablename__ = "clara_onboarding_steps"
    
    id = Column(Integer, primary_key=True, index=True)
    step_type = Column(Enum(OnboardingStepType), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    content = Column(Text)
    order_index = Column(Integer, nullable=False)
    is_required = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class ClaraOnboardingSession(Base):
    __tablename__ = "clara_onboarding_sessions"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    current_step_id = Column(Integer, ForeignKey("clara_onboarding_steps.id"))
    status = Column(Enum(OnboardingStatus), default=OnboardingStatus.NOT_STARTED)
    progress_percentage = Column(Float, default=0.0)
    start_time = Column(DateTime(timezone=True), server_default=func.now())
    completion_time = Column(DateTime(timezone=True))
    extra_metadata = Column('metadata', JSON, default={})
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    current_step = relationship("ClaraOnboardingStep")

class ClaraOnboardingTutorial(Base):
    __tablename__ = "clara_onboarding_tutorials"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    content = Column(Text, nullable=False)
    video_url = Column(String(500))
    step_id = Column(Integer, ForeignKey("clara_onboarding_steps.id"))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    step = relationship("ClaraOnboardingStep")

class ClaraOnboardingProgress(Base):
    __tablename__ = "clara_onboarding_progress"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("clara_onboarding_sessions.id"), nullable=False)
    step_id = Column(Integer, ForeignKey("clara_onboarding_steps.id"), nullable=False)
    status = Column(Enum(OnboardingStatus), default=OnboardingStatus.NOT_STARTED)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    time_spent = Column(Integer)  # in seconds
    extra_metadata = Column('metadata', JSON, default={})
    
    # Relationships
    session = relationship("ClaraOnboardingSession", foreign_keys=[session_id])
    step = relationship("ClaraOnboardingStep", foreign_keys=[step_id])

# Setup Wizard Models
class ClaraSetupWizardStep(Base):
    __tablename__ = "clara_setup_wizard_steps"
    
    id = Column(Integer, primary_key=True, index=True)
    step_type = Column(Enum(SetupWizardStepType), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    content = Column(Text)
    order_index = Column(Integer, nullable=False)
    validation_rules = Column(JSON, default=[])
    is_required = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class ClaraSetupWizardSession(Base):
    __tablename__ = "clara_setup_wizard_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    current_step_id = Column(Integer, ForeignKey("clara_setup_wizard_steps.id"))
    status = Column(Enum(SetupWizardStatus), default=SetupWizardStatus.NOT_STARTED)
    progress_percentage = Column(Float, default=0.0)
    configuration_data = Column(JSON, default={})
    start_time = Column(DateTime(timezone=True), server_default=func.now())
    completion_time = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    current_step = relationship("ClaraSetupWizardStep")

class ClaraSetupWizardConfig(Base):
    __tablename__ = "clara_setup_wizard_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("clara_setup_wizard_sessions.id"), nullable=False)
    config_key = Column(String(100), nullable=False)
    config_value = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    session = relationship("ClaraSetupWizardSession")

class ClaraSetupWizardValidation(Base):
    __tablename__ = "clara_setup_wizard_validations"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("clara_setup_wizard_sessions.id"), nullable=False)
    validation_type = Column(Enum(SetupWizardValidationType), nullable=False)
    validation_data = Column(JSON, nullable=False)
    status = Column(String(50), default="pending")  # pending, success, failed
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    session = relationship("ClaraSetupWizardSession")

# In-Store Inquiry Integration Models
class ClaraInStoreKiosk(Base):
    __tablename__ = "clara_in_store_kiosks"
    
    id = Column(Integer, primary_key=True, index=True)
    kiosk_id = Column(String(100), unique=True, nullable=False)
    location_name = Column(String(200), nullable=False)
    device_type = Column(Enum(InStoreDeviceType), nullable=False)
    location_address = Column(Text)
    coordinates = Column(JSON)  # latitude, longitude
    is_active = Column(Boolean, default=True)
    last_heartbeat = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class ClaraInStoreInquiry(Base):
    __tablename__ = "clara_in_store_inquiries"
    
    id = Column(Integer, primary_key=True, index=True)
    kiosk_id = Column(Integer, ForeignKey("clara_in_store_kiosks.id"), nullable=False)
    inquiry_type = Column(Enum(InStoreInquiryType), nullable=False)
    customer_question = Column(Text, nullable=False)
    ai_response = Column(Text)
    human_response = Column(Text)
    status = Column(Enum(InStoreInquiryStatus), default=InStoreInquiryStatus.PENDING)
    customer_satisfaction = Column(Integer)  # 1-5 rating
    resolution_time = Column(Integer)  # in seconds
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True))
    
    # Relationships
    kiosk = relationship("InStoreKiosk")

class ClaraInStoreQRCode(Base):
    __tablename__ = "clara_in_store_qr_codes"
    
    id = Column(Integer, primary_key=True, index=True)
    qr_code_id = Column(String(100), unique=True, nullable=False)
    location_id = Column(Integer, ForeignKey("clara_in_store_locations.id"))
    product_id = Column(String(100))
    qr_code_url = Column(String(500), nullable=False)
    scan_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    location = relationship("ClaraInStoreLocation")

class ClaraInStoreLocation(Base):
    __tablename__ = "clara_in_store_locations"
    
    id = Column(Integer, primary_key=True, index=True)
    location_name = Column(String(200), nullable=False)
    location_type = Column(String(50))  # store, mall, office, event
    address = Column(Text)
    coordinates = Column(JSON)  # latitude, longitude
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class ClaraInStoreDevice(Base):
    __tablename__ = "clara_in_store_devices"
    
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String(100), unique=True, nullable=False)
    device_type = Column(Enum(InStoreDeviceType), nullable=False)
    location_id = Column(Integer, ForeignKey("clara_in_store_locations.id"))
    device_name = Column(String(200))
    device_model = Column(String(100))
    is_active = Column(Boolean, default=True)
    last_online = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    location = relationship("ClaraInStoreLocation")

# Mobile App for Monitoring Models
class ClaraMobileAppUser(Base):
    __tablename__ = "clara_mobile_app_users"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    device_id = Column(String(100), unique=True, nullable=False)
    device_type = Column(String(50))  # ios, android, web
    app_version = Column(String(20))
    role = Column(Enum(MobileAppUserRole), default=MobileAppUserRole.AGENT)
    permissions = Column(JSON, default=[])
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])

class ClaraMobileAppSession(Base):
    __tablename__ = "mobile_app_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("clara_mobile_app_users.id"), nullable=False)
    session_token = Column(String(255), unique=True, nullable=False)
    status = Column(Enum(MobileAppSessionStatus), default=MobileAppSessionStatus.ACTIVE)
    start_time = Column(DateTime(timezone=True), server_default=func.now())
    end_time = Column(DateTime(timezone=True))
    last_activity = Column(DateTime(timezone=True))
    extra_metadata = Column('metadata', JSON, default={})
    
    # Relationships
    user = relationship("ClaraMobileAppUser")

class ClaraMobileAppOverride(Base):
    __tablename__ = "mobile_app_overrides"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("clara_mobile_app_users.id"), nullable=False)
    override_type = Column(Enum(MobileAppOverrideType), nullable=False)
    target_id = Column(Integer)  # ticket_id, response_id, etc.
    original_value = Column(JSON)
    new_value = Column(JSON, nullable=False)
    reason = Column(Text)
    approved_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("ClaraMobileAppUser")
    approver = relationship("User", foreign_keys=[approved_by])

class ClaraMobileAppNotification(Base):
    __tablename__ = "mobile_app_notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("clara_mobile_app_users.id"), nullable=False)
    notification_type = Column(Enum(MobileAppNotificationType), nullable=False)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    data = Column(JSON, default={})
    status = Column(String(50), default="pending")  # pending, sent, delivered, read
    sent_at = Column(DateTime(timezone=True))
    read_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("ClaraMobileAppUser")

class ClaraMobileAppDevice(Base):
    __tablename__ = "mobile_app_devices"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("clara_mobile_app_users.id"), nullable=False)
    device_token = Column(String(255), unique=True, nullable=False)
    device_type = Column(String(50))  # ios, android, web
    device_model = Column(String(100))
    os_version = Column(String(20))
    app_version = Column(String(20))
    is_active = Column(Boolean, default=True)
    last_used = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("ClaraMobileAppUser")

class ClaraMobileAppPermission(Base):
    __tablename__ = "mobile_app_permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("clara_mobile_app_users.id"), nullable=False)
    permission_name = Column(String(100), nullable=False)
    permission_value = Column(JSON, nullable=False)
    granted_by = Column(Integer, ForeignKey("users.id"))
    granted_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("ClaraMobileAppUser")
    granter = relationship("User", foreign_keys=[granted_by])

# Voice Sentiment Coaching Models
class ClaraVoiceSentimentSession(Base):
    __tablename__ = "voice_sentiment_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_type = Column(String(50), nullable=False)  # training, practice, assessment
    audio_file_path = Column(String(500))
    transcript = Column(Text)
    status = Column(Enum(VoiceSentimentSessionStatus), default=VoiceSentimentSessionStatus.ACTIVE)
    start_time = Column(DateTime(timezone=True), server_default=func.now())
    end_time = Column(DateTime(timezone=True))
    duration = Column(Integer)  # in seconds
    extra_metadata = Column('metadata', JSON, default={})
    
    # Relationships
    agent = relationship("User", foreign_keys=[agent_id])

class ClaraVoiceSentimentAnalysis(Base):
    __tablename__ = "voice_sentiment_analysis"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("voice_sentiment_sessions.id"), nullable=False)
    sentiment_type = Column(Enum(VoiceSentimentType), nullable=False)
    confidence_score = Column(Float, nullable=False)
    analysis_data = Column(JSON, nullable=False)  # pitch, pace, volume, clarity, etc.
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    session = relationship("ClaraVoiceSentimentSession")

class ClaraVoiceSentimentFeedback(Base):
    __tablename__ = "voice_sentiment_feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("voice_sentiment_sessions.id"), nullable=False)
    feedback_type = Column(String(50), nullable=False)  # positive, negative, neutral
    feedback_text = Column(Text, nullable=False)
    rating = Column(Integer)  # 1-5 rating
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    session = relationship("ClaraVoiceSentimentSession")
    creator = relationship("User", foreign_keys=[created_by])

class ClaraVoiceSentimentCoaching(Base):
    __tablename__ = "voice_sentiment_coaching"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("voice_sentiment_sessions.id"), nullable=False)
    coaching_type = Column(Enum(VoiceSentimentCoachingType), nullable=False)
    recommendation = Column(Text, nullable=False)
    improvement_areas = Column(JSON, default=[])
    practice_exercises = Column(JSON, default=[])
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    session = relationship("ClaraVoiceSentimentSession")

class ClaraVoiceSentimentScenario(Base):
    __tablename__ = "voice_sentiment_scenarios"
    
    id = Column(Integer, primary_key=True, index=True)
    scenario_type = Column(Enum(VoiceSentimentScenarioType), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    scenario_content = Column(Text, nullable=False)
    expected_sentiment = Column(Enum(VoiceSentimentType))
    difficulty_level = Column(String(20), default="beginner")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class ClaraVoiceSentimentPractice(Base):
    __tablename__ = "voice_sentiment_practice"
    
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    scenario_id = Column(Integer, ForeignKey("voice_sentiment_scenarios.id"), nullable=False)
    practice_session_id = Column(Integer, ForeignKey("voice_sentiment_sessions.id"))
    performance_score = Column(Float)
    feedback = Column(Text)
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    agent = relationship("User", foreign_keys=[agent_id])
    scenario = relationship("ClaraVoiceSentimentScenario")
    session = relationship("ClaraVoiceSentimentSession")

# Additional indexes for new models
Index("idx_brands_name", ClaraBrand.name)
Index("idx_brand_configs_brand_type", ClaraBrandConfiguration.brand_id, ClaraBrandConfiguration.config_type)
Index("idx_customer_journeys_customer_type", ClaraCustomerJourney.customer_id, ClaraCustomerJourney.journey_type)
Index("idx_journey_events_journey_timestamp", ClaraJourneyEvent.journey_id, ClaraJourneyEvent.timestamp)
Index("idx_proactive_notifications_customer_status", ClaraProactiveNotification.customer_id, ClaraProactiveNotification.status)
Index("idx_agent_training_agent_status", ClaraAgentTraining.agent_id, ClaraAgentTraining.status)
Index("idx_training_modules_difficulty", ClaraTrainingModule.difficulty_level, ClaraTrainingModule.is_active)
Index("idx_faq_categories_name", ClaraFAQCategory.name)
Index("idx_faq_entries_category", ClaraFAQEntry.category_id, ClaraFAQEntry.is_active)
Index("idx_prediction_models_type", ClaraPredictionModel.model_type, ClaraPredictionModel.is_active)
Index("idx_ticket_groups_type_status", ClaraTicketGroup.group_type, ClaraTicketGroup.status)
Index("idx_onboarding_sessions_user_status", ClaraOnboardingSession.user_id, ClaraOnboardingSession.status)
Index("idx_setup_wizard_sessions_user_status", ClaraSetupWizardSession.user_id, ClaraSetupWizardSession.status)
Index("idx_in_store_inquiries_kiosk_status", ClaraInStoreInquiry.kiosk_id, ClaraInStoreInquiry.status)
Index("idx_mobile_app_users_device", ClaraMobileAppUser.device_id, ClaraMobileAppUser.is_active)
Index("idx_voice_sentiment_sessions_agent", ClaraVoiceSentimentSession.agent_id, ClaraVoiceSentimentSession.status)
