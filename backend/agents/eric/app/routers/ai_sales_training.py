from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from datetime import datetime
import json

from ..services.ai_sales_training_service import AISalesTrainingService
from ..database import get_eric_database
from ..models import SalesRep
from sqlalchemy import select

router = APIRouter()

class TrainingModuleRequest(BaseModel):
    title: str
    description: str
    category: str
    difficulty: str
    duration: int
    content: Dict[str, Any]
    assessments: List[Dict[str, Any]] = []
    prerequisites: List[str] = []
    brand_id: int
    created_by: int

class AssessmentRequest(BaseModel):
    session_id: str
    questions: List[Dict[str, Any]]
    answers: List[str]

class TrainingPathResponse(BaseModel):
    success: bool
    training_path: Dict[str, Any]

class TrainingModuleResponse(BaseModel):
    success: bool
    module: Dict[str, Any]

class TrainingSessionResponse(BaseModel):
    success: bool
    session: Dict[str, Any]
    module: Dict[str, Any]

class AssessmentResponse(BaseModel):
    success: bool
    assessment: Dict[str, Any]
    session_progress: int

class TrainingProgressResponse(BaseModel):
    success: bool
    progress: Dict[str, Any]

@router.post("/training/modules", response_model=TrainingModuleResponse)
async def create_training_module(request: TrainingModuleRequest):
    """Create a new AI-powered training module"""
    try:
        service = AISalesTrainingService()
        module_data = request.dict()
        result = await service.create_training_module(module_data)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/training/personalized-path/{rep_id}", response_model=TrainingPathResponse)
async def get_personalized_training_path(
    rep_id: int,
    brand_id: int = Query(..., description="Brand ID")
):
    """Get personalized training path for a sales representative"""
    try:
        service = AISalesTrainingService()
        result = await service.get_personalized_training_path(rep_id, brand_id)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/training/sessions", response_model=TrainingSessionResponse)
async def start_training_session(
    rep_id: int = Query(..., description="Sales Representative ID"),
    module_id: str = Query(..., description="Training Module ID")
):
    """Start a training session for a sales representative"""
    try:
        service = AISalesTrainingService()
        result = await service.start_training_session(rep_id, module_id)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/training/assessments", response_model=AssessmentResponse)
async def complete_training_assessment(request: AssessmentRequest):
    """Complete a training assessment"""
    try:
        service = AISalesTrainingService()
        result = await service.complete_training_assessment(request.session_id, request.dict())
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/training/progress/{rep_id}", response_model=TrainingProgressResponse)
async def get_training_progress(rep_id: int):
    """Get training progress for a sales representative"""
    try:
        service = AISalesTrainingService()
        result = await service.get_training_progress(rep_id)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/training/modules")
async def get_available_modules(
    brand_id: int = Query(..., description="Brand ID")
):
    """Get available training modules"""
    try:
        service = AISalesTrainingService()
        
        return {
            "success": True,
            "modules": service.training_modules
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/training/sessions/{session_id}")
async def get_training_session(session_id: str):
    """Get training session details"""
    try:
        service = AISalesTrainingService()
        session_key = f"training_session:{session_id}"
        session_data = await service.redis_manager.get(session_key)
        
        if not session_data:
            raise HTTPException(status_code=404, detail="Training session not found")
        
        session = json.loads(session_data)
        
        return {
            "success": True,
            "session": session
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/training/assessments/{assessment_id}")
async def get_assessment_result(assessment_id: str):
    """Get assessment result"""
    try:
        service = AISalesTrainingService()
        assessment_key = f"training_assessment:{assessment_id}"
        assessment_data = await service.redis_manager.get(assessment_key)
        
        if not assessment_data:
            raise HTTPException(status_code=404, detail="Assessment not found")
        
        assessment = json.loads(assessment_data)
        
        return {
            "success": True,
            "assessment": assessment
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/training/performance-analysis/{rep_id}")
async def get_performance_analysis(rep_id: int):
    """Get performance analysis for training recommendations"""
    try:
        service = AISalesTrainingService()
        db = await get_eric_database()
        async with db.get_session() as session:
            analysis = await service._analyze_rep_performance(session, rep_id)
            skill_gaps = await service._identify_skill_gaps(analysis)
            
            return {
                "success": True,
                "performance_analysis": analysis,
                "skill_gaps": skill_gaps,
                "skill_level": await service._determine_skill_level(analysis)
            }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/training/recommendations/{rep_id}")
async def get_training_recommendations(
    rep_id: int,
    brand_id: int = Query(..., description="Brand ID")
):
    """Get personalized training recommendations"""
    try:
        service = AISalesTrainingService()
        db = await get_eric_database()
        async with db.get_session() as session:
            analysis = await service._analyze_rep_performance(session, rep_id)
            skill_gaps = await service._identify_skill_gaps(analysis)
            recommended_modules = await service._get_recommended_modules(skill_gaps, brand_id)
            
            return {
                "success": True,
                "recommendations": {
                    "skill_gaps": skill_gaps,
                    "recommended_modules": recommended_modules,
                    "priority_order": await service._prioritize_modules(recommended_modules, skill_gaps),
                    "estimated_completion_time": await service._estimate_completion_time(recommended_modules)
                }
            }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/training/certificates/{rep_id}")
async def get_training_certificates(rep_id: int):
    """Get training certificates for a sales representative"""
    try:
        service = AISalesTrainingService()
        progress = await service.get_training_progress(rep_id)
        
        if not progress["success"]:
            raise HTTPException(status_code=400, detail=progress["error"])
        
        certificates = []
        for module in progress["progress"]["completed_modules"]:
            if module.get("score", 0) >= 80:  # Minimum score for certificate
                certificates.append({
                    "certificate_id": f"cert_{rep_id}_{module['module_id']}",
                    "module_title": module["module_title"],
                    "completion_date": module["completion_time"],
                    "score": module["score"],
                    "status": "issued"
                })
        
        return {
            "success": True,
            "certificates": certificates
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/training/team-progress")
async def get_team_training_progress(
    brand_id: int = Query(..., description="Brand ID")
):
    """Get team-wide training progress"""
    try:
        service = AISalesTrainingService()
        db = await get_eric_database()
        async with db.get_session() as session:
            sales_reps = await session.execute(
                select(SalesRep).where(SalesRep.brand_id == brand_id)
            )
            sales_reps = sales_reps.scalars().all()
            
            team_progress = {
                "total_reps": len(sales_reps),
                "reps_with_progress": 0,
                "average_completion": 0,
                "top_learners": [],
                "modules_in_progress": {}
            }
            
            rep_progress_data = []
            for rep in sales_reps:
                progress = await service.get_training_progress(rep.id)
                if progress["success"]:
                    rep_data = {
                        "rep_id": rep.id,
                        "rep_name": f"{rep.first_name} {rep.last_name}",
                        "completion_percentage": progress["progress"]["completion_percentage"],
                        "modules_completed": progress["progress"]["modules_completed"]
                    }
                    rep_progress_data.append(rep_data)
                    
                    if progress["progress"]["completion_percentage"] > 0:
                        team_progress["reps_with_progress"] += 1
            
            if rep_progress_data:
                rep_progress_data.sort(key=lambda x: x["completion_percentage"], reverse=True)
                team_progress["top_learners"] = rep_progress_data[:5]
                team_progress["average_completion"] = sum(r["completion_percentage"] for r in rep_progress_data) / len(rep_progress_data)
            
            return {
                "success": True,
                "team_progress": team_progress
            }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
