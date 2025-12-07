from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import json

from ..database import get_db
from ..services.ai_faq_builder_service import AIFAQBuilderService
from ..models import FAQEntry, FAQCategory, FAQSource, FAQAnalytics, KnowledgeBase
from ..core.integration_manager import IntegrationManager
from ..core.event_bus import EventBus

router = APIRouter()

# Pydantic models for request/response
class CreateFAQCategoryRequest(BaseModel):
    category_name: str = Field(..., description="Category name")
    description: Optional[str] = Field(None, description="Category description")
    parent_category_id: Optional[int] = Field(None, description="Parent category ID")
    is_active: bool = Field(True, description="Category active status")

class UpdateFAQCategoryRequest(BaseModel):
    category_name: Optional[str] = Field(None, description="Category name")
    description: Optional[str] = Field(None, description="Category description")
    parent_category_id: Optional[int] = Field(None, description="Parent category ID")
    is_active: Optional[bool] = Field(None, description="Category active status")

class CreateFAQEntryRequest(BaseModel):
    question: str = Field(..., description="FAQ question")
    answer: str = Field(..., description="FAQ answer")
    category_id: int = Field(..., description="Category ID")
    tags: List[str] = Field([], description="FAQ tags")
    priority: str = Field("medium", description="FAQ priority")
    is_active: bool = Field(True, description="FAQ active status")
    source_type: str = Field(..., description="Source type (auto_generated, manual, imported)")

class UpdateFAQEntryRequest(BaseModel):
    question: Optional[str] = Field(None, description="FAQ question")
    answer: Optional[str] = Field(None, description="FAQ answer")
    category_id: Optional[int] = Field(None, description="Category ID")
    tags: Optional[List[str]] = Field(None, description="FAQ tags")
    priority: Optional[str] = Field(None, description="FAQ priority")
    is_active: Optional[bool] = Field(None, description="FAQ active status")

class GenerateFAQRequest(BaseModel):
    source_type: str = Field(..., description="Source type (interactions, tickets, website, documents)")
    source_data: Optional[Dict[str, Any]] = Field(None, description="Source data")
    category_id: Optional[int] = Field(None, description="Target category ID")
    max_faqs: int = Field(10, description="Maximum number of FAQs to generate")
    confidence_threshold: float = Field(0.7, description="Confidence threshold for generation")

class FAQCategoryResponse(BaseModel):
    id: int
    category_name: str
    description: Optional[str]
    parent_category_id: Optional[int]
    is_active: bool
    faq_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class FAQEntryResponse(BaseModel):
    id: int
    question: str
    answer: str
    category_id: int
    tags: List[str]
    priority: str
    is_active: bool
    source_type: str
    confidence_score: Optional[float]
    view_count: int
    helpful_count: int
    not_helpful_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class FAQSourceResponse(BaseModel):
    id: int
    source_type: str
    source_name: str
    source_data: Dict[str, Any]
    processed_at: datetime
    faqs_generated: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class FAQAnalyticsResponse(BaseModel):
    total_faqs: int
    active_faqs: int
    total_views: int
    average_helpfulness: float
    top_performing_faqs: List[Dict[str, Any]]
    popular_categories: List[Dict[str, Any]]
    search_analytics: Dict[str, Any]
    generation_metrics: Dict[str, Any]

# Dependency
async def get_ai_faq_builder_service(db: AsyncSession = Depends(get_db)) -> AIFAQBuilderService:
    integration_manager = IntegrationManager()
    event_bus = EventBus()
    return AIFAQBuilderService(db, integration_manager, event_bus)

# FAQ Category Management
@router.post("/categories", response_model=FAQCategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_faq_category(
    request: CreateFAQCategoryRequest,
    service: AIFAQBuilderService = Depends(get_ai_faq_builder_service)
):
    """Create a new FAQ category"""
    try:
        category = await service.create_faq_category(
            category_name=request.category_name,
            description=request.description,
            parent_category_id=request.parent_category_id,
            is_active=request.is_active
        )
        return FAQCategoryResponse.from_orm(category)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/categories", response_model=List[FAQCategoryResponse])
async def get_faq_categories(
    active_only: bool = True,
    include_faq_count: bool = True,
    service: AIFAQBuilderService = Depends(get_ai_faq_builder_service)
):
    """Get FAQ categories with optional filtering"""
    try:
        categories = await service.get_faq_categories(
            active_only=active_only,
            include_faq_count=include_faq_count
        )
        return [FAQCategoryResponse.from_orm(category) for category in categories]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/categories/{category_id}", response_model=FAQCategoryResponse)
async def get_faq_category(
    category_id: int,
    service: AIFAQBuilderService = Depends(get_ai_faq_builder_service)
):
    """Get a specific FAQ category by ID"""
    try:
        category = await service.get_faq_category(category_id)
        if not category:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="FAQ category not found")
        return FAQCategoryResponse.from_orm(category)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.put("/categories/{category_id}", response_model=FAQCategoryResponse)
async def update_faq_category(
    category_id: int,
    request: UpdateFAQCategoryRequest,
    service: AIFAQBuilderService = Depends(get_ai_faq_builder_service)
):
    """Update a FAQ category"""
    try:
        category = await service.update_faq_category(
            category_id=category_id,
            category_name=request.category_name,
            description=request.description,
            parent_category_id=request.parent_category_id,
            is_active=request.is_active
        )
        if not category:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="FAQ category not found")
        return FAQCategoryResponse.from_orm(category)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_faq_category(
    category_id: int,
    service: AIFAQBuilderService = Depends(get_ai_faq_builder_service)
):
    """Delete a FAQ category"""
    try:
        success = await service.delete_faq_category(category_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="FAQ category not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# FAQ Entry Management
@router.post("/entries", response_model=FAQEntryResponse, status_code=status.HTTP_201_CREATED)
async def create_faq_entry(
    request: CreateFAQEntryRequest,
    service: AIFAQBuilderService = Depends(get_ai_faq_builder_service)
):
    """Create a new FAQ entry"""
    try:
        entry = await service.create_faq_entry(
            question=request.question,
            answer=request.answer,
            category_id=request.category_id,
            tags=request.tags,
            priority=request.priority,
            is_active=request.is_active,
            source_type=request.source_type
        )
        return FAQEntryResponse.from_orm(entry)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/entries", response_model=List[FAQEntryResponse])
async def get_faq_entries(
    category_id: Optional[int] = None,
    tags: Optional[List[str]] = None,
    priority: Optional[str] = None,
    source_type: Optional[str] = None,
    active_only: bool = True,
    search_query: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    service: AIFAQBuilderService = Depends(get_ai_faq_builder_service)
):
    """Get FAQ entries with optional filtering and search"""
    try:
        entries = await service.get_faq_entries(
            category_id=category_id,
            tags=tags,
            priority=priority,
            source_type=source_type,
            active_only=active_only,
            search_query=search_query,
            limit=limit,
            offset=offset
        )
        return [FAQEntryResponse.from_orm(entry) for entry in entries]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/entries/{entry_id}", response_model=FAQEntryResponse)
async def get_faq_entry(
    entry_id: int,
    service: AIFAQBuilderService = Depends(get_ai_faq_builder_service)
):
    """Get a specific FAQ entry by ID"""
    try:
        entry = await service.get_faq_entry(entry_id)
        if not entry:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="FAQ entry not found")
        return FAQEntryResponse.from_orm(entry)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.put("/entries/{entry_id}", response_model=FAQEntryResponse)
async def update_faq_entry(
    entry_id: int,
    request: UpdateFAQEntryRequest,
    service: AIFAQBuilderService = Depends(get_ai_faq_builder_service)
):
    """Update a FAQ entry"""
    try:
        entry = await service.update_faq_entry(
            entry_id=entry_id,
            question=request.question,
            answer=request.answer,
            category_id=request.category_id,
            tags=request.tags,
            priority=request.priority,
            is_active=request.is_active
        )
        if not entry:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="FAQ entry not found")
        return FAQEntryResponse.from_orm(entry)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.delete("/entries/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_faq_entry(
    entry_id: int,
    service: AIFAQBuilderService = Depends(get_ai_faq_builder_service)
):
    """Delete a FAQ entry"""
    try:
        success = await service.delete_faq_entry(entry_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="FAQ entry not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# AI-Driven FAQ Generation
@router.post("/generate", response_model=List[FAQEntryResponse])
async def generate_faqs(
    request: GenerateFAQRequest,
    service: AIFAQBuilderService = Depends(get_ai_faq_builder_service)
):
    """Generate FAQs from various sources using AI"""
    try:
        generated_faqs = await service.generate_faqs(
            source_type=request.source_type,
            source_data=request.source_data,
            category_id=request.category_id,
            max_faqs=request.max_faqs,
            confidence_threshold=request.confidence_threshold
        )
        return [FAQEntryResponse.from_orm(faq) for faq in generated_faqs]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/generate-from-interactions")
async def generate_faqs_from_interactions(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    category_id: Optional[int] = None,
    max_faqs: int = 20,
    service: AIFAQBuilderService = Depends(get_ai_faq_builder_service)
):
    """Generate FAQs from customer interactions"""
    try:
        generated_faqs = await service.generate_faqs_from_interactions(
            start_date=start_date,
            end_date=end_date,
            category_id=category_id,
            max_faqs=max_faqs
        )
        return generated_faqs
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/generate-from-tickets")
async def generate_faqs_from_tickets(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    ticket_status: Optional[str] = None,
    category_id: Optional[int] = None,
    max_faqs: int = 20,
    service: AIFAQBuilderService = Depends(get_ai_faq_builder_service)
):
    """Generate FAQs from support tickets"""
    try:
        generated_faqs = await service.generate_faqs_from_tickets(
            start_date=start_date,
            end_date=end_date,
            ticket_status=ticket_status,
            category_id=category_id,
            max_faqs=max_faqs
        )
        return generated_faqs
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/generate-from-website")
async def generate_faqs_from_website(
    website_url: str,
    content_type: str = "general",
    category_id: Optional[int] = None,
    max_faqs: int = 15,
    service: AIFAQBuilderService = Depends(get_ai_faq_builder_service)
):
    """Generate FAQs from website content"""
    try:
        generated_faqs = await service.generate_faqs_from_website(
            website_url=website_url,
            content_type=content_type,
            category_id=category_id,
            max_faqs=max_faqs
        )
        return generated_faqs
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/generate-from-documents")
async def generate_faqs_from_documents(
    document_urls: List[str],
    document_type: str = "general",
    category_id: Optional[int] = None,
    max_faqs: int = 25,
    service: AIFAQBuilderService = Depends(get_ai_faq_builder_service)
):
    """Generate FAQs from uploaded documents"""
    try:
        generated_faqs = await service.generate_faqs_from_documents(
            document_urls=document_urls,
            document_type=document_type,
            category_id=category_id,
            max_faqs=max_faqs
        )
        return generated_faqs
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

# FAQ Source Management
@router.get("/sources", response_model=List[FAQSourceResponse])
async def get_faq_sources(
    source_type: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    service: AIFAQBuilderService = Depends(get_ai_faq_builder_service)
):
    """Get FAQ sources with optional filtering"""
    try:
        sources = await service.get_faq_sources(
            source_type=source_type,
            status=status,
            start_date=start_date,
            end_date=end_date
        )
        return [FAQSourceResponse.from_orm(source) for source in sources]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/sources/{source_id}", response_model=FAQSourceResponse)
async def get_faq_source(
    source_id: int,
    service: AIFAQBuilderService = Depends(get_ai_faq_builder_service)
):
    """Get a specific FAQ source by ID"""
    try:
        source = await service.get_faq_source(source_id)
        if not source:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="FAQ source not found")
        return FAQSourceResponse.from_orm(source)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# FAQ Analytics and Insights
@router.get("/analytics", response_model=FAQAnalyticsResponse)
async def get_faq_analytics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    category_id: Optional[int] = None,
    service: AIFAQBuilderService = Depends(get_ai_faq_builder_service)
):
    """Get FAQ analytics and insights"""
    try:
        analytics = await service.get_faq_analytics(
            start_date=start_date,
            end_date=end_date,
            category_id=category_id
        )
        return FAQAnalyticsResponse(**analytics)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/entries/{entry_id}/view")
async def record_faq_view(
    entry_id: int,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    service: AIFAQBuilderService = Depends(get_ai_faq_builder_service)
):
    """Record a FAQ view"""
    try:
        result = await service.record_faq_view(
            entry_id=entry_id,
            user_id=user_id,
            session_id=session_id
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/entries/{entry_id}/feedback")
async def record_faq_feedback(
    entry_id: int,
    feedback_type: str,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    service: AIFAQBuilderService = Depends(get_ai_faq_builder_service)
):
    """Record FAQ feedback (helpful/not helpful)"""
    try:
        result = await service.record_faq_feedback(
            entry_id=entry_id,
            feedback_type=feedback_type,
            user_id=user_id,
            session_id=session_id
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

# FAQ Search and Recommendations
@router.get("/search")
async def search_faqs(
    query: str,
    category_id: Optional[int] = None,
    limit: int = 10,
    include_similar: bool = True,
    service: AIFAQBuilderService = Depends(get_ai_faq_builder_service)
):
    """Search FAQs with semantic understanding"""
    try:
        search_results = await service.search_faqs(
            query=query,
            category_id=category_id,
            limit=limit,
            include_similar=include_similar
        )
        return search_results
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/recommendations")
async def get_faq_recommendations(
    context: Optional[str] = None,
    user_id: Optional[str] = None,
    category_id: Optional[int] = None,
    limit: int = 5,
    service: AIFAQBuilderService = Depends(get_ai_faq_builder_service)
):
    """Get personalized FAQ recommendations"""
    try:
        recommendations = await service.get_faq_recommendations(
            context=context,
            user_id=user_id,
            category_id=category_id,
            limit=limit
        )
        return recommendations
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# FAQ Quality and Optimization
@router.post("/entries/{entry_id}/optimize")
async def optimize_faq_entry(
    entry_id: int,
    optimization_type: str = "content",
    service: AIFAQBuilderService = Depends(get_ai_faq_builder_service)
):
    """Optimize a FAQ entry using AI"""
    try:
        optimized_entry = await service.optimize_faq_entry(
            entry_id=entry_id,
            optimization_type=optimization_type
        )
        return optimized_entry
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/batch-optimize")
async def batch_optimize_faqs(
    category_id: Optional[int] = None,
    optimization_type: str = "content",
    max_entries: int = 50,
    service: AIFAQBuilderService = Depends(get_ai_faq_builder_service)
):
    """Batch optimize multiple FAQ entries"""
    try:
        optimization_results = await service.batch_optimize_faqs(
            category_id=category_id,
            optimization_type=optimization_type,
            max_entries=max_entries
        )
        return optimization_results
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/entries/{entry_id}/duplicate-check")
async def check_faq_duplicates(
    entry_id: int,
    threshold: float = 0.8,
    service: AIFAQBuilderService = Depends(get_ai_faq_builder_service)
):
    """Check for duplicate FAQ entries"""
    try:
        duplicates = await service.check_faq_duplicates(
            entry_id=entry_id,
            threshold=threshold
        )
        return duplicates
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

# FAQ Export and Import
@router.post("/export")
async def export_faqs(
    category_id: Optional[int] = None,
    format: str = "json",
    include_analytics: bool = True,
    service: AIFAQBuilderService = Depends(get_ai_faq_builder_service)
):
    """Export FAQs in specified format"""
    try:
        export_data = await service.export_faqs(
            category_id=category_id,
            format=format,
            include_analytics=include_analytics
        )
        return export_data
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/import")
async def import_faqs(
    import_data: Dict[str, Any],
    category_mapping: Optional[Dict[str, int]] = None,
    service: AIFAQBuilderService = Depends(get_ai_faq_builder_service)
):
    """Import FAQs from external source"""
    try:
        import_results = await service.import_faqs(
            import_data=import_data,
            category_mapping=category_mapping
        )
        return import_results
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

# Health Check
@router.get("/health")
async def health_check():
    """Health check endpoint for AI-Driven FAQ Builder"""
    return {
        "status": "healthy",
        "service": "AI-Driven FAQ Builder",
        "features": [
            "faq_category_management",
            "faq_entry_management",
            "ai_driven_generation",
            "source_management",
            "faq_analytics",
            "semantic_search",
            "personalized_recommendations",
            "faq_optimization",
            "duplicate_detection",
            "export_import"
        ],
        "message": "AI-Driven FAQ Builder service is running and ready!"
    }
