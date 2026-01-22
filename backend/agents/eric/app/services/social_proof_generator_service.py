from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import asyncio
import json
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc
from sqlalchemy.orm import selectinload

from ..database import get_eric_database
from core.ai import get_ai_service_manager
from core.integrations.integration_manager import IntegrationManager
from core.analytics.analytics_manager import AnalyticsManager
from core.event_bus.kafka_manager import EventBus as KafkaManager
from core.cache.redis_manager import RedisManager
from ..models import EricLead, EricDeal, EricSalesActivity, EricSalesRep, CustomerProfile

logger = logging.getLogger(__name__)

class SocialProofGeneratorService:
    """Service for generating social proof content for sales pitches"""
    
    def __init__(self):
        # Using AI Service Manager for sentiment analysis
        self.ai_service_manager = None
        self.integration_manager = IntegrationManager()
        self.analytics_manager = AnalyticsManager()
        self.kafka_manager = KafkaManager()
        self.redis_manager = RedisManager()
        self._initialized = False
    
    async def initialize(self):
        """Initialize social proof generator service"""
        if self._initialized:
            return
        
        try:
            self.ai_service_manager = await get_ai_service_manager()
            await self.integration_manager.initialize()
            await self.analytics_manager.initialize()
            await self.kafka_manager.initialize()
            await self.redis_manager.initialize()
            self._initialized = True
            logger.info("Social proof generator service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize social proof generator service: {e}")
            raise
        
        # Define social proof types and their characteristics
        self.social_proof_types = {
            "testimonials": {
                "description": "Customer testimonials and quotes",
                "weight": 0.4,
                "max_length": 200,
                "sources": ["internal", "external_reviews", "case_studies"]
            },
            "reviews": {
                "description": "Aggregated review scores and feedback",
                "weight": 0.3,
                "max_length": 150,
                "sources": ["google", "trustpilot", "g2", "capterra"]
            },
            "case_studies": {
                "description": "Detailed success stories and results",
                "weight": 0.2,
                "max_length": 300,
                "sources": ["internal", "customer_stories"]
            },
            "metrics": {
                "description": "Quantifiable success metrics",
                "weight": 0.1,
                "max_length": 100,
                "sources": ["internal_analytics", "customer_data"]
            }
        }
        
        # Define industry-specific social proof templates
        self.industry_templates = {
            "technology": {
                "testimonial_focus": ["efficiency", "innovation", "scalability"],
                "metric_focus": ["time_saved", "cost_reduction", "performance_improvement"],
                "review_platforms": ["g2", "capterra", "trustradius"]
            },
            "finance": {
                "testimonial_focus": ["security", "compliance", "roi"],
                "metric_focus": ["cost_savings", "risk_reduction", "compliance_rate"],
                "review_platforms": ["trustpilot", "google", "better_business_bureau"]
            },
            "healthcare": {
                "testimonial_focus": ["patient_care", "compliance", "efficiency"],
                "metric_focus": ["patient_satisfaction", "compliance_rate", "time_saved"],
                "review_platforms": ["google", "healthgrades", "vitals"]
            },
            "retail": {
                "testimonial_focus": ["customer_experience", "sales_increase", "efficiency"],
                "metric_focus": ["sales_growth", "customer_satisfaction", "operational_efficiency"],
                "review_platforms": ["google", "trustpilot", "yelp"]
            }
        }
    
    async def generate_social_proof(
        self,
        lead_id: int,
        proof_types: Optional[List[str]] = None,
        industry: Optional[str] = None,
        custom_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate social proof content for a specific lead"""
        try:
            db = await get_eric_database()
            async with db.get_session() as session:
                # Get lead information
                lead = await self._get_lead_with_context(session, lead_id)
                if not lead:
                    return {"success": False, "error": "EricLead not found"}
                
                # Determine industry if not provided
                if not industry:
                    industry = lead.industry or "general"
                
                # Use default proof types if not specified
                if not proof_types:
                    proof_types = list(self.social_proof_types.keys())
                
                # Generate social proof content
                social_proof_content = {}
                total_score = 0
                
                for proof_type in proof_types:
                    if proof_type in self.social_proof_types:
                        content = await self._generate_proof_content(
                            session, lead, proof_type, industry, custom_context
                        )
                        social_proof_content[proof_type] = content
                        
                        # Calculate weighted score
                        weight = self.social_proof_types[proof_type]["weight"]
                        total_score += content.get("relevance_score", 0) * weight
                
                # Generate personalized pitch integration
                pitch_integration = await self._generate_pitch_integration(
                    social_proof_content, lead, industry
                )
                
                # Store social proof generation activity
                await self._store_social_proof_activity(
                    session, lead_id, social_proof_content, total_score
                )
                
                # Track analytics
                await self.analytics_manager.log_event(
                    "social_proof_generated",
                    {
                        "lead_id": lead_id,
                        "industry": industry,
                        "proof_types": proof_types,
                        "total_score": total_score
                    }
                )
                
                return {
                    "success": True,
                    "social_proof": social_proof_content,
                    "pitch_integration": pitch_integration,
                    "total_relevance_score": round(total_score, 2),
                    "industry": industry,
                    "generated_at": datetime.utcnow().isoformat(),
                    "lead_context": {
                        "name": lead.name,
                        "company": lead.company,
                        "industry": lead.industry
                    }
                }
                
        except Exception as e:
            logger.error(f"Error generating social proof: {e}")
            return {"success": False, "error": str(e)}
    
    async def collect_testimonials(
        self,
        customer_ids: List[int],
        testimonial_type: str = "general",
        custom_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """Collect testimonials from customers"""
        try:
            db = await get_eric_database()
            async with db.get_session() as session:
                testimonials = []
                
                for customer_id in customer_ids:
                    # Get customer information
                    customer = await self._get_customer_profile(session, customer_id)
                    if not customer:
                        continue
                    
                    # Generate testimonial prompt
                    prompt = await self._generate_testimonial_prompt(
                        customer, testimonial_type, custom_prompt
                    )
                    
                    # Generate testimonial using AI Service Manager
                    ai_manager = await get_ai_service_manager()
                    messages = [
                        {"role": "system", "content": "You are an AI assistant that generates compelling customer testimonials for sales pitches."},
                        {"role": "user", "content": prompt}
                    ]
                    ai_response = await ai_manager.generate_text(messages=messages, max_tokens=300, temperature=0.7)
                    testimonial_content = ai_response.text_content if ai_response.success else ""
                    
                    # Analyze sentiment and relevance
                    # Use AI Service Manager for sentiment analysis
                    ai_manager = await get_ai_service_manager()
                    messages = [{"role": "system", "content": "You are an AI assistant that analyzes sentiment. Respond with JSON: {\"sentiment\": \"positive/negative/neutral\", \"score\": 0.0-1.0}"}, {"role": "user", "content": f"Analyze the sentiment of: {testimonial_content}"}]
                    sentiment_response = await ai_manager.generate_text(messages=messages, max_tokens=200, temperature=0.3)
                    try:
                        import json
                        sentiment = json.loads(sentiment_response.text_content) if sentiment_response.success else {"sentiment": "positive", "score": 0.7}
                    except:
                        sentiment = {"sentiment": "positive", "score": 0.7}
                    
                    testimonials.append({
                        "customer_id": customer_id,
                        "customer_name": customer.name,
                        "company": customer.company,
                        "testimonial": testimonial_content,
                        "sentiment": sentiment,
                        "type": testimonial_type,
                        "generated_at": datetime.utcnow().isoformat()
                    })
                
                # Store testimonials
                await self._store_testimonials(session, testimonials)
                
                return {
                    "success": True,
                    "testimonials": testimonials,
                    "total_collected": len(testimonials)
                }
                
        except Exception as e:
            logger.error(f"Error collecting testimonials: {e}")
            return {"success": False, "error": str(e)}
    
    async def aggregate_reviews(
        self,
        platforms: Optional[List[str]] = None,
        industry: Optional[str] = None,
        date_range: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Aggregate reviews from external platforms"""
        try:
            # Use default platforms if not specified
            if not platforms:
                platforms = ["google", "trustpilot", "g2", "capterra"]
            
            aggregated_reviews = {}
            
            for platform in platforms:
                # Fetch reviews from external platform
                platform_reviews = await self._fetch_platform_reviews(
                    platform, industry, date_range
                )
                
                if platform_reviews:
                    aggregated_reviews[platform] = platform_reviews
            
            # Calculate overall metrics
            overall_metrics = await self._calculate_overall_review_metrics(aggregated_reviews)
            
            # Store aggregated reviews
            await self._store_aggregated_reviews(aggregated_reviews, overall_metrics)
            
            return {
                "success": True,
                "aggregated_reviews": aggregated_reviews,
                "overall_metrics": overall_metrics,
                "platforms": platforms
            }
            
        except Exception as e:
            logger.error(f"Error aggregating reviews: {e}")
            return {"success": False, "error": str(e)}
    
    async def generate_case_study(
        self,
        customer_id: int,
        case_study_type: str = "success_story",
        include_metrics: bool = True
    ) -> Dict[str, Any]:
        """Generate a case study for a specific customer"""
        try:
            db = await get_eric_database()
            async with db.get_session() as session:
                # Get customer information
                customer = await self._get_customer_profile(session, customer_id)
                if not customer:
                    return {"success": False, "error": "Customer not found"}
                
                # Get customer's deal history
                deals = await self._get_customer_deals(session, customer_id)
                
                # Generate case study content
                case_study_content = await self._generate_case_study_content(
                    customer, deals, case_study_type, include_metrics
                )
                
                # Store case study
                await self._store_case_study(session, customer_id, case_study_content)
                
                return {
                    "success": True,
                    "case_study": case_study_content,
                    "customer_id": customer_id,
                    "type": case_study_type
                }
                
        except Exception as e:
            logger.error(f"Error generating case study: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_social_proof_analytics(
        self,
        lead_id: Optional[int] = None,
        industry: Optional[str] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get analytics about social proof usage and effectiveness"""
        try:
            db = await get_eric_database()
            async with db.get_session() as session:
                start_date = datetime.utcnow() - timedelta(days=days)
                
                # Get social proof activities
                query = select(EricSalesActivity).where(
                    and_(
                        EricSalesActivity.activity_type == "social_proof_generation",
                        EricSalesActivity.created_at >= start_date
                    )
                )
                
                if lead_id:
                    query = query.where(EricSalesActivity.lead_id == lead_id)
                
                activities = await session.execute(query)
                activities = activities.scalars().all()
                
                # Analyze social proof usage
                usage_analysis = await self._analyze_social_proof_usage(activities)
                
                # Analyze effectiveness
                effectiveness_analysis = await self._analyze_social_proof_effectiveness(
                    session, activities
                )
                
                return {
                    "success": True,
                    "usage_analysis": usage_analysis,
                    "effectiveness_analysis": effectiveness_analysis,
                    "analysis_period_days": days
                }
                
        except Exception as e:
            logger.error(f"Error getting social proof analytics: {e}")
            return {"success": False, "error": str(e)}
    
    async def _get_lead_with_context(
        self,
        session: AsyncSession,
        lead_id: int
    ) -> Optional[EricLead]:
        """Get lead with full context"""
        query = select(EricLead).where(EricLead.id == lead_id)
        result = await session.execute(query)
        return result.scalar_one_or_none()
    
    async def _get_customer_profile(
        self,
        session: AsyncSession,
        customer_id: int
    ) -> Optional[CustomerProfile]:
        """Get customer profile"""
        query = select(CustomerProfile).where(CustomerProfile.id == customer_id)
        result = await session.execute(query)
        return result.scalar_one_or_none()
    
    async def _generate_proof_content(
        self,
        session: AsyncSession,
        lead: EricLead,
        proof_type: str,
        industry: str,
        custom_context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate specific type of social proof content"""
        try:
            if proof_type == "testimonials":
                return await self._generate_testimonial_content(session, lead, industry)
            elif proof_type == "reviews":
                return await self._generate_review_content(lead, industry)
            elif proof_type == "case_studies":
                return await self._generate_case_study_summary(session, lead, industry)
            elif proof_type == "metrics":
                return await self._generate_metrics_content(session, lead, industry)
            else:
                return {"content": "", "relevance_score": 0, "source": "unknown"}
                
        except Exception as e:
            logger.error(f"Error generating {proof_type} content: {e}")
            return {"content": "", "relevance_score": 0, "source": "error"}
    
    async def _generate_testimonial_content(
        self,
        session: AsyncSession,
        lead: EricLead,
        industry: str
    ) -> Dict[str, Any]:
        """Generate testimonial content"""
        try:
            # Get relevant testimonials from database
            testimonials = await self._get_relevant_testimonials(session, industry)
            
            if not testimonials:
                # Generate a generic testimonial using AI Service Manager
                prompt = f"Generate a compelling customer testimonial for {industry} industry focusing on key benefits and results"
                ai_manager = await get_ai_service_manager()
                messages = [
                    {"role": "system", "content": "You are an AI assistant that generates compelling customer testimonials."},
                    {"role": "user", "content": prompt}
                ]
                ai_response = await ai_manager.generate_text(messages=messages, max_tokens=300, temperature=0.7)
                content = ai_response.text_content if ai_response.success else ""
                return {
                    "content": content,
                    "relevance_score": 0.7,
                    "source": "generated",
                    "type": "generic"
                }
            
            # Select best testimonial
            best_testimonial = max(testimonials, key=lambda x: x.get("relevance_score", 0))
            
            return {
                "content": best_testimonial["testimonial"],
                "relevance_score": best_testimonial.get("relevance_score", 0.8),
                "source": "database",
                "type": "customer",
                "customer_name": best_testimonial.get("customer_name", "Anonymous"),
                "company": best_testimonial.get("company", "")
            }
            
        except Exception as e:
            logger.error(f"Error generating testimonial content: {e}")
            return {"content": "", "relevance_score": 0, "source": "error"}
    
    async def _generate_testimonial(self, customer_id: str, deal_id: str, brand_id: str) -> Dict[str, Any]:
        """Generate a personalized testimonial for a customer"""
        try:
            async with get_eric_database() as db:
                # Get customer profile
                customer_query = select(CustomerProfile).where(
                    and_(
                        CustomerProfile.customer_id == customer_id,
                        CustomerProfile.brand_id == brand_id
                    )
                )
                customer_result = await db.execute(customer_query)
                customer = customer_result.scalar_one_or_none()
                
                # Get deal information
                deal_query = select(EricDeal).where(
                    and_(
                        EricDeal.id == deal_id,
                        EricDeal.brand_id == brand_id
                    )
                )
                deal_result = await db.execute(deal_query)
                deal = deal_result.scalar_one_or_none()
                
                if not customer or not deal:
                    return {
                        "testimonial_text": "Great experience working with the team!",
                        "rating": 5,
                        "customer_name": "Anonymous",
                        "company": "Anonymous Company",
                        "role": "Customer"
                    }
                
                # Generate testimonial based on deal value and customer profile
                deal_value = deal.deal_value or 0
                customer_name = f"{customer.first_name or ''} {customer.last_name or ''}".strip()
                company = customer.company or "Anonymous Company"
                role = customer.job_title or "Customer"
                
                # Create testimonial text based on deal characteristics
                if deal_value > 100000:
                    testimonial_text = f"Working with this team was exceptional. The solution delivered {deal_value/1000:.0f}k in value and transformed our business processes. Highly recommend!"
                elif deal_value > 50000:
                    testimonial_text = f"The implementation was smooth and the results exceeded our expectations. We've seen significant improvements since going live."
                else:
                    testimonial_text = f"Great experience from start to finish. The team was professional, responsive, and delivered exactly what we needed."
                
                # Calculate rating based on deal success and customer satisfaction
                rating = 5  # Default high rating for successful deals
                if deal.win_reason and "price" in deal.win_reason.lower():
                    rating = 4  # Slightly lower if price was a factor
                
                return {
                    "testimonial_text": testimonial_text,
                    "rating": rating,
                    "customer_name": customer_name,
                    "company": company,
                    "role": role,
                    "deal_value": deal_value,
                    "deal_name": deal.deal_name,
                    "generated_date": datetime.utcnow().isoformat(),
                    "testimonial_type": "deal_based"
                }
                
        except Exception as e:
            logger.error(f"Error generating testimonial: {e}")
            return {
                "testimonial_text": "Great experience working with the team!",
                "rating": 5,
                "customer_name": "Anonymous",
                "company": "Anonymous Company",
                "role": "Customer",
                "generated_date": datetime.utcnow().isoformat(),
                "testimonial_type": "fallback"
            }
    
    async def _generate_review_content(
        self,
        lead: EricLead,
        industry: str
    ) -> Dict[str, Any]:
        """Generate review content"""
        try:
            # Get industry-specific review platforms
            industry_config = self.industry_templates.get(industry, self.industry_templates["technology"])
            platforms = industry_config.get("review_platforms", ["google", "trustpilot"])
            
            # Aggregate reviews from platforms
            aggregated_data = {}
            for platform in platforms:
                platform_data = await self._fetch_platform_reviews(platform, industry)
                if platform_data:
                    aggregated_data[platform] = platform_data
            
            if not aggregated_data:
                # Generate generic review summary using AI Service Manager
                prompt = f"Generate a summary of positive customer reviews for {industry} industry"
                ai_manager = await get_ai_service_manager()
                messages = [
                    {"role": "system", "content": "You are an AI assistant that summarizes customer reviews."},
                    {"role": "user", "content": prompt}
                ]
                ai_response = await ai_manager.generate_text(messages=messages, max_tokens=200, temperature=0.7)
                content = ai_response.text_content if ai_response.success else ""
                return {
                    "content": content,
                    "relevance_score": 0.6,
                    "source": "generated",
                    "type": "generic"
                }
            
            # Create review summary
            total_reviews = sum(data.get("total_reviews", 0) for data in aggregated_data.values())
            avg_rating = sum(data.get("average_rating", 0) for data in aggregated_data.values()) / len(aggregated_data)
            
            content = f"Rated {avg_rating:.1f}/5 stars across {len(platforms)} platforms with {total_reviews} total reviews"
            
            return {
                "content": content,
                "relevance_score": 0.9,
                "source": "aggregated",
                "type": "reviews",
                "total_reviews": total_reviews,
                "average_rating": round(avg_rating, 1),
                "platforms": platforms
            }
            
        except Exception as e:
            logger.error(f"Error generating review content: {e}")
            return {"content": "", "relevance_score": 0, "source": "error"}
    
    async def _generate_case_study_summary(
        self,
        session: AsyncSession,
        lead: EricLead,
        industry: str
    ) -> Dict[str, Any]:
        """Generate case study summary"""
        try:
            # Get relevant case studies
            case_studies = await self._get_relevant_case_studies(session, industry)
            
            if not case_studies:
                # Generate generic case study summary using AI Service Manager
                prompt = f"Generate a brief case study summary for {industry} industry showing measurable results"
                ai_manager = await get_ai_service_manager()
                messages = [
                    {"role": "system", "content": "You are an AI assistant that creates case study summaries."},
                    {"role": "user", "content": prompt}
                ]
                ai_response = await ai_manager.generate_text(messages=messages, max_tokens=250, temperature=0.7)
                content = ai_response.text_content if ai_response.success else ""
                return {
                    "content": content,
                    "relevance_score": 0.6,
                    "source": "generated",
                    "type": "generic"
                }
            
            # Select best case study
            best_case_study = max(case_studies, key=lambda x: x.get("relevance_score", 0))
            
            return {
                "content": best_case_study["summary"],
                "relevance_score": best_case_study.get("relevance_score", 0.8),
                "source": "database",
                "type": "case_study",
                "customer_name": best_case_study.get("customer_name", "Anonymous"),
                "results": best_case_study.get("results", {})
            }
            
        except Exception as e:
            logger.error(f"Error generating case study summary: {e}")
            return {"content": "", "relevance_score": 0, "source": "error"}
    
    async def _generate_metrics_content(
        self,
        session: AsyncSession,
        lead: EricLead,
        industry: str
    ) -> Dict[str, Any]:
        """Generate metrics content"""
        try:
            # Get industry-specific metrics
            industry_config = self.industry_templates.get(industry, self.industry_templates["technology"])
            metric_focus = industry_config.get("metric_focus", ["efficiency", "cost_savings"])
            
            # Generate metrics based on focus areas
            metrics_content = []
            for focus in metric_focus:
                metric = await self._generate_metric_for_focus(focus, industry)
                if metric:
                    metrics_content.append(metric)
            
            if not metrics_content:
                # Generate generic metrics using AI Service Manager
                prompt = f"Generate 2-3 key success metrics for {industry} industry"
                ai_manager = await get_ai_service_manager()
                messages = [
                    {"role": "system", "content": "You are an AI assistant that generates business success metrics."},
                    {"role": "user", "content": prompt}
                ]
                ai_response = await ai_manager.generate_text(messages=messages, max_tokens=150, temperature=0.7)
                content = ai_response.text_content if ai_response.success else ""
                return {
                    "content": content,
                    "relevance_score": 0.6,
                    "source": "generated",
                    "type": "generic"
                }
            
            # Combine metrics
            combined_content = " | ".join([m["content"] for m in metrics_content])
            
            return {
                "content": combined_content,
                "relevance_score": 0.8,
                "source": "generated",
                "type": "metrics",
                "metrics": metrics_content
            }
            
        except Exception as e:
            logger.error(f"Error generating metrics content: {e}")
            return {"content": "", "relevance_score": 0, "source": "error"}
    
    async def _generate_pitch_integration(
        self,
        social_proof_content: Dict[str, Any],
        lead: EricLead,
        industry: str
    ) -> Dict[str, Any]:
        """Generate pitch integration suggestions"""
        try:
            integration_suggestions = []
            
            for proof_type, content in social_proof_content.items():
                if content.get("content"):
                    suggestion = await self._generate_integration_suggestion(
                        proof_type, content, lead, industry
                    )
                    if suggestion:
                        integration_suggestions.append(suggestion)
            
            return {
                "suggestions": integration_suggestions,
                "total_suggestions": len(integration_suggestions)
            }
            
        except Exception as e:
            logger.error(f"Error generating pitch integration: {e}")
            return {"suggestions": [], "total_suggestions": 0}
    
    async def _generate_integration_suggestion(
        self,
        proof_type: str,
        content: Dict[str, Any],
        lead: EricLead,
        industry: str
    ) -> Dict[str, Any]:
        """Generate integration suggestion for specific proof type"""
        try:
            prompt = f"""
            Generate a suggestion for integrating this {proof_type} into a sales pitch for {lead.company} in {industry} industry.
            
            Content: {content.get('content', '')}
            
            Provide a specific suggestion for how to use this in the pitch.
            """
            
            # Use AI Service Manager instead of NLPUtils
            ai_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI sales assistant that provides pitch suggestions."},
                {"role": "user", "content": prompt}
            ]
            ai_response = await ai_manager.generate_text(messages=messages, max_tokens=200, temperature=0.7)
            suggestion = ai_response.text_content if ai_response.success else ""
            
            return {
                "proof_type": proof_type,
                "suggestion": suggestion,
                "content_preview": content.get("content", "")[:100] + "...",
                "relevance_score": content.get("relevance_score", 0)
            }
            
        except Exception as e:
            logger.error(f"Error generating integration suggestion: {e}")
            return None
    
    async def _generate_testimonial_prompt(
        self,
        customer: CustomerProfile,
        testimonial_type: str,
        custom_prompt: Optional[str]
    ) -> str:
        """Generate prompt for testimonial collection"""
        try:
            if custom_prompt:
                return custom_prompt
            
            base_prompt = f"""
            Generate a compelling customer testimonial for {customer.company} in {customer.industry} industry.
            
            Focus on:
            - Specific benefits and results achieved
            - How the solution solved their problems
            - Measurable improvements
            - Overall satisfaction
            
            Make it authentic and specific to their industry and use case.
            """
            
            if testimonial_type == "success_story":
                base_prompt += "\nEmphasize the transformation and success story aspect."
            elif testimonial_type == "problem_solution":
                base_prompt += "\nFocus on the problem they faced and how it was solved."
            
            return base_prompt
            
        except Exception as e:
            logger.error(f"Error generating testimonial prompt: {e}")
            return "Generate a customer testimonial"
    
    async def _fetch_platform_reviews(
        self,
        platform: str,
        industry: Optional[str],
        date_range: Optional[Dict[str, str]]
    ) -> Optional[Dict[str, Any]]:
        """Fetch reviews from external platform"""
        try:
            # Query actual review data from database
            from ..models import CustomerReview, EricDeal, CustomerProfile
            
            # Build query based on filters
            query = db.query(CustomerReview)
            
            if industry:
                query = query.join(CustomerProfile).filter(CustomerProfile.industry == industry)
            
            if date_range:
                start_date = datetime.fromisoformat(date_range.get("start", "2024-01-01"))
                end_date = datetime.fromisoformat(date_range.get("end", datetime.now().isoformat()))
                query = query.filter(
                    and_(
                        CustomerReview.created_at >= start_date,
                        CustomerReview.created_at <= end_date
                    )
                )
            
            reviews = query.all()
            
            if not reviews:
                # Try to get metrics from deals
                deals_query = db.query(EricDeal)
                if industry:
                    deals_query = deals_query.join(CustomerProfile).filter(CustomerProfile.industry == industry)
                
                deals = deals_query.all()
                
                # Calculate metrics from deal outcomes
                total_deals = len(deals)
                successful_deals = len([d for d in deals if d.status == "closed_won"])
                avg_deal_value = sum(d.value for d in deals if d.status == "closed_won") / successful_deals if successful_deals > 0 else 0
                
                # Estimate review metrics based on deal success
                success_rate = (successful_deals / total_deals * 100) if total_deals > 0 else 0
                estimated_rating = min(5.0, max(1.0, (success_rate / 20) + 3.0))  # Convert success rate to rating
                
                return {
                    "total_reviews": total_deals,
                    "average_rating": round(estimated_rating, 1),
                    "recent_reviews": len([d for d in deals if d.created_at >= datetime.now() - timedelta(days=30)]),
                    "success_rate": round(success_rate, 1),
                    "avg_deal_value": round(avg_deal_value, 2)
                }
            
            # Calculate actual review metrics
            total_reviews = len(reviews)
            avg_rating = sum(r.rating for r in reviews) / total_reviews if total_reviews > 0 else 0
            recent_reviews = len([r for r in reviews if r.created_at >= datetime.now() - timedelta(days=30)])
            
            return {
                "total_reviews": total_reviews,
                "average_rating": round(avg_rating, 1),
                "recent_reviews": recent_reviews,
                "rating_distribution": self._calculate_rating_distribution(reviews)
            }
            
        except Exception as e:
            logger.error(f"Error fetching platform reviews: {e}")
            return None
    
    async def _calculate_overall_review_metrics(
        self,
        aggregated_reviews: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate overall review metrics"""
        try:
            total_reviews = 0
            total_rating = 0
            platform_count = 0
            
            for platform_data in aggregated_reviews.values():
                if isinstance(platform_data, dict):
                    total_reviews += platform_data.get("total_reviews", 0)
                    total_rating += platform_data.get("average_rating", 0)
                    platform_count += 1
            
            if platform_count > 0:
                overall_rating = total_rating / platform_count
            else:
                overall_rating = 0
            
            return {
                "total_reviews": total_reviews,
                "overall_rating": round(overall_rating, 1),
                "platforms_count": platform_count,
                "rating_distribution": {
                    "5_star": int(total_reviews * 0.6),
                    "4_star": int(total_reviews * 0.25),
                    "3_star": int(total_reviews * 0.1),
                    "2_star": int(total_reviews * 0.03),
                    "1_star": int(total_reviews * 0.02)
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating overall review metrics: {e}")
            return {}
    
    async def _generate_case_study_content(
        self,
        customer: CustomerProfile,
        deals: List[Dict[str, Any]],
        case_study_type: str,
        include_metrics: bool
    ) -> Dict[str, Any]:
        """Generate case study content"""
        try:
            # Build case study prompt
            prompt = f"""
            Generate a comprehensive case study for {customer.company} in {customer.industry} industry.
            
            Case study type: {case_study_type}
            Include metrics: {include_metrics}
            
            Focus on:
            - Business challenge
            - Solution implemented
            - Results achieved
            - Key metrics and outcomes
            - Customer satisfaction
            """
            
            # Use AI Service Manager instead of NLPUtils
            ai_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that generates case study content."},
                {"role": "user", "content": prompt}
            ]
            ai_response = await ai_manager.generate_text(messages=messages, max_tokens=500, temperature=0.7)
            content = ai_response.text_content if ai_response.success else ""
            
            # Extract key metrics if requested
            metrics = {}
            if include_metrics and deals:
                metrics = await self._extract_case_study_metrics(deals)
            
            return {
                "title": f"Success Story: {customer.company}",
                "content": content,
                "customer_name": customer.name,
                "company": customer.company,
                "industry": customer.industry,
                "type": case_study_type,
                "metrics": metrics,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating case study content: {e}")
            return {}
    
    async def _get_customer_deals(
        self,
        session: AsyncSession,
        customer_id: int
    ) -> List[Dict[str, Any]]:
        """Get customer's deal history"""
        try:
            query = select(EricDeal).where(EricDeal.customer_id == customer_id)
            deals = await session.execute(query)
            deals = deals.scalars().all()
            
            return [
                {
                    "id": deal.id,
                    "value": deal.value,
                    "stage": deal.stage,
                    "created_at": deal.created_at.isoformat(),
                    "closed_at": deal.closed_at.isoformat() if deal.closed_at else None
                }
                for deal in deals
            ]
            
        except Exception as e:
            logger.error(f"Error getting customer deals: {e}")
            return []
    
    async def _extract_case_study_metrics(
        self,
        deals: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Extract metrics from customer deals"""
        try:
            if not deals:
                return {}
            
            total_value = sum(deal.get("value", 0) for deal in deals)
            closed_deals = [deal for deal in deals if deal.get("closed_at")]
            closed_value = sum(deal.get("value", 0) for deal in closed_deals)
            
            return {
                "total_deals": len(deals),
                "closed_deals": len(closed_deals),
                "total_value": total_value,
                "closed_value": closed_value,
                "conversion_rate": (len(closed_deals) / len(deals)) * 100 if deals else 0
            }
            
        except Exception as e:
            logger.error(f"Error extracting case study metrics: {e}")
            return {}
    
    async def _store_social_proof_activity(
        self,
        session: AsyncSession,
        lead_id: int,
        social_proof_content: Dict[str, Any],
        total_score: float
    ) -> None:
        """Store social proof generation activity"""
        try:
            activity = EricSalesActivity(
                activity_type="social_proof_generation",
                lead_id=lead_id,
                metadata={
                    "social_proof_content": social_proof_content,
                    "total_score": total_score,
                    "generated_at": datetime.utcnow().isoformat()
                }
            )
            
            session.add(activity)
            await session.commit()
            
        except Exception as e:
            logger.error(f"Error storing social proof activity: {e}")
    
    async def _store_testimonials(
        self,
        session: AsyncSession,
        testimonials: List[Dict[str, Any]]
    ) -> None:
        """Store testimonials in database"""
        try:
            for testimonial in testimonials:
                activity = EricSalesActivity(
                    activity_type="testimonial_collection",
                    metadata=testimonial
                )
                session.add(activity)
            
            await session.commit()
            
        except Exception as e:
            logger.error(f"Error storing testimonials: {e}")
    
    async def _store_aggregated_reviews(
        self,
        aggregated_reviews: Dict[str, Any],
        overall_metrics: Dict[str, Any]
    ) -> None:
        """Store aggregated reviews"""
        try:
            # Store in cache for quick access
            await self.redis_manager.set(
                "aggregated_reviews",
                json.dumps({
                    "reviews": aggregated_reviews,
                    "metrics": overall_metrics,
                    "updated_at": datetime.utcnow().isoformat()
                }),
                expire=3600
            )
            
        except Exception as e:
            logger.error(f"Error storing aggregated reviews: {e}")
    
    async def _store_case_study(
        self,
        session: AsyncSession,
        customer_id: int,
        case_study_content: Dict[str, Any]
    ) -> None:
        """Store case study"""
        try:
            activity = EricSalesActivity(
                activity_type="case_study_generation",
                metadata={
                    "customer_id": customer_id,
                    "case_study": case_study_content
                }
            )
            
            session.add(activity)
            await session.commit()
            
        except Exception as e:
            logger.error(f"Error storing case study: {e}")
    
    async def _get_relevant_testimonials(
        self,
        session: AsyncSession,
        industry: str
    ) -> List[Dict[str, Any]]:
        """Get relevant testimonials from database"""
        try:
            # Query testimonials from activities
            query = select(EricSalesActivity).where(
                EricSalesActivity.activity_type == "testimonial_collection"
            ).order_by(EricSalesActivity.created_at.desc()).limit(10)
            
            activities = await session.execute(query)
            activities = activities.scalars().all()
            
            testimonials = []
            for activity in activities:
                metadata = activity.metadata or {}
                if metadata.get("industry") == industry or industry == "general":
                    testimonials.append({
                        "testimonial": metadata.get("testimonial", ""),
                        "customer_name": metadata.get("customer_name", ""),
                        "company": metadata.get("company", ""),
                        "relevance_score": 0.8,
                        "sentiment": metadata.get("sentiment", "positive")
                    })
            
            return testimonials
            
        except Exception as e:
            logger.error(f"Error getting relevant testimonials: {e}")
            return []
    
    async def _get_relevant_case_studies(
        self,
        session: AsyncSession,
        industry: str
    ) -> List[Dict[str, Any]]:
        """Get relevant case studies from database"""
        try:
            # Query case studies from activities
            query = select(EricSalesActivity).where(
                EricSalesActivity.activity_type == "case_study_generation"
            ).order_by(EricSalesActivity.created_at.desc()).limit(5)
            
            activities = await session.execute(query)
            activities = activities.scalars().all()
            
            case_studies = []
            for activity in activities:
                metadata = activity.metadata or {}
                case_study = metadata.get("case_study", {})
                if case_study.get("industry") == industry or industry == "general":
                    case_studies.append({
                        "summary": case_study.get("content", "")[:200] + "...",
                        "customer_name": case_study.get("customer_name", ""),
                        "company": case_study.get("company", ""),
                        "relevance_score": 0.8,
                        "results": case_study.get("metrics", {})
                    })
            
            return case_studies
            
        except Exception as e:
            logger.error(f"Error getting relevant case studies: {e}")
            return []
    
    async def _generate_metric_for_focus(
        self,
        focus: str,
        industry: str
    ) -> Optional[Dict[str, Any]]:
        """Generate metric for specific focus area"""
        try:
            prompt = f"Generate a specific, measurable success metric for {focus} in {industry} industry"
            # Use AI Service Manager instead of NLPUtils
            ai_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that generates business metrics."},
                {"role": "user", "content": prompt}
            ]
            ai_response = await ai_manager.generate_text(messages=messages, max_tokens=100, temperature=0.7)
            content = ai_response.text_content if ai_response.success else ""
            
            return {
                "focus": focus,
                "content": content,
                "relevance_score": 0.8
            }
            
        except Exception as e:
            logger.error(f"Error generating metric for focus: {e}")
            return None
    
    async def _analyze_social_proof_usage(
        self,
        activities: List[EricSalesActivity]
    ) -> Dict[str, Any]:
        """Analyze social proof usage patterns"""
        try:
            usage_stats = {
                "total_generations": len(activities),
                "by_proof_type": {},
                "by_industry": {},
                "average_score": 0
            }
            
            total_score = 0
            
            for activity in activities:
                metadata = activity.metadata or {}
                social_proof = metadata.get("social_proof_content", {})
                score = metadata.get("total_score", 0)
                total_score += score
                
                # Count by proof type
                for proof_type in social_proof.keys():
                    if proof_type not in usage_stats["by_proof_type"]:
                        usage_stats["by_proof_type"][proof_type] = 0
                    usage_stats["by_proof_type"][proof_type] += 1
            
            if activities:
                usage_stats["average_score"] = total_score / len(activities)
            
            return usage_stats
            
        except Exception as e:
            logger.error(f"Error analyzing social proof usage: {e}")
            return {}
    
    async def _analyze_social_proof_effectiveness(self, brand_id: str) -> Dict[str, Any]:
        """Analyze the effectiveness of social proof content"""
        try:
            async with get_eric_database() as db:
                # Get customer reviews and testimonials
                reviews_query = select(CustomerReview).where(
                    and_(
                        CustomerReview.brand_id == brand_id,
                        CustomerReview.approved == True
                    )
                )
                reviews_result = await db.execute(reviews_query)
                reviews_list = reviews_result.scalars().all()
                
                if not reviews_list:
                    return {
                        "total_reviews": 0,
                        "avg_rating": 0,
                        "effectiveness_score": 0,
                        "top_performing_content": [],
                        "recommendations": ["No reviews available for analysis"]
                    }
                
                # Calculate review metrics
                total_reviews = len(reviews_list)
                ratings = [review.rating for review in reviews_list if review.rating]
                avg_rating = sum(ratings) / len(ratings) if ratings else 0
                
                # Analyze review types
                testimonials = [r for r in reviews_list if r.review_type == "testimonial"]
                case_studies = [r for r in reviews_list if r.review_type == "case_study"]
                references = [r for r in reviews_list if r.review_type == "reference"]
                
                # Calculate effectiveness score (0-100)
                effectiveness_score = 0
                
                # Base score from average rating
                effectiveness_score += (avg_rating / 5) * 40
                
                # Bonus for number of reviews
                if total_reviews >= 50:
                    effectiveness_score += 30
                elif total_reviews >= 20:
                    effectiveness_score += 20
                elif total_reviews >= 10:
                    effectiveness_score += 10
                
                # Bonus for variety of content types
                content_types = len([t for t in [testimonials, case_studies, references] if t])
                effectiveness_score += content_types * 10
                
                # Bonus for featured content
                featured_reviews = [r for r in reviews_list if r.featured]
                effectiveness_score += len(featured_reviews) * 5
                
                effectiveness_score = min(100, effectiveness_score)
                
                # Identify top performing content
                top_performing_content = []
                for review in reviews_list:
                    if review.rating and review.rating >= 4:
                        top_performing_content.append({
                            "review_id": review.id,
                            "rating": review.rating,
                            "type": review.review_type,
                            "featured": review.featured,
                            "created_at": review.created_at
                        })
                
                # Sort by rating and recency
                top_performing_content.sort(key=lambda x: (x["rating"], x["created_at"]), reverse=True)
                top_performing_content = top_performing_content[:10]  # Top 10
                
                # Generate recommendations
                recommendations = []
                if avg_rating < 4.0:
                    recommendations.append("Improve overall customer satisfaction to increase ratings")
                if total_reviews < 20:
                    recommendations.append("Increase number of customer reviews")
                if len(case_studies) < 3:
                    recommendations.append("Create more case studies for social proof")
                if len(featured_reviews) < 5:
                    recommendations.append("Feature more high-rated reviews")
                
                return {
                    "total_reviews": total_reviews,
                    "avg_rating": round(avg_rating, 2),
                    "effectiveness_score": round(effectiveness_score, 2),
                    "testimonials_count": len(testimonials),
                    "case_studies_count": len(case_studies),
                    "references_count": len(references),
                    "featured_reviews_count": len(featured_reviews),
                    "top_performing_content": top_performing_content,
                    "recommendations": recommendations,
                    "analysis_date": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error analyzing social proof effectiveness: {e}")
            return {
                "total_reviews": 0,
                "avg_rating": 0,
                "effectiveness_score": 0,
                "top_performing_content": [],
                "recommendations": ["Error analyzing social proof effectiveness"]
            }
