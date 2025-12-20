"""
Helper functions for broadcasting WebSocket messages
Centralized location for all WebSocket broadcasts
"""

from typing import Dict, Any, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

async def broadcast_task_update(user_id: int, task_data: Dict[str, Any]):
    """Broadcast a task update to a specific user"""
    try:
        from core.realtime.websocket_router import manager
        
        await manager.broadcast_to_user(user_id, {
            "type": "task_update",
            "data": {
                "task_id": task_data.get("id"),
                "agent_id": task_data.get("agent_id"),
                "agent_key": task_data.get("agent_key"),
                "status": task_data.get("status"),
                "title": task_data.get("title"),
                "description": task_data.get("description"),
                "updated_at": task_data.get("updated_at") or datetime.utcnow().isoformat(),
                **task_data
            },
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.warning(f"Failed to broadcast task update: {e}")

async def broadcast_notification(user_id: int, notification: Dict[str, Any]):
    """Broadcast a notification to a specific user"""
    try:
        from core.realtime.websocket_router import broadcast_notification as ws_broadcast
        await ws_broadcast(user_id, notification)
    except Exception as e:
        logger.warning(f"Failed to broadcast notification: {e}")

async def broadcast_agent_response(user_id: int, agent_key: str, response_data: Dict[str, Any]):
    """Broadcast an agent response to a specific user"""
    try:
        from core.realtime.websocket_router import manager
        
        await manager.broadcast_to_user(user_id, {
            "type": "agent_response",
            "data": {
                "agent_key": agent_key,
                "agent_id": agent_key,  # For compatibility
                "response": response_data.get("response"),
                "task_id": response_data.get("task_id"),
                "status": response_data.get("status", "completed"),
                **response_data
            },
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.warning(f"Failed to broadcast agent response: {e}")

