from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Dict, Any
import json
from datetime import datetime

from ..models import PurityBusinessIdea, PurityEcommerceSetup, PurityBusinessModel
from core.ai import get_ai_service_manager, AIServiceManager
from core.event_bus.kafka_manager import KafkaManager
from core.cache.redis_manager import RedisManager

class EcommerceSetupService:
    def __init__(self):
        self.ai_service_manager: Optional[AIServiceManager] = None
        self.event_bus = KafkaManager()
        self.redis_manager = RedisManager()
    
    async def setup_ecommerce_store(
        self,
        db: AsyncSession,
        business_idea_id: int,
        platform_choice: str,
        store_configuration: Dict[str, Any],
        product_catalog: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        try:
            business_idea_result = await db.execute(
                select(PurityBusinessIdea).where(PurityBusinessIdea.id == business_idea_id)
            )
            business_idea = business_idea_result.scalar_one_or_none()
            if not business_idea:
                raise ValueError("Business idea not found")
            
            cache_key = f"ecommerce_setup:{business_idea_id}:{platform_choice}"
            cached_result = await self.redis_manager.get(cache_key)
            if cached_result:
                return json.loads(cached_result)
            
            prompt = self._create_ecommerce_setup_prompt(
                business_idea, platform_choice, store_configuration, product_catalog
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                from core.ai import get_ai_service_manager
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that helps with ecommerce setup. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            setup_data = json.loads(ai_response)
            
            ecommerce_setup = {
                "id": business_idea_id,
                "business_idea_id": business_idea_id,
                "platform_choice": platform_choice,
                "store_configuration": store_configuration,
                "product_catalog": product_catalog,
                "store_structure": setup_data.get("store_structure", {}),
                "theme_customization": setup_data.get("theme_customization", {}),
                "payment_setup": setup_data.get("payment_setup", {}),
                "shipping_configuration": setup_data.get("shipping_configuration", {}),
                "seo_optimization": setup_data.get("seo_optimization", {}),
                "created_at": datetime.utcnow()
            }
            
            await self.redis_manager.set(cache_key, json.dumps(setup_data), expire=3600)
            await self.event_bus.publish("purity.ecommerce_store_setup", {
                "business_idea_id": business_idea_id,
                "platform_choice": platform_choice,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return ecommerce_setup
            
        except Exception as e:
            raise e
    
    async def configure_product_catalog(
        self,
        db: AsyncSession,
        business_idea_id: int,
        products: List[Dict[str, Any]],
        inventory_management: Dict[str, Any],
        pricing_strategy: Dict[str, Any]
    ) -> Dict[str, Any]:
        try:
            business_idea_result = await db.execute(
                select(PurityBusinessIdea).where(PurityBusinessIdea.id == business_idea_id)
            )
            business_idea = business_idea_result.scalar_one_or_none()
            if not business_idea:
                raise ValueError("Business idea not found")
            
            prompt = self._create_product_catalog_prompt(
                business_idea, products, inventory_management, pricing_strategy
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                from core.ai import get_ai_service_manager
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that helps with ecommerce setup. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            catalog_data = json.loads(ai_response)
            
            product_catalog = {
                "id": business_idea_id,
                "business_idea_id": business_idea_id,
                "products": products,
                "inventory_management": inventory_management,
                "pricing_strategy": pricing_strategy,
                "product_categories": catalog_data.get("product_categories", []),
                "product_descriptions": catalog_data.get("product_descriptions", {}),
                "pricing_structure": catalog_data.get("pricing_structure", {}),
                "inventory_alerts": catalog_data.get("inventory_alerts", []),
                "created_at": datetime.utcnow()
            }
            
            await self.event_bus.publish("purity.product_catalog_configured", {
                "business_idea_id": business_idea_id,
                "product_count": len(products),
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return product_catalog
            
        except Exception as e:
            raise e
    
    async def optimize_store_performance(
        self,
        db: AsyncSession,
        business_idea_id: int,
        performance_metrics: Dict[str, Any],
        optimization_goals: List[str],
        conversion_funnel: Dict[str, Any]
    ) -> Dict[str, Any]:
        try:
            business_idea_result = await db.execute(
                select(PurityBusinessIdea).where(PurityBusinessIdea.id == business_idea_id)
            )
            business_idea = business_idea_result.scalar_one_or_none()
            if not business_idea:
                raise ValueError("Business idea not found")
            
            prompt = self._create_store_optimization_prompt(
                business_idea, performance_metrics, optimization_goals, conversion_funnel
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                from core.ai import get_ai_service_manager
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that helps with ecommerce setup. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            optimization_data = json.loads(ai_response)
            
            store_optimization = {
                "id": business_idea_id,
                "business_idea_id": business_idea_id,
                "performance_metrics": performance_metrics,
                "optimization_goals": optimization_goals,
                "conversion_funnel": conversion_funnel,
                "optimization_strategies": optimization_data.get("optimization_strategies", []),
                "a_b_testing_plans": optimization_data.get("a_b_testing_plans", []),
                "conversion_optimization": optimization_data.get("conversion_optimization", {}),
                "user_experience_improvements": optimization_data.get("user_experience_improvements", []),
                "performance_monitoring": optimization_data.get("performance_monitoring", {}),
                "created_at": datetime.utcnow()
            }
            
            await self.event_bus.publish("purity.store_optimization_completed", {
                "business_idea_id": business_idea_id,
                "optimization_goals": optimization_goals,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return store_optimization
            
        except Exception as e:
            raise e
    
    async def setup_integrations(
        self,
        db: AsyncSession,
        business_idea_id: int,
        integration_requirements: List[str],
        third_party_services: List[str],
        automation_needs: List[str]
    ) -> Dict[str, Any]:
        try:
            business_idea_result = await db.execute(
                select(PurityBusinessIdea).where(PurityBusinessIdea.id == business_idea_id)
            )
            business_idea = business_idea_result.scalar_one_or_none()
            if not business_idea:
                raise ValueError("Business idea not found")
            
            prompt = self._create_integrations_prompt(
                business_idea, integration_requirements, third_party_services, automation_needs
            )
            
            # Use AI Service Manager instead of NLPUtils
            if not self.ai_service_manager:
                from core.ai import get_ai_service_manager
                self.ai_service_manager = await get_ai_service_manager()
            messages = [
                {"role": "system", "content": "You are an AI assistant that helps with ecommerce setup. Respond in JSON format."},
                {"role": "user", "content": prompt}
            ]
            ai_response_obj = await self.ai_service_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
            ai_response = ai_response_obj.text_content if ai_response_obj.success else "{}"
            integrations_data = json.loads(ai_response)
            
            store_integrations = {
                "id": business_idea_id,
                "business_idea_id": business_idea_id,
                "integration_requirements": integration_requirements,
                "third_party_services": third_party_services,
                "automation_needs": automation_needs,
                "integration_setup": integrations_data.get("integration_setup", {}),
                "automation_workflows": integrations_data.get("automation_workflows", []),
                "data_sync_configuration": integrations_data.get("data_sync_configuration", {}),
                "api_connections": integrations_data.get("api_connections", []),
                "created_at": datetime.utcnow()
            }
            
            await self.event_bus.publish("purity.store_integrations_setup", {
                "business_idea_id": business_idea_id,
                "integration_count": len(integration_requirements),
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return store_integrations
            
        except Exception as e:
            raise e
    
    def _create_ecommerce_setup_prompt(
        self,
        business_idea: PurityBusinessIdea,
        platform_choice: str,
        store_configuration: Dict[str, Any],
        product_catalog: List[Dict[str, Any]]
    ) -> str:
        return f"""
        Setup e-commerce store for:
        - Business Idea: {business_idea.description}
        - Platform Choice: {platform_choice}
        - Store Configuration: {store_configuration}
        - Product Catalog: {len(product_catalog)} products
        
        Configure comprehensive e-commerce store including:
        1. Store structure
        2. Theme customization
        3. Payment setup
        4. Shipping configuration
        5. SEO optimization
        
        Return the response as a JSON object with the following structure:
        {{
            "store_structure": {{
                "store_name": "Store name",
                "domain_setup": "Domain configuration",
                "store_layout": "Store layout structure",
                "navigation_structure": "Navigation menu structure",
                "page_templates": "Page template setup"
            }},
            "theme_customization": {{
                "theme_selection": "Theme selection",
                "color_scheme": "Color scheme configuration",
                "typography": "Typography settings",
                "layout_customization": "Layout customization",
                "branding_elements": "Branding elements setup"
            }},
            "payment_setup": {{
                "payment_gateways": ["Gateway 1", "Gateway 2"],
                "payment_methods": ["Method 1", "Method 2"],
                "security_configuration": "Security settings",
                "tax_configuration": "Tax setup",
                "currency_setup": "Currency configuration"
            }},
            "shipping_configuration": {{
                "shipping_zones": ["Zone 1", "Zone 2"],
                "shipping_methods": ["Method 1", "Method 2"],
                "shipping_rates": "Shipping rate configuration",
                "delivery_options": "Delivery options setup",
                "packaging_configuration": "Packaging setup"
            }},
            "seo_optimization": {{
                "meta_tags": "Meta tags configuration",
                "url_structure": "URL structure optimization",
                "content_optimization": "Content SEO setup",
                "sitemap_configuration": "Sitemap setup",
                "analytics_setup": "Analytics configuration"
            }}
        }}
        """
    
    def _create_product_catalog_prompt(
        self,
        business_idea: PurityBusinessIdea,
        products: List[Dict[str, Any]],
        inventory_management: Dict[str, Any],
        pricing_strategy: Dict[str, Any]
    ) -> str:
        return f"""
        Configure product catalog for:
        - Business Idea: {business_idea.description}
        - Products: {len(products)} products
        - Inventory Management: {inventory_management}
        - Pricing Strategy: {pricing_strategy}
        
        Setup comprehensive product catalog including:
        1. Product categories
        2. Product descriptions
        3. Pricing structure
        4. Inventory alerts
        
        Return the response as a JSON object with the following structure:
        {{
            "product_categories": [
                {{
                    "category_name": "Category name",
                    "category_description": "Category description",
                    "product_count": "Number of products",
                    "category_attributes": ["Attribute 1", "Attribute 2"]
                }}
            ],
            "product_descriptions": {{
                "description_templates": "Description templates",
                "feature_highlights": "Feature highlighting",
                "benefit_focus": "Benefit-focused descriptions",
                "seo_optimization": "SEO optimization for descriptions"
            }},
            "pricing_structure": {{
                "base_pricing": "Base pricing strategy",
                "discount_strategy": "Discount configuration",
                "bulk_pricing": "Bulk pricing setup",
                "dynamic_pricing": "Dynamic pricing rules",
                "price_comparison": "Price comparison setup"
            }},
            "inventory_alerts": [
                "Alert 1: Low stock notifications",
                "Alert 2: Out of stock alerts",
                "Alert 3: Reorder point notifications",
                "Alert 4: Inventory level monitoring"
            ]
        }}
        """
    
    def _create_store_optimization_prompt(
        self,
        business_idea: PurityBusinessIdea,
        performance_metrics: Dict[str, Any],
        optimization_goals: List[str],
        conversion_funnel: Dict[str, Any]
    ) -> str:
        return f"""
        Optimize store performance for:
        - Business Idea: {business_idea.description}
        - Performance Metrics: {performance_metrics}
        - Optimization Goals: {', '.join(optimization_goals)}
        - Conversion Funnel: {conversion_funnel}
        
        Provide comprehensive store optimization including:
        1. Optimization strategies
        2. A/B testing plans
        3. Conversion optimization
        4. User experience improvements
        5. Performance monitoring
        
        Return the response as a JSON object with the following structure:
        {{
            "optimization_strategies": [
                "Strategy 1: Improve page load speed",
                "Strategy 2: Optimize product images",
                "Strategy 3: Enhance checkout process",
                "Strategy 4: Improve mobile experience"
            ],
            "a_b_testing_plans": [
                {{
                    "test_name": "Test name",
                    "hypothesis": "Test hypothesis",
                    "variants": ["Variant A", "Variant B"],
                    "success_metric": "Success metric",
                    "test_duration": "Test duration"
                }}
            ],
            "conversion_optimization": {{
                "checkout_optimization": "Checkout process optimization",
                "cart_abandonment": "Cart abandonment reduction",
                "product_page_optimization": "Product page improvements",
                "call_to_action_optimization": "CTA optimization"
            }},
            "user_experience_improvements": [
                "Improvement 1: Simplify navigation",
                "Improvement 2: Enhance search functionality",
                "Improvement 3: Improve product filtering",
                "Improvement 4: Optimize mobile layout"
            ],
            "performance_monitoring": {{
                "key_metrics": "Key performance metrics",
                "monitoring_tools": "Monitoring tools setup",
                "alert_configuration": "Alert configuration",
                "reporting_dashboard": "Reporting dashboard setup"
            }}
        }}
        """
    
    def _create_integrations_prompt(
        self,
        business_idea: PurityBusinessIdea,
        integration_requirements: List[str],
        third_party_services: List[str],
        automation_needs: List[str]
    ) -> str:
        return f"""
        Setup store integrations for:
        - Business Idea: {business_idea.description}
        - Integration Requirements: {', '.join(integration_requirements)}
        - Third Party Services: {', '.join(third_party_services)}
        - Automation Needs: {', '.join(automation_needs)}
        
        Configure comprehensive integrations including:
        1. Integration setup
        2. Automation workflows
        3. Data sync configuration
        4. API connections
        
        Return the response as a JSON object with the following structure:
        {{
            "integration_setup": {{
                "payment_integrations": ["Integration 1", "Integration 2"],
                "shipping_integrations": ["Integration 1", "Integration 2"],
                "marketing_integrations": ["Integration 1", "Integration 2"],
                "analytics_integrations": ["Integration 1", "Integration 2"],
                "crm_integrations": ["Integration 1", "Integration 2"]
            }},
            "automation_workflows": [
                {{
                    "workflow_name": "Workflow name",
                    "trigger_conditions": "Trigger conditions",
                    "automated_actions": ["Action 1", "Action 2"],
                    "workflow_steps": ["Step 1", "Step 2"],
                    "success_criteria": "Success criteria"
                }}
            ],
            "data_sync_configuration": {{
                "sync_frequency": "Data sync frequency",
                "sync_scope": "Data sync scope",
                "error_handling": "Error handling configuration",
                "backup_strategy": "Backup strategy",
                "data_mapping": "Data mapping configuration"
            }},
            "api_connections": [
                {{
                    "api_name": "API name",
                    "endpoint_configuration": "Endpoint setup",
                    "authentication": "Authentication method",
                    "rate_limiting": "Rate limiting configuration",
                    "error_handling": "Error handling setup"
                }}
            ]
        }}
        """
