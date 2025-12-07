from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List
from pydantic import BaseModel, Field

from ..database import get_joe_database
from ..services.research_summarizer_service import ResearchSummarizerService

router = APIRouter(prefix="/research-summarizer", tags=["Research Summarizer"])

class SummarizeRequest(BaseModel):
    data_type: str = Field(..., description="Type of data to summarize")
    content: str = Field(..., description="Content to summarize")
    summary_length: str = Field(default="medium", description="Length of summary")

# Dependency
async def get_research_summarizer_service() -> ResearchSummarizerService:
    service = ResearchSummarizerService()
    await service.initialize()
    return service

@router.post("/summarize")
async def summarize_research_data(
    request: SummarizeRequest,
    service: ResearchSummarizerService = Depends(get_research_summarizer_service)
):
    """Summarize research data and content"""
    try:
        result = await service.summarize_research_data(
            user_id=1,  # TODO: Get from authentication
            data_type=request.data_type,
            content=request.content,
            summary_length=request.summary_length
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["summary_data"],
                "message": f"Research data summarized for {request.data_type}"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Research summarization failed: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to summarize research data: {str(e)}"
        )

@router.get("/history")
async def get_summary_history(
    limit: int = 10,
    service: ResearchSummarizerService = Depends(get_research_summarizer_service)
):
    """Get user's summary history"""
    try:
        result = await service.get_summary_history(
            user_id=1,  # TODO: Get from authentication
            limit=limit
        )
        
        if result["success"]:
            return {
                "status": "success",
                "data": result["history"],
                "message": f"Retrieved {result['total_summaries']} summary records"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get summary history: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get summary history: {str(e)}"
        )

@router.get("/summary-lengths")
async def get_summary_lengths(service: ResearchSummarizerService = Depends(get_research_summarizer_service)):
    """Get available summary length options"""
    lengths = [
        {
            "id": "short",
            "name": "Short Summary",
            "description": "Brief overview with key points",
            "target_length": "100-200 words",
            "reduction_rate": "90-95%"
        },
        {
            "id": "medium",
            "name": "Medium Summary",
            "description": "Balanced summary with main insights",
            "target_length": "300-500 words",
            "reduction_rate": "75-85%"
        },
        {
            "id": "long",
            "name": "Long Summary",
            "description": "Detailed summary with comprehensive insights",
            "target_length": "800-1200 words",
            "reduction_rate": "50-70%"
        },
        {
            "id": "executive",
            "name": "Executive Summary",
            "description": "High-level summary for decision makers",
            "target_length": "150-300 words",
            "reduction_rate": "85-90%"
        }
    ]
    
    return {
        "status": "success",
        "data": lengths,
        "message": f"Retrieved {len(lengths)} summary length options"
    }
