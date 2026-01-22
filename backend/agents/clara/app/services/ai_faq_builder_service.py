from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from fastapi import HTTPException, BackgroundTasks
import json
import asyncio
from enum import Enum

from ..models import (
    ClaraFAQEntry, ClaraFAQCategory, ClaraFAQSource, ClaraFAQAnalytics, ClaraKnowledgeBase,
    ClaraCustomerInteraction, ClaraSupportTicket, ClaraSupportAgent
)
from ..schemas.ai_faq_builder import (
    CreateFAQCategoryRequest, UpdateFAQCategoryRequest,
    CreateFAQEntryRequest, UpdateFAQEntryRequest,
    GenerateFAQRequest, FAQCategoryResponse, FAQEntryResponse,
    FAQSourceResponse, FAQAnalyticsResponse
)
from ..database import get_clara_database
from core.config import settings
from core.integrations import IntegrationManager
from core.analytics import AnalyticsManager
from core.ai import get_ai_service_manager
from core.utils.nlp_utils import NLPUtils


class FAQSourceType(str, Enum):
    CUSTOMER_INTERACTIONS = "customer_interactions"
    SUPPORT_TICKETS = "support_tickets"
    WEBSITE_CONTENT = "website_content"
    DOCUMENTS = "documents"
    MANUAL = "manual"


class AIFAQBuilderService:
    def __init__(self):
        self.integration_manager = IntegrationManager()
        self.analytics_manager = AnalyticsManager()
        self.nlp_utils = NLPUtils()
        
    async def create_faq_category(
        self, 
        db: Session, 
        request: CreateFAQCategoryRequest
    ) -> FAQCategoryResponse:
        """Create a new ClaraFAQ category"""
        try:
            category = ClaraFAQCategory(
                name=request.name,
                description=request.description,
                parent_category_id=request.parent_category_id,
                is_active=request.is_active,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(category)
            db.commit()
            db.refresh(category)
            
            return FAQCategoryResponse(
                id=category.id,
                name=category.name,
                description=category.description,
                parent_category_id=category.parent_category_id,
                is_active=category.is_active,
                created_at=category.created_at,
                updated_at=category.updated_at
            )
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to create ClaraFAQ category: {str(e)}")
    
    async def get_faq_category(
        self, 
        db: Session, 
        category_id: int
    ) -> FAQCategoryResponse:
        """Get ClaraFAQ category by ID"""
        category = db.query(ClaraFAQCategory).filter(ClaraFAQCategory.id == category_id).first()
        if not category:
            raise HTTPException(status_code=404, detail="ClaraFAQ category not found")
        
        return FAQCategoryResponse(
            id=category.id,
            name=category.name,
            description=category.description,
            parent_category_id=category.parent_category_id,
            is_active=category.is_active,
            created_at=category.created_at,
            updated_at=category.updated_at
        )
    
    async def list_faq_categories(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        is_active: Optional[bool] = None
    ) -> List[FAQCategoryResponse]:
        """List ClaraFAQ categories"""
        query = db.query(ClaraFAQCategory)
        
        if is_active is not None:
            query = query.filter(ClaraFAQCategory.is_active == is_active)
        
        categories = query.offset(skip).limit(limit).all()
        
        return [
            FAQCategoryResponse(
                id=category.id,
                name=category.name,
                description=category.description,
                parent_category_id=category.parent_category_id,
                is_active=category.is_active,
                created_at=category.created_at,
                updated_at=category.updated_at
            ) for category in categories
        ]
    
    async def create_faq_entry(
        self, 
        db: Session, 
        request: CreateFAQEntryRequest
    ) -> FAQEntryResponse:
        """Create a new ClaraFAQ entry"""
        try:
            entry = ClaraFAQEntry(
                question=request.question,
                answer=request.answer,
                category_id=request.category_id,
                keywords=request.keywords,
                tags=request.tags,
                is_active=request.is_active,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(entry)
            db.commit()
            db.refresh(entry)
            
            return FAQEntryResponse(
                id=entry.id,
                question=entry.question,
                answer=entry.answer,
                category_id=entry.category_id,
                keywords=entry.keywords,
                tags=entry.tags,
                is_active=entry.is_active,
                created_at=entry.created_at,
                updated_at=entry.updated_at
            )
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to create ClaraFAQ entry: {str(e)}")
    
    async def get_faq_entry(
        self, 
        db: Session, 
        entry_id: int
    ) -> FAQEntryResponse:
        """Get ClaraFAQ entry by ID"""
        entry = db.query(ClaraFAQEntry).filter(ClaraFAQEntry.id == entry_id).first()
        if not entry:
            raise HTTPException(status_code=404, detail="ClaraFAQ entry not found")
        
        return FAQEntryResponse(
            id=entry.id,
            question=entry.question,
            answer=entry.answer,
            category_id=entry.category_id,
            keywords=entry.keywords,
            tags=entry.tags,
            is_active=entry.is_active,
            created_at=entry.created_at,
            updated_at=entry.updated_at
        )
    
    async def list_faq_entries(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        category_id: Optional[int] = None,
        is_active: Optional[bool] = None
    ) -> List[FAQEntryResponse]:
        """List ClaraFAQ entries"""
        query = db.query(ClaraFAQEntry)
        
        if category_id:
            query = query.filter(ClaraFAQEntry.category_id == category_id)
        if is_active is not None:
            query = query.filter(ClaraFAQEntry.is_active == is_active)
        
        entries = query.offset(skip).limit(limit).all()
        
        return [
            FAQEntryResponse(
                id=entry.id,
                question=entry.question,
                answer=entry.answer,
                category_id=entry.category_id,
                keywords=entry.keywords,
                tags=entry.tags,
                is_active=entry.is_active,
                created_at=entry.created_at,
                updated_at=entry.updated_at
            ) for entry in entries
        ]
    
    async def generate_faq_from_interactions(
        self, 
        db: Session, 
        request: GenerateFAQRequest
    ) -> List[FAQEntryResponse]:
        """Generate ClaraFAQ entries from customer interactions"""
        try:
            # Get recent customer interactions
            interactions = db.query(ClaraCustomerInteraction).filter(
                and_(
                    ClaraCustomerInteraction.created_at >= datetime.utcnow() - timedelta(days=request.days_back),
                    ClaraCustomerInteraction.interaction_type == "question"
                )
            ).all()
            
            # Group similar questions
            question_groups = self._group_similar_questions(interactions)
            
            # Generate ClaraFAQ entries
            generated_entries = []
            for group in question_groups:
                if len(group) >= request.min_occurrences:
                    # Generate question and answer
                    question = await self._generate_question_from_group(group)
                    answer = await self._generate_answer_from_group(group)
                    
                    # Create ClaraFAQ entry
                    entry = ClaraFAQEntry(
                        question=question,
                        answer=answer,
                        category_id=request.category_id,
                        keywords=await self._extract_keywords(question),
                        tags=self._extract_tags(group),
                        is_active=True,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    
                    db.add(entry)
                    generated_entries.append(entry)
            
            db.commit()
            
            # Log generation event
            await self._log_faq_event("faq_generated", {
                "source": "interactions",
                "entries_generated": len(generated_entries),
                "days_back": request.days_back
            })
            
            return [
                FAQEntryResponse(
                    id=entry.id,
                    question=entry.question,
                    answer=entry.answer,
                    category_id=entry.category_id,
                    keywords=entry.keywords,
                    tags=entry.tags,
                    is_active=entry.is_active,
                    created_at=entry.created_at,
                    updated_at=entry.updated_at
                ) for entry in generated_entries
            ]
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to generate ClaraFAQ from interactions: {str(e)}")
    
    async def generate_faq_from_tickets(
        self, 
        db: Session, 
        request: GenerateFAQRequest
    ) -> List[FAQEntryResponse]:
        """Generate ClaraFAQ entries from support tickets"""
        try:
            # Get recent support tickets
            tickets = db.query(ClaraSupportTicket).filter(
                and_(
                    ClaraSupportTicket.created_at >= datetime.utcnow() - timedelta(days=request.days_back),
                    ClaraSupportTicket.status == "resolved"
                )
            ).all()
            
            # Group similar ticket issues
            ticket_groups = self._group_similar_tickets(tickets)
            
            # Generate ClaraFAQ entries
            generated_entries = []
            for group in ticket_groups:
                if len(group) >= request.min_occurrences:
                    # Generate question and answer
                    question = await self._generate_question_from_tickets(group)
                    answer = await self._generate_answer_from_tickets(group)
                    
                    # Create ClaraFAQ entry
                    entry = ClaraFAQEntry(
                        question=question,
                        answer=answer,
                        category_id=request.category_id,
                        keywords=await self._extract_keywords(question),
                        tags=self._extract_tags_from_tickets(group),
                        is_active=True,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    
                    db.add(entry)
                    generated_entries.append(entry)
            
            db.commit()
            
            return [
                FAQEntryResponse(
                    id=entry.id,
                    question=entry.question,
                    answer=entry.answer,
                    category_id=entry.category_id,
                    keywords=entry.keywords,
                    tags=entry.tags,
                    is_active=entry.is_active,
                    created_at=entry.created_at,
                    updated_at=entry.updated_at
                ) for entry in generated_entries
            ]
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to generate ClaraFAQ from tickets: {str(e)}")
    
    async def generate_faq_from_website(
        self, 
        db: Session, 
        request: GenerateFAQRequest
    ) -> List[FAQEntryResponse]:
        """Generate ClaraFAQ entries from website content"""
        try:
            # Extract content from website
            website_content = await self._extract_website_content(request.website_url)
            
            # Process content to identify potential ClaraFAQ topics
            faq_topics = await self._identify_faq_topics(website_content)
            
            # Generate ClaraFAQ entries
            generated_entries = []
            for topic in faq_topics:
                question = topic["question"]
                answer = await self._generate_answer_from_content(topic["content"])
                
                entry = ClaraFAQEntry(
                    question=question,
                    answer=answer,
                    category_id=request.category_id,
                    keywords=self._extract_keywords(question),
                    tags=topic["tags"],
                    is_active=True,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                
                db.add(entry)
                generated_entries.append(entry)
            
            db.commit()
            
            return [
                FAQEntryResponse(
                    id=entry.id,
                    question=entry.question,
                    answer=entry.answer,
                    category_id=entry.category_id,
                    keywords=entry.keywords,
                    tags=entry.tags,
                    is_active=entry.is_active,
                    created_at=entry.created_at,
                    updated_at=entry.updated_at
                ) for entry in generated_entries
            ]
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to generate ClaraFAQ from website: {str(e)}")
    
    async def search_faq(
        self, 
        db: Session, 
        query: str,
        limit: int = 10
    ) -> List[FAQEntryResponse]:
        """Search ClaraFAQ entries"""
        try:
            # Use semantic search to find relevant entries
            relevant_entries = await self._semantic_search_faq(db, query, limit)
            
            return [
                FAQEntryResponse(
                    id=entry.id,
                    question=entry.question,
                    answer=entry.answer,
                    category_id=entry.category_id,
                    keywords=entry.keywords,
                    tags=entry.tags,
                    is_active=entry.is_active,
                    created_at=entry.created_at,
                    updated_at=entry.updated_at
                ) for entry in relevant_entries
            ]
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to search ClaraFAQ: {str(e)}")
    
    async def get_faq_analytics(
        self, 
        db: Session, 
        start_date: datetime,
        end_date: datetime
    ) -> FAQAnalyticsResponse:
        """Get ClaraFAQ analytics"""
        try:
            # Get ClaraFAQ entries in date range
            entries = db.query(ClaraFAQEntry).filter(
                and_(
                    ClaraFAQEntry.created_at >= start_date,
                    ClaraFAQEntry.created_at <= end_date
                )
            ).all()
            
            # Get ClaraFAQ analytics
            analytics = db.query(ClaraFAQAnalytics).filter(
                and_(
                    ClaraFAQAnalytics.created_at >= start_date,
                    ClaraFAQAnalytics.created_at <= end_date
                )
            ).all()
            
            # Calculate metrics
            total_entries = len(entries)
            active_entries = len([e for e in entries if e.is_active])
            total_views = sum(a.views for a in analytics)
            total_helpful_votes = sum(a.helpful_votes for a in analytics)
            total_not_helpful_votes = sum(a.not_helpful_votes for a in analytics)
            
            # Category breakdown
            category_stats = {}
            for entry in entries:
                category_id = entry.category_id
                if category_id not in category_stats:
                    category_stats[category_id] = {"total": 0, "active": 0}
                category_stats[category_id]["total"] += 1
                if entry.is_active:
                    category_stats[category_id]["active"] += 1
            
            return FAQAnalyticsResponse(
                period_start=start_date,
                period_end=end_date,
                total_entries=total_entries,
                active_entries=active_entries,
                total_views=total_views,
                total_helpful_votes=total_helpful_votes,
                total_not_helpful_votes=total_not_helpful_votes,
                helpful_rate=total_helpful_votes / (total_helpful_votes + total_not_helpful_votes) if (total_helpful_votes + total_not_helpful_votes) > 0 else 0,
                category_breakdown=category_stats
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get ClaraFAQ analytics: {str(e)}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check the health of AI ClaraFAQ Builder system"""
        try:
            db = next(get_db())
            category_count = db.query(ClaraFAQCategory).count()
            entry_count = db.query(ClaraFAQEntry).count()
            source_count = db.query(ClaraFAQSource).count()
            
            return {
                "status": "healthy",
                "database": {
                    "connected": True,
                    "categories_count": category_count,
                    "entries_count": entry_count,
                    "sources_count": source_count
                },
                "last_check": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "last_check": datetime.utcnow().isoformat()
            }
    
    def _group_similar_questions(self, interactions: List[ClaraCustomerInteraction]) -> List[List[ClaraCustomerInteraction]]:
        """Group similar customer questions"""
        # Use NLP to group similar questions
        groups = []
        processed = set()
        
        for interaction in interactions:
            if interaction.id in processed:
                continue
            
            group = [interaction]
            processed.add(interaction.id)
            
            for other in interactions:
                if other.id not in processed:
                    similarity = self.nlp_utils.calculate_similarity(
                        interaction.content, other.content
                    )
                    if similarity > 0.8:  # High similarity threshold
                        group.append(other)
                        processed.add(other.id)
            
            if len(group) > 1:
                groups.append(group)
        
        return groups
    
    def _group_similar_tickets(self, tickets: List[ClaraSupportTicket]) -> List[List[ClaraSupportTicket]]:
        """Group similar support tickets"""
        groups = []
        processed = set()
        
        for ticket in tickets:
            if ticket.id in processed:
                continue
            
            group = [ticket]
            processed.add(ticket.id)
            
            for other in tickets:
                if other.id not in processed and other.category == ticket.category:
                    similarity = self.nlp_utils.calculate_similarity(
                        ticket.description, other.description
                    )
                    if similarity > 0.7:
                        group.append(other)
                        processed.add(other.id)
            
            if len(group) > 1:
                groups.append(group)
        
        return groups
    
    async def _generate_question_from_group(self, group: List[ClaraCustomerInteraction]) -> str:
        """Generate a question from a group of similar interactions"""
        # Use the most common question pattern
        questions = [i.content for i in group]
        # Use AI Service Manager for extracting common questions
        ai_manager = await get_ai_service_manager()
        questions_text = "\n".join([f"- {q}" for q in questions])
        messages = [{"role": "system", "content": "You are an AI assistant that identifies common questions from a list. Respond with only the most common question."}, {"role": "user", "content": f"Identify the most common question from these: {questions_text}"}]
        ai_response = await ai_manager.generate_text(messages=messages, max_tokens=200, temperature=0.3)
        return ai_response.text_content.strip() if ai_response.success else questions[0] if questions else ""
    
    async def _generate_question_from_tickets(self, group: List[ClaraSupportTicket]) -> str:
        """Generate a question from a group of similar tickets"""
        descriptions = [t.description for t in group]
        # Use AI Service Manager for extracting common questions
        ai_manager = await get_ai_service_manager()
        descriptions_text = "\n".join([f"- {d}" for d in descriptions])
        messages = [{"role": "system", "content": "You are an AI assistant that identifies common questions from ticket descriptions. Respond with only the most common question."}, {"role": "user", "content": f"Identify the most common question from these descriptions: {descriptions_text}"}]
        ai_response = await ai_manager.generate_text(messages=messages, max_tokens=200, temperature=0.3)
        return ai_response.text_content.strip() if ai_response.success else descriptions[0] if descriptions else ""
    
    async def _generate_answer_from_group(self, group: List[ClaraCustomerInteraction]) -> str:
        """Generate an answer from a group of similar interactions"""
        # Use AI Service Manager to generate answer based on agent responses
        responses = [i.agent_response for i in group if i.agent_response]
        if responses:
            from core.ai import get_ai_service_manager
            ai_manager = await get_ai_service_manager()
            prompt = f"Based on these customer support responses, generate a concise ClaraFAQ answer:\n\n" + "\n\n".join(responses)
            messages = [
                {"role": "system", "content": "You are an AI assistant that creates ClaraFAQ answers from support responses."},
                {"role": "user", "content": prompt}
            ]
            ai_response = await ai_manager.generate_text(messages=messages, max_tokens=300, temperature=0.7)
            return ai_response.text_content if ai_response.success else "Please contact our support team for assistance."
        return "Please contact our support team for assistance."
    
    async def _generate_answer_from_tickets(self, group: List[ClaraSupportTicket]) -> str:
        """Generate an answer from a group of similar tickets"""
        resolutions = [t.resolution for t in group if t.resolution]
        if resolutions:
            from core.ai import get_ai_service_manager
            ai_manager = await get_ai_service_manager()
            prompt = f"Based on these ticket resolutions, generate a concise ClaraFAQ answer:\n\n" + "\n\n".join(resolutions)
            messages = [
                {"role": "system", "content": "You are an AI assistant that creates ClaraFAQ answers from ticket resolutions."},
                {"role": "user", "content": prompt}
            ]
            ai_response = await ai_manager.generate_text(messages=messages, max_tokens=300, temperature=0.7)
            return ai_response.text_content if ai_response.success else "Please contact our support team for assistance."
        return "Please contact our support team for assistance."
    
    async def _extract_website_content(self, url: str) -> str:
        """Extract content from website"""
        # Use integration manager to fetch website content
        return await self.integration_manager.fetch_website_content(url)
    
    async def _identify_faq_topics(self, content: str) -> List[Dict[str, Any]]:
        """Identify potential ClaraFAQ topics from content"""
        # Use NLP to identify ClaraFAQ-worthy topics
        # Use AI Service Manager for identifying ClaraFAQ topics
        ai_manager = await get_ai_service_manager()
        messages = [{"role": "system", "content": "You are an AI assistant that identifies ClaraFAQ topics from content. Return a comma-separated list of topics."}, {"role": "user", "content": f"Identify ClaraFAQ topics from: {content}"}]
        ai_response = await ai_manager.generate_text(messages=messages, max_tokens=200, temperature=0.3)
        topics_str = ai_response.text_content if ai_response.success else ""
        topics = [t.strip() for t in topics_str.split(",") if t.strip()]
        return topics
    
    async def _generate_answer_from_content(self, content: str) -> str:
        """Generate answer from content using AI Service Manager"""
        from core.ai import get_ai_service_manager
        ai_manager = await get_ai_service_manager()
        prompt = f"Based on this content, generate a concise ClaraFAQ answer:\n\n{content}"
        messages = [
            {"role": "system", "content": "You are an AI assistant that creates ClaraFAQ answers from content."},
            {"role": "user", "content": prompt}
        ]
        ai_response = await ai_manager.generate_text(messages=messages, max_tokens=300, temperature=0.7)
        return ai_response.text_content if ai_response.success else "Please contact our support team for assistance."
    
    async def _semantic_search_faq(self, db: Session, query: str, limit: int) -> List[ClaraFAQEntry]:
        """Perform semantic search on ClaraFAQ entries"""
        # Use vector search to find relevant entries
        return await self.nlp_utils.semantic_search_faq(db, query, limit)
    
    async def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text"""
        # Use AI Service Manager for keyword extraction
        ai_manager = await get_ai_service_manager()
        messages = [{"role": "system", "content": "You are an AI assistant that extracts keywords from text. Return a comma-separated list of keywords."}, {"role": "user", "content": f"Extract keywords from: {text}"}]
        ai_response = await ai_manager.generate_text(messages=messages, max_tokens=200, temperature=0.3)
        keywords_str = ai_response.text_content if ai_response.success else ""
        keywords = [k.strip() for k in keywords_str.split(",") if k.strip()]
        return keywords
    
    def _extract_tags(self, group: List[ClaraCustomerInteraction]) -> List[str]:
        """Extract tags from interaction group"""
        tags = set()
        for interaction in group:
            if interaction.tags:
                tags.update(interaction.tags)
        return list(tags)
    
    def _extract_tags_from_tickets(self, group: List[ClaraSupportTicket]) -> List[str]:
        """Extract tags from ticket group"""
        tags = set()
        for ticket in group:
            if ticket.tags:
                tags.update(ticket.tags)
        return list(tags)
    
    async def _log_faq_event(self, event_type: str, data: Dict[str, Any]):
        """Log ClaraFAQ events for analytics"""
        try:
            log_data = {
                "event_type": event_type,
                "timestamp": datetime.utcnow().isoformat(),
                "data": data
            }
            
            await self.analytics_manager.log_event("ai_faq_builder", log_data)
            
        except Exception:
            pass
