import uuid
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session

from core.event_bus.kafka_manager import EventBus
from core.cache.redis_manager import RedisManager
from ..models import AgentConnection, AgentEvent, AgentSyncData

class AgentIntegrationService:
    def __init__(self, db: Session):
        self.db = db
        self.event_bus = EventBus()
        self.redis_manager = RedisManager()
        
    async def sync_data_with_agent(self, target_agent: str, data_type: str, data: Dict[str, Any], sync_config: Dict[str, Any]) -> Dict[str, Any]:
        sync_id = str(uuid.uuid4())
        sync_data = AgentSyncData(
            id=sync_id, source_agent="jackie", target_agent=target_agent,
            data_type=data_type, data=json.dumps(data), sync_config=json.dumps(sync_config),
            status="pending", created_at=datetime.utcnow()
        )
        self.db.add(sync_data)
        self.db.commit()
        
        try:
            event_payload = {
                "sync_id": sync_id, "source_agent": "jackie", "target_agent": target_agent,
                "data_type": data_type, "data": data, "sync_config": sync_config,
                "timestamp": datetime.utcnow().isoformat()
            }
            await self.event_bus.publish_event(f"agent.sync.{target_agent}", "data_sync_request", event_payload)
            sync_data.status = "sent"
            self.db.commit()
            return {"sync_id": sync_id, "status": "sent", "target_agent": target_agent, "data_type": data_type}
        except Exception as e:
            sync_data.status = "failed"
            sync_data.error_message = str(e)
            self.db.commit()
            raise Exception(f"Failed to sync data with {target_agent}: {str(e)}")
    
    async def publish_event_to_agents(self, event_type: str, payload: Dict[str, Any], target_agents: List[str]) -> Dict[str, Any]:
        event_id = str(uuid.uuid4())
        event = AgentEvent(
            id=event_id, source_agent="jackie", event_type=event_type,
            payload=json.dumps(payload), target_agents=json.dumps(target_agents),
            status="published", created_at=datetime.utcnow()
        )
        self.db.add(event)
        self.db.commit()
        
        published_count = 0
        failed_agents = []
        
        for agent in target_agents:
            try:
                await self.event_bus.publish_event(f"agent.events.{agent}", event_type, {
                    "event_id": event_id, "source_agent": "jackie", "event_type": event_type,
                    "payload": payload, "timestamp": datetime.utcnow().isoformat()
                })
                published_count += 1
            except Exception as e:
                failed_agents.append({"agent": agent, "error": str(e)})
        
        event.published_count = published_count
        event.failed_agents = json.dumps(failed_agents)
        self.db.commit()
        
        return {"event_id": event_id, "published_count": published_count, "failed_agents": failed_agents, "total_agents": len(target_agents)}
    
    async def establish_connection(self, agent_name: str, connection_config: Dict[str, Any]) -> Dict[str, Any]:
        connection_id = str(uuid.uuid4())
        existing_connection = self.db.query(AgentConnection).filter(
            AgentConnection.source_agent == "jackie",
            AgentConnection.target_agent == agent_name,
            AgentConnection.status == "active"
        ).first()
        
        if existing_connection:
            return {"connection_id": existing_connection.id, "status": "already_connected", "message": f"Already connected to {agent_name}"}
        
        connection = AgentConnection(
            id=connection_id, source_agent="jackie", target_agent=agent_name,
            connection_type=connection_config.get("type", "kafka"), config=json.dumps(connection_config),
            status="connecting", created_at=datetime.utcnow()
        )
        self.db.add(connection)
        self.db.commit()
        
        try:
            await self.event_bus.publish_event(f"agent.connection.{agent_name}", "connection_request", {
                "connection_id": connection_id, "source_agent": "jackie",
                "connection_config": connection_config, "timestamp": datetime.utcnow().isoformat()
            })
            connection.status = "active"
            connection.connected_at = datetime.utcnow()
            self.db.commit()
            return {"connection_id": connection_id, "status": "connected", "target_agent": agent_name, "connection_type": connection_config.get("type", "kafka")}
        except Exception as e:
            connection.status = "failed"
            connection.error_message = str(e)
            self.db.commit()
            raise Exception(f"Failed to establish connection with {agent_name}: {str(e)}")
    
    async def manage_connection(self, connection_id: str, action: str, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        connection = self.db.query(AgentConnection).filter(AgentConnection.id == connection_id).first()
        if not connection:
            raise Exception("Connection not found")
        
        if action == "update":
            if config:
                connection.config = json.dumps(config)
                connection.updated_at = datetime.utcnow()
                self.db.commit()
            return {"message": "Connection updated successfully"}
        elif action == "disconnect":
            try:
                await self.event_bus.publish_event(f"agent.connection.{connection.target_agent}", "disconnect_request", {
                    "connection_id": connection_id, "source_agent": "jackie", "timestamp": datetime.utcnow().isoformat()
                })
                connection.status = "disconnected"
                connection.disconnected_at = datetime.utcnow()
                self.db.commit()
                return {"message": "Connection disconnected successfully"}
            except Exception as e:
                raise Exception(f"Failed to disconnect: {str(e)}")
        elif action == "reconnect":
            try:
                connection.status = "connecting"
                self.db.commit()
                await self.event_bus.publish_event(f"agent.connection.{connection.target_agent}", "reconnect_request", {
                    "connection_id": connection_id, "source_agent": "jackie", "timestamp": datetime.utcnow().isoformat()
                })
                connection.status = "active"
                connection.connected_at = datetime.utcnow()
                self.db.commit()
                return {"message": "Connection reconnected successfully"}
            except Exception as e:
                connection.status = "failed"
                connection.error_message = str(e)
                self.db.commit()
                raise Exception(f"Failed to reconnect: {str(e)}")
        else:
            raise Exception(f"Unknown action: {action}")
    
    async def share_data_with_agents(self, data: Dict[str, Any], data_type: str, target_agents: List[str], sharing_config: Dict[str, Any]) -> Dict[str, Any]:
        share_id = str(uuid.uuid4())
        shared_count = 0
        failed_agents = []
        
        for agent in target_agents:
            try:
                await self.event_bus.publish_event(f"agent.data.{agent}", "data_share", {
                    "share_id": share_id, "source_agent": "jackie", "data_type": data_type,
                    "data": data, "sharing_config": sharing_config, "timestamp": datetime.utcnow().isoformat()
                })
                shared_count += 1
            except Exception as e:
                failed_agents.append({"agent": agent, "error": str(e)})
        
        return {"share_id": share_id, "shared_count": shared_count, "failed_agents": failed_agents, "data_type": data_type, "total_agents": len(target_agents)}
    
    async def trigger_workflow(self, workflow_name: str, target_agent: str, workflow_params: Dict[str, Any]) -> Dict[str, Any]:
        workflow_id = str(uuid.uuid4())
        try:
            await self.event_bus.publish_event(f"agent.workflow.{target_agent}", "workflow_trigger", {
                "workflow_id": workflow_id, "source_agent": "jackie", "workflow_name": workflow_name,
                "workflow_params": workflow_params, "timestamp": datetime.utcnow().isoformat()
            })
            return {"workflow_id": workflow_id, "status": "triggered", "target_agent": target_agent, "workflow_name": workflow_name}
        except Exception as e:
            raise Exception(f"Failed to trigger workflow: {str(e)}")
    
    async def manage_collaboration_request(self, request_type: str, target_agent: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
        request_id = str(uuid.uuid4())
        try:
            await self.event_bus.publish_event(f"agent.collaboration.{target_agent}", "collaboration_request", {
                "request_id": request_id, "source_agent": "jackie", "request_type": request_type,
                "request_data": request_data, "timestamp": datetime.utcnow().isoformat()
            })
            return {"request_id": request_id, "status": "sent", "target_agent": target_agent, "request_type": request_type}
        except Exception as e:
            raise Exception(f"Failed to send collaboration request: {str(e)}")
    
    def get_agent_health(self, agent_name: str) -> Dict[str, Any]:
        try:
            health_data = self.redis_manager.get(f"agent.health.{agent_name}")
            if health_data:
                return json.loads(health_data)
            else:
                return {"agent": agent_name, "status": "unknown", "last_seen": None, "response_time": None}
        except Exception as e:
            return {"agent": agent_name, "status": "error", "error": str(e)}
    
    def get_agent_capabilities(self, agent_name: str) -> Dict[str, Any]:
        try:
            capabilities = self.redis_manager.get(f"agent.capabilities.{agent_name}")
            if capabilities:
                return json.loads(capabilities)
            else:
                return {"agent": agent_name, "capabilities": [], "version": "unknown"}
        except Exception as e:
            return {"agent": agent_name, "capabilities": [], "error": str(e)}
    
    def list_active_connections(self) -> List[Dict[str, Any]]:
        connections = self.db.query(AgentConnection).filter(AgentConnection.status == "active").all()
        return [{
            "id": conn.id, "target_agent": conn.target_agent, "connection_type": conn.connection_type,
            "created_at": conn.created_at.isoformat(), "connected_at": conn.connected_at.isoformat() if conn.connected_at else None
        } for conn in connections]
    
    def get_sync_status(self, sync_id: str) -> Optional[Dict[str, Any]]:
        sync_data = self.db.query(AgentSyncData).filter(AgentSyncData.id == sync_id).first()
        if not sync_data:
            return None
        return {
            "id": sync_data.id, "source_agent": sync_data.source_agent, "target_agent": sync_data.target_agent,
            "data_type": sync_data.data_type, "status": sync_data.status, "created_at": sync_data.created_at.isoformat(),
            "completed_at": sync_data.completed_at.isoformat() if sync_data.completed_at else None, "error_message": sync_data.error_message
        }
    
    def get_recent_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        events = self.db.query(AgentEvent).order_by(AgentEvent.created_at.desc()).limit(limit).all()
        return [{
            "id": event.id, "event_type": event.event_type, "source_agent": event.source_agent,
            "target_agents": json.loads(event.target_agents) if event.target_agents else [], "status": event.status,
            "created_at": event.created_at.isoformat(), "published_count": event.published_count
        } for event in events]
    
    async def subscribe_to_agent_events(self, agent_name: str, event_types: List[str]) -> Dict[str, Any]:
        subscription_id = str(uuid.uuid4())
        try:
            for event_type in event_types:
                await self.event_bus.subscribe_to_topic(f"agent.events.{agent_name}", event_type, self._handle_agent_event)
            return {"subscription_id": subscription_id, "agent": agent_name, "event_types": event_types, "status": "subscribed"}
        except Exception as e:
            raise Exception(f"Failed to subscribe to agent events: {str(e)}")
    
    async def _handle_agent_event(self, event_data: Dict[str, Any]) -> None:
        try:
            event = AgentEvent(
                id=str(uuid.uuid4()), source_agent=event_data.get("source_agent"),
                event_type=event_data.get("event_type"), payload=json.dumps(event_data.get("payload", {})),
                status="received", created_at=datetime.utcnow()
            )
            self.db.add(event)
            self.db.commit()
            await self._process_agent_event(event_data)
        except Exception as e:
            print(f"Error handling agent event: {str(e)}")
    
    async def _process_agent_event(self, event_data: Dict[str, Any]) -> None:
        event_type = event_data.get("event_type")
        source_agent = event_data.get("source_agent")
        payload = event_data.get("payload", {})
        
        if event_type == "data_sync_response":
            await self._handle_sync_response(payload)
        elif event_type == "workflow_completion":
            await self._handle_workflow_completion(payload)
        elif event_type == "collaboration_response":
            await self._handle_collaboration_response(payload)
        elif event_type == "health_update":
            await self._handle_health_update(source_agent, payload)
    
    async def _handle_sync_response(self, payload: Dict[str, Any]) -> None:
        sync_id = payload.get("sync_id")
        if sync_id:
            sync_data = self.db.query(AgentSyncData).filter(AgentSyncData.id == sync_id).first()
            if sync_data:
                sync_data.status = "completed"
                sync_data.completed_at = datetime.utcnow()
                sync_data.response_data = json.dumps(payload.get("response_data", {}))
                self.db.commit()
    
    async def _handle_workflow_completion(self, payload: Dict[str, Any]) -> None:
        workflow_id = payload.get("workflow_id")
        result = payload.get("result", {})
        await self.redis_manager.set(f"workflow.result.{workflow_id}", json.dumps(result), expire=3600)
    
    async def _handle_collaboration_response(self, payload: Dict[str, Any]) -> None:
        request_id = payload.get("request_id")
        response = payload.get("response", {})
        await self.redis_manager.set(f"collaboration.response.{request_id}", json.dumps(response), expire=3600)
    
    async def _handle_health_update(self, agent_name: str, payload: Dict[str, Any]) -> None:
        health_data = {
            "agent": agent_name, "status": payload.get("status", "unknown"),
            "last_seen": datetime.utcnow().isoformat(), "response_time": payload.get("response_time"),
            "capabilities": payload.get("capabilities", [])
        }
        await self.redis_manager.set(f"agent.health.{agent_name}", json.dumps(health_data), expire=300)
        if payload.get("capabilities"):
            await self.redis_manager.set(f"agent.capabilities.{agent_name}", json.dumps(payload.get("capabilities")), expire=3600)
