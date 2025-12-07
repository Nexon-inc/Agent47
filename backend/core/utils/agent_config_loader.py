"""
Utility functions for agents to fetch their custom configuration/tweaks
Agents can use these functions to access user's custom instructions and preferences
"""
import logging
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database.models import UserSelectedAgent

logger = logging.getLogger(__name__)


async def get_agent_configuration_for_user(
    user_id: int, 
    agent_key: str, 
    db: AsyncSession
) -> Optional[Dict[str, Any]]:
    """
    Fetch agent's custom configuration/tweaks for a specific user
    Returns configuration dict with custom_instructions and preferences
    """
    try:
        result = await db.execute(
            select(UserSelectedAgent).where(
                UserSelectedAgent.user_id == user_id,
                UserSelectedAgent.agent_key == agent_key
            )
        )
        agent_selection = result.scalar_one_or_none()
        
        if not agent_selection:
            return None
        
        config = agent_selection.configuration if agent_selection.configuration else {}
        
        return {
            "custom_instructions": config.get("custom_instructions", ""),
            "preferences": config.get("preferences", {}),
            "status": agent_selection.status,
            "automation_enabled": agent_selection.automation_enabled
        }
    except Exception as e:
        logger.error(f"Failed to fetch agent configuration for user {user_id}, agent {agent_key}: {e}")
        return None


async def get_agent_custom_instructions(
    user_id: int, 
    agent_key: str, 
    db: AsyncSession
) -> str:
    """
    Get only the custom instructions for an agent (convenience function)
    Returns empty string if no instructions are set
    """
    config = await get_agent_configuration_for_user(user_id, agent_key, db)
    if config:
        return config.get("custom_instructions", "")
    return ""

