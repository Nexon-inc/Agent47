import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime
from core.ai import get_ai_service_manager, AIServiceManager
from core.integrations.integration_manager import IntegrationManager
from core.event_bus.kafka_manager import EventBus
from ..database import get_shakes_database
from ..models import ContentProject, ContentPiece

logger = logging.getLogger(__name__)

class PlagiarismDetectionService:
    """Service for plagiarism detection and originality checking"""
    
    def __init__(self):
        self.integration_manager = IntegrationManager()
        self.event_bus = EventBus()
        self._initialized = False
        self.model_config = {
            "model": "grok-llm",
            "max_tokens": 2000,
            "temperature": 0.1
        }
    
    async def initialize(self):
        """Initialize plagiarism detection service"""
        if self._initialized:
            return
        
        try:
            await self.integration_manager.initialize()
            await self.event_bus.initialize()
            self._initialized = True
            logger.info("Plagiarism detection service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize plagiarism detection service: {e}")
            raise
    
    async def check_plagiarism(
        self,
        content_piece_id: int,
        check_type: str = "comprehensive",
        similarity_threshold: float = 0.8
    ) -> Dict[str, Any]:
        """Check content for plagiarism and originality"""
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
                
                # Perform plagiarism analysis
                plagiarism_analysis = await self._analyze_plagiarism(
                    content_piece.content, content_piece.content_type, check_type, similarity_threshold
                )
                
                # Generate originality report
                originality_report = await self._generate_originality_report(
                    content_piece.content, content_piece.content_type, plagiarism_analysis
                )
                
                # Check against internal database
                internal_similarity = await self._check_internal_similarity(
                    content_piece.content, content_piece_id, session
                )
                
                # Calculate overall originality score
                originality_score = self._calculate_originality_score(
                    plagiarism_analysis, internal_similarity
                )
                
                return {
                    "success": True,
                    "content_piece_id": content_piece_id,
                    "check_type": check_type,
                    "originality_score": originality_score,
                    "plagiarism_analysis": plagiarism_analysis,
                    "originality_report": originality_report,
                    "internal_similarity": internal_similarity,
                    "similarity_threshold": similarity_threshold,
                    "is_original": originality_score >= (1 - similarity_threshold),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Plagiarism check failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def batch_check_plagiarism(
        self,
        content_piece_ids: List[int],
        check_type: str = "comprehensive",
        similarity_threshold: float = 0.8
    ) -> Dict[str, Any]:
        """Check multiple content pieces for plagiarism in batch"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_shakes_database()
            async with db.get_session() as session:
                plagiarism_results = []
                
                for content_piece_id in content_piece_ids:
                    # Get content piece
                    content_result = await session.execute(
                        select(ContentPiece).where(ContentPiece.id == content_piece_id)
                    )
                    content_piece = content_result.scalar_one_or_none()
                    
                    if not content_piece:
                        continue
                    
                    # Perform plagiarism analysis
                    plagiarism_analysis = await self._analyze_plagiarism(
                        content_piece.content, content_piece.content_type, check_type, similarity_threshold
                    )
                    
                    # Check against internal database
                    internal_similarity = await self._check_internal_similarity(
                        content_piece.content, content_piece_id, session
                    )
                    
                    # Calculate originality score
                    originality_score = self._calculate_originality_score(
                        plagiarism_analysis, internal_similarity
                    )
                    
                    plagiarism_results.append({
                        "content_piece_id": content_piece_id,
                        "originality_score": originality_score,
                        "plagiarism_analysis": plagiarism_analysis,
                        "internal_similarity": internal_similarity,
                        "is_original": originality_score >= (1 - similarity_threshold)
                    })
                
                return {
                    "success": True,
                    "plagiarism_results": plagiarism_results,
                    "total_checked": len(plagiarism_results),
                    "check_type": check_type,
                    "similarity_threshold": similarity_threshold,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Batch plagiarism check failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def improve_originality(
        self,
        content_piece_id: int,
        target_originality_score: float = 0.9,
        improvement_focus: List[str] = None
    ) -> Dict[str, Any]:
        """Improve content originality while maintaining quality"""
        if not self._initialized:
            await self.initialize()
        
        if improvement_focus is None:
            improvement_focus = ["rewrite_phrases", "add_original_insights", "restructure_content"]
        
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
                
                # Check current originality
                current_check = await self.check_plagiarism(content_piece_id, "comprehensive", 0.8)
                if not current_check.get("success"):
                    return current_check
                
                current_originality = current_check["originality_score"]
                
                if current_originality >= target_originality_score:
                    return {
                        "success": True,
                        "message": "Content already meets originality target",
                        "current_originality": current_originality,
                        "target_originality": target_originality_score
                    }
                
                # Generate improved content
                improvement_prompt = self._create_originality_improvement_prompt(
                    content_piece.content, content_piece.content_type, current_originality,
                    target_originality_score, improvement_focus
                )
                # Use AI Service Manager instead of NLPUtils
                ai_manager = await get_ai_service_manager()
                messages = [{"role": "system", "content": "You are an AI assistant that improves content originality."}, {"role": "user", "content": improvement_prompt}]
                ai_response = await ai_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.1)
                improved_content = ai_response.text_content if ai_response.success else ""
                
                # Update content piece
                original_content = content_piece.content
                content_piece.content = improved_content
                content_piece.word_count = len(improved_content.split())
                content_piece.character_count = len(improved_content)
                content_piece.reading_time = self._calculate_reading_time(improved_content)
                content_piece.updated_at = datetime.utcnow()
                
                await session.commit()
                
                # Re-check originality
                new_check = await self.check_plagiarism(content_piece_id, "comprehensive", 0.8)
                new_originality = new_check.get("originality_score", current_originality)
                
                return {
                    "success": True,
                    "content_piece_id": content_piece_id,
                    "original_content": original_content,
                    "improved_content": improved_content,
                    "current_originality": current_originality,
                    "new_originality": new_originality,
                    "target_originality": target_originality_score,
                    "improvement_achieved": new_originality - current_originality,
                    "improvement_focus": improvement_focus,
                    "word_count": content_piece.word_count,
                    "reading_time": content_piece.reading_time,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Originality improvement failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _analyze_plagiarism(
        self, content: str, content_type: str, check_type: str, similarity_threshold: float
    ) -> Dict[str, Any]:
        """Analyze content for potential plagiarism"""
        analysis_prompt = self._create_plagiarism_analysis_prompt(
            content, content_type, check_type, similarity_threshold
        )
        # Use AI Service Manager instead of NLPUtils
        ai_manager = await get_ai_service_manager()
        messages = [{"role": "system", "content": "You are an AI assistant that analyzes content for plagiarism. Respond in JSON format."}, {"role": "user", "content": analysis_prompt}]
        ai_response = await ai_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.1)
        analysis_result = ai_response.text_content if ai_response.success else ""
        
        return {
            "analysis_type": check_type,
            "similarity_threshold": similarity_threshold,
            "analysis_result": analysis_result,
            "potential_issues": self._extract_potential_issues(analysis_result),
            "recommendations": self._extract_recommendations(analysis_result)
        }
    
    async def _generate_originality_report(
        self, content: str, content_type: str, plagiarism_analysis: Dict[str, Any]
    ) -> str:
        """Generate comprehensive originality report"""
        report_prompt = self._create_originality_report_prompt(
            content, content_type, plagiarism_analysis
        )
        # Use AI Service Manager instead of NLPUtils
        ai_manager = await get_ai_service_manager()
        messages = [{"role": "system", "content": "You are an AI assistant that generates originality reports."}, {"role": "user", "content": report_prompt}]
        ai_response = await ai_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.1)
        return ai_response.text_content if ai_response.success else ""
    
    async def _check_internal_similarity(
        self, content: str, content_piece_id: int, session: AsyncSession
    ) -> Dict[str, Any]:
        """Check similarity against internal content database"""
        # Get other content pieces from the same user
        other_content_result = await session.execute(
            select(ContentPiece).where(
                ContentPiece.id != content_piece_id,
                ContentPiece.ai_generated == True
            ).limit(100)
        )
        other_content_pieces = other_content_result.scalars().all()
        
        similarities = []
        for other_piece in other_content_pieces:
            similarity_score = self._calculate_text_similarity(content, other_piece.content)
            if similarity_score > 0.3:  # Only report significant similarities
                similarities.append({
                    "content_piece_id": other_piece.id,
                    "similarity_score": similarity_score,
                    "title": other_piece.title,
                    "content_type": other_piece.content_type
                })
        
        return {
            "total_checked": len(other_content_pieces),
            "significant_similarities": similarities,
            "max_similarity": max([s["similarity_score"] for s in similarities], default=0.0)
        }
    
    def _calculate_originality_score(
        self, plagiarism_analysis: Dict[str, Any], internal_similarity: Dict[str, Any]
    ) -> float:
        """Calculate overall originality score"""
        # Base score from plagiarism analysis
        base_score = 0.8  # Default assumption
        
        # Adjust based on internal similarity
        max_internal_similarity = internal_similarity.get("max_similarity", 0.0)
        internal_penalty = max_internal_similarity * 0.5
        
        # Calculate final score
        originality_score = max(0.0, min(1.0, base_score - internal_penalty))
        
        return round(originality_score, 3)
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts"""
        # Simple word-based similarity calculation
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _extract_potential_issues(self, analysis_result: str) -> List[str]:
        """Extract potential plagiarism issues from analysis"""
        # Simple extraction - in production, use more sophisticated parsing
        issues = []
        if "similar" in analysis_result.lower():
            issues.append("Potential similarity to existing content")
        if "common phrase" in analysis_result.lower():
            issues.append("Common phrases detected")
        if "template" in analysis_result.lower():
            issues.append("Template-like content detected")
        return issues
    
    def _extract_recommendations(self, analysis_result: str) -> List[str]:
        """Extract improvement recommendations from analysis"""
        recommendations = []
        if "rewrite" in analysis_result.lower():
            recommendations.append("Consider rewriting certain sections")
        if "original" in analysis_result.lower():
            recommendations.append("Add more original insights")
        if "structure" in analysis_result.lower():
            recommendations.append("Restructure content for better originality")
        return recommendations
    
    def _create_plagiarism_analysis_prompt(
        self, content: str, content_type: str, check_type: str, similarity_threshold: float
    ) -> str:
        """Create prompt for plagiarism analysis"""
        return f"""
        Analyze this {content_type} content for potential plagiarism:
        
        Content:
        {content}
        
        Analysis Type: {check_type}
        Similarity Threshold: {similarity_threshold}
        
        Check for:
        1. Common phrases and expressions
        2. Template-like structures
        3. Generic content patterns
        4. Overused industry terminology
        5. Lack of original insights
        6. Structural similarities to common formats
        
        Provide:
        1. Overall originality assessment
        2. Specific areas of concern
        3. Similarity indicators
        4. Recommendations for improvement
        
        Format as comprehensive plagiarism analysis.
        """
    
    def _create_originality_report_prompt(
        self, content: str, content_type: str, plagiarism_analysis: Dict[str, Any]
    ) -> str:
        """Create prompt for originality report"""
        return f"""
        Generate a comprehensive originality report for this {content_type} content:
        
        Content:
        {content}
        
        Plagiarism Analysis:
        {plagiarism_analysis}
        
        Include:
        1. Originality score and assessment
        2. Detailed analysis of findings
        3. Specific areas of concern
        4. Recommendations for improvement
        5. Best practices for original content
        6. Quality assurance guidelines
        
        Format as professional originality report.
        """
    
    def _create_originality_improvement_prompt(
        self, content: str, content_type: str, current_originality: float,
        target_originality: float, improvement_focus: List[str]
    ) -> str:
        """Create prompt for originality improvement"""
        return f"""
        Improve the originality of this {content_type} content:
        
        Content:
        {content}
        
        Current Originality: {current_originality}
        Target Originality: {target_originality}
        Improvement Focus: {', '.join(improvement_focus)}
        
        Requirements:
        - Increase originality while maintaining quality
        - Apply specified improvement focus areas
        - Preserve original message and intent
        - Add unique insights and perspectives
        - Rewrite common phrases and expressions
        - Restructure content for better originality
        - Maintain readability and engagement
        
        Generate the improved content.
        """
    
    def _calculate_reading_time(self, content: str) -> int:
        """Calculate estimated reading time in minutes"""
        words = len(content.split())
        words_per_minute = 200
        reading_time = max(1, round(words / words_per_minute))
        return reading_time
