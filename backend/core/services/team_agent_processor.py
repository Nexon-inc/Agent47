"""
Team Agent Request Processor
Background processor that handles team-agent requests and posts outputs to chat
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from ..database import get_database as get_db_manager
from ..database.models import TeamAgentRequest, TeamChatMessage
from ..event_bus import get_kafka
from ..voice import get_voice_io_service

logger = logging.getLogger(__name__)

class TeamAgentProcessor:
    """Processes team-agent requests in the background"""
    
    def __init__(self):
        self._running = False
        self._initialized = False
    
    async def initialize(self):
        """Initialize processor"""
        if self._initialized:
            return
        
        self._initialized = True
        logger.info("Team agent processor initialized")
    
    async def start(self):
        """Start background processing"""
        if self._running:
            return
        
        self._running = True
        asyncio.create_task(self._process_requests_loop())
        logger.info("Team agent processor started")
    
    async def stop(self):
        """Stop background processing"""
        self._running = False
        logger.info("Team agent processor stopped")
    
    async def _process_requests_loop(self):
        """Main processing loop"""
        while self._running:
            try:
                await self._process_pending_requests()
                await asyncio.sleep(5)  # Check every 5 seconds
            except Exception as e:
                logger.error(f"Error in request processing loop: {e}")
                await asyncio.sleep(10)
    
    async def _process_pending_requests(self):
        """Process pending agent requests"""
        try:
            db = await get_db_manager()
            async with db.get_session() as session:
                from sqlalchemy import select
                from ..database.models import TeamAgentRequest
                
                # Get pending requests
                result = await session.execute(
                    select(TeamAgentRequest).where(
                        TeamAgentRequest.status == "pending"
                    ).limit(10)
                )
                requests = result.scalars().all()
                
                for request in requests:
                    await self._process_request(request, session)
                    
        except Exception as e:
            logger.error(f"Failed to process pending requests: {e}")
    
    async def _process_request(
        self,
        request: TeamAgentRequest,
        session
    ):
        """Process a single agent request"""
        try:
            # Update status to processing
            request.status = "processing"
            request.processed_at = datetime.utcnow()
            await session.commit()
            
            # Get team owner's tier for image generation access
            # Team members inherit access from team owner's tier
            team_owner_tier = None
            try:
                from sqlalchemy import select
                from ..database.models import Team, User, UserTier
                team_result = await session.execute(
                    select(Team).where(Team.id == request.team_id)
                )
                team = team_result.scalar_one_or_none()
                if team:
                    owner_result = await session.execute(
                        select(User).where(User.id == team.owner_id)
                    )
                    team_owner = owner_result.scalar_one_or_none()
                    if team_owner:
                        team_owner_tier = team_owner.tier
            except Exception as e:
                logger.warning(f"Failed to get team owner tier: {e}")
            
            # Get detailed user resources (platforms, integrations, profile, team)
            user_resources = {}
            try:
                from core.utils.agent_user_data import get_all_user_resources_for_agent
                user_resources = await get_all_user_resources_for_agent(request.team_member_id, session)
            except Exception as e:
                logger.warning(f"Failed to fetch user resources for context: {e}")

            # Get chat history (last 10 messages)
            chat_history = []
            try:
                from sqlalchemy import select
                from ..database.models import TeamChatMessage
                history_result = await session.execute(
                    select(TeamChatMessage).where(
                        TeamChatMessage.team_id == request.team_id,
                        # Filter for messages involving this agent or user
                        # (simplified: just last 10 messages in the team chat)
                        TeamChatMessage.deleted_at.is_(None)
                    ).order_by(TeamChatMessage.created_at.desc()).limit(10)
                )
                history_messages = history_result.scalars().all()
                # Format history for LLM
                for msg in reversed(history_messages):
                    chat_history.append({
                        "role": "assistant" if msg.agent_key else "user",
                        "content": msg.content,
                        "name": msg.agent_key if msg.agent_key else "User"
                    })
            except Exception as e:
                logger.warning(f"Failed to fetch chat history: {e}")

            # Prepare enriched request data
            enriched_request_data = {
                **(request.request_data or {}),
                "history": chat_history,
                "user_resources": user_resources
            }

            # Route to appropriate agent service with team owner's tier
            agent_result = await self._route_to_agent(
                agent_key=request.agent_key,
                request_type=request.request_type,
                request_data=enriched_request_data,
                team_member_id=request.team_member_id,
                team_owner_tier=team_owner_tier,
                db=session  # Pass database session
            )
            
            if not agent_result.get("success"):
                request.status = "failed"
                request.error_message = agent_result.get("error", "Unknown error")
                await session.commit()
                return
            
            # Update request with output
            request.status = "completed"
            request.completed_at = datetime.utcnow()
            request.output_data = agent_result.get("output", {})
            await session.commit()
            
            # Broadcast agent response via WebSocket
            try:
                from core.realtime.broadcast_helpers import broadcast_agent_response
                await broadcast_agent_response(
                    user_id=request.team_member_id,
                    agent_key=request.agent_key,
                    response_data={
                        "response": agent_result.get("response", ""),
                        "task_id": request.id,
                        "status": "completed",
                        "output": agent_result.get("output", {})
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to broadcast agent response: {e}")
            
            # Extract image_url from agent result (could be in output or response)
            image_url = None
            output_data = agent_result.get("output", {})
            if isinstance(output_data, dict):
                image_url = output_data.get("image_url") or agent_result.get("image_url")
            
            # Post output to team chat
            await self._post_to_team_chat(
                team_id=request.team_id,
                team_member_id=request.team_member_id,
                agent_key=request.agent_key,
                content=agent_result.get("response", ""),
                request_id=request.id,
                audio_url=agent_result.get("audio_url"),
                image_url=image_url
            )
            
        except Exception as e:
            logger.error(f"Failed to process request {request.id}: {e}")
            request.status = "failed"
            request.error_message = str(e)
            await session.commit()
    
    async def _route_to_agent(
        self,
        agent_key: str,
        request_type: str,
        request_data: Dict[str, Any],
        team_member_id: int,
        team_owner_tier = None,
        db = None
    ) -> Dict[str, Any]:
        """Route request to appropriate agent service"""
        try:
            # Route based on agent and request type
            if agent_key == "clara":
                from agents.clara.app.services.clara_chat_service import ClaraChatService
                service = ClaraChatService()
                await service.initialize()
                result = await service.process_chat_message(
                    user_id=team_member_id,
                    message=request_data.get("message", ""),
                    session_id=request_data.get("session_id"),
                    db=db,
                    history=request_data.get("history"),
                    user_resources=request_data.get("user_resources")
                )
                return {
                    "success": True,
                    "response": result.get("response", ""),
                    "image_url": result.get("image_url"),
                    "output": result
                }
            
            elif agent_key == "eric":
                from agents.eric.app.services.eric_chat_service import EricChatService
                service = EricChatService()
                await service.initialize()
                result = await service.process_chat_message(
                    user_id=team_member_id,
                    message=request_data.get("message", ""),
                    session_id=request_data.get("session_id"),
                    db=db,
                    history=request_data.get("history"),
                    user_resources=request_data.get("user_resources")
                )
                return {
                    "success": True,
                    "response": result.get("response", ""),
                    "image_url": result.get("image_url"),
                    "output": result
                }
            
            elif agent_key == "aria":
                from agents.aria.app.services.aria_chat_service import AriaChatService
                service = AriaChatService()
                await service.initialize()
                result = await service.process_chat_message(
                    user_id=team_member_id,
                    message=request_data.get("message", ""),
                    session_id=request_data.get("session_id"),
                    db=db,
                    history=request_data.get("history"),
                    user_resources=request_data.get("user_resources")
                )
                return {
                    "success": True,
                    "response": result.get("response", ""),
                    "image_url": result.get("image_url"),
                    "output": result
                }
            
            elif agent_key == "jackie":
                from agents.jackie.app.services.jackie_chat_service import JackieChatService
                service = JackieChatService()
                await service.initialize()
                result = await service.process_chat_message(
                    user_id=team_member_id,
                    message=request_data.get("message", ""),
                    session_id=request_data.get("session_id"),
                    db=db,
                    history=request_data.get("history"),
                    user_resources=request_data.get("user_resources")
                )
                return {
                    "success": True,
                    "response": result.get("response", ""),
                    "image_url": result.get("image_url"),
                    "output": result
                }
            
            elif agent_key == "joe":
                from agents.joe.app.services.joe_chat_service import JoeChatService
                service = JoeChatService()
                await service.initialize()
                result = await service.process_chat_message(
                    user_id=team_member_id,
                    message=request_data.get("message", ""),
                    session_id=request_data.get("session_id"),
                    db=db,
                    history=request_data.get("history"),
                    user_resources=request_data.get("user_resources")
                )
                return {
                    "success": True,
                    "response": result.get("response", ""),
                    "image_url": result.get("image_url"),
                    "output": result
                }
            
            elif agent_key == "purity":
                from agents.purity.app.services.purity_chat_service import PurityChatService
                service = PurityChatService()
                await service.initialize()
                result = await service.process_chat_message(
                    user_id=team_member_id,
                    message=request_data.get("message", ""),
                    session_id=request_data.get("session_id"),
                    db=db,
                    history=request_data.get("history"),
                    user_resources=request_data.get("user_resources")
                )
                return {
                    "success": True,
                    "response": result.get("response", ""),
                    "image_url": result.get("image_url"),
                    "output": result
                }
            
            elif agent_key == "shakes":
                from agents.shakes.app.services.shakes_chat_service import ShakesChatService
                service = ShakesChatService()
                await service.initialize()
                result = await service.process_chat_message(
                    user_id=team_member_id,
                    message=request_data.get("message", ""),
                    session_id=request_data.get("session_id"),
                    db=db,
                    history=request_data.get("history"),
                    user_resources=request_data.get("user_resources")
                )
                return {
                    "success": True,
                    "response": result.get("response", ""),
                    "image_url": result.get("image_url"),
                    "output": result
                }
            
            else:
                return {
                    "success": False,
                    "error": f"Unknown agent: {agent_key}"
                }
                
        except Exception as e:
            logger.error(f"Failed to route to agent {agent_key}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _post_to_team_chat(
        self,
        team_id: int,
        team_member_id: int,
        agent_key: str,
        content: str,
        request_id: int,
        audio_url: Optional[str] = None,
        image_url: Optional[str] = None
    ):
        """Post agent output to team chat"""
        try:
            db = await get_db_manager()
            async with db.get_session() as session:
                from ..database.models import TeamChatMessage
                
                # Include image_url in metadata if provided
                metadata = {
                    "request_id": request_id,
                    "posted_at": datetime.utcnow().isoformat()
                }
                if image_url:
                    metadata["image_url"] = image_url
                
                chat_message = TeamChatMessage(
                    team_id=team_id,
                    user_id=team_member_id,  # Message from team member's perspective
                    agent_key=agent_key,
                    message_type="agent_output",
                    content=content,
                    audio_url=audio_url,
                    file_url=image_url,  # Store image URL in file_url field for frontend
                    metadata=metadata
                )
                
                session.add(chat_message)
                await session.commit()
                
                # Broadcast to team members via WebSocket
                try:
                    from core.realtime.websocket_router import broadcast_team_chat_message
                    await broadcast_team_chat_message(team_id, {
                        "id": chat_message.id,
                        "team_id": team_id,
                        "user_id": team_member_id,
                        "agent_key": agent_key,
                        "message_type": "agent_output",
                        "content": content,
                        "audio_url": audio_url,
                        "created_at": chat_message.created_at.isoformat() if chat_message.created_at else None
                    })
                except Exception as e:
                    logger.warning(f"Failed to broadcast agent output: {e}")
                
                logger.info(f"Posted agent output to team chat for request {request_id}")
                
        except Exception as e:
            logger.error(f"Failed to post to team chat: {e}")

# Singleton instance
_team_agent_processor: Optional[TeamAgentProcessor] = None

async def get_team_agent_processor() -> TeamAgentProcessor:
    """Get or create team agent processor instance"""
    global _team_agent_processor
    if not _team_agent_processor:
        _team_agent_processor = TeamAgentProcessor()
        await _team_agent_processor.initialize()
        await _team_agent_processor.start()
    return _team_agent_processor

