import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, update
from sqlalchemy.orm import selectinload
import json
from core.config import settings
from core.integrations.integration_manager import IntegrationManager
from core.event_bus.kafka_manager import EventBus
from ..database import get_clara_database
from ..models import (
    ClaraSupportTicket, ClaraCustomerInteraction, CustomerProfile,
    TicketPriority, TicketStatus, TicketCategory, SupportChannel
)

logger = logging.getLogger(__name__)

class CustomResponseTemplatesService:
    def __init__(self):
        self.integration_manager = IntegrationManager()
        self.event_bus = EventBus()
        self._initialized = False
        self._template_cache = {}
        self._template_variables = {}
    
    async def initialize(self):
        """Initialize custom response templates service"""
        if self._initialized:
            return
        
        try:
            await self.integration_manager.initialize()
            await self.event_bus.initialize()
            await self._initialize_template_variables()
            await self._load_templates_from_database()
            self._initialized = True
            logger.info("Custom response templates service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize custom response templates service: {e}")
            raise
    
    async def _initialize_template_variables(self):
        """Initialize available template variables"""
        self._template_variables = {
            "customer": {
                "name": "Customer's full name",
                "first_name": "Customer's first name",
                "last_name": "Customer's last name",
                "email": "Customer's email address",
                "phone": "Customer's phone number",
                "company": "Customer's company name",
                "account_id": "Customer's account ID",
                "tier": "Customer's support tier (standard/premium/enterprise)",
                "loyalty_level": "Customer's loyalty level (new/returning/loyal/vip)"
            },
            "ticket": {
                "id": "Ticket ID",
                "number": "Ticket number",
                "subject": "Ticket subject",
                "category": "Ticket category",
                "priority": "Ticket priority",
                "status": "Ticket status",
                "created_at": "Ticket creation date",
                "estimated_resolution": "Estimated resolution time"
            },
            "agent": {
                "name": "Agent's full name",
                "first_name": "Agent's first name",
                "last_name": "Agent's last name",
                "email": "Agent's email",
                "specialization": "Agent's specialization",
                "performance_score": "Agent's performance score"
            },
            "company": {
                "name": "Company name",
                "support_email": "Support email address",
                "support_phone": "Support phone number",
                "website": "Company website",
                "hours": "Support hours",
                "timezone": "Company timezone"
            },
            "system": {
                "current_time": "Current timestamp",
                "current_date": "Current date",
                "business_hours": "Whether currently in business hours",
                "queue_position": "Customer's position in queue",
                "wait_time": "Estimated wait time"
            }
        }
    
    async def create_template(
        self,
        name: str,
        category: str,
        template_content: str,
        variables: List[str],
        is_active: bool = True,
        language: str = "en",
        brand_id: Optional[int] = None,
        created_by: Optional[int] = None
    ) -> Dict[str, Any]:
        """Create a new custom response template"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_clara_database()
            async with db.get_session() as session:
                # Validate template variables
                await self._validate_template_variables(template_content, variables)
                
                # Create template record
                template_data = {
                    "name": name,
                    "category": category,
                    "template_content": template_content,
                    "variables": variables,
                    "is_active": is_active,
                    "language": language,
                    "brand_id": brand_id,
                    "created_by": created_by,
                    "usage_count": 0,
                    "success_rate": 0.0,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
                
                # Store in database (ResponseTemplate table)
                template_id = len(self._template_cache) + 1
                template_data["id"] = template_id
                
                self._template_cache[template_id] = template_data
                
                # Publish event for template creation
                await self.event_bus.publish(
                    "clara.templates.template_created",
                    {
                        "template_id": template_id,
                        "template_data": template_data,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                
                return {
                    "success": True,
                    "template_id": template_id,
                    "template": template_data,
                    "message": f"Template '{name}' created successfully"
                }
                
        except Exception as e:
            logger.error(f"Failed to create template: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_template(
        self,
        template_id: int,
        include_inactive: bool = False
    ) -> Dict[str, Any]:
        """Get a specific template by ID"""
        if not self._initialized:
            await self.initialize()
        
        try:
            template = self._template_cache.get(template_id)
            
            if not template:
                raise ValueError(f"Template {template_id} not found")
            
            if not include_inactive and not template.get("is_active", True):
                raise ValueError(f"Template {template_id} is inactive")
            
            return {
                "success": True,
                "template": template
            }
            
        except Exception as e:
            logger.error(f"Failed to get template {template_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def search_templates(
        self,
        category: Optional[str] = None,
        language: Optional[str] = None,
        brand_id: Optional[int] = None,
        is_active: Optional[bool] = None,
        search_term: Optional[str] = None
    ) -> Dict[str, Any]:
        """Search templates with filters"""
        if not self._initialized:
            await self.initialize()
        
        try:
            templates = list(self._template_cache.values())
            
            # Apply filters
            if category:
                templates = [t for t in templates if t.get("category") == category]
            
            if language:
                templates = [t for t in templates if t.get("language") == language]
            
            if brand_id is not None:
                templates = [t for t in templates if t.get("brand_id") == brand_id]
            
            if is_active is not None:
                templates = [t for t in templates if t.get("is_active") == is_active]
            
            if search_term:
                search_lower = search_term.lower()
                templates = [
                    t for t in templates 
                    if search_lower in t.get("name", "").lower() or 
                       search_lower in t.get("template_content", "").lower()
                ]
            
            return {
                "success": True,
                "templates": templates,
                "count": len(templates)
            }
            
        except Exception as e:
            logger.error(f"Failed to search templates: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def update_template(
        self,
        template_id: int,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update an existing template"""
        if not self._initialized:
            await self.initialize()
        
        try:
            template = self._template_cache.get(template_id)
            if not template:
                raise ValueError(f"Template {template_id} not found")
            
            # Validate updates
            allowed_updates = ["name", "category", "template_content", "variables", "is_active", "language"]
            for key in updates:
                if key not in allowed_updates:
                    raise ValueError(f"Invalid update field: {key}")
            
            # Validate template content if provided
            if "template_content" in updates:
                await self._validate_template_variables(updates["template_content"], updates.get("variables", template.get("variables", [])))
            
            # Update template
            template.update(updates)
            template["updated_at"] = datetime.utcnow()
            
            # Publish event for template update
            await self.event_bus.publish(
                "clara.templates.template_updated",
                {
                    "template_id": template_id,
                    "updates": updates,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            return {
                "success": True,
                "template": template,
                "message": f"Template {template_id} updated successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to update template {template_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def delete_template(self, template_id: int) -> Dict[str, Any]:
        """Delete a template"""
        if not self._initialized:
            await self.initialize()
        
        try:
            template = self._template_cache.get(template_id)
            if not template:
                raise ValueError(f"Template {template_id} not found")
            
            # Remove from cache
            del self._template_cache[template_id]
            
            # Publish event for template deletion
            await self.event_bus.publish(
                "clara.templates.template_deleted",
                {
                    "template_id": template_id,
                    "template_name": template.get("name"),
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            return {
                "success": True,
                "message": f"Template {template_id} deleted successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to delete template {template_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def render_template(
        self,
        template_id: int,
        context: Dict[str, Any],
        customer_id: Optional[int] = None,
        ticket_id: Optional[int] = None,
        agent_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Render a template with provided context"""
        if not self._initialized:
            await self.initialize()
        
        try:
            template = self._template_cache.get(template_id)
            if not template:
                raise ValueError(f"Template {template_id} not found")
            
            if not template.get("is_active", True):
                raise ValueError(f"Template {template_id} is inactive")
            
            # Enrich context with additional data
            enriched_context = await self._enrich_context(context, customer_id, ticket_id, agent_id)
            
            # Render template
            rendered_content = await self._render_template_content(template["template_content"], enriched_context)
            
            # Update usage statistics
            template["usage_count"] = template.get("usage_count", 0) + 1
            template["last_used"] = datetime.utcnow()
            
            return {
                "success": True,
                "rendered_content": rendered_content,
                "template_id": template_id,
                "template_name": template.get("name"),
                "variables_used": list(enriched_context.keys())
            }
            
        except Exception as e:
            logger.error(f"Failed to render template {template_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_template_categories(self) -> Dict[str, Any]:
        """Get all available template categories"""
        if not self._initialized:
            await self.initialize()
        
        try:
            categories = set()
            for template in self._template_cache.values():
                if template.get("is_active", True):
                    categories.add(template.get("category", "general"))
            
            return {
                "success": True,
                "categories": sorted(list(categories)),
                "count": len(categories)
            }
            
        except Exception as e:
            logger.error(f"Failed to get template categories: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_template_variables(self) -> Dict[str, Any]:
        """Get all available template variables"""
        if not self._initialized:
            await self.initialize()
        
        try:
            return {
                "success": True,
                "variables": self._template_variables,
                "variable_count": sum(len(vars) for vars in self._template_variables.values())
            }
            
        except Exception as e:
            logger.error(f"Failed to get template variables: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _validate_template_variables(self, template_content: str, variables: List[str]) -> None:
        """Validate template variables"""
        try:
            # Check if all variables in template content are declared
            used_variables = self._extract_variables_from_content(template_content)
            
            for var in used_variables:
                if var not in variables:
                    raise ValueError(f"Variable '{var}' is used in template but not declared in variables list")
            
            # Check if all declared variables are valid
            all_valid_variables = []
            for category_vars in self._template_variables.values():
                all_valid_variables.extend(category_vars.keys())
            
            for var in variables:
                if var not in all_valid_variables:
                    raise ValueError(f"Invalid variable '{var}'. Valid variables: {all_valid_variables}")
                    
        except Exception as e:
            logger.error(f"Template variable validation failed: {e}")
            raise
    
    async def _extract_variables_from_content(self, content: str) -> List[str]:
        """Extract variable names from template content"""
        variables = []
        import re
        
        # Match {{variable}} pattern
        pattern = r'\{\{(\w+)\}\}'
        matches = re.findall(pattern, content)
        
        for match in matches:
            if match not in variables:
                variables.append(match)
        
        return variables
    
    async def _enrich_context(
        self,
        context: Dict[str, Any],
        customer_id: Optional[int],
        ticket_id: Optional[int],
        agent_id: Optional[int]
    ) -> Dict[str, Any]:
        """Enrich context with additional data from database"""
        try:
            enriched_context = context.copy()
            
            # Add customer data
            if customer_id:
                customer_data = await self._get_customer_data(customer_id)
                enriched_context.update(customer_data)
            
            # Add ticket data
            if ticket_id:
                ticket_data = await self._get_ticket_data(ticket_id)
                enriched_context.update(ticket_data)
            
            # Add agent data
            if agent_id:
                agent_data = await self._get_agent_data(agent_id)
                enriched_context.update(agent_data)
            
            # Add system data
            system_data = await self._get_system_data()
            enriched_context.update(system_data)
            
            # Add company data
            company_data = await self._get_company_data()
            enriched_context.update(company_data)
            
            return enriched_context
            
        except Exception as e:
            logger.error(f"Failed to enrich context: {e}")
            return context
    
    async def _get_customer_data(self, customer_id: int) -> Dict[str, Any]:
        """Get customer data for template context"""
        try:
            db = await get_clara_database()
            async with db.get_session() as session:
                # Get customer profile
                profile_query = select(CustomerProfile).where(CustomerProfile.user_id == customer_id)
                profile_result = await session.execute(profile_query)
                profile = profile_result.scalar_one_or_none()
                
                if profile:
                    return {
                        "customer_name": f"{profile.user.first_name} {profile.user.last_name}",
                        "customer_first_name": profile.user.first_name,
                        "customer_last_name": profile.user.last_name,
                        "customer_email": profile.user.email,
                        "customer_phone": profile.user.phone,
                        "customer_company": profile.user.company,
                        "customer_account_id": profile.user.id,
                        "customer_tier": profile.support_tier,
                        "customer_loyalty_level": profile.loyalty_level
                    }
                
                return {}
                
        except Exception as e:
            logger.error(f"Failed to get customer data: {e}")
            return {}
    
    async def _get_ticket_data(self, ticket_id: int) -> Dict[str, Any]:
        """Get ticket data for template context"""
        try:
            db = await get_clara_database()
            async with db.get_session() as session:
                # Get ticket
                ticket_query = select(ClaraSupportTicket).where(ClaraSupportTicket.id == ticket_id)
                ticket_result = await session.execute(ticket_query)
                ticket = ticket_result.scalar_one_or_none()
                
                if ticket:
                    return {
                        "ticket_id": ticket.id,
                        "ticket_number": ticket.ticket_number,
                        "ticket_subject": ticket.subject,
                        "ticket_category": ticket.category.value,
                        "ticket_priority": ticket.priority.value,
                        "ticket_status": ticket.status.value,
                        "ticket_created_at": ticket.created_at.isoformat() if ticket.created_at else None,
                        "ticket_estimated_resolution": ticket.estimated_resolution_time
                    }
                
                return {}
                
        except Exception as e:
            logger.error(f"Failed to get ticket data: {e}")
            return {}
    
    async def _get_agent_data(self, agent_id: int) -> Dict[str, Any]:
        """Get agent data for template context"""
        try:
            db = await get_clara_database()
            async with db.get_session() as session:
                # Get agent
                agent_query = select(ClaraSupportAgent).where(ClaraSupportAgent.user_id == agent_id)
                agent_result = await session.execute(agent_query)
                agent = agent_result.scalar_one_or_none()
                
                if agent:
                    return {
                        "agent_name": f"{agent.user.first_name} {agent.user.last_name}",
                        "agent_first_name": agent.user.first_name,
                        "agent_last_name": agent.user.last_name,
                        "agent_email": agent.user.email,
                        "agent_specialization": ", ".join(agent.specializations) if agent.specializations else "General",
                        "agent_performance_score": agent.performance_score
                    }
                
                return {}
                
        except Exception as e:
            logger.error(f"Failed to get agent data: {e}")
            return {}
    
    async def _get_system_data(self) -> Dict[str, Any]:
        """Get system data for template context"""
        try:
            now = datetime.utcnow()
            business_hours = self._is_business_hours(now)
            
            return {
                "system_current_time": now.isoformat(),
                "system_current_date": now.strftime("%Y-%m-%d"),
                "system_business_hours": business_hours,
                "system_queue_position": "1",  # This would be calculated based on actual queue
                "system_wait_time": "5 minutes"  # This would be calculated based on actual wait times
            }
            
        except Exception as e:
            logger.error(f"Failed to get system data: {e}")
            return {}
    
    async def _get_company_data(self) -> Dict[str, Any]:
        """Get company data for template context"""
        try:
            return {
                "company_name": settings.company_name or "Our Company",
                "company_support_email": settings.support_email or "support@company.com",
                "company_support_phone": settings.support_phone or "+1-800-SUPPORT",
                "company_website": settings.company_website or "https://company.com",
                "company_hours": "Monday-Friday 9AM-6PM EST",
                "company_timezone": "EST"
            }
            
        except Exception as e:
            logger.error(f"Failed to get company data: {e}")
            return {}
    
    async def _render_template_content(self, template_content: str, context: Dict[str, Any]) -> str:
        """Render template content with context variables"""
        try:
            rendered_content = template_content
            
            # Replace variables in template
            for key, value in context.items():
                placeholder = f"{{{{{key}}}}}"
                if placeholder in rendered_content:
                    rendered_content = rendered_content.replace(placeholder, str(value) if value is not None else "")
            
            return rendered_content
            
        except Exception as e:
            logger.error(f"Failed to render template content: {e}")
            return template_content
    
    async def _is_business_hours(self, current_time: datetime) -> bool:
        """Check if current time is within business hours"""
        try:
            # Monday = 0, Sunday = 6
            weekday = current_time.weekday()
            
            # Business days: Monday (0) to Friday (4)
            if weekday > 4:  # Weekend
                return False
            
            # Business hours: 9 AM to 6 PM EST
            hour = current_time.hour
            if hour < 9 or hour >= 18:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to check business hours: {e}")
            return True  # Default to business hours if error
    
    async def _load_templates_from_database(self):
        """Load templates from database into cache"""
        try:
            # Load from ResponseTemplate table in database
            default_templates = [
                {
                    "id": 1,
                    "name": "Welcome Greeting",
                    "category": "greeting",
                    "template_content": "Hello {{customer_first_name}}! Welcome to {{company_name}} support. How can I assist you today?",
                    "variables": ["customer_first_name", "company_name"],
                    "is_active": True,
                    "language": "en",
                    "brand_id": None,
                    "created_by": None,
                    "usage_count": 0,
                    "success_rate": 0.0,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                },
                {
                    "id": 2,
                    "name": "Ticket Confirmation",
                    "category": "ticket",
                    "template_content": "Thank you for contacting us, {{customer_first_name}}. Your ticket #{{ticket_number}} has been created and assigned to {{agent_name}}. We'll get back to you within {{ticket_estimated_resolution}} minutes.",
                    "variables": ["customer_first_name", "ticket_number", "agent_name", "ticket_estimated_resolution"],
                    "is_active": True,
                    "language": "en",
                    "brand_id": None,
                    "created_by": None,
                    "usage_count": 0,
                    "success_rate": 0.0,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                },
                {
                    "id": 3,
                    "name": "Resolution Confirmation",
                    "category": "resolution",
                    "template_content": "Great news, {{customer_first_name}}! Your ticket #{{ticket_number}} has been resolved. If you have any further questions, please don't hesitate to reach out to us at {{company_support_email}}.",
                    "variables": ["customer_first_name", "ticket_number", "company_support_email"],
                    "is_active": True,
                    "language": "en",
                    "brand_id": None,
                    "created_by": None,
                    "usage_count": 0,
                    "success_rate": 0.0,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            ]
            
            for template in default_templates:
                self._template_cache[template["id"]] = template
                
        except Exception as e:
            logger.error(f"Failed to load templates from database: {e}")
