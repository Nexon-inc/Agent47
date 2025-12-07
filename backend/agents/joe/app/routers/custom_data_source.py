"""
Custom Data Source Router

This router handles external data source integration and custom data feeds endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List
from pydantic import BaseModel, Field

from ..database import get_joe_database
from ..services.custom_data_source_service import CustomDataSourceService

router = APIRouter(prefix="/custom-data-source", tags=["Custom Data Source"])

class DataSourceIntegrationRequest(BaseModel):
    source_config: Dict[str, Any] = Field(..., description="Data source configuration for integration")

class DataSourceValidationRequest(BaseModel):
    source_id: str = Field(..., description="Data source ID to validate")

# Dependency
async def get_custom_data_source_service() -> CustomDataSourceService:
    service = CustomDataSourceService()
    await service.initialize()
    return service

@router.post("/integrate-source")
async def integrate_data_source(
    request: DataSourceIntegrationRequest,
    service: CustomDataSourceService = Depends(get_custom_data_source_service)
):
    """Integrate a new external data source"""
    try:
        result = await service.integrate_data_source(
            user_id=1,  # TODO: Get from authentication
            source_config=request.source_config
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["integration_data"],
                "message": "Data source integrated successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Data source integration failed: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to integrate data source: {str(e)}"
        )

@router.post("/validate-source")
async def validate_data_source(
    request: DataSourceValidationRequest,
    service: CustomDataSourceService = Depends(get_custom_data_source_service)
):
    """Validate data source connection and data quality"""
    try:
        result = await service.validate_data_source(
            user_id=1,  # TODO: Get from authentication
            source_id=request.source_id
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["validation_data"],
                "message": "Data source validation completed"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Data source validation failed: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate data source: {str(e)}"
        )

@router.get("/source-types")
async def get_supported_source_types(service: CustomDataSourceService = Depends(get_custom_data_source_service)):
    """Get supported data source types for integration"""
    source_types = [
        {
            "id": "api",
            "name": "API Integration",
            "description": "Connect to external APIs and web services",
            "capabilities": ["real_time_data", "structured_data", "authentication"],
            "examples": ["REST APIs", "GraphQL", "SOAP services"]
        },
        {
            "id": "database",
            "name": "Database Connection",
            "description": "Connect to external databases",
            "capabilities": ["sql_queries", "data_export", "connection_pooling"],
            "examples": ["PostgreSQL", "MySQL", "MongoDB", "SQL Server"]
        },
        {
            "id": "file_upload",
            "name": "File Upload",
            "description": "Upload and process data files",
            "capabilities": ["file_parsing", "format_support", "batch_processing"],
            "examples": ["CSV", "Excel", "JSON", "XML"]
        },
        {
            "id": "web_scraping",
            "name": "Web Scraping",
            "description": "Extract data from websites",
            "capabilities": ["html_parsing", "scheduled_scraping", "data_cleaning"],
            "examples": ["News sites", "E-commerce", "Social media"]
        },
        {
            "id": "streaming",
            "name": "Real-time Streaming",
            "description": "Connect to real-time data streams",
            "capabilities": ["real_time_processing", "event_handling", "scalability"],
            "examples": ["Kafka", "WebSockets", "IoT devices"]
        }
    ]
    
    return {
        "status": "success",
        "data": source_types,
        "message": f"Retrieved {len(source_types)} supported source types"
    }
