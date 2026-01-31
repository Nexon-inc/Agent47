from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging
from .models import BillingPlan, BillingTier
from ..database.connection import get_database
from sqlalchemy import select

logger = logging.getLogger(__name__)

class BillingPlans:
    """Manages billing plans and their features for the Agent47 system."""
    
    def __init__(self):
        self.plans = {}
        self._initialized = False
    
    async def initialize(self):
        """Initialize billing plans with default configurations."""
        if self._initialized:
            return
        db = get_database()
        async with db.get_session() as session:
            # Check if plans already exist
            existing_plans = await session.execute(select(BillingPlan))
            if existing_plans.scalars().first():
                logger.info("Billing plans already exist in database.")
                self._initialized = True
                return

            # Create default billing plans
            default_plans = self._get_default_plans()
            for plan_data in default_plans:
                # Map old/default keys to BillingPlan model fields
                bp = {
                    "name": plan_data.get("name"),
                    "description": plan_data.get("description"),
                    "tier": plan_data.get("tier"),
                    "price_usd": plan_data.get("price_usd", 0.0),
                    "yearly_price_usd": plan_data.get("yearly_price_usd"),
                    "billing_cycle": plan_data.get("billing_cycle", "monthly"),
                    "features": plan_data.get("features", {}),
                    "max_agents": plan_data.get("max_agents", 0),
                    "max_api_calls_per_month": plan_data.get("max_api_calls_per_month", 0),
                    "is_active": plan_data.get("is_active", True)
                }
                plan = BillingPlan(**bp)
                session.add(plan)

            await session.commit()
            logger.info("Default billing plans created successfully.")

        self._initialized = True
    
    def _get_default_plans(self) -> List[Dict[str, Any]]:
        """Get default billing plan configurations."""
        return [
            {
                "tier": BillingTier.FREE,
                "name": "Free Plan",
                "description": "Perfect for trying out Agent47",
                "price_usd": 0.0,
                "yearly_price_usd": 0.0,
                "billing_cycle": "monthly",
                "max_agents": 1,
                "max_api_calls_per_month": 0,  # No API access
                "features": {
                    "agents": {
                        "max_count": 1,
                        "excluded_agents": [],
                        "available_agents": ["aria", "clara", "eric", "joe", "jackie", "shakes", "purity"]
                    },
                    "api_access": False,
                    "inter_agent_communication": False,
                    "team_collaboration": False,
                    "usage_limit_hours": 24,  # 24-hour trial, then 5 actions/day
                    "storage_limit_mb": 100,
                    "support": "community_support",
                    "custom_integrations": {
                        "max_count": 0,
                        "types": []
                    },
                    "advanced_analytics": False,
                    "priority_support": False,
                    "webhook_access": False,
                    "billing_features": {
                        "auto_renewal": False,
                        "payment_methods": [],
                        "invoice_access": False,
                        "usage_reports": False
                    }
                },
                "is_active": True
            },
            {
                "tier": BillingTier.STARTER,
                "name": "Starter Plan",
                "description": "Perfect for freelancers and small teams",
                "price_usd": 24.99,
                "yearly_price_usd": 269.89,  # 10% discount: (24.99 * 12) * 0.9
                "billing_cycle": "monthly",
                "max_agents": 4,
                "max_api_calls_per_month": 0,  # No API access
                "features": {
                    "agents": {
                        "max_count": 4,
                        "excluded_agents": ["purity"],
                        "available_agents": ["aria", "clara", "eric", "joe", "jackie", "shakes"]
                    },
                    "api_access": False,
                    "inter_agent_communication": False,
                    "team_collaboration": False,
                    "usage_limit_hours": None,  # Unlimited
                    "storage_limit_mb": 1000,
                    "support": "email_support",
                    "custom_integrations": {
                        "max_count": 5,
                        "types": ["social_media", "tools"]
                    },
                    "advanced_analytics": False,
                    "priority_support": False,
                    "webhook_access": False,
                    "billing_features": {
                        "auto_renewal": True,
                        "payment_methods": ["card", "bank_transfer"],
                        "invoice_access": True,
                        "usage_reports": True
                    }
                },
                "is_active": True
            },
            {
                "tier": BillingTier.PRO,
                "name": "Pro Plan",
                "description": "For agencies and growing businesses",
                "price_usd": 79.0,
                "yearly_price_usd": 853.20,  # 10% discount: (79 * 12) * 0.9
                "billing_cycle": "monthly",
                "max_agents": 7,  # All 7 agents
                "max_api_calls_per_month": 0,  # No API access
                "features": {
                    "agents": {
                        "max_count": 7,
                        "excluded_agents": [],
                        "available_agents": ["aria", "clara", "eric", "joe", "jackie", "shakes", "purity"]
                    },
                    "api_access": False,
                    "inter_agent_communication": True,
                    "team_collaboration": {
                        "max_members": 5,
                        "features": ["collaboration", "sharing", "permissions"]
                    },
                    "usage_limit_hours": None,  # Unlimited
                    "storage_limit_mb": 5000,
                    "support": "priority_support",
                    "custom_integrations": {
                        "max_count": None,  # Unlimited
                        "types": ["all_platforms", "all_tools"]
                    },
                    "advanced_analytics": True,
                    "priority_support": True,
                    "webhook_access": False,
                    "billing_features": {
                        "auto_renewal": True,
                        "payment_methods": ["card", "bank_transfer", "paypal"],
                        "invoice_access": True,
                        "usage_reports": True,
                        "cost_optimization": True,
                        "budget_alerts": True
                    },
                    "advanced_features": {
                        "custom_agent_development": False,
                        "white_label_options": False,
                        "dedicated_support": False,
                        "custom_contracts": False,
                        "sla_guarantees": False
                    }
                },
                "is_active": True
            }
        ]
    
    async def get_plan_by_tier(self, tier: BillingTier) -> Optional[BillingPlan]:
        """Get billing plan by tier."""
        db = get_database()
        async with db.get_session() as session:
            result = await session.execute(
                select(BillingPlan).where(BillingPlan.tier == tier)
            )
            return result.scalar_one_or_none()
    
    async def get_all_plans(self) -> List[BillingPlan]:
        """Get all active billing plans."""
        db = get_database()
        async with db.get_session() as session:
            result = await session.execute(
                select(BillingPlan).where(BillingPlan.is_active == True)
            )
            return result.scalars().all()
    
    async def get_plan_features(self, tier: BillingTier) -> Dict[str, Any]:
        """Get features for a specific billing tier."""
        plan = await self.get_plan_by_tier(tier)
        if plan:
            return plan.features
        return {}
    
    async def check_feature_access(self, tier: BillingTier, feature: str) -> bool:
        """Check if a tier has access to a specific feature."""
        features = await self.get_plan_features(tier)
        
        feature_map = {
            "api_access": features.get("api_access", False),
            "inter_agent_communication": features.get("inter_agent_communication", False),
            "team_collaboration": features.get("team_collaboration", False),
            "custom_integrations": features.get("custom_integrations", False),
            "advanced_analytics": features.get("advanced_analytics", False),
            "priority_support": features.get("priority_support", False),
            "webhook_access": features.get("webhook_access", False),
            "custom_agent_development": features.get("advanced_features", {}).get("custom_agent_development", False),
            "white_label_options": features.get("advanced_features", {}).get("white_label_options", False),
            "dedicated_support": features.get("advanced_features", {}).get("dedicated_support", False)
        }
        
        return feature_map.get(feature, False)
    
    async def get_agent_limits(self, tier: BillingTier) -> Dict[str, Any]:
        """Get agent limits for a specific tier."""
        features = await self.get_plan_features(tier)
        agent_config = features.get("agents", {})
        
        return {
            "max_count": agent_config.get("max_count"),
            "excluded_agents": agent_config.get("excluded_agents", []),
            "available_agents": agent_config.get("available_agents", [])
        }
    
    async def get_api_limits(self, tier: BillingTier) -> Dict[str, Any]:
        """Get API limits for a specific tier."""
        features = await self.get_plan_features(tier)
        
        return {
            "max_calls_per_month": features.get("max_api_calls_per_month"),
            "rate_limits": features.get("api_rate_limits", {}),
            "webhook_access": features.get("webhook_access", False)
        }
    
    async def get_storage_limits(self, tier: BillingTier) -> Dict[str, Any]:
        """Get storage limits for a specific tier."""
        features = await self.get_plan_features(tier)
        
        return {
            "storage_limit_mb": features.get("storage_limit_mb"),
            "usage_limit_hours": features.get("usage_limit_hours")
        }
    
    async def get_support_level(self, tier: BillingTier) -> str:
        """Get support level for a specific tier."""
        features = await self.get_plan_features(tier)
        return features.get("support", "community_only")
    
    async def can_access_agent(self, tier: BillingTier, agent_name: str) -> bool:
        """Check if a tier can access a specific agent."""
        agent_limits = await self.get_agent_limits(tier)
        excluded_agents = agent_limits.get("excluded_agents", [])
        
        return agent_name.lower() not in [agent.lower() for agent in excluded_agents]
    
    async def get_upgrade_path(self, current_tier: BillingTier) -> List[BillingTier]:
        """Get available upgrade paths from current tier."""
        tier_hierarchy = [BillingTier.FREE, BillingTier.STARTER, BillingTier.PRO]
        
        try:
            current_index = tier_hierarchy.index(current_tier)
            return tier_hierarchy[current_index + 1:]
        except (ValueError, IndexError):
            return []
    
    async def get_downgrade_path(self, current_tier: BillingTier) -> List[BillingTier]:
        """Get available downgrade paths from current tier."""
        tier_hierarchy = [BillingTier.FREE, BillingTier.STARTER, BillingTier.PRO]
        
        try:
            current_index = tier_hierarchy.index(current_tier)
            return tier_hierarchy[:current_index]
        except (ValueError, IndexError):
            return []
    
    async def calculate_upgrade_cost(self, from_tier: BillingTier, to_tier: BillingTier) -> float:
        """Calculate the cost to upgrade between tiers."""
        from_plan = await self.get_plan_by_tier(from_tier)
        to_plan = await self.get_plan_by_tier(to_tier)
        
        if not from_plan or not to_plan:
            return 0.0
        
        # Pro-rated calculation for monthly plans
        if from_plan.billing_cycle == "monthly" and to_plan.billing_cycle == "monthly":
            return to_plan.price_usd - from_plan.price_usd
        
        return to_plan.price_usd
    
    async def get_plan_comparison(self) -> Dict[str, Dict[str, Any]]:
        """Get a comparison of all billing plans."""
        plans = await self.get_all_plans()
        comparison = {}
        
        for plan in plans:
            comparison[plan.tier.value] = {
                "name": plan.name,
                "price": plan.price_usd,
                "billing_cycle": plan.billing_cycle,
                "max_agents": plan.max_agents,
                "max_api_calls": plan.max_api_calls_per_month,
                "features": plan.features,
                "is_active": plan.is_active
            }
        
        return comparison
    
    async def update_plan(self, tier: BillingTier, updates: Dict[str, Any]) -> bool:
        """Update a billing plan."""
        db = get_database()
        async with db.get_session() as session:
            plan = await self.get_plan_by_tier(tier)
            if not plan:
                return False

            for key, value in updates.items():
                if hasattr(plan, key):
                    setattr(plan, key, value)

            plan.updated_at = datetime.utcnow()
            session.add(plan)
            await session.commit()

            logger.info(f"Updated billing plan for tier: {tier}")
            return True
    
    async def deactivate_plan(self, tier: BillingTier) -> bool:
        """Deactivate a billing plan."""
        return await self.update_plan(tier, {"is_active": False})
    
    async def activate_plan(self, tier: BillingTier) -> bool:
        """Activate a billing plan."""
        return await self.update_plan(tier, {"is_active": True})

# Global instance
billing_plans = BillingPlans()

async def get_billing_plans() -> BillingPlans:
    """Get the global billing plans instance."""
    if not billing_plans._initialized:
        await billing_plans.initialize()
    return billing_plans
