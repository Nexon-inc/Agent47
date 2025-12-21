"""
WebSocket router for real-time updates
Provides WebSocket endpoints for system status, notifications, and live data
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from typing import Dict, List, Set, Any
import json
import asyncio
import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from core.database.connection import get_db
from core.database import get_supabase
from core.cache import get_redis
from core.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/realtime", tags=["WebSocket"])

# Connection manager for WebSocket connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        self.broadcast_queue: asyncio.Queue = asyncio.Queue()
        
    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
        logger.info(f"WebSocket connected for user {user_id}")
        
    def disconnect(self, websocket: WebSocket, user_id: int):
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        logger.info(f"WebSocket disconnected for user {user_id}")
        
    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            
    async def broadcast_to_user(self, user_id: int, message: Dict[str, Any]):
        if user_id in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_text(json.dumps(message))
                except Exception as e:
                    logger.error(f"Error broadcasting to user {user_id}: {e}")
                    disconnected.add(connection)
            
            # Remove disconnected connections
            for conn in disconnected:
                self.disconnect(conn, user_id)
                
    async def broadcast_to_all(self, message: Dict[str, Any]):
        disconnected_users = []
        for user_id, connections in self.active_connections.items():
            disconnected = set()
            for connection in connections:
                try:
                    await connection.send_text(json.dumps(message))
                except Exception as e:
                    logger.error(f"Error broadcasting to all: {e}")
                    disconnected.add(connection)
            
            # Clean up disconnected connections
            for user_id, connections in list(self.active_connections.items()):
                for conn in disconnected:
                    if conn in connections:
                        connections.discard(conn)
                if not connections:
                    disconnected_users.append(user_id)
        
        for user_id in disconnected_users:
            del self.active_connections[user_id]

# Global connection manager
manager = ConnectionManager()

async def get_system_status_data() -> Dict[str, Any]:
    """Get current system status for real-time updates"""
    try:
        settings = get_settings()
        supabase_manager = await get_supabase()
        supabase_healthy, _ = await supabase_manager.health_check()
        
        # Check Redis health
        redis_healthy = True
        try:
            redis_client = await get_redis()
            await redis_client.ping()
        except Exception:
            redis_healthy = False
        
        # Get agent status
        agent_status = {
            "aria": {"port": settings.agents.aria_port, "status": "running"},
            "clara": {"port": settings.agents.clara_port, "status": "running"},
            "eric": {"port": settings.agents.eric_port, "status": "running"},
            "jackie": {"port": settings.agents.jackie_port, "status": "running"},
            "joe": {"port": settings.agents.joe_port, "status": "running"},
            "purity": {"port": settings.agents.purity_port, "status": "running"},
            "shakes": {"port": settings.agents.shakes_port, "status": "running"}
        }
        
        overall_status = "healthy" if supabase_healthy and redis_healthy else "degraded"
        
        return {
            "type": "system_status",
            "data": {
                "status": overall_status,
                "service": "Agent47 API",
                "version": settings.version,
                "environment": settings.environment,
                "components": {
                    "supabase": "healthy" if supabase_healthy else "unhealthy",
                    "redis": "healthy" if redis_healthy else "unhealthy",
                    "agents": agent_status
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        return {
            "type": "system_status",
            "data": {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        }

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    Main WebSocket endpoint for real-time updates
    Clients should send authentication token in query params or headers
    """
    user_id = None
    
    try:
        # Get user ID from query params or headers
        token = websocket.query_params.get("token") or websocket.headers.get("authorization", "").replace("Bearer ", "")
        
        if not token:
            await websocket.close(code=1008, reason="Authentication required")
            return
        
        # Verify token and get user ID
        from core.authentication.auth_manager import AuthManager
        
        try:
            auth_manager = AuthManager()
            
            # Verify JWT token
            try:
                payload = auth_manager.verify_token(token, "access")
                user_id = payload.get("sub") or payload.get("user_id")
                
                # Convert user_id to int if it's a string
                try:
                    user_id = int(user_id) if user_id else None
                except (ValueError, TypeError):
                    user_id = None
                
                if not user_id:
                    await websocket.close(code=1008, reason="Invalid token")
                    return
            except Exception as e:
                logger.error(f"Token verification error: {e}")
                await websocket.close(code=1008, reason="Invalid token")
                return
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            await websocket.close(code=1008, reason="Invalid token")
            return
        
        # Connect
        await manager.connect(websocket, user_id)
        
        # Send initial system status
        initial_status = await get_system_status_data()
        await manager.send_personal_message(initial_status, websocket)
        
        # Start periodic status updates
        async def send_periodic_updates():
            while True:
                try:
                    await asyncio.sleep(30)  # Update every 30 seconds
                    status = await get_system_status_data()
                    await manager.send_personal_message(status, websocket)
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Error in periodic updates: {e}")
                    break
        
        update_task = asyncio.create_task(send_periodic_updates())
        
        # Listen for messages from client
        try:
            while True:
                data = await websocket.receive_text()
                try:
                    message = json.loads(data)
                    message_type = message.get("type")
                    
                    if message_type == "ping":
                        # Respond to ping with pong
                        await manager.send_personal_message({
                            "type": "pong",
                            "timestamp": datetime.utcnow().isoformat()
                        }, websocket)
                    elif message_type == "subscribe":
                        # Handle subscription requests
                        channels = message.get("channels", [])
                        await manager.send_personal_message({
                            "type": "subscribed",
                            "channels": channels,
                            "timestamp": datetime.utcnow().isoformat()
                        }, websocket)
                    elif message_type == "unsubscribe":
                        # Handle unsubscription requests
                        channels = message.get("channels", [])
                        await manager.send_personal_message({
                            "type": "unsubscribed",
                            "channels": channels,
                            "timestamp": datetime.utcnow().isoformat()
                        }, websocket)
                except json.JSONDecodeError:
                    await manager.send_personal_message({
                        "type": "error",
                        "message": "Invalid JSON format"
                    }, websocket)
                    
        except WebSocketDisconnect:
            update_task.cancel()
            manager.disconnect(websocket, user_id)
            logger.info(f"WebSocket disconnected for user {user_id}")
        except Exception as e:
            logger.error(f"WebSocket error for user {user_id}: {e}")
            update_task.cancel()
            manager.disconnect(websocket, user_id)
            
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except:
            pass

# Function to broadcast notifications to specific user
async def broadcast_notification(user_id: int, notification: Dict[str, Any]):
    """Broadcast a notification to a specific user"""
    await manager.broadcast_to_user(user_id, {
        "type": "notification",
        "data": notification,
        "timestamp": datetime.utcnow().isoformat()
    })

# Function to broadcast team chat messages
async def broadcast_team_chat_message(team_id: int, message: Dict[str, Any]):
    """Broadcast a team chat message to all team members"""
    # Get all team member user IDs
    from core.database import get_database
    from sqlalchemy import select, and_
    from core.database.models import TeamMember
    
    db = await get_database()
    async with db.get_session() as session:
        result = await session.execute(
            select(TeamMember.user_id).where(
                and_(
                    TeamMember.team_id == team_id,
                    TeamMember.is_active == True
                )
            )
        )
        user_ids = [row[0] for row in result.all()]
        
        # Broadcast to all team members
        for user_id in user_ids:
            await manager.broadcast_to_user(user_id, {
                "type": "team_chat_message",
                "data": message,
                "timestamp": datetime.utcnow().isoformat()
            })

# Function to broadcast system-wide alerts
async def broadcast_alert(alert: Dict[str, Any]):
    """Broadcast a system-wide alert to all connected users"""
    await manager.broadcast_to_all({
        "type": "alert",
        "data": alert,
        "timestamp": datetime.utcnow().isoformat()
    })

# Function to broadcast task updates to specific user
async def broadcast_task_update(user_id: int, task_data: Dict[str, Any]):
    """Broadcast a task update to a specific user"""
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

# Function to broadcast agent responses to specific user
async def broadcast_agent_response(user_id: int, agent_key: str, response_data: Dict[str, Any]):
    """Broadcast an agent response to a specific user"""
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

