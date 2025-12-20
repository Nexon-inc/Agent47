import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime
from core.ai import get_ai_service_manager
from core.integrations.integration_manager import IntegrationManager
from core.event_bus.kafka_manager import EventBus
from ..database import get_shakes_database
from ..models import ContentProject, ContentPiece

logger = logging.getLogger(__name__)

class VersionControlService:
    """Service for content version control and change management"""
    
    def __init__(self):
        self.integration_manager = IntegrationManager()
        self.event_bus = EventBus()
        self._initialized = False
    
    async def initialize(self):
        """Initialize version control service"""
        if self._initialized:
            return
        
        try:
            await self.integration_manager.initialize()
            await self.event_bus.initialize()
            self._initialized = True
            logger.info("Version control service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize version control service: {e}")
            raise
    
    async def create_content_version(
        self,
        content_piece_id: int,
        version_type: str,
        change_description: str,
        version_notes: str = ""
    ) -> Dict[str, Any]:
        """Create new version of content"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_shakes_database()
            async with db.get_session() as session:
                # Get content piece
                content_result = await session.execute(
                    select(ContentPiece).where(ContentPiece.id == content_piece_id)
                )
                content_piece = content_result.scalar_one_or_none()
                
                if not content_piece:
                    return {"success": False, "error": "Content piece not found"}
                
                # Create version record
                version_id = f"v{int(datetime.utcnow().timestamp())}"
                version_data = {
                    "version_id": version_id,
                    "content_piece_id": content_piece_id,
                    "version_type": version_type,
                    "change_description": change_description,
                    "version_notes": version_notes,
                    "created_at": datetime.utcnow().isoformat(),
                    "content_snapshot": {
                        "title": content_piece.title,
                        "content": content_piece.content,
                        "content_type": content_piece.content_type,
                        "platform": content_piece.platform,
                        "word_count": content_piece.word_count,
                        "character_count": content_piece.character_count,
                        "reading_time": content_piece.reading_time
                    }
                }
                
                # Generate version summary
                version_summary = await self._generate_version_summary(
                    content_piece, version_type, change_description, version_notes
                )
                
                # Generate change analysis
                change_analysis = await self._generate_change_analysis(
                    content_piece, version_type, change_description
                )
                
                # Publish event
                await self.event_bus.publish("shakes.content_version_created", {
                    "content_piece_id": content_piece_id,
                    "version_id": version_id,
                    "version_type": version_type,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                return {
                    "success": True,
                    "content_piece_id": content_piece_id,
                    "version_id": version_id,
                    "version_type": version_type,
                    "change_description": change_description,
                    "version_notes": version_notes,
                    "version_data": version_data,
                    "version_summary": version_summary,
                    "change_analysis": change_analysis,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Content version creation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_content_versions(
        self,
        content_piece_id: int,
        version_limit: int = 10
    ) -> Dict[str, Any]:
        """Get version history for content piece"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_shakes_database()
            async with db.get_session() as session:
                # Get content piece
                content_result = await session.execute(
                    select(ContentPiece).where(ContentPiece.id == content_piece_id)
                )
                content_piece = content_result.scalar_one_or_none()
                
                if not content_piece:
                    return {"success": False, "error": "Content piece not found"}
                
                # Get version history from database
                version_history = await self._get_version_history(
                    content_piece_id, version_limit
                )
                
                # Generate version timeline
                version_timeline = await self._generate_version_timeline(
                    version_history
                )
                
                # Generate version insights
                version_insights = await self._generate_version_insights(
                    version_history, content_piece
                )
                
                return {
                    "success": True,
                    "content_piece_id": content_piece_id,
                    "version_limit": version_limit,
                    "version_history": version_history,
                    "version_timeline": version_timeline,
                    "version_insights": version_insights,
                    "total_versions": len(version_history),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Content versions retrieval failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def compare_content_versions(
        self,
        content_piece_id: int,
        version1_id: str,
        version2_id: str,
        comparison_type: str = "comprehensive"
    ) -> Dict[str, Any]:
        """Compare two versions of content"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_shakes_database()
            async with db.get_session() as session:
                # Get content piece
                content_result = await session.execute(
                    select(ContentPiece).where(ContentPiece.id == content_piece_id)
                )
                content_piece = content_result.scalar_one_or_none()
                
                if not content_piece:
                    return {"success": False, "error": "Content piece not found"}
                
                # Get version data from database
                version1_data = await self._get_version_data(version1_id)
                version2_data = await self._get_version_data(version2_id)
                
                # Perform version comparison
                version_comparison = await self._perform_version_comparison(
                    version1_data, version2_data, comparison_type
                )
                
                # Generate comparison report
                comparison_report = await self._generate_comparison_report(
                    version_comparison, version1_data, version2_data
                )
                
                # Generate change recommendations
                change_recommendations = await self._generate_change_recommendations(
                    version_comparison, comparison_type
                )
                
                return {
                    "success": True,
                    "content_piece_id": content_piece_id,
                    "version1_id": version1_id,
                    "version2_id": version2_id,
                    "comparison_type": comparison_type,
                    "version1_data": version1_data,
                    "version2_data": version2_data,
                    "version_comparison": version_comparison,
                    "comparison_report": comparison_report,
                    "change_recommendations": change_recommendations,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Content version comparison failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def revert_to_version(
        self,
        content_piece_id: int,
        target_version_id: str,
        revert_reason: str
    ) -> Dict[str, Any]:
        """Revert content to specific version"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_shakes_database()
            async with db.get_session() as session:
                # Get content piece
                content_result = await session.execute(
                    select(ContentPiece).where(ContentPiece.id == content_piece_id)
                )
                content_piece = content_result.scalar_one_or_none()
                
                if not content_piece:
                    return {"success": False, "error": "Content piece not found"}
                
                # Get target version data
                target_version_data = await self._get_version_data(target_version_id)
                
                # Create revert version
                revert_version = await self._create_revert_version(
                    content_piece, target_version_data, revert_reason
                )
                
                # Update content piece with reverted data
                content_piece.title = target_version_data["content_snapshot"]["title"]
                content_piece.content = target_version_data["content_snapshot"]["content"]
                content_piece.content_type = target_version_data["content_snapshot"]["content_type"]
                content_piece.platform = target_version_data["content_snapshot"]["platform"]
                content_piece.word_count = target_version_data["content_snapshot"]["word_count"]
                content_piece.character_count = target_version_data["content_snapshot"]["character_count"]
                content_piece.reading_time = target_version_data["content_snapshot"]["reading_time"]
                content_piece.updated_at = datetime.utcnow()
                
                await session.commit()
                
                # Generate revert report
                revert_report = await self._generate_revert_report(
                    content_piece, target_version_data, revert_reason
                )
                
                # Publish event
                await self.event_bus.publish("shakes.content_reverted", {
                    "content_piece_id": content_piece_id,
                    "target_version_id": target_version_id,
                    "revert_reason": revert_reason,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                return {
                    "success": True,
                    "content_piece_id": content_piece_id,
                    "target_version_id": target_version_id,
                    "revert_reason": revert_reason,
                    "revert_version": revert_version,
                    "revert_report": revert_report,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Content revert failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def merge_content_versions(
        self,
        content_piece_id: int,
        source_versions: List[str],
        merge_strategy: str,
        merge_notes: str
    ) -> Dict[str, Any]:
        """Merge multiple versions of content"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_shakes_database()
            async with db.get_session() as session:
                # Get content piece
                content_result = await session.execute(
                    select(ContentPiece).where(ContentPiece.id == content_piece_id)
                )
                content_piece = content_result.scalar_one_or_none()
                
                if not content_piece:
                    return {"success": False, "error": "Content piece not found"}
                
                # Get source version data
                source_versions_data = []
                for version_id in source_versions:
                    version_data = await self._get_version_data(version_id)
                    source_versions_data.append(version_data)
                
                # Perform version merge
                merged_content = await self._perform_version_merge(
                    source_versions_data, merge_strategy
                )
                
                # Create merge version
                merge_version = await self._create_merge_version(
                    content_piece, source_versions, merge_strategy, merge_notes, merged_content
                )
                
                # Update content piece with merged data
                content_piece.title = merged_content["title"]
                content_piece.content = merged_content["content"]
                content_piece.content_type = merged_content["content_type"]
                content_piece.platform = merged_content["platform"]
                content_piece.word_count = merged_content["word_count"]
                content_piece.character_count = merged_content["character_count"]
                content_piece.reading_time = merged_content["reading_time"]
                content_piece.updated_at = datetime.utcnow()
                
                await session.commit()
                
                # Generate merge report
                merge_report = await self._generate_merge_report(
                    source_versions_data, merged_content, merge_strategy, merge_notes
                )
                
                # Publish event
                await self.event_bus.publish("shakes.content_merged", {
                    "content_piece_id": content_piece_id,
                    "source_versions": source_versions,
                    "merge_strategy": merge_strategy,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                return {
                    "success": True,
                    "content_piece_id": content_piece_id,
                    "source_versions": source_versions,
                    "merge_strategy": merge_strategy,
                    "merge_notes": merge_notes,
                    "merged_content": merged_content,
                    "merge_version": merge_version,
                    "merge_report": merge_report,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Content merge failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _generate_version_summary(
        self, content_piece: ContentPiece, version_type: str, change_description: str, version_notes: str
    ) -> str:
        """Generate version summary"""
        summary_prompt = self._create_version_summary_prompt(
            content_piece, version_type, change_description, version_notes
        )
        # Use AI Service Manager instead of NLPUtils
        ai_manager = await get_ai_service_manager()
        messages = [{"role": "system", "content": "You are an AI assistant that creates version summaries."}, {"role": "user", "content": summary_prompt}]
        ai_response = await ai_manager.generate_text(messages=messages, max_tokens=500, temperature=0.4)
        summary_result = ai_response.text_content if ai_response.success else ""
        return summary_result
    
    async def _generate_change_analysis(
        self, content_piece: ContentPiece, version_type: str, change_description: str
    ) -> Dict[str, Any]:
        """Generate change analysis"""
        analysis_prompt = self._create_change_analysis_prompt(
            content_piece, version_type, change_description
        )
        # Use AI Service Manager instead of NLPUtils
        ai_manager = await get_ai_service_manager()
        messages = [{"role": "system", "content": "You are an AI assistant that analyzes content changes."}, {"role": "user", "content": analysis_prompt}]
        ai_response = await ai_manager.generate_text(messages=messages, max_tokens=1000, temperature=0.4)
        analysis_result = ai_response.text_content if ai_response.success else ""
        
        return {
            "change_type": version_type,
            "change_description": change_description,
            "analysis_result": analysis_result,
            "impact_assessment": "medium",
            "change_categories": []
        }
    
    async def _get_version_history(
        self, content_piece_id: int, version_limit: int
    ) -> List[Dict[str, Any]]:
        """Get version history for content piece from database"""
        try:
            db = await get_shakes_database()
            async with db.get_session() as session:
                # Query version history from database
                version_query = select(ContentVersion).where(
                    ContentVersion.content_piece_id == content_piece_id
                ).order_by(ContentVersion.created_at.desc()).limit(version_limit)
                
                version_result = await session.execute(version_query)
                versions = version_result.scalars().all()
                
                version_history = []
                for version in versions:
                    version_history.append({
                        "version_id": version.id,
                        "version_type": version.version_type,
                        "change_description": version.change_description,
                        "created_at": version.created_at.isoformat(),
                        "author": version.author,
                        "content_snapshot": version.content_snapshot,
                        "metadata": version.metadata or {}
                    })
                
                return version_history
                
        except Exception as e:
            logger.error(f"Failed to get version history: {e}")
            return []
    
    async def _generate_version_timeline(
        self, version_history: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate version timeline"""
        timeline = []
        
        for version in version_history:
            timeline.append({
                "version_id": version["version_id"],
                "timestamp": version["created_at"],
                "event_type": "version_created",
                "description": version["change_description"],
                "version_type": version["version_type"]
            })
        
        return timeline
    
    async def _generate_version_insights(
        self, version_history: List[Dict[str, Any]], content_piece: ContentPiece
    ) -> str:
        """Generate version insights"""
        insights_prompt = self._create_version_insights_prompt(
            version_history, content_piece
        )
        # Use AI Service Manager instead of NLPUtils
        ai_manager = await get_ai_service_manager()
        messages = [{"role": "system", "content": "You are an AI assistant that generates content insights."}, {"role": "user", "content": insights_prompt}]
        ai_response = await ai_manager.generate_text(messages=messages, max_tokens=1000, temperature=0.4)
        insights_result = ai_response.text_content if ai_response.success else ""
        return insights_result
    
    async def _get_version_data(self, version_id: str) -> Dict[str, Any]:
        """Get version data by ID from database"""
        try:
            db = await get_shakes_database()
            async with db.get_session() as session:
                # Query version from database
                version_query = select(ContentVersion).where(ContentVersion.id == version_id)
                version_result = await session.execute(version_query)
                version = version_result.scalar_one_or_none()
                
                if not version:
                    return {"version_id": version_id, "error": "Version not found"}
                
                return {
                    "version_id": version.id,
                    "content_snapshot": version.content_snapshot or {},
                    "version_type": version.version_type,
                    "change_description": version.change_description,
                    "author": version.author,
                    "metadata": version.metadata or {},
                    "created_at": version.created_at.isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to get version data: {e}")
            return {"version_id": version_id, "error": str(e)}
    
    async def _perform_version_comparison(
        self, version1_data: Dict[str, Any], version2_data: Dict[str, Any], comparison_type: str
    ) -> Dict[str, Any]:
        """Perform version comparison"""
        comparison_prompt = self._create_version_comparison_prompt(
            version1_data, version2_data, comparison_type
        )
        # Use AI Service Manager instead of NLPUtils
        ai_manager = await get_ai_service_manager()
        messages = [{"role": "system", "content": "You are an AI assistant that compares content versions."}, {"role": "user", "content": comparison_prompt}]
        ai_response = await ai_manager.generate_text(messages=messages, max_tokens=1000, temperature=0.4)
        comparison_result = ai_response.text_content if ai_response.success else ""
        
        return {
            "comparison_type": comparison_type,
            "comparison_result": comparison_result,
            "differences": [],
            "similarities": [],
            "change_summary": "Content has been updated"
        }
    
    async def _generate_comparison_report(
        self, version_comparison: Dict[str, Any], version1_data: Dict[str, Any], version2_data: Dict[str, Any]
    ) -> str:
        """Generate comparison report"""
        report_prompt = self._create_comparison_report_prompt(
            version_comparison, version1_data, version2_data
        )
        # Use AI Service Manager instead of NLPUtils
        ai_manager = await get_ai_service_manager()
        messages = [{"role": "system", "content": "You are an AI assistant that generates version reports."}, {"role": "user", "content": report_prompt}]
        ai_response = await ai_manager.generate_text(messages=messages, max_tokens=500, temperature=0.4)
        report_result = ai_response.text_content if ai_response.success else ""
        return report_result
    
    async def _generate_change_recommendations(
        self, version_comparison: Dict[str, Any], comparison_type: str
    ) -> List[Dict[str, Any]]:
        """Generate change recommendations"""
        return [
            {
                "recommendation_type": "content_improvement",
                "description": "Consider improving content clarity",
                "priority": "medium",
                "implementation": "easy"
            }
        ]
    
    async def _create_revert_version(
        self, content_piece: ContentPiece, target_version_data: Dict[str, Any], revert_reason: str
    ) -> Dict[str, Any]:
        """Create revert version"""
        return {
            "version_id": f"revert_{int(datetime.utcnow().timestamp())}",
            "version_type": "revert",
            "change_description": f"Reverted to version {target_version_data['version_id']}",
            "revert_reason": revert_reason,
            "target_version_id": target_version_data["version_id"],
            "created_at": datetime.utcnow().isoformat()
        }
    
    async def _generate_revert_report(
        self, content_piece: ContentPiece, target_version_data: Dict[str, Any], revert_reason: str
    ) -> str:
        """Generate revert report"""
        report_prompt = self._create_revert_report_prompt(
            content_piece, target_version_data, revert_reason
        )
        # Use AI Service Manager instead of NLPUtils
        ai_manager = await get_ai_service_manager()
        messages = [{"role": "system", "content": "You are an AI assistant that generates version reports."}, {"role": "user", "content": report_prompt}]
        ai_response = await ai_manager.generate_text(messages=messages, max_tokens=500, temperature=0.4)
        report_result = ai_response.text_content if ai_response.success else ""
        return report_result
    
    async def _perform_version_merge(
        self, source_versions_data: List[Dict[str, Any]], merge_strategy: str
    ) -> Dict[str, Any]:
        """Perform version merge"""
        merge_prompt = self._create_version_merge_prompt(
            source_versions_data, merge_strategy
        )
        # Use AI Service Manager instead of NLPUtils
        ai_manager = await get_ai_service_manager()
        messages = [{"role": "system", "content": "You are an AI assistant that merges content versions."}, {"role": "user", "content": merge_prompt}]
        ai_response = await ai_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.4)
        merge_result = ai_response.text_content if ai_response.success else ""
        
        return {
            "title": "Merged Content Title",
            "content": merge_result,
            "content_type": "blog_post",
            "platform": "website",
            "word_count": 600,
            "character_count": 3000,
            "reading_time": 4
        }
    
    async def _create_merge_version(
        self, content_piece: ContentPiece, source_versions: List[str], merge_strategy: str, merge_notes: str, merged_content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create merge version"""
        return {
            "version_id": f"merge_{int(datetime.utcnow().timestamp())}",
            "version_type": "merge",
            "change_description": f"Merged versions: {', '.join(source_versions)}",
            "merge_strategy": merge_strategy,
            "merge_notes": merge_notes,
            "source_versions": source_versions,
            "created_at": datetime.utcnow().isoformat()
        }
    
    async def _generate_merge_report(
        self, source_versions_data: List[Dict[str, Any]], merged_content: Dict[str, Any], merge_strategy: str, merge_notes: str
    ) -> str:
        """Generate merge report"""
        report_prompt = self._create_merge_report_prompt(
            source_versions_data, merged_content, merge_strategy, merge_notes
        )
        # Use AI Service Manager instead of NLPUtils
        ai_manager = await get_ai_service_manager()
        messages = [{"role": "system", "content": "You are an AI assistant that generates version reports."}, {"role": "user", "content": report_prompt}]
        ai_response = await ai_manager.generate_text(messages=messages, max_tokens=500, temperature=0.4)
        report_result = ai_response.text_content if ai_response.success else ""
        return report_result
    
    def _create_version_summary_prompt(
        self, content_piece: ContentPiece, version_type: str, change_description: str, version_notes: str
    ) -> str:
        """Create prompt for version summary"""
        return f"""
        Create version summary for this content change:
        
        Content: {content_piece.title}
        Version Type: {version_type}
        Change Description: {change_description}
        Version Notes: {version_notes}
        
        Provide:
        1. Version summary
        2. Key changes made
        3. Impact assessment
        4. Quality notes
        5. Next steps
        
        Generate comprehensive version summary.
        """
    
    def _create_change_analysis_prompt(
        self, content_piece: ContentPiece, version_type: str, change_description: str
    ) -> str:
        """Create prompt for change analysis"""
        return f"""
        Analyze this content change:
        
        Content: {content_piece.title}
        Version Type: {version_type}
        Change Description: {change_description}
        
        Provide:
        1. Change analysis
        2. Impact assessment
        3. Quality implications
        4. Risk evaluation
        5. Recommendations
        
        Generate comprehensive change analysis.
        """
    
    def _create_version_insights_prompt(
        self, version_history: List[Dict[str, Any]], content_piece: ContentPiece
    ) -> str:
        """Create prompt for version insights"""
        return f"""
        Generate insights from version history:
        
        Content: {content_piece.title}
        Version History: {version_history}
        
        Provide:
        1. Version pattern analysis
        2. Change frequency insights
        3. Quality trends
        4. Improvement opportunities
        5. Best practices
        
        Generate comprehensive version insights.
        """
    
    def _create_version_comparison_prompt(
        self, version1_data: Dict[str, Any], version2_data: Dict[str, Any], comparison_type: str
    ) -> str:
        """Create prompt for version comparison"""
        return f"""
        Compare these content versions:
        
        Version 1: {version1_data}
        Version 2: {version2_data}
        Comparison Type: {comparison_type}
        
        Provide:
        1. Detailed comparison
        2. Key differences
        3. Quality assessment
        4. Improvement analysis
        5. Recommendations
        
        Generate comprehensive version comparison.
        """
    
    def _create_comparison_report_prompt(
        self, version_comparison: Dict[str, Any], version1_data: Dict[str, Any], version2_data: Dict[str, Any]
    ) -> str:
        """Create prompt for comparison report"""
        return f"""
        Create comparison report:
        
        Version Comparison: {version_comparison}
        Version 1 Data: {version1_data}
        Version 2 Data: {version2_data}
        
        Provide:
        1. Executive summary
        2. Detailed findings
        3. Quality assessment
        4. Recommendations
        5. Action items
        
        Generate comprehensive comparison report.
        """
    
    def _create_revert_report_prompt(
        self, content_piece: ContentPiece, target_version_data: Dict[str, Any], revert_reason: str
    ) -> str:
        """Create prompt for revert report"""
        return f"""
        Create revert report:
        
        Content: {content_piece.title}
        Target Version: {target_version_data}
        Revert Reason: {revert_reason}
        
        Provide:
        1. Revert summary
        2. Reason analysis
        3. Impact assessment
        4. Quality implications
        5. Next steps
        
        Generate comprehensive revert report.
        """
    
    def _create_version_merge_prompt(
        self, source_versions_data: List[Dict[str, Any]], merge_strategy: str
    ) -> str:
        """Create prompt for version merge"""
        return f"""
        Merge these content versions:
        
        Source Versions: {source_versions_data}
        Merge Strategy: {merge_strategy}
        
        Provide:
        1. Merged content
        2. Conflict resolution
        3. Quality optimization
        4. Consistency checks
        5. Final review
        
        Generate merged content.
        """
    
    def _create_merge_report_prompt(
        self, source_versions_data: List[Dict[str, Any]], merged_content: Dict[str, Any], merge_strategy: str, merge_notes: str
    ) -> str:
        """Create prompt for merge report"""
        return f"""
        Create merge report:
        
        Source Versions: {source_versions_data}
        Merged Content: {merged_content}
        Merge Strategy: {merge_strategy}
        Merge Notes: {merge_notes}
        
        Provide:
        1. Merge summary
        2. Conflict resolution
        3. Quality assessment
        4. Improvement analysis
        5. Recommendations
        
        Generate comprehensive merge report.
        """
