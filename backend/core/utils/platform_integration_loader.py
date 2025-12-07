"""Utility to dynamically load all available platforms and integrations for agent task breakdown"""
import logging
from typing import Dict, List, Any, Optional
from functools import lru_cache

logger = logging.getLogger(__name__)

# Cache for platform and integration data
_platforms_cache: Optional[Dict[str, Any]] = None
_integrations_cache: Optional[Dict[str, Any]] = None

def get_all_platforms_static() -> Dict[str, str]:
    """Get all available platforms from static configuration
    Returns dict mapping platform_key -> display_name
    Includes ALL platforms from backend/core/platforms configuration
    """
    return {
        # Social Media Platforms
        "facebook": "Facebook",
        "instagram": "Instagram",
        "twitter": "Twitter/X",
        "linkedin": "LinkedIn",
        "youtube": "YouTube",
        "tiktok": "TikTok",
        "pinterest": "Pinterest",
        "snapchat": "Snapchat",
        "reddit": "Reddit",
        "discord": "Discord",
        "threads": "Threads",
        # Business Platforms
        "shopify": "Shopify",
        "stripe": "Stripe",
        "mailchimp": "Mailchimp",
        "hubspot": "HubSpot",
        "salesforce": "Salesforce",
        # Content Platforms
        "wordpress": "WordPress",
        "medium": "Medium",
        "substack": "Substack",
        # Analytics Platforms
        "google_analytics": "Google Analytics",
        "mixpanel": "Mixpanel",
        "amplitude": "Amplitude"
    }

def get_all_integrations_static() -> Dict[str, Dict[str, Any]]:
    """Get all available integrations from static configuration
    Returns dict mapping integration_key -> {display_name, integration_type, description}
    Includes ALL integrations from backend/core/integrations configuration
    """
    return {
        # Marketing Integrations
        "mailchimp": {"display_name": "Mailchimp", "type": "marketing", "description": "Email marketing and automation"},
        "convertkit": {"display_name": "ConvertKit", "type": "marketing", "description": "Email marketing for creators"},
        "klaviyo": {"display_name": "Klaviyo", "type": "marketing", "description": "Customer data and marketing automation"},
        # Analytics Integrations
        "google_analytics": {"display_name": "Google Analytics", "type": "analytics", "description": "Web analytics service"},
        "mixpanel": {"display_name": "Mixpanel", "type": "analytics", "description": "Product analytics platform"},
        "amplitude": {"display_name": "Amplitude", "type": "analytics", "description": "Digital analytics platform"},
        # CRM Integrations
        "hubspot": {"display_name": "HubSpot", "type": "crm", "description": "Customer relationship management"},
        "salesforce": {"display_name": "Salesforce", "type": "crm", "description": "CRM and cloud computing platform"},
        "pipedrive": {"display_name": "Pipedrive", "type": "crm", "description": "Sales CRM and pipeline management"},
        "zoho": {"display_name": "Zoho CRM", "type": "crm", "description": "Cloud-based CRM solution"},
        "freshsales": {"display_name": "Freshsales", "type": "crm", "description": "AI-powered CRM"},
        # Content Integrations
        "wordpress": {"display_name": "WordPress", "type": "content", "description": "Content management system"},
        "contentful": {"display_name": "Contentful", "type": "content", "description": "Headless CMS"},
        "notion": {"display_name": "Notion", "type": "content", "description": "All-in-one workspace"},
        # Design Integrations
        "figma": {"display_name": "Figma", "type": "design", "description": "Collaborative design tool"},
        "canva": {"display_name": "Canva", "type": "design", "description": "Graphic design platform"},
        # Productivity Integrations
        "slack": {"display_name": "Slack", "type": "productivity", "description": "Team communication"},
        "trello": {"display_name": "Trello", "type": "productivity", "description": "Project management"},
        "asana": {"display_name": "Asana", "type": "productivity", "description": "Work management platform"},
        # Finance Integrations
        "stripe": {"display_name": "Stripe", "type": "finance", "description": "Payment processing"},
        "paypal": {"display_name": "PayPal", "type": "finance", "description": "Online payment system"},
        # Automation Integrations
        "zapier": {"display_name": "Zapier", "type": "automation", "description": "Workflow automation"},
        "ifttt": {"display_name": "IFTTT", "type": "automation", "description": "Platform automation"},
        # Communication Integrations
        "discord": {"display_name": "Discord", "type": "communication", "description": "Voice and text communication"},
        "telegram": {"display_name": "Telegram", "type": "communication", "description": "Messaging platform"},
        "whatsapp": {"display_name": "WhatsApp", "type": "communication", "description": "Messaging platform"},
        # AI Integrations (fallback)
        "openai": {"display_name": "OpenAI", "type": "ai", "description": "AI research and deployment"},
        "grok-llm": {"display_name": "Grok LLM", "type": "ai", "description": "Advanced AI language model"}
    }

def detect_platforms_in_message(message: str, available_platforms: Optional[Dict[str, str]] = None) -> List[str]:
    """Detect all platforms mentioned in a message
    
    Args:
        message: User message to analyze
        available_platforms: Optional dict of platform_key -> display_name. If None, uses static list.
    
    Returns:
        List of detected platform display names
    """
    if available_platforms is None:
        available_platforms = get_all_platforms_static()
    
    message_lower = message.lower()
    detected = []
    
    for platform_key, platform_name in available_platforms.items():
        # Check for platform name or key in message
        if platform_key in message_lower or platform_name.lower() in message_lower:
            detected.append(platform_name)
    
    return detected

def detect_integrations_in_message(message: str, available_integrations: Optional[Dict[str, Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
    """Detect all integrations mentioned in a message
    
    Args:
        message: User message to analyze
        available_integrations: Optional dict of integration_key -> integration_info. If None, uses static list.
    
    Returns:
        List of detected integration info dicts
    """
    if available_integrations is None:
        available_integrations = get_all_integrations_static()
    
    message_lower = message.lower()
    detected = []
    
    for integration_key, integration_info in available_integrations.items():
        # Check for integration name or key in message
        if integration_key in message_lower or integration_info["display_name"].lower() in message_lower:
            detected.append(integration_info)
    
    return detected

def get_platforms_by_type(platform_type: str) -> Dict[str, str]:
    """Get platforms filtered by type
    
    Args:
        platform_type: Type of platform (social_media, business, content, analytics, etc.)
    
    Returns:
        Dict of platform_key -> display_name
    """
    all_platforms = get_all_platforms_static()
    
    # Type mappings
    type_mappings = {
        "social_media": ["facebook", "instagram", "twitter", "linkedin", "youtube", "tiktok", "pinterest", "snapchat", "reddit", "discord", "threads"],
        "business": ["shopify", "stripe", "mailchimp", "hubspot", "salesforce"],
        "content": ["wordpress", "medium", "substack"],
        "analytics": ["google_analytics", "mixpanel", "amplitude"]
    }
    
    if platform_type in type_mappings:
        return {k: v for k, v in all_platforms.items() if k in type_mappings[platform_type]}
    
    return all_platforms

def get_integrations_by_type(integration_type: str) -> Dict[str, Dict[str, Any]]:
    """Get integrations filtered by type
    
    Args:
        integration_type: Type of integration (marketing, crm, analytics, content, etc.)
    
    Returns:
        Dict of integration_key -> integration_info
    """
    all_integrations = get_all_integrations_static()
    
    return {
        k: v for k, v in all_integrations.items()
        if v.get("type") == integration_type
    }

