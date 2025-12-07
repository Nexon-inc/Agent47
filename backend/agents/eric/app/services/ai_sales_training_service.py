from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy import select, and_, or_, func, desc, text
from sqlalchemy.ext.asyncio import AsyncSession
import json
import logging

from backend.core.cache.redis_manager import RedisManager
from backend.core.messaging.kafka_manager import KafkaManager
from backend.core.integrations.integration_manager import IntegrationManager
from backend.core.platforms.platform_manager import PlatformManager
# NLPUtils removed - not used
from ..database import get_eric_database
from ..models import (
    Lead, LeadInteraction, Deal, SalesActivity, Objection,
    SalesCampaign, EmailSequence, SalesTeam, SalesRep
)

logger = logging.getLogger(__name__)

class AISalesTrainingService:
    def __init__(self):
        self.ai_service_manager = None
        self.redis_manager = RedisManager()
        self.kafka_manager = KafkaManager()
        self.integration_manager = IntegrationManager()
        self.platform_manager = PlatformManager()
        self._initialized = False
        # NLPUtils removed - not used
    
    async def initialize(self):
        """Initialize AI sales training service"""
        if self._initialized:
            return
        
        try:
            from backend.core.ai import get_ai_service_manager
            self.ai_service_manager = await get_ai_service_manager()
            await self.redis_manager.initialize()
            await self.kafka_manager.initialize()
            await self.integration_manager.initialize()
            await self.platform_manager.initialize()
            self._initialized = True
            logger.info("AI sales training service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize AI sales training service: {e}")
            raise
        
        self.training_modules = {
            "prospecting": {
                "name": "Advanced Prospecting Techniques",
                "description": "Learn effective prospecting strategies and lead generation methods",
                "duration": 120,  # minutes
                "difficulty": "intermediate",
                "topics": [
                    "Cold calling techniques",
                    "LinkedIn prospecting",
                    "Email outreach strategies",
                    "Social selling fundamentals"
                ]
            },
            "objection_handling": {
                "name": "Objection Handling Mastery",
                "description": "Master the art of handling customer objections effectively",
                "duration": 90,
                "difficulty": "advanced",
                "topics": [
                    "Common objection types",
                    "Response frameworks",
                    "Psychological techniques",
                    "Practice scenarios"
                ]
            },
            "closing_techniques": {
                "name": "Sales Closing Strategies",
                "description": "Learn proven techniques to close deals successfully",
                "duration": 150,
                "difficulty": "advanced",
                "topics": [
                    "Assumptive closing",
                    "Alternative choice closing",
                    "Urgency and scarcity",
                    "Trial closing methods"
                ]
            },
            "negotiation": {
                "name": "Sales Negotiation Skills",
                "description": "Develop negotiation skills for better deal outcomes",
                "duration": 180,
                "difficulty": "advanced",
                "topics": [
                    "Negotiation psychology",
                    "Value-based selling",
                    "Price negotiation",
                    "Win-win strategies"
                ]
            },
            "product_knowledge": {
                "name": "Product Knowledge Mastery",
                "description": "Deep dive into product features and benefits",
                "duration": 60,
                "difficulty": "beginner",
                "topics": [
                    "Product features",
                    "Competitive advantages",
                    "Use cases and applications",
                    "Technical specifications"
                ]
            }
        }

    async def create_training_module(self, module_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new AI-powered training module"""
        try:
            db = await get_eric_database()
            async with db.get_session() as session:
                module = {
                    "module_id": f"module_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                    "title": module_data["title"],
                    "description": module_data["description"],
                    "category": module_data["category"],
                    "difficulty": module_data["difficulty"],
                    "duration": module_data["duration"],
                    "content": module_data["content"],
                    "assessments": module_data.get("assessments", []),
                    "prerequisites": module_data.get("prerequisites", []),
                    "brand_id": module_data["brand_id"],
                    "created_by": module_data["created_by"],
                    "status": "active",
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
                
                module_key = f"training_module:{module['module_id']}"
                await self.redis_manager.set(
                    module_key,
                    json.dumps(module, default=str),
                    expire=86400 * 365
                )
                
                await self._publish_training_event("module_created", module)
                
                return {
                    "success": True,
                    "module": module
                }
                
        except Exception as e:
            logger.error(f"Failed to create training module: {e}")
            return {"success": False, "error": str(e)}

    async def get_personalized_training_path(self, rep_id: int, brand_id: int) -> Dict[str, Any]:
        """Get personalized training path for a sales representative"""
        try:
            db = await get_eric_database()
            async with db.get_session() as session:
                rep = await session.execute(
                    select(SalesRep).where(SalesRep.id == rep_id)
                )
                rep = rep.scalar_one_or_none()
                
                if not rep:
                    return {"success": False, "error": "Sales representative not found"}
                
                performance_analysis = await self._analyze_rep_performance(session, rep_id)
                skill_gaps = await self._identify_skill_gaps(performance_analysis)
                recommended_modules = await self._get_recommended_modules(skill_gaps, brand_id)
                
                training_path = {
                    "rep_id": rep_id,
                    "rep_name": f"{rep.first_name} {rep.last_name}",
                    "current_level": await self._determine_skill_level(performance_analysis),
                    "performance_analysis": performance_analysis,
                    "skill_gaps": skill_gaps,
                    "recommended_modules": recommended_modules,
                    "estimated_completion_time": await self._estimate_completion_time(recommended_modules),
                    "priority_order": await self._prioritize_modules(recommended_modules, skill_gaps)
                }
                
                return {
                    "success": True,
                    "training_path": training_path
                }
                
        except Exception as e:
            logger.error(f"Failed to get personalized training path: {e}")
            return {"success": False, "error": str(e)}

    async def _analyze_rep_performance(self, session: AsyncSession, rep_id: int) -> Dict[str, Any]:
        """Analyze sales representative performance to identify training needs"""
        try:
            start_date = datetime.utcnow() - timedelta(days=90)
            
            deals = await session.execute(
                select(Deal).where(
                    Deal.assigned_to == rep_id,
                    Deal.created_at >= start_date
                )
            )
            deals = deals.scalars().all()
            
            leads = await session.execute(
                select(Lead).where(
                    Lead.assigned_to == rep_id,
                    Lead.created_at >= start_date
                )
            )
            leads = leads.scalars().all()
            
            objections = await session.execute(
                select(Objection).where(
                    Objection.assigned_to == rep_id,
                    Objection.created_at >= start_date
                )
            )
            objections = objections.scalars().all()
            
            activities = await session.execute(
                select(SalesActivity).where(
                    SalesActivity.assigned_to == rep_id,
                    SalesActivity.created_at >= start_date
                )
            )
            activities = activities.scalars().all()
            
            analysis = {
                "deals_closed": len([deal for deal in deals if deal.status == "closed_won"]),
                "deals_lost": len([deal for deal in deals if deal.status == "closed_lost"]),
                "conversion_rate": len([deal for deal in deals if deal.status == "closed_won"]) / len(deals) if deals else 0,
                "avg_deal_value": sum([deal.value for deal in deals if deal.status == "closed_won"]) / len([deal for deal in deals if deal.status == "closed_won"]) if [deal for deal in deals if deal.status == "closed_won"] else 0,
                "leads_generated": len(leads),
                "leads_qualified": len([lead for lead in leads if lead.lead_status == "qualified"]),
                "objections_handled": len(objections),
                "objection_resolution_rate": len([obj for obj in objections if obj.status == "resolved"]) / len(objections) if objections else 0,
                "activities_completed": len([activity for activity in activities if activity.status == "completed"]),
                "response_time": await self._calculate_avg_response_time(session, rep_id, start_date)
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze rep performance: {e}")
            return {}

    async def _identify_skill_gaps(self, performance_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify skill gaps based on performance analysis"""
        try:
            skill_gaps = []
            
            if performance_analysis.get("conversion_rate", 0) < 0.2:
                skill_gaps.append({
                    "skill": "closing_techniques",
                    "priority": "high",
                    "reason": "Low conversion rate indicates need for better closing skills",
                    "current_performance": performance_analysis.get("conversion_rate", 0),
                    "target_performance": 0.3
                })
            
            if performance_analysis.get("leads_generated", 0) < 20:
                skill_gaps.append({
                    "skill": "prospecting",
                    "priority": "high",
                    "reason": "Low lead generation indicates need for better prospecting skills",
                    "current_performance": performance_analysis.get("leads_generated", 0),
                    "target_performance": 30
                })
            
            if performance_analysis.get("objection_resolution_rate", 0) < 0.7:
                skill_gaps.append({
                    "skill": "objection_handling",
                    "priority": "medium",
                    "reason": "Low objection resolution rate indicates need for better objection handling",
                    "current_performance": performance_analysis.get("objection_resolution_rate", 0),
                    "target_performance": 0.8
                })
            
            if performance_analysis.get("avg_deal_value", 0) < 5000:
                skill_gaps.append({
                    "skill": "negotiation",
                    "priority": "medium",
                    "reason": "Low average deal value indicates need for better negotiation skills",
                    "current_performance": performance_analysis.get("avg_deal_value", 0),
                    "target_performance": 7500
                })
            
            if performance_analysis.get("response_time", 0) > 3600:  # More than 1 hour
                skill_gaps.append({
                    "skill": "time_management",
                    "priority": "medium",
                    "reason": "Slow response time indicates need for better time management",
                    "current_performance": performance_analysis.get("response_time", 0),
                    "target_performance": 1800  # 30 minutes
                })
            
            return skill_gaps
            
        except Exception as e:
            logger.error(f"Failed to identify skill gaps: {e}")
            return []

    async def _get_recommended_modules(self, skill_gaps: List[Dict[str, Any]], brand_id: int) -> List[Dict[str, Any]]:
        """Get recommended training modules based on skill gaps"""
        try:
            recommended_modules = []
            
            for gap in skill_gaps:
                skill = gap["skill"]
                if skill in self.training_modules:
                    module = self.training_modules[skill].copy()
                    module["priority"] = gap["priority"]
                    module["skill_gap"] = gap
                    recommended_modules.append(module)
            
            return recommended_modules
            
        except Exception as e:
            logger.error(f"Failed to get recommended modules: {e}")
            return []

    async def _determine_skill_level(self, performance_analysis: Dict[str, Any]) -> str:
        """Determine current skill level based on performance"""
        try:
            conversion_rate = performance_analysis.get("conversion_rate", 0)
            avg_deal_value = performance_analysis.get("avg_deal_value", 0)
            objection_resolution_rate = performance_analysis.get("objection_resolution_rate", 0)
            
            score = 0
            score += conversion_rate * 40  # 40% weight
            score += min(avg_deal_value / 10000, 1) * 30  # 30% weight
            score += objection_resolution_rate * 30  # 30% weight
            
            if score >= 0.8:
                return "expert"
            elif score >= 0.6:
                return "advanced"
            elif score >= 0.4:
                return "intermediate"
            else:
                return "beginner"
                
        except Exception as e:
            logger.error(f"Failed to determine skill level: {e}")
            return "beginner"

    async def _estimate_completion_time(self, recommended_modules: List[Dict[str, Any]]) -> int:
        """Estimate total completion time for recommended modules"""
        try:
            total_time = 0
            for module in recommended_modules:
                total_time += module.get("duration", 0)
            return total_time
            
        except Exception as e:
            logger.error(f"Failed to estimate completion time: {e}")
            return 0

    async def _prioritize_modules(self, recommended_modules: List[Dict[str, Any]], skill_gaps: List[Dict[str, Any]]) -> List[str]:
        """Prioritize training modules based on skill gaps"""
        try:
            priority_scores = {}
            
            for module in recommended_modules:
                score = 0
                skill = module.get("skill", "")
                
                for gap in skill_gaps:
                    if gap["skill"] == skill:
                        if gap["priority"] == "high":
                            score += 10
                        elif gap["priority"] == "medium":
                            score += 5
                        elif gap["priority"] == "low":
                            score += 2
                        
                        score += (gap["target_performance"] - gap["current_performance"]) / gap["target_performance"] * 5
                
                priority_scores[module.get("name", "")] = score
            
            sorted_modules = sorted(priority_scores.items(), key=lambda x: x[1], reverse=True)
            return [module[0] for module in sorted_modules]
            
        except Exception as e:
            logger.error(f"Failed to prioritize modules: {e}")
            return []

    async def start_training_session(self, rep_id: int, module_id: str) -> Dict[str, Any]:
        """Start a training session for a sales representative"""
        try:
            db = await get_eric_database()
            async with db.get_session() as session:
                module_key = f"training_module:{module_id}"
                module_data = await self.redis_manager.get(module_key)
                
                if not module_data:
                    return {"success": False, "error": "Training module not found"}
                
                module = json.loads(module_data)
                
                session_data = {
                    "session_id": f"session_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                    "rep_id": rep_id,
                    "module_id": module_id,
                    "module_title": module["title"],
                    "start_time": datetime.utcnow(),
                    "status": "in_progress",
                    "progress": 0,
                    "current_section": 0,
                    "assessments_completed": [],
                    "time_spent": 0
                }
                
                session_key = f"training_session:{session_data['session_id']}"
                await self.redis_manager.set(
                    session_key,
                    json.dumps(session_data, default=str),
                    expire=86400 * 7
                )
                
                await self._publish_training_event("session_started", session_data)
                
                return {
                    "success": True,
                    "session": session_data,
                    "module": module
                }
                
        except Exception as e:
            logger.error(f"Failed to start training session: {e}")
            return {"success": False, "error": str(e)}

    async def complete_training_assessment(self, session_id: str, assessment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Complete a training assessment"""
        try:
            session_key = f"training_session:{session_id}"
            session_data = await self.redis_manager.get(session_key)
            
            if not session_data:
                return {"success": False, "error": "Training session not found"}
            
            session = json.loads(session_data)
            
            assessment_result = await self._evaluate_assessment(assessment_data)
            
            assessment_record = {
                "assessment_id": f"assessment_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                "session_id": session_id,
                "rep_id": session["rep_id"],
                "module_id": session["module_id"],
                "questions": assessment_data["questions"],
                "answers": assessment_data["answers"],
                "score": assessment_result["score"],
                "feedback": assessment_result["feedback"],
                "completed_at": datetime.utcnow()
            }
            
            assessment_key = f"training_assessment:{assessment_record['assessment_id']}"
            await self.redis_manager.set(
                assessment_key,
                json.dumps(assessment_record, default=str),
                expire=86400 * 365
            )
            
            session["assessments_completed"].append(assessment_record["assessment_id"])
            session["progress"] = min(100, session["progress"] + 20)
            
            if session["progress"] >= 100:
                session["status"] = "completed"
                session["completion_time"] = datetime.utcnow()
                
                await self._award_training_completion(session["rep_id"], session["module_id"])
            
            await self.redis_manager.set(
                session_key,
                json.dumps(session, default=str),
                expire=86400 * 7
            )
            
            await self._publish_training_event("assessment_completed", assessment_record)
            
            return {
                "success": True,
                "assessment": assessment_record,
                "session_progress": session["progress"]
            }
            
        except Exception as e:
            logger.error(f"Failed to complete training assessment: {e}")
            return {"success": False, "error": str(e)}

    async def _evaluate_assessment(self, assessment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate training assessment and provide feedback"""
        try:
            questions = assessment_data["questions"]
            answers = assessment_data["answers"]
            
            correct_answers = 0
            total_questions = len(questions)
            feedback = []
            
            for i, question in enumerate(questions):
                user_answer = answers[i] if i < len(answers) else None
                correct_answer = question.get("correct_answer")
                
                if user_answer == correct_answer:
                    correct_answers += 1
                    feedback.append({
                        "question": question["text"],
                        "status": "correct",
                        "feedback": "Great job! You answered correctly."
                    })
                else:
                    feedback.append({
                        "question": question["text"],
                        "status": "incorrect",
                        "feedback": f"Correct answer: {correct_answer}. Consider reviewing this topic."
                    })
            
            score = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
            
            return {
                "score": score,
                "correct_answers": correct_answers,
                "total_questions": total_questions,
                "feedback": feedback
            }
            
        except Exception as e:
            logger.error(f"Failed to evaluate assessment: {e}")
            return {"score": 0, "feedback": []}

    async def _award_training_completion(self, rep_id: int, module_id: str) -> None:
        """Award points for training completion"""
        try:
            module_key = f"training_module:{module_id}"
            module_data = await self.redis_manager.get(module_key)
            
            if module_data:
                module = json.loads(module_data)
                points = module.get("duration", 60) // 10  # 1 point per 10 minutes
                
                await self._publish_training_event("training_completed", {
                    "rep_id": rep_id,
                    "module_id": module_id,
                    "points_awarded": points
                })
                
        except Exception as e:
            logger.error(f"Failed to award training completion: {e}")

    async def _calculate_avg_response_time(self, session: AsyncSession, rep_id: int, start_date: datetime) -> float:
        """Calculate average response time for a sales rep"""
        try:
            interactions = await session.execute(
                select(LeadInteraction).where(
                    LeadInteraction.assigned_to == rep_id,
                    LeadInteraction.created_at >= start_date,
                    LeadInteraction.response_time.isnot(None)
                )
            )
            interactions = interactions.scalars().all()
            
            if not interactions:
                return 0.0
            
            total_response_time = sum(interaction.response_time for interaction in interactions)
            return total_response_time / len(interactions)
            
        except Exception as e:
            logger.error(f"Failed to calculate avg response time: {e}")
            return 0.0

    async def _publish_training_event(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """Publish training event to Kafka"""
        try:
            event = {
                "event_type": event_type,
                "timestamp": datetime.utcnow().isoformat(),
                "data": event_data
            }
            
            await self.kafka_manager.publish("eric.training", event)
        except Exception as e:
            logger.error(f"Failed to publish training event: {e}")

    async def get_training_progress(self, rep_id: int) -> Dict[str, Any]:
        """Get training progress for a sales representative"""
        try:
            progress_data = {
                "rep_id": rep_id,
                "modules_completed": 0,
                "total_modules": len(self.training_modules),
                "completion_percentage": 0,
                "current_sessions": [],
                "completed_modules": [],
                "certificates": []
            }
            
            session_keys = await self.redis_manager.keys("training_session:*")
            
            for key in session_keys:
                session_data = await self.redis_manager.get(key)
                if session_data:
                    session = json.loads(session_data)
                    if session["rep_id"] == rep_id:
                        if session["status"] == "completed":
                            progress_data["modules_completed"] += 1
                            progress_data["completed_modules"].append({
                                "module_id": session["module_id"],
                                "module_title": session["module_title"],
                                "completion_time": session.get("completion_time", ""),
                                "score": session.get("final_score", 0)
                            })
                        elif session["status"] == "in_progress":
                            progress_data["current_sessions"].append(session)
            
            progress_data["completion_percentage"] = (progress_data["modules_completed"] / progress_data["total_modules"]) * 100
            
            return {
                "success": True,
                "progress": progress_data
            }
            
        except Exception as e:
            logger.error(f"Failed to get training progress: {e}")
            return {"success": False, "error": str(e)}

    async def _generate_training_content(self, training_type: str, target_audience: List[str]) -> Dict[str, Any]:
        """Generate personalized training content"""
        try:
            # Define training content based on type and audience
            content_modules = []
            
            if training_type == "objection_handling":
                content_modules = [
                    {
                        "module_name": "Price Objection Handling",
                        "duration_minutes": 15,
                        "content_type": "video",
                        "difficulty": "intermediate",
                        "key_points": [
                            "Understand customer budget constraints",
                            "Focus on value proposition",
                            "Provide payment flexibility options"
                        ]
                    },
                    {
                        "module_name": "Timeline Objection Handling",
                        "duration_minutes": 12,
                        "content_type": "interactive",
                        "difficulty": "beginner",
                        "key_points": [
                            "Address urgency concerns",
                            "Show implementation timeline",
                            "Highlight quick wins"
                        ]
                    }
                ]
            elif training_type == "closing_techniques":
                content_modules = [
                    {
                        "module_name": "Consultative Closing",
                        "duration_minutes": 20,
                        "content_type": "video",
                        "difficulty": "advanced",
                        "key_points": [
                            "Build trust through consultation",
                            "Identify decision makers",
                            "Create urgency naturally"
                        ]
                    },
                    {
                        "module_name": "Value-Based Closing",
                        "duration_minutes": 18,
                        "content_type": "interactive",
                        "difficulty": "intermediate",
                        "key_points": [
                            "Quantify value proposition",
                            "ROI demonstration",
                            "Competitive differentiation"
                        ]
                    }
                ]
            else:  # general sales training
                content_modules = [
                    {
                        "module_name": "Prospecting Fundamentals",
                        "duration_minutes": 25,
                        "content_type": "video",
                        "difficulty": "beginner",
                        "key_points": [
                            "Lead qualification criteria",
                            "Cold calling techniques",
                            "Follow-up strategies"
                        ]
                    }
                ]
            
            # Calculate total duration
            total_duration = sum(module["duration_minutes"] for module in content_modules)
            
            # Generate assessment questions
            assessment_questions = [
                {
                    "question": "What is the most effective way to handle price objections?",
                    "options": ["Lower the price", "Focus on value", "Offer discounts", "Walk away"],
                    "correct_answer": 1,
                    "explanation": "Focusing on value helps customers understand ROI"
                },
                {
                    "question": "When should you ask for the sale?",
                    "options": ["Immediately", "After building value", "Never", "Only at the end"],
                    "correct_answer": 1,
                    "explanation": "Ask for the sale after demonstrating clear value"
                }
            ]
            
            return {
                "training_type": training_type,
                "target_audience": target_audience,
                "content_modules": content_modules,
                "total_duration_minutes": total_duration,
                "assessment_questions": assessment_questions,
                "completion_criteria": {
                    "minimum_score": 80,
                    "required_modules": len(content_modules),
                    "time_limit_days": 30
                },
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating training content: {e}")
            return {
                "training_type": training_type,
                "target_audience": target_audience,
                "content_modules": [],
                "total_duration_minutes": 0,
                "assessment_questions": [],
                "completion_criteria": {
                    "minimum_score": 80,
                    "required_modules": 0,
                    "time_limit_days": 30
                }
            }
