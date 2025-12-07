import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session

from backend.core.utils.nlp_utils import NLPProcessor
from backend.core.cache.redis_manager import RedisManager
from ..models import InteractivePoll, CampaignQuiz, EmailSurvey, InteractiveContent

class InteractiveElementsService:
    def __init__(self, db: Session):
        self.db = db
        self.nlp_processor = NLPProcessor()
        self.redis_manager = RedisManager()
        
    def create_interactive_poll(self, poll_data: Dict[str, Any], target_audience: List[str]) -> Dict[str, Any]:
        poll_id = str(uuid.uuid4())
        poll_result = self.nlp_processor.create_interactive_poll(f"Poll Data: {poll_data}")
        
        poll = InteractivePoll(
            id=poll_id, poll_data=json.dumps(poll_data), target_audience=json.dumps(target_audience),
            poll_content=json.dumps(poll_result), status="active", created_at=datetime.utcnow()
        )
        self.db.add(poll)
        self.db.commit()
        
        return {"poll_id": poll_id, "poll_content": poll_result}
    
    def create_campaign_quiz(self, quiz_data: Dict[str, Any], quiz_type: str) -> Dict[str, Any]:
        quiz_id = str(uuid.uuid4())
        quiz_result = self.nlp_processor.create_campaign_quiz(f"Quiz Data: {quiz_data}")
        
        quiz = CampaignQuiz(
            id=quiz_id, quiz_data=json.dumps(quiz_data), quiz_type=quiz_type,
            quiz_content=json.dumps(quiz_result), created_at=datetime.utcnow()
        )
        self.db.add(quiz)
        self.db.commit()
        
        return {"quiz_id": quiz_id, "quiz_content": quiz_result}
    
    def create_email_survey(self, survey_data: Dict[str, Any], target_segments: List[str]) -> Dict[str, Any]:
        survey_id = str(uuid.uuid4())
        survey_result = self.nlp_processor.create_email_survey(f"Survey Data: {survey_data}")
        
        survey = EmailSurvey(
            id=survey_id, survey_data=json.dumps(survey_data), target_segments=json.dumps(target_segments),
            survey_content=json.dumps(survey_result), created_at=datetime.utcnow()
        )
        self.db.add(survey)
        self.db.commit()
        
        return {"survey_id": survey_id, "survey_content": survey_result}
    
    def create_interactive_content(self, content_brief: Dict[str, Any], content_type: str) -> Dict[str, Any]:
        content_id = str(uuid.uuid4())
        content_result = self.nlp_processor.create_interactive_content(f"Content Brief: {content_brief}")
        
        content = InteractiveContent(
            id=content_id, content_brief=json.dumps(content_brief), content_type=content_type,
            content_data=json.dumps(content_result), created_at=datetime.utcnow()
        )
        self.db.add(content)
        self.db.commit()
        
        return {"content_id": content_id, "content_data": content_result}
    
    def get_interactive_analytics(self, timeframe: str = "30d") -> Dict[str, Any]:
        cutoff_date = datetime.utcnow() - timedelta(days=30 if timeframe == "30d" else 7)
        
        polls_created = self.db.query(InteractivePoll).filter(InteractivePoll.created_at >= cutoff_date).count()
        quizzes_created = self.db.query(CampaignQuiz).filter(CampaignQuiz.created_at >= cutoff_date).count()
        surveys_created = self.db.query(EmailSurvey).filter(EmailSurvey.created_at >= cutoff_date).count()
        interactive_content = self.db.query(InteractiveContent).filter(InteractiveContent.created_at >= cutoff_date).count()
        
        return {
            "timeframe": timeframe, "polls_created": polls_created,
            "quizzes_created": quizzes_created, "surveys_created": surveys_created,
            "interactive_content": interactive_content
        }
