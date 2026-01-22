from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from datetime import datetime

from ..services.auto_pitch_generator_service import AutoPitchGeneratorService
from ..database import get_eric_database

router = APIRouter()

class GeneratePitchRequest(BaseModel):
    lead_id: int
    style: str
    format_type: str
    custom_context: Optional[Dict[str, Any]] = None

class BulkPitchRequest(BaseModel):
    lead_ids: List[int]
    style: str
    format_type: str
    custom_context: Optional[Dict[str, Any]] = None

class PitchTemplatesRequest(BaseModel):
    industry: Optional[str] = None
    use_case: Optional[str] = None

class PitchPerformanceRequest(BaseModel):
    pitch_id: int
    engagement_data: Dict[str, Any]

class PitchHistoryRequest(BaseModel):
    lead_id: Optional[int] = None
    rep_id: Optional[int] = None
    style: Optional[str] = None
    limit: int = 50

class PitchResponse(BaseModel):
    success: bool
    pitch: Optional[Dict[str, Any]] = None
    style: Optional[str] = None
    format: Optional[str] = None
    generated_at: Optional[str] = None
    lead_context: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class BulkPitchResponse(BaseModel):
    success: bool
    results: List[Dict[str, Any]]
    total_leads: int
    successful_generations: int
    error: Optional[str] = None

class PitchTemplatesResponse(BaseModel):
    success: bool
    templates: Dict[str, Any]
    error: Optional[str] = None

class PitchPerformanceResponse(BaseModel):
    success: bool
    performance_metrics: Dict[str, Any]
    recommendations: List[str]
    analyzed_at: str
    error: Optional[str] = None

class PitchHistoryResponse(BaseModel):
    success: bool
    pitch_history: List[Dict[str, Any]]
    total_count: int
    error: Optional[str] = None

@router.post("/pitch/generate", response_model=PitchResponse)
async def generate_pitch(request: GeneratePitchRequest):
    """Generate a sales pitch in the specified style and format"""
    try:
        service = AutoPitchGeneratorService()
        result = await service.generate_pitch(
            request.lead_id,
            request.style,
            request.format_type,
            request.custom_context
        )
        
        if result["success"]:
            return PitchResponse(
                success=True,
                pitch=result["pitch"],
                style=result["style"],
                format=result["format"],
                generated_at=result["generated_at"],
                lead_context=result["lead_context"]
            )
        else:
            return PitchResponse(success=False, error=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/pitch/bulk-generate", response_model=BulkPitchResponse)
async def generate_bulk_pitches(request: BulkPitchRequest):
    """Generate pitches for multiple leads"""
    try:
        service = AutoPitchGeneratorService()
        result = await service.generate_bulk_pitches(
            request.lead_ids,
            request.style,
            request.format_type,
            request.custom_context
        )
        
        if result["success"]:
            return BulkPitchResponse(
                success=True,
                results=result["results"],
                total_leads=result["total_leads"],
                successful_generations=result["successful_generations"]
            )
        else:
            return BulkPitchResponse(success=False, error=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/pitch/templates", response_model=PitchTemplatesResponse)
async def get_pitch_templates(request: PitchTemplatesRequest):
    """Get pitch templates for different industries and use cases"""
    try:
        service = AutoPitchGeneratorService()
        result = await service.get_pitch_templates(
            request.industry,
            request.use_case
        )
        
        if result["success"]:
            return PitchTemplatesResponse(
                success=True,
                templates=result["templates"]
            )
        else:
            return PitchTemplatesResponse(success=False, error=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/pitch/analyze-performance", response_model=PitchPerformanceResponse)
async def analyze_pitch_performance(request: PitchPerformanceRequest):
    """Analyze the performance of a generated pitch"""
    try:
        service = AutoPitchGeneratorService()
        result = await service.analyze_pitch_performance(
            request.pitch_id,
            request.engagement_data
        )
        
        if result["success"]:
            return PitchPerformanceResponse(
                success=True,
                performance_metrics=result["performance_metrics"],
                recommendations=result["recommendations"],
                analyzed_at=result["analyzed_at"]
            )
        else:
            return PitchPerformanceResponse(success=False, error=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/pitch/history", response_model=PitchHistoryResponse)
async def get_pitch_history(request: PitchHistoryRequest):
    """Get pitch generation history with filters"""
    try:
        service = AutoPitchGeneratorService()
        result = await service.get_pitch_history(
            request.lead_id,
            request.rep_id,
            request.style,
            request.limit
        )
        
        if result["success"]:
            return PitchHistoryResponse(
                success=True,
                pitch_history=result["pitch_history"],
                total_count=result["total_count"]
            )
        else:
            return PitchHistoryResponse(success=False, error=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/pitch/styles")
async def get_available_pitch_styles():
    """Get available pitch styles and their characteristics"""
    try:
        service = AutoPitchGeneratorService()
        return {
            "success": True,
            "styles": service.pitch_styles,
            "total_styles": len(service.pitch_styles)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/pitch/formats")
async def get_available_formats():
    """Get available pitch formats"""
    try:
        return {
            "success": True,
            "formats": [
                {
                    "type": "text",
                    "description": "Text-based pitch for email, messaging, or chat",
                    "features": ["Emojis support", "Formatting", "Easy editing"]
                },
                {
                    "type": "voice",
                    "description": "Voice-optimized pitch for calls or voice messages",
                    "features": ["Pause markers", "Emphasis indicators", "Duration estimation"]
                }
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/pitch/performance-summary")
async def get_pitch_performance_summary(
    lead_id: Optional[int] = Query(None, description="Filter by lead ID"),
    style: Optional[str] = Query(None, description="Filter by pitch style"),
    days: int = Query(30, description="Number of days to analyze")
):
    """Get summary of pitch performance metrics"""
    try:
        service = AutoPitchGeneratorService()
        db = await get_eric_database()
        async with db.get_session() as session:
            # Get pitch history for analysis
            result = await service.get_pitch_history(
                lead_id=lead_id,
                style=style,
                limit=1000
            )
            
            if not result["success"]:
                return {"success": False, "error": result["error"]}
            
            # Calculate performance summary
            pitches = result["pitch_history"]
            total_pitches = len(pitches)
            
            if total_pitches == 0:
                return {
                    "success": True,
                    "summary": {
                        "total_pitches": 0,
                        "average_engagement_score": 0,
                        "most_effective_style": None,
                        "conversion_rate": 0
                    }
                }
            
            # Calculate metrics
            engagement_scores = []
            style_performance = {}
            conversions = 0
            
            for pitch in pitches:
                engagement_metrics = pitch.get("engagement_metrics", {})
                score = engagement_metrics.get("engagement_score", 0)
                engagement_scores.append(score)
                
                pitch_style = pitch.get("style", "unknown")
                if pitch_style not in style_performance:
                    style_performance[pitch_style] = {"count": 0, "total_score": 0}
                
                style_performance[pitch_style]["count"] += 1
                style_performance[pitch_style]["total_score"] += score
                
                if engagement_metrics.get("conversion_likelihood") == "high":
                    conversions += 1
            
            # Calculate averages
            avg_engagement = sum(engagement_scores) / len(engagement_scores) if engagement_scores else 0
            conversion_rate = (conversions / total_pitches) * 100 if total_pitches > 0 else 0
            
            # Find most effective style
            most_effective_style = None
            best_avg_score = 0
            
            for style, data in style_performance.items():
                avg_score = data["total_score"] / data["count"]
                if avg_score > best_avg_score:
                    best_avg_score = avg_score
                    most_effective_style = style
            
            return {
                "success": True,
                "summary": {
                    "total_pitches": total_pitches,
                    "average_engagement_score": round(avg_engagement, 2),
                    "most_effective_style": most_effective_style,
                    "conversion_rate": round(conversion_rate, 2),
                    "style_performance": style_performance
                }
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/pitch/recommendations/{lead_id}")
async def get_pitch_recommendations(
    lead_id: int,
    preferred_style: Optional[str] = Query(None, description="Preferred pitch style")
):
    """Get personalized pitch recommendations for a lead"""
    try:
        service = AutoPitchGeneratorService()
        db = await get_eric_database()
        async with db.get_session() as session:
            # Get lead information
            from ..models import EricLead
            from sqlalchemy import select
            
            query = select(EricLead).where(EricLead.id == lead_id)
            result = await session.execute(query)
            lead = result.scalar_one_or_none()
            
            if not lead:
                raise HTTPException(status_code=404, detail="EricLead not found")
            
            # Analyze lead characteristics for style recommendation
            recommended_style = preferred_style or "consultative"
            
            # Determine best style based on lead characteristics
            if lead.industry in ["technology", "startup"]:
                recommended_style = "gen_z" if not preferred_style else preferred_style
            elif lead.industry in ["finance", "legal"]:
                recommended_style = "formal" if not preferred_style else preferred_style
            elif lead.budget and lead.budget > 100000:
                recommended_style = "consultative" if not preferred_style else preferred_style
            
            # Get pitch history for this lead
            history_result = await service.get_pitch_history(lead_id=lead_id, limit=10)
            
            # Generate recommendations
            recommendations = {
                "recommended_style": recommended_style,
                "reasoning": f"Based on {lead.industry} industry and {lead.stage} stage",
                "alternative_styles": ["consultative", "storytelling", "formal"],
                "best_time_to_pitch": "Tuesday 10 AM - 2 PM",
                "personalization_tips": [
                    f"Reference {lead.company} recent achievements",
                    f"Address {lead.pain_points or 'industry challenges'}",
                    "Include relevant case studies"
                ]
            }
            
            if history_result["success"] and history_result["pitch_history"]:
                # Analyze past performance
                past_pitches = history_result["pitch_history"]
                best_performing_style = None
                best_score = 0
                
                for pitch in past_pitches:
                    engagement_metrics = pitch.get("engagement_metrics", {})
                    score = engagement_metrics.get("engagement_score", 0)
                    if score > best_score:
                        best_score = score
                        best_performing_style = pitch.get("style")
                
                if best_performing_style:
                    recommendations["best_performing_style"] = best_performing_style
                    recommendations["past_performance_score"] = best_score
            
            return {
                "success": True,
                "lead_id": lead_id,
                "recommendations": recommendations
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/pitch/{pitch_id}")
async def delete_pitch(pitch_id: int):
    """Delete a generated pitch"""
    try:
        service = AutoPitchGeneratorService()
        db = await get_eric_database()
        async with db.get_session() as session:
            from ..models import EricSalesActivity
            from sqlalchemy import select
            
            # Find and delete the pitch activity
            query = select(EricSalesActivity).where(
                EricSalesActivity.id == pitch_id,
                EricSalesActivity.activity_type == "pitch_generation"
            )
            result = await session.execute(query)
            activity = result.scalar_one_or_none()
            
            if not activity:
                raise HTTPException(status_code=404, detail="Pitch not found")
            
            await session.delete(activity)
            await session.commit()
            
            return {
                "success": True,
                "message": "Pitch deleted successfully",
                "pitch_id": pitch_id
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
