import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from datetime import datetime
from core.ai import get_ai_service_manager, AIServiceManager
from core.integrations.integration_manager import IntegrationManager
from core.event_bus.kafka_manager import EventBus
from ..database import get_shakes_database
from ..models import ShakesContentProject, ShakesContentPiece, ContentCollaboration, ContentComment

logger = logging.getLogger(__name__)

class ContentCollaborationService:
    """Service for content collaboration and team management"""
    
    def __init__(self):
        self.integration_manager = IntegrationManager()
        self.event_bus = EventBus()
        self._initialized = False
        self.model_config = {
            "model": "grok-llm",
            "max_tokens": 2000,
            "temperature": 0.5
        }
    
    async def initialize(self):
        """Initialize content collaboration service"""
        if self._initialized:
            return
        
        try:
            await self.integration_manager.initialize()
            await self.event_bus.initialize()
            self._initialized = True
            logger.info("Content collaboration service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize content collaboration service: {e}")
            raise
    
    async def create_collaboration_session(
        self,
        user_id: int,
        content_piece_id: int,
        collaboration_type: str,
        team_members: List[int],
        collaboration_goals: List[str],
        deadline: datetime = None
    ) -> Dict[str, Any]:
        """Create a collaboration session for content"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_shakes_database()
            async with db.get_session() as session:
                # Get content piece
                content_result = await session.execute(
                    select(ShakesContentPiece).where(ShakesContentPiece.id == content_piece_id)
                )
                content_piece = content_result.scalar_one_or_none()
                
                if not content_piece:
                    return {"success": False, "error": "Content piece not found"}
                
                # Create collaboration session
                collaboration = ContentCollaboration(
                    content_piece_id=content_piece_id,
                    owner_id=user_id,
                    collaboration_type=collaboration_type,
                    team_members=team_members,
                    collaboration_goals=collaboration_goals,
                    status="active",
                    deadline=deadline
                )
                session.add(collaboration)
                await session.flush()
                
                # Generate collaboration guidelines
                guidelines_prompt = self._create_collaboration_guidelines_prompt(
                    content_piece, collaboration_type, team_members, collaboration_goals
                )
                # Use AI Service Manager instead of NLPUtils
                ai_manager = await get_ai_service_manager()
                messages = [{"role": "system", "content": "You are an AI assistant that creates collaboration guidelines."}, {"role": "user", "content": guidelines_prompt}]
                ai_response = await ai_manager.generate_text(messages=messages, max_tokens=1500, temperature=0.7)
                collaboration_guidelines = ai_response.text_content if ai_response.success else ""
                
                # Create initial comment
                initial_comment = ContentComment(
                    collaboration_id=collaboration.id,
                    user_id=user_id,
                    comment_type="guidelines",
                    content=collaboration_guidelines,
                    is_system_generated=True
                )
                session.add(initial_comment)
                await session.flush()
                
                await session.commit()
                
                # Publish event
                await self.event_bus.publish("shakes.collaboration_created", {
                    "collaboration_id": collaboration.id,
                    "content_piece_id": content_piece_id,
                    "owner_id": user_id,
                    "team_members": team_members,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                return {
                    "success": True,
                    "collaboration_id": collaboration.id,
                    "content_piece_id": content_piece_id,
                    "collaboration_type": collaboration_type,
                    "team_members": team_members,
                    "collaboration_goals": collaboration_goals,
                    "collaboration_guidelines": collaboration_guidelines,
                    "status": "active",
                    "deadline": deadline.isoformat() if deadline else None,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Collaboration session creation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def add_comment(
        self,
        collaboration_id: int,
        user_id: int,
        comment_type: str,
        content: str,
        parent_comment_id: int = None
    ) -> Dict[str, Any]:
        """Add comment to collaboration session"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_shakes_database()
            async with db.get_session() as session:
                # Get collaboration
                collaboration_result = await session.execute(
                    select(ContentCollaboration).where(ContentCollaboration.id == collaboration_id)
                )
                collaboration = collaboration_result.scalar_one_or_none()
                
                if not collaboration:
                    return {"success": False, "error": "Collaboration session not found"}
                
                # Create comment
                comment = ContentComment(
                    collaboration_id=collaboration_id,
                    user_id=user_id,
                    comment_type=comment_type,
                    content=content,
                    parent_comment_id=parent_comment_id
                )
                session.add(comment)
                await session.flush()
                
                await session.commit()
                
                # Publish event
                await self.event_bus.publish("shakes.comment_added", {
                    "comment_id": comment.id,
                    "collaboration_id": collaboration_id,
                    "user_id": user_id,
                    "comment_type": comment_type,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                return {
                    "success": True,
                    "comment_id": comment.id,
                    "collaboration_id": collaboration_id,
                    "user_id": user_id,
                    "comment_type": comment_type,
                    "content": content,
                    "parent_comment_id": parent_comment_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Comment addition failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_collaboration_thread(
        self,
        collaboration_id: int
    ) -> Dict[str, Any]:
        """Get collaboration thread with all comments"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_shakes_database()
            async with db.get_session() as session:
                # Get collaboration
                collaboration_result = await session.execute(
                    select(ContentCollaboration).where(ContentCollaboration.id == collaboration_id)
                )
                collaboration = collaboration_result.scalar_one_or_none()
                
                if not collaboration:
                    return {"success": False, "error": "Collaboration session not found"}
                
                # Get comments
                comments_result = await session.execute(
                    select(ContentComment).where(ContentComment.collaboration_id == collaboration_id)
                    .order_by(ContentComment.created_at)
                )
                comments = comments_result.scalars().all()
                
                # Format comments
                formatted_comments = []
                for comment in comments:
                    formatted_comments.append({
                        "comment_id": comment.id,
                        "user_id": comment.user_id,
                        "comment_type": comment.comment_type,
                        "content": comment.content,
                        "parent_comment_id": comment.parent_comment_id,
                        "is_system_generated": comment.is_system_generated,
                        "created_at": comment.created_at.isoformat(),
                        "updated_at": comment.updated_at.isoformat()
                    })
                
                return {
                    "success": True,
                    "collaboration_id": collaboration_id,
                    "content_piece_id": collaboration.content_piece_id,
                    "collaboration_type": collaboration.collaboration_type,
                    "team_members": collaboration.team_members,
                    "collaboration_goals": collaboration.collaboration_goals,
                    "status": collaboration.status,
                    "deadline": collaboration.deadline.isoformat() if collaboration.deadline else None,
                    "comments": formatted_comments,
                    "total_comments": len(formatted_comments),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Collaboration thread retrieval failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def update_collaboration_status(
        self,
        collaboration_id: int,
        new_status: str,
        status_notes: str = ""
    ) -> Dict[str, Any]:
        """Update collaboration session status"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_shakes_database()
            async with db.get_session() as session:
                # Get collaboration
                collaboration_result = await session.execute(
                    select(ContentCollaboration).where(ContentCollaboration.id == collaboration_id)
                )
                collaboration = collaboration_result.scalar_one_or_none()
                
                if not collaboration:
                    return {"success": False, "error": "Collaboration session not found"}
                
                # Update status
                old_status = collaboration.status
                collaboration.status = new_status
                collaboration.updated_at = datetime.utcnow()
                
                # Add status update comment if notes provided
                if status_notes:
                    status_comment = ContentComment(
                        collaboration_id=collaboration_id,
                        user_id=collaboration.owner_id,
                        comment_type="status_update",
                        content=f"Status changed from {old_status} to {new_status}. {status_notes}",
                        is_system_generated=True
                    )
                    session.add(status_comment)
                
                await session.commit()
                
                return {
                    "success": True,
                    "collaboration_id": collaboration_id,
                    "old_status": old_status,
                    "new_status": new_status,
                    "status_notes": status_notes,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Collaboration status update failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def generate_collaboration_summary(
        self,
        collaboration_id: int
    ) -> Dict[str, Any]:
        """Generate summary of collaboration session"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_shakes_database()
            async with db.get_session() as session:
                # Get collaboration and comments
                collaboration_result = await session.execute(
                    select(ContentCollaboration).where(ContentCollaboration.id == collaboration_id)
                )
                collaboration = collaboration_result.scalar_one_or_none()
                
                if not collaboration:
                    return {"success": False, "error": "Collaboration session not found"}
                
                comments_result = await session.execute(
                    select(ContentComment).where(ContentComment.collaboration_id == collaboration_id)
                )
                comments = comments_result.scalars().all()
                
                # Generate summary
                summary_prompt = self._create_summary_prompt(collaboration, comments)
                # Use AI Service Manager instead of NLPUtils
                ai_manager = await get_ai_service_manager()
                messages = [{"role": "system", "content": "You are an AI assistant that creates collaboration summaries."}, {"role": "user", "content": summary_prompt}]
                ai_response = await ai_manager.generate_text(messages=messages, max_tokens=1000, temperature=0.7)
                collaboration_summary = ai_response.text_content if ai_response.success else ""
                
                return {
                    "success": True,
                    "collaboration_id": collaboration_id,
                    "collaboration_summary": collaboration_summary,
                    "total_comments": len(comments),
                    "collaboration_goals": collaboration.collaboration_goals,
                    "status": collaboration.status,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Collaboration summary generation failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _create_collaboration_guidelines_prompt(
        self, content_piece: ShakesContentPiece, collaboration_type: str, team_members: List[int], collaboration_goals: List[str]
    ) -> str:
        """Create prompt for collaboration guidelines"""
        return f"""
        Create collaboration guidelines for this content piece:
        
        Content Title: {content_piece.title}
        Content Type: {content_piece.content_type}
        Platform: {content_piece.platform}
        Collaboration Type: {collaboration_type}
        Team Members: {len(team_members)} members
        Collaboration Goals: {', '.join(collaboration_goals)}
        
        Include:
        1. Collaboration objectives and expectations
        2. Roles and responsibilities
        3. Communication guidelines
        4. Review and feedback process
        5. Quality standards
        6. Timeline and deadlines
        7. Best practices for effective collaboration
        
        Format as comprehensive collaboration guidelines.
        """
    
    def _create_summary_prompt(
        self, collaboration: ContentCollaboration, comments: List[ContentComment]
    ) -> str:
        """Create prompt for collaboration summary"""
        return f"""
        Generate a summary of this collaboration session:
        
        Collaboration Type: {collaboration.collaboration_type}
        Goals: {', '.join(collaboration.collaboration_goals)}
        Status: {collaboration.status}
        Total Comments: {len(comments)}
        
        Comments Summary:
        {self._format_comments_for_summary(comments)}
        
        Provide:
        1. Key discussion points
        2. Decisions made
        3. Action items
        4. Next steps
        5. Overall progress assessment
        
        Format as comprehensive collaboration summary.
        """
    
    def _format_comments_for_summary(self, comments: List[ContentComment]) -> str:
        """Format comments for summary generation"""
        formatted_comments = []
        for comment in comments:
            formatted_comments.append(f"- {comment.comment_type}: {comment.content[:100]}...")
        return "\n".join(formatted_comments)
