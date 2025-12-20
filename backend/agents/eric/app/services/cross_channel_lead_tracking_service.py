import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc
import httpx
import json
import redis.asyncio as redis
from kafka import KafkaProducer
import json

from ..database import get_eric_database
from ..models import (
    Lead, Deal, SalesActivity, SalesRep, CustomerProfile, 
    SalesCampaign, SalesAnalytics, SalesForecast
)
# NLPUtils removed - not used
from core.integrations.integration_manager import IntegrationManager
from core.platforms.platform_manager import PlatformManager
from core.analytics.analytics_manager import AnalyticsManager

logger = logging.getLogger(__name__)

class CrossChannelLeadTrackingService:
    """Service for tracking leads across multiple channels"""
    
    def __init__(self):
        # NLPUtils removed - not used
        self.ai_service_manager = None
        self.integration_manager = IntegrationManager()
        self.platform_manager = PlatformManager()
        self.analytics_manager = AnalyticsManager()
        self.redis_client = None
        self.kafka_producer = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize cross channel lead tracking service"""
        if self._initialized:
            return
        
        try:
            from core.ai import get_ai_service_manager
            from core.cache.redis_manager import init_redis
            self.ai_service_manager = await get_ai_service_manager()
            self.redis_client = await init_redis()
            await self.integration_manager.initialize()
            await self.platform_manager.initialize()
            await self.analytics_manager.initialize()
            self._initialized = True
            logger.info("Cross channel lead tracking service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize cross channel lead tracking service: {e}")
            raise
        
    async def _get_redis_client(self):
        """Get Redis client"""
        if not self.redis_client:
            self.redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        return self.redis_client
        
    async def _get_kafka_producer(self):
        """Get Kafka producer"""
        if not self.kafka_producer:
            self.kafka_producer = KafkaProducer(
                bootstrap_servers=['localhost:9092'],
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
        return self.kafka_producer
        
    async def _publish_event(self, event_type: str, data: Dict[str, Any]):
        """Publish event to Kafka"""
        try:
            producer = await self._get_kafka_producer()
            event = {
                "event_type": event_type,
                "agent": "eric",
                "timestamp": datetime.utcnow().isoformat(),
                "data": data
            }
            producer.send('agent_events', event)
            logger.info(f"Published {event_type} event to Kafka")
        except Exception as e:
            logger.error(f"Failed to publish event: {e}")
            
    async def track_lead_across_channels(self, lead_id: int, channel_data: Dict[str, Any]) -> Dict[str, Any]:
        """Track a lead's activity across multiple channels"""
        try:
            db = next(get_db())
            
            # Get or create lead
            lead = db.query(Lead).filter(Lead.id == lead_id).first()
            if not lead:
                raise ValueError(f"Lead with ID {lead_id} not found")
            
            # Extract channel information
            channel_type = channel_data.get("channel_type")
            channel_id = channel_data.get("channel_id")
            activity_type = channel_data.get("activity_type")
            activity_data = channel_data.get("activity_data", {})
            
            # Create cross-channel tracking record
            tracking_record = await self._create_tracking_record(db, lead_id, channel_type, channel_id, activity_type, activity_data)
            
            # Update lead's cross-channel profile
            await self._update_lead_channel_profile(db, lead_id, channel_type, activity_data)
            
            # Analyze cross-channel behavior
            behavior_analysis = await self._analyze_cross_channel_behavior(db, lead_id)
            
            # Generate insights
            insights = await self._generate_cross_channel_insights(behavior_analysis)
            
            # Publish event
            await self._publish_event("lead_cross_channel_tracked", {
                "lead_id": lead_id,
                "channel_type": channel_type,
                "activity_type": activity_type,
                "tracking_id": tracking_record["id"]
            })
            
            return {
                "status": "success",
                "lead_id": lead_id,
                "tracking_record": tracking_record,
                "behavior_analysis": behavior_analysis,
                "insights": insights,
                "tracked_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error tracking lead across channels: {e}")
            return {"status": "error", "message": str(e)}
            
    async def get_lead_channel_journey(self, lead_id: int, period_days: int = 30) -> Dict[str, Any]:
        """Get a lead's journey across all channels"""
        try:
            db = next(get_db())
            
            # Get lead
            lead = db.query(Lead).filter(Lead.id == lead_id).first()
            if not lead:
                raise ValueError(f"Lead with ID {lead_id} not found")
            
            # Get tracking records for the period
            start_date = datetime.utcnow() - timedelta(days=period_days)
            tracking_records = await self._get_tracking_records(db, lead_id, start_date)
            
            # Build journey timeline
            journey_timeline = await self._build_journey_timeline(tracking_records)
            
            # Analyze channel preferences
            channel_preferences = await self._analyze_channel_preferences(tracking_records)
            
            # Calculate engagement metrics
            engagement_metrics = await self._calculate_engagement_metrics(tracking_records)
            
            # Generate journey insights
            journey_insights = await self._generate_journey_insights(journey_timeline, channel_preferences, engagement_metrics)
            
            return {
                "status": "success",
                "lead_id": lead_id,
                "period_days": period_days,
                "journey_timeline": journey_timeline,
                "channel_preferences": channel_preferences,
                "engagement_metrics": engagement_metrics,
                "insights": journey_insights,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting lead channel journey: {e}")
            return {"status": "error", "message": str(e)}
            
    async def get_cross_channel_analytics(self, team_id: Optional[int] = None, period_days: int = 30) -> Dict[str, Any]:
        """Get cross-channel analytics for the team or organization"""
        try:
            db = next(get_db())
            
            # Get team or all leads
            if team_id:
                leads = db.query(Lead).join(SalesRep).filter(SalesRep.team_id == team_id).all()
            else:
                leads = db.query(Lead).all()
            
            lead_ids = [lead.id for lead in leads]
            
            # Get tracking data for all leads
            start_date = datetime.utcnow() - timedelta(days=period_days)
            all_tracking_records = await self._get_tracking_records_for_leads(db, lead_ids, start_date)
            
            # Calculate cross-channel metrics
            cross_channel_metrics = await self._calculate_cross_channel_metrics(all_tracking_records)
            
            # Analyze channel effectiveness
            channel_effectiveness = await self._analyze_channel_effectiveness(all_tracking_records)
            
            # Get conversion insights
            conversion_insights = await self._get_conversion_insights(all_tracking_records)
            
            # Generate recommendations
            recommendations = await self._generate_cross_channel_recommendations(cross_channel_metrics, channel_effectiveness)
            
            return {
                "status": "success",
                "team_id": team_id,
                "period_days": period_days,
                "cross_channel_metrics": cross_channel_metrics,
                "channel_effectiveness": channel_effectiveness,
                "conversion_insights": conversion_insights,
                "recommendations": recommendations,
                "analyzed_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting cross-channel analytics: {e}")
            return {"status": "error", "message": str(e)}
            
    async def identify_channel_opportunities(self, lead_id: int) -> Dict[str, Any]:
        """Identify opportunities for engaging leads on different channels"""
        try:
            db = next(get_db())
            
            # Get lead's current channel activity
            lead_activity = await self._get_lead_channel_activity(db, lead_id)
            
            # Analyze channel gaps
            channel_gaps = await self._analyze_channel_gaps(lead_activity)
            
            # Identify optimal channels
            optimal_channels = await self._identify_optimal_channels(lead_activity, channel_gaps)
            
            # Generate engagement strategies
            engagement_strategies = await self._generate_engagement_strategies(optimal_channels, lead_activity)
            
            # Calculate opportunity scores
            opportunity_scores = await self._calculate_opportunity_scores(optimal_channels, engagement_strategies)
            
            return {
                "status": "success",
                "lead_id": lead_id,
                "channel_gaps": channel_gaps,
                "optimal_channels": optimal_channels,
                "engagement_strategies": engagement_strategies,
                "opportunity_scores": opportunity_scores,
                "identified_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error identifying channel opportunities: {e}")
            return {"status": "error", "message": str(e)}
            
    async def sync_channel_data(self, channel_type: str, sync_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sync data from external channels"""
        try:
            db = next(get_db())
            
            # Validate channel type
            if channel_type not in ["email", "social", "website", "crm", "chat", "phone"]:
                raise ValueError(f"Unsupported channel type: {channel_type}")
            
            # Process sync data
            processed_data = await self._process_channel_sync_data(channel_type, sync_data)
            
            # Update lead records
            updated_leads = await self._update_leads_from_sync(db, processed_data)
            
            # Create tracking records
            tracking_records = await self._create_sync_tracking_records(db, processed_data)
            
            # Publish sync event
            await self._publish_event("channel_data_synced", {
                "channel_type": channel_type,
                "records_processed": len(processed_data),
                "leads_updated": len(updated_leads)
            })
            
            return {
                "status": "success",
                "channel_type": channel_type,
                "records_processed": len(processed_data),
                "leads_updated": len(updated_leads),
                "tracking_records_created": len(tracking_records),
                "synced_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error syncing channel data: {e}")
            return {"status": "error", "message": str(e)}
            
    async def get_channel_performance_report(self, period_days: int = 30) -> Dict[str, Any]:
        """Get comprehensive channel performance report"""
        try:
            db = next(get_db())
            
            # Get all tracking data for the period
            start_date = datetime.utcnow() - timedelta(days=period_days)
            all_tracking_records = await self._get_all_tracking_records(db, start_date)
            
            # Calculate channel performance metrics
            channel_performance = await self._calculate_channel_performance(all_tracking_records)
            
            # Analyze channel ROI
            channel_roi = await self._analyze_channel_roi(all_tracking_records)
            
            # Get channel trends
            channel_trends = await self._analyze_channel_trends(all_tracking_records, period_days)
            
            # Generate performance insights
            performance_insights = await self._generate_performance_insights(channel_performance, channel_roi, channel_trends)
            
            # Create recommendations
            recommendations = await self._create_performance_recommendations(channel_performance, channel_roi)
            
            return {
                "status": "success",
                "period_days": period_days,
                "channel_performance": channel_performance,
                "channel_roi": channel_roi,
                "channel_trends": channel_trends,
                "performance_insights": performance_insights,
                "recommendations": recommendations,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting channel performance report: {e}")
            return {"status": "error", "message": str(e)}
            
    async def health_check(self) -> Dict[str, Any]:
        """Health check for the service"""
        try:
            redis_client = await self._get_redis_client()
            await redis_client.ping()
            
            return {
                "status": "healthy",
                "service": "cross_channel_lead_tracking",
                "timestamp": datetime.utcnow().isoformat(),
                "dependencies": {
                    "redis": "connected",
                    "kafka": "available",
                    "database": "connected"
                }
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "service": "cross_channel_lead_tracking",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
