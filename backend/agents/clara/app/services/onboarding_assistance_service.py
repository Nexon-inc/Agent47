from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from fastapi import HTTPException, BackgroundTasks
import json
import asyncio
from enum import Enum

from ..models import OnboardingStep, OnboardingSession, OnboardingTutorial, OnboardingProgress
from ..database import get_clara_database
from core.config import settings
from core.integrations import IntegrationManager
from core.analytics import AnalyticsManager
# NLPUtils kept for specialized semantic_search_tutorials only
from core.utils.nlp_utils import NLPUtils


class OnboardingAssistanceService:
    def __init__(self):
        self.integration_manager = IntegrationManager()
        self.analytics_manager = AnalyticsManager()
        # NLPUtils removed - using AI Service Manager for semantic search
        
    async def create_onboarding_step(
        self, 
        db: Session, 
        step_name: str,
        step_type: str,
        description: Optional[str] = None,
        content: str = "",
        order_index: int = 0,
        is_required: bool = True,
        estimated_time_minutes: Optional[int] = None
    ) -> Dict[str, Any]:
        """Create a new onboarding step"""
        try:
            step = OnboardingStep(
                step_name=step_name,
                step_type=step_type,
                description=description,
                content=content,
                order_index=order_index,
                is_required=is_required,
                estimated_time_minutes=estimated_time_minutes,
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(step)
            db.commit()
            db.refresh(step)
            
            return {
                "id": step.id,
                "step_name": step.step_name,
                "step_type": step.step_type,
                "description": step.description,
                "content": step.content,
                "order_index": step.order_index,
                "is_required": step.is_required,
                "estimated_time_minutes": step.estimated_time_minutes,
                "is_active": step.is_active,
                "created_at": step.created_at,
                "updated_at": step.updated_at
            }
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to create onboarding step: {str(e)}")
    
    async def get_onboarding_step(
        self, 
        db: Session, 
        step_id: int
    ) -> Dict[str, Any]:
        """Get onboarding step by ID"""
        try:
            step = db.query(OnboardingStep).filter(OnboardingStep.id == step_id).first()
            if not step:
                raise HTTPException(status_code=404, detail="Onboarding step not found")
            
            return {
                "id": step.id,
                "step_name": step.step_name,
                "step_type": step.step_type,
                "description": step.description,
                "content": step.content,
                "order_index": step.order_index,
                "is_required": step.is_required,
                "estimated_time_minutes": step.estimated_time_minutes,
                "is_active": step.is_active,
                "created_at": step.created_at,
                "updated_at": step.updated_at
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get onboarding step: {str(e)}")
    
    async def list_onboarding_steps(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        step_type: Optional[str] = None,
        is_required: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        """List onboarding steps"""
        try:
            query = db.query(OnboardingStep).filter(OnboardingStep.is_active == True)
            
            if step_type:
                query = query.filter(OnboardingStep.step_type == step_type)
            if is_required is not None:
                query = query.filter(OnboardingStep.is_required == is_required)
            
            steps = query.order_by(OnboardingStep.order_index).offset(skip).limit(limit).all()
            
            return [
                {
                    "id": step.id,
                    "step_name": step.step_name,
                    "step_type": step.step_type,
                    "description": step.description,
                    "content": step.content,
                    "order_index": step.order_index,
                    "is_required": step.is_required,
                    "estimated_time_minutes": step.estimated_time_minutes,
                    "is_active": step.is_active,
                    "created_at": step.created_at,
                    "updated_at": step.updated_at
                } for step in steps
            ]
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to list onboarding steps: {str(e)}")
    
    async def update_onboarding_step(
        self, 
        db: Session, 
        step_id: int,
        step_name: Optional[str] = None,
        step_type: Optional[str] = None,
        description: Optional[str] = None,
        content: Optional[str] = None,
        order_index: Optional[int] = None,
        is_required: Optional[bool] = None,
        estimated_time_minutes: Optional[int] = None
    ) -> Dict[str, Any]:
        """Update onboarding step"""
        try:
            step = db.query(OnboardingStep).filter(OnboardingStep.id == step_id).first()
            if not step:
                raise HTTPException(status_code=404, detail="Onboarding step not found")
            
            if step_name is not None:
                step.step_name = step_name
            if step_type is not None:
                step.step_type = step_type
            if description is not None:
                step.description = description
            if content is not None:
                step.content = content
            if order_index is not None:
                step.order_index = order_index
            if is_required is not None:
                step.is_required = is_required
            if estimated_time_minutes is not None:
                step.estimated_time_minutes = estimated_time_minutes
            
            step.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(step)
            
            return {
                "id": step.id,
                "step_name": step.step_name,
                "step_type": step.step_type,
                "description": step.description,
                "content": step.content,
                "order_index": step.order_index,
                "is_required": step.is_required,
                "estimated_time_minutes": step.estimated_time_minutes,
                "is_active": step.is_active,
                "created_at": step.created_at,
                "updated_at": step.updated_at
            }
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to update onboarding step: {str(e)}")
    
    async def delete_onboarding_step(
        self, 
        db: Session, 
        step_id: int
    ) -> Dict[str, str]:
        """Delete onboarding step"""
        try:
            step = db.query(OnboardingStep).filter(OnboardingStep.id == step_id).first()
            if not step:
                raise HTTPException(status_code=404, detail="Onboarding step not found")
            
            db.delete(step)
            db.commit()
            
            return {"message": "Onboarding step deleted successfully"}
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to delete onboarding step: {str(e)}")
    
    async def get_next_step(
        self, 
        db: Session, 
        current_step_id: int
    ) -> Dict[str, Any]:
        """Get the next onboarding step"""
        try:
            current_step = db.query(OnboardingStep).filter(OnboardingStep.id == current_step_id).first()
            if not current_step:
                raise HTTPException(status_code=404, detail="Current onboarding step not found")
            
            next_step = db.query(OnboardingStep).filter(
                and_(
                    OnboardingStep.order_index > current_step.order_index,
                    OnboardingStep.is_active == True
                )
            ).order_by(OnboardingStep.order_index).first()
            
            if not next_step:
                return {"message": "No next step available", "step": None}
            
            return {
                "id": next_step.id,
                "step_name": next_step.step_name,
                "step_type": next_step.step_type,
                "description": next_step.description,
                "content": next_step.content,
                "order_index": next_step.order_index,
                "is_required": next_step.is_required,
                "estimated_time_minutes": next_step.estimated_time_minutes,
                "is_active": next_step.is_active,
                "created_at": next_step.created_at,
                "updated_at": next_step.updated_at
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get next step: {str(e)}")
    
    async def create_onboarding_session(
        self, 
        db: Session, 
        user_id: int,
        step_id: int,
        status: str = "in_progress"
    ) -> Dict[str, Any]:
        """Create a new onboarding session"""
        try:
            session = OnboardingSession(
                user_id=user_id,
                step_id=step_id,
                status=status,
                started_at=datetime.utcnow(),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(session)
            db.commit()
            db.refresh(session)
            
            return {
                "id": session.id,
                "user_id": session.user_id,
                "step_id": session.step_id,
                "status": session.status,
                "started_at": session.started_at,
                "completed_at": session.completed_at,
                "notes": session.notes,
                "created_at": session.created_at,
                "updated_at": session.updated_at
            }
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to create onboarding session: {str(e)}")
    
    async def get_onboarding_session(
        self, 
        db: Session, 
        session_id: int
    ) -> Dict[str, Any]:
        """Get onboarding session by ID"""
        try:
            session = db.query(OnboardingSession).filter(OnboardingSession.id == session_id).first()
            if not session:
                raise HTTPException(status_code=404, detail="Onboarding session not found")
            
            return {
                "id": session.id,
                "user_id": session.user_id,
                "step_id": session.step_id,
                "status": session.status,
                "started_at": session.started_at,
                "completed_at": session.completed_at,
                "notes": session.notes,
                "created_at": session.created_at,
                "updated_at": session.updated_at
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get onboarding session: {str(e)}")
    
    async def list_onboarding_sessions(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        user_id: Optional[int] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List onboarding sessions"""
        try:
            query = db.query(OnboardingSession)
            
            if user_id:
                query = query.filter(OnboardingSession.user_id == user_id)
            if status:
                query = query.filter(OnboardingSession.status == status)
            
            sessions = query.order_by(desc(OnboardingSession.created_at)).offset(skip).limit(limit).all()
            
            return [
                {
                    "id": session.id,
                    "user_id": session.user_id,
                    "step_id": session.step_id,
                    "status": session.status,
                    "started_at": session.started_at,
                    "completed_at": session.completed_at,
                    "notes": session.notes,
                    "created_at": session.created_at,
                    "updated_at": session.updated_at
                } for session in sessions
            ]
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to list onboarding sessions: {str(e)}")
    
    async def update_onboarding_session(
        self, 
        db: Session, 
        session_id: int,
        status: Optional[str] = None,
        completed_at: Optional[datetime] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update onboarding session"""
        try:
            session = db.query(OnboardingSession).filter(OnboardingSession.id == session_id).first()
            if not session:
                raise HTTPException(status_code=404, detail="Onboarding session not found")
            
            if status is not None:
                session.status = status
            if completed_at is not None:
                session.completed_at = completed_at
            if notes is not None:
                session.notes = notes
            
            session.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(session)
            
            return {
                "id": session.id,
                "user_id": session.user_id,
                "step_id": session.step_id,
                "status": session.status,
                "started_at": session.started_at,
                "completed_at": session.completed_at,
                "notes": session.notes,
                "created_at": session.created_at,
                "updated_at": session.updated_at
            }
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to update onboarding session: {str(e)}")
    
    async def delete_onboarding_session(
        self, 
        db: Session, 
        session_id: int
    ) -> Dict[str, str]:
        """Delete onboarding session"""
        try:
            session = db.query(OnboardingSession).filter(OnboardingSession.id == session_id).first()
            if not session:
                raise HTTPException(status_code=404, detail="Onboarding session not found")
            
            db.delete(session)
            db.commit()
            
            return {"message": "Onboarding session deleted successfully"}
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to delete onboarding session: {str(e)}")
    
    async def create_onboarding_tutorial(
        self, 
        db: Session, 
        title: str,
        content: str,
        category: str,
        tags: Optional[List[str]] = None,
        difficulty_level: str = "beginner"
    ) -> Dict[str, Any]:
        """Create a new onboarding tutorial"""
        try:
            tutorial = OnboardingTutorial(
                title=title,
                content=content,
                category=category,
                tags=tags or [],
                difficulty_level=difficulty_level,
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(tutorial)
            db.commit()
            db.refresh(tutorial)
            
            return {
                "id": tutorial.id,
                "title": tutorial.title,
                "content": tutorial.content,
                "category": tutorial.category,
                "tags": tutorial.tags,
                "difficulty_level": tutorial.difficulty_level,
                "is_active": tutorial.is_active,
                "created_at": tutorial.created_at,
                "updated_at": tutorial.updated_at
            }
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to create onboarding tutorial: {str(e)}")
    
    async def get_onboarding_tutorial(
        self, 
        db: Session, 
        tutorial_id: int
    ) -> Dict[str, Any]:
        """Get onboarding tutorial by ID"""
        try:
            tutorial = db.query(OnboardingTutorial).filter(OnboardingTutorial.id == tutorial_id).first()
            if not tutorial:
                raise HTTPException(status_code=404, detail="Onboarding tutorial not found")
            
            return {
                "id": tutorial.id,
                "title": tutorial.title,
                "content": tutorial.content,
                "category": tutorial.category,
                "tags": tutorial.tags,
                "difficulty_level": tutorial.difficulty_level,
                "is_active": tutorial.is_active,
                "created_at": tutorial.created_at,
                "updated_at": tutorial.updated_at
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get onboarding tutorial: {str(e)}")
    
    async def list_onboarding_tutorials(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        category: Optional[str] = None,
        difficulty_level: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List onboarding tutorials"""
        try:
            query = db.query(OnboardingTutorial).filter(OnboardingTutorial.is_active == True)
            
            if category:
                query = query.filter(OnboardingTutorial.category == category)
            if difficulty_level:
                query = query.filter(OnboardingTutorial.difficulty_level == difficulty_level)
            
            tutorials = query.order_by(desc(OnboardingTutorial.created_at)).offset(skip).limit(limit).all()
            
            return [
                {
                    "id": tutorial.id,
                    "title": tutorial.title,
                    "content": tutorial.content,
                    "category": tutorial.category,
                    "tags": tutorial.tags,
                    "difficulty_level": tutorial.difficulty_level,
                    "is_active": tutorial.is_active,
                    "created_at": tutorial.created_at,
                    "updated_at": tutorial.updated_at
                } for tutorial in tutorials
            ]
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to list onboarding tutorials: {str(e)}")
    
    async def update_onboarding_tutorial(
        self, 
        db: Session, 
        tutorial_id: int,
        title: Optional[str] = None,
        content: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        difficulty_level: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update onboarding tutorial"""
        try:
            tutorial = db.query(OnboardingTutorial).filter(OnboardingTutorial.id == tutorial_id).first()
            if not tutorial:
                raise HTTPException(status_code=404, detail="Onboarding tutorial not found")
            
            if title is not None:
                tutorial.title = title
            if content is not None:
                tutorial.content = content
            if category is not None:
                tutorial.category = category
            if tags is not None:
                tutorial.tags = tags
            if difficulty_level is not None:
                tutorial.difficulty_level = difficulty_level
            
            tutorial.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(tutorial)
            
            return {
                "id": tutorial.id,
                "title": tutorial.title,
                "content": tutorial.content,
                "category": tutorial.category,
                "tags": tutorial.tags,
                "difficulty_level": tutorial.difficulty_level,
                "is_active": tutorial.is_active,
                "created_at": tutorial.created_at,
                "updated_at": tutorial.updated_at
            }
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to update onboarding tutorial: {str(e)}")
    
    async def delete_onboarding_tutorial(
        self, 
        db: Session, 
        tutorial_id: int
    ) -> Dict[str, str]:
        """Delete onboarding tutorial"""
        try:
            tutorial = db.query(OnboardingTutorial).filter(OnboardingTutorial.id == tutorial_id).first()
            if not tutorial:
                raise HTTPException(status_code=404, detail="Onboarding tutorial not found")
            
            db.delete(tutorial)
            db.commit()
            
            return {"message": "Onboarding tutorial deleted successfully"}
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to delete onboarding tutorial: {str(e)}")
    
    async def search_onboarding_tutorials(
        self, 
        db: Session, 
        query: str,
        category: Optional[str] = None,
        difficulty_level: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search onboarding tutorials"""
        try:
            # Use semantic search to find relevant tutorials
            results = await self.nlp_utils.semantic_search_tutorials(db, query, limit)
            
            # Filter by category if specified
            if category:
                results = [r for r in results if r.get('category') == category]
            
            # Filter by difficulty level if specified
            if difficulty_level:
                results = [r for r in results if r.get('difficulty_level') == difficulty_level]
            
            return results
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to search onboarding tutorials: {str(e)}")
    
    async def get_onboarding_progress(
        self, 
        db: Session, 
        user_id: int
    ) -> Dict[str, Any]:
        """Get user's onboarding progress"""
        try:
            # Get user's sessions
            sessions = db.query(OnboardingSession).filter(OnboardingSession.user_id == user_id).all()
            
            # Get all active steps
            total_steps = db.query(OnboardingStep).filter(OnboardingStep.is_active == True).count()
            
            # Calculate completed steps
            completed_sessions = [s for s in sessions if s.status == "completed"]
            completed_steps = len(completed_sessions)
            
            # Calculate progress percentage
            progress_percentage = (completed_steps / total_steps * 100) if total_steps > 0 else 0
            
            # Get current step
            current_session = db.query(OnboardingSession).filter(
                and_(
                    OnboardingSession.user_id == user_id,
                    OnboardingSession.status == "in_progress"
                )
            ).first()
            
            current_step = None
            if current_session:
                current_step = db.query(OnboardingStep).filter(OnboardingStep.id == current_session.step_id).first()
            
            return {
                "user_id": user_id,
                "total_steps": total_steps,
                "completed_steps": completed_steps,
                "progress_percentage": progress_percentage,
                "current_step": {
                    "id": current_step.id,
                    "step_name": current_step.step_name,
                    "step_type": current_step.step_type,
                    "description": current_step.description
                } if current_step else None,
                "sessions": [
                    {
                        "id": session.id,
                        "step_id": session.step_id,
                        "status": session.status,
                        "started_at": session.started_at,
                        "completed_at": session.completed_at
                    } for session in sessions
                ]
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get onboarding progress: {str(e)}")
    
    async def calculate_onboarding_progress(
        self, 
        db: Session, 
        user_id: int
    ) -> Dict[str, Any]:
        """Calculate user's onboarding progress"""
        try:
            # Calculate comprehensive onboarding progress with weighted scoring
            session = db.query(OnboardingSession).filter(OnboardingSession.user_id == user_id).first()
            if not session:
                return {"progress_percentage": 0, "completed_steps": 0, "total_steps": 0, "current_step": None}
            
            # Get all steps for this user's onboarding flow
            steps = db.query(OnboardingStep).filter(
                OnboardingStep.onboarding_flow_id == session.onboarding_flow_id,
                OnboardingStep.is_active == True
            ).order_by(OnboardingStep.step_order).all()
            
            if not steps:
                return {"progress_percentage": 0, "completed_steps": 0, "total_steps": 0, "current_step": None}
            
            # Calculate weighted progress based on step importance
            total_weight = sum(step.importance_score for step in steps)
            completed_weight = 0
            completed_steps = 0
            
            for step in steps:
                step_session = db.query(OnboardingSession).filter(
                    OnboardingSession.user_id == user_id,
                    OnboardingSession.step_id == step.id,
                    OnboardingSession.status == "completed"
                ).first()
                
                if step_session:
                    completed_weight += step.importance_score
                    completed_steps += 1
            
            progress_percentage = (completed_weight / total_weight * 100) if total_weight > 0 else 0
            
            # Find current step (next incomplete step)
            current_step = None
            for step in steps:
                step_session = db.query(OnboardingSession).filter(
                    OnboardingSession.user_id == user_id,
                    OnboardingSession.step_id == step.id,
                    OnboardingSession.status == "completed"
                ).first()
                
                if not step_session:
                    current_step = {
                        "step_id": step.id,
                        "step_name": step.step_name,
                        "step_order": step.step_order,
                        "description": step.description
                    }
                    break
            
            return {
                "progress_percentage": round(progress_percentage, 2),
                "completed_steps": completed_steps,
                "total_steps": len(steps),
                "current_step": current_step,
                "weighted_score": completed_weight,
                "total_weight": total_weight
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to calculate onboarding progress: {str(e)}")
    
    async def get_onboarding_analytics(
        self, 
        db: Session, 
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get onboarding analytics"""
        try:
            # Get sessions in date range
            sessions = db.query(OnboardingSession).filter(
                and_(
                    OnboardingSession.created_at >= start_date,
                    OnboardingSession.created_at <= end_date
                )
            ).all()
            
            # Calculate metrics
            total_sessions = len(sessions)
            completed_sessions = len([s for s in sessions if s.status == "completed"])
            in_progress_sessions = len([s for s in sessions if s.status == "in_progress"])
            
            # Calculate average completion time
            completion_times = []
            for session in completed_sessions:
                if session.completed_at and session.started_at:
                    completion_time = (session.completed_at - session.started_at).total_seconds() / 60  # minutes
                    completion_times.append(completion_time)
            
            avg_completion_time = sum(completion_times) / len(completion_times) if completion_times else 0
            
            # Step completion breakdown
            step_completion = {}
            for session in sessions:
                step = db.query(OnboardingStep).filter(OnboardingStep.id == session.step_id).first()
                if step:
                    step_name = step.step_name
                    if step_name not in step_completion:
                        step_completion[step_name] = {"total": 0, "completed": 0}
                    step_completion[step_name]["total"] += 1
                    if session.status == "completed":
                        step_completion[step_name]["completed"] += 1
            
            return {
                "period_start": start_date,
                "period_end": end_date,
                "total_sessions": total_sessions,
                "completed_sessions": completed_sessions,
                "in_progress_sessions": in_progress_sessions,
                "completion_rate": completed_sessions / total_sessions if total_sessions > 0 else 0,
                "avg_completion_time_minutes": avg_completion_time,
                "step_completion_breakdown": step_completion
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get onboarding analytics: {str(e)}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check the health of onboarding assistance system"""
        try:
            db = next(get_db())
            step_count = db.query(OnboardingStep).count()
            session_count = db.query(OnboardingSession).count()
            tutorial_count = db.query(OnboardingTutorial).count()
            
            return {
                "status": "healthy",
                "database": {
                    "connected": True,
                    "steps_count": step_count,
                    "sessions_count": session_count,
                    "tutorials_count": tutorial_count
                },
                "last_check": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "last_check": datetime.utcnow().isoformat()
            }
