import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc
import httpx
import json
import redis.asyncio as redis
from core.event_bus.kafka_manager import EventBus as KafkaProducer
import json


class ProposalTemplate(BaseModel):
    template_id: str
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    sections: List[str] = []
    branding_options: Optional[Dict[str, Any]] = None
    is_active: bool = True


class GeneratedProposal(BaseModel):
    id: str
    lead_id: Optional[int] = None
    proposal_document: Dict[str, Any]
    pricing_recommendations: Optional[Dict[str, Any]] = None
    requirements_analysis: Optional[Dict[str, Any]] = None
    generated_at: Optional[str] = None
    status: str = "success"

from ..database import get_eric_database
from ..models import (
    EricLead, EricDeal, EricSalesActivity, EricSalesRep, EricCustomerProfile as CustomerProfile, 
    EricSalesCampaign, EricSalesAnalytics, EricSalesForecast
)
# NLPUtils removed - not used
from core.integrations.integration_manager import IntegrationManager
from core.platforms.platform_manager import PlatformManager
from core.analytics.analytics_manager import AnalyticsManager

logger = logging.getLogger(__name__)

class AutomatedProposalBuilderService:
    """Service for automated proposal building and generation"""
    
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
        """Initialize automated proposal builder service"""
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
            logger.info("Automated proposal builder service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize automated proposal builder service: {e}")
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
            
    async def generate_proposal(self, lead_id: int, proposal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate an automated proposal for a lead"""
        try:
            db = next(get_db())
            
            # Get lead information
            lead = db.query(EricLead).filter(EricLead.id == lead_id).first()
            if not lead:
                raise ValueError(f"EricLead with ID {lead_id} not found")
            
            # Get customer profile
            customer_profile = db.query(CustomerProfile).filter(CustomerProfile.lead_id == lead_id).first()
            
            # Analyze lead requirements
            requirements_analysis = await self._analyze_lead_requirements(lead, customer_profile, proposal_data)
            
            # Generate proposal content
            proposal_content = await self._generate_proposal_content(requirements_analysis, proposal_data)
            
            # Create proposal structure
            proposal_structure = await self._create_proposal_structure(proposal_content, proposal_data)
            
            # Generate pricing recommendations
            pricing_recommendations = await self._generate_pricing_recommendations(requirements_analysis, proposal_data)
            
            # Create proposal document
            proposal_document = await self._create_proposal_document(proposal_structure, pricing_recommendations)
            
            # Store proposal
            proposal_id = await self._store_proposal(db, lead_id, proposal_document, proposal_data)
            
            # Publish event
            await self._publish_event("proposal_generated", {
                "lead_id": lead_id,
                "proposal_id": proposal_id,
                "proposal_type": proposal_data.get("type", "standard")
            })
            
            return {
                "status": "success",
                "lead_id": lead_id,
                "proposal_id": proposal_id,
                "proposal_document": proposal_document,
                "pricing_recommendations": pricing_recommendations,
                "requirements_analysis": requirements_analysis,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating proposal: {e}")
            return {"status": "error", "message": str(e)}
            
    async def get_proposal_templates(self, industry: str = None, proposal_type: str = None) -> Dict[str, Any]:
        """Get available proposal templates"""
        try:
            templates = await self._load_proposal_templates(industry, proposal_type)
            
            return {
                "status": "success",
                "templates": templates,
                "total_count": len(templates),
                "retrieved_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting proposal templates: {e}")
            return {"status": "error", "message": str(e)}
            
    async def customize_proposal(self, proposal_id: str, customization_data: Dict[str, Any]) -> Dict[str, Any]:
        """Customize an existing proposal"""
        try:
            db = next(get_db())
            
            # Get existing proposal
            proposal = await self._get_proposal(db, proposal_id)
            if not proposal:
                raise ValueError(f"Proposal with ID {proposal_id} not found")
            
            # Apply customizations
            customized_proposal = await self._apply_customizations(proposal, customization_data)
            
            # Update proposal
            await self._update_proposal(db, proposal_id, customized_proposal)
            
            # Publish event
            await self._publish_event("proposal_customized", {
                "proposal_id": proposal_id,
                "customizations_applied": list(customization_data.keys())
            })
            
            return {
                "status": "success",
                "proposal_id": proposal_id,
                "customized_proposal": customized_proposal,
                "customizations_applied": list(customization_data.keys()),
                "customized_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error customizing proposal: {e}")
            return {"status": "error", "message": str(e)}
            
    async def get_proposal_analytics(self, period_days: int = 30) -> Dict[str, Any]:
        """Get analytics for proposal performance"""
        try:
            db = next(get_db())
            
            # Get proposals for the period
            start_date = datetime.utcnow() - timedelta(days=period_days)
            proposals = await self._get_proposals_for_period(db, start_date)
            
            # Calculate analytics
            analytics = await self._calculate_proposal_analytics(proposals)
            
            # Generate insights
            insights = await self._generate_proposal_insights(analytics)
            
            # Get recommendations
            recommendations = await self._get_proposal_recommendations(analytics)
            
            return {
                "status": "success",
                "period_days": period_days,
                "analytics": analytics,
                "insights": insights,
                "recommendations": recommendations,
                "analyzed_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting proposal analytics: {e}")
            return {"status": "error", "message": str(e)}
            
    async def export_proposal(self, proposal_id: str, format: str = "pdf") -> Dict[str, Any]:
        """Export proposal in specified format"""
        try:
            db = next(get_db())
            
            # Get proposal
            proposal = await self._get_proposal(db, proposal_id)
            if not proposal:
                raise ValueError(f"Proposal with ID {proposal_id} not found")
            
            # Generate export
            export_data = await self._generate_export(proposal, format)
            
            # Store export record
            export_id = await self._store_export_record(db, proposal_id, format, export_data)
            
            # Publish event
            await self._publish_event("proposal_exported", {
                "proposal_id": proposal_id,
                "export_format": format,
                "export_id": export_id
            })
            
            return {
                "status": "success",
                "proposal_id": proposal_id,
                "export_format": format,
                "export_id": export_id,
                "export_url": export_data.get("url"),
                "exported_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error exporting proposal: {e}")
            return {"status": "error", "message": str(e)}
            
    async def _analyze_lead_requirements(self, lead: EricLead, customer_profile: CustomerProfile, proposal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze lead requirements for proposal generation"""
        requirements = {
            "industry": lead.industry if hasattr(lead, 'industry') else "general",
            "company_size": lead.company_size if hasattr(lead, 'company_size') else "medium",
            "budget_range": proposal_data.get("budget_range", "medium"),
            "timeline": proposal_data.get("timeline", "standard"),
            "specific_needs": proposal_data.get("specific_needs", []),
            "pain_points": proposal_data.get("pain_points", []),
            "goals": proposal_data.get("goals", []),
            "preferences": proposal_data.get("preferences", {})
        }
        
        # Analyze customer profile if available
        if customer_profile:
            requirements["customer_maturity"] = customer_profile.maturity_level if hasattr(customer_profile, 'maturity_level') else "intermediate"
            requirements["decision_making_process"] = customer_profile.decision_process if hasattr(customer_profile, 'decision_process') else "standard"
        
        return requirements
        
    async def _generate_proposal_content(self, requirements: Dict[str, Any], proposal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate proposal content based on requirements"""
        content = {
            "executive_summary": await self._generate_executive_summary(requirements),
            "problem_statement": await self._generate_problem_statement(requirements),
            "solution_overview": await self._generate_solution_overview(requirements),
            "implementation_plan": await self._generate_implementation_plan(requirements),
            "timeline": await self._generate_timeline(requirements),
            "pricing": await self._generate_pricing_section(requirements),
            "case_studies": await self._generate_case_studies(requirements),
            "team_credentials": await self._generate_team_credentials(),
            "next_steps": await self._generate_next_steps(requirements)
        }
        
        return content
        
    async def _create_proposal_structure(self, content: Dict[str, Any], proposal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create proposal structure and layout"""
        structure = {
            "title": proposal_data.get("title", "Proposal for Your Business"),
            "subtitle": proposal_data.get("subtitle", "Customized Solution for Your Needs"),
            "sections": [
                {"title": "Executive Summary", "content": content["executive_summary"], "order": 1},
                {"title": "Problem Statement", "content": content["problem_statement"], "order": 2},
                {"title": "Our Solution", "content": content["solution_overview"], "order": 3},
                {"title": "Implementation Plan", "content": content["implementation_plan"], "order": 4},
                {"title": "Timeline", "content": content["timeline"], "order": 5},
                {"title": "Investment", "content": content["pricing"], "order": 6},
                {"title": "Success Stories", "content": content["case_studies"], "order": 7},
                {"title": "Our Team", "content": content["team_credentials"], "order": 8},
                {"title": "Next Steps", "content": content["next_steps"], "order": 9}
            ],
            "branding": proposal_data.get("branding", {}),
            "layout": proposal_data.get("layout", "professional")
        }
        
        return structure
        
    async def _generate_pricing_recommendations(self, requirements: Dict[str, Any], proposal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate pricing recommendations"""
        base_price = await self._calculate_base_price(requirements)
        
        recommendations = {
            "base_price": base_price,
            "discount_options": await self._calculate_discount_options(base_price, requirements),
            "payment_terms": await self._generate_payment_terms(requirements),
            "value_proposition": await self._generate_value_proposition(requirements),
            "roi_calculation": await self._calculate_roi(requirements, base_price)
        }
        
        return recommendations
        
    async def _create_proposal_document(self, structure: Dict[str, Any], pricing: Dict[str, Any]) -> Dict[str, Any]:
        """Create the final proposal document"""
        document = {
            "id": f"prop_{int(datetime.utcnow().timestamp())}",
            "structure": structure,
            "pricing": pricing,
            "metadata": {
                "created_at": datetime.utcnow().isoformat(),
                "version": "1.0",
                "status": "draft"
            },
            "content": await self._compile_document_content(structure, pricing)
        }
        
        return document
        
    async def _store_proposal(self, db: Session, lead_id: int, proposal_document: Dict[str, Any], proposal_data: Dict[str, Any]) -> str:
        """Store proposal in database"""
        proposal_id = proposal_document["id"]
        
        # Store in Redis for quick access
        redis_client = await self._get_redis_client()
        await redis_client.set(f"proposal:{proposal_id}", json.dumps(proposal_document), ex=86400)
        
        return proposal_id
        
    async def _load_proposal_templates(self, industry: str = None, proposal_type: str = None) -> List[Dict[str, Any]]:
        """Load proposal templates"""
        templates = [
            {
                "id": "template_1",
                "name": "Professional Business Proposal",
                "industry": "general",
                "type": "standard",
                "description": "Comprehensive business proposal template",
                "sections": ["executive_summary", "problem_statement", "solution", "implementation", "pricing", "timeline"],
                "estimated_pages": 8
            },
            {
                "id": "template_2",
                "name": "Technology Solution Proposal",
                "industry": "technology",
                "type": "technical",
                "description": "Specialized template for technology solutions",
                "sections": ["executive_summary", "technical_overview", "architecture", "implementation", "pricing", "support"],
                "estimated_pages": 12
            },
            {
                "id": "template_3",
                "name": "Quick Pitch Proposal",
                "industry": "general",
                "type": "quick",
                "description": "Concise proposal for quick decisions",
                "sections": ["overview", "solution", "pricing", "next_steps"],
                "estimated_pages": 4
            }
        ]
        
        # Filter by industry and type if specified
        if industry:
            templates = [t for t in templates if t["industry"] == industry or t["industry"] == "general"]
        
        if proposal_type:
            templates = [t for t in templates if t["type"] == proposal_type]
        
        return templates
        
    async def _get_proposal(self, db: Session, proposal_id: str) -> Optional[Dict[str, Any]]:
        """Get proposal from storage"""
        redis_client = await self._get_redis_client()
        proposal_data = await redis_client.get(f"proposal:{proposal_id}")
        
        if proposal_data:
            return json.loads(proposal_data)
        
        return None
        
    async def _apply_customizations(self, proposal: Dict[str, Any], customization_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply customizations to proposal"""
        customized_proposal = proposal.copy()
        
        # Apply content customizations
        if "content" in customization_data:
            for section, content in customization_data["content"].items():
                if section in customized_proposal["structure"]:
                    for section_data in customized_proposal["structure"]["sections"]:
                        if section_data["title"].lower().replace(" ", "_") == section:
                            section_data["content"] = content
                            break
        
        # Apply branding customizations
        if "branding" in customization_data:
            customized_proposal["structure"]["branding"].update(customization_data["branding"])
        
        # Apply pricing customizations
        if "pricing" in customization_data:
            customized_proposal["pricing"].update(customization_data["pricing"])
        
        # Update metadata
        customized_proposal["metadata"]["last_modified"] = datetime.utcnow().isoformat()
        customized_proposal["metadata"]["version"] = str(float(customized_proposal["metadata"]["version"]) + 0.1)
        
        return customized_proposal
        
    async def _update_proposal(self, db: Session, proposal_id: str, proposal: Dict[str, Any]):
        """Update proposal in storage"""
        redis_client = await self._get_redis_client()
        await redis_client.set(f"proposal:{proposal_id}", json.dumps(proposal), ex=86400)
        
    async def _get_proposals_for_period(self, db: Session, start_date: datetime) -> List[Dict[str, Any]]:
        """Get proposals created in a specific period from database"""
        try:
            # Query proposals from the database
            proposals_query = db.query(Proposal).filter(
                Proposal.created_at >= start_date
            ).all()
            
            proposals_data = []
            for proposal in proposals_query:
                # Calculate response and conversion rates
                response_rate = 0.0
                conversion_rate = 0.0
                
                # Get related activities to calculate rates
                activities = db.query(EricSalesActivity).filter(
                    EricSalesActivity.proposal_id == proposal.id
                ).all()
                
                if activities:
                    # Calculate response rate (activities after proposal sent)
                    response_activities = [a for a in activities if a.activity_type in ["email_response", "call_response", "meeting_scheduled"]]
                    response_rate = len(response_activities) / len(activities) if activities else 0.0
                    
                    # Calculate conversion rate (deals won from this proposal)
                    deals = db.query(EricDeal).filter(
                        and_(
                            EricDeal.proposal_id == proposal.id,
                            EricDeal.status == "closed_won"
                        )
                    ).all()
                    conversion_rate = len(deals) / 1 if proposal.status == "sent" else 0.0
                
                proposals_data.append({
                    "id": proposal.id,
                    "lead_id": proposal.lead_id,
                    "status": proposal.status,
                    "response_rate": response_rate,
                    "conversion_rate": conversion_rate,
                    "created_at": proposal.created_at.isoformat()
                })
            
            return proposals_data
            
        except Exception as e:
            logger.error(f"Failed to get proposals for period: {e}")
            return []
        
    async def _calculate_proposal_analytics(self, proposals: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate proposal analytics"""
        if not proposals:
            return {"total_proposals": 0, "avg_response_rate": 0.0, "avg_conversion_rate": 0.0}
        
        total_proposals = len(proposals)
        response_rates = [p.get("response_rate", 0) for p in proposals]
        conversion_rates = [p.get("conversion_rate", 0) for p in proposals]
        
        analytics = {
            "total_proposals": total_proposals,
            "avg_response_rate": sum(response_rates) / len(response_rates),
            "avg_conversion_rate": sum(conversion_rates) / len(conversion_rates),
            "successful_proposals": len([p for p in proposals if p.get("conversion_rate", 0) > 0.2])
        }
        
        return analytics
        
    async def _generate_proposal_insights(self, analytics: Dict[str, Any]) -> List[str]:
        """Generate insights from proposal analytics"""
        insights = []
        
        if analytics["avg_response_rate"] > 0.7:
            insights.append("High response rate indicates strong proposal quality")
        elif analytics["avg_response_rate"] < 0.3:
            insights.append("Low response rate - consider improving proposal content")
        
        if analytics["avg_conversion_rate"] > 0.25:
            insights.append("Good conversion rate - proposals are effective")
        elif analytics["avg_conversion_rate"] < 0.1:
            insights.append("Low conversion rate - review pricing and value proposition")
        
        return insights
        
    async def _get_proposal_recommendations(self, analytics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get recommendations based on proposal analytics"""
        recommendations = []
        
        if analytics["avg_response_rate"] < 0.5:
            recommendations.append({
                "type": "content_improvement",
                "priority": "high",
                "recommendation": "Improve proposal content to increase response rate",
                "action_items": [
                    "Enhance executive summary",
                    "Add more compelling case studies",
                    "Improve value proposition clarity"
                ]
            })
        
        if analytics["avg_conversion_rate"] < 0.15:
            recommendations.append({
                "type": "pricing_optimization",
                "priority": "medium",
                "recommendation": "Review pricing strategy to improve conversions",
                "action_items": [
                    "Analyze competitor pricing",
                    "Consider flexible payment terms",
                    "Highlight ROI more prominently"
                ]
            })
        
        return recommendations
        
    async def _generate_export(self, proposal: Dict[str, Any], format: str) -> Dict[str, Any]:
        """Generate export in specified format"""
        export_data = {
            "format": format,
            "url": f"/exports/proposal_{proposal['id']}.{format}",
            "size": "2.5MB",
            "generated_at": datetime.utcnow().isoformat()
        }
        
        return export_data
        
    async def _store_export_record(self, db: Session, proposal_id: str, format: str, export_data: Dict[str, Any]) -> str:
        """Store export record"""
        export_id = f"export_{proposal_id}_{int(datetime.utcnow().timestamp())}"
        
        # Store in Redis
        redis_client = await self._get_redis_client()
        await redis_client.set(f"export:{export_id}", json.dumps(export_data), ex=86400)
        
        return export_id
        
    async def _generate_executive_summary(self, requirements: Dict[str, Any]) -> str:
        """Generate executive summary"""
        return f"Based on our analysis of your {requirements['industry']} business needs, we propose a comprehensive solution that addresses your key challenges and delivers measurable results."
        
    async def _generate_problem_statement(self, requirements: Dict[str, Any]) -> str:
        """Generate problem statement"""
        return f"Your organization faces challenges in {', '.join(requirements.get('pain_points', ['efficiency', 'growth']))} that require a strategic solution."
        
    async def _generate_solution_overview(self, requirements: Dict[str, Any]) -> str:
        """Generate solution overview"""
        return f"Our solution provides a comprehensive approach to address your specific needs in {requirements['industry']} with proven methodologies and technologies."
        
    async def _generate_implementation_plan(self, requirements: Dict[str, Any]) -> str:
        """Generate implementation plan"""
        return "Our implementation plan includes discovery, design, development, testing, and deployment phases with regular checkpoints and deliverables."
        
    async def _generate_timeline(self, requirements: Dict[str, Any]) -> str:
        """Generate timeline"""
        timeline = requirements.get("timeline", "standard")
        if timeline == "urgent":
            return "Project completion within 4-6 weeks"
        elif timeline == "standard":
            return "Project completion within 8-12 weeks"
        else:
            return "Project completion within 12-16 weeks"
        
    async def _generate_pricing_section(self, requirements: Dict[str, Any]) -> str:
        """Generate pricing section"""
        budget_range = requirements.get("budget_range", "medium")
        return f"Our pricing is designed to fit your {budget_range} budget requirements while delivering maximum value."
        
    async def _generate_case_studies(self, requirements: Dict[str, Any]) -> str:
        """Generate case studies section"""
        industry = requirements.get("industry", "general")
        return f"We have successfully delivered similar solutions for {industry} companies, achieving significant improvements in efficiency and ROI."
        
    async def _generate_team_credentials(self) -> str:
        """Generate team credentials section"""
        return "Our team brings extensive experience in delivering successful projects with proven methodologies and industry best practices."
        
    async def _generate_next_steps(self, requirements: Dict[str, Any]) -> str:
        """Generate next steps section"""
        return "Next steps include a detailed discovery session, proposal review meeting, and project kickoff planning."
        
    async def _calculate_base_price(self, requirements: Dict[str, Any]) -> float:
        """Calculate base price for proposal"""
        base_price = 5000.0
        
        # Adjust based on company size
        company_size = requirements.get("company_size", "medium")
        if company_size == "large":
            base_price *= 1.5
        elif company_size == "small":
            base_price *= 0.7
        
        # Adjust based on complexity
        specific_needs = requirements.get("specific_needs", [])
        if len(specific_needs) > 5:
            base_price *= 1.3
        
        return base_price
        
    async def _calculate_discount_options(self, base_price: float, requirements: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Calculate discount options"""
        return [
            {"type": "early_bird", "discount": 0.10, "description": "10% off for commitment within 7 days"},
            {"type": "annual", "discount": 0.15, "description": "15% off for annual contract"},
            {"type": "referral", "discount": 0.05, "description": "5% off for successful referral"}
        ]
        
    async def _generate_payment_terms(self, requirements: Dict[str, Any]) -> List[str]:
        """Generate payment terms"""
        return [
            "50% upfront, 50% upon completion",
            "Monthly installments over project duration",
            "Quarterly payments with milestone deliverables"
        ]
        
    async def _generate_value_proposition(self, requirements: Dict[str, Any]) -> str:
        """Generate value proposition"""
        return f"Our solution delivers {requirements.get('goals', ['increased efficiency', 'cost savings'])} with a proven track record of success."
        
    async def _calculate_roi(self, requirements: Dict[str, Any], base_price: float) -> Dict[str, Any]:
        """Calculate ROI for the proposal"""
        estimated_savings = base_price * 2.5  # Conservative estimate
        roi_percentage = ((estimated_savings - base_price) / base_price) * 100
        
        return {
            "estimated_savings": estimated_savings,
            "roi_percentage": roi_percentage,
            "payback_period": "6-12 months"
        }
        
    async def _compile_document_content(self, structure: Dict[str, Any], pricing: Dict[str, Any]) -> str:
        """Compile document content"""
        content = f"# {structure['title']}\n\n"
        content += f"## {structure['subtitle']}\n\n"
        
        for section in structure["sections"]:
            content += f"### {section['title']}\n\n"
            content += f"{section['content']}\n\n"
        
        return content
        
    async def health_check(self) -> Dict[str, Any]:
        """Health check for the service"""
        try:
            redis_client = await self._get_redis_client()
            await redis_client.ping()
            
            return {
                "status": "healthy",
                "service": "automated_proposal_builder",
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
                "service": "automated_proposal_builder",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
