import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session

from backend.core.utils.nlp_utils import NLPProcessor
from backend.core.cache.redis_manager import RedisManager
from ..models import LaunchProject, MarketingFunnel, LandingPage, EmailFlow

class LaunchAssistantService:
    def __init__(self, db: Session):
        self.db = db
        self.nlp_processor = NLPProcessor()
        self.redis_manager = RedisManager()
        
    def create_launch_project(self, project_brief: Dict[str, Any], business_info: Dict[str, Any]) -> Dict[str, Any]:
        project_id = str(uuid.uuid4())
        project_result = self.nlp_processor.create_launch_project(f"Project Brief: {project_brief}")
        
        project = LaunchProject(
            id=project_id, project_brief=json.dumps(project_brief), business_info=json.dumps(business_info),
            project_data=json.dumps(project_result), status="active", created_at=datetime.utcnow()
        )
        self.db.add(project)
        self.db.commit()
        
        return {"project_id": project_id, "project_data": project_result}
    
    def build_marketing_funnel(self, funnel_type: str, conversion_goals: List[str]) -> Dict[str, Any]:
        funnel_id = str(uuid.uuid4())
        funnel_result = self.nlp_processor.build_marketing_funnel(f"Funnel Type: {funnel_type}")
        
        funnel = MarketingFunnel(
            id=funnel_id, funnel_type=funnel_type, conversion_goals=json.dumps(conversion_goals),
            funnel_config=json.dumps(funnel_result), created_at=datetime.utcnow()
        )
        self.db.add(funnel)
        self.db.commit()
        
        return {"funnel_id": funnel_id, "funnel_config": funnel_result}
    
    def create_landing_page(self, page_brief: Dict[str, Any], conversion_goals: List[str]) -> Dict[str, Any]:
        page_id = str(uuid.uuid4())
        page_result = self.nlp_processor.create_landing_page(f"Page Brief: {page_brief}")
        
        page = LandingPage(
            id=page_id, page_brief=json.dumps(page_brief), conversion_goals=json.dumps(conversion_goals),
            page_content=json.dumps(page_result), created_at=datetime.utcnow()
        )
        self.db.add(page)
        self.db.commit()
        
        return {"page_id": page_id, "page_content": page_result}
    
    def create_email_flow(self, flow_brief: Dict[str, Any], subscriber_segments: List[str]) -> Dict[str, Any]:
        flow_id = str(uuid.uuid4())
        flow_result = self.nlp_processor.create_email_flow(f"Flow Brief: {flow_brief}")
        
        flow = EmailFlow(
            id=flow_id, flow_brief=json.dumps(flow_brief), subscriber_segments=json.dumps(subscriber_segments),
            flow_content=json.dumps(flow_result), created_at=datetime.utcnow()
        )
        self.db.add(flow)
        self.db.commit()
        
        return {"flow_id": flow_id, "flow_content": flow_result}
    
    def get_launch_analytics(self, timeframe: str = "30d") -> Dict[str, Any]:
        cutoff_date = datetime.utcnow() - timedelta(days=30 if timeframe == "30d" else 7)
        
        projects_created = self.db.query(LaunchProject).filter(LaunchProject.created_at >= cutoff_date).count()
        funnels_built = self.db.query(MarketingFunnel).filter(MarketingFunnel.created_at >= cutoff_date).count()
        landing_pages = self.db.query(LandingPage).filter(LandingPage.created_at >= cutoff_date).count()
        email_flows = self.db.query(EmailFlow).filter(EmailFlow.created_at >= cutoff_date).count()
        
        return {
            "timeframe": timeframe, "projects_created": projects_created,
            "funnels_built": funnels_built, "landing_pages": landing_pages,
            "email_flows": email_flows
        }
