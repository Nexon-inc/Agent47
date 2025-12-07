from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from fastapi import HTTPException, BackgroundTasks
import json
import asyncio
from enum import Enum

from ..models import (
    AgentTraining, TrainingModule, TrainingSession, AgentPerformance,
    TrainingAssessment, SupportAgent, CustomerInteraction, SupportTicket
)
from ..schemas.agent_training import (
    CreateTrainingModuleRequest, UpdateTrainingModuleRequest,
    CreateTrainingSessionRequest, StartTrainingSessionRequest,
    CompleteTrainingSessionRequest, CreateAssessmentRequest,
    TrainingModuleResponse, TrainingSessionResponse, AgentPerformanceResponse,
    TrainingAssessmentResponse, TrainingAnalyticsResponse
)
from ..database import get_clara_database
from ..core.config import settings
from ..core.integrations import IntegrationManager
from ..core.analytics import AnalyticsManager
from ..core.nlp import NLPUtils


class TrainingStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class AssessmentType(str, Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    SCENARIO_BASED = "scenario_based"
    PRACTICAL_EXERCISE = "practical_exercise"
    PEER_REVIEW = "peer_review"


class AgentTrainingService:
    def __init__(self):
        self.integration_manager = IntegrationManager()
        self.analytics_manager = AnalyticsManager()
        # NLPUtils removed - not used in this service
        
    async def create_training_module(
        self, 
        db: Session, 
        request: CreateTrainingModuleRequest
    ) -> TrainingModuleResponse:
        """Create a new training module"""
        try:
            module = TrainingModule(
                title=request.title,
                description=request.description,
                content=request.content,
                duration_minutes=request.duration_minutes,
                difficulty_level=request.difficulty_level,
                prerequisites=request.prerequisites,
                learning_objectives=request.learning_objectives,
                is_active=request.is_active,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(module)
            db.commit()
            db.refresh(module)
            
            # Log module creation
            await self._log_training_event("module_created", {
                "module_id": module.id,
                "title": module.title,
                "difficulty": module.difficulty_level
            })
            
            return TrainingModuleResponse(
                id=module.id,
                title=module.title,
                description=module.description,
                content=module.content,
                duration_minutes=module.duration_minutes,
                difficulty_level=module.difficulty_level,
                prerequisites=module.prerequisites,
                learning_objectives=module.learning_objectives,
                is_active=module.is_active,
                created_at=module.created_at,
                updated_at=module.updated_at
            )
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to create training module: {str(e)}")
    
    async def get_training_module(
        self, 
        db: Session, 
        module_id: int
    ) -> TrainingModuleResponse:
        """Get a training module by ID"""
        module = db.query(TrainingModule).filter(TrainingModule.id == module_id).first()
        if not module:
            raise HTTPException(status_code=404, detail="Training module not found")
        
        return TrainingModuleResponse(
            id=module.id,
            title=module.title,
            description=module.description,
            content=module.content,
            duration_minutes=module.duration_minutes,
            difficulty_level=module.difficulty_level,
            prerequisites=module.prerequisites,
            learning_objectives=module.learning_objectives,
            is_active=module.is_active,
            created_at=module.created_at,
            updated_at=module.updated_at
        )
    
    async def list_training_modules(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        difficulty_level: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[TrainingModuleResponse]:
        """List training modules with optional filtering"""
        query = db.query(TrainingModule)
        
        if difficulty_level:
            query = query.filter(TrainingModule.difficulty_level == difficulty_level)
        if is_active is not None:
            query = query.filter(TrainingModule.is_active == is_active)
        
        modules = query.offset(skip).limit(limit).all()
        
        return [
            TrainingModuleResponse(
                id=module.id,
                title=module.title,
                description=module.description,
                content=module.content,
                duration_minutes=module.duration_minutes,
                difficulty_level=module.difficulty_level,
                prerequisites=module.prerequisites,
                learning_objectives=module.learning_objectives,
                is_active=module.is_active,
                created_at=module.created_at,
                updated_at=module.updated_at
            ) for module in modules
        ]
    
    async def update_training_module(
        self, 
        db: Session, 
        module_id: int, 
        request: UpdateTrainingModuleRequest
    ) -> TrainingModuleResponse:
        """Update a training module"""
        module = db.query(TrainingModule).filter(TrainingModule.id == module_id).first()
        if not module:
            raise HTTPException(status_code=404, detail="Training module not found")
        
        try:
            if request.title is not None:
                module.title = request.title
            if request.description is not None:
                module.description = request.description
            if request.content is not None:
                module.content = request.content
            if request.duration_minutes is not None:
                module.duration_minutes = request.duration_minutes
            if request.difficulty_level is not None:
                module.difficulty_level = request.difficulty_level
            if request.prerequisites is not None:
                module.prerequisites = request.prerequisites
            if request.learning_objectives is not None:
                module.learning_objectives = request.learning_objectives
            if request.is_active is not None:
                module.is_active = request.is_active
            
            module.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(module)
            
            return TrainingModuleResponse(
                id=module.id,
                title=module.title,
                description=module.description,
                content=module.content,
                duration_minutes=module.duration_minutes,
                difficulty_level=module.difficulty_level,
                prerequisites=module.prerequisites,
                learning_objectives=module.learning_objectives,
                is_active=module.is_active,
                created_at=module.created_at,
                updated_at=module.updated_at
            )
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to update training module: {str(e)}")
    
    async def delete_training_module(
        self, 
        db: Session, 
        module_id: int
    ) -> Dict[str, str]:
        """Delete a training module"""
        module = db.query(TrainingModule).filter(TrainingModule.id == module_id).first()
        if not module:
            raise HTTPException(status_code=404, detail="Training module not found")
        
        try:
            db.delete(module)
            db.commit()
            return {"message": "Training module deleted successfully"}
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to delete training module: {str(e)}")
    
    async def create_training_session(
        self, 
        db: Session, 
        request: CreateTrainingSessionRequest
    ) -> TrainingSessionResponse:
        """Create a new training session"""
        try:
            # Verify agent exists
            agent = db.query(SupportAgent).filter(SupportAgent.id == request.agent_id).first()
            if not agent:
                raise HTTPException(status_code=404, detail="Agent not found")
            
            # Verify module exists
            module = db.query(TrainingModule).filter(TrainingModule.id == request.module_id).first()
            if not module:
                raise HTTPException(status_code=404, detail="Training module not found")
            
            session = TrainingSession(
                agent_id=request.agent_id,
                module_id=request.module_id,
                status=TrainingStatus.NOT_STARTED,
                start_time=None,
                end_time=None,
                progress_percentage=0.0,
                score=None,
                feedback=None,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(session)
            db.commit()
            db.refresh(session)
            
            return TrainingSessionResponse(
                id=session.id,
                agent_id=session.agent_id,
                module_id=session.module_id,
                status=session.status,
                start_time=session.start_time,
                end_time=session.end_time,
                progress_percentage=session.progress_percentage,
                score=session.score,
                feedback=session.feedback,
                created_at=session.created_at,
                updated_at=session.updated_at
            )
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to create training session: {str(e)}")
    
    async def start_training_session(
        self, 
        db: Session, 
        session_id: int, 
        request: StartTrainingSessionRequest
    ) -> TrainingSessionResponse:
        """Start a training session"""
        session = db.query(TrainingSession).filter(TrainingSession.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Training session not found")
        
        if session.status != TrainingStatus.NOT_STARTED:
            raise HTTPException(status_code=400, detail="Session cannot be started")
        
        try:
            session.status = TrainingStatus.IN_PROGRESS
            session.start_time = datetime.utcnow()
            session.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(session)
            
            # Log session start
            await self._log_training_event("session_started", {
                "session_id": session.id,
                "agent_id": session.agent_id,
                "module_id": session.module_id
            })
            
            return TrainingSessionResponse(
                id=session.id,
                agent_id=session.agent_id,
                module_id=session.module_id,
                status=session.status,
                start_time=session.start_time,
                end_time=session.end_time,
                progress_percentage=session.progress_percentage,
                score=session.score,
                feedback=session.feedback,
                created_at=session.created_at,
                updated_at=session.updated_at
            )
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to start training session: {str(e)}")
    
    async def complete_training_session(
        self, 
        db: Session, 
        session_id: int, 
        request: CompleteTrainingSessionRequest
    ) -> TrainingSessionResponse:
        """Complete a training session"""
        session = db.query(TrainingSession).filter(TrainingSession.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Training session not found")
        
        if session.status != TrainingStatus.IN_PROGRESS:
            raise HTTPException(status_code=400, detail="Session is not in progress")
        
        try:
            session.status = TrainingStatus.COMPLETED
            session.end_time = datetime.utcnow()
            session.progress_percentage = 100.0
            session.score = request.score
            session.feedback = request.feedback
            session.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(session)
            
            # Update agent performance
            await self._update_agent_performance(db, session.agent_id, session.module_id, request.score)
            
            # Log session completion
            await self._log_training_event("session_completed", {
                "session_id": session.id,
                "agent_id": session.agent_id,
                "module_id": session.module_id,
                "score": request.score
            })
            
            return TrainingSessionResponse(
                id=session.id,
                agent_id=session.agent_id,
                module_id=session.module_id,
                status=session.status,
                start_time=session.start_time,
                end_time=session.end_time,
                progress_percentage=session.progress_percentage,
                score=session.score,
                feedback=session.feedback,
                created_at=session.created_at,
                updated_at=session.updated_at
            )
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to complete training session: {str(e)}")
    
    async def get_training_session(
        self, 
        db: Session, 
        session_id: int
    ) -> TrainingSessionResponse:
        """Get a training session by ID"""
        session = db.query(TrainingSession).filter(TrainingSession.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Training session not found")
        
        return TrainingSessionResponse(
            id=session.id,
            agent_id=session.agent_id,
            module_id=session.module_id,
            status=session.status,
            start_time=session.start_time,
            end_time=session.end_time,
            progress_percentage=session.progress_percentage,
            score=session.score,
            feedback=session.feedback,
            created_at=session.created_at,
            updated_at=session.updated_at
        )
    
    async def list_agent_training_sessions(
        self, 
        db: Session, 
        agent_id: int,
        skip: int = 0, 
        limit: int = 100
    ) -> List[TrainingSessionResponse]:
        """List training sessions for an agent"""
        sessions = db.query(TrainingSession).filter(
            TrainingSession.agent_id == agent_id
        ).offset(skip).limit(limit).all()
        
        return [
            TrainingSessionResponse(
                id=session.id,
                agent_id=session.agent_id,
                module_id=session.module_id,
                status=session.status,
                start_time=session.start_time,
                end_time=session.end_time,
                progress_percentage=session.progress_percentage,
                score=session.score,
                feedback=session.feedback,
                created_at=session.created_at,
                updated_at=session.updated_at
            ) for session in sessions
        ]
    
    async def create_training_assessment(
        self, 
        db: Session, 
        request: CreateAssessmentRequest
    ) -> TrainingAssessmentResponse:
        """Create a new training assessment"""
        try:
            assessment = TrainingAssessment(
                title=request.title,
                description=request.description,
                assessment_type=request.assessment_type,
                questions=request.questions,
                passing_score=request.passing_score,
                time_limit_minutes=request.time_limit_minutes,
                is_active=request.is_active,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(assessment)
            db.commit()
            db.refresh(assessment)
            
            return TrainingAssessmentResponse(
                id=assessment.id,
                title=assessment.title,
                description=assessment.description,
                assessment_type=assessment.assessment_type,
                questions=assessment.questions,
                passing_score=assessment.passing_score,
                time_limit_minutes=assessment.time_limit_minutes,
                is_active=assessment.is_active,
                created_at=assessment.created_at,
                updated_at=assessment.updated_at
            )
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to create training assessment: {str(e)}")
    
    async def get_training_assessment(
        self, 
        db: Session, 
        assessment_id: int
    ) -> TrainingAssessmentResponse:
        """Get a training assessment by ID"""
        assessment = db.query(TrainingAssessment).filter(TrainingAssessment.id == assessment_id).first()
        if not assessment:
            raise HTTPException(status_code=404, detail="Training assessment not found")
        
        return TrainingAssessmentResponse(
            id=assessment.id,
            title=assessment.title,
            description=assessment.description,
            assessment_type=assessment.assessment_type,
            questions=assessment.questions,
            passing_score=assessment.passing_score,
            time_limit_minutes=assessment.time_limit_minutes,
            is_active=assessment.is_active,
            created_at=assessment.created_at,
            updated_at=assessment.updated_at
        )
    
    async def list_training_assessments(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        assessment_type: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[TrainingAssessmentResponse]:
        """List training assessments with optional filtering"""
        query = db.query(TrainingAssessment)
        
        if assessment_type:
            query = query.filter(TrainingAssessment.assessment_type == assessment_type)
        if is_active is not None:
            query = query.filter(TrainingAssessment.is_active == is_active)
        
        assessments = query.offset(skip).limit(limit).all()
        
        return [
            TrainingAssessmentResponse(
                id=assessment.id,
                title=assessment.title,
                description=assessment.description,
                assessment_type=assessment.assessment_type,
                questions=assessment.questions,
                passing_score=assessment.passing_score,
                time_limit_minutes=assessment.time_limit_minutes,
                is_active=assessment.is_active,
                created_at=assessment.created_at,
                updated_at=assessment.updated_at
            ) for assessment in assessments
        ]
    
    async def get_agent_performance(
        self, 
        db: Session, 
        agent_id: int
    ) -> AgentPerformanceResponse:
        """Get agent performance metrics"""
        try:
            # Get agent
            agent = db.query(SupportAgent).filter(SupportAgent.id == agent_id).first()
            if not agent:
                raise HTTPException(status_code=404, detail="Agent not found")
            
            # Get performance record
            performance = db.query(AgentPerformance).filter(
                AgentPerformance.agent_id == agent_id
            ).first()
            
            if not performance:
                # Create new performance record
                performance = AgentPerformance(
                    agent_id=agent_id,
                    total_training_hours=0,
                    completed_modules=0,
                    average_score=0.0,
                    skills_acquired=[],
                    areas_for_improvement=[],
                    last_assessment_date=None,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.add(performance)
                db.commit()
                db.refresh(performance)
            
            # Calculate recent metrics
            recent_sessions = db.query(TrainingSession).filter(
                and_(
                    TrainingSession.agent_id == agent_id,
                    TrainingSession.created_at >= datetime.utcnow() - timedelta(days=30)
                )
            ).all()
            
            recent_score = 0.0
            if recent_sessions:
                recent_score = sum(s.score or 0 for s in recent_sessions) / len(recent_sessions)
            
            return AgentPerformanceResponse(
                agent_id=performance.agent_id,
                total_training_hours=performance.total_training_hours,
                completed_modules=performance.completed_modules,
                average_score=performance.average_score,
                recent_score=recent_score,
                skills_acquired=performance.skills_acquired,
                areas_for_improvement=performance.areas_for_improvement,
                last_assessment_date=performance.last_assessment_date,
                created_at=performance.created_at,
                updated_at=performance.updated_at
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get agent performance: {str(e)}")
    
    async def ai_driven_coaching(
        self, 
        db: Session, 
        agent_id: int
    ) -> Dict[str, Any]:
        """Provide AI-driven coaching recommendations"""
        try:
            # Get agent performance
            performance = await self.get_agent_performance(db, agent_id)
            
            # Get recent interactions
            recent_interactions = db.query(CustomerInteraction).filter(
                and_(
                    CustomerInteraction.agent_id == agent_id,
                    CustomerInteraction.created_at >= datetime.utcnow() - timedelta(days=7)
                )
            ).all()
            
            # Analyze interaction patterns
            sentiment_scores = [i.sentiment_score for i in recent_interactions if i.sentiment_score]
            response_times = [i.response_time for i in recent_interactions if i.response_time]
            
            # Generate coaching recommendations
            recommendations = []
            
            # Sentiment analysis recommendations
            if sentiment_scores:
                avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
                if avg_sentiment < 0.6:
                    recommendations.append({
                        "type": "sentiment_improvement",
                        "priority": "high",
                        "title": "Improve Customer Sentiment",
                        "description": "Focus on more empathetic and positive communication",
                        "suggested_actions": [
                            "Use more positive language",
                            "Acknowledge customer feelings",
                            "Provide reassurance when appropriate"
                        ]
                    })
            
            # Response time recommendations
            if response_times:
                avg_response_time = sum(response_times) / len(response_times)
                if avg_response_time > 300:  # 5 minutes
                    recommendations.append({
                        "type": "response_time",
                        "priority": "medium",
                        "title": "Improve Response Time",
                        "description": "Work on responding to customers more quickly",
                        "suggested_actions": [
                            "Use response templates for common issues",
                            "Prioritize urgent tickets",
                            "Improve typing speed"
                        ]
                    })
            
            # Training recommendations based on performance
            if performance.average_score < 0.7:
                recommendations.append({
                    "type": "additional_training",
                    "priority": "high",
                    "title": "Additional Training Recommended",
                    "description": "Consider completing more training modules",
                    "suggested_actions": [
                        "Review basic support procedures",
                        "Complete advanced communication training",
                        "Practice with scenario-based exercises"
                    ]
                })
            
            # Skill gap recommendations
            if performance.areas_for_improvement:
                recommendations.append({
                    "type": "skill_gap",
                    "priority": "medium",
                    "title": "Address Skill Gaps",
                    "description": "Focus on identified areas for improvement",
                    "suggested_actions": performance.areas_for_improvement
                })
            
            return {
                "agent_id": agent_id,
                "recommendations": recommendations,
                "performance_summary": {
                    "average_score": performance.average_score,
                    "recent_score": performance.recent_score,
                    "completed_modules": performance.completed_modules,
                    "total_training_hours": performance.total_training_hours
                },
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to generate AI coaching: {str(e)}")
    
    async def skill_gap_analysis(
        self, 
        db: Session, 
        agent_id: int
    ) -> Dict[str, Any]:
        """Analyze agent skill gaps"""
        try:
            # Get agent performance
            performance = await self.get_agent_performance(db, agent_id)
            
            # Get recent tickets handled by agent
            recent_tickets = db.query(SupportTicket).filter(
                and_(
                    SupportTicket.assigned_agent_id == agent_id,
                    SupportTicket.created_at >= datetime.utcnow() - timedelta(days=30)
                )
            ).all()
            
            # Analyze ticket categories and outcomes
            category_performance = {}
            for ticket in recent_tickets:
                category = ticket.category
                if category not in category_performance:
                    category_performance[category] = {
                        "total": 0,
                        "resolved": 0,
                        "escalated": 0,
                        "avg_resolution_time": 0
                    }
                
                category_performance[category]["total"] += 1
                if ticket.status == "resolved":
                    category_performance[category]["resolved"] += 1
                elif ticket.status == "escalated":
                    category_performance[category]["escalated"] += 1
                
                if ticket.resolved_at and ticket.created_at:
                    resolution_time = (ticket.resolved_at - ticket.created_at).total_seconds() / 3600  # hours
                    category_performance[category]["avg_resolution_time"] += resolution_time
            
            # Calculate success rates and identify gaps
            skill_gaps = []
            for category, stats in category_performance.items():
                if stats["total"] > 0:
                    success_rate = stats["resolved"] / stats["total"]
                    escalation_rate = stats["escalated"] / stats["total"]
                    avg_time = stats["avg_resolution_time"] / stats["total"]
                    
                    if success_rate < 0.8:
                        skill_gaps.append({
                            "category": category,
                            "type": "low_success_rate",
                            "severity": "high" if success_rate < 0.6 else "medium",
                            "current_rate": success_rate,
                            "target_rate": 0.8,
                            "description": f"Low success rate in {category} tickets"
                        })
                    
                    if escalation_rate > 0.2:
                        skill_gaps.append({
                            "category": category,
                            "type": "high_escalation_rate",
                            "severity": "high" if escalation_rate > 0.3 else "medium",
                            "current_rate": escalation_rate,
                            "target_rate": 0.2,
                            "description": f"High escalation rate in {category} tickets"
                        })
                    
                    if avg_time > 24:  # More than 24 hours
                        skill_gaps.append({
                            "category": category,
                            "type": "slow_resolution",
                            "severity": "medium",
                            "current_time": avg_time,
                            "target_time": 24,
                            "description": f"Slow resolution time for {category} tickets"
                        })
            
            return {
                "agent_id": agent_id,
                "skill_gaps": skill_gaps,
                "category_performance": category_performance,
                "overall_assessment": {
                    "total_tickets": sum(stats["total"] for stats in category_performance.values()),
                    "overall_success_rate": sum(stats["resolved"] for stats in category_performance.values()) / 
                                          sum(stats["total"] for stats in category_performance.values()) if category_performance else 0,
                    "gaps_identified": len(skill_gaps)
                },
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to analyze skill gaps: {str(e)}")
    
    async def personalized_learning_path(
        self, 
        db: Session, 
        agent_id: int
    ) -> Dict[str, Any]:
        """Generate personalized learning path for agent"""
        try:
            # Get skill gap analysis
            skill_gaps = await self.skill_gap_analysis(db, agent_id)
            
            # Get available training modules
            available_modules = await self.list_training_modules(db, is_active=True)
            
            # Match modules to skill gaps
            recommended_modules = []
            for gap in skill_gaps["skill_gaps"]:
                category = gap["category"]
                gap_type = gap["type"]
                
                # Find relevant modules
                for module in available_modules:
                    if self._module_matches_gap(module, category, gap_type):
                        recommended_modules.append({
                            "module_id": module.id,
                            "title": module.title,
                            "difficulty": module.difficulty_level,
                            "duration": module.duration_minutes,
                            "addresses_gap": gap,
                            "priority": gap["severity"]
                        })
            
            # Sort by priority and difficulty
            recommended_modules.sort(key=lambda x: (
                {"high": 0, "medium": 1, "low": 2}[x["priority"]],
                {"beginner": 0, "intermediate": 1, "advanced": 2}[x["difficulty"]]
            ))
            
            # Create learning path
            learning_path = {
                "agent_id": agent_id,
                "estimated_duration_hours": sum(m["duration"] for m in recommended_modules) / 60,
                "modules": recommended_modules[:10],  # Top 10 recommendations
                "milestones": self._create_milestones(recommended_modules),
                "generated_at": datetime.utcnow().isoformat()
            }
            
            return learning_path
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to generate learning path: {str(e)}")
    
    async def gamification_features(
        self, 
        db: Session, 
        agent_id: int
    ) -> Dict[str, Any]:
        """Get gamification features for agent"""
        try:
            # Get agent performance
            performance = await self.get_agent_performance(db, agent_id)
            
            # Get recent training sessions
            recent_sessions = db.query(TrainingSession).filter(
                and_(
                    TrainingSession.agent_id == agent_id,
                    TrainingSession.status == TrainingStatus.COMPLETED,
                    TrainingSession.created_at >= datetime.utcnow() - timedelta(days=30)
                )
            ).all()
            
            # Calculate points and achievements
            total_points = 0
            achievements = []
            
            # Points for completed modules
            for session in recent_sessions:
                if session.score:
                    points = int(session.score * 100)
                    total_points += points
                    
                    if session.score >= 0.9:
                        achievements.append({
                            "type": "excellent_score",
                            "title": "Excellent Performance",
                            "description": f"Scored {session.score*100}% on training module",
                            "points": points,
                            "earned_at": session.end_time.isoformat()
                        })
                    elif session.score >= 0.8:
                        achievements.append({
                            "type": "good_score",
                            "title": "Good Performance",
                            "description": f"Scored {session.score*100}% on training module",
                            "points": points,
                            "earned_at": session.end_time.isoformat()
                        })
            
            # Points for training hours
            training_hours = performance.total_training_hours
            if training_hours >= 10:
                achievements.append({
                    "type": "dedicated_learner",
                    "title": "Dedicated Learner",
                    "description": "Completed 10+ hours of training",
                    "points": 500,
                    "earned_at": datetime.utcnow().isoformat()
                })
            
            # Points for completed modules
            if performance.completed_modules >= 5:
                achievements.append({
                    "type": "module_master",
                    "title": "Module Master",
                    "description": f"Completed {performance.completed_modules} training modules",
                    "points": 300,
                    "earned_at": datetime.utcnow().isoformat()
                })
            
            # Calculate level
            level = (total_points // 1000) + 1
            
            # Get leaderboard position
            all_agents = db.query(AgentPerformance).order_by(desc(AgentPerformance.average_score)).all()
            leaderboard_position = next((i + 1 for i, p in enumerate(all_agents) if p.agent_id == agent_id), None)
            
            return {
                "agent_id": agent_id,
                "total_points": total_points,
                "level": level,
                "achievements": achievements,
                "leaderboard_position": leaderboard_position,
                "recent_activity": {
                    "sessions_completed": len(recent_sessions),
                    "points_earned": total_points,
                    "achievements_earned": len(achievements)
                },
                "next_milestones": self._get_next_milestones(total_points, performance),
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get gamification features: {str(e)}")
    
    async def get_training_analytics(
        self, 
        db: Session, 
        start_date: datetime,
        end_date: datetime
    ) -> TrainingAnalyticsResponse:
        """Get comprehensive training analytics"""
        try:
            # Get training sessions in date range
            sessions = db.query(TrainingSession).filter(
                and_(
                    TrainingSession.created_at >= start_date,
                    TrainingSession.created_at <= end_date
                )
            ).all()
            
            # Calculate metrics
            total_sessions = len(sessions)
            completed_sessions = len([s for s in sessions if s.status == TrainingStatus.COMPLETED])
            in_progress_sessions = len([s for s in sessions if s.status == TrainingStatus.IN_PROGRESS])
            failed_sessions = len([s for s in sessions if s.status == TrainingStatus.FAILED])
            
            # Average scores
            completed_with_scores = [s for s in sessions if s.status == TrainingStatus.COMPLETED and s.score]
            average_score = sum(s.score for s in completed_with_scores) / len(completed_with_scores) if completed_with_scores else 0
            
            # Module popularity
            module_stats = {}
            for session in sessions:
                module_id = session.module_id
                if module_id not in module_stats:
                    module_stats[module_id] = {"total": 0, "completed": 0, "avg_score": 0}
                module_stats[module_id]["total"] += 1
                if session.status == TrainingStatus.COMPLETED:
                    module_stats[module_id]["completed"] += 1
                    if session.score:
                        module_stats[module_id]["avg_score"] += session.score
            
            # Calculate averages
            for module_id in module_stats:
                if module_stats[module_id]["completed"] > 0:
                    module_stats[module_id]["avg_score"] /= module_stats[module_id]["completed"]
            
            # Daily trends
            daily_stats = {}
            for session in sessions:
                date_key = session.created_at.date().isoformat()
                if date_key not in daily_stats:
                    daily_stats[date_key] = {"total": 0, "completed": 0, "avg_score": 0}
                daily_stats[date_key]["total"] += 1
                if session.status == TrainingStatus.COMPLETED:
                    daily_stats[date_key]["completed"] += 1
                    if session.score:
                        daily_stats[date_key]["avg_score"] += session.score
            
            # Calculate daily averages
            for date_key in daily_stats:
                if daily_stats[date_key]["completed"] > 0:
                    daily_stats[date_key]["avg_score"] /= daily_stats[date_key]["completed"]
            
            return TrainingAnalyticsResponse(
                period_start=start_date,
                period_end=end_date,
                total_sessions=total_sessions,
                completed_sessions=completed_sessions,
                in_progress_sessions=in_progress_sessions,
                failed_sessions=failed_sessions,
                completion_rate=completed_sessions / total_sessions if total_sessions > 0 else 0,
                average_score=average_score,
                module_breakdown=module_stats,
                daily_trends=daily_stats
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get training analytics: {str(e)}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check the health of agent training system"""
        try:
            # Check database connectivity
            db = next(get_db())
            module_count = db.query(TrainingModule).count()
            session_count = db.query(TrainingSession).count()
            assessment_count = db.query(TrainingAssessment).count()
            active_sessions = db.query(TrainingSession).filter(
                TrainingSession.status == TrainingStatus.IN_PROGRESS
            ).count()
            
            return {
                "status": "healthy",
                "database": {
                    "connected": True,
                    "modules_count": module_count,
                    "sessions_count": session_count,
                    "assessments_count": assessment_count,
                    "active_sessions": active_sessions
                },
                "last_check": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "last_check": datetime.utcnow().isoformat()
            }
    
    async def _update_agent_performance(
        self, 
        db: Session, 
        agent_id: int, 
        module_id: int, 
        score: float
    ):
        """Update agent performance after training completion"""
        try:
            performance = db.query(AgentPerformance).filter(
                AgentPerformance.agent_id == agent_id
            ).first()
            
            if not performance:
                performance = AgentPerformance(
                    agent_id=agent_id,
                    total_training_hours=0,
                    completed_modules=0,
                    average_score=0.0,
                    skills_acquired=[],
                    areas_for_improvement=[],
                    last_assessment_date=None,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.add(performance)
            
            # Update metrics
            performance.completed_modules += 1
            performance.average_score = (
                (performance.average_score * (performance.completed_modules - 1) + score) / 
                performance.completed_modules
            )
            performance.last_assessment_date = datetime.utcnow()
            performance.updated_at = datetime.utcnow()
            
            # Get module to update training hours
            module = db.query(TrainingModule).filter(TrainingModule.id == module_id).first()
            if module:
                performance.total_training_hours += module.duration_minutes / 60
            
            db.commit()
            
        except Exception as e:
            db.rollback()
            raise e
    
    def _module_matches_gap(self, module: TrainingModuleResponse, category: str, gap_type: str) -> bool:
        """Check if module addresses a specific skill gap"""
        # This is a simplified matching logic
        # In a real implementation, you'd have more sophisticated matching
        module_content = module.content.lower()
        module_title = module.title.lower()
        
        if gap_type == "low_success_rate":
            return category.lower() in module_content or category.lower() in module_title
        elif gap_type == "high_escalation_rate":
            return "escalation" in module_content or "complex" in module_content
        elif gap_type == "slow_resolution":
            return "efficiency" in module_content or "time" in module_content
        
        return False
    
    def _create_milestones(self, modules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create learning milestones"""
        milestones = []
        completed_hours = 0
        
        for i, module in enumerate(modules):
            completed_hours += module["duration"] / 60
            milestones.append({
                "milestone_id": i + 1,
                "title": f"Complete {module['title']}",
                "description": f"Finish {module['title']} training module",
                "estimated_hours": completed_hours,
                "reward": f"{module['duration']} points"
            })
        
        return milestones
    
    def _get_next_milestones(self, current_points: int, performance: AgentPerformanceResponse) -> List[Dict[str, Any]]:
        """Get next achievable milestones"""
        milestones = []
        
        # Points milestones
        next_point_targets = [1000, 2500, 5000, 10000]
        for target in next_point_targets:
            if current_points < target:
                milestones.append({
                    "type": "points",
                    "title": f"Reach {target} Points",
                    "description": f"Earn {target - current_points} more points",
                    "progress": current_points / target
                })
                break
        
        # Training hours milestones
        next_hour_targets = [20, 50, 100, 200]
        for target in next_hour_targets:
            if performance.total_training_hours < target:
                milestones.append({
                    "type": "hours",
                    "title": f"Complete {target} Training Hours",
                    "description": f"Complete {target - performance.total_training_hours} more hours",
                    "progress": performance.total_training_hours / target
                })
                break
        
        # Module completion milestones
        next_module_targets = [10, 25, 50, 100]
        for target in next_module_targets:
            if performance.completed_modules < target:
                milestones.append({
                    "type": "modules",
                    "title": f"Complete {target} Modules",
                    "description": f"Complete {target - performance.completed_modules} more modules",
                    "progress": performance.completed_modules / target
                })
                break
        
        return milestones[:3]  # Return top 3 milestones
    
    async def _log_training_event(self, event_type: str, data: Dict[str, Any]):
        """Log training events for analytics"""
        try:
            log_data = {
                "event_type": event_type,
                "timestamp": datetime.utcnow().isoformat(),
                "data": data
            }
            
            # Use analytics manager to log event
            await self.analytics_manager.log_event("agent_training", log_data)
            
        except Exception:
            # Silently fail logging
            pass
