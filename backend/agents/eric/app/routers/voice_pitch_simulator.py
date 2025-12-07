from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from datetime import datetime

from ..services.voice_pitch_simulator_service import VoicePitchSimulatorService
from ..database import get_eric_database

router = APIRouter()

class SimulateVoicePitchRequest(BaseModel):
    rep_id: int
    scenario_type: str
    audio_data: str
    pitch_content: Optional[str] = None

class GeneratePracticeScenariosRequest(BaseModel):
    rep_id: int
    difficulty_level: str = "medium"
    focus_areas: Optional[List[str]] = None

class ComparePerformanceRequest(BaseModel):
    rep_id: int
    baseline_date: Optional[str] = None
    comparison_date: Optional[str] = None

class SimulateVoicePitchResponse(BaseModel):
    success: bool
    simulation_completed: bool
    rep_id: int
    scenario_type: str
    voice_analysis: Dict[str, Any]
    content_analysis: Dict[str, Any]
    feedback: Dict[str, Any]
    overall_score: float
    recommendations: List[Dict[str, Any]]
    simulated_at: str
    error: Optional[str] = None

class VoicePitchHistoryResponse(BaseModel):
    success: bool
    simulation_history: List[Dict[str, Any]]
    total_simulations: int
    error: Optional[str] = None

class VoiceAnalyticsResponse(BaseModel):
    success: bool
    performance_analysis: Dict[str, Any]
    improvement_trends: Dict[str, Any]
    analysis_period_days: int
    error: Optional[str] = None

class PracticeScenariosResponse(BaseModel):
    success: bool
    scenarios: List[Dict[str, Any]]
    improvement_areas: List[str]
    difficulty_level: str
    total_scenarios: int
    error: Optional[str] = None

@router.post("/voice-pitch/simulate", response_model=SimulateVoicePitchResponse)
async def simulate_voice_pitch(request: SimulateVoicePitchRequest):
    """Simulate and analyze a voice pitch"""
    try:
        service = VoicePitchSimulatorService()
        result = await service.simulate_voice_pitch(
            request.rep_id,
            request.scenario_type,
            request.audio_data,
            request.pitch_content
        )
        
        if result["success"]:
            return SimulateVoicePitchResponse(
                success=True,
                simulation_completed=result["simulation_completed"],
                rep_id=result["rep_id"],
                scenario_type=result["scenario_type"],
                voice_analysis=result["voice_analysis"],
                content_analysis=result["content_analysis"],
                feedback=result["feedback"],
                overall_score=result["overall_score"],
                recommendations=result["recommendations"],
                simulated_at=result["simulated_at"]
            )
        else:
            return SimulateVoicePitchResponse(success=False, error=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/voice-pitch/history", response_model=VoicePitchHistoryResponse)
async def get_voice_pitch_history(
    rep_id: Optional[int] = Query(None, description="Filter by sales rep ID"),
    scenario_type: Optional[str] = Query(None, description="Filter by scenario type"),
    limit: int = Query(50, description="Number of simulations to return")
):
    """Get voice pitch simulation history"""
    try:
        service = VoicePitchSimulatorService()
        result = await service.get_voice_pitch_history(rep_id, scenario_type, limit)
        
        if result["success"]:
            return VoicePitchHistoryResponse(
                success=True,
                simulation_history=result["simulation_history"],
                total_simulations=result["total_simulations"]
            )
        else:
            return VoicePitchHistoryResponse(success=False, error=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/voice-pitch/analytics", response_model=VoiceAnalyticsResponse)
async def get_voice_analytics(
    rep_id: Optional[int] = Query(None, description="Filter by sales rep ID"),
    days: int = Query(30, description="Number of days to analyze")
):
    """Get analytics about voice pitch performance"""
    try:
        service = VoicePitchSimulatorService()
        result = await service.get_voice_analytics(rep_id, days)
        
        if result["success"]:
            return VoiceAnalyticsResponse(
                success=True,
                performance_analysis=result["performance_analysis"],
                improvement_trends=result["improvement_trends"],
                analysis_period_days=result["analysis_period_days"]
            )
        else:
            return VoiceAnalyticsResponse(success=False, error=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/voice-pitch/practice-scenarios", response_model=PracticeScenariosResponse)
async def generate_practice_scenarios(request: GeneratePracticeScenariosRequest):
    """Generate practice scenarios for voice pitch improvement"""
    try:
        service = VoicePitchSimulatorService()
        result = await service.generate_practice_scenarios(
            request.rep_id,
            request.difficulty_level,
            request.focus_areas
        )
        
        if result["success"]:
            return PracticeScenariosResponse(
                success=True,
                scenarios=result["scenarios"],
                improvement_areas=result["improvement_areas"],
                difficulty_level=result["difficulty_level"],
                total_scenarios=result["total_scenarios"]
            )
        else:
            return PracticeScenariosResponse(success=False, error=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/voice-pitch/compare-performance")
async def compare_voice_performance(request: ComparePerformanceRequest):
    """Compare voice performance over time"""
    try:
        service = VoicePitchSimulatorService()
        result = await service.compare_voice_performance(
            request.rep_id,
            request.baseline_date,
            request.comparison_date
        )
        
        if result["success"]:
            return {
                "success": True,
                "baseline_data": result["baseline_data"],
                "comparison_data": result["comparison_data"],
                "improvements": result["improvements"],
                "overall_improvement": result["overall_improvement"]
            }
        else:
            return {"success": False, "error": result["error"]}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/voice-pitch/scenarios")
async def get_available_scenarios():
    """Get available pitch scenarios and their characteristics"""
    try:
        service = VoicePitchSimulatorService()
        return {
            "success": True,
            "pitch_scenarios": service.pitch_scenarios,
            "total_scenarios": len(service.pitch_scenarios)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/voice-pitch/parameters")
async def get_voice_parameters():
    """Get voice analysis parameters and optimal ranges"""
    try:
        service = VoicePitchSimulatorService()
        return {
            "success": True,
            "voice_parameters": service.voice_parameters,
            "total_parameters": len(service.voice_parameters)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/voice-pitch/performance-metrics")
async def get_voice_performance_metrics(
    rep_id: Optional[int] = Query(None, description="Filter by sales rep ID"),
    days: int = Query(30, description="Number of days to analyze")
):
    """Get detailed performance metrics for voice pitch simulations"""
    try:
        service = VoicePitchSimulatorService()
        db = await get_eric_database()
        async with db.get_session() as session:
            from ..models import SalesActivity
            from sqlalchemy import select, func, and_
            from datetime import datetime, timedelta
            
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Get simulation activities
            query = select(SalesActivity).where(
                and_(
                    SalesActivity.activity_type == "voice_pitch_simulation",
                    SalesActivity.created_at >= start_date
                )
            )
            
            if rep_id:
                query = query.where(SalesActivity.rep_id == rep_id)
            
            activities = await session.execute(query)
            activities = activities.scalars().all()
            
            # Calculate metrics
            total_simulations = len(activities)
            scores = []
            scenario_breakdown = {}
            parameter_breakdown = {}
            
            for activity in activities:
                metadata = activity.metadata or {}
                score = metadata.get("overall_score", 0)
                scores.append(score)
                
                # Scenario breakdown
                scenario_type = metadata.get("scenario_type", "unknown")
                if scenario_type not in scenario_breakdown:
                    scenario_breakdown[scenario_type] = {"count": 0, "total_score": 0}
                scenario_breakdown[scenario_type]["count"] += 1
                scenario_breakdown[scenario_type]["total_score"] += score
                
                # Parameter breakdown
                voice_analysis = metadata.get("voice_analysis", {})
                for param_name, analysis in voice_analysis.items():
                    if param_name != "overall_voice_score":
                        if param_name not in parameter_breakdown:
                            parameter_breakdown[param_name] = {"count": 0, "total_score": 0}
                        parameter_breakdown[param_name]["count"] += 1
                        parameter_breakdown[param_name]["total_score"] += analysis.get("score", 0)
            
            # Calculate averages
            avg_score = sum(scores) / len(scores) if scores else 0
            
            for scenario in scenario_breakdown.values():
                scenario["average_score"] = scenario["total_score"] / scenario["count"] if scenario["count"] > 0 else 0
            
            for param in parameter_breakdown.values():
                param["average_score"] = param["total_score"] / param["count"] if param["count"] > 0 else 0
            
            return {
                "success": True,
                "metrics": {
                    "total_simulations": total_simulations,
                    "average_score": round(avg_score, 2),
                    "scenario_breakdown": scenario_breakdown,
                    "parameter_breakdown": parameter_breakdown,
                    "score_distribution": {
                        "excellent": len([s for s in scores if s >= 0.8]),
                        "good": len([s for s in scores if 0.6 <= s < 0.8]),
                        "needs_improvement": len([s for s in scores if s < 0.6])
                    },
                    "analysis_period_days": days
                }
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/voice-pitch/improvement-trends")
async def get_improvement_trends(
    rep_id: int = Query(..., description="Sales rep ID"),
    days: int = Query(30, description="Number of days to analyze")
):
    """Get improvement trends for a specific sales rep"""
    try:
        service = VoicePitchSimulatorService()
        db = await get_eric_database()
        async with db.get_session() as session:
            from ..models import SalesActivity
            from sqlalchemy import select, and_
            from datetime import datetime, timedelta
            
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Get rep's simulation activities
            query = select(SalesActivity).where(
                and_(
                    SalesActivity.rep_id == rep_id,
                    SalesActivity.activity_type == "voice_pitch_simulation",
                    SalesActivity.created_at >= start_date
                )
            ).order_by(SalesActivity.created_at)
            
            activities = await session.execute(query)
            activities = activities.scalars().all()
            
            if len(activities) < 2:
                return {
                    "success": True,
                    "trends": {
                        "trend": "insufficient_data",
                        "message": "Need at least 2 simulations to analyze trends"
                    }
                }
            
            # Calculate daily averages
            daily_scores = {}
            for activity in activities:
                date_key = activity.created_at.date().isoformat()
                if date_key not in daily_scores:
                    daily_scores[date_key] = []
                daily_scores[date_key].append(activity.metadata.get("overall_score", 0))
            
            # Calculate trend
            dates = sorted(daily_scores.keys())
            if len(dates) >= 2:
                early_avg = sum(daily_scores[dates[0]]) / len(daily_scores[dates[0]])
                recent_avg = sum(daily_scores[dates[-1]]) / len(daily_scores[dates[-1]])
                improvement = recent_avg - early_avg
                
                if improvement > 0.1:
                    trend = "improving"
                elif improvement < -0.1:
                    trend = "declining"
                else:
                    trend = "stable"
            else:
                trend = "insufficient_data"
                improvement = 0
            
            return {
                "success": True,
                "trends": {
                    "trend": trend,
                    "improvement_amount": round(improvement, 2),
                    "daily_averages": {
                        date: round(sum(scores) / len(scores), 2)
                        for date, scores in daily_scores.items()
                    },
                    "total_simulations": len(activities)
                }
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/voice-pitch/recommendations/{rep_id}")
async def get_voice_recommendations(
    rep_id: int,
    scenario_type: Optional[str] = Query(None, description="Focus on specific scenario")
):
    """Get personalized voice pitch recommendations for a sales rep"""
    try:
        service = VoicePitchSimulatorService()
        db = await get_eric_database()
        async with db.get_session() as session:
            from ..models import SalesRep
            from sqlalchemy import select
            
            # Get rep information
            query = select(SalesRep).where(SalesRep.id == rep_id)
            result = await session.execute(query)
            rep = result.scalar_one_or_none()
            
            if not rep:
                raise HTTPException(status_code=404, detail="Sales rep not found")
            
            # Get rep's performance history
            performance_history = await service._get_rep_performance_history(session, rep_id)
            
            # Identify improvement areas
            improvement_areas = await service._identify_improvement_areas(performance_history)
            
            # Generate recommendations
            recommendations = {
                "rep_name": rep.name,
                "improvement_areas": improvement_areas,
                "scenario_focus": scenario_type or "all",
                "practice_recommendations": [
                    "Practice daily for 15-20 minutes",
                    "Record yourself and analyze playback",
                    "Focus on one improvement area at a time",
                    "Use the voice pitch simulator regularly"
                ],
                "specific_tips": []
            }
            
            # Add specific tips based on improvement areas
            for area in improvement_areas:
                if area == "pitch":
                    recommendations["specific_tips"].append("Practice humming at different frequencies")
                elif area == "speech_rate":
                    recommendations["specific_tips"].append("Use a metronome to practice 140 words per minute")
                elif area == "volume":
                    recommendations["specific_tips"].append("Practice projecting your voice without shouting")
                elif area == "clarity":
                    recommendations["specific_tips"].append("Practice tongue twisters and enunciation")
                elif area == "confidence":
                    recommendations["specific_tips"].append("Practice power poses before speaking")
            
            return {
                "success": True,
                "recommendations": recommendations
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/voice-pitch/scenario-templates")
async def get_scenario_templates():
    """Get templates for different pitch scenarios"""
    try:
        return {
            "success": True,
            "templates": {
                "cold_call": {
                    "duration": 30,
                    "structure": [
                        "Introduction (5 seconds)",
                        "Value proposition (15 seconds)",
                        "Call to action (10 seconds)"
                    ],
                    "key_phrases": [
                        "Hi [Name], this is [Your Name] from [Company]",
                        "We help [industry] companies [benefit]",
                        "Would you be interested in a quick 15-minute call?"
                    ]
                },
                "follow_up": {
                    "duration": 45,
                    "structure": [
                        "Relationship building (10 seconds)",
                        "Pain point identification (20 seconds)",
                        "Solution presentation (15 seconds)"
                    ],
                    "key_phrases": [
                        "Thanks for taking my call",
                        "What challenges are you currently facing?",
                        "Our solution specifically addresses [pain point]"
                    ]
                },
                "closing": {
                    "duration": 60,
                    "structure": [
                        "Objection handling (20 seconds)",
                        "Value reinforcement (25 seconds)",
                        "Closing technique (15 seconds)"
                    ],
                    "key_phrases": [
                        "I understand your concern about [objection]",
                        "The ROI on this investment is [specific number]",
                        "Shall we proceed with the agreement?"
                    ]
                }
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
