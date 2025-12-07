import uuid
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload

from backend.core.ai import get_ai_service_manager, AIServiceManager
from backend.core.cache.redis_manager import init_redis
from ..database import get_clara_database
from ..models import (
    SupportTicket, CustomerInteraction, SupportChannel,
    SentimentType, InteractionType
)

logger = logging.getLogger(__name__)

class ChatWidgetService:
    """Service for managing customizable chat widgets for websites and apps"""
    
    def __init__(self):
        self.ai_service_manager: Optional[AIServiceManager] = None
        self.redis_client = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize chat widget service"""
        if self._initialized:
            return
        
        try:
            self.ai_service_manager = await get_ai_service_manager()
            self.redis_client = await init_redis()
            self._initialized = True
            logger.info("Clara chat widget service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize chat widget service: {e}")
            raise
    
    async def create_chat_widget(
        self,
        brand_id: int,
        widget_config: Dict[str, Any],
        domain_whitelist: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create a new customizable chat widget"""
        try:
            await self.initialize()
            
            # Generate unique widget ID
            widget_id = str(uuid.uuid4())
            
            # Validate widget configuration
            validated_config = await self._validate_widget_config(widget_config)
            
            # Store widget configuration in Redis for fast access
            widget_data = {
                "widget_id": widget_id,
                "brand_id": brand_id,
                "config": validated_config,
                "domain_whitelist": domain_whitelist or [],
                "created_at": datetime.now().isoformat(),
                "is_active": True,
                "usage_stats": {
                    "total_conversations": 0,
                    "total_messages": 0,
                    "average_response_time": 0,
                    "customer_satisfaction": 0
                }
            }
            
            await self.redis_client.setex(
                f"chat_widget:{widget_id}",
                86400,  # 24 hours TTL
                json.dumps(widget_data)
            )
            
            # Generate embed code
            embed_code = await self._generate_embed_code(widget_id, validated_config)
            
            return {
                "success": True,
                "widget_id": widget_id,
                "embed_code": embed_code,
                "config": validated_config,
                "message": "Chat widget created successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to create chat widget: {e}")
            return {
                "success": False,
                "error": f"Failed to create chat widget: {str(e)}"
            }
    
    async def update_chat_widget(
        self,
        widget_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update an existing chat widget configuration"""
        try:
            await self.initialize()
            
            # Get current widget data
            widget_data = await self.redis_client.get(f"chat_widget:{widget_id}")
            if not widget_data:
                return {
                    "success": False,
                    "error": "Widget not found"
                }
            
            current_config = json.loads(widget_data)
            
            # Update configuration
            if "config" in updates:
                validated_config = await self._validate_widget_config(updates["config"])
                current_config["config"].update(validated_config)
            
            if "domain_whitelist" in updates:
                current_config["domain_whitelist"] = updates["domain_whitelist"]
            
            if "is_active" in updates:
                current_config["is_active"] = updates["is_active"]
            
            current_config["updated_at"] = datetime.now().isoformat()
            
            # Store updated configuration
            await self.redis_client.setex(
                f"chat_widget:{widget_id}",
                86400,
                json.dumps(current_config)
            )
            
            # Generate new embed code if config changed
            if "config" in updates:
                embed_code = await self._generate_embed_code(widget_id, current_config["config"])
                current_config["embed_code"] = embed_code
            
            return {
                "success": True,
                "widget_id": widget_id,
                "config": current_config["config"],
                "embed_code": current_config.get("embed_code"),
                "message": "Chat widget updated successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to update chat widget: {e}")
            return {
                "success": False,
                "error": f"Failed to update chat widget: {str(e)}"
            }
    
    async def get_chat_widget(
        self,
        widget_id: str
    ) -> Dict[str, Any]:
        """Get chat widget configuration and stats"""
        try:
            await self.initialize()
            
            widget_data = await self.redis_client.get(f"chat_widget:{widget_id}")
            if not widget_data:
                return {
                    "success": False,
                    "error": "Widget not found"
                }
            
            widget_info = json.loads(widget_data)
            
            # Get real-time stats from database
            db = await get_clara_database()
            async with db.get_session() as session:
                # Get conversation count
                conv_count = await session.execute(
                    select(func.count(SupportTicket.id)).where(
                        and_(
                            SupportTicket.metadata.contains({"widget_id": widget_id}),
                            SupportTicket.created_at >= datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                        )
                    )
                )
                daily_conversations = conv_count.scalar() or 0
                
                # Get message count
                msg_count = await session.execute(
                    select(func.count(CustomerInteraction.id)).where(
                        and_(
                            CustomerInteraction.metadata.contains({"widget_id": widget_id}),
                            CustomerInteraction.created_at >= datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                        )
                    )
                )
                daily_messages = msg_count.scalar() or 0
            
            # Update daily stats
            widget_info["daily_stats"] = {
                "conversations": daily_conversations,
                "messages": daily_messages
            }
            
            return {
                "success": True,
                "widget": widget_info
            }
            
        except Exception as e:
            logger.error(f"Failed to get chat widget: {e}")
            return {
                "success": False,
                "error": f"Failed to get chat widget: {str(e)}"
            }
    
    async def delete_chat_widget(
        self,
        widget_id: str
    ) -> Dict[str, Any]:
        """Delete a chat widget"""
        try:
            await self.initialize()
            
            # Remove from Redis
            await self.redis_client.delete(f"chat_widget:{widget_id}")
            
            return {
                "success": True,
                "message": "Chat widget deleted successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to delete chat widget: {e}")
            return {
                "success": False,
                "error": f"Failed to delete chat widget: {str(e)}"
            }
    
    async def list_chat_widgets(
        self,
        brand_id: int
    ) -> Dict[str, Any]:
        """List all chat widgets for a brand"""
        try:
            await self.initialize()
            
            # Get all widget keys for the brand
            pattern = f"chat_widget:*"
            cursor = 0
            widgets = []
            
            while True:
                cursor, keys = await self.redis_client.scan(cursor, match=pattern, count=100)
                
                for key in keys:
                    widget_data = await self.redis_client.get(key)
                    if widget_data:
                        widget_info = json.loads(widget_data)
                        if widget_info.get("brand_id") == brand_id:
                            widgets.append({
                                "widget_id": widget_info["widget_id"],
                                "config": widget_info["config"],
                                "is_active": widget_info["is_active"],
                                "created_at": widget_info["created_at"],
                                "usage_stats": widget_info["usage_stats"]
                            })
                
                if cursor == 0:
                    break
            
            return {
                "success": True,
                "widgets": widgets,
                "count": len(widgets)
            }
            
        except Exception as e:
            logger.error(f"Failed to list chat widgets: {e}")
            return {
                "success": False,
                "error": f"Failed to list chat widgets: {str(e)}"
            }
    
    async def _validate_widget_config(
        self,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate and sanitize widget configuration"""
        default_config = {
            "theme": "light",
            "primary_color": "#007bff",
            "secondary_color": "#6c757d",
            "position": "bottom-right",
            "size": "medium",
            "greeting_message": "Hello! How can I help you today?",
            "brand_name": "Customer Support",
            "show_avatar": True,
            "show_branding": True,
            "auto_open": False,
            "typing_indicator": True,
            "sound_notifications": True,
            "language": "en",
            "timezone": "UTC"
        }
        
        # Merge with defaults
        validated_config = default_config.copy()
        validated_config.update(config)
        
        # Validate values
        if validated_config["theme"] not in ["light", "dark", "auto"]:
            validated_config["theme"] = "light"
        
        if validated_config["position"] not in ["top-left", "top-right", "bottom-left", "bottom-right", "center"]:
            validated_config["position"] = "bottom-right"
        
        if validated_config["size"] not in ["small", "medium", "large"]:
            validated_config["size"] = "medium"
        
        if validated_config["language"] not in ["en", "es", "fr", "de", "it", "pt", "ru", "zh", "ja", "ko"]:
            validated_config["language"] = "en"
        
        return validated_config
    
    async def _generate_embed_code(
        self,
        widget_id: str,
        config: Dict[str, Any]
    ) -> str:
        """Generate HTML embed code for the chat widget"""
        
        # Generate CSS variables
        css_vars = f"""
            --clara-primary-color: {config['primary_color']};
            --clara-secondary-color: {config['secondary_color']};
            --clara-theme: {config['theme']};
        """
        
        # Generate embed code
        embed_code = f"""
<!-- Clara Chat Widget -->
<div id="clara-chat-widget-{widget_id}" class="clara-chat-widget" style="display: none;">
    <div class="clara-chat-header">
        <div class="clara-chat-brand">
            <span class="clara-brand-name">{config['brand_name']}</span>
        </div>
        <button class="clara-chat-close" onclick="toggleClaraChat('{widget_id}')">×</button>
    </div>
    <div class="clara-chat-body">
        <div class="clara-chat-messages" id="clara-messages-{widget_id}">
            <div class="clara-message clara-bot-message">
                <div class="clara-message-content">
                    {config['greeting_message']}
                </div>
            </div>
        </div>
        <div class="clara-chat-input">
            <input type="text" id="clara-input-{widget_id}" placeholder="Type your message..." />
            <button onclick="sendClaraMessage('{widget_id}')">Send</button>
        </div>
    </div>
</div>

<button class="clara-chat-toggle" onclick="toggleClaraChat('{widget_id}')" style="
    position: fixed;
    {config['position'].replace('-', ': ').replace('top', 'top').replace('bottom', 'bottom').replace('left', 'left').replace('right', 'right')};
    z-index: 9999;
    background: {config['primary_color']};
    color: white;
    border: none;
    border-radius: 50%;
    width: 60px;
    height: 60px;
    cursor: pointer;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
">
    💬
</button>

<style>
.clara-chat-widget {{
    position: fixed;
    bottom: 20px;
    right: 20px;
    width: 350px;
    height: 500px;
    background: white;
    border-radius: 12px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.12);
    z-index: 10000;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    {css_vars}
}}

.clara-chat-header {{
    background: var(--clara-primary-color);
    color: white;
    padding: 16px;
    border-radius: 12px 12px 0 0;
    display: flex;
    justify-content: space-between;
    align-items: center;
}}

.clara-chat-brand-name {{
    font-weight: 600;
    font-size: 16px;
}}

.clara-chat-close {{
    background: none;
    border: none;
    color: white;
    font-size: 24px;
    cursor: pointer;
    padding: 0;
    width: 24px;
    height: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
}}

.clara-chat-body {{
    height: calc(100% - 60px);
    display: flex;
    flex-direction: column;
}}

.clara-chat-messages {{
    flex: 1;
    padding: 16px;
    overflow-y: auto;
}}

.clara-message {{
    margin-bottom: 12px;
}}

.clara-bot-message .clara-message-content {{
    background: #f8f9fa;
    padding: 12px;
    border-radius: 18px;
    max-width: 80%;
    display: inline-block;
}}

.clara-user-message .clara-message-content {{
    background: var(--clara-primary-color);
    color: white;
    padding: 12px;
    border-radius: 18px;
    max-width: 80%;
    display: inline-block;
    margin-left: auto;
    text-align: right;
}}

.clara-chat-input {{
    padding: 16px;
    border-top: 1px solid #e9ecef;
    display: flex;
    gap: 8px;
}}

.clara-chat-input input {{
    flex: 1;
    padding: 12px;
    border: 1px solid #dee2e6;
    border-radius: 24px;
    outline: none;
}}

.clara-chat-input button {{
    background: var(--clara-primary-color);
    color: white;
    border: none;
    padding: 12px 20px;
    border-radius: 24px;
    cursor: pointer;
    font-weight: 500;
}}

.clara-chat-input button:hover {{
    opacity: 0.9;
}}

.clara-chat-toggle:hover {{
    transform: scale(1.1);
    transition: transform 0.2s ease;
}}
</style>

<script>
let claraChatOpen = false;

function toggleClaraChat(widgetId) {{
    const widget = document.getElementById(`clara-chat-widget-${{widgetId}}`);
    const toggle = document.querySelector('.clara-chat-toggle');
    
    if (claraChatOpen) {{
        widget.style.display = 'none';
        toggle.style.display = 'block';
        claraChatOpen = false;
    }} else {{
        widget.style.display = 'block';
        toggle.style.display = 'none';
        claraChatOpen = true;
        document.getElementById(`clara-input-${{widgetId}}`).focus();
    }}
}}

function sendClaraMessage(widgetId) {{
    const input = document.getElementById(`clara-input-${{widgetId}}`);
    const message = input.value.trim();
    
    if (!message) return;
    
    // Add user message to chat
    addMessage(widgetId, message, 'user');
    input.value = '';
    
    // Send to Clara API
    sendToClara(widgetId, message);
}}

function addMessage(widgetId, content, sender) {{
    const messagesContainer = document.getElementById(`clara-messages-${{widgetId}}`);
    const messageDiv = document.createElement('div');
    messageDiv.className = `clara-message clara-${{sender}}-message`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'clara-message-content';
    contentDiv.textContent = content;
    
    messageDiv.appendChild(contentDiv);
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}}

async function sendToClara(widgetId, message) {{
    try {{
        const response = await fetch('/clara/chatbot/message', {{
            method: 'POST',
            headers: {{
                'Content-Type': 'application/json',
            }},
            body: JSON.stringify({{
                message: message,
                widget_id: widgetId,
                channel: 'chat_widget'
            }})
        }});
        
        const data = await response.json();
        
        if (data.success) {{
            addMessage(widgetId, data.response, 'bot');
        }} else {{
            addMessage(widgetId, 'Sorry, I encountered an error. Please try again.', 'bot');
        }}
    }} catch (error) {{
        addMessage(widgetId, 'Sorry, I\'m having trouble connecting. Please try again.', 'bot');
    }}
}}

// Handle Enter key in input
document.addEventListener('DOMContentLoaded', function() {{
    const inputs = document.querySelectorAll('[id^="clara-input-"]');
    inputs.forEach(input => {{
        input.addEventListener('keypress', function(e) {{
            if (e.key === 'Enter') {{
                const widgetId = input.id.replace('clara-input-', '');
                sendClaraMessage(widgetId);
            }}
        }});
    }});
}});
</script>
"""
        
        return embed_code
    
    async def get_widget_analytics(
        self,
        widget_id: str,
        date_range: str = "7d"
    ) -> Dict[str, Any]:
        """Get analytics for a specific chat widget"""
        try:
            await self.initialize()
            
            db = await get_clara_database()
            async with db.get_session() as session:
                # Calculate date range
                end_date = datetime.now()
                if date_range == "1d":
                    start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
                elif date_range == "7d":
                    start_date = end_date - timedelta(days=7)
                elif date_range == "30d":
                    start_date = end_date - timedelta(days=30)
                else:
                    start_date = end_date - timedelta(days=7)
                
                # Get conversation count
                conv_count = await session.execute(
                    select(func.count(SupportTicket.id)).where(
                        and_(
                            SupportTicket.metadata.contains({"widget_id": widget_id}),
                            SupportTicket.created_at >= start_date
                        )
                    )
                )
                conversations = conv_count.scalar() or 0
                
                # Get message count
                msg_count = await session.execute(
                    select(func.count(CustomerInteraction.id)).where(
                        and_(
                            CustomerInteraction.metadata.contains({"widget_id": widget_id}),
                            CustomerInteraction.created_at >= start_date
                        )
                    )
                )
                messages = msg_count.scalar() or 0
                
                # Get average response time
                response_times = await session.execute(
                    select(CustomerInteraction.created_at).where(
                        and_(
                            CustomerInteraction.metadata.contains({"widget_id": widget_id}),
                            CustomerInteraction.interaction_type == InteractionType.BOT_RESPONSE,
                            CustomerInteraction.created_at >= start_date
                        )
                    ).order_by(CustomerInteraction.created_at)
                )
                
                response_times = response_times.scalars().all()
                avg_response_time = 0
                if len(response_times) > 1:
                    total_time = sum([
                        (response_times[i] - response_times[i-1]).total_seconds()
                        for i in range(1, len(response_times))
                    ])
                    avg_response_time = total_time / (len(response_times) - 1)
                
                # Get satisfaction score (if available)
                satisfaction_query = await session.execute(
                    select(func.avg(CustomerInteraction.satisfaction_score)).where(
                        and_(
                            CustomerInteraction.metadata.contains({"widget_id": widget_id}),
                            CustomerInteraction.satisfaction_score.isnot(None),
                            CustomerInteraction.created_at >= start_date
                        )
                    )
                )
                satisfaction_score = satisfaction_query.scalar() or 0
                
                return {
                    "success": True,
                    "analytics": {
                        "date_range": date_range,
                        "conversations": conversations,
                        "messages": messages,
                        "average_response_time_seconds": round(avg_response_time, 2),
                        "customer_satisfaction": round(satisfaction_score, 2),
                        "messages_per_conversation": round(messages / conversations, 2) if conversations > 0 else 0
                    }
                }
                
        except Exception as e:
            logger.error(f"Failed to get widget analytics: {e}")
            return {
                "success": False,
                "error": f"Failed to get widget analytics: {str(e)}"
            }
