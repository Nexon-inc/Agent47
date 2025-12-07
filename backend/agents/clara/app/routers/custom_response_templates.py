from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel
from ..services.custom_response_templates_service import CustomResponseTemplatesService
from ..models import SupportChannel, TicketPriority, TicketStatus, TicketCategory

router = APIRouter()

# Pydantic models for request/response
class CreateTemplateRequest(BaseModel):
    name: str
    category: str
    template_content: str
    variables: List[str]
    is_active: bool = True
    language: str = "en"
    brand_id: Optional[int] = None

class UpdateTemplateRequest(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    template_content: Optional[str] = None
    variables: Optional[List[str]] = None
    is_active: Optional[bool] = None
    language: Optional[str] = None

class RenderTemplateRequest(BaseModel):
    context: Dict[str, Any]
    customer_id: Optional[int] = None
    ticket_id: Optional[int] = None
    agent_id: Optional[int] = None

async def get_templates_service() -> CustomResponseTemplatesService:
    """Dependency to get custom response templates service"""
    service = CustomResponseTemplatesService()
    await service.initialize()
    return service

@router.post("/templates", response_model=Dict[str, Any])
async def create_template(
    request: CreateTemplateRequest,
    created_by: Optional[int] = Query(None),
    templates_service: CustomResponseTemplatesService = Depends(get_templates_service)
):
    """Create a new custom response template"""
    try:
        result = await templates_service.create_template(
            name=request.name,
            category=request.category,
            template_content=request.template_content,
            variables=request.variables,
            is_active=request.is_active,
            language=request.language,
            brand_id=request.brand_id,
            created_by=created_by
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/templates/{template_id}", response_model=Dict[str, Any])
async def get_template(
    template_id: int,
    include_inactive: bool = Query(False),
    templates_service: CustomResponseTemplatesService = Depends(get_templates_service)
):
    """Get a specific template by ID"""
    try:
        result = await templates_service.get_template(
            template_id=template_id,
            include_inactive=include_inactive
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/templates", response_model=Dict[str, Any])
async def search_templates(
    category: Optional[str] = Query(None),
    language: Optional[str] = Query(None),
    brand_id: Optional[int] = Query(None),
    is_active: Optional[bool] = Query(None),
    search_term: Optional[str] = Query(None),
    templates_service: CustomResponseTemplatesService = Depends(get_templates_service)
):
    """Search templates with filters"""
    try:
        result = await templates_service.search_templates(
            category=category,
            language=language,
            brand_id=brand_id,
            is_active=is_active,
            search_term=search_term
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/templates/{template_id}", response_model=Dict[str, Any])
async def update_template(
    template_id: int,
    request: UpdateTemplateRequest,
    templates_service: CustomResponseTemplatesService = Depends(get_templates_service)
):
    """Update an existing template"""
    try:
        updates = request.dict(exclude_unset=True)
        
        result = await templates_service.update_template(
            template_id=template_id,
            updates=updates
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/templates/{template_id}", response_model=Dict[str, Any])
async def delete_template(
    template_id: int,
    templates_service: CustomResponseTemplatesService = Depends(get_templates_service)
):
    """Delete a template"""
    try:
        result = await templates_service.delete_template(template_id=template_id)
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/templates/{template_id}/render", response_model=Dict[str, Any])
async def render_template(
    template_id: int,
    request: RenderTemplateRequest,
    templates_service: CustomResponseTemplatesService = Depends(get_templates_service)
):
    """Render a template with provided context"""
    try:
        result = await templates_service.render_template(
            template_id=template_id,
            context=request.context,
            customer_id=request.customer_id,
            ticket_id=request.ticket_id,
            agent_id=request.agent_id
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/categories", response_model=Dict[str, Any])
async def get_template_categories(
    templates_service: CustomResponseTemplatesService = Depends(get_templates_service)
):
    """Get all available template categories"""
    try:
        result = await templates_service.get_template_categories()
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/variables", response_model=Dict[str, Any])
async def get_template_variables(
    templates_service: CustomResponseTemplatesService = Depends(get_templates_service)
):
    """Get all available template variables"""
    try:
        result = await templates_service.get_template_variables()
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health", response_model=Dict[str, Any])
async def check_templates_health(
    templates_service: CustomResponseTemplatesService = Depends(get_templates_service)
):
    """Check health status of templates service"""
    try:
        return {
            "success": True,
            "service": "custom_response_templates",
            "status": "healthy",
            "templates_count": len(templates_service._template_cache),
            "variables_count": sum(len(vars) for vars in templates_service._template_variables.values()),
            "message": "Custom response templates service is operational"
        }
    except Exception as e:
        return {
            "success": False,
            "service": "custom_response_templates",
            "status": "error",
            "error": str(e)
        }
