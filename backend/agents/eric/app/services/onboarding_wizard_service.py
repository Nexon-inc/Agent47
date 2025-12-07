from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy import select, and_, func, text
from sqlalchemy.ext.asyncio import AsyncSession
import json
import logging
from pydantic import BaseModel

from backend.core.cache.redis_manager import RedisManager
from backend.core.messaging.kafka_manager import KafkaManager
from backend.core.integrations.integration_manager import IntegrationManager
from backend.core.platforms.platform_manager import PlatformManager
# NLPUtils removed - not used
from ..database import get_eric_database
from ..models import (
    Lead, LeadInteraction, Deal, SalesActivity, Objection,
    SalesCampaign, EmailSequence, SalesTeam, SalesRep, SalesAnalytics
)

logger = logging.getLogger(__name__)

class OnboardingStep(BaseModel):
    id: Optional[int] = None
    step_number: int
    step_name: str
    step_type: str  # setup, configuration, integration, training, completion
    title: str
    description: str
    instructions: List[str] = []
    required_fields: List[str] = []
    optional_fields: List[str] = []
    validation_rules: Dict[str, Any] = {}
    help_text: str = ""
    estimated_time: int = 5  # minutes
    is_completed: bool = False
    completed_at: Optional[datetime] = None
    user_data: Dict[str, Any] = {}

class OnboardingSession(BaseModel):
    id: Optional[int] = None
    user_id: str
    session_token: str
    current_step: int = 1
    total_steps: int = 10
    progress_percentage: float = 0.0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    is_active: bool = True
    user_preferences: Dict[str, Any] = {}
    completed_steps: List[int] = []

class OnboardingWizardService:
    def __init__(self):
        self.ai_service_manager = None
        self.redis_manager = RedisManager()
        self.kafka_manager = KafkaManager()
        self.integration_manager = IntegrationManager()
        self.platform_manager = PlatformManager()
        self._initialized = False
        # NLPUtils removed - not used
    
    async def initialize(self):
        """Initialize onboarding wizard service"""
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
            logger.info("Onboarding wizard service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize onboarding wizard service: {e}")
            raise
        
        # Define onboarding steps
        self.onboarding_steps = [
            {
                "step_number": 1,
                "step_name": "welcome",
                "step_type": "setup",
                "title": "Welcome to Eric - Your AI Sales Assistant",
                "description": "Let's get you set up with Eric in just a few minutes. We'll guide you through each step to get your sales automation running smoothly.",
                "instructions": [
                    "Review the overview of Eric's capabilities",
                    "Understand what we'll be setting up",
                    "Click 'Get Started' when ready"
                ],
                "required_fields": [],
                "optional_fields": ["company_name", "user_role"],
                "validation_rules": {},
                "help_text": "Eric is your AI-powered sales assistant that helps automate lead generation, personalize outreach, and provide insights to close deals faster.",
                "estimated_time": 2
            },
            {
                "step_number": 2,
                "step_name": "company_setup",
                "step_type": "configuration",
                "title": "Company Information",
                "description": "Tell us about your company so Eric can personalize your sales approach.",
                "instructions": [
                    "Enter your company name",
                    "Select your industry",
                    "Choose your company size",
                    "Specify your target market"
                ],
                "required_fields": ["company_name", "industry", "company_size", "target_market"],
                "optional_fields": ["website", "location", "description"],
                "validation_rules": {
                    "company_name": {"min_length": 2, "max_length": 100},
                    "industry": {"allowed_values": ["technology", "healthcare", "finance", "manufacturing", "retail", "education", "real_estate", "consulting", "other"]},
                    "company_size": {"allowed_values": ["startup", "small_business", "mid_market", "enterprise"]}
                },
                "help_text": "This information helps Eric understand your business context and tailor sales strategies accordingly.",
                "estimated_time": 3
            },
            {
                "step_number": 3,
                "step_name": "sales_goals",
                "step_type": "configuration",
                "title": "Sales Goals & Objectives",
                "description": "Define your sales goals to help Eric prioritize and optimize your sales activities.",
                "instructions": [
                    "Set your monthly sales target",
                    "Define your primary sales objectives",
                    "Specify your target conversion rate",
                    "Choose your sales cycle length"
                ],
                "required_fields": ["monthly_target", "primary_objectives", "target_conversion_rate", "sales_cycle_length"],
                "optional_fields": ["quarterly_target", "annual_target", "specific_goals"],
                "validation_rules": {
                    "monthly_target": {"type": "number", "min": 1000},
                    "target_conversion_rate": {"type": "number", "min": 0.1, "max": 50},
                    "sales_cycle_length": {"type": "number", "min": 1, "max": 365}
                },
                "help_text": "Clear goals help Eric focus on activities that drive results and measure success effectively.",
                "estimated_time": 4
            },
            {
                "step_number": 4,
                "step_name": "crm_integration",
                "step_type": "integration",
                "title": "CRM Integration",
                "description": "Connect Eric to your existing CRM to sync leads, contacts, and deals automatically.",
                "instructions": [
                    "Select your CRM platform",
                    "Enter your CRM credentials",
                    "Test the connection",
                    "Configure sync settings"
                ],
                "required_fields": ["crm_platform", "crm_credentials"],
                "optional_fields": ["sync_frequency", "custom_fields", "webhook_url"],
                "validation_rules": {
                    "crm_platform": {"allowed_values": ["salesforce", "hubspot", "pipedrive", "zoho", "freshsales", "none"]}
                },
                "help_text": "CRM integration enables seamless data flow between Eric and your existing sales tools.",
                "estimated_time": 5
            },
            {
                "step_number": 5,
                "step_name": "email_setup",
                "step_type": "configuration",
                "title": "Email Configuration",
                "description": "Set up your email integration for automated outreach and follow-ups.",
                "instructions": [
                    "Connect your email provider",
                    "Set up email templates",
                    "Configure sending limits",
                    "Test email delivery"
                ],
                "required_fields": ["email_provider", "email_credentials"],
                "optional_fields": ["email_templates", "sending_schedule", "bounce_handling"],
                "validation_rules": {
                    "email_provider": {"allowed_values": ["gmail", "outlook", "sendgrid", "mailgun", "ses"]}
                },
                "help_text": "Email integration allows Eric to send personalized outreach and automated follow-ups on your behalf.",
                "estimated_time": 6
            },
            {
                "step_number": 6,
                "step_name": "lead_sources",
                "step_type": "configuration",
                "title": "Lead Source Configuration",
                "description": "Configure where Eric should look for and capture leads.",
                "instructions": [
                    "Select lead sources to monitor",
                    "Configure website tracking",
                    "Set up social media monitoring",
                    "Define lead qualification criteria"
                ],
                "required_fields": ["lead_sources", "qualification_criteria"],
                "optional_fields": ["website_url", "social_media_accounts", "custom_sources"],
                "validation_rules": {
                    "lead_sources": {"min_items": 1},
                    "qualification_criteria": {"min_items": 1}
                },
                "help_text": "Lead source configuration helps Eric identify and capture qualified prospects from multiple channels.",
                "estimated_time": 4
            },
            {
                "step_number": 7,
                "step_name": "sales_process",
                "step_type": "configuration",
                "title": "Sales Process Setup",
                "description": "Define your sales process stages and workflows for Eric to follow.",
                "instructions": [
                    "Define your sales stages",
                    "Set up stage transitions",
                    "Configure automation rules",
                    "Define success criteria"
                ],
                "required_fields": ["sales_stages", "automation_rules"],
                "optional_fields": ["stage_durations", "handoff_rules", "escalation_criteria"],
                "validation_rules": {
                    "sales_stages": {"min_items": 3, "max_items": 10}
                },
                "help_text": "A well-defined sales process helps Eric move leads through your pipeline efficiently and consistently.",
                "estimated_time": 5
            },
            {
                "step_number": 8,
                "step_name": "team_setup",
                "step_type": "configuration",
                "title": "Sales Team Configuration",
                "description": "Set up your sales team members and their roles in Eric.",
                "instructions": [
                    "Add team members",
                    "Assign roles and permissions",
                    "Set up territories",
                    "Configure collaboration settings"
                ],
                "required_fields": ["team_members"],
                "optional_fields": ["roles_permissions", "territories", "collaboration_settings"],
                "validation_rules": {
                    "team_members": {"min_items": 1}
                },
                "help_text": "Team configuration enables collaboration and ensures proper lead distribution and follow-up.",
                "estimated_time": 4
            },
            {
                "step_number": 9,
                "step_name": "training",
                "step_type": "training",
                "title": "Quick Training & Demo",
                "description": "Learn how to use Eric effectively with interactive training and demos.",
                "instructions": [
                    "Watch the overview video",
                    "Complete interactive tutorials",
                    "Practice with sample data",
                    "Take the knowledge check"
                ],
                "required_fields": ["training_completed"],
                "optional_fields": ["preferred_learning_style", "training_feedback"],
                "validation_rules": {
                    "training_completed": {"type": "boolean", "required": True}
                },
                "help_text": "Training ensures you get the most value from Eric and understand how to use all features effectively.",
                "estimated_time": 8
            },
            {
                "step_number": 10,
                "step_name": "completion",
                "step_type": "completion",
                "title": "Setup Complete!",
                "description": "Congratulations! Eric is now configured and ready to help you close more deals.",
                "instructions": [
                    "Review your configuration",
                    "Start your first campaign",
                    "Schedule a follow-up call",
                    "Access your dashboard"
                ],
                "required_fields": [],
                "optional_fields": ["feedback", "next_steps"],
                "validation_rules": {},
                "help_text": "You're all set! Eric will start working immediately to help you achieve your sales goals.",
                "estimated_time": 2
            }
        ]
    
    async def create_onboarding_session(self, user_id: str) -> OnboardingSession:
        """Create a new onboarding session for a user"""
        async with get_eric_database() as session:
            try:
                # Generate session token
                session_token = self._generate_session_token()
                
                # Create onboarding session
                onboarding_session = OnboardingSession(
                    user_id=user_id,
                    session_token=session_token,
                    current_step=1,
                    total_steps=len(self.onboarding_steps),
                    progress_percentage=0.0,
                    started_at=datetime.utcnow(),
                    is_active=True,
                    user_preferences={},
                    completed_steps=[]
                )
                
                # Store in database (simplified for demo)
                onboarding_session.id = 1  # Simulate ID generation
                
                # Cache session
                await self.redis_manager.set_cache(
                    f"onboarding_session_{session_token}",
                    onboarding_session.dict(),
                    expire=86400  # 24 hours
                )
                
                # Publish event
                await self.kafka_manager.publish_event(
                    "onboarding_wizard.session_created",
                    {
                        "user_id": user_id,
                        "session_token": session_token,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                
                logger.info(f"Created onboarding session for user {user_id}")
                return onboarding_session
                
            except Exception as e:
                logger.error(f"Failed to create onboarding session: {e}")
                raise
    
    async def get_onboarding_session(self, session_token: str) -> OnboardingSession:
        """Get an onboarding session by token"""
        try:
            # Try to get from cache first
            cached_session = await self.redis_manager.get_cache(f"onboarding_session_{session_token}")
            if cached_session:
                return OnboardingSession(**cached_session)
            
            # If not in cache, return None (session not found)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get onboarding session: {e}")
            raise
    
    async def get_current_step(self, session_token: str) -> OnboardingStep:
        """Get the current step for an onboarding session"""
        try:
            session = await self.get_onboarding_session(session_token)
            if not session:
                raise ValueError("Onboarding session not found")
            
            # Get current step data
            current_step_data = next(
                (step for step in self.onboarding_steps if step["step_number"] == session.current_step),
                None
            )
            
            if not current_step_data:
                raise ValueError(f"Step {session.current_step} not found")
            
            # Create step object
            step = OnboardingStep(**current_step_data)
            
            # Check if step is completed
            step.is_completed = session.current_step in session.completed_steps
            
            return step
            
        except Exception as e:
            logger.error(f"Failed to get current step: {e}")
            raise
    
    async def get_all_steps(self, session_token: str) -> List[OnboardingStep]:
        """Get all onboarding steps with completion status"""
        try:
            session = await self.get_onboarding_session(session_token)
            if not session:
                raise ValueError("Onboarding session not found")
            
            steps = []
            for step_data in self.onboarding_steps:
                step = OnboardingStep(**step_data)
                step.is_completed = step.step_number in session.completed_steps
                steps.append(step)
            
            return steps
            
        except Exception as e:
            logger.error(f"Failed to get all steps: {e}")
            raise
    
    async def update_step_data(self, session_token: str, step_number: int, user_data: Dict[str, Any]) -> bool:
        """Update user data for a specific step"""
        try:
            session = await self.get_onboarding_session(session_token)
            if not session:
                raise ValueError("Onboarding session not found")
            
            # Validate step number
            if step_number < 1 or step_number > len(self.onboarding_steps):
                raise ValueError("Invalid step number")
            
            # Get step data
            step_data = next(
                (step for step in self.onboarding_steps if step["step_number"] == step_number),
                None
            )
            
            if not step_data:
                raise ValueError(f"Step {step_number} not found")
            
            # Validate user data
            validation_result = self._validate_step_data(step_data, user_data)
            if not validation_result["is_valid"]:
                raise ValueError(f"Validation failed: {validation_result['errors']}")
            
            # Update session data
            session.user_preferences[f"step_{step_number}"] = user_data
            
            # Update cache
            await self.redis_manager.set_cache(
                f"onboarding_session_{session_token}",
                session.dict(),
                expire=86400  # 24 hours
            )
            
            # Publish event
            await self.kafka_manager.publish_event(
                "onboarding_wizard.step_data_updated",
                {
                    "session_token": session_token,
                    "step_number": step_number,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            logger.info(f"Updated step {step_number} data for session {session_token}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update step data: {e}")
            raise
    
    async def complete_step(self, session_token: str, step_number: int) -> bool:
        """Mark a step as completed and move to next step"""
        try:
            session = await self.get_onboarding_session(session_token)
            if not session:
                raise ValueError("Onboarding session not found")
            
            # Validate step number
            if step_number < 1 or step_number > len(self.onboarding_steps):
                raise ValueError("Invalid step number")
            
            # Mark step as completed
            if step_number not in session.completed_steps:
                session.completed_steps.append(step_number)
            
            # Update progress
            session.progress_percentage = (len(session.completed_steps) / session.total_steps) * 100
            
            # Move to next step if not the last step
            if step_number < session.total_steps:
                session.current_step = step_number + 1
            
            # Check if onboarding is complete
            if len(session.completed_steps) == session.total_steps:
                session.is_active = False
                session.completed_at = datetime.utcnow()
            
            # Update cache
            await self.redis_manager.set_cache(
                f"onboarding_session_{session_token}",
                session.dict(),
                expire=86400  # 24 hours
            )
            
            # Publish event
            await self.kafka_manager.publish_event(
                "onboarding_wizard.step_completed",
                {
                    "session_token": session_token,
                    "step_number": step_number,
                    "progress_percentage": session.progress_percentage,
                    "is_complete": not session.is_active,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            logger.info(f"Completed step {step_number} for session {session_token}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to complete step: {e}")
            raise
    
    async def go_to_step(self, session_token: str, step_number: int) -> bool:
        """Navigate to a specific step"""
        try:
            session = await self.get_onboarding_session(session_token)
            if not session:
                raise ValueError("Onboarding session not found")
            
            # Validate step number
            if step_number < 1 or step_number > len(self.onboarding_steps):
                raise ValueError("Invalid step number")
            
            # Update current step
            session.current_step = step_number
            
            # Update cache
            await self.redis_manager.set_cache(
                f"onboarding_session_{session_token}",
                session.dict(),
                expire=86400  # 24 hours
            )
            
            # Publish event
            await self.kafka_manager.publish_event(
                "onboarding_wizard.navigated_to_step",
                {
                    "session_token": session_token,
                    "step_number": step_number,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            logger.info(f"Navigated to step {step_number} for session {session_token}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to navigate to step: {e}")
            raise
    
    async def get_onboarding_progress(self, session_token: str) -> Dict[str, Any]:
        """Get detailed onboarding progress information"""
        try:
            session = await self.get_onboarding_session(session_token)
            if not session:
                raise ValueError("Onboarding session not found")
            
            steps = await self.get_all_steps(session_token)
            
            # Calculate progress metrics
            completed_steps = [s for s in steps if s.is_completed]
            remaining_steps = [s for s in steps if not s.is_completed]
            
            # Estimate remaining time
            remaining_time = sum(s.estimated_time for s in remaining_steps)
            
            # Get step categories
            setup_steps = [s for s in steps if s.step_type == "setup"]
            config_steps = [s for s in steps if s.step_type == "configuration"]
            integration_steps = [s for s in steps if s.step_type == "integration"]
            training_steps = [s for s in steps if s.step_type == "training"]
            
            progress = {
                "session_token": session_token,
                "current_step": session.current_step,
                "total_steps": session.total_steps,
                "progress_percentage": session.progress_percentage,
                "completed_steps_count": len(completed_steps),
                "remaining_steps_count": len(remaining_steps),
                "estimated_remaining_time": remaining_time,
                "is_complete": not session.is_active,
                "started_at": session.started_at.isoformat() if session.started_at else None,
                "completed_at": session.completed_at.isoformat() if session.completed_at else None,
                "step_categories": {
                    "setup": {"total": len(setup_steps), "completed": len([s for s in setup_steps if s.is_completed])},
                    "configuration": {"total": len(config_steps), "completed": len([s for s in config_steps if s.is_completed])},
                    "integration": {"total": len(integration_steps), "completed": len([s for s in integration_steps if s.is_completed])},
                    "training": {"total": len(training_steps), "completed": len([s for s in training_steps if s.is_completed])}
                },
                "next_step": steps[session.current_step - 1] if session.current_step <= len(steps) else None
            }
            
            return progress
            
        except Exception as e:
            logger.error(f"Failed to get onboarding progress: {e}")
            raise
    
    async def get_step_help(self, step_number: int) -> Dict[str, Any]:
        """Get detailed help information for a specific step"""
        try:
            # Get step data
            step_data = next(
                (step for step in self.onboarding_steps if step["step_number"] == step_number),
                None
            )
            
            if not step_data:
                raise ValueError(f"Step {step_number} not found")
            
            # Generate help content
            help_content = {
                "step_number": step_number,
                "step_name": step_data["step_name"],
                "title": step_data["title"],
                "help_text": step_data["help_text"],
                "detailed_instructions": step_data["instructions"],
                "estimated_time": step_data["estimated_time"],
                "tips": self._generate_step_tips(step_data),
                "common_issues": self._get_common_issues(step_data),
                "video_tutorial": self._get_video_tutorial(step_data),
                "related_articles": self._get_related_articles(step_data)
            }
            
            return help_content
            
        except Exception as e:
            logger.error(f"Failed to get step help: {e}")
            raise
    
    async def save_onboarding_preferences(self, session_token: str, preferences: Dict[str, Any]) -> bool:
        """Save user preferences from onboarding"""
        try:
            session = await self.get_onboarding_session(session_token)
            if not session:
                raise ValueError("Onboarding session not found")
            
            # Update preferences
            session.user_preferences.update(preferences)
            
            # Update cache
            await self.redis_manager.set_cache(
                f"onboarding_session_{session_token}",
                session.dict(),
                expire=86400  # 24 hours
            )
            
            # Publish event
            await self.kafka_manager.publish_event(
                "onboarding_wizard.preferences_saved",
                {
                    "session_token": session_token,
                    "preferences_count": len(preferences),
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            logger.info(f"Saved preferences for session {session_token}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save preferences: {e}")
            raise
    
    async def get_onboarding_summary(self, session_token: str) -> Dict[str, Any]:
        """Get a summary of the completed onboarding"""
        try:
            session = await self.get_onboarding_session(session_token)
            if not session:
                raise ValueError("Onboarding session not found")
            
            if session.is_active:
                raise ValueError("Onboarding session is not complete")
            
            # Get all steps
            steps = await self.get_all_steps(session_token)
            
            # Extract key information from user preferences
            company_info = session.user_preferences.get("step_2", {})
            sales_goals = session.user_preferences.get("step_3", {})
            crm_info = session.user_preferences.get("step_4", {})
            email_info = session.user_preferences.get("step_5", {})
            
            summary = {
                "session_token": session_token,
                "user_id": session.user_id,
                "completed_at": session.completed_at.isoformat() if session.completed_at else None,
                "total_time": self._calculate_total_time(session.started_at, session.completed_at),
                "company_setup": {
                    "company_name": company_info.get("company_name"),
                    "industry": company_info.get("industry"),
                    "company_size": company_info.get("company_size"),
                    "target_market": company_info.get("target_market")
                },
                "sales_goals": {
                    "monthly_target": sales_goals.get("monthly_target"),
                    "primary_objectives": sales_goals.get("primary_objectives"),
                    "target_conversion_rate": sales_goals.get("target_conversion_rate")
                },
                "integrations": {
                    "crm_platform": crm_info.get("crm_platform"),
                    "email_provider": email_info.get("email_provider")
                },
                "next_steps": [
                    "Start your first lead generation campaign",
                    "Configure your first email sequence",
                    "Set up your sales dashboard",
                    "Schedule a follow-up call with our team"
                ],
                "support_resources": [
                    "Knowledge Base",
                    "Video Tutorials",
                    "Live Chat Support",
                    "Email Support"
                ]
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to get onboarding summary: {e}")
            raise
    
    def _generate_session_token(self) -> str:
        """Generate a unique session token"""
        import uuid
        return str(uuid.uuid4())
    
    def _validate_step_data(self, step_data: Dict[str, Any], user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate user data against step validation rules"""
        errors = []
        
        # Check required fields
        for field in step_data.get("required_fields", []):
            if field not in user_data or not user_data[field]:
                errors.append(f"Required field '{field}' is missing or empty")
        
        # Check validation rules
        validation_rules = step_data.get("validation_rules", {})
        for field, rules in validation_rules.items():
            if field in user_data:
                value = user_data[field]
                
                # Type validation
                if "type" in rules:
                    if rules["type"] == "number" and not isinstance(value, (int, float)):
                        errors.append(f"Field '{field}' must be a number")
                    elif rules["type"] == "boolean" and not isinstance(value, bool):
                        errors.append(f"Field '{field}' must be a boolean")
                
                # Length validation
                if "min_length" in rules and len(str(value)) < rules["min_length"]:
                    errors.append(f"Field '{field}' must be at least {rules['min_length']} characters")
                if "max_length" in rules and len(str(value)) > rules["max_length"]:
                    errors.append(f"Field '{field}' must be no more than {rules['max_length']} characters")
                
                # Value validation
                if "min" in rules and value < rules["min"]:
                    errors.append(f"Field '{field}' must be at least {rules['min']}")
                if "max" in rules and value > rules["max"]:
                    errors.append(f"Field '{field}' must be no more than {rules['max']}")
                
                # Allowed values validation
                if "allowed_values" in rules and value not in rules["allowed_values"]:
                    errors.append(f"Field '{field}' must be one of: {', '.join(rules['allowed_values'])}")
                
                # Min items validation
                if "min_items" in rules and len(value) < rules["min_items"]:
                    errors.append(f"Field '{field}' must have at least {rules['min_items']} items")
                if "max_items" in rules and len(value) > rules["max_items"]:
                    errors.append(f"Field '{field}' must have no more than {rules['max_items']} items")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors
        }
    
    def _generate_step_tips(self, step_data: Dict[str, Any]) -> List[str]:
        """Generate helpful tips for a step"""
        tips = []
        
        if step_data["step_name"] == "company_setup":
            tips = [
                "Use your official company name as it appears on your website",
                "Select the industry that best matches your primary business",
                "Be specific about your target market to help Eric personalize outreach"
            ]
        elif step_data["step_name"] == "crm_integration":
            tips = [
                "Ensure your CRM credentials are correct",
                "Test the connection before proceeding",
                "Consider setting up a dedicated API user for Eric"
            ]
        elif step_data["step_name"] == "email_setup":
            tips = [
                "Use a business email address for better deliverability",
                "Set up proper authentication (SPF, DKIM, DMARC)",
                "Start with conservative sending limits"
            ]
        
        return tips
    
    def _get_common_issues(self, step_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Get common issues and solutions for a step"""
        issues = []
        
        if step_data["step_name"] == "crm_integration":
            issues = [
                {
                    "issue": "Connection timeout",
                    "solution": "Check your internet connection and CRM server status"
                },
                {
                    "issue": "Invalid credentials",
                    "solution": "Verify your username and password are correct"
                },
                {
                    "issue": "API access denied",
                    "solution": "Ensure your CRM account has API access enabled"
                }
            ]
        
        return issues
    
    def _get_video_tutorial(self, step_data: Dict[str, Any]) -> str:
        """Get video tutorial URL for a step"""
        # In a real implementation, this would return actual video URLs
        return f"https://example.com/tutorials/{step_data['step_name']}"
    
    def _get_related_articles(self, step_data: Dict[str, Any]) -> List[str]:
        """Get related help articles for a step"""
        # In a real implementation, this would return actual article URLs
        return [
            f"https://example.com/help/{step_data['step_name']}-guide",
            f"https://example.com/help/{step_data['step_name']}-best-practices"
        ]
    
    def _calculate_total_time(self, started_at: datetime, completed_at: datetime) -> int:
        """Calculate total time spent on onboarding in minutes"""
        if not started_at or not completed_at:
            return 0
        
        duration = completed_at - started_at
        return int(duration.total_seconds() / 60)
