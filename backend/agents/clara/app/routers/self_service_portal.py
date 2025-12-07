from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from ..services.self_service_portal_service import SelfServicePortalService
from ..models import TicketCategory, TicketPriority

router = APIRouter()

# Pydantic models for request/response
class CustomerPortalRequest(BaseModel):
    customer_id: int
    include_tickets: bool = True
    include_knowledge: bool = True
    include_profile: bool = True

class KnowledgeSearchRequest(BaseModel):
    customer_id: int
    query: str
    category: Optional[str] = None
    limit: int = 10

class SelfServiceTicketRequest(BaseModel):
    customer_id: int
    subject: str
    description: str
    category: str
    priority: Optional[str] = None
    tags: Optional[List[str]] = None
    source_url: Optional[str] = None

class SupportResourcesRequest(BaseModel):
    customer_id: int
    resource_type: Optional[str] = None

# Dependency
async def get_self_service_portal_service() -> SelfServicePortalService:
    service = SelfServicePortalService()
    await service.initialize()
    return service

@router.post("/customer/portal-data", response_model=Dict[str, Any])
async def get_customer_portal_data(
    request: CustomerPortalRequest,
    service: SelfServicePortalService = Depends(get_self_service_portal_service)
):
    """Get comprehensive customer portal data"""
    try:
        result = await service.get_customer_portal_data(
            customer_id=request.customer_id,
            include_tickets=request.include_tickets,
            include_knowledge=request.include_knowledge,
            include_profile=request.include_profile
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/knowledge/search", response_model=Dict[str, Any])
async def search_knowledge_for_customer(
    request: KnowledgeSearchRequest,
    service: SelfServicePortalService = Depends(get_self_service_portal_service)
):
    """Search knowledge base with customer context"""
    try:
        result = await service.search_knowledge_for_customer(
            customer_id=request.customer_id,
            query=request.query,
            category=request.category,
            limit=request.limit
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tickets/create", response_model=Dict[str, Any])
async def create_self_service_ticket(
    request: SelfServiceTicketRequest,
    service: SelfServicePortalService = Depends(get_self_service_portal_service)
):
    """Create a ticket through self-service portal"""
    try:
        result = await service.create_self_service_ticket(
            customer_id=request.customer_id,
            subject=request.subject,
            description=request.description,
            category=TicketCategory(request.category),
            priority=TicketPriority(request.priority) if request.priority else None,
            tags=request.tags,
            source_url=request.source_url
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/resources/support", response_model=Dict[str, Any])
async def get_customer_support_resources(
    request: SupportResourcesRequest,
    service: SelfServicePortalService = Depends(get_self_service_portal_service)
):
    """Get personalized support resources for customer"""
    try:
        result = await service.get_customer_support_resources(
            customer_id=request.customer_id,
            resource_type=request.resource_type
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/faq/categories", response_model=Dict[str, Any])
async def get_faq_categories(
    service: SelfServicePortalService = Depends(get_self_service_portal_service)
):
    """Get FAQ categories and popular questions"""
    try:
        result = await service.get_faq_categories()
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/portal/overview", response_model=Dict[str, Any])
async def get_portal_overview(
    service: SelfServicePortalService = Depends(get_self_service_portal_service)
):
    """Get overview of self-service portal capabilities"""
    try:
        overview = {
            "success": True,
            "portal_overview": {
                "features": [
                    "Customer Portal Dashboard",
                    "Knowledge Base Search",
                    "Self-Service Ticket Creation",
                    "Personalized Support Resources",
                    "FAQ Categories",
                    "Ticket Tracking",
                    "Support History"
                ],
                "capabilities": {
                    "knowledge_search": True,
                    "ticket_creation": True,
                    "profile_management": True,
                    "resource_access": True,
                    "offline_support": True
                },
                "supported_channels": [
                    "web_portal",
                    "mobile_app",
                    "email",
                    "chat_widget"
                ]
            },
            "last_updated": "2024-01-01T00:00:00Z"
        }
        
        return overview
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/usage", response_model=Dict[str, Any])
async def get_portal_usage_statistics(
    service: SelfServicePortalService = Depends(get_self_service_portal_service)
):
    """Get self-service portal usage statistics"""
    try:
        # Get portal usage statistics from the service
        stats = await service.get_portal_usage_statistics()
        
        return {
            "success": True,
            "portal_usage_statistics": stats
        }
        
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
