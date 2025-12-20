import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session

from core.utils.nlp_utils import NLPProcessor
from core.cache.redis_manager import RedisManager
from ..models import OrganicStrategy, ContentPiece, SocialPost, CommunityEngagement

class OrganicMarketingService:
    def __init__(self, db: Session):
        self.db = db
        self.nlp_processor = NLPProcessor()
        self.redis_manager = RedisManager()
        
    def create_organic_strategy(self, business_info: Dict[str, Any], target_audience: List[str],
                               goals: List[str]) -> Dict[str, Any]:
        strategy_id = str(uuid.uuid4())
        
        prompt = f"""
        Business Info: {business_info}
        Target Audience: {target_audience}
        Goals: {goals}
        
        Create a comprehensive organic marketing strategy that requires no budget.
        """
        
        strategy_result = self.nlp_processor.create_organic_strategy(prompt)
        
        strategy = OrganicStrategy(
            id=strategy_id, business_info=json.dumps(business_info), target_audience=json.dumps(target_audience),
            goals=json.dumps(goals), strategy_plan=json.dumps(strategy_result.get("strategy_plan", {})),
            created_at=datetime.utcnow()
        )
        self.db.add(strategy)
        self.db.commit()
        
        return {"strategy_id": strategy_id, "strategy_plan": strategy_result.get("strategy_plan", {})}
    
    def generate_content_piece(self, topic: str, content_type: str, target_audience: List[str],
                              seo_keywords: List[str]) -> Dict[str, Any]:
        content_id = str(uuid.uuid4())
        
        prompt = f"""
        Topic: {topic}
        Content Type: {content_type}
        Target Audience: {target_audience}
        SEO Keywords: {seo_keywords}
        
        Generate high-quality organic content that will rank well and engage the audience.
        """
        
        content_result = self.nlp_processor.generate_organic_content(prompt)
        
        content = ContentPiece(
            id=content_id, topic=topic, content_type=content_type, target_audience=json.dumps(target_audience),
            seo_keywords=json.dumps(seo_keywords), content=content_result.get("content", ""),
            seo_score=content_result.get("seo_score", 0.0), created_at=datetime.utcnow()
        )
        self.db.add(content)
        self.db.commit()
        
        return {"content_id": content_id, "content": content_result.get("content", "")}
    
    def create_social_post(self, platform: str, content_brief: str, target_audience: List[str],
                          engagement_goals: Dict[str, Any]) -> Dict[str, Any]:
        post_id = str(uuid.uuid4())
        
        prompt = f"""
        Platform: {platform}
        Content Brief: {content_brief}
        Target Audience: {target_audience}
        Engagement Goals: {engagement_goals}
        
        Create an engaging organic social media post optimized for the platform.
        """
        
        post_result = self.nlp_processor.create_organic_social_post(prompt)
        
        post = SocialPost(
            id=post_id, platform=platform, content_brief=content_brief,
            target_audience=json.dumps(target_audience), engagement_goals=json.dumps(engagement_goals),
            post_content=post_result.get("post_content", ""), hashtags=json.dumps(post_result.get("hashtags", [])),
            created_at=datetime.utcnow()
        )
        self.db.add(post)
        self.db.commit()
        
        return {"post_id": post_id, "post_content": post_result.get("post_content", "")}
    
    def build_community_engagement(self, community_type: str, engagement_strategy: Dict[str, Any],
                                 target_members: List[str]) -> Dict[str, Any]:
        engagement_id = str(uuid.uuid4())
        
        prompt = f"""
        Community Type: {community_type}
        Engagement Strategy: {engagement_strategy}
        Target Members: {target_members}
        
        Create a community engagement plan to build organic relationships and brand awareness.
        """
        
        engagement_result = self.nlp_processor.build_community_engagement(prompt)
        
        engagement = CommunityEngagement(
            id=engagement_id, community_type=community_type,
            engagement_strategy=json.dumps(engagement_strategy), target_members=json.dumps(target_members),
            engagement_plan=json.dumps(engagement_result.get("engagement_plan", {})),
            created_at=datetime.utcnow()
        )
        self.db.add(engagement)
        self.db.commit()
        
        return {"engagement_id": engagement_id, "engagement_plan": engagement_result.get("engagement_plan", {})}
    
    def optimize_seo_organically(self, website_url: str, target_keywords: List[str],
                               industry: str) -> Dict[str, Any]:
        prompt = f"""
        Website URL: {website_url}
        Target Keywords: {target_keywords}
        Industry: {industry}
        
        Provide organic SEO optimization recommendations that don't require paid tools.
        """
        
        seo_result = self.nlp_processor.optimize_seo_organically(prompt)
        
        return {
            "website_url": website_url, "target_keywords": target_keywords,
            "seo_recommendations": seo_result.get("recommendations", []),
            "content_suggestions": seo_result.get("content_suggestions", [])
        }
    
    def create_guest_posting_strategy(self, industry: str, target_publications: List[str],
                                    content_themes: List[str]) -> Dict[str, Any]:
        prompt = f"""
        Industry: {industry}
        Target Publications: {target_publications}
        Content Themes: {content_themes}
        
        Create a guest posting strategy to build organic backlinks and authority.
        """
        
        guest_posting_result = self.nlp_processor.create_guest_posting_strategy(prompt)
        
        return {
            "industry": industry, "target_publications": target_publications,
            "guest_posting_strategy": guest_posting_result.get("strategy", {}),
            "pitch_templates": guest_posting_result.get("pitch_templates", [])
        }
    
    def develop_influencer_relationships(self, industry: str, target_influencers: List[str],
                                       relationship_goals: Dict[str, Any]) -> Dict[str, Any]:
        prompt = f"""
        Industry: {industry}
        Target Influencers: {target_influencers}
        Relationship Goals: {relationship_goals}
        
        Develop a strategy for building organic relationships with influencers.
        """
        
        influencer_result = self.nlp_processor.develop_influencer_relationships(prompt)
        
        return {
            "industry": industry, "target_influencers": target_influencers,
            "relationship_strategy": influencer_result.get("strategy", {}),
            "outreach_templates": influencer_result.get("outreach_templates", [])
        }
    
    def create_user_generated_content_campaign(self, campaign_brief: Dict[str, Any],
                                             target_audience: List[str]) -> Dict[str, Any]:
        prompt = f"""
        Campaign Brief: {campaign_brief}
        Target Audience: {target_audience}
        
        Create a user-generated content campaign to build organic brand awareness.
        """
        
        ugc_result = self.nlp_processor.create_ugc_campaign(prompt)
        
        return {
            "campaign_brief": campaign_brief, "target_audience": target_audience,
            "ugc_strategy": ugc_result.get("strategy", {}),
            "campaign_ideas": ugc_result.get("campaign_ideas", [])
        }
    
    def optimize_local_seo(self, business_location: Dict[str, Any], local_keywords: List[str],
                          industry: str) -> Dict[str, Any]:
        prompt = f"""
        Business Location: {business_location}
        Local Keywords: {local_keywords}
        Industry: {industry}
        
        Provide local SEO optimization strategies for organic local search visibility.
        """
        
        local_seo_result = self.nlp_processor.optimize_local_seo(prompt)
        
        return {
            "business_location": business_location, "local_keywords": local_keywords,
            "local_seo_recommendations": local_seo_result.get("recommendations", []),
            "local_content_ideas": local_seo_result.get("content_ideas", [])
        }
    
    def create_email_newsletter_strategy(self, subscriber_segments: List[str],
                                       content_themes: List[str]) -> Dict[str, Any]:
        prompt = f"""
        Subscriber Segments: {subscriber_segments}
        Content Themes: {content_themes}
        
        Create an organic email newsletter strategy to build relationships and drive engagement.
        """
        
        newsletter_result = self.nlp_processor.create_email_newsletter_strategy(prompt)
        
        return {
            "subscriber_segments": subscriber_segments, "content_themes": content_themes,
            "newsletter_strategy": newsletter_result.get("strategy", {}),
            "content_calendar": newsletter_result.get("content_calendar", [])
        }
    
    def get_organic_analytics(self, timeframe: str = "30d") -> Dict[str, Any]:
        cutoff_date = datetime.utcnow() - timedelta(days=30 if timeframe == "30d" else 7)
        
        strategies_count = self.db.query(OrganicStrategy).filter(
            OrganicStrategy.created_at >= cutoff_date
        ).count()
        
        content_count = self.db.query(ContentPiece).filter(
            ContentPiece.created_at >= cutoff_date
        ).count()
        
        social_posts_count = self.db.query(SocialPost).filter(
            SocialPost.created_at >= cutoff_date
        ).count()
        
        engagement_count = self.db.query(CommunityEngagement).filter(
            CommunityEngagement.created_at >= cutoff_date
        ).count()
        
        return {
            "timeframe": timeframe, "strategies_count": strategies_count,
            "content_count": content_count, "social_posts_count": social_posts_count,
            "engagement_count": engagement_count
        }
    
    def batch_create_content(self, content_batch: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results = []
        
        for content_item in content_batch:
            try:
                result = self.generate_content_piece(
                    content_item.get("topic", ""),
                    content_item.get("content_type", "blog"),
                    content_item.get("target_audience", []),
                    content_item.get("seo_keywords", [])
                )
                results.append({"content_id": content_item.get("id"), "result": result})
            except Exception as e:
                results.append({"content_id": content_item.get("id"), "error": str(e)})
        
        return results
