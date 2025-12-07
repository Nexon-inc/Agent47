from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from ..database import get_clara_database
from ..models import KnowledgeBase
from sqlalchemy import select, and_, or_, func

router = APIRouter()

# Pydantic models for request/response
class CreateKnowledgeItemRequest(BaseModel):
    category: str
    subcategory: Optional[str] = None
    title: str
    question: str
    answer: str
    tags: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    is_public: bool = True
    language: str = "en"

class UpdateKnowledgeItemRequest(BaseModel):
    category: Optional[str] = None
    subcategory: Optional[str] = None
    title: Optional[str] = None
    question: Optional[str] = None
    answer: Optional[str] = None
    tags: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    is_public: Optional[bool] = None
    language: Optional[str] = None

class SearchKnowledgeRequest(BaseModel):
    query: str
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    language: str = "en"
    limit: int = 10

@router.post("/items", response_model=Dict[str, Any])
async def create_knowledge_item(
    request: CreateKnowledgeItemRequest,
    created_by: int = Query(..., description="ID of the user creating the item")
):
    """Create a new knowledge base item"""
    try:
        db = await get_clara_database()
        async with db.get_session() as session:
            # Create knowledge base item
            kb_item = KnowledgeBase(
                category=request.category,
                subcategory=request.subcategory,
                title=request.title,
                question=request.question,
                answer=request.answer,
                tags=request.tags or [],
                keywords=request.keywords or [],
                is_public=request.is_public,
                language=request.language,
                created_by=created_by
            )
            
            session.add(kb_item)
            await session.commit()
            
            return {
                "success": True,
                "knowledge_item": {
                    "id": kb_item.id,
                    "category": kb_item.category,
                    "title": kb_item.title,
                    "created_at": kb_item.created_at.isoformat() if kb_item.created_at else None
                }
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/items/{item_id}", response_model=Dict[str, Any])
async def get_knowledge_item(item_id: int):
    """Get a specific knowledge base item"""
    try:
        db = await get_clara_database()
        async with db.get_session() as session:
            kb_item = await session.execute(
                select(KnowledgeBase).where(KnowledgeBase.id == item_id)
            )
            kb_item = kb_item.scalar_one_or_none()
            
            if not kb_item:
                raise HTTPException(status_code=404, detail="Knowledge base item not found")
            
            return {
                "success": True,
                "knowledge_item": {
                    "id": kb_item.id,
                    "category": kb_item.category,
                    "subcategory": kb_item.subcategory,
                    "title": kb_item.title,
                    "question": kb_item.question,
                    "answer": kb_item.answer,
                    "tags": kb_item.tags,
                    "keywords": kb_item.keywords,
                    "usage_count": kb_item.usage_count,
                    "success_rate": kb_item.success_rate,
                    "helpful_count": kb_item.helpful_count,
                    "not_helpful_count": kb_item.not_helpful_count,
                    "is_public": kb_item.is_public,
                    "language": kb_item.language,
                    "created_at": kb_item.created_at.isoformat() if kb_item.created_at else None,
                    "last_updated": kb_item.last_updated.isoformat() if kb_item.last_updated else None
                }
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/items/{item_id}", response_model=Dict[str, Any])
async def update_knowledge_item(
    item_id: int,
    request: UpdateKnowledgeItemRequest
):
    """Update a knowledge base item"""
    try:
        db = await get_clara_database()
        async with db.get_session() as session:
            kb_item = await session.execute(
                select(KnowledgeBase).where(KnowledgeBase.id == item_id)
            )
            kb_item = kb_item.scalar_one_or_none()
            
            if not kb_item:
                raise HTTPException(status_code=404, detail="Knowledge base item not found")
            
            # Update fields
            if request.category is not None:
                kb_item.category = request.category
            if request.subcategory is not None:
                kb_item.subcategory = request.subcategory
            if request.title is not None:
                kb_item.title = request.title
            if request.question is not None:
                kb_item.question = request.question
            if request.answer is not None:
                kb_item.answer = request.answer
            if request.tags is not None:
                kb_item.tags = request.tags
            if request.keywords is not None:
                kb_item.keywords = request.keywords
            if request.is_public is not None:
                kb_item.is_public = request.is_public
            if request.language is not None:
                kb_item.language = request.language
            
            await session.commit()
            
            return {
                "success": True,
                "message": "Knowledge base item updated successfully",
                "item_id": item_id
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/items/{item_id}", response_model=Dict[str, Any])
async def delete_knowledge_item(item_id: int):
    """Delete a knowledge base item"""
    try:
        db = await get_clara_database()
        async with db.get_session() as session:
            kb_item = await session.execute(
                select(KnowledgeBase).where(KnowledgeBase.id == item_id)
            )
            kb_item = kb_item.scalar_one_or_none()
            
            if not kb_item:
                raise HTTPException(status_code=404, detail="Knowledge base item not found")
            
            await session.delete(kb_item)
            await session.commit()
            
            return {
                "success": True,
                "message": "Knowledge base item deleted successfully",
                "item_id": item_id
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search", response_model=Dict[str, Any])
async def search_knowledge_base(request: SearchKnowledgeRequest):
    """Search knowledge base"""
    try:
        db = await get_clara_database()
        async with db.get_session() as session:
            
            # Build search query
            query = select(KnowledgeBase).where(
                and_(
                    KnowledgeBase.is_public == True,
                    KnowledgeBase.language == request.language
                )
            )
            
            # Add category filter
            if request.category:
                query = query.where(KnowledgeBase.category == request.category)
            
            # Add tags filter
            if request.tags:
                tag_conditions = [KnowledgeBase.tags.contains([tag]) for tag in request.tags]
                query = query.where(or_(*tag_conditions))
            
            # Add text search
            if request.query:
                search_terms = request.query.lower().split()
                text_conditions = []
                for term in search_terms:
                    text_conditions.extend([
                        KnowledgeBase.title.ilike(f"%{term}%"),
                        KnowledgeBase.question.ilike(f"%{term}%"),
                        KnowledgeBase.answer.ilike(f"%{term}%")
                    ])
                query = query.where(or_(*text_conditions))
            
            # Order by relevance and usage
            query = query.order_by(
                KnowledgeBase.success_rate.desc(),
                KnowledgeBase.usage_count.desc()
            ).limit(request.limit)
            
            results = await session.execute(query)
            results = results.scalars().all()
            
            return {
                "success": True,
                "results": [
                    {
                        "id": item.id,
                        "category": item.category,
                        "subcategory": item.subcategory,
                        "title": item.title,
                        "question": item.question,
                        "answer": item.answer,
                        "tags": item.tags,
                        "usage_count": item.usage_count,
                        "success_rate": item.success_rate
                    }
                    for item in results
                ],
                "total_results": len(results),
                "query": request.query
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/categories", response_model=Dict[str, Any])
async def get_knowledge_categories():
    """Get all knowledge base categories"""
    try:
        db = await get_clara_database()
        async with db.get_session() as session:
            
            # Get unique categories
            categories = await session.execute(
                select(KnowledgeBase.category, func.count(KnowledgeBase.id).label("count"))
                .where(KnowledgeBase.is_public == True)
                .group_by(KnowledgeBase.category)
                .order_by(KnowledgeBase.category)
            )
            categories = categories.all()
            
            return {
                "success": True,
                "categories": [
                    {
                        "name": cat.category,
                        "item_count": cat.count
                    }
                    for cat in categories
                ]
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tags", response_model=Dict[str, Any])
async def get_knowledge_tags():
    """Get all knowledge base tags"""
    try:
        db = await get_clara_database()
        async with db.get_session() as session:
            
            # Get all tags and their counts
            all_tags = []
            items = await session.execute(select(KnowledgeBase.tags))
            items = items.scalars().all()
            
            tag_counts = {}
            for item in items:
                if item.tags:
                    for tag in item.tags:
                        tag_counts[tag] = tag_counts.get(tag, 0) + 1
            
            # Sort by count
            sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
            
            return {
                "success": True,
                "tags": [
                    {
                        "name": tag,
                        "count": count
                    }
                    for tag, count in sorted_tags
                ]
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/items/{item_id}/feedback", response_model=Dict[str, Any])
async def submit_knowledge_feedback(
    item_id: int,
    helpful: bool = Body(...),
    feedback_text: Optional[str] = Body(None)
):
    """Submit feedback for a knowledge base item"""
    try:
        db = await get_clara_database()
        async with db.get_session() as session:
            kb_item = await session.execute(
                select(KnowledgeBase).where(KnowledgeBase.id == item_id)
            )
            kb_item = kb_item.scalar_one_or_none()
            
            if not kb_item:
                raise HTTPException(status_code=404, detail="Knowledge base item not found")
            
            # Update feedback counts
            if helpful:
                kb_item.helpful_count += 1
            else:
                kb_item.not_helpful_count += 1
            
            # Update success rate
            total_feedback = kb_item.helpful_count + kb_item.not_helpful_count
            if total_feedback > 0:
                kb_item.success_rate = kb_item.helpful_count / total_feedback
            
            await session.commit()
            
            return {
                "success": True,
                "message": "Feedback submitted successfully",
                "item_id": item_id,
                "helpful": helpful
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/summary", response_model=Dict[str, Any])
async def get_knowledge_stats():
    """Get knowledge base statistics"""
    try:
        db = await get_clara_database()
        async with db.get_session() as session:
            
            # Get total items
            total_items = await session.execute(select(func.count(KnowledgeBase.id)))
            total_items = total_items.scalar()
            
            # Get public items
            public_items = await session.execute(
                select(func.count(KnowledgeBase.id)).where(KnowledgeBase.is_public == True)
            )
            public_items = public_items.scalar()
            
            # Get average success rate
            avg_success_rate = await session.execute(
                select(func.avg(KnowledgeBase.success_rate))
                .where(KnowledgeBase.is_public == True)
            )
            avg_success_rate = avg_success_rate.scalar() or 0
            
            # Get total usage
            total_usage = await session.execute(
                select(func.sum(KnowledgeBase.usage_count))
                .where(KnowledgeBase.is_public == True)
            )
            total_usage = total_usage.scalar() or 0
            
            return {
                "success": True,
                "stats": {
                    "total_items": total_items,
                    "public_items": public_items,
                    "private_items": total_items - public_items,
                    "average_success_rate": round(avg_success_rate, 2),
                    "total_usage": total_usage,
                    "average_usage_per_item": round(total_usage / public_items, 2) if public_items > 0 else 0
                }
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
