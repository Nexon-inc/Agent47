from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from fastapi import HTTPException, BackgroundTasks
import json
import asyncio
from enum import Enum

from ..models import (
    VoiceSentimentSession, VoiceSentimentAnalysis, VoiceSentimentFeedback,
    VoiceSentimentCoaching, VoiceSentimentScenario, VoiceSentimentPractice,
    SupportAgent, CustomerInteraction
)
from ..schemas.voice_sentiment_coaching import (
    CreateVoiceSentimentSessionRequest, UpdateVoiceSentimentSessionRequest,
    CreateVoiceSentimentAnalysisRequest, UpdateVoiceSentimentAnalysisRequest,
    CreateVoiceSentimentFeedbackRequest, UpdateVoiceSentimentFeedbackRequest,
    CreateVoiceSentimentCoachingRequest, UpdateVoiceSentimentCoachingRequest,
    CreateVoiceSentimentScenarioRequest, UpdateVoiceSentimentScenarioRequest,
    VoiceSentimentSessionResponse, VoiceSentimentAnalysisResponse, VoiceSentimentFeedbackResponse,
    VoiceSentimentCoachingResponse, VoiceSentimentScenarioResponse, VoiceSentimentAnalyticsResponse
)
from ..database import get_clara_database
from core.config import settings
from core.integrations import IntegrationManager
from core.analytics import AnalyticsManager
from core.ai import get_ai_service_manager


class VoiceSentimentType(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    FRUSTRATED = "frustrated"
    ANGRY = "angry"
    SATISFIED = "satisfied"
    CONFUSED = "confused"
    ANXIOUS = "anxious"


class VoiceSentimentSessionStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class VoiceSentimentCoachingType(str, Enum):
    EMPATHY_TRAINING = "empathy_training"
    TONE_ADJUSTMENT = "tone_adjustment"
    RESPONSE_OPTIMIZATION = "response_optimization"
    CONFLICT_RESOLUTION = "conflict_resolution"
    DE_ESCALATION = "de_escalation"


class VoiceSentimentScenarioType(str, Enum):
    CUSTOMER_COMPLAINT = "customer_complaint"
    TECHNICAL_ISSUE = "technical_issue"
    BILLING_DISPUTE = "billing_dispute"
    PRODUCT_INQUIRY = "product_inquiry"
    GENERAL_SUPPORT = "general_support"


class VoiceSentimentCoachingService:
    def __init__(self):
        self.integration_manager = IntegrationManager()
        self.analytics_manager = AnalyticsManager()
        # Using AI Service Manager for sentiment analysis - NLPUtils removed
        
    async def create_voice_sentiment_session(
        self, 
        db: Session, 
        request: CreateVoiceSentimentSessionRequest
    ) -> VoiceSentimentSessionResponse:
        """Create a new voice sentiment coaching session"""
        try:
            session = VoiceSentimentSession(
                agent_id=request.agent_id,
                session_type=request.session_type,
                status=VoiceSentimentSessionStatus.ACTIVE,
                start_time=datetime.utcnow(),
                end_time=None,
                duration_minutes=0,
                scenarios_completed=0,
                total_scenarios=request.total_scenarios or 5,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(session)
            db.commit()
            db.refresh(session)
            
            return VoiceSentimentSessionResponse(
                id=session.id,
                agent_id=session.agent_id,
                session_type=session.session_type,
                status=session.status,
                start_time=session.start_time,
                end_time=session.end_time,
                duration_minutes=session.duration_minutes,
                scenarios_completed=session.scenarios_completed,
                total_scenarios=session.total_scenarios,
                created_at=session.created_at,
                updated_at=session.updated_at
            )
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to create voice sentiment session: {str(e)}")
    
    async def get_voice_sentiment_session(
        self, 
        db: Session, 
        session_id: int
    ) -> VoiceSentimentSessionResponse:
        """Get voice sentiment session by ID"""
        session = db.query(VoiceSentimentSession).filter(VoiceSentimentSession.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Voice sentiment session not found")
        
        return VoiceSentimentSessionResponse(
            id=session.id,
            agent_id=session.agent_id,
            session_type=session.session_type,
            status=session.status,
            start_time=session.start_time,
            end_time=session.end_time,
            duration_minutes=session.duration_minutes,
            scenarios_completed=session.scenarios_completed,
            total_scenarios=session.total_scenarios,
            created_at=session.created_at,
            updated_at=session.updated_at
        )
    
    async def list_voice_sentiment_sessions(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        agent_id: Optional[int] = None,
        session_type: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[VoiceSentimentSessionResponse]:
        """List voice sentiment sessions"""
        query = db.query(VoiceSentimentSession)
        
        if agent_id:
            query = query.filter(VoiceSentimentSession.agent_id == agent_id)
        if session_type:
            query = query.filter(VoiceSentimentSession.session_type == session_type)
        if status:
            query = query.filter(VoiceSentimentSession.status == status)
        
        sessions = query.order_by(desc(VoiceSentimentSession.created_at)).offset(skip).limit(limit).all()
        
        return [
            VoiceSentimentSessionResponse(
                id=session.id,
                agent_id=session.agent_id,
                session_type=session.session_type,
                status=session.status,
                start_time=session.start_time,
                end_time=session.end_time,
                duration_minutes=session.duration_minutes,
                scenarios_completed=session.scenarios_completed,
                total_scenarios=session.total_scenarios,
                created_at=session.created_at,
                updated_at=session.updated_at
            ) for session in sessions
        ]
    
    async def update_voice_sentiment_session(
        self, 
        db: Session, 
        session_id: int, 
        request: UpdateVoiceSentimentSessionRequest
    ) -> VoiceSentimentSessionResponse:
        """Update voice sentiment session"""
        session = db.query(VoiceSentimentSession).filter(VoiceSentimentSession.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Voice sentiment session not found")
        
        try:
            if request.status is not None:
                session.status = request.status
                if request.status == VoiceSentimentSessionStatus.COMPLETED:
                    session.end_time = datetime.utcnow()
                    session.duration_minutes = int((session.end_time - session.start_time).total_seconds() / 60)
            if request.scenarios_completed is not None:
                session.scenarios_completed = request.scenarios_completed
            
            session.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(session)
            
            return VoiceSentimentSessionResponse(
                id=session.id,
                agent_id=session.agent_id,
                session_type=session.session_type,
                status=session.status,
                start_time=session.start_time,
                end_time=session.end_time,
                duration_minutes=session.duration_minutes,
                scenarios_completed=session.scenarios_completed,
                total_scenarios=session.total_scenarios,
                created_at=session.created_at,
                updated_at=session.updated_at
            )
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to update voice sentiment session: {str(e)}")
    
    async def create_voice_sentiment_analysis(
        self, 
        db: Session, 
        request: CreateVoiceSentimentAnalysisRequest
    ) -> VoiceSentimentAnalysisResponse:
        """Create a new voice sentiment analysis"""
        try:
            # Analyze voice sentiment using NLP
            sentiment_result = await self._analyze_voice_sentiment(request.audio_data, request.transcript)
            
            analysis = VoiceSentimentAnalysis(
                session_id=request.session_id,
                scenario_id=request.scenario_id,
                audio_data=request.audio_data,
                transcript=request.transcript,
                sentiment_type=sentiment_result["sentiment_type"],
                sentiment_score=sentiment_result["sentiment_score"],
                confidence_score=sentiment_result["confidence_score"],
                detected_emotions=sentiment_result["detected_emotions"],
                tone_analysis=sentiment_result["tone_analysis"],
                created_at=datetime.utcnow()
            )
            
            db.add(analysis)
            db.commit()
            db.refresh(analysis)
            
            return VoiceSentimentAnalysisResponse(
                id=analysis.id,
                session_id=analysis.session_id,
                scenario_id=analysis.scenario_id,
                audio_data=analysis.audio_data,
                transcript=analysis.transcript,
                sentiment_type=analysis.sentiment_type,
                sentiment_score=analysis.sentiment_score,
                confidence_score=analysis.confidence_score,
                detected_emotions=analysis.detected_emotions,
                tone_analysis=analysis.tone_analysis,
                created_at=analysis.created_at
            )
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to create voice sentiment analysis: {str(e)}")
    
    async def get_voice_sentiment_analysis(
        self, 
        db: Session, 
        analysis_id: int
    ) -> VoiceSentimentAnalysisResponse:
        """Get voice sentiment analysis by ID"""
        analysis = db.query(VoiceSentimentAnalysis).filter(VoiceSentimentAnalysis.id == analysis_id).first()
        if not analysis:
            raise HTTPException(status_code=404, detail="Voice sentiment analysis not found")
        
        return VoiceSentimentAnalysisResponse(
            id=analysis.id,
            session_id=analysis.session_id,
            scenario_id=analysis.scenario_id,
            audio_data=analysis.audio_data,
            transcript=analysis.transcript,
            sentiment_type=analysis.sentiment_type,
            sentiment_score=analysis.sentiment_score,
            confidence_score=analysis.confidence_score,
            detected_emotions=analysis.detected_emotions,
            tone_analysis=analysis.tone_analysis,
            created_at=analysis.created_at
        )
    
    async def list_voice_sentiment_analyses(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        session_id: Optional[int] = None,
        scenario_id: Optional[int] = None,
        sentiment_type: Optional[str] = None
    ) -> List[VoiceSentimentAnalysisResponse]:
        """List voice sentiment analyses"""
        query = db.query(VoiceSentimentAnalysis)
        
        if session_id:
            query = query.filter(VoiceSentimentAnalysis.session_id == session_id)
        if scenario_id:
            query = query.filter(VoiceSentimentAnalysis.scenario_id == scenario_id)
        if sentiment_type:
            query = query.filter(VoiceSentimentAnalysis.sentiment_type == sentiment_type)
        
        analyses = query.order_by(desc(VoiceSentimentAnalysis.created_at)).offset(skip).limit(limit).all()
        
        return [
            VoiceSentimentAnalysisResponse(
                id=analysis.id,
                session_id=analysis.session_id,
                scenario_id=analysis.scenario_id,
                audio_data=analysis.audio_data,
                transcript=analysis.transcript,
                sentiment_type=analysis.sentiment_type,
                sentiment_score=analysis.sentiment_score,
                confidence_score=analysis.confidence_score,
                detected_emotions=analysis.detected_emotions,
                tone_analysis=analysis.tone_analysis,
                created_at=analysis.created_at
            ) for analysis in analyses
        ]
    
    async def create_voice_sentiment_feedback(
        self, 
        db: Session, 
        request: CreateVoiceSentimentFeedbackRequest
    ) -> VoiceSentimentFeedbackResponse:
        """Create a new voice sentiment feedback"""
        try:
            feedback = VoiceSentimentFeedback(
                analysis_id=request.analysis_id,
                agent_id=request.agent_id,
                feedback_type=request.feedback_type,
                feedback_text=request.feedback_text,
                improvement_suggestions=request.improvement_suggestions,
                empathy_score=request.empathy_score,
                tone_score=request.tone_score,
                response_effectiveness=request.response_effectiveness,
                created_at=datetime.utcnow()
            )
            
            db.add(feedback)
            db.commit()
            db.refresh(feedback)
            
            return VoiceSentimentFeedbackResponse(
                id=feedback.id,
                analysis_id=feedback.analysis_id,
                agent_id=feedback.agent_id,
                feedback_type=feedback.feedback_type,
                feedback_text=feedback.feedback_text,
                improvement_suggestions=feedback.improvement_suggestions,
                empathy_score=feedback.empathy_score,
                tone_score=feedback.tone_score,
                response_effectiveness=feedback.response_effectiveness,
                created_at=feedback.created_at
            )
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to create voice sentiment feedback: {str(e)}")
    
    async def get_voice_sentiment_feedback(
        self, 
        db: Session, 
        feedback_id: int
    ) -> VoiceSentimentFeedbackResponse:
        """Get voice sentiment feedback by ID"""
        feedback = db.query(VoiceSentimentFeedback).filter(VoiceSentimentFeedback.id == feedback_id).first()
        if not feedback:
            raise HTTPException(status_code=404, detail="Voice sentiment feedback not found")
        
        return VoiceSentimentFeedbackResponse(
            id=feedback.id,
            analysis_id=feedback.analysis_id,
            agent_id=feedback.agent_id,
            feedback_type=feedback.feedback_type,
            feedback_text=feedback.feedback_text,
            improvement_suggestions=feedback.improvement_suggestions,
            empathy_score=feedback.empathy_score,
            tone_score=feedback.tone_score,
            response_effectiveness=feedback.response_effectiveness,
            created_at=feedback.created_at
        )
    
    async def list_voice_sentiment_feedbacks(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        agent_id: Optional[int] = None,
        analysis_id: Optional[int] = None,
        feedback_type: Optional[str] = None
    ) -> List[VoiceSentimentFeedbackResponse]:
        """List voice sentiment feedbacks"""
        query = db.query(VoiceSentimentFeedback)
        
        if agent_id:
            query = query.filter(VoiceSentimentFeedback.agent_id == agent_id)
        if analysis_id:
            query = query.filter(VoiceSentimentFeedback.analysis_id == analysis_id)
        if feedback_type:
            query = query.filter(VoiceSentimentFeedback.feedback_type == feedback_type)
        
        feedbacks = query.order_by(desc(VoiceSentimentFeedback.created_at)).offset(skip).limit(limit).all()
        
        return [
            VoiceSentimentFeedbackResponse(
                id=feedback.id,
                analysis_id=feedback.analysis_id,
                agent_id=feedback.agent_id,
                feedback_type=feedback.feedback_type,
                feedback_text=feedback.feedback_text,
                improvement_suggestions=feedback.improvement_suggestions,
                empathy_score=feedback.empathy_score,
                tone_score=feedback.tone_score,
                response_effectiveness=feedback.response_effectiveness,
                created_at=feedback.created_at
            ) for feedback in feedbacks
        ]
    
    async def create_voice_sentiment_coaching(
        self, 
        db: Session, 
        request: CreateVoiceSentimentCoachingRequest
    ) -> VoiceSentimentCoachingResponse:
        """Create a new voice sentiment coaching recommendation"""
        try:
            coaching = VoiceSentimentCoaching(
                agent_id=request.agent_id,
                session_id=request.session_id,
                coaching_type=request.coaching_type,
                scenario_description=request.scenario_description,
                current_response=request.current_response,
                suggested_response=request.suggested_response,
                empathy_techniques=request.empathy_techniques,
                tone_adjustments=request.tone_adjustments,
                de_escalation_tips=request.de_escalation_tips,
                practice_exercises=request.practice_exercises,
                created_at=datetime.utcnow()
            )
            
            db.add(coaching)
            db.commit()
            db.refresh(coaching)
            
            return VoiceSentimentCoachingResponse(
                id=coaching.id,
                agent_id=coaching.agent_id,
                session_id=coaching.session_id,
                coaching_type=coaching.coaching_type,
                scenario_description=coaching.scenario_description,
                current_response=coaching.current_response,
                suggested_response=coaching.suggested_response,
                empathy_techniques=coaching.empathy_techniques,
                tone_adjustments=coaching.tone_adjustments,
                de_escalation_tips=coaching.de_escalation_tips,
                practice_exercises=coaching.practice_exercises,
                created_at=coaching.created_at
            )
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to create voice sentiment coaching: {str(e)}")
    
    async def get_voice_sentiment_coaching(
        self, 
        db: Session, 
        coaching_id: int
    ) -> VoiceSentimentCoachingResponse:
        """Get voice sentiment coaching by ID"""
        coaching = db.query(VoiceSentimentCoaching).filter(VoiceSentimentCoaching.id == coaching_id).first()
        if not coaching:
            raise HTTPException(status_code=404, detail="Voice sentiment coaching not found")
        
        return VoiceSentimentCoachingResponse(
            id=coaching.id,
            agent_id=coaching.agent_id,
            session_id=coaching.session_id,
            coaching_type=coaching.coaching_type,
            scenario_description=coaching.scenario_description,
            current_response=coaching.current_response,
            suggested_response=coaching.suggested_response,
            empathy_techniques=coaching.empathy_techniques,
            tone_adjustments=coaching.tone_adjustments,
            de_escalation_tips=coaching.de_escalation_tips,
            practice_exercises=coaching.practice_exercises,
            created_at=coaching.created_at
        )
    
    async def list_voice_sentiment_coachings(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        agent_id: Optional[int] = None,
        session_id: Optional[int] = None,
        coaching_type: Optional[str] = None
    ) -> List[VoiceSentimentCoachingResponse]:
        """List voice sentiment coachings"""
        query = db.query(VoiceSentimentCoaching)
        
        if agent_id:
            query = query.filter(VoiceSentimentCoaching.agent_id == agent_id)
        if session_id:
            query = query.filter(VoiceSentimentCoaching.session_id == session_id)
        if coaching_type:
            query = query.filter(VoiceSentimentCoaching.coaching_type == coaching_type)
        
        coachings = query.order_by(desc(VoiceSentimentCoaching.created_at)).offset(skip).limit(limit).all()
        
        return [
            VoiceSentimentCoachingResponse(
                id=coaching.id,
                agent_id=coaching.agent_id,
                session_id=coaching.session_id,
                coaching_type=coaching.coaching_type,
                scenario_description=coaching.scenario_description,
                current_response=coaching.current_response,
                suggested_response=coaching.suggested_response,
                empathy_techniques=coaching.empathy_techniques,
                tone_adjustments=coaching.tone_adjustments,
                de_escalation_tips=coaching.de_escalation_tips,
                practice_exercises=coaching.practice_exercises,
                created_at=coaching.created_at
            ) for coaching in coachings
        ]
    
    async def create_voice_sentiment_scenario(
        self, 
        db: Session, 
        request: CreateVoiceSentimentScenarioRequest
    ) -> VoiceSentimentScenarioResponse:
        """Create a new voice sentiment scenario"""
        try:
            scenario = VoiceSentimentScenario(
                scenario_type=request.scenario_type,
                title=request.title,
                description=request.description,
                customer_context=request.customer_context,
                initial_sentiment=request.initial_sentiment,
                target_sentiment=request.target_sentiment,
                difficulty_level=request.difficulty_level,
                expected_duration=request.expected_duration,
                learning_objectives=request.learning_objectives,
                is_active=request.is_active,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(scenario)
            db.commit()
            db.refresh(scenario)
            
            return VoiceSentimentScenarioResponse(
                id=scenario.id,
                scenario_type=scenario.scenario_type,
                title=scenario.title,
                description=scenario.description,
                customer_context=scenario.customer_context,
                initial_sentiment=scenario.initial_sentiment,
                target_sentiment=scenario.target_sentiment,
                difficulty_level=scenario.difficulty_level,
                expected_duration=scenario.expected_duration,
                learning_objectives=scenario.learning_objectives,
                is_active=scenario.is_active,
                created_at=scenario.created_at,
                updated_at=scenario.updated_at
            )
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to create voice sentiment scenario: {str(e)}")
    
    async def get_voice_sentiment_scenario(
        self, 
        db: Session, 
        scenario_id: int
    ) -> VoiceSentimentScenarioResponse:
        """Get voice sentiment scenario by ID"""
        scenario = db.query(VoiceSentimentScenario).filter(VoiceSentimentScenario.id == scenario_id).first()
        if not scenario:
            raise HTTPException(status_code=404, detail="Voice sentiment scenario not found")
        
        return VoiceSentimentScenarioResponse(
            id=scenario.id,
            scenario_type=scenario.scenario_type,
            title=scenario.title,
            description=scenario.description,
            customer_context=scenario.customer_context,
            initial_sentiment=scenario.initial_sentiment,
            target_sentiment=scenario.target_sentiment,
            difficulty_level=scenario.difficulty_level,
            expected_duration=scenario.expected_duration,
            learning_objectives=scenario.learning_objectives,
            is_active=scenario.is_active,
            created_at=scenario.created_at,
            updated_at=scenario.updated_at
        )
    
    async def list_voice_sentiment_scenarios(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        scenario_type: Optional[str] = None,
        difficulty_level: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[VoiceSentimentScenarioResponse]:
        """List voice sentiment scenarios"""
        query = db.query(VoiceSentimentScenario)
        
        if scenario_type:
            query = query.filter(VoiceSentimentScenario.scenario_type == scenario_type)
        if difficulty_level:
            query = query.filter(VoiceSentimentScenario.difficulty_level == difficulty_level)
        if is_active is not None:
            query = query.filter(VoiceSentimentScenario.is_active == is_active)
        
        scenarios = query.offset(skip).limit(limit).all()
        
        return [
            VoiceSentimentScenarioResponse(
                id=scenario.id,
                scenario_type=scenario.scenario_type,
                title=scenario.title,
                description=scenario.description,
                customer_context=scenario.customer_context,
                initial_sentiment=scenario.initial_sentiment,
                target_sentiment=scenario.target_sentiment,
                difficulty_level=scenario.difficulty_level,
                expected_duration=scenario.expected_duration,
                learning_objectives=scenario.learning_objectives,
                is_active=scenario.is_active,
                created_at=scenario.created_at,
                updated_at=scenario.updated_at
            ) for scenario in scenarios
        ]
    
    async def get_voice_sentiment_analytics(
        self, 
        db: Session, 
        start_date: datetime,
        end_date: datetime,
        agent_id: Optional[int] = None
    ) -> VoiceSentimentAnalyticsResponse:
        """Get voice sentiment analytics"""
        try:
            # Build queries
            sessions_query = db.query(VoiceSentimentSession).filter(
                and_(
                    VoiceSentimentSession.created_at >= start_date,
                    VoiceSentimentSession.created_at <= end_date
                )
            )
            
            analyses_query = db.query(VoiceSentimentAnalysis).filter(
                and_(
                    VoiceSentimentAnalysis.created_at >= start_date,
                    VoiceSentimentAnalysis.created_at <= end_date
                )
            )
            
            feedbacks_query = db.query(VoiceSentimentFeedback).filter(
                and_(
                    VoiceSentimentFeedback.created_at >= start_date,
                    VoiceSentimentFeedback.created_at <= end_date
                )
            )
            
            if agent_id:
                sessions_query = sessions_query.filter(VoiceSentimentSession.agent_id == agent_id)
                feedbacks_query = feedbacks_query.filter(VoiceSentimentFeedback.agent_id == agent_id)
            
            sessions = sessions_query.all()
            analyses = analyses_query.all()
            feedbacks = feedbacks_query.all()
            
            # Calculate metrics
            total_sessions = len(sessions)
            completed_sessions = len([s for s in sessions if s.status == VoiceSentimentSessionStatus.COMPLETED])
            total_analyses = len(analyses)
            total_feedbacks = len(feedbacks)
            
            # Average scores
            avg_empathy_score = sum(f.empathy_score for f in feedbacks) / len(feedbacks) if feedbacks else 0
            avg_tone_score = sum(f.tone_score for f in feedbacks) / len(feedbacks) if feedbacks else 0
            avg_response_effectiveness = sum(f.response_effectiveness for f in feedbacks) / len(feedbacks) if feedbacks else 0
            
            # Sentiment breakdown
            sentiment_breakdown = {}
            for analysis in analyses:
                sentiment_type = analysis.sentiment_type
                if sentiment_type not in sentiment_breakdown:
                    sentiment_breakdown[sentiment_type] = 0
                sentiment_breakdown[sentiment_type] += 1
            
            # Coaching type breakdown
            coaching_query = db.query(VoiceSentimentCoaching).filter(
                and_(
                    VoiceSentimentCoaching.created_at >= start_date,
                    VoiceSentimentCoaching.created_at <= end_date
                )
            )
            if agent_id:
                coaching_query = coaching_query.filter(VoiceSentimentCoaching.agent_id == agent_id)
            
            coachings = coaching_query.all()
            coaching_type_breakdown = {}
            for coaching in coachings:
                coaching_type = coaching.coaching_type
                if coaching_type not in coaching_type_breakdown:
                    coaching_type_breakdown[coaching_type] = 0
                coaching_type_breakdown[coaching_type] += 1
            
            return VoiceSentimentAnalyticsResponse(
                period_start=start_date,
                period_end=end_date,
                total_sessions=total_sessions,
                completed_sessions=completed_sessions,
                completion_rate=completed_sessions / total_sessions if total_sessions > 0 else 0,
                total_analyses=total_analyses,
                total_feedbacks=total_feedbacks,
                avg_empathy_score=avg_empathy_score,
                avg_tone_score=avg_tone_score,
                avg_response_effectiveness=avg_response_effectiveness,
                sentiment_breakdown=sentiment_breakdown,
                coaching_type_breakdown=coaching_type_breakdown
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get voice sentiment analytics: {str(e)}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check the health of voice sentiment coaching system"""
        try:
            db = next(get_db())
            session_count = db.query(VoiceSentimentSession).count()
            analysis_count = db.query(VoiceSentimentAnalysis).count()
            feedback_count = db.query(VoiceSentimentFeedback).count()
            coaching_count = db.query(VoiceSentimentCoaching).count()
            scenario_count = db.query(VoiceSentimentScenario).count()
            
            return {
                "status": "healthy",
                "database": {
                    "connected": True,
                    "sessions_count": session_count,
                    "analyses_count": analysis_count,
                    "feedbacks_count": feedback_count,
                    "coachings_count": coaching_count,
                    "scenarios_count": scenario_count
                },
                "last_check": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "last_check": datetime.utcnow().isoformat()
            }
    
    async def _analyze_voice_sentiment(self, audio_data: str, transcript: str) -> Dict[str, Any]:
        """Analyze voice sentiment using NLP and audio analysis"""
        try:
            # Use NLP to analyze transcript sentiment
            # Use AI Service Manager for sentiment analysis
            ai_manager = await get_ai_service_manager()
            messages = [{"role": "system", "content": "You are an AI assistant that analyzes sentiment from text. Respond with JSON: {\"sentiment\": \"positive/negative/neutral\", \"score\": 0.0-1.0}"}, {"role": "user", "content": f"Analyze the sentiment of: {transcript}"}]
            sentiment_response = await ai_manager.generate_text(messages=messages, max_tokens=200, temperature=0.3)
            try:
                import json
                text_sentiment = json.loads(sentiment_response.text_content) if sentiment_response.success else {"sentiment": "neutral", "score": 0.5}
            except:
                text_sentiment = {"sentiment": "neutral", "score": 0.5}
            
            # Analyze audio characteristics (tone, pitch, speed)
            audio_analysis = await self._analyze_audio_characteristics(audio_data)
            
            # Combine text and audio analysis
            combined_sentiment = self._combine_sentiment_analysis(text_sentiment, audio_analysis)
            
            return {
                "sentiment_type": combined_sentiment["sentiment_type"],
                "sentiment_score": combined_sentiment["sentiment_score"],
                "confidence_score": combined_sentiment["confidence_score"],
                "detected_emotions": combined_sentiment["detected_emotions"],
                "tone_analysis": audio_analysis["tone_analysis"]
            }
            
        except Exception as e:
            # Fallback to basic sentiment analysis
            return {
                "sentiment_type": VoiceSentimentType.NEUTRAL,
                "sentiment_score": 0.0,
                "confidence_score": 0.5,
                "detected_emotions": ["neutral"],
                "tone_analysis": {"tone": "neutral", "pitch": "medium", "speed": "normal"}
            }
    
    async def _analyze_audio_characteristics(self, audio_data: str) -> Dict[str, Any]:
        """Analyze audio characteristics for tone detection"""
        try:
            # Decode base64 audio data
            import base64
            import numpy as np
            from scipy import signal
            from scipy.stats import skew, kurtosis
            
            # Decode audio data
            audio_bytes = base64.b64decode(audio_data)
            
            # Convert to numpy array (assuming 16-bit PCM)
            audio_array = np.frombuffer(audio_bytes, dtype=np.int16)
            
            # Normalize audio
            audio_normalized = audio_array.astype(np.float32) / 32768.0
            
            # Calculate audio features
            sample_rate = 16000  # Assuming 16kHz sample rate
            
            # Pitch analysis using autocorrelation
            def estimate_pitch(audio, sr):
                # Calculate autocorrelation
                autocorr = np.correlate(audio, audio, mode='full')
                autocorr = autocorr[len(autocorr)//2:]
                
                # Find peaks
                peaks = signal.find_peaks(autocorr, height=0.1*np.max(autocorr))[0]
                
                if len(peaks) > 0:
                    # Calculate fundamental frequency
                    fundamental_period = peaks[0]
                    fundamental_freq = sr / fundamental_period
                    return fundamental_freq
                return 0
            
            pitch_freq = estimate_pitch(audio_normalized, sample_rate)
            
            # Determine pitch category
            if pitch_freq < 150:
                pitch_category = "low"
            elif pitch_freq < 300:
                pitch_category = "medium"
            else:
                pitch_category = "high"
            
            # Calculate speech rate (syllables per second approximation)
            # Using zero-crossing rate as a proxy
            zero_crossings = np.sum(np.diff(np.sign(audio_normalized)) != 0)
            speech_rate = zero_crossings / (len(audio_normalized) / sample_rate)
            
            if speech_rate < 10:
                speed_category = "slow"
            elif speech_rate < 20:
                speed_category = "normal"
            else:
                speed_category = "fast"
            
            # Calculate volume (RMS)
            rms = np.sqrt(np.mean(audio_normalized**2))
            if rms < 0.1:
                volume_category = "low"
            elif rms < 0.3:
                volume_category = "moderate"
            else:
                volume_category = "high"
            
            # Analyze clarity (using spectral centroid)
            fft = np.fft.fft(audio_normalized)
            magnitude = np.abs(fft)
            frequencies = np.fft.fftfreq(len(audio_normalized), 1/sample_rate)
            
            # Spectral centroid
            spectral_centroid = np.sum(frequencies * magnitude) / np.sum(magnitude)
            
            if spectral_centroid > 2000:
                clarity_category = "clear"
            elif spectral_centroid > 1000:
                clarity_category = "moderate"
            else:
                clarity_category = "unclear"
            
            # Determine tone based on pitch and speech rate
            if pitch_category == "high" and speed_category == "fast":
                tone_category = "excited"
            elif pitch_category == "low" and speed_category == "slow":
                tone_category = "calm"
            elif pitch_category == "high" and speed_category == "slow":
                tone_category = "thoughtful"
            elif pitch_category == "low" and speed_category == "fast":
                tone_category = "urgent"
            else:
                tone_category = "neutral"
            
            # Estimate stress level based on pitch variation and speech rate
            pitch_variation = np.std(audio_normalized)
            if pitch_variation > 0.5 and speech_rate > 15:
                stress_level = "high"
            elif pitch_variation > 0.3:
                stress_level = "medium"
            else:
                stress_level = "low"
            
            # Estimate confidence based on clarity and volume
            if clarity_category == "clear" and volume_category in ["moderate", "high"]:
                confidence_level = "high"
            elif clarity_category == "moderate":
                confidence_level = "medium"
            else:
                confidence_level = "low"
            
            # Estimate engagement based on speech rate and volume
            if speech_rate > 15 and volume_category in ["moderate", "high"]:
                engagement_level = "high"
            elif speech_rate > 10:
                engagement_level = "medium"
            else:
                engagement_level = "low"
            
            return {
                "tone_analysis": {
                    "tone": tone_category,
                    "pitch": pitch_category,
                    "speed": speed_category,
                    "volume": volume_category,
                    "clarity": clarity_category,
                    "pitch_frequency": float(pitch_freq),
                    "speech_rate": float(speech_rate),
                    "rms_volume": float(rms)
                },
                "emotion_indicators": {
                    "stress_level": stress_level,
                    "confidence": confidence_level,
                    "engagement": engagement_level,
                    "pitch_variation": float(pitch_variation),
                    "spectral_centroid": float(spectral_centroid)
                }
            }
            
        except Exception:
            return {
                "tone_analysis": {
                    "tone": "neutral",
                    "pitch": "medium",
                    "speed": "normal",
                    "volume": "moderate",
                    "clarity": "clear"
                },
                "emotion_indicators": {
                    "stress_level": "unknown",
                    "confidence": "unknown",
                    "engagement": "unknown"
                }
            }
    
    def _combine_sentiment_analysis(self, text_sentiment: Dict[str, Any], audio_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Combine text and audio sentiment analysis"""
        # Weight text sentiment more heavily than audio
        text_weight = 0.7
        audio_weight = 0.3
        
        # Combine sentiment scores
        combined_score = (text_sentiment.get("score", 0) * text_weight + 
                         audio_analysis.get("sentiment_score", 0) * audio_weight)
        
        # Determine sentiment type
        if combined_score > 0.3:
            sentiment_type = VoiceSentimentType.POSITIVE
        elif combined_score < -0.3:
            sentiment_type = VoiceSentimentType.NEGATIVE
        else:
            sentiment_type = VoiceSentimentType.NEUTRAL
        
        # Detect emotions based on combined analysis
        detected_emotions = text_sentiment.get("emotions", [])
        if audio_analysis.get("emotion_indicators", {}).get("stress_level") == "high":
            detected_emotions.append("anxious")
        
        return {
            "sentiment_type": sentiment_type,
            "sentiment_score": combined_score,
            "confidence_score": (text_sentiment.get("confidence", 0.5) + 0.5) / 2,
            "detected_emotions": list(set(detected_emotions))
        }
