from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import json

from ..database import get_db
from ..services.multi_brand_service import MultiBrandService
from ..models import Brand, BrandConfiguration, BrandTemplate
from ..core.integration_manager import IntegrationManager
from ..core.event_bus import EventBus

router = APIRouter()

# Pydantic models for request/response
class CreateBrandRequest(BaseModel):
    name: str = Field(..., description="Brand name")
    description: Optional[str] = Field(None, description="Brand description")
    logo_url: Optional[str] = Field(None, description="Brand logo URL")
    primary_color: Optional[str] = Field(None, description="Primary brand color")
    secondary_color: Optional[str] = Field(None, description="Secondary brand color")
    tone_of_voice: str = Field(..., description="Brand tone of voice (formal, casual, friendly, professional)")
    industry: Optional[str] = Field(None, description="Industry vertical")
    target_audience: Optional[str] = Field(None, description="Target audience description")
    contact_info: Optional[Dict[str, str]] = Field(None, description="Contact information")
    social_media_handles: Optional[Dict[str, str]] = Field(None, description="Social media handles")

class UpdateBrandRequest(BaseModel):
    name: Optional[str] = Field(None, description="Brand name")
    description: Optional[str] = Field(None, description="Brand description")
    logo_url: Optional[str] = Field(None, description="Brand logo URL")
    primary_color: Optional[str] = Field(None, description="Primary brand color")
    secondary_color: Optional[str] = Field(None, description="Secondary brand color")
    tone_of_voice: Optional[str] = Field(None, description="Brand tone of voice")
    industry: Optional[str] = Field(None, description="Industry vertical")
    target_audience: Optional[str] = Field(None, description="Target audience description")
    contact_info: Optional[Dict[str, str]] = Field(None, description="Contact information")
    social_media_handles: Optional[Dict[str, str]] = Field(None, description="Social media handles")
    is_active: Optional[bool] = Field(None, description="Brand active status")

class CreateConfigurationRequest(BaseModel):
    brand_id: int = Field(..., description="Brand ID")
    config_type: str = Field(..., description="Configuration type (response_templates, workflows, integrations, etc.)")
    config_data: Dict[str, Any] = Field(..., description="Configuration data")
    is_default: bool = Field(False, description="Whether this is the default configuration")
    priority: int = Field(1, description="Configuration priority")

class UpdateConfigurationRequest(BaseModel):
    config_type: Optional[str] = Field(None, description="Configuration type")
    config_data: Optional[Dict[str, Any]] = Field(None, description="Configuration data")
    is_default: Optional[bool] = Field(None, description="Whether this is the default configuration")
    priority: Optional[int] = Field(None, description="Configuration priority")

class CreateTemplateRequest(BaseModel):
    brand_id: int = Field(..., description="Brand ID")
    template_name: str = Field(..., description="Template name")
    template_type: str = Field(..., description="Template type (welcome, support, escalation, etc.)")
    content: str = Field(..., description="Template content")
    variables: List[str] = Field([], description="Template variables")
    is_active: bool = Field(True, description="Template active status")

class UpdateTemplateRequest(BaseModel):
    template_name: Optional[str] = Field(None, description="Template name")
    template_type: Optional[str] = Field(None, description="Template type")
    content: Optional[str] = Field(None, description="Template content")
    variables: Optional[List[str]] = Field(None, description="Template variables")
    is_active: Optional[bool] = Field(None, description="Template active status")

class BrandResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    logo_url: Optional[str]
    primary_color: Optional[str]
    secondary_color: Optional[str]
    tone_of_voice: str
    industry: Optional[str]
    target_audience: Optional[str]
    contact_info: Optional[Dict[str, str]]
    social_media_handles: Optional[Dict[str, str]]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ConfigurationResponse(BaseModel):
    id: int
    brand_id: int
    config_type: str
    config_data: Dict[str, Any]
    is_default: bool
    priority: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class TemplateResponse(BaseModel):
    id: int
    brand_id: int
    template_name: str
    template_type: str
    content: str
    variables: List[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class BrandContextRequest(BaseModel):
    brand_id: int = Field(..., description="Brand ID to switch to")
    customer_id: Optional[str] = Field(None, description="Customer ID for context")
    session_id: Optional[str] = Field(None, description="Session ID")

class BrandContextResponse(BaseModel):
    brand: BrandResponse
    configurations: List[ConfigurationResponse]
    templates: List[TemplateResponse]
    context_switched: bool
    message: str

class BrandAnalyticsResponse(BaseModel):
    brand_id: int
    brand_name: str
    total_tickets: int
    resolved_tickets: int
    average_response_time: float
    customer_satisfaction: float
    active_agents: int
    popular_channels: List[Dict[str, Any]]
    top_issues: List[Dict[str, Any]]

# Dependency
async def get_multi_brand_service(db: AsyncSession = Depends(get_db)) -> MultiBrandService:
    integration_manager = IntegrationManager()
    event_bus = EventBus()
    return MultiBrandService(db, integration_manager, event_bus)

# Brand Management Endpoints
@router.post("/brands", response_model=BrandResponse, status_code=status.HTTP_201_CREATED)
async def create_brand(
    request: CreateBrandRequest,
    service: MultiBrandService = Depends(get_multi_brand_service)
):
    """Create a new brand configuration"""
    try:
        brand = await service.create_brand(
            name=request.name,
            description=request.description,
            logo_url=request.logo_url,
            primary_color=request.primary_color,
            secondary_color=request.secondary_color,
            tone_of_voice=request.tone_of_voice,
            industry=request.industry,
            target_audience=request.target_audience,
            contact_info=request.contact_info,
            social_media_handles=request.social_media_handles
        )
        return BrandResponse.from_orm(brand)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/brands", response_model=List[BrandResponse])
async def get_brands(
    active_only: bool = True,
    service: MultiBrandService = Depends(get_multi_brand_service)
):
    """Get all brands with optional filtering"""
    try:
        brands = await service.get_brands(active_only=active_only)
        return [BrandResponse.from_orm(brand) for brand in brands]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/brands/{brand_id}", response_model=BrandResponse)
async def get_brand(
    brand_id: int,
    service: MultiBrandService = Depends(get_multi_brand_service)
):
    """Get a specific brand by ID"""
    try:
        brand = await service.get_brand(brand_id)
        if not brand:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand not found")
        return BrandResponse.from_orm(brand)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.put("/brands/{brand_id}", response_model=BrandResponse)
async def update_brand(
    brand_id: int,
    request: UpdateBrandRequest,
    service: MultiBrandService = Depends(get_multi_brand_service)
):
    """Update a brand configuration"""
    try:
        brand = await service.update_brand(
            brand_id=brand_id,
            name=request.name,
            description=request.description,
            logo_url=request.logo_url,
            primary_color=request.primary_color,
            secondary_color=request.secondary_color,
            tone_of_voice=request.tone_of_voice,
            industry=request.industry,
            target_audience=request.target_audience,
            contact_info=request.contact_info,
            social_media_handles=request.social_media_handles,
            is_active=request.is_active
        )
        if not brand:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand not found")
        return BrandResponse.from_orm(brand)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.delete("/brands/{brand_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_brand(
    brand_id: int,
    service: MultiBrandService = Depends(get_multi_brand_service)
):
    """Delete a brand (soft delete)"""
    try:
        success = await service.delete_brand(brand_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Configuration Management Endpoints
@router.post("/configurations", response_model=ConfigurationResponse, status_code=status.HTTP_201_CREATED)
async def create_configuration(
    request: CreateConfigurationRequest,
    service: MultiBrandService = Depends(get_multi_brand_service)
):
    """Create a new brand configuration"""
    try:
        config = await service.create_configuration(
            brand_id=request.brand_id,
            config_type=request.config_type,
            config_data=request.config_data,
            is_default=request.is_default,
            priority=request.priority
        )
        return ConfigurationResponse.from_orm(config)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/brands/{brand_id}/configurations", response_model=List[ConfigurationResponse])
async def get_brand_configurations(
    brand_id: int,
    config_type: Optional[str] = None,
    service: MultiBrandService = Depends(get_multi_brand_service)
):
    """Get configurations for a specific brand"""
    try:
        configs = await service.get_brand_configurations(brand_id, config_type=config_type)
        return [ConfigurationResponse.from_orm(config) for config in configs]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/configurations/{config_id}", response_model=ConfigurationResponse)
async def get_configuration(
    config_id: int,
    service: MultiBrandService = Depends(get_multi_brand_service)
):
    """Get a specific configuration by ID"""
    try:
        config = await service.get_configuration(config_id)
        if not config:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Configuration not found")
        return ConfigurationResponse.from_orm(config)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.put("/configurations/{config_id}", response_model=ConfigurationResponse)
async def update_configuration(
    config_id: int,
    request: UpdateConfigurationRequest,
    service: MultiBrandService = Depends(get_multi_brand_service)
):
    """Update a configuration"""
    try:
        config = await service.update_configuration(
            config_id=config_id,
            config_type=request.config_type,
            config_data=request.config_data,
            is_default=request.is_default,
            priority=request.priority
        )
        if not config:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Configuration not found")
        return ConfigurationResponse.from_orm(config)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.delete("/configurations/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_configuration(
    config_id: int,
    service: MultiBrandService = Depends(get_multi_brand_service)
):
    """Delete a configuration"""
    try:
        success = await service.delete_configuration(config_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Configuration not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Template Management Endpoints
@router.post("/templates", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    request: CreateTemplateRequest,
    service: MultiBrandService = Depends(get_multi_brand_service)
):
    """Create a new brand template"""
    try:
        template = await service.create_template(
            brand_id=request.brand_id,
            template_name=request.template_name,
            template_type=request.template_type,
            content=request.content,
            variables=request.variables,
            is_active=request.is_active
        )
        return TemplateResponse.from_orm(template)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/brands/{brand_id}/templates", response_model=List[TemplateResponse])
async def get_brand_templates(
    brand_id: int,
    template_type: Optional[str] = None,
    active_only: bool = True,
    service: MultiBrandService = Depends(get_multi_brand_service)
):
    """Get templates for a specific brand"""
    try:
        templates = await service.get_brand_templates(
            brand_id, 
            template_type=template_type, 
            active_only=active_only
        )
        return [TemplateResponse.from_orm(template) for template in templates]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/templates/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: int,
    service: MultiBrandService = Depends(get_multi_brand_service)
):
    """Get a specific template by ID"""
    try:
        template = await service.get_template(template_id)
        if not template:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
        return TemplateResponse.from_orm(template)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.put("/templates/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: int,
    request: UpdateTemplateRequest,
    service: MultiBrandService = Depends(get_multi_brand_service)
):
    """Update a template"""
    try:
        template = await service.update_template(
            template_id=template_id,
            template_name=request.template_name,
            template_type=request.template_type,
            content=request.content,
            variables=request.variables,
            is_active=request.is_active
        )
        if not template:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
        return TemplateResponse.from_orm(template)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.delete("/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: int,
    service: MultiBrandService = Depends(get_multi_brand_service)
):
    """Delete a template"""
    try:
        success = await service.delete_template(template_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Brand Context Management
@router.post("/context/switch", response_model=BrandContextResponse)
async def switch_brand_context(
    request: BrandContextRequest,
    service: MultiBrandService = Depends(get_multi_brand_service)
):
    """Switch to a specific brand context"""
    try:
        context = await service.switch_brand_context(
            brand_id=request.brand_id,
            customer_id=request.customer_id,
            session_id=request.session_id
        )
        return BrandContextResponse(
            brand=BrandResponse.from_orm(context["brand"]),
            configurations=[ConfigurationResponse.from_orm(config) for config in context["configurations"]],
            templates=[TemplateResponse.from_orm(template) for template in context["templates"]],
            context_switched=context["context_switched"],
            message=context["message"]
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/context/current")
async def get_current_brand_context(
    customer_id: Optional[str] = None,
    session_id: Optional[str] = None,
    service: MultiBrandService = Depends(get_multi_brand_service)
):
    """Get current brand context"""
    try:
        context = await service.get_current_brand_context(
            customer_id=customer_id,
            session_id=session_id
        )
        return context
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Brand-Specific Response Generation
@router.post("/brands/{brand_id}/generate-response")
async def generate_brand_response(
    brand_id: int,
    message: str,
    context: Optional[Dict[str, Any]] = None,
    template_type: Optional[str] = None,
    service: MultiBrandService = Depends(get_multi_brand_service)
):
    """Generate a brand-specific response"""
    try:
        response = await service.generate_brand_response(
            brand_id=brand_id,
            message=message,
            context=context,
            template_type=template_type
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

# Analytics and Reporting
@router.get("/brands/{brand_id}/analytics", response_model=BrandAnalyticsResponse)
async def get_brand_analytics(
    brand_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    service: MultiBrandService = Depends(get_multi_brand_service)
):
    """Get analytics for a specific brand"""
    try:
        analytics = await service.get_brand_analytics(
            brand_id=brand_id,
            start_date=start_date,
            end_date=end_date
        )
        return BrandAnalyticsResponse(**analytics)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/analytics/comparison")
async def compare_brands_analytics(
    brand_ids: List[int],
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    service: MultiBrandService = Depends(get_multi_brand_service)
):
    """Compare analytics across multiple brands"""
    try:
        comparison = await service.compare_brands_analytics(
            brand_ids=brand_ids,
            start_date=start_date,
            end_date=end_date
        )
        return comparison
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Brand Import/Export
@router.post("/brands/{brand_id}/export")
async def export_brand_configuration(
    brand_id: int,
    include_templates: bool = True,
    include_configurations: bool = True,
    service: MultiBrandService = Depends(get_multi_brand_service)
):
    """Export brand configuration"""
    try:
        export_data = await service.export_brand_configuration(
            brand_id=brand_id,
            include_templates=include_templates,
            include_configurations=include_configurations
        )
        return export_data
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/brands/import")
async def import_brand_configuration(
    brand_data: Dict[str, Any],
    service: MultiBrandService = Depends(get_multi_brand_service)
):
    """Import brand configuration"""
    try:
        imported_brand = await service.import_brand_configuration(brand_data)
        return BrandResponse.from_orm(imported_brand)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

# Health Check
@router.get("/health")
async def health_check():
    """Health check endpoint for Multi-Brand Support"""
    return {
        "status": "healthy",
        "service": "Multi-Brand Support",
        "features": [
            "brand_management",
            "configuration_management", 
            "template_management",
            "context_switching",
            "brand_specific_responses",
            "analytics_and_reporting",
            "import_export"
        ],
        "message": "Multi-Brand Support service is running and ready!"
    }
