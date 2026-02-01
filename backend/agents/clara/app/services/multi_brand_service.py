from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_, func, desc
from sqlalchemy.orm import selectinload, joinedload
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
import json
import uuid
import asyncio
from pydantic import ValidationError

from ..models import ClaraBrand, ClaraBrandConfiguration, ClaraBrandTemplate, ClaraSupportTicket, ClaraCustomerInteraction
from core.integrations.integration_manager import IntegrationManager
from core.event_bus.kafka_manager import EventBus
from core.ai import get_ai_service_manager
from core.config import Settings

class MultiBrandService:
    def __init__(self, db: Optional[AsyncSession] = None, integration_manager: Optional[IntegrationManager] = None, event_bus: Optional[EventBus] = None):
        self.db = db
        self.integration_manager = integration_manager
        self.event_bus = event_bus
        # Using AI Service Manager for sentiment analysis and intent detection
        self.settings = Settings()
        self._brand_context_cache = {}
        self._configuration_cache = {}
        self._template_cache = {}

    # ClaraBrand Management Methods
    async def create_brand(
        self,
        name: str,
        description: Optional[str] = None,
        logo_url: Optional[str] = None,
        primary_color: Optional[str] = None,
        secondary_color: Optional[str] = None,
        tone_of_voice: str = "professional",
        industry: Optional[str] = None,
        target_audience: Optional[str] = None,
        contact_info: Optional[Dict[str, str]] = None,
        social_media_handles: Optional[Dict[str, str]] = None
    ) -> ClaraBrand:
        """Create a new brand configuration"""
        try:
            # Validate tone of voice
            valid_tones = ["formal", "casual", "friendly", "professional", "technical", "conversational"]
            if tone_of_voice not in valid_tones:
                raise ValueError(f"Invalid tone of voice. Must be one of: {valid_tones}")

            # Check if brand name already exists
            existing_brand = await self.db.execute(
                select(ClaraBrand).where(ClaraBrand.name == name)
            )
            if existing_brand.scalar_one_or_none():
                raise ValueError(f"ClaraBrand with name '{name}' already exists")

            # Create new brand
            brand = ClaraBrand(
                name=name,
                description=description,
                logo_url=logo_url,
                primary_color=primary_color,
                secondary_color=secondary_color,
                tone_of_voice=tone_of_voice,
                industry=industry,
                target_audience=target_audience,
                contact_info=contact_info,
                social_media_handles=social_media_handles,
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            self.db.add(brand)
            await self.db.commit()
            await self.db.refresh(brand)

            # Create default configurations
            await self._create_default_configurations(brand.id)

            # Publish event
            await self.event_bus.publish("brand.created", {
                "brand_id": brand.id,
                "brand_name": brand.name,
                "timestamp": datetime.utcnow().isoformat()
            })

            return brand

        except Exception as e:
            await self.db.rollback()
            raise e

    async def get_brands(self, active_only: bool = True) -> List[ClaraBrand]:
        """Get all brands with optional filtering"""
        try:
            query = select(ClaraBrand)
            if active_only:
                query = query.where(ClaraBrand.is_active == True)
            query = query.order_by(ClaraBrand.name)
            
            result = await self.db.execute(query)
            return result.scalars().all()

        except Exception as e:
            raise e

    async def get_brand(self, brand_id: int) -> Optional[ClaraBrand]:
        """Get a specific brand by ID"""
        try:
            result = await self.db.execute(
                select(ClaraBrand).where(ClaraBrand.id == brand_id)
            )
            return result.scalar_one_or_none()

        except Exception as e:
            raise e

    async def update_brand(
        self,
        brand_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        logo_url: Optional[str] = None,
        primary_color: Optional[str] = None,
        secondary_color: Optional[str] = None,
        tone_of_voice: Optional[str] = None,
        industry: Optional[str] = None,
        target_audience: Optional[str] = None,
        contact_info: Optional[Dict[str, str]] = None,
        social_media_handles: Optional[Dict[str, str]] = None,
        is_active: Optional[bool] = None
    ) -> Optional[ClaraBrand]:
        """Update a brand configuration"""
        try:
            # Get existing brand
            brand = await self.get_brand(brand_id)
            if not brand:
                return None

            # Validate tone of voice if provided
            if tone_of_voice:
                valid_tones = ["formal", "casual", "friendly", "professional", "technical", "conversational"]
                if tone_of_voice not in valid_tones:
                    raise ValueError(f"Invalid tone of voice. Must be one of: {valid_tones}")

            # Check name uniqueness if changing
            if name and name != brand.name:
                existing_brand = await self.db.execute(
                    select(ClaraBrand).where(and_(ClaraBrand.name == name, ClaraBrand.id != brand_id))
                )
                if existing_brand.scalar_one_or_none():
                    raise ValueError(f"ClaraBrand with name '{name}' already exists")

            # Update fields
            update_data = {}
            if name is not None:
                update_data["name"] = name
            if description is not None:
                update_data["description"] = description
            if logo_url is not None:
                update_data["logo_url"] = logo_url
            if primary_color is not None:
                update_data["primary_color"] = primary_color
            if secondary_color is not None:
                update_data["secondary_color"] = secondary_color
            if tone_of_voice is not None:
                update_data["tone_of_voice"] = tone_of_voice
            if industry is not None:
                update_data["industry"] = industry
            if target_audience is not None:
                update_data["target_audience"] = target_audience
            if contact_info is not None:
                update_data["contact_info"] = contact_info
            if social_media_handles is not None:
                update_data["social_media_handles"] = social_media_handles
            if is_active is not None:
                update_data["is_active"] = is_active

            update_data["updated_at"] = datetime.utcnow()

            # Execute update
            await self.db.execute(
                update(ClaraBrand).where(ClaraBrand.id == brand_id).values(**update_data)
            )
            await self.db.commit()

            # Clear cache
            self._clear_brand_cache(brand_id)

            # Get updated brand
            updated_brand = await self.get_brand(brand_id)

            # Publish event
            await self.event_bus.publish("brand.updated", {
                "brand_id": brand_id,
                "updated_fields": list(update_data.keys()),
                "timestamp": datetime.utcnow().isoformat()
            })

            return updated_brand

        except Exception as e:
            await self.db.rollback()
            raise e

    async def delete_brand(self, brand_id: int) -> bool:
        """Delete a brand (soft delete)"""
        try:
            brand = await self.get_brand(brand_id)
            if not brand:
                return False

            # Soft delete
            await self.db.execute(
                update(ClaraBrand).where(ClaraBrand.id == brand_id).values(
                    is_active=False,
                    updated_at=datetime.utcnow()
                )
            )
            await self.db.commit()

            # Clear cache
            self._clear_brand_cache(brand_id)

            # Publish event
            await self.event_bus.publish("brand.deleted", {
                "brand_id": brand_id,
                "brand_name": brand.name,
                "timestamp": datetime.utcnow().isoformat()
            })

            return True

        except Exception as e:
            await self.db.rollback()
            raise e

    # Configuration Management Methods
    async def create_configuration(
        self,
        brand_id: int,
        config_type: str,
        config_data: Dict[str, Any],
        is_default: bool = False,
        priority: int = 1
    ) -> ClaraBrandConfiguration:
        """Create a new brand configuration"""
        try:
            # Validate brand exists
            brand = await self.get_brand(brand_id)
            if not brand:
                raise ValueError(f"ClaraBrand with ID {brand_id} not found")

            # Validate configuration type
            valid_types = [
                "response_templates", "workflows", "integrations", "automation_rules",
                "escalation_policies", "sla_config", "notification_settings",
                "custom_fields", "branding", "localization"
            ]
            if config_type not in valid_types:
                raise ValueError(f"Invalid configuration type. Must be one of: {valid_types}")

            # If this is default, unset other defaults of same type
            if is_default:
                await self.db.execute(
                    update(ClaraBrandConfiguration).where(
                        and_(
                            ClaraBrandConfiguration.brand_id == brand_id,
                            ClaraBrandConfiguration.config_type == config_type,
                            ClaraBrandConfiguration.is_default == True
                        )
                    ).values(is_default=False)
                )

            # Create configuration
            config = ClaraBrandConfiguration(
                brand_id=brand_id,
                config_type=config_type,
                config_data=config_data,
                is_default=is_default,
                priority=priority,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            self.db.add(config)
            await self.db.commit()
            await self.db.refresh(config)

            # Clear cache
            self._clear_configuration_cache(brand_id, config_type)

            return config

        except Exception as e:
            await self.db.rollback()
            raise e

    async def get_brand_configurations(
        self, 
        brand_id: int, 
        config_type: Optional[str] = None
    ) -> List[ClaraBrandConfiguration]:
        """Get configurations for a specific brand"""
        try:
            query = select(ClaraBrandConfiguration).where(ClaraBrandConfiguration.brand_id == brand_id)
            
            if config_type:
                query = query.where(ClaraBrandConfiguration.config_type == config_type)
            
            query = query.order_by(ClaraBrandConfiguration.priority.desc(), ClaraBrandConfiguration.created_at)
            
            result = await self.db.execute(query)
            return result.scalars().all()

        except Exception as e:
            raise e

    async def get_configuration(self, config_id: int) -> Optional[ClaraBrandConfiguration]:
        """Get a specific configuration by ID"""
        try:
            result = await self.db.execute(
                select(ClaraBrandConfiguration).where(ClaraBrandConfiguration.id == config_id)
            )
            return result.scalar_one_or_none()

        except Exception as e:
            raise e

    async def update_configuration(
        self,
        config_id: int,
        config_type: Optional[str] = None,
        config_data: Optional[Dict[str, Any]] = None,
        is_default: Optional[bool] = None,
        priority: Optional[int] = None
    ) -> Optional[ClaraBrandConfiguration]:
        """Update a configuration"""
        try:
            config = await self.get_configuration(config_id)
            if not config:
                return None

            # If setting as default, unset other defaults of same type
            if is_default and not config.is_default:
                await self.db.execute(
                    update(ClaraBrandConfiguration).where(
                        and_(
                            ClaraBrandConfiguration.brand_id == config.brand_id,
                            ClaraBrandConfiguration.config_type == config.config_type,
                            ClaraBrandConfiguration.is_default == True,
                            ClaraBrandConfiguration.id != config_id
                        )
                    ).values(is_default=False)
                )

            # Update fields
            update_data = {}
            if config_type is not None:
                update_data["config_type"] = config_type
            if config_data is not None:
                update_data["config_data"] = config_data
            if is_default is not None:
                update_data["is_default"] = is_default
            if priority is not None:
                update_data["priority"] = priority

            update_data["updated_at"] = datetime.utcnow()

            # Execute update
            await self.db.execute(
                update(ClaraBrandConfiguration).where(ClaraBrandConfiguration.id == config_id).values(**update_data)
            )
            await self.db.commit()

            # Clear cache
            self._clear_configuration_cache(config.brand_id, config.config_type)

            # Get updated config
            updated_config = await self.get_configuration(config_id)

            return updated_config

        except Exception as e:
            await self.db.rollback()
            raise e

    async def delete_configuration(self, config_id: int) -> bool:
        """Delete a configuration"""
        try:
            config = await self.get_configuration(config_id)
            if not config:
                return False

            await self.db.execute(
                delete(ClaraBrandConfiguration).where(ClaraBrandConfiguration.id == config_id)
            )
            await self.db.commit()

            # Clear cache
            self._clear_configuration_cache(config.brand_id, config.config_type)

            return True

        except Exception as e:
            await self.db.rollback()
            raise e

    # Template Management Methods
    async def create_template(
        self,
        brand_id: int,
        template_name: str,
        template_type: str,
        content: str,
        variables: List[str] = None,
        is_active: bool = True
    ) -> ClaraBrandTemplate:
        """Create a new brand template"""
        try:
            # Validate brand exists
            brand = await self.get_brand(brand_id)
            if not brand:
                raise ValueError(f"ClaraBrand with ID {brand_id} not found")

            # Check template name uniqueness for this brand
            existing_template = await self.db.execute(
                select(ClaraBrandTemplate).where(
                    and_(
                        ClaraBrandTemplate.brand_id == brand_id,
                        ClaraBrandTemplate.template_name == template_name
                    )
                )
            )
            if existing_template.scalar_one_or_none():
                raise ValueError(f"Template with name '{template_name}' already exists for this brand")

            # Validate template type
            valid_types = [
                "welcome", "support", "escalation", "resolution", "follow_up",
                "apology", "thank_you", "out_of_office", "maintenance", "update"
            ]
            if template_type not in valid_types:
                raise ValueError(f"Invalid template type. Must be one of: {valid_types}")

            # Create template
            template = ClaraBrandTemplate(
                brand_id=brand_id,
                template_name=template_name,
                template_type=template_type,
                content=content,
                variables=variables or [],
                is_active=is_active,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            self.db.add(template)
            await self.db.commit()
            await self.db.refresh(template)

            # Clear cache
            self._clear_template_cache(brand_id, template_type)

            return template

        except Exception as e:
            await self.db.rollback()
            raise e

    async def get_brand_templates(
        self,
        brand_id: int,
        template_type: Optional[str] = None,
        active_only: bool = True
    ) -> List[ClaraBrandTemplate]:
        """Get templates for a specific brand"""
        try:
            query = select(ClaraBrandTemplate).where(ClaraBrandTemplate.brand_id == brand_id)
            
            if template_type:
                query = query.where(ClaraBrandTemplate.template_type == template_type)
            
            if active_only:
                query = query.where(ClaraBrandTemplate.is_active == True)
            
            query = query.order_by(ClaraBrandTemplate.template_name)
            
            result = await self.db.execute(query)
            return result.scalars().all()

        except Exception as e:
            raise e

    async def get_template(self, template_id: int) -> Optional[ClaraBrandTemplate]:
        """Get a specific template by ID"""
        try:
            result = await self.db.execute(
                select(ClaraBrandTemplate).where(ClaraBrandTemplate.id == template_id)
            )
            return result.scalar_one_or_none()

        except Exception as e:
            raise e

    async def update_template(
        self,
        template_id: int,
        template_name: Optional[str] = None,
        template_type: Optional[str] = None,
        content: Optional[str] = None,
        variables: Optional[List[str]] = None,
        is_active: Optional[bool] = None
    ) -> Optional[ClaraBrandTemplate]:
        """Update a template"""
        try:
            template = await self.get_template(template_id)
            if not template:
                return None

            # Check name uniqueness if changing
            if template_name and template_name != template.template_name:
                existing_template = await self.db.execute(
                    select(ClaraBrandTemplate).where(
                        and_(
                            ClaraBrandTemplate.brand_id == template.brand_id,
                            ClaraBrandTemplate.template_name == template_name,
                            ClaraBrandTemplate.id != template_id
                        )
                    )
                )
                if existing_template.scalar_one_or_none():
                    raise ValueError(f"Template with name '{template_name}' already exists for this brand")

            # Update fields
            update_data = {}
            if template_name is not None:
                update_data["template_name"] = template_name
            if template_type is not None:
                update_data["template_type"] = template_type
            if content is not None:
                update_data["content"] = content
            if variables is not None:
                update_data["variables"] = variables
            if is_active is not None:
                update_data["is_active"] = is_active

            update_data["updated_at"] = datetime.utcnow()

            # Execute update
            await self.db.execute(
                update(ClaraBrandTemplate).where(ClaraBrandTemplate.id == template_id).values(**update_data)
            )
            await self.db.commit()

            # Clear cache
            self._clear_template_cache(template.brand_id, template.template_type)

            # Get updated template
            updated_template = await self.get_template(template_id)

            return updated_template

        except Exception as e:
            await self.db.rollback()
            raise e

    async def delete_template(self, template_id: int) -> bool:
        """Delete a template"""
        try:
            template = await self.get_template(template_id)
            if not template:
                return False

            await self.db.execute(
                delete(ClaraBrandTemplate).where(ClaraBrandTemplate.id == template_id)
            )
            await self.db.commit()

            # Clear cache
            self._clear_template_cache(template.brand_id, template.template_type)

            return True

        except Exception as e:
            await self.db.rollback()
            raise e

    # ClaraBrand Context Management
    async def switch_brand_context(
        self,
        brand_id: int,
        customer_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Switch to a specific brand context"""
        try:
            # Get brand
            brand = await self.get_brand(brand_id)
            if not brand:
                raise ValueError(f"ClaraBrand with ID {brand_id} not found")

            # Get configurations and templates
            configurations = await self.get_brand_configurations(brand_id)
            templates = await self.get_brand_templates(brand_id, active_only=True)

            # Create context key
            context_key = f"{brand_id}_{customer_id}_{session_id}"
            
            # Store in cache
            self._brand_context_cache[context_key] = {
                "brand": brand,
                "configurations": configurations,
                "templates": templates,
                "switched_at": datetime.utcnow()
            }

            # Publish event
            await self.event_bus.publish("brand.context_switched", {
                "brand_id": brand_id,
                "customer_id": customer_id,
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat()
            })

            return {
                "brand": brand,
                "configurations": configurations,
                "templates": templates,
                "context_switched": True,
                "message": f"Successfully switched to brand context: {brand.name}"
            }

        except Exception as e:
            raise e

    async def get_current_brand_context(
        self,
        customer_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get current brand context"""
        try:
            # Try to find context in cache
            for context_key, context_data in self._brand_context_cache.items():
                if customer_id in context_key or session_id in context_key:
                    return context_data

            return None

        except Exception as e:
            raise e

    # ClaraBrand-Specific Response Generation
    async def generate_brand_response(
        self,
        brand_id: int,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        template_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate a brand-specific response"""
        try:
            # Get brand
            brand = await self.get_brand(brand_id)
            if not brand:
                raise ValueError(f"ClaraBrand with ID {brand_id} not found")

            # Get brand configurations
            configs = await self.get_brand_configurations(brand_id, "response_templates")
            response_config = next((c for c in configs if c.is_default), configs[0] if configs else None)

            # Get templates if specified
            templates = []
            if template_type:
                templates = await self.get_brand_templates(brand_id, template_type=template_type)

            # Generate response using brand tone and configurations
            response_content = await self._generate_brand_aware_response(
                brand=brand,
                message=message,
                context=context,
                response_config=response_config,
                templates=templates
            )

            return {
                "brand_id": brand_id,
                "brand_name": brand.name,
                "original_message": message,
                "response": response_content,
                "tone_of_voice": brand.tone_of_voice,
                "template_used": template_type,
                "generated_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            raise e

    # Analytics and Reporting
    async def get_brand_analytics(
        self,
        brand_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get analytics for a specific brand"""
        try:
            # Validate brand exists
            brand = await self.get_brand(brand_id)
            if not brand:
                raise ValueError(f"ClaraBrand with ID {brand_id} not found")

            # Set default date range if not provided
            if not end_date:
                end_date = datetime.utcnow()
            if not start_date:
                start_date = end_date - timedelta(days=30)

            # Get ticket statistics
            ticket_stats = await self._get_ticket_statistics(brand_id, start_date, end_date)
            
            # Get customer satisfaction
            satisfaction = await self._get_customer_satisfaction(brand_id, start_date, end_date)
            
            # Get popular channels
            popular_channels = await self._get_popular_channels(brand_id, start_date, end_date)
            
            # Get top issues
            top_issues = await self._get_top_issues(brand_id, start_date, end_date)

            return {
                "brand_id": brand_id,
                "brand_name": brand.name,
                "total_tickets": ticket_stats["total"],
                "resolved_tickets": ticket_stats["resolved"],
                "average_response_time": ticket_stats["avg_response_time"],
                "customer_satisfaction": satisfaction,
                "active_agents": ticket_stats["active_agents"],
                "popular_channels": popular_channels,
                "top_issues": top_issues,
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                }
            }

        except Exception as e:
            raise e

    async def compare_brands_analytics(
        self,
        brand_ids: List[int],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Compare analytics across multiple brands"""
        try:
            # Set default date range if not provided
            if not end_date:
                end_date = datetime.utcnow()
            if not start_date:
                start_date = end_date - timedelta(days=30)

            comparison_data = []
            
            for brand_id in brand_ids:
                analytics = await self.get_brand_analytics(brand_id, start_date, end_date)
                comparison_data.append(analytics)

            # Calculate comparative metrics
            total_tickets = sum(data["total_tickets"] for data in comparison_data)
            avg_satisfaction = sum(data["customer_satisfaction"] for data in comparison_data) / len(comparison_data)
            avg_response_time = sum(data["average_response_time"] for data in comparison_data) / len(comparison_data)

            return {
                "comparison_data": comparison_data,
                "summary": {
                    "total_brands": len(brand_ids),
                    "total_tickets": total_tickets,
                    "average_satisfaction": avg_satisfaction,
                    "average_response_time": avg_response_time
                },
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                }
            }

        except Exception as e:
            raise e

    # Import/Export Methods
    async def export_brand_configuration(
        self,
        brand_id: int,
        include_templates: bool = True,
        include_configurations: bool = True
    ) -> Dict[str, Any]:
        """Export brand configuration"""
        try:
            # Get brand
            brand = await self.get_brand(brand_id)
            if not brand:
                raise ValueError(f"ClaraBrand with ID {brand_id} not found")

            export_data = {
                "brand": {
                    "name": brand.name,
                    "description": brand.description,
                    "logo_url": brand.logo_url,
                    "primary_color": brand.primary_color,
                    "secondary_color": brand.secondary_color,
                    "tone_of_voice": brand.tone_of_voice,
                    "industry": brand.industry,
                    "target_audience": brand.target_audience,
                    "contact_info": brand.contact_info,
                    "social_media_handles": brand.social_media_handles
                },
                "exported_at": datetime.utcnow().isoformat(),
                "version": "1.0"
            }

            # Include configurations
            if include_configurations:
                configs = await self.get_brand_configurations(brand_id)
                export_data["configurations"] = [
                    {
                        "config_type": config.config_type,
                        "config_data": config.config_data,
                        "is_default": config.is_default,
                        "priority": config.priority
                    }
                    for config in configs
                ]

            # Include templates
            if include_templates:
                templates = await self.get_brand_templates(brand_id, active_only=False)
                export_data["templates"] = [
                    {
                        "template_name": template.template_name,
                        "template_type": template.template_type,
                        "content": template.content,
                        "variables": template.variables,
                        "is_active": template.is_active
                    }
                    for template in templates
                ]

            return export_data

        except Exception as e:
            raise e

    async def import_brand_configuration(self, brand_data: Dict[str, Any]) -> ClaraBrand:
        """Import brand configuration"""
        try:
            # Validate required fields
            if "brand" not in brand_data or "name" not in brand_data["brand"]:
                raise ValueError("Invalid brand data format")

            # Create brand
            brand_info = brand_data["brand"]
            brand = await self.create_brand(
                name=brand_info["name"],
                description=brand_info.get("description"),
                logo_url=brand_info.get("logo_url"),
                primary_color=brand_info.get("primary_color"),
                secondary_color=brand_info.get("secondary_color"),
                tone_of_voice=brand_info.get("tone_of_voice", "professional"),
                industry=brand_info.get("industry"),
                target_audience=brand_info.get("target_audience"),
                contact_info=brand_info.get("contact_info"),
                social_media_handles=brand_info.get("social_media_handles")
            )

            # Import configurations
            if "configurations" in brand_data:
                for config_data in brand_data["configurations"]:
                    await self.create_configuration(
                        brand_id=brand.id,
                        config_type=config_data["config_type"],
                        config_data=config_data["config_data"],
                        is_default=config_data.get("is_default", False),
                        priority=config_data.get("priority", 1)
                    )

            # Import templates
            if "templates" in brand_data:
                for template_data in brand_data["templates"]:
                    await self.create_template(
                        brand_id=brand.id,
                        template_name=template_data["template_name"],
                        template_type=template_data["template_type"],
                        content=template_data["content"],
                        variables=template_data.get("variables", []),
                        is_active=template_data.get("is_active", True)
                    )

            return brand

        except Exception as e:
            raise e

    # Private Helper Methods
    async def _create_default_configurations(self, brand_id: int):
        """Create default configurations for a new brand"""
        default_configs = [
            {
                "config_type": "response_templates",
                "config_data": {
                    "max_response_length": 500,
                    "include_branding": True,
                    "auto_escalation_threshold": 3
                },
                "is_default": True,
                "priority": 1
            },
            {
                "config_type": "workflows",
                "config_data": {
                    "auto_categorization": True,
                    "priority_assignment": True,
                    "escalation_rules": []
                },
                "is_default": True,
                "priority": 1
            },
            {
                "config_type": "notification_settings",
                "config_data": {
                    "email_notifications": True,
                    "slack_notifications": False,
                    "urgent_ticket_alerts": True
                },
                "is_default": True,
                "priority": 1
            }
        ]

        for config in default_configs:
            await self.create_configuration(
                brand_id=brand_id,
                config_type=config["config_type"],
                config_data=config["config_data"],
                is_default=config["is_default"],
                priority=config["priority"]
            )

    async def _generate_brand_aware_response(
        self,
        brand: ClaraBrand,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        response_config: Optional[ClaraBrandConfiguration] = None,
        templates: List[ClaraBrandTemplate] = None
    ) -> str:
        """Generate a brand-aware response using NLP and brand configurations"""
        try:
            # Analyze message sentiment and intent
            # Use AI Service Manager for sentiment and intent analysis
            ai_manager = await get_ai_service_manager()
            sentiment_prompt = f"Analyze the sentiment of this message: {message}. Respond with JSON: {{\"sentiment\": \"positive/negative/neutral\", \"score\": 0.0-1.0}}"
            messages = [{"role": "system", "content": "You are an AI assistant that analyzes sentiment. Respond in JSON format."}, {"role": "user", "content": sentiment_prompt}]
            sentiment_response = await ai_manager.generate_text(messages=messages, max_tokens=200, temperature=0.3)
            try:
                import json
                sentiment = json.loads(sentiment_response.text_content) if sentiment_response.success else {"sentiment": "neutral", "score": 0.5}
            except:
                sentiment = {"sentiment": "neutral", "score": 0.5}
            
            intent_prompt = f"Extract the intent from this message: {message}. Respond with JSON: {{\"intent\": \"...\", \"confidence\": 0.0-1.0}}"
            messages = [{"role": "system", "content": "You are an AI assistant that extracts intent. Respond in JSON format."}, {"role": "user", "content": intent_prompt}]
            intent_response = await ai_manager.generate_text(messages=messages, max_tokens=200, temperature=0.3)
            try:
                intent = json.loads(intent_response.text_content) if intent_response.success else {"intent": "general", "confidence": 0.5}
            except:
                intent = {"intent": "general", "confidence": 0.5}

            # Apply brand tone
            tone_adjustments = {
                "formal": "professional and respectful",
                "casual": "friendly and relaxed",
                "friendly": "warm and approachable",
                "professional": "polite and business-like",
                "technical": "detailed and precise",
                "conversational": "natural and engaging"
            }

            tone_instruction = tone_adjustments.get(brand.tone_of_voice, "professional")

            # Build response using brand context
            response_parts = []
            
            # Add brand-specific greeting if available
            if templates:
                greeting_template = next((t for t in templates if t.template_type == "welcome"), None)
                if greeting_template:
                    response_parts.append(greeting_template.content)

            # Generate main response using AI Service Manager
            from core.ai import get_ai_service_manager
            ai_manager = await get_ai_service_manager()
            prompt = f"Context: {context}\n\nMessage: {message}\n\nTone: {tone_instruction}\n\nBrand: {brand.name}"
            messages = [
                {"role": "system", "content": f"You are a customer support assistant for {brand.name}. Use {tone_instruction} tone."},
                {"role": "user", "content": prompt}
            ]
            max_tokens = response_config.config_data.get("max_response_length", 500) if response_config else 500
            ai_response = await ai_manager.generate_text(messages=messages, max_tokens=max_tokens, temperature=0.7)
            main_response = ai_response.text_content if ai_response.success else ""

            response_parts.append(main_response)

            # Add brand signature if configured
            if response_config and response_config.config_data.get("include_branding", True):
                if brand.contact_info:
                    signature = f"\n\nBest regards,\n{brand.name} Support Team"
                    if "email" in brand.contact_info:
                        signature += f"\nEmail: {brand.contact_info['email']}"
                    response_parts.append(signature)

            return " ".join(response_parts)

        except Exception as e:
            # Fallback response
            return f"Thank you for contacting {brand.name}. We're here to help you with your inquiry."

    async def _get_ticket_statistics(
        self, 
        brand_id: int, 
        start_date: datetime, 
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get ticket statistics for a brand"""
        try:
            db = next(get_db())
            
            # Query tickets for the brand in the date range
            tickets = db.query(ClaraSupportTicket).filter(
                and_(
                    ClaraSupportTicket.brand_id == brand_id,
                    ClaraSupportTicket.created_at >= start_date,
                    ClaraSupportTicket.created_at <= end_date
                )
            ).all()
            
            total_tickets = len(tickets)
            resolved_tickets = len([t for t in tickets if t.status == "resolved"])
            
            # Calculate average response time
            response_times = []
            for ticket in tickets:
                if ticket.assigned_at and ticket.created_at:
                    response_time = (ticket.assigned_at - ticket.created_at).total_seconds() / 3600  # hours
                    response_times.append(response_time)
            
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            
            # Count active agents
            active_agents = db.query(ClaraSupportAgent).filter(
                and_(
                    ClaraSupportAgent.brand_id == brand_id,
                    ClaraSupportAgent.is_active == True
                )
            ).count()
            
            return {
                "total": total_tickets,
                "resolved": resolved_tickets,
                "avg_response_time": round(avg_response_time, 2),
                "active_agents": active_agents,
                "resolution_rate": resolved_tickets / total_tickets if total_tickets > 0 else 0
            }
        except Exception as e:
            raise e

    async def _get_customer_satisfaction(
        self, 
        brand_id: int, 
        start_date: datetime, 
        end_date: datetime
    ) -> float:
        """Get customer satisfaction score for a brand"""
        try:
            db = next(get_db())
            
            # Query customer interactions with satisfaction scores
            interactions = db.query(ClaraCustomerInteraction).filter(
                and_(
                    ClaraCustomerInteraction.brand_id == brand_id,
                    ClaraCustomerInteraction.created_at >= start_date,
                    ClaraCustomerInteraction.created_at <= end_date,
                    ClaraCustomerInteraction.satisfaction_score.isnot(None)
                )
            ).all()
            
            if not interactions:
                return 0.0
            
            # Calculate average satisfaction score
            total_score = sum(i.satisfaction_score for i in interactions)
            avg_satisfaction = total_score / len(interactions)
            
            return round(avg_satisfaction, 2)
        except Exception as e:
            raise e

    async def _get_popular_channels(
        self, 
        brand_id: int, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Get popular support channels for a brand"""
        try:
            db = next(get_db())
            
            # Query interactions for the brand in the date range
            interactions = db.query(ClaraCustomerInteraction).filter(
                and_(
                    ClaraCustomerInteraction.brand_id == brand_id,
                    ClaraCustomerInteraction.created_at >= start_date,
                    ClaraCustomerInteraction.created_at <= end_date
                )
            ).all()
            
            # Count interactions by channel
            channel_counts = {}
            total_interactions = len(interactions)
            
            for interaction in interactions:
                channel = interaction.channel
                if channel not in channel_counts:
                    channel_counts[channel] = 0
                channel_counts[channel] += 1
            
            # Convert to list format
            popular_channels = []
            for channel, count in channel_counts.items():
                percentage = (count / total_interactions * 100) if total_interactions > 0 else 0
                popular_channels.append({
                    "channel": channel,
                    "volume": count,
                    "percentage": round(percentage, 1)
                })
            
            # Sort by volume (descending)
            popular_channels.sort(key=lambda x: x["volume"], reverse=True)
            
            return popular_channels
        except Exception as e:
            raise e

    async def _get_top_issues(
        self, 
        brand_id: int, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Get top issues for a brand"""
        try:
            db = next(get_db())
            
            # Query tickets for the brand in the date range
            tickets = db.query(ClaraSupportTicket).filter(
                and_(
                    ClaraSupportTicket.brand_id == brand_id,
                    ClaraSupportTicket.created_at >= start_date,
                    ClaraSupportTicket.created_at <= end_date
                )
            ).all()
            
            # Count tickets by category
            category_counts = {}
            total_tickets = len(tickets)
            
            for ticket in tickets:
                category = ticket.category
                if category not in category_counts:
                    category_counts[category] = 0
                category_counts[category] += 1
            
            # Convert to list format
            top_issues = []
            for category, count in category_counts.items():
                percentage = (count / total_tickets * 100) if total_tickets > 0 else 0
                top_issues.append({
                    "issue": category,
                    "count": count,
                    "percentage": round(percentage, 1)
                })
            
            # Sort by count (descending)
            top_issues.sort(key=lambda x: x["count"], reverse=True)
            
            return top_issues
        except Exception as e:
            raise e

    def _clear_brand_cache(self, brand_id: int):
        """Clear brand-related cache"""
        keys_to_remove = [key for key in self._brand_context_cache.keys() if str(brand_id) in key]
        for key in keys_to_remove:
            del self._brand_context_cache[key]

    def _clear_configuration_cache(self, brand_id: int, config_type: str):
        """Clear configuration cache"""
        cache_key = f"{brand_id}_{config_type}"
        if cache_key in self._configuration_cache:
            del self._configuration_cache[cache_key]

    def _clear_template_cache(self, brand_id: int, template_type: str):
        """Clear template cache"""
        cache_key = f"{brand_id}_{template_type}"
        if cache_key in self._template_cache:
            del self._template_cache[cache_key]
