from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List
from pydantic import BaseModel, Field

from ..database import get_joe_database
from ..services.data_export_service import DataExportService

router = APIRouter(prefix="/data-export", tags=["Data Export"])

class ExportRequest(BaseModel):
    data_type: str = Field(..., description="Type of data to export")
    format_type: str = Field(default="csv", description="Export format")
    filters: Dict[str, Any] = Field(default={}, description="Export filters")

# Dependency
async def get_data_export_service() -> DataExportService:
    service = DataExportService()
    await service.initialize()
    return service

@router.post("/export")
async def export_research_data(
    request: ExportRequest,
    service: DataExportService = Depends(get_data_export_service)
):
    """Export research data in specified format"""
    try:
        result = await service.export_research_data(
            user_id=1,  # TODO: Get from authentication
            data_type=request.data_type,
            format_type=request.format_type,
            filters=request.filters
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["export_data"],
                "message": f"Data exported in {request.format_type} format"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Data export failed: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export data: {str(e)}"
        )

@router.get("/history")
async def get_export_history(
    limit: int = 10,
    service: DataExportService = Depends(get_data_export_service)
):
    """Get user's export history"""
    try:
        result = await service.get_export_history(
            user_id=1,  # TODO: Get from authentication
            limit=limit
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["history"],
                "message": f"Retrieved {result['total_exports']} export records"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get export history: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get export history: {str(e)}"
        )

@router.get("/formats")
async def get_export_formats(service: DataExportService = Depends(get_data_export_service)):
    """Get available export formats"""
    formats = [
        {
            "id": "csv",
            "name": "CSV",
            "description": "Comma-separated values format",
            "best_for": "Data analysis, spreadsheet applications",
            "file_extension": ".csv"
        },
        {
            "id": "json",
            "name": "JSON",
            "description": "JavaScript Object Notation format",
            "best_for": "API integration, web applications",
            "file_extension": ".json"
        },
        {
            "id": "pdf",
            "name": "PDF",
            "description": "Portable Document Format",
            "best_for": "Reports, presentations, sharing",
            "file_extension": ".pdf"
        },
        {
            "id": "excel",
            "name": "Excel",
            "description": "Microsoft Excel format",
            "best_for": "Advanced analysis, charts, formatting",
            "file_extension": ".xlsx"
        }
    ]
    
    return {
        "status": "success",
        "data": formats,
        "message": f"Retrieved {len(formats)} export formats"
    }
