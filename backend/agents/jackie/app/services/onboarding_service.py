import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session

from core.utils.nlp_utils import NLPProcessor
from core.cache.redis_manager import RedisManager
from ..models import JackieOnboardingSession, TutorialStep, SetupWizard, JackieUserProgress

class OnboardingService:
    def __init__(self, db: Session):
        self.db = db
        self.nlp_processor = NLPProcessor()
        self.redis_manager = RedisManager()
        
    def create_onboarding_session(self, user_id: str, business_info: Dict[str, Any],
                                onboarding_type: str = "comprehensive") -> Dict[str, Any]:
        session_id = str(uuid.uuid4())
        
        prompt = f"""
        User ID: {user_id}
        Business Info: {business_info}
        Onboarding Type: {onboarding_type}
        
        Create a personalized onboarding session with guided setup steps.
        """
        
        session_result = self.nlp_processor.create_onboarding_session(prompt)
        
        session = JackieOnboardingSession(
            id=session_id, user_id=user_id, business_info=json.dumps(business_info),
            onboarding_type=onboarding_type, session_data=json.dumps(session_result),
            status="active", created_at=datetime.utcnow()
        )
        self.db.add(session)
        self.db.commit()
        
        return {"session_id": session_id, "session_data": session_result}
    
    def create_setup_wizard(self, wizard_type: str, steps_data: List[Dict[str, Any]],
                          target_audience: str) -> Dict[str, Any]:
        wizard_id = str(uuid.uuid4())
        
        prompt = f"""
        Wizard Type: {wizard_type}
        Steps Data: {steps_data}
        Target Audience: {target_audience}
        
        Create an interactive setup wizard with guided steps.
        """
        
        wizard_result = self.nlp_processor.create_setup_wizard(prompt)
        
        wizard = SetupWizard(
            id=wizard_id, wizard_type=wizard_type, steps_data=json.dumps(steps_data),
            target_audience=target_audience, wizard_config=json.dumps(wizard_result),
            created_at=datetime.utcnow()
        )
        self.db.add(wizard)
        self.db.commit()
        
        return {"wizard_id": wizard_id, "wizard_config": wizard_result}
    
    def create_tutorial_step(self, step_data: Dict[str, Any], tutorial_type: str,
                           difficulty_level: str = "beginner") -> Dict[str, Any]:
        step_id = str(uuid.uuid4())
        
        prompt = f"""
        Step Data: {step_data}
        Tutorial Type: {tutorial_type}
        Difficulty Level: {difficulty_level}
        
        Create an engaging tutorial step with clear instructions.
        """
        
        step_result = self.nlp_processor.create_tutorial_step(prompt)
        
        step = TutorialStep(
            id=step_id, step_data=json.dumps(step_data), tutorial_type=tutorial_type,
            difficulty_level=difficulty_level, step_content=json.dumps(step_result),
            created_at=datetime.utcnow()
        )
        self.db.add(step)
        self.db.commit()
        
        return {"step_id": step_id, "step_content": step_result}
    
    def track_user_progress(self, user_id: str, session_id: str, progress_data: Dict[str, Any],
                          current_step: str) -> Dict[str, Any]:
        progress_id = str(uuid.uuid4())
        
        progress = JackieUserProgress(
            id=progress_id, user_id=user_id, session_id=session_id,
            progress_data=json.dumps(progress_data), current_step=current_step,
            created_at=datetime.utcnow()
        )
        self.db.add(progress)
        self.db.commit()
        
        return {"progress_id": progress_id, "current_step": current_step}
    
    def get_next_onboarding_step(self, user_id: str, session_id: str,
                               current_step: str) -> Dict[str, Any]:
        prompt = f"""
        User ID: {user_id}
        Session ID: {session_id}
        Current Step: {current_step}
        
        Determine the next onboarding step based on user progress.
        """
        
        next_step_result = self.nlp_processor.get_next_onboarding_step(prompt)
        
        return {
            "user_id": user_id, "session_id": session_id,
            "next_step": next_step_result.get("next_step", ""),
            "recommendations": next_step_result.get("recommendations", [])
        }
    
    def generate_onboarding_recommendations(self, user_data: Dict[str, Any],
                                         business_type: str) -> Dict[str, Any]:
        prompt = f"""
        User Data: {user_data}
        Business Type: {business_type}
        
        Generate personalized onboarding recommendations.
        """
        
        recommendations_result = self.nlp_processor.generate_onboarding_recommendations(prompt)
        
        return {
            "user_data": user_data, "business_type": business_type,
            "recommendations": recommendations_result
        }
    
    def create_quick_start_guide(self, business_info: Dict[str, Any],
                               guide_type: str = "marketing") -> Dict[str, Any]:
        prompt = f"""
        Business Info: {business_info}
        Guide Type: {guide_type}
        
        Create a quick start guide for immediate setup and usage.
        """
        
        guide_result = self.nlp_processor.create_quick_start_guide(prompt)
        
        return {
            "business_info": business_info, "guide_type": guide_type,
            "quick_start_guide": guide_result
        }
    
    def get_onboarding_analytics(self, timeframe: str = "30d") -> Dict[str, Any]:
        cutoff_date = datetime.utcnow() - timedelta(days=30 if timeframe == "30d" else 7)
        
        sessions_count = self.db.query(JackieOnboardingSession).filter(
            JackieOnboardingSession.created_at >= cutoff_date
        ).count()
        
        completed_sessions = self.db.query(JackieOnboardingSession).filter(
            JackieOnboardingSession.created_at >= cutoff_date,
            JackieOnboardingSession.status == "completed"
        ).count()
        
        wizards_created = self.db.query(SetupWizard).filter(
            SetupWizard.created_at >= cutoff_date
        ).count()
        
        tutorial_steps = self.db.query(TutorialStep).filter(
            TutorialStep.created_at >= cutoff_date
        ).count()
        
        return {
            "timeframe": timeframe, "sessions_count": sessions_count,
            "completed_sessions": completed_sessions, "completion_rate": 
            (completed_sessions / sessions_count * 100) if sessions_count > 0 else 0,
            "wizards_created": wizards_created, "tutorial_steps": tutorial_steps
        }
