from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from fastapi import HTTPException, BackgroundTasks
import json
import asyncio
from enum import Enum

from ..models import KnowledgeBase, SupportTicket, CustomerInteraction
from ..database import get_clara_database
from core.config import settings
from core.integrations import IntegrationManager
from core.analytics import AnalyticsManager
from core.utils.nlp_utils import NLPUtils


class KnowledgeService:
    def __init__(self):
        self.integration_manager = IntegrationManager()
        self.analytics_manager = AnalyticsManager()
        # NLPUtils kept for specialized semantic_search_knowledge_base only
        from core.utils.nlp_utils import NLPUtils
        self.nlp_utils = NLPUtils()
        
    async def search_knowledge_base(
        self, 
        db: Session, 
        query: str,
        category: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search knowledge base for relevant articles"""
        try:
            # Use semantic search to find relevant knowledge base entries
            results = await self.nlp_utils.semantic_search_knowledge_base(db, query, limit)
            
            # Filter by category if specified
            if category:
                results = [r for r in results if r.get('category') == category]
            
            return results
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to search knowledge base: {str(e)}")
    
    async def get_knowledge_article(
        self, 
        db: Session, 
        article_id: int
    ) -> Dict[str, Any]:
        """Get knowledge base article by ID"""
        try:
            article = db.query(KnowledgeBase).filter(KnowledgeBase.id == article_id).first()
            if not article:
                raise HTTPException(status_code=404, detail="Knowledge base article not found")
            
            return {
                "id": article.id,
                "title": article.title,
                "content": article.content,
                "category": article.category,
                "tags": article.tags,
                "created_at": article.created_at,
                "updated_at": article.updated_at
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get knowledge article: {str(e)}")
    
    async def create_knowledge_article(
        self, 
        db: Session, 
        title: str,
        content: str,
        category: str,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create a new knowledge base article"""
        try:
            article = KnowledgeBase(
                title=title,
                content=content,
                category=category,
                tags=tags or [],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(article)
            db.commit()
            db.refresh(article)
            
            return {
                "id": article.id,
                "title": article.title,
                "content": article.content,
                "category": article.category,
                "tags": article.tags,
                "created_at": article.created_at,
                "updated_at": article.updated_at
            }
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to create knowledge article: {str(e)}")
    
    async def update_knowledge_article(
        self, 
        db: Session, 
        article_id: int,
        title: Optional[str] = None,
        content: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Update knowledge base article"""
        try:
            article = db.query(KnowledgeBase).filter(KnowledgeBase.id == article_id).first()
            if not article:
                raise HTTPException(status_code=404, detail="Knowledge base article not found")
            
            if title is not None:
                article.title = title
            if content is not None:
                article.content = content
            if category is not None:
                article.category = category
            if tags is not None:
                article.tags = tags
            
            article.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(article)
            
            return {
                "id": article.id,
                "title": article.title,
                "content": article.content,
                "category": article.category,
                "tags": article.tags,
                "created_at": article.created_at,
                "updated_at": article.updated_at
            }
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to update knowledge article: {str(e)}")
    
    async def delete_knowledge_article(
        self, 
        db: Session, 
        article_id: int
    ) -> Dict[str, str]:
        """Delete knowledge base article"""
        try:
            article = db.query(KnowledgeBase).filter(KnowledgeBase.id == article_id).first()
            if not article:
                raise HTTPException(status_code=404, detail="Knowledge base article not found")
            
            db.delete(article)
            db.commit()
            
            return {"message": "Knowledge base article deleted successfully"}
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to delete knowledge article: {str(e)}")
    
    async def list_knowledge_articles(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List knowledge base articles"""
        try:
            query = db.query(KnowledgeBase)
            
            if category:
                query = query.filter(KnowledgeBase.category == category)
            
            articles = query.offset(skip).limit(limit).all()
            
            return [
                {
                    "id": article.id,
                    "title": article.title,
                    "content": article.content,
                    "category": article.category,
                    "tags": article.tags,
                    "created_at": article.created_at,
                    "updated_at": article.updated_at
                } for article in articles
            ]
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to list knowledge articles: {str(e)}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check the health of knowledge base system"""
        try:
            db = next(get_db())
            article_count = db.query(KnowledgeBase).count()
            
            return {
                "status": "healthy",
                "database": {
                    "connected": True,
                    "articles_count": article_count
                },
                "last_check": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "last_check": datetime.utcnow().isoformat()
            }
