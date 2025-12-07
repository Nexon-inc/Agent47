"""
Agent Voice Mapping Service
Maps agents to their gender-specific voices for natural voice output
"""

from typing import Dict, Optional
import logging
from ..config import settings

logger = logging.getLogger(__name__)

# Agent Voice Mapping
# Male Agents: shakes, eric, joe
# Female Agents: clara, jackie, purity, aria

AGENT_VOICE_MAPPING = {
    # Male Agents
    "shakes": {
        "voice": "adam",
        "gender": "male",
        "style": "professional",
        "description": "Creative, professional voice for content creation"
    },
    "eric": {
        "voice": "arnold",
        "gender": "male",
        "style": "confident",
        "description": "Confident, sales-focused voice"
    },
    "joe": {
        "voice": "josh",
        "gender": "male",
        "style": "analytical",
        "description": "Analytical, research-focused voice"
    },
    # Female Agents
    "clara": {
        "voice": "bella",
        "gender": "female",
        "style": "friendly",
        "description": "Friendly, support-focused voice"
    },
    "jackie": {
        "voice": "rachel",
        "gender": "female",
        "style": "energetic",
        "description": "Energetic, marketing-focused voice"
    },
    "purity": {
        "voice": "emily",
        "gender": "female",
        "style": "professional",
        "description": "Professional, business-focused voice"
    },
    "aria": {
        "voice": "nova",
        "gender": "female",
        "style": "warm",
        "description": "Warm, social-focused voice"
    }
}

# Override with environment variables if set
def _load_voice_overrides():
    """Load voice overrides from environment variables"""
    overrides = {}
    for agent_key in AGENT_VOICE_MAPPING.keys():
        env_var = f"AGENT_VOICE_{agent_key.upper()}"
        voice_override = getattr(settings.groq, env_var.lower(), None)
        if voice_override:
            overrides[agent_key] = voice_override
    return overrides

VOICE_OVERRIDES = _load_voice_overrides()

class AgentVoiceMapping:
    """Service for mapping agents to their voice configurations"""
    
    @staticmethod
    def get_agent_voice(agent_key: str) -> Dict[str, str]:
        """
        Get voice configuration for an agent
        
        Args:
            agent_key: Agent identifier (aria, clara, eric, etc.)
            
        Returns:
            Dict with voice, gender, style, and description
        """
        agent_key_lower = agent_key.lower()
        
        if agent_key_lower not in AGENT_VOICE_MAPPING:
            logger.warning(f"Unknown agent key: {agent_key}, using default voice")
            return {
                "voice": "alloy",
                "gender": "neutral",
                "style": "neutral",
                "description": "Default voice"
            }
        
        voice_config = AGENT_VOICE_MAPPING[agent_key_lower].copy()
        
        # Apply environment variable override if exists
        if agent_key_lower in VOICE_OVERRIDES:
            voice_config["voice"] = VOICE_OVERRIDES[agent_key_lower]
            logger.info(f"Using voice override for {agent_key}: {VOICE_OVERRIDES[agent_key_lower]}")
        
        return voice_config
    
    @staticmethod
    def get_voice_for_agent(agent_key: str, language: str = "en") -> str:
        """
        Get the voice name for an agent
        
        Args:
            agent_key: Agent identifier
            language: Language code (for future multi-language support)
            
        Returns:
            Voice name string
        """
        config = AgentVoiceMapping.get_agent_voice(agent_key)
        return config["voice"]
    
    @staticmethod
    def is_male_agent(agent_key: str) -> bool:
        """Check if agent is male"""
        config = AgentVoiceMapping.get_agent_voice(agent_key)
        return config.get("gender") == "male"
    
    @staticmethod
    def is_female_agent(agent_key: str) -> bool:
        """Check if agent is female"""
        config = AgentVoiceMapping.get_agent_voice(agent_key)
        return config.get("gender") == "female"
    
    @staticmethod
    def get_all_agent_voices() -> Dict[str, Dict[str, str]]:
        """Get all agent voice mappings"""
        return AGENT_VOICE_MAPPING.copy()

