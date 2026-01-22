import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, or_, desc
from sqlalchemy.orm import selectinload
from core.ai import get_ai_service_manager, AIServiceManager
from ..database import get_clara_database
from ..models import (
    ClaraKnowledgeBase, ClaraSupportTicket, CustomerProfile, ClaraSupportTicket,
    TicketCategory, TicketPriority, SupportChannel
)

logger = logging.getLogger(__name__)

class SelfServicePortalService:
    def __init__(self):
        self.ai_service_manager: Optional[AIServiceManager] = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize self-service portal service"""
        if self._initialized:
            return
        
        try:
            self.ai_service_manager = await get_ai_service_manager()
            self._initialized = True
            logger.info("Self-service portal service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize self-service portal service: {e}")
            raise
    
    async def get_customer_portal_data(
        self,
        customer_id: int,
        include_tickets: bool = True,
        include_knowledge: bool = True,
        include_profile: bool = True
    ) -> Dict[str, Any]:
        """Get comprehensive customer portal data"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_clara_database()
            async with db.get_session() as session:
                portal_data = {}
                
                # Get customer profile
                if include_profile:
                    profile = await session.execute(
                        select(CustomerProfile).where(CustomerProfile.user_id == customer_id)
                    )
                    profile = profile.scalar_one_or_none()
                    
                    if profile:
                        portal_data["profile"] = {
                            "support_tier": profile.support_tier,
                            "preferred_channel": profile.preferred_channel.value if profile.preferred_channel else "chat",
                            "language_preference": profile.language_preference,
                            "timezone": profile.timezone,
                            "loyalty_level": profile.loyalty_level,
                            "total_support_tickets": profile.total_support_tickets,
                            "resolved_tickets": profile.resolved_tickets,
                            "average_satisfaction": profile.average_satisfaction,
                            "trust_score": profile.trust_score
                        }
                
                # Get customer tickets
                if include_tickets:
                    tickets = await session.execute(
                        select(ClaraSupportTicket).where(
                            ClaraSupportTicket.customer_id == customer_id
                        ).order_by(ClaraSupportTicket.created_at.desc()).limit(10)
                    )
                    tickets = tickets.scalars().all()
                    
                    portal_data["recent_tickets"] = []
                    for ticket in tickets:
                        portal_data["recent_tickets"].append({
                            "id": ticket.id,
                            "ticket_number": ticket.ticket_number,
                            "subject": ticket.subject,
                            "status": ticket.status.value,
                            "priority": ticket.priority.value,
                            "category": ticket.category.value,
                            "created_at": ticket.created_at.isoformat(),
                            "resolved_at": ticket.resolved_at.isoformat() if ticket.resolved_at else None,
                            "satisfaction_score": ticket.satisfaction_score
                        })
                    
                    # Get ticket statistics
                    total_tickets = await session.execute(
                        select(func.count(ClaraSupportTicket.id)).where(
                            ClaraSupportTicket.customer_id == customer_id
                        )
                    )
                    total_tickets = total_tickets.scalar() or 0
                    
                    open_tickets = await session.execute(
                        select(func.count(ClaraSupportTicket.id)).where(
                            and_(
                                ClaraSupportTicket.customer_id == customer_id,
                                ClaraSupportTicket.status.in_(["open", "in_progress", "waiting_customer"])
                            )
                        )
                    )
                    open_tickets = open_tickets.scalar() or 0
                    
                    resolved_tickets = await session.execute(
                        select(func.count(ClaraSupportTicket.id)).where(
                            and_(
                                ClaraSupportTicket.customer_id == customer_id,
                                ClaraSupportTicket.status == "resolved"
                            )
                        )
                    )
                    resolved_tickets = resolved_tickets.scalar() or 0
                    
                    portal_data["ticket_statistics"] = {
                        "total_tickets": total_tickets,
                        "open_tickets": open_tickets,
                        "resolved_tickets": resolved_tickets,
                        "resolution_rate": round((resolved_tickets / max(total_tickets, 1)) * 100, 1)
                    }
                
                # Get relevant knowledge base items
                if include_knowledge:
                    # Get knowledge items based on customer's ticket history
                    customer_categories = await session.execute(
                        select(ClaraSupportTicket.category).where(
                            ClaraSupportTicket.customer_id == customer_id
                        ).distinct()
                    )
                    customer_categories = customer_categories.scalars().all()
                    
                    if customer_categories:
                        category_values = [cat.value for cat in customer_categories]
                        knowledge_items = await session.execute(
                            select(ClaraKnowledgeBase).where(
                                and_(
                                    ClaraKnowledgeBase.is_public == True,
                                    or_(
                                        ClaraKnowledgeBase.category.in_(category_values),
                                        ClaraKnowledgeBase.tags.overlap(category_values)
                                    )
                                )
                            ).order_by(ClaraKnowledgeBase.success_rate.desc(), ClaraKnowledgeBase.usage_count.desc()).limit(15)
                        )
                        knowledge_items = knowledge_items.scalars().all()
                        
                        portal_data["recommended_knowledge"] = []
                        for item in knowledge_items:
                            portal_data["recommended_knowledge"].append({
                                "id": item.id,
                                "title": item.title,
                                "category": item.category,
                                "subcategory": item.subcategory,
                                "tags": item.tags,
                                "success_rate": item.success_rate,
                                "usage_count": item.usage_count
                            })
                    
                    # Get popular knowledge items
                    popular_items = await session.execute(
                        select(ClaraKnowledgeBase).where(
                            ClaraKnowledgeBase.is_public == True
                        ).order_by(ClaraKnowledgeBase.usage_count.desc(), ClaraKnowledgeBase.success_rate.desc()).limit(10)
                    )
                    popular_items = popular_items.scalars().all()
                    
                    portal_data["popular_knowledge"] = []
                    for item in popular_items:
                        portal_data["popular_knowledge"].append({
                            "id": item.id,
                            "title": item.title,
                            "category": item.category,
                            "subcategory": item.subcategory,
                            "tags": item.tags,
                            "success_rate": item.success_rate,
                            "usage_count": item.usage_count
                        })
                
                return {
                    "success": True,
                    "customer_id": customer_id,
                    "portal_data": portal_data,
                    "last_updated": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to get customer portal data: {e}")
            return {"success": False, "error": str(e)}
    
    async def search_knowledge_for_customer(
        self,
        customer_id: int,
        query: str,
        category: Optional[str] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """Search knowledge base with customer context"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_clara_database()
            async with db.get_session() as session:
                # Get customer's ticket history for context
                customer_tickets = await session.execute(
                    select(ClaraSupportTicket.category, ClaraSupportTicket.tags).where(
                        ClaraSupportTicket.customer_id == customer_id
                    )
                )
                customer_tickets = customer_tickets.all()
                
                # Build search query
                search_query = select(ClaraKnowledgeBase).where(ClaraKnowledgeBase.is_public == True)
                
                # Add category filter if specified
                if category:
                    search_query = search_query.where(ClaraKnowledgeBase.category == category)
                
                # Add text search
                search_terms = query.lower().split()
                search_conditions = []
                for term in search_terms:
                    search_conditions.append(
                        or_(
                            ClaraKnowledgeBase.title.ilike(f"%{term}%"),
                            ClaraKnowledgeBase.question.ilike(f"%{term}%"),
                            ClaraKnowledgeBase.answer.ilike(f"%{term}%"),
                            ClaraKnowledgeBase.tags.contains([term])
                        )
                    )
                
                if search_conditions:
                    search_query = search_query.where(or_(*search_conditions))
                
                # Order by relevance (customer context + general popularity)
                search_query = search_query.order_by(
                    ClaraKnowledgeBase.success_rate.desc(),
                    ClaraKnowledgeBase.usage_count.desc()
                ).limit(limit)
                
                results = await session.execute(search_query)
                results = results.scalars().all()
                
                # Score results based on customer context
                scored_results = []
                for item in results:
                    score = 0.0
                    
                    # Base score from success rate and usage
                    score += (item.success_rate or 0) * 0.4
                    score += min((item.usage_count or 0) / 100, 1.0) * 0.3
                    
                    # Context relevance score
                    if customer_tickets:
                        # Check if item category matches customer's ticket categories
                        customer_categories = [ticket.category.value for ticket in customer_tickets]
                        if item.category in customer_categories:
                            score += 0.3
                        
                        # Check if item tags match customer's ticket tags
                        customer_tags = []
                        for ticket in customer_tickets:
                            if ticket.tags:
                                customer_tags.extend(ticket.tags)
                        
                        if customer_tags and item.tags:
                            tag_matches = len(set(customer_tags) & set(item.tags))
                            score += min(tag_matches * 0.1, 0.2)
                    
                    scored_results.append({
                        "item": item,
                        "relevance_score": round(score, 3)
                    })
                
                # Sort by relevance score
                scored_results.sort(key=lambda x: x["relevance_score"], reverse=True)
                
                # Format results
                search_results = []
                for result in scored_results:
                    item = result["item"]
                    search_results.append({
                        "id": item.id,
                        "title": item.title,
                        "question": item.question,
                        "answer": item.answer[:200] + "..." if len(item.answer) > 200 else item.answer,
                        "category": item.category,
                        "subcategory": item.subcategory,
                        "tags": item.tags,
                        "relevance_score": result["relevance_score"],
                        "success_rate": item.success_rate,
                        "usage_count": item.usage_count
                    })
                
                return {
                    "success": True,
                    "query": query,
                    "customer_id": customer_id,
                    "results": search_results,
                    "total_results": len(search_results),
                    "search_context": {
                        "customer_categories": list(set([ticket.category.value for ticket in customer_tickets])),
                        "customer_tags": list(set([tag for ticket in customer_tickets if ticket.tags for tag in ticket.tags]))
                    }
                }
                
        except Exception as e:
            logger.error(f"Failed to search knowledge for customer: {e}")
            return {"success": False, "error": str(e)}
    
    async def create_self_service_ticket(
        self,
        customer_id: int,
        subject: str,
        description: str,
        category: TicketCategory,
        priority: Optional[TicketPriority] = None,
        tags: Optional[List[str]] = None,
        source_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a ticket through self-service portal"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_clara_database()
            async with db.get_session() as session:
                # Auto-assign priority if not specified
                if not priority:
                    priority = await self._auto_assign_priority(description, category)
                
                # Create ticket
                from ..services.support_service import SupportService
                support_service = SupportService()
                await support_service.initialize()
                
                ticket_result = await support_service.create_ticket(
                    customer_id=customer_id,
                    channel=SupportChannel.WEB_FORM,
                    category=category,
                    subject=subject,
                    description=description,
                    priority=priority,
                    tags=tags or [],
                    source_url=source_url,
                    metadata={"created_via": "self_service_portal"}
                )
                
                if ticket_result["success"]:
                    # Update customer profile
                    await self._update_customer_self_service_usage(customer_id, session)
                    
                    return {
                        "success": True,
                        "ticket": ticket_result["ticket"],
                        "message": "Ticket created successfully through self-service portal",
                        "estimated_response_time": "Within 2 hours during business hours",
                        "next_steps": [
                            "You will receive a confirmation email",
                            "Our team will review your request",
                            "You can track progress in your portal"
                        ]
                    }
                else:
                    return ticket_result
                
        except Exception as e:
            logger.error(f"Failed to create self-service ticket: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_faq_categories(self) -> Dict[str, Any]:
        """Get ClaraFAQ categories and popular questions"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_clara_database()
            async with db.get_session() as session:
                # Get all categories with knowledge items
                categories = await session.execute(
                    select(ClaraKnowledgeBase.category, func.count(ClaraKnowledgeBase.id).label("count"))
                    .where(ClaraKnowledgeBase.is_public == True)
                    .group_by(ClaraKnowledgeBase.category)
                    .order_by(desc("count"))
                )
                categories = categories.all()
                
                # Get popular questions for each category
                faq_data = []
                for category_row in categories:
                    category = category_row.category
                    count = category_row.count
                    
                    # Get top questions for this category
                    questions = await session.execute(
                        select(ClaraKnowledgeBase).where(
                            and_(
                                ClaraKnowledgeBase.category == category,
                                ClaraKnowledgeBase.is_public == True
                            )
                        ).order_by(ClaraKnowledgeBase.usage_count.desc(), ClaraKnowledgeBase.success_rate.desc()).limit(5)
                    )
                    questions = questions.scalars().all()
                    
                    category_questions = []
                    for question in questions:
                        category_questions.append({
                            "id": question.id,
                            "title": question.title,
                            "question": question.question,
                            "answer_preview": question.answer[:150] + "..." if len(question.answer) > 150 else question.answer,
                            "usage_count": question.usage_count,
                            "success_rate": question.success_rate
                        })
                    
                    faq_data.append({
                        "category": category,
                        "question_count": count,
                        "popular_questions": category_questions
                    })
                
                return {
                    "success": True,
                    "faq_categories": faq_data,
                    "total_categories": len(faq_data),
                    "total_questions": sum(cat["question_count"] for cat in faq_data)
                }
                
        except Exception as e:
            logger.error(f"Failed to get ClaraFAQ categories: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_customer_support_resources(
        self,
        customer_id: int,
        resource_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get personalized support resources for customer"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_clara_database()
            async with db.get_session() as session:
                # Get customer profile
                profile = await session.execute(
                    select(CustomerProfile).where(CustomerProfile.user_id == customer_id)
                )
                profile = profile.scalar_one_or_none()
                
                if not profile:
                    return {"success": False, "error": "Customer profile not found"}
                
                resources = {
                    "quick_actions": [
                        {
                            "id": "create_ticket",
                            "title": "Create Support Ticket",
                            "description": "Submit a new support request",
                            "icon": "📝",
                            "action": "create_ticket",
                            "url": "/portal/tickets/create"
                        },
                        {
                            "id": "view_tickets",
                            "title": "My Tickets",
                            "description": "View and track your support tickets",
                            "icon": "🎫",
                            "action": "view_tickets",
                            "url": "/portal/tickets"
                        },
                        {
                            "id": "knowledge_base",
                            "title": "Knowledge Base",
                            "description": "Search for answers and guides",
                            "icon": "📚",
                            "action": "search_knowledge",
                            "url": "/portal/knowledge"
                        },
                        {
                            "id": "contact_support",
                            "title": "Contact Support",
                            "description": "Get in touch with our team",
                            "icon": "💬",
                            "action": "contact_support",
                            "url": "/portal/contact"
                        }
                    ],
                    "helpful_links": [
                        {
                            "title": "Getting Started Guide",
                            "url": "/portal/guides/getting-started",
                            "description": "Learn how to use our services"
                        },
                        {
                            "title": "Common Issues",
                            "url": "/portal/guides/common-issues",
                            "description": "Solutions to frequent problems"
                        },
                        {
                            "title": "Video Tutorials",
                            "url": "/portal/tutorials",
                            "description": "Step-by-step video guides"
                        },
                        {
                            "title": "Community Forum",
                            "url": "/portal/community",
                            "description": "Connect with other users"
                        }
                    ]
                }
                
                # Add personalized resources based on customer profile
                if profile.support_tier == "premium":
                    resources["premium_features"] = [
                        {
                            "title": "Priority Support",
                            "description": "Faster response times for premium customers",
                            "icon": "⭐"
                        },
                        {
                            "title": "Dedicated Support Agent",
                            "description": "Personal support representative",
                            "icon": "👤"
                        },
                        {
                            "title": "Advanced Analytics",
                            "description": "Detailed support history and insights",
                            "icon": "📊"
                        }
                    ]
                
                # Add resources based on customer's ticket history
                recent_tickets = await session.execute(
                    select(ClaraSupportTicket.category).where(
                        ClaraSupportTicket.customer_id == customer_id
                    ).order_by(ClaraSupportTicket.created_at.desc()).limit(5)
                )
                recent_tickets = recent_tickets.scalars().all()
                
                if recent_tickets:
                    common_categories = [ticket.value for ticket in recent_tickets]
                    resources["personalized_guides"] = [
                        {
                            "title": f"{category.title()} Troubleshooting",
                            "url": f"/portal/guides/{category.lower()}",
                            "description": f"Common solutions for {category.lower()} issues"
                        }
                        for category in set(common_categories)
                    ]
                
                return {
                    "success": True,
                    "customer_id": customer_id,
                    "resources": resources,
                    "last_updated": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to get customer support resources: {e}")
            return {"success": False, "error": str(e)}
    
    async def _auto_assign_priority(
        self,
        description: str,
        category: TicketCategory
    ) -> TicketPriority:
        """Auto-assign priority based on description and category"""
        try:
            # Use NLP to analyze urgency
            urgency_prompt = f"""Analyze this support request and determine urgency level (1-5, where 5 is most urgent):

Description: {description}
Category: {category.value}

Consider:
- Security issues are always high priority
- Billing issues affecting service are high priority
- Technical issues preventing work are medium-high priority
- General questions are low-medium priority

Respond with just a number 1-5:"""
            
            # Use AI Service Manager instead of NLPUtils
            from core.ai import get_ai_service_manager
            ai_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that analyzes urgency. Respond with only a number 1-5."},
                {"role": "user", "content": urgency_prompt}
            ]
            ai_response = await ai_manager.generate_text(messages=messages, max_tokens=10, temperature=0.3)
            if ai_response.success:
                try:
                    urgency_level = int(ai_response.text_content.strip())
                    if urgency_level >= 5:
                        return TicketPriority.CRITICAL
                    elif urgency_level >= 4:
                        return TicketPriority.HIGH
                    elif urgency_level >= 3:
                        return TicketPriority.MEDIUM
                    else:
                        return TicketPriority.LOW
                except (ValueError, AttributeError):
                    pass
            
            # Fallback priority assignment
            if category in [TicketCategory.SECURITY, TicketCategory.BUG_REPORT]:
                return TicketPriority.HIGH
            elif category in [TicketCategory.BILLING, TicketCategory.ACCOUNT_ISSUE]:
                return TicketPriority.MEDIUM
            else:
                return TicketPriority.LOW
                
        except Exception as e:
            logger.error(f"Failed to auto-assign priority: {e}")
            return TicketPriority.MEDIUM
    
    async def _update_customer_self_service_usage(
        self,
        customer_id: int,
        session: AsyncSession
    ):
        """Update customer profile with self-service usage"""
        try:
            profile = await session.execute(
                select(CustomerProfile).where(CustomerProfile.user_id == customer_id)
            )
            profile = profile.scalar_one_or_none()
            
            if profile:
                # Update self-service usage metrics
                if not hasattr(profile, 'self_service_usage_count'):
                    # This would need to be added to the model
                    pass
                else:
                    profile.self_service_usage_count += 1
                    profile.last_self_service_usage = datetime.utcnow()
                
                session.add(profile)
                
        except Exception as e:
            logger.error(f"Failed to update customer self-service usage: {e}")
            # Don't fail the main operation for this
            pass
