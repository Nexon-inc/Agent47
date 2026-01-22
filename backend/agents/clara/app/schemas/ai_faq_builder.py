"""
AI ClaraFAQ Builder Schemas
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum

class FAQSourceType(str, Enum):
    CUSTOMER_INTERACTIONS = "customer_interactions"
    SUPPORT_TICKETS = "support_tickets"
    WEBSITE_CONTENT = "website_content"
    DOCUMENTS = "documents"
    MANUAL = "manual"

# ClaraFAQ Category Schemas
class CreateFAQCategoryRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    parent_category_id: Optional[int] = None
    is_active: bool = True

class UpdateFAQCategoryRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    parent_category_id: Optional[int] = None
    is_active: Optional[bool] = None

class FAQCategoryResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    parent_category_id: Optional[int] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# ClaraFAQ Entry Schemas
class CreateFAQEntryRequest(BaseModel):
    category_id: int
    question: str = Field(..., min_length=1)
    answer: str = Field(..., min_length=1)
    keywords: List[str] = []
    tags: List[str] = []
    is_active: bool = True

class UpdateFAQEntryRequest(BaseModel):
    category_id: Optional[int] = None
    question: Optional[str] = Field(None, min_length=1)
    answer: Optional[str] = Field(None, min_length=1)
    keywords: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    is_active: Optional[bool] = None

class FAQEntryResponse(BaseModel):
    id: int
    category_id: int
    question: str
    answer: str
    keywords: List[str]
    tags: List[str]
    usage_count: int
    helpful_count: int
    not_helpful_count: int
    success_rate: float
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# ClaraFAQ Source Schemas
class FAQSourceResponse(BaseModel):
    id: int
    source_type: str
    source_name: str
    source_url: Optional[str] = None
    content: Optional[str] = None
    processed: bool
    faq_entries_generated: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# ClaraFAQ Analytics Schemas
class FAQAnalyticsResponse(BaseModel):
    id: int
    entry_id: int
    date: datetime
    views: int
    helpful_votes: int
    not_helpful_votes: int
    search_rankings: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True

# AI Generation Schemas
class GenerateFAQRequest(BaseModel):
    source_type: FAQSourceType
    source_content: str = Field(..., min_length=1)
    category_id: Optional[int] = None
    max_questions: int = Field(10, ge=1, le=50)
    language: str = "en"
    tone: str = "professional"

class GenerateFAQResponse(BaseModel):
    success: bool
    generated_entries: List[FAQEntryResponse]
    source_id: Optional[int] = None
    processing_time: float
    confidence_score: float

# Search and Analysis Schemas
class FAQSearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    category_id: Optional[int] = None
    tags: Optional[List[str]] = None
    limit: int = Field(10, ge=1, le=100)
    min_confidence: float = Field(0.7, ge=0.0, le=1.0)

class FAQSearchResponse(BaseModel):
    results: List[FAQEntryResponse]
    total_found: int
    search_time: float
    query_analysis: Dict[str, Any]

class FAQAnalyticsRequest(BaseModel):
    start_date: datetime
    end_date: datetime
    category_id: Optional[int] = None
    entry_id: Optional[int] = None

class FAQAnalyticsSummary(BaseModel):
    total_entries: int
    total_views: int
    total_helpful_votes: int
    total_not_helpful_votes: int
    average_success_rate: float
    most_viewed_entries: List[FAQEntryResponse]
    most_helpful_entries: List[FAQEntryResponse]
    category_performance: Dict[str, Any]

# Bulk Operations Schemas
class BulkFAQGenerationRequest(BaseModel):
    sources: List[Dict[str, Any]]
    category_id: Optional[int] = None
    max_questions_per_source: int = Field(5, ge=1, le=20)
    language: str = "en"
    tone: str = "professional"

class BulkFAQGenerationResponse(BaseModel):
    success: bool
    total_generated: int
    sources_processed: int
    processing_time: float
    results: List[GenerateFAQResponse]

# Quality Assessment Schemas
class FAQQualityAssessment(BaseModel):
    entry_id: int
    clarity_score: float
    completeness_score: float
    relevance_score: float
    suggested_improvements: List[str]
    overall_score: float

class FAQQualityReport(BaseModel):
    total_assessed: int
    average_clarity: float
    average_completeness: float
    average_relevance: float
    overall_quality_score: float
    entries_needing_improvement: List[FAQQualityAssessment]
    recommendations: List[str]
