import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session

from core.utils.nlp_utils import NLPProcessor
from core.cache.redis_manager import RedisManager
from ..models import CampaignIdea, JackieTrendAnalysis, JackieCompetitorAnalysis, BrainstormingSession

class CampaignIdeationService:
    def __init__(self, db: Session):
        self.db = db
        self.nlp_processor = NLPProcessor()
        self.redis_manager = RedisManager()
        
    def generate_campaign_ideas(self, industry: str, target_audience: List[str], 
                              campaign_goals: List[str], budget_range: str, 
                              timeframe: str, constraints: Dict[str, Any]) -> List[Dict[str, Any]]:
        idea_id = str(uuid.uuid4())
        
        prompt = f"""
        Industry: {industry}
        Target Audience: {target_audience}
        Campaign Goals: {campaign_goals}
        Budget Range: {budget_range}
        Timeframe: {timeframe}
        Constraints: {constraints}
        
        Generate innovative campaign ideas that align with the industry, target audience, and goals.
        Consider current trends, competitor strategies, and budget constraints.
        """
        
        generated_ideas = self.nlp_processor.generate_campaign_ideas(prompt)
        
        ideas = []
        for idea_data in generated_ideas:
            idea_id = str(uuid.uuid4())
            idea = CampaignIdea(
                id=idea_id, title=idea_data.get("title", ""), description=idea_data.get("description", ""),
                concept_type=idea_data.get("concept_type", "general"), target_audience=json.dumps(target_audience),
                estimated_budget=json.dumps(idea_data.get("estimated_budget", {})),
                expected_roi=idea_data.get("expected_roi", 0.0), implementation_timeline=idea_data.get("timeline", ""),
                risk_level=idea_data.get("risk_level", "medium"), created_at=datetime.utcnow()
            )
            self.db.add(idea)
            ideas.append({
                "id": idea_id, "title": idea.get("title"), "description": idea.get("description"),
                "concept_type": idea.get("concept_type"), "target_audience": target_audience,
                "estimated_budget": idea_data.get("estimated_budget", {}), "expected_roi": idea.get("expected_roi"),
                "implementation_timeline": idea.get("implementation_timeline"), "risk_level": idea.get("risk_level"),
                "created_at": idea.created_at.isoformat()
            })
        
        self.db.commit()
        return ideas
    
    def get_campaign_idea(self, idea_id: str) -> Optional[Dict[str, Any]]:
        idea = self.db.query(CampaignIdea).filter(CampaignIdea.id == idea_id).first()
        if not idea:
            return None
        
        return {
            "id": idea.id, "title": idea.title, "description": idea.description,
            "concept_type": idea.concept_type, "target_audience": json.loads(idea.target_audience),
            "estimated_budget": json.loads(idea.estimated_budget), "expected_roi": idea.expected_roi,
            "implementation_timeline": idea.implementation_timeline, "risk_level": idea.risk_level,
            "created_at": idea.created_at.isoformat()
        }
    
    def list_campaign_ideas(self, industry: Optional[str] = None, concept_type: Optional[str] = None,
                           budget_range: Optional[str] = None, risk_level: Optional[str] = None,
                           limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        query = self.db.query(CampaignIdea)
        
        if industry:
            query = query.filter(CampaignIdea.industry == industry)
        if concept_type:
            query = query.filter(CampaignIdea.concept_type == concept_type)
        if risk_level:
            query = query.filter(CampaignIdea.risk_level == risk_level)
        
        ideas = query.offset(offset).limit(limit).all()
        
        return [{
            "id": idea.id, "title": idea.title, "description": idea.description,
            "concept_type": idea.concept_type, "target_audience": json.loads(idea.target_audience),
            "estimated_budget": json.loads(idea.estimated_budget), "expected_roi": idea.expected_roi,
            "implementation_timeline": idea.implementation_timeline, "risk_level": idea.risk_level,
            "created_at": idea.created_at.isoformat()
        } for idea in ideas]
    
    def refine_campaign_idea(self, idea_id: str, refinement_criteria: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        idea = self.db.query(CampaignIdea).filter(CampaignIdea.id == idea_id).first()
        if not idea:
            return None
        
        prompt = f"""
        Original Idea: {idea.title} - {idea.description}
        Refinement Criteria: {refinement_criteria}
        
        Refine and improve this campaign idea based on the specified criteria.
        """
        
        refined_idea = self.nlp_processor.refine_campaign_idea(prompt)
        
        idea.title = refined_idea.get("title", idea.title)
        idea.description = refined_idea.get("description", idea.description)
        idea.updated_at = datetime.utcnow()
        self.db.commit()
        
        return {
            "refined_idea": {
                "id": idea.id, "title": idea.title, "description": idea.description,
                "concept_type": idea.concept_type, "target_audience": json.loads(idea.target_audience),
                "estimated_budget": json.loads(idea.estimated_budget), "expected_roi": idea.expected_roi,
                "implementation_timeline": idea.implementation_timeline, "risk_level": idea.risk_level,
                "updated_at": idea.updated_at.isoformat()
            }
        }
    
    def expand_campaign_idea(self, idea_id: str, expansion_type: str, 
                           additional_context: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        idea = self.db.query(CampaignIdea).filter(CampaignIdea.id == idea_id).first()
        if not idea:
            return None
        
        prompt = f"""
        Campaign Idea: {idea.title} - {idea.description}
        Expansion Type: {expansion_type}
        Additional Context: {additional_context or {}}
        
        Expand this campaign idea with detailed {expansion_type} information.
        """
        
        expanded_details = self.nlp_processor.expand_campaign_idea(prompt, expansion_type)
        
        return {
            "expanded_details": expanded_details,
            "expansion_type": expansion_type,
            "idea_id": idea_id
        }
    
    def validate_campaign_idea(self, idea_id: str, validation_criteria: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        idea = self.db.query(CampaignIdea).filter(CampaignIdea.id == idea_id).first()
        if not idea:
            return None
        
        validation_results = {}
        for criterion, requirements in validation_criteria.items():
            if criterion == "budget_feasibility":
                validation_results[criterion] = self._validate_budget_feasibility(idea, requirements)
            elif criterion == "audience_alignment":
                validation_results[criterion] = self._validate_audience_alignment(idea, requirements)
            elif criterion == "timeline_realistic":
                validation_results[criterion] = self._validate_timeline_realistic(idea, requirements)
        
        overall_valid = all(result.get("valid", False) for result in validation_results.values())
        
        return {
            "idea_id": idea_id, "overall_valid": overall_valid,
            "validation_results": validation_results, "validation_criteria": validation_criteria
        }
    
    def implement_campaign_idea(self, idea_id: str, implementation_plan: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        idea = self.db.query(CampaignIdea).filter(CampaignIdea.id == idea_id).first()
        if not idea:
            return None
        
        campaign_id = str(uuid.uuid4())
        
        implementation_status = {
            "campaign_id": campaign_id,
            "idea_id": idea_id,
            "status": "implementation_started",
            "implementation_plan": implementation_plan,
            "started_at": datetime.utcnow().isoformat()
        }
        
        return {
            "campaign_id": campaign_id,
            "implementation_status": implementation_status
        }
    
    def analyze_trends_for_ideation(self, industry: str, timeframe: str = "30d", 
                                  trend_sources: Optional[List[str]] = None) -> Dict[str, Any]:
        trend_id = str(uuid.uuid4())
        
        prompt = f"""
        Industry: {industry}
        Timeframe: {timeframe}
        Trend Sources: {trend_sources or ['social_media', 'search_trends', 'industry_reports']}
        
        Analyze current trends in this industry that could inform campaign ideation.
        """
        
        trend_analysis = self.nlp_processor.analyze_trends(prompt)
        
        trend_record = JackieTrendAnalysis(
            id=trend_id, industry=industry, timeframe=timeframe,
            trend_sources=json.dumps(trend_sources or []), analysis_data=json.dumps(trend_analysis),
            created_at=datetime.utcnow()
        )
        self.db.add(trend_record)
        self.db.commit()
        
        return {
            "trend_id": trend_id, "industry": industry, "timeframe": timeframe,
            "trend_analysis": trend_analysis, "created_at": trend_record.created_at.isoformat()
        }
    
    def get_industry_trends(self, industry: str, trend_category: Optional[str] = None,
                           limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        query = self.db.query(JackieTrendAnalysis).filter(JackieTrendAnalysis.industry == industry)
        
        if trend_category:
            query = query.filter(JackieTrendAnalysis.trend_category == trend_category)
        
        trends = query.offset(offset).limit(limit).all()
        
        return [{
            "id": trend.id, "industry": trend.industry, "timeframe": trend.timeframe,
            "trend_category": trend.trend_category, "analysis_data": json.loads(trend.analysis_data),
            "created_at": trend.created_at.isoformat()
        } for trend in trends]
    
    def analyze_competitor_campaigns(self, competitors: List[str], industry: str, 
                                   analysis_period: str = "90d") -> Dict[str, Any]:
        analysis_id = str(uuid.uuid4())
        
        prompt = f"""
        Competitors: {competitors}
        Industry: {industry}
        Analysis Period: {analysis_period}
        
        Analyze competitor campaigns to identify patterns, strategies, and opportunities.
        """
        
        competitor_analysis = self.nlp_processor.analyze_competitors(prompt)
        
        analysis_record = CompetitorAnalysis(
            id=analysis_id, competitors=json.dumps(competitors), industry=industry,
            analysis_period=analysis_period, analysis_data=json.dumps(competitor_analysis),
            created_at=datetime.utcnow()
        )
        self.db.add(analysis_record)
        self.db.commit()
        
        return {
            "analysis_id": analysis_id, "competitors": competitors, "industry": industry,
            "analysis_period": analysis_period, "competitor_analysis": competitor_analysis,
            "created_at": analysis_record.created_at.isoformat()
        }
    
    def get_competitor_campaigns(self, competitor: str, campaign_type: Optional[str] = None,
                                limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        query = self.db.query(CompetitorAnalysis).filter(
            CompetitorAnalysis.competitors.contains(competitor)
        )
        
        if campaign_type:
            query = query.filter(CompetitorAnalysis.campaign_type == campaign_type)
        
        campaigns = query.offset(offset).limit(limit).all()
        
        return [{
            "id": campaign.id, "competitor": competitor, "campaign_type": campaign.campaign_type,
            "analysis_data": json.loads(campaign.analysis_data), "created_at": campaign.created_at.isoformat()
        } for campaign in campaigns]
    
    def generate_inspiration(self, inspiration_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        prompt = f"""
        Inspiration Type: {inspiration_type}
        Context: {context}
        
        Generate inspiration for campaign ideation based on the specified type and context.
        """
        
        inspiration = self.nlp_processor.generate_inspiration(prompt, inspiration_type)
        
        return {
            "inspiration_type": inspiration_type, "context": context,
            "inspiration": inspiration, "generated_at": datetime.utcnow().isoformat()
        }
    
    def get_inspiration_sources(self, source_type: Optional[str] = None) -> List[Dict[str, Any]]:
        sources = [
            {"type": "social_media", "name": "Social Media Trends", "description": "Current trends on social platforms"},
            {"type": "industry_reports", "name": "Industry Reports", "description": "Latest industry insights and data"},
            {"type": "competitor_analysis", "name": "Competitor Analysis", "description": "Competitor campaign strategies"},
            {"type": "consumer_behavior", "name": "Consumer Behavior", "description": "Changing consumer preferences"},
            {"type": "technology_trends", "name": "Technology Trends", "description": "Emerging technologies and platforms"}
        ]
        
        if source_type:
            sources = [s for s in sources if s["type"] == source_type]
        
        return sources
    
    def start_brainstorming_session(self, session_config: Dict[str, Any]) -> Dict[str, Any]:
        session_id = str(uuid.uuid4())
        
        session = BrainstormingSession(
            id=session_id, config=json.dumps(session_config), status="active",
            created_at=datetime.utcnow()
        )
        self.db.add(session)
        self.db.commit()
        
        return {
            "session_id": session_id,
            "session_status": "active",
            "config": session_config,
            "created_at": session.created_at.isoformat()
        }
    
    def get_brainstorming_ideas(self, session_id: str, idea_category: Optional[str] = None,
                               limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        session = self.db.query(BrainstormingSession).filter(BrainstormingSession.id == session_id).first()
        if not session:
            return []
        
        ideas = self.db.query(CampaignIdea).filter(
            CampaignIdea.brainstorming_session_id == session_id
        )
        
        if idea_category:
            ideas = ideas.filter(CampaignIdea.concept_type == idea_category)
        
        ideas = ideas.offset(offset).limit(limit).all()
        
        return [{
            "id": idea.id, "title": idea.title, "description": idea.description,
            "concept_type": idea.concept_type, "created_at": idea.created_at.isoformat()
        } for idea in ideas]
    
    def add_brainstorming_idea(self, session_id: str, idea_content: str, 
                              idea_category: str = "general") -> Dict[str, Any]:
        session = self.db.query(BrainstormingSession).filter(BrainstormingSession.id == session_id).first()
        if not session:
            raise Exception("Brainstorming session not found")
        
        idea_id = str(uuid.uuid4())
        idea = CampaignIdea(
            id=idea_id, title=f"Brainstorming Idea - {idea_category}",
            description=idea_content, concept_type=idea_category,
            brainstorming_session_id=session_id, created_at=datetime.utcnow()
        )
        self.db.add(idea)
        self.db.commit()
        
        return {
            "idea_id": idea_id,
            "session_id": session_id,
            "idea_content": idea_content,
            "idea_category": idea_category
        }
    
    def rate_campaign_idea(self, idea_id: str, rating: int, feedback: Optional[str] = None) -> Optional[Dict[str, Any]]:
        idea = self.db.query(CampaignIdea).filter(CampaignIdea.id == idea_id).first()
        if not idea:
            return None
        
        idea.rating = rating
        idea.feedback = feedback
        idea.rated_at = datetime.utcnow()
        self.db.commit()
        
        return {
            "idea_id": idea_id,
            "rating": rating,
            "feedback": feedback,
            "rated_at": idea.rated_at.isoformat()
        }
    
    def get_idea_ratings(self, idea_id: str) -> Optional[Dict[str, Any]]:
        idea = self.db.query(CampaignIdea).filter(CampaignIdea.id == idea_id).first()
        if not idea:
            return None
        
        return {
            "idea_id": idea_id,
            "rating": idea.rating,
            "feedback": idea.feedback,
            "rated_at": idea.rated_at.isoformat() if idea.rated_at else None
        }
    
    def favorite_campaign_idea(self, idea_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        idea = self.db.query(CampaignIdea).filter(CampaignIdea.id == idea_id).first()
        if not idea:
            return None
        
        favorites = json.loads(idea.favorites or "[]")
        if user_id not in favorites:
            favorites.append(user_id)
            idea.favorites = json.dumps(favorites)
            idea.updated_at = datetime.utcnow()
            self.db.commit()
        
        return {
            "idea_id": idea_id,
            "user_id": user_id,
            "favorited": True
        }
    
    def get_user_favorites(self, user_id: str, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        ideas = self.db.query(CampaignIdea).filter(
            CampaignIdea.favorites.contains(user_id)
        ).offset(offset).limit(limit).all()
        
        return [{
            "id": idea.id, "title": idea.title, "description": idea.description,
            "concept_type": idea.concept_type, "created_at": idea.created_at.isoformat()
        } for idea in ideas]
    
    def share_campaign_idea(self, idea_id: str, share_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        idea = self.db.query(CampaignIdea).filter(CampaignIdea.id == idea_id).first()
        if not idea:
            return None
        
        share_url = f"/campaign-ideas/{idea_id}?shared=true"
        
        return {
            "idea_id": idea_id,
            "share_url": share_url,
            "share_config": share_config
        }
    
    def batch_generate_ideas(self, batch_config: Dict[str, Any]) -> Dict[str, Any]:
        ideas = []
        generated_count = 0
        
        for config in batch_config.get("configs", []):
            try:
                batch_ideas = self.generate_campaign_ideas(**config)
                ideas.extend(batch_ideas)
                generated_count += len(batch_ideas)
            except Exception as e:
                print(f"Error generating ideas for config {config}: {str(e)}")
        
        return {
            "generated_count": generated_count,
            "ideas": ideas,
            "batch_config": batch_config
        }
    
    def get_top_rated_ideas(self, industry: Optional[str] = None, timeframe: str = "30d", 
                           limit: int = 20) -> List[Dict[str, Any]]:
        query = self.db.query(CampaignIdea).filter(CampaignIdea.rating.isnot(None))
        
        if industry:
            query = query.filter(CampaignIdea.industry == industry)
        
        if timeframe == "30d":
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            query = query.filter(CampaignIdea.created_at >= cutoff_date)
        
        ideas = query.order_by(CampaignIdea.rating.desc()).limit(limit).all()
        
        return [{
            "id": idea.id, "title": idea.title, "description": idea.description,
            "concept_type": idea.concept_type, "rating": idea.rating,
            "created_at": idea.created_at.isoformat()
        } for idea in ideas]
    
    def get_trending_ideas(self, industry: Optional[str] = None, timeframe: str = "7d", 
                          limit: int = 20) -> List[Dict[str, Any]]:
        query = self.db.query(CampaignIdea)
        
        if industry:
            query = query.filter(CampaignIdea.industry == industry)
        
        if timeframe == "7d":
            cutoff_date = datetime.utcnow() - timedelta(days=7)
            query = query.filter(CampaignIdea.created_at >= cutoff_date)
        
        ideas = query.order_by(CampaignIdea.created_at.desc()).limit(limit).all()
        
        return [{
            "id": idea.id, "title": idea.title, "description": idea.description,
            "concept_type": idea.concept_type, "created_at": idea.created_at.isoformat()
        } for idea in ideas]
    
    def duplicate_campaign_idea(self, idea_id: str, customization: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        original_idea = self.db.query(CampaignIdea).filter(CampaignIdea.id == idea_id).first()
        if not original_idea:
            return None
        
        new_idea_id = str(uuid.uuid4())
        new_idea = CampaignIdea(
            id=new_idea_id, title=f"{original_idea.title} (Copy)",
            description=original_idea.description, concept_type=original_idea.concept_type,
            target_audience=original_idea.target_audience, estimated_budget=original_idea.estimated_budget,
            expected_roi=original_idea.expected_roi, implementation_timeline=original_idea.implementation_timeline,
            risk_level=original_idea.risk_level, created_at=datetime.utcnow()
        )
        
        if customization:
            for key, value in customization.items():
                if hasattr(new_idea, key):
                    setattr(new_idea, key, value)
        
        self.db.add(new_idea)
        self.db.commit()
        
        return {
            "new_idea_id": new_idea_id,
            "original_idea_id": idea_id,
            "customization": customization
        }
    
    def get_ideation_analytics(self, timeframe: str = "30d") -> Dict[str, Any]:
        cutoff_date = datetime.utcnow() - timedelta(days=30 if timeframe == "30d" else 7)
        
        total_ideas = self.db.query(CampaignIdea).filter(
            CampaignIdea.created_at >= cutoff_date
        ).count()
        
        avg_rating = self.db.query(CampaignIdea).filter(
            CampaignIdea.rating.isnot(None),
            CampaignIdea.created_at >= cutoff_date
        ).with_entities(CampaignIdea.rating).all()
        
        avg_rating_value = sum(rating[0] for rating in avg_rating) / len(avg_rating) if avg_rating else 0
        
        return {
            "timeframe": timeframe, "total_ideas": total_ideas,
            "average_rating": avg_rating_value, "ideas_with_ratings": len(avg_rating)
        }
    
    def get_idea_performance_analytics(self, idea_id: str, metrics: List[str], 
                                     timeframe: str = "30d") -> Optional[Dict[str, Any]]:
        idea = self.db.query(CampaignIdea).filter(CampaignIdea.id == idea_id).first()
        if not idea:
            return None
        
        analytics = {}
        for metric in metrics:
            if metric == "rating":
                analytics[metric] = idea.rating
            elif metric == "favorites_count":
                favorites = json.loads(idea.favorites or "[]")
                analytics[metric] = len(favorites)
            elif metric == "age_days":
                age = (datetime.utcnow() - idea.created_at).days
                analytics[metric] = age
        
        return {
            "idea_id": idea_id, "metrics": analytics,
            "timeframe": timeframe, "analyzed_at": datetime.utcnow().isoformat()
        }
    
    def _validate_budget_feasibility(self, idea: CampaignIdea, requirements: Dict[str, Any]) -> Dict[str, Any]:
        estimated_budget = json.loads(idea.estimated_budget or "{}")
        max_budget = requirements.get("max_budget", float('inf'))
        
        total_budget = sum(estimated_budget.values()) if isinstance(estimated_budget, dict) else estimated_budget
        valid = total_budget <= max_budget
        
        return {"valid": valid, "estimated_budget": total_budget, "max_budget": max_budget}
    
    def _validate_audience_alignment(self, idea: CampaignIdea, requirements: Dict[str, Any]) -> Dict[str, Any]:
        target_audience = json.loads(idea.target_audience or "[]")
        required_audience = requirements.get("required_audience", [])
        
        alignment_score = len(set(target_audience) & set(required_audience)) / len(required_audience) if required_audience else 1.0
        valid = alignment_score >= requirements.get("min_alignment", 0.5)
        
        return {"valid": valid, "alignment_score": alignment_score, "target_audience": target_audience}
    
    def _validate_timeline_realistic(self, idea: CampaignIdea, requirements: Dict[str, Any]) -> Dict[str, Any]:
        timeline = idea.implementation_timeline
        max_timeline = requirements.get("max_timeline", "6 months")
        
        timeline_days = self._parse_timeline_to_days(timeline)
        max_days = self._parse_timeline_to_days(max_timeline)
        
        valid = timeline_days <= max_days
        
        return {"valid": valid, "timeline_days": timeline_days, "max_days": max_days}
    
    def _parse_timeline_to_days(self, timeline: str) -> int:
        if "month" in timeline.lower():
            return 30
        elif "week" in timeline.lower():
            return 7
        elif "day" in timeline.lower():
            return 1
        else:
            return 30
