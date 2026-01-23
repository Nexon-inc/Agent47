import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session

from core.utils.nlp_utils import NLPProcessor
from core.cache.redis_manager import RedisManager
from ..models import JackieMobileCampaign, JackiePushNotification, MobileContent, AppEngagement

class MobileCampaignService:
    def __init__(self, db: Session):
        self.db = db
        self.nlp_processor = NLPProcessor()
        self.redis_manager = RedisManager()
        
    def create_mobile_campaign(self, campaign_data: Dict[str, Any], mobile_platforms: List[str],
                              target_devices: List[str]) -> Dict[str, Any]:
        campaign_id = str(uuid.uuid4())
        
        prompt = f"""
        JackieCampaign Data: {campaign_data}
        Mobile Platforms: {mobile_platforms}
        Target Devices: {target_devices}
        
        Create a mobile-optimized campaign strategy.
        """
        
        campaign_result = self.nlp_processor.create_mobile_campaign(prompt)
        
        campaign = JackieMobileCampaign(
            id=campaign_id, campaign_data=json.dumps(campaign_data), mobile_platforms=json.dumps(mobile_platforms),
            target_devices=json.dumps(target_devices), campaign_strategy=json.dumps(campaign_result.get("strategy", {})),
            status="active", created_at=datetime.utcnow()
        )
        self.db.add(campaign)
        self.db.commit()
        
        return {"campaign_id": campaign_id, "strategy": campaign_result.get("strategy", {})}
    
    def send_push_notification(self, notification_data: Dict[str, Any], target_users: List[str],
                              notification_type: str) -> Dict[str, Any]:
        notification_id = str(uuid.uuid4())
        
        prompt = f"""
        Notification Data: {notification_data}
        Target Users: {target_users}
        Notification Type: {notification_type}
        
        Create an engaging push notification for mobile users.
        """
        
        notification_result = self.nlp_processor.create_push_notification(prompt)
        
        notification = JackiePushNotification(
            id=notification_id, notification_data=json.dumps(notification_data),
            target_users=json.dumps(target_users), notification_type=notification_type,
            notification_content=notification_result.get("content", ""),
            delivery_status="sent", created_at=datetime.utcnow()
        )
        self.db.add(notification)
        self.db.commit()
        
        return {"notification_id": notification_id, "content": notification_result.get("content", "")}
    
    def create_mobile_content(self, content_brief: Dict[str, Any], mobile_format: str,
                            target_platform: str) -> Dict[str, Any]:
        content_id = str(uuid.uuid4())
        
        prompt = f"""
        Content Brief: {content_brief}
        Mobile Format: {mobile_format}
        Target Platform: {target_platform}
        
        Create mobile-optimized content for the specified format and platform.
        """
        
        content_result = self.nlp_processor.create_mobile_content(prompt)
        
        content = MobileContent(
            id=content_id, content_brief=json.dumps(content_brief), mobile_format=mobile_format,
            target_platform=target_platform, content=content_result.get("content", ""),
            mobile_optimizations=json.dumps(content_result.get("optimizations", [])),
            created_at=datetime.utcnow()
        )
        self.db.add(content)
        self.db.commit()
        
        return {"content_id": content_id, "content": content_result.get("content", "")}
    
    def track_app_engagement(self, user_id: str, engagement_data: Dict[str, Any],
                           engagement_type: str) -> Dict[str, Any]:
        engagement_id = str(uuid.uuid4())
        
        engagement = AppEngagement(
            id=engagement_id, user_id=user_id, engagement_data=json.dumps(engagement_data),
            engagement_type=engagement_type, created_at=datetime.utcnow()
        )
        self.db.add(engagement)
        self.db.commit()
        
        return {"engagement_id": engagement_id, "user_id": user_id, "type": engagement_type}
    
    def optimize_mobile_campaign(self, campaign_id: str, optimization_goals: Dict[str, Any]) -> Dict[str, Any]:
        campaign = self.db.query(JackieMobileCampaign).filter(JackieMobileCampaign.id == campaign_id).first()
        if not campaign:
            raise Exception("Mobile campaign not found")
        
        prompt = f"""
        JackieCampaign Data: {campaign.campaign_data}
        Optimization Goals: {optimization_goals}
        
        Optimize the mobile campaign based on the specified goals.
        """
        
        optimization_result = self.nlp_processor.optimize_mobile_campaign(prompt)
        
        campaign.campaign_strategy = json.dumps(optimization_result.get("optimized_strategy", {}))
        campaign.updated_at = datetime.utcnow()
        self.db.commit()
        
        return {"campaign_id": campaign_id, "optimized_strategy": optimization_result.get("optimized_strategy", {})}
    
    def create_mobile_ad(self, ad_brief: Dict[str, Any], ad_format: str, target_platform: str) -> Dict[str, Any]:
        prompt = f"""
        Ad Brief: {ad_brief}
        Ad Format: {ad_format}
        Target Platform: {target_platform}
        
        Create a mobile-optimized ad for the specified format and platform.
        """
        
        ad_result = self.nlp_processor.create_mobile_ad(prompt)
        
        return {
            "ad_brief": ad_brief, "ad_format": ad_format, "target_platform": target_platform,
            "mobile_ad": ad_result.get("mobile_ad", ""), "optimizations": ad_result.get("optimizations", [])
        }
    
    def manage_mobile_budget(self, campaign_id: str, budget_data: Dict[str, Any]) -> Dict[str, Any]:
        prompt = f"""
        JackieCampaign ID: {campaign_id}
        Budget Data: {budget_data}
        
        Manage mobile campaign budget allocation and optimization.
        """
        
        budget_result = self.nlp_processor.manage_mobile_budget(prompt)
        
        return {
            "campaign_id": campaign_id, "budget_data": budget_data,
            "budget_recommendations": budget_result.get("recommendations", []),
            "allocation_strategy": budget_result.get("allocation_strategy", {})
        }
    
    def get_mobile_analytics(self, campaign_id: str, timeframe: str = "30d") -> Dict[str, Any]:
        cutoff_date = datetime.utcnow() - timedelta(days=30 if timeframe == "30d" else 7)
        
        notifications_sent = self.db.query(JackiePushNotification).filter(
            JackiePushNotification.created_at >= cutoff_date
        ).count()
        
        content_created = self.db.query(MobileContent).filter(
            MobileContent.created_at >= cutoff_date
        ).count()
        
        engagements = self.db.query(AppEngagement).filter(
            AppEngagement.created_at >= cutoff_date
        ).count()
        
        return {
            "campaign_id": campaign_id, "timeframe": timeframe,
            "notifications_sent": notifications_sent, "content_created": content_created,
            "engagements": engagements
        }
    
    def batch_send_notifications(self, notifications_batch: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results = []
        
        for notification_data in notifications_batch:
            try:
                result = self.send_push_notification(
                    notification_data.get("notification_data", {}),
                    notification_data.get("target_users", []),
                    notification_data.get("notification_type", "general")
                )
                results.append({"notification_id": notification_data.get("id"), "result": result})
            except Exception as e:
                results.append({"notification_id": notification_data.get("id"), "error": str(e)})
        
        return results
