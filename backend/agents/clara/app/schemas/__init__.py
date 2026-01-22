"""
Pydantic schemas for Clara API request/response validation
"""

from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum

# Core Enums
class TicketPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"

class TicketStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    WAITING_CUSTOMER = "waiting_customer"
    WAITING_AGENT = "waiting_agent"
    RESOLVED = "resolved"
    CLOSED = "closed"
    ESCALATED = "escalated"

class TicketCategory(str, Enum):
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

class SupportChannel(str, Enum):
    CHAT = "chat"
    EMAIL = "email"
    PHONE = "phone"
    SOCIAL_MEDIA = "social_media"
    WEB_FORM = "web_form"
    IVR = "ivr"
    MOBILE_APP = "mobile_app"
    IN_STORE = "in_store"

class SentimentType(str, Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    FRUSTRATED = "frustrated"
    SATISFIED = "satisfied"

# Core Schemas
class SupportTicketBase(BaseModel):
    customer_id: int
    channel: SupportChannel
    category: TicketCategory
    subject: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    priority: TicketPriority = TicketPriority.MEDIUM
    tags: List[str] = []
    metadata: Dict[str, Any] = {}

class SupportTicketCreate(SupportTicketBase):
    pass

class SupportTicketUpdate(BaseModel):
    subject: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=1)
    priority: Optional[TicketPriority] = None
    status: Optional[TicketStatus] = None
    assigned_agent_id: Optional[int] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

class SupportTicketResponse(SupportTicketBase):
    id: int
    ticket_number: str
    status: TicketStatus
    assigned_agent_id: Optional[int] = None
    sentiment_score: float = 0.0
    satisfaction_score: Optional[int] = None
    estimated_resolution_time: Optional[int] = None
    actual_resolution_time: Optional[int] = None
    first_response_time: Optional[int] = None
    sla_breach: bool = False
    crm_case_id: Optional[str] = None
    source_url: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Customer Interaction Schemas
class CustomerInteractionBase(BaseModel):
    ticket_id: int
    interaction_type: str
    channel: SupportChannel
    message: str = Field(..., min_length=1)
    response: Optional[str] = None
    sentiment: SentimentType = SentimentType.NEUTRAL
    sentiment_score: float = 0.0
    satisfaction_score: Optional[int] = Field(None, ge=1, le=5)
    is_automated: bool = False
    agent_id: Optional[int] = None
    metadata: Dict[str, Any] = {}

class CustomerInteractionCreate(CustomerInteractionBase):
    pass

class CustomerInteractionResponse(CustomerInteractionBase):
    id: int
    processing_time_ms: Optional[int] = None
    timestamp: datetime

    class Config:
        from_attributes = True

# Knowledge Base Schemas
class KnowledgeBaseBase(BaseModel):
    category: str = Field(..., min_length=1, max_length=100)
    subcategory: Optional[str] = Field(None, max_length=100)
    title: str = Field(..., min_length=1, max_length=200)
    question: str = Field(..., min_length=1)
    answer: str = Field(..., min_length=1)
    tags: List[str] = []
    keywords: List[str] = []
    is_public: bool = True
    language: str = "en"

class KnowledgeBaseCreate(KnowledgeBaseBase):
    pass

class KnowledgeBaseUpdate(BaseModel):
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    subcategory: Optional[str] = Field(None, max_length=100)
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    question: Optional[str] = Field(None, min_length=1)
    answer: Optional[str] = Field(None, min_length=1)
    tags: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    is_public: Optional[bool] = None
    language: Optional[str] = None

class KnowledgeBaseResponse(KnowledgeBaseBase):
    id: int
    usage_count: int = 0
    success_rate: float = 0.0
    helpful_count: int = 0
    not_helpful_count: int = 0
    created_by: Optional[int] = None
    created_at: datetime
    last_updated: Optional[datetime] = None

    class Config:
        from_attributes = True

# Support Agent Schemas
class SupportAgentBase(BaseModel):
    user_id: int
    agent_code: str = Field(..., min_length=1, max_length=50)
    skills: List[str] = []
    specializations: List[str] = []
    availability_status: str = "available"
    max_concurrent_tickets: int = 5
    training_level: str = "beginner"

class SupportAgentCreate(SupportAgentBase):
    pass

class SupportAgentUpdate(BaseModel):
    skills: Optional[List[str]] = None
    specializations: Optional[List[str]] = None
    availability_status: Optional[str] = None
    max_concurrent_tickets: Optional[int] = None
    training_level: Optional[str] = None

class SupportAgentResponse(SupportAgentBase):
    id: int
    current_ticket_count: int = 0
    performance_score: float = 0.0
    response_time_avg: Optional[float] = None
    resolution_rate: Optional[float] = None
    customer_satisfaction_avg: Optional[float] = None
    total_tickets_resolved: int = 0
    total_tickets_escalated: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Support Workflow Schemas
class SupportWorkflowBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    category: TicketCategory
    priority: TicketPriority
    steps: List[Dict[str, Any]] = Field(..., min_items=1)
    auto_assign: bool = False
    auto_assign_agent_id: Optional[int] = None
    sla_target: Optional[int] = None
    escalation_rules: Dict[str, Any] = {}
    is_active: bool = True

class SupportWorkflowCreate(SupportWorkflowBase):
    pass

class SupportWorkflowUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    category: Optional[TicketCategory] = None
    priority: Optional[TicketPriority] = None
    steps: Optional[List[Dict[str, Any]]] = None
    auto_assign: Optional[bool] = None
    auto_assign_agent_id: Optional[int] = None
    sla_target: Optional[int] = None
    escalation_rules: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class SupportWorkflowResponse(SupportWorkflowBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Customer Profile Schemas
class CustomerProfileBase(BaseModel):
    user_id: int
    support_tier: str = "standard"
    preferred_channel: SupportChannel = SupportChannel.CHAT
    language_preference: str = "en"
    timezone: str = "UTC"
    support_history: Dict[str, Any] = {}
    trust_score: float = 0.0
    loyalty_level: str = "new"

class CustomerProfileCreate(CustomerProfileBase):
    pass

class CustomerProfileUpdate(BaseModel):
    support_tier: Optional[str] = None
    preferred_channel: Optional[SupportChannel] = None
    language_preference: Optional[str] = None
    timezone: Optional[str] = None
    support_history: Optional[Dict[str, Any]] = None
    trust_score: Optional[float] = None
    loyalty_level: Optional[str] = None

class CustomerProfileResponse(CustomerProfileBase):
    id: int
    last_support_contact: Optional[datetime] = None
    total_support_tickets: int = 0
    resolved_tickets: int = 0
    average_satisfaction: float = 0.0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Support Analytics Schemas
class SupportAnalyticsBase(BaseModel):
    date: datetime
    total_tickets: int = 0
    open_tickets: int = 0
    resolved_tickets: int = 0
    escalated_tickets: int = 0
    average_response_time: Optional[float] = None
    average_resolution_time: Optional[float] = None
    customer_satisfaction_avg: Optional[float] = None
    first_contact_resolution_rate: Optional[float] = None
    sla_compliance_rate: Optional[float] = None
    channel_distribution: Dict[str, Any] = {}
    category_distribution: Dict[str, Any] = {}
    agent_performance: Dict[str, Any] = {}

class SupportAnalyticsCreate(SupportAnalyticsBase):
    pass

class SupportAnalyticsResponse(SupportAnalyticsBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Chat Session Schemas
class ChatSessionBase(BaseModel):
    customer_id: int
    agent_id: Optional[int] = None
    ticket_id: Optional[int] = None
    channel: SupportChannel = SupportChannel.CHAT
    status: str = "active"
    metadata: Dict[str, Any] = {}

class ChatSessionCreate(ChatSessionBase):
    pass

class ChatSessionUpdate(BaseModel):
    agent_id: Optional[int] = None
    ticket_id: Optional[int] = None
    status: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class ChatSessionResponse(ChatSessionBase):
    id: int
    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[int] = None
    messages_count: int = 0
    customer_satisfaction: Optional[int] = None
    auto_responses_count: int = 0
    human_handoff_count: int = 0

    class Config:
        from_attributes = True

# Chat Message Schemas
class ChatMessageBase(BaseModel):
    session_id: int
    sender_type: str = Field(..., min_length=1, max_length=20)
    sender_id: Optional[int] = None
    message: str = Field(..., min_length=1)
    message_type: str = "text"
    metadata: Dict[str, Any] = {}

class ChatMessageCreate(ChatMessageBase):
    pass

class ChatMessageResponse(ChatMessageBase):
    id: int
    timestamp: datetime
    is_read: bool = False
    read_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Multi-ClaraBrand Support Schemas
class BrandBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    tone_of_voice: str = "professional"
    industry: Optional[str] = None
    target_audience: Optional[str] = None
    contact_info: Dict[str, str] = {}
    social_media_handles: Dict[str, str] = {}

class BrandCreate(BrandBase):
    pass

class BrandUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    tone_of_voice: Optional[str] = None
    industry: Optional[str] = None
    target_audience: Optional[str] = None
    contact_info: Optional[Dict[str, str]] = None
    social_media_handles: Optional[Dict[str, str]] = None

class BrandResponse(BrandBase):
    id: int
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Customer Journey Schemas
class CustomerJourneyBase(BaseModel):
    customer_id: int
    journey_type: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    current_stage: str = "started"
    status: str = "active"
    metadata: Dict[str, Any] = {}

class CustomerJourneyCreate(CustomerJourneyBase):
    pass

class CustomerJourneyUpdate(BaseModel):
    description: Optional[str] = None
    current_stage: Optional[str] = None
    status: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class CustomerJourneyResponse(CustomerJourneyBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Proactive Notifications Schemas
class ProactiveNotificationBase(BaseModel):
    customer_id: int
    notification_type: str = Field(..., min_length=1, max_length=50)
    title: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1)
    channel: SupportChannel
    priority: TicketPriority = TicketPriority.MEDIUM
    status: str = "pending"
    scheduled_at: Optional[datetime] = None
    metadata: Dict[str, Any] = {}

class ProactiveNotificationCreate(ProactiveNotificationBase):
    pass

class ProactiveNotificationUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    message: Optional[str] = Field(None, min_length=1)
    channel: Optional[SupportChannel] = None
    priority: Optional[TicketPriority] = None
    status: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None

class ProactiveNotificationResponse(ProactiveNotificationBase):
    id: int
    sent_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

# Agent Training Schemas
class TrainingModuleBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    content: str = Field(..., min_length=1)
    difficulty_level: str = "beginner"
    estimated_duration: Optional[int] = None
    skills_covered: List[str] = []
    prerequisites: List[str] = []

class TrainingModuleCreate(TrainingModuleBase):
    pass

class TrainingModuleUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    content: Optional[str] = Field(None, min_length=1)
    difficulty_level: Optional[str] = None
    estimated_duration: Optional[int] = None
    skills_covered: Optional[List[str]] = None
    prerequisites: Optional[List[str]] = None

class TrainingModuleResponse(TrainingModuleBase):
    id: int
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# ClaraFAQ Schemas
class FAQCategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    parent_category_id: Optional[int] = None

class FAQCategoryCreate(FAQCategoryBase):
    pass

class FAQCategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    parent_category_id: Optional[int] = None

class FAQCategoryResponse(FAQCategoryBase):
    id: int
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class FAQEntryBase(BaseModel):
    category_id: int
    question: str = Field(..., min_length=1)
    answer: str = Field(..., min_length=1)
    keywords: List[str] = []
    tags: List[str] = []

class FAQEntryCreate(FAQEntryBase):
    pass

class FAQEntryUpdate(BaseModel):
    category_id: Optional[int] = None
    question: Optional[str] = Field(None, min_length=1)
    answer: Optional[str] = Field(None, min_length=1)
    keywords: Optional[List[str]] = None
    tags: Optional[List[str]] = None

class FAQEntryResponse(FAQEntryBase):
    id: int
    usage_count: int = 0
    helpful_count: int = 0
    not_helpful_count: int = 0
    success_rate: float = 0.0
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Pagination Schemas
class PaginationParams(BaseModel):
    page: int = Field(1, ge=1)
    size: int = Field(10, ge=1, le=100)
    skip: Optional[int] = None

class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    size: int
    pages: int

# Search Schemas
class SearchParams(BaseModel):
    query: str = Field(..., min_length=1)
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    limit: int = Field(10, ge=1, le=100)

# Response Schemas
class SuccessResponse(BaseModel):
    success: bool = True
    message: str
    data: Optional[Any] = None

class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    details: Optional[Dict[str, Any]] = None

# Health Check Schema
class HealthCheckResponse(BaseModel):
    status: str
    agent: str
    version: str
    features: List[str]
    message: str

# Root Schema
class RootResponse(BaseModel):
    message: str
    agent: str
    version: str
    description: str
    docs: str
    health: str
    features: str
    advanced_capabilities: List[str]
