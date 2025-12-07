from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import json

from ..database import get_db
from ..services.agent_integration_service import AgentIntegrationService

from pydantic import BaseModel

router = APIRouter(prefix="/agent-integration", tags=["Agent Integration"])

class AgentSyncRequest(BaseModel):
    target_agent: str
    sync_type: str
    data: Dict[str, Any]
    priority: str = "normal"


class EventPublishRequest(BaseModel):
    event_type: str
    event_data: Dict[str, Any]
    target_agents: List[str]
    priority: str = "normal"


class AgentConnectionRequest(BaseModel):
    agent_name: str
    connection_type: str
    config: Dict[str, Any]

@router.post("/sync")
async def sync_with_agent(
    request: AgentSyncRequest,
    db: Session = Depends(get_db)
):
    service = AgentIntegrationService(db)
    try:
        result = service.sync_with_agent(
            request.target_agent,
            request.sync_type,
            request.data,
            request.priority
        )
        return {
            "message": f"Sync initiated with {request.target_agent}",
            "sync_id": result["sync_id"],
            "status": result["status"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sync/{sync_id}/status")
async def get_sync_status(sync_id: str, db: Session = Depends(get_db)):
    service = AgentIntegrationService(db)
    try:
        status = service.get_sync_status(sync_id)
        if not status:
            raise HTTPException(status_code=404, detail="Sync not found")
        return status
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/events/publish")
async def publish_event(
    request: EventPublishRequest,
    db: Session = Depends(get_db)
):
    service = AgentIntegrationService(db)
    try:
        result = service.publish_event(
            request.event_type,
            request.event_data,
            request.target_agents,
            request.priority
        )
        return {
            "message": "Event published successfully",
            "event_id": result["event_id"],
            "published_to": result["published_to"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/events")
async def list_events(
    event_type: Optional[str] = None,
    source_agent: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    service = AgentIntegrationService(db)
    try:
        events = service.list_events(event_type, source_agent, limit, offset)
        return {"events": events}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/connections/establish")
async def establish_connection(
    request: AgentConnectionRequest,
    db: Session = Depends(get_db)
):
    service = AgentIntegrationService(db)
    try:
        result = service.establish_connection(
            request.agent_name,
            request.connection_type,
            request.config
        )
        return {
            "message": f"Connection established with {request.agent_name}",
            "connection_id": result["connection_id"],
            "status": result["status"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/connections")
async def list_connections(db: Session = Depends(get_db)):
    service = AgentIntegrationService(db)
    try:
        connections = service.list_connections()
        return {"connections": connections}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/connections/{agent_name}/status")
async def get_connection_status(agent_name: str, db: Session = Depends(get_db)):
    service = AgentIntegrationService(db)
    try:
        status = service.get_connection_status(agent_name)
        if not status:
            raise HTTPException(status_code=404, detail="Connection not found")
        return status
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/connections/{agent_name}/disconnect")
async def disconnect_agent(agent_name: str, db: Session = Depends(get_db)):
    service = AgentIntegrationService(db)
    try:
        result = service.disconnect_agent(agent_name)
        if not result:
            raise HTTPException(status_code=404, detail="Connection not found")
        return {"message": f"Disconnected from {agent_name}"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/data/share")
async def share_data_with_agent(
    target_agent: str,
    data_type: str,
    data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    service = AgentIntegrationService(db)
    try:
        result = service.share_data_with_agent(target_agent, data_type, data)
        return {
            "message": f"Data shared with {target_agent}",
            "share_id": result["share_id"],
            "status": result["status"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/data/received")
async def get_received_data(
    source_agent: Optional[str] = None,
    data_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    service = AgentIntegrationService(db)
    try:
        data = service.get_received_data(source_agent, data_type, limit, offset)
        return {"received_data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/workflows/trigger")
async def trigger_workflow(
    workflow_name: str,
    workflow_data: Dict[str, Any],
    target_agents: List[str],
    db: Session = Depends(get_db)
):
    service = AgentIntegrationService(db)
    try:
        result = service.trigger_workflow(workflow_name, workflow_data, target_agents)
        return {
            "message": "Workflow triggered successfully",
            "workflow_id": result["workflow_id"],
            "status": result["status"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/workflows")
async def list_workflows(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    service = AgentIntegrationService(db)
    try:
        workflows = service.list_workflows(status, limit, offset)
        return {"workflows": workflows}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/workflows/{workflow_id}/status")
async def get_workflow_status(workflow_id: str, db: Session = Depends(get_db)):
    service = AgentIntegrationService(db)
    try:
        status = service.get_workflow_status(workflow_id)
        if not status:
            raise HTTPException(status_code=404, detail="Workflow not found")
        return status
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/collaboration/request")
async def request_collaboration(
    target_agent: str,
    collaboration_type: str,
    request_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    service = AgentIntegrationService(db)
    try:
        result = service.request_collaboration(target_agent, collaboration_type, request_data)
        return {
            "message": f"Collaboration requested with {target_agent}",
            "request_id": result["request_id"],
            "status": result["status"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/collaboration/requests")
async def list_collaboration_requests(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    service = AgentIntegrationService(db)
    try:
        requests = service.list_collaboration_requests(status, limit, offset)
        return {"requests": requests}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/collaboration/{request_id}/respond")
async def respond_to_collaboration(
    request_id: str,
    response: str,
    response_data: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db)
):
    service = AgentIntegrationService(db)
    try:
        result = service.respond_to_collaboration(request_id, response, response_data)
        if not result:
            raise HTTPException(status_code=404, detail="Request not found")
        return {"message": "Response sent successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agents/available")
async def get_available_agents(db: Session = Depends(get_db)):
    service = AgentIntegrationService(db)
    try:
        agents = service.get_available_agents()
        return {"agents": agents}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agents/{agent_name}/capabilities")
async def get_agent_capabilities(agent_name: str, db: Session = Depends(get_db)):
    service = AgentIntegrationService(db)
    try:
        capabilities = service.get_agent_capabilities(agent_name)
        if not capabilities:
            raise HTTPException(status_code=404, detail="Agent not found")
        return capabilities
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/messaging/send")
async def send_message_to_agent(
    target_agent: str,
    message_type: str,
    message_content: Dict[str, Any],
    priority: str = "normal",
    db: Session = Depends(get_db)
):
    service = AgentIntegrationService(db)
    try:
        result = service.send_message_to_agent(target_agent, message_type, message_content, priority)
        return {
            "message": f"Message sent to {target_agent}",
            "message_id": result["message_id"],
            "status": result["status"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/messaging/inbox")
async def get_inbox_messages(
    sender_agent: Optional[str] = None,
    message_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    service = AgentIntegrationService(db)
    try:
        messages = service.get_inbox_messages(sender_agent, message_type, limit, offset)
        return {"messages": messages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/integration")
async def get_integration_analytics(
    timeframe: str = "30d",
    db: Session = Depends(get_db)
):
    service = AgentIntegrationService(db)
    try:
        analytics = service.get_integration_analytics(timeframe)
        return analytics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health/check")
async def check_agent_health(db: Session = Depends(get_db)):
    service = AgentIntegrationService(db)
    try:
        health_status = service.check_agent_health()
        return health_status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
