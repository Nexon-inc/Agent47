import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session

from core.utils.nlp_utils import NLPProcessor
from core.cache.redis_manager import RedisManager
from ..models import PlatformOptimization, EmergingChannel, PlatformContent, ChannelStrategy

class PlatformOptimizationService:
    def __init__(self, db: Session):
        self.db = db
        self.nlp_processor = NLPProcessor()
        self.redis_manager = RedisManager()
        
    def optimize_for_tiktok(self, content_brief: Dict[str, Any], target_audience: List[str],
                           content_type: str = "video") -> Dict[str, Any]:
        optimization_id = str(uuid.uuid4())
        
        prompt = f"""
        Content Brief: {content_brief}
        Target Audience: {target_audience}
        Content Type: {content_type}
        
        Optimize content specifically for TikTok platform with trending elements.
        """
        
        tiktok_result = self.nlp_processor.optimize_for_tiktok(prompt)
        
        optimization = PlatformOptimization(
            id=optimization_id, platform="tiktok", content_brief=json.dumps(content_brief),
            target_audience=json.dumps(target_audience), content_type=content_type,
            optimization_data=json.dumps(tiktok_result), created_at=datetime.utcnow()
        )
        self.db.add(optimization)
        self.db.commit()
        
        return {"optimization_id": optimization_id, "tiktok_optimization": tiktok_result}
    
    def optimize_for_shopify_ads(self, product_data: Dict[str, Any], ad_format: str,
                               target_audience: List[str]) -> Dict[str, Any]:
        optimization_id = str(uuid.uuid4())
        
        prompt = f"""
        Product Data: {product_data}
        Ad Format: {ad_format}
        Target Audience: {target_audience}
        
        Optimize ads specifically for Shopify Ads platform.
        """
        
        shopify_result = self.nlp_processor.optimize_for_shopify_ads(prompt)
        
        optimization = PlatformOptimization(
            id=optimization_id, platform="shopify_ads", content_brief=json.dumps(product_data),
            target_audience=json.dumps(target_audience), content_type=ad_format,
            optimization_data=json.dumps(shopify_result), created_at=datetime.utcnow()
        )
        self.db.add(optimization)
        self.db.commit()
        
        return {"optimization_id": optimization_id, "shopify_optimization": shopify_result}
    
    def optimize_for_threads(self, content_brief: Dict[str, Any], engagement_goals: Dict[str, Any]) -> Dict[str, Any]:
        optimization_id = str(uuid.uuid4())
        
        prompt = f"""
        Content Brief: {content_brief}
        Engagement Goals: {engagement_goals}
        
        Optimize content specifically for Threads platform.
        """
        
        threads_result = self.nlp_processor.optimize_for_threads(prompt)
        
        optimization = PlatformOptimization(
            id=optimization_id, platform="threads", content_brief=json.dumps(content_brief),
            target_audience=json.dumps([]), content_type="text",
            optimization_data=json.dumps(threads_result), created_at=datetime.utcnow()
        )
        self.db.add(optimization)
        self.db.commit()
        
        return {"optimization_id": optimization_id, "threads_optimization": threads_result}
    
    def create_emerging_channel_strategy(self, channel_name: str, channel_data: Dict[str, Any],
                                       target_audience: List[str]) -> Dict[str, Any]:
        channel_id = str(uuid.uuid4())
        
        prompt = f"""
        Channel Name: {channel_name}
        Channel Data: {channel_data}
        Target Audience: {target_audience}
        
        Create a comprehensive strategy for the emerging channel.
        """
        
        strategy_result = self.nlp_processor.create_emerging_channel_strategy(prompt)
        
        channel = EmergingChannel(
            id=channel_id, channel_name=channel_name, channel_data=json.dumps(channel_data),
            target_audience=json.dumps(target_audience), strategy_data=json.dumps(strategy_result),
            created_at=datetime.utcnow()
        )
        self.db.add(channel)
        self.db.commit()
        
        return {"channel_id": channel_id, "strategy_data": strategy_result}
    
    def create_platform_content(self, platform: str, content_brief: Dict[str, Any],
                              platform_specific_requirements: Dict[str, Any]) -> Dict[str, Any]:
        content_id = str(uuid.uuid4())
        
        prompt = f"""
        Platform: {platform}
        Content Brief: {content_brief}
        Platform Requirements: {platform_specific_requirements}
        
        Create platform-specific content optimized for the target platform.
        """
        
        content_result = self.nlp_processor.create_platform_content(prompt)
        
        content = PlatformContent(
            id=content_id, platform=platform, content_brief=json.dumps(content_brief),
            platform_requirements=json.dumps(platform_specific_requirements),
            content_data=json.dumps(content_result), created_at=datetime.utcnow()
        )
        self.db.add(content)
        self.db.commit()
        
        return {"content_id": content_id, "content_data": content_result}
    
    def analyze_platform_trends(self, platform: str, trend_analysis: Dict[str, Any]) -> Dict[str, Any]:
        prompt = f"""
        Platform: {platform}
        Trend Analysis: {trend_analysis}
        
        Analyze current trends and opportunities on the platform.
        """
        
        trends_result = self.nlp_processor.analyze_platform_trends(prompt)
        
        return {
            "platform": platform, "trend_analysis": trend_analysis,
            "trends_data": trends_result
        }
    
    def get_platform_optimization_analytics(self, timeframe: str = "30d") -> Dict[str, Any]:
        cutoff_date = datetime.utcnow() - timedelta(days=30 if timeframe == "30d" else 7)
        
        optimizations_count = self.db.query(PlatformOptimization).filter(
            PlatformOptimization.created_at >= cutoff_date
        ).count()
        
        channels_created = self.db.query(EmergingChannel).filter(
            EmergingChannel.created_at >= cutoff_date
        ).count()
        
        content_created = self.db.query(PlatformContent).filter(
            PlatformContent.created_at >= cutoff_date
        ).count()
        
        return {
            "timeframe": timeframe, "optimizations_count": optimizations_count,
            "channels_created": channels_created, "content_created": content_created
        }
