import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, func
from datetime import datetime, timedelta
from backend.core.ai import get_ai_service_manager, AIServiceManager
from backend.core.integrations.integration_manager import IntegrationManager
from backend.core.event_bus.kafka_manager import EventBus
from ..database import get_shakes_database
from ..models import ContentProject, ContentPiece, ContentAnalytics

logger = logging.getLogger(__name__)

class ContentDNAService:
    """Service for content DNA analysis and optimization"""
    
    def __init__(self):
        self.integration_manager = IntegrationManager()
        self.event_bus = EventBus()
        self._initialized = False
        self.model_config = {
            "model": "grok-llm",
            "max_tokens": 3000,
            "temperature": 0.4
        }
    
    async def initialize(self):
        """Initialize content DNA service"""
        if self._initialized:
            return
        
        try:
            await self.integration_manager.initialize()
            await self.event_bus.initialize()
            self._initialized = True
            logger.info("Content DNA service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize content DNA service: {e}")
            raise
    
    async def analyze_content_dna(
        self,
        user_id: int,
        analysis_scope: str = "all",
        time_period_days: int = 90
    ) -> Dict[str, Any]:
        """Analyze content DNA for user's content portfolio"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_shakes_database()
            async with db.get_session() as session:
                # Get user's content pieces
                end_date = datetime.utcnow()
                start_date = end_date - timedelta(days=time_period_days)
                
                content_query = select(ContentPiece).join(ContentProject).where(
                    and_(
                        ContentProject.user_id == user_id,
                        ContentPiece.created_at >= start_date,
                        ContentPiece.created_at <= end_date
                    )
                )
                content_result = await session.execute(content_query)
                content_pieces = content_result.scalars().all()
                
                if not content_pieces:
                    return {"success": False, "error": "No content found for analysis"}
                
                # Get analytics for content pieces
                content_piece_ids = [piece.id for piece in content_pieces]
                analytics_result = await session.execute(
                    select(ContentAnalytics).where(ContentAnalytics.content_piece_id.in_(content_piece_ids))
                )
                analytics_records = analytics_result.scalars().all()
                
                # Analyze content DNA patterns
                dna_analysis = await self._analyze_content_patterns(
                    content_pieces, analytics_records
                )
                
                # Generate content DNA insights
                insights_prompt = self._create_dna_insights_prompt(
                    user_id, content_pieces, analytics_records, dna_analysis
                )
                # Use AI Service Manager instead of NLPUtils
                ai_manager = await get_ai_service_manager()
                messages = [{"role": "system", "content": "You are an AI assistant that analyzes content DNA and provides insights."}, {"role": "user", "content": insights_prompt}]
                ai_response = await ai_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.4)
                dna_insights = ai_response.text_content if ai_response.success else ""
                
                # Generate optimization recommendations
                optimization_prompt = self._create_dna_optimization_prompt(
                    dna_analysis, dna_insights
                )
                messages = [{"role": "system", "content": "You are an AI assistant that optimizes content based on DNA analysis."}, {"role": "user", "content": optimization_prompt}]
                ai_response = await ai_manager.generate_text(messages=messages, max_tokens=1500, temperature=0.4)
                dna_optimization = ai_response.text_content if ai_response.success else ""
                
                return {
                    "success": True,
                    "user_id": user_id,
                    "analysis_scope": analysis_scope,
                    "time_period_days": time_period_days,
                    "content_pieces_analyzed": len(content_pieces),
                    "dna_analysis": dna_analysis,
                    "dna_insights": dna_insights,
                    "dna_optimization": dna_optimization,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Content DNA analysis failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def generate_content_heatmap(
        self,
        user_id: int,
        heatmap_type: str = "performance",
        time_period_days: int = 30
    ) -> Dict[str, Any]:
        """Generate content performance heatmap"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_shakes_database()
            async with db.get_session() as session:
                # Get user's content and analytics
                end_date = datetime.utcnow()
                start_date = end_date - timedelta(days=time_period_days)
                
                content_query = select(ContentPiece).join(ContentProject).where(
                    and_(
                        ContentProject.user_id == user_id,
                        ContentPiece.created_at >= start_date,
                        ContentPiece.created_at <= end_date
                    )
                )
                content_result = await session.execute(content_query)
                content_pieces = content_result.scalars().all()
                
                content_piece_ids = [piece.id for piece in content_pieces]
                analytics_result = await session.execute(
                    select(ContentAnalytics).where(ContentAnalytics.content_piece_id.in_(content_piece_ids))
                )
                analytics_records = analytics_result.scalars().all()
                
                # Generate heatmap data
                heatmap_data = await self._generate_heatmap_data(
                    content_pieces, analytics_records, heatmap_type
                )
                
                # Generate heatmap insights
                insights_prompt = self._create_heatmap_insights_prompt(
                    heatmap_data, heatmap_type, time_period_days
                )
                # Use AI Service Manager instead of NLPUtils
                ai_manager = await get_ai_service_manager()
                messages = [{"role": "system", "content": "You are an AI assistant that analyzes content heatmaps and provides insights."}, {"role": "user", "content": insights_prompt}]
                ai_response = await ai_manager.generate_text(messages=messages, max_tokens=1500, temperature=0.7)
                heatmap_insights = ai_response.text_content if ai_response.success else ""
                
                return {
                    "success": True,
                    "user_id": user_id,
                    "heatmap_type": heatmap_type,
                    "time_period_days": time_period_days,
                    "heatmap_data": heatmap_data,
                    "heatmap_insights": heatmap_insights,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Content heatmap generation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def identify_content_patterns(
        self,
        user_id: int,
        pattern_types: List[str] = None
    ) -> Dict[str, Any]:
        """Identify patterns in user's content"""
        if not self._initialized:
            await self.initialize()
        
        if pattern_types is None:
            pattern_types = ["themes", "tone", "format", "timing", "performance"]
        
        try:
            db = await get_shakes_database()
            async with db.get_session() as session:
                # Get user's content
                content_query = select(ContentPiece).join(ContentProject).where(
                    ContentProject.user_id == user_id
                )
                content_result = await session.execute(content_query)
                content_pieces = content_result.scalars().all()
                
                if not content_pieces:
                    return {"success": False, "error": "No content found for pattern analysis"}
                
                # Get analytics
                content_piece_ids = [piece.id for piece in content_pieces]
                analytics_result = await session.execute(
                    select(ContentAnalytics).where(ContentAnalytics.content_piece_id.in_(content_piece_ids))
                )
                analytics_records = analytics_result.scalars().all()
                
                # Identify patterns
                identified_patterns = {}
                for pattern_type in pattern_types:
                    pattern_analysis = await self._identify_specific_patterns(
                        content_pieces, analytics_records, pattern_type
                    )
                    identified_patterns[pattern_type] = pattern_analysis
                
                # Generate pattern insights
                insights_prompt = self._create_pattern_insights_prompt(
                    identified_patterns, pattern_types
                )
                # Use AI Service Manager instead of NLPUtils
                ai_manager = await get_ai_service_manager()
                messages = [{"role": "system", "content": "You are an AI assistant that identifies content patterns and provides insights."}, {"role": "user", "content": insights_prompt}]
                ai_response = await ai_manager.generate_text(messages=messages, max_tokens=1500, temperature=0.7)
                pattern_insights = ai_response.text_content if ai_response.success else ""
                
                return {
                    "success": True,
                    "user_id": user_id,
                    "pattern_types": pattern_types,
                    "identified_patterns": identified_patterns,
                    "pattern_insights": pattern_insights,
                    "total_content_analyzed": len(content_pieces),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Content pattern identification failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def optimize_content_dna(
        self,
        user_id: int,
        optimization_goals: List[str],
        target_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Optimize content DNA based on goals and metrics"""
        if not self._initialized:
            await self.initialize()
        
        try:
            db = await get_shakes_database()
            async with db.get_session() as session:
                # Get user's content and analytics
                content_query = select(ContentPiece).join(ContentProject).where(
                    ContentProject.user_id == user_id
                )
                content_result = await session.execute(content_query)
                content_pieces = content_result.scalars().all()
                
                content_piece_ids = [piece.id for piece in content_pieces]
                analytics_result = await session.execute(
                    select(ContentAnalytics).where(ContentAnalytics.content_piece_id.in_(content_piece_ids))
                )
                analytics_records = analytics_result.scalars().all()
                
                # Analyze current DNA
                current_dna = await self._analyze_content_patterns(
                    content_pieces, analytics_records
                )
                
                # Generate optimization strategy
                optimization_prompt = self._create_dna_optimization_strategy_prompt(
                    current_dna, optimization_goals, target_metrics
                )
                # Use AI Service Manager instead of NLPUtils
                ai_manager = await get_ai_service_manager()
                messages = [{"role": "system", "content": "You are an AI assistant that creates content optimization strategies."}, {"role": "user", "content": optimization_prompt}]
                ai_response = await ai_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.4)
                optimization_strategy = ai_response.text_content if ai_response.success else ""
                
                # Generate specific recommendations
                recommendations_prompt = self._create_dna_recommendations_prompt(
                    current_dna, optimization_goals, target_metrics, optimization_strategy
                )
                messages = [{"role": "system", "content": "You are an AI assistant that provides content DNA-based recommendations."}, {"role": "user", "content": recommendations_prompt}]
                ai_response = await ai_manager.generate_text(messages=messages, max_tokens=1500, temperature=0.4)
                dna_recommendations = ai_response.text_content if ai_response.success else ""
                
                return {
                    "success": True,
                    "user_id": user_id,
                    "optimization_goals": optimization_goals,
                    "target_metrics": target_metrics,
                    "current_dna": current_dna,
                    "optimization_strategy": optimization_strategy,
                    "dna_recommendations": dna_recommendations,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Content DNA optimization failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _analyze_content_patterns(
        self, content_pieces: List[ContentPiece], analytics_records: List[ContentAnalytics]
    ) -> Dict[str, Any]:
        """Analyze patterns in content pieces and analytics"""
        # Analyze content themes
        themes = {}
        for piece in content_pieces:
            # Extract themes from content (simplified)
            content_words = piece.content.lower().split()
            for word in content_words:
                if len(word) > 4:  # Filter short words
                    themes[word] = themes.get(word, 0) + 1
        
        # Analyze performance patterns
        performance_by_type = {}
        performance_by_platform = {}
        
        for analytics in analytics_records:
            content_piece = next((p for p in content_pieces if p.id == analytics.content_piece_id), None)
            if content_piece:
                # By content type
                if content_piece.content_type not in performance_by_type:
                    performance_by_type[content_piece.content_type] = []
                performance_by_type[content_piece.content_type].append(analytics.engagement_rate)
                
                # By platform
                if analytics.platform not in performance_by_platform:
                    performance_by_platform[analytics.platform] = []
                performance_by_platform[analytics.platform].append(analytics.engagement_rate)
        
        # Calculate averages
        for content_type in performance_by_type:
            performance_by_type[content_type] = sum(performance_by_type[content_type]) / len(performance_by_type[content_type])
        
        for platform in performance_by_platform:
            performance_by_platform[platform] = sum(performance_by_platform[platform]) / len(performance_by_platform[platform])
        
        return {
            "content_themes": dict(sorted(themes.items(), key=lambda x: x[1], reverse=True)[:20]),
            "performance_by_type": performance_by_type,
            "performance_by_platform": performance_by_platform,
            "total_content_pieces": len(content_pieces),
            "total_analytics_records": len(analytics_records)
        }
    
    async def _generate_heatmap_data(
        self, content_pieces: List[ContentPiece], analytics_records: List[ContentAnalytics], heatmap_type: str
    ) -> Dict[str, Any]:
        """Generate heatmap data based on type"""
        heatmap_data = {}
        
        if heatmap_type == "performance":
            # Performance heatmap by day of week and hour
            for analytics in analytics_records:
                content_piece = next((p for p in content_pieces if p.id == analytics.content_piece_id), None)
                if content_piece:
                    day_of_week = content_piece.created_at.weekday()
                    hour = content_piece.created_at.hour
                    
                    key = f"{day_of_week}_{hour}"
                    if key not in heatmap_data:
                        heatmap_data[key] = []
                    heatmap_data[key].append(analytics.engagement_rate)
        
        elif heatmap_type == "themes":
            # Theme heatmap
            for piece in content_pieces:
                # Extract themes (simplified)
                content_words = piece.content.lower().split()
                for word in content_words:
                    if len(word) > 4:
                        if word not in heatmap_data:
                            heatmap_data[word] = 0
                        heatmap_data[word] += 1
        
        # Calculate averages for performance heatmap
        if heatmap_type == "performance":
            for key in heatmap_data:
                heatmap_data[key] = sum(heatmap_data[key]) / len(heatmap_data[key])
        
        return heatmap_data
    
    async def _identify_specific_patterns(
        self, content_pieces: List[ContentPiece], analytics_records: List[ContentAnalytics], pattern_type: str
    ) -> Dict[str, Any]:
        """Identify specific patterns based on type"""
        if pattern_type == "themes":
            themes = {}
            for piece in content_pieces:
                content_words = piece.content.lower().split()
                for word in content_words:
                    if len(word) > 4:
                        themes[word] = themes.get(word, 0) + 1
            return {"themes": dict(sorted(themes.items(), key=lambda x: x[1], reverse=True)[:10])}
        
        elif pattern_type == "tone":
            # Analyze tone patterns (simplified)
            tone_patterns = {}
            for piece in content_pieces:
                # Simple tone analysis based on keywords
                content_lower = piece.content.lower()
                if "!" in content_lower:
                    tone_patterns["excited"] = tone_patterns.get("excited", 0) + 1
                if "?" in content_lower:
                    tone_patterns["questioning"] = tone_patterns.get("questioning", 0) + 1
                if len(piece.content.split()) > 100:
                    tone_patterns["detailed"] = tone_patterns.get("detailed", 0) + 1
            return {"tone_patterns": tone_patterns}
        
        elif pattern_type == "format":
            format_patterns = {}
            for piece in content_pieces:
                format_patterns[piece.content_type] = format_patterns.get(piece.content_type, 0) + 1
            return {"format_patterns": format_patterns}
        
        elif pattern_type == "timing":
            timing_patterns = {}
            for piece in content_pieces:
                hour = piece.created_at.hour
                timing_patterns[hour] = timing_patterns.get(hour, 0) + 1
            return {"timing_patterns": timing_patterns}
        
        elif pattern_type == "performance":
            performance_patterns = {}
            for analytics in analytics_records:
                content_piece = next((p for p in content_pieces if p.id == analytics.content_piece_id), None)
                if content_piece:
                    if content_piece.content_type not in performance_patterns:
                        performance_patterns[content_piece.content_type] = []
                    performance_patterns[content_piece.content_type].append(analytics.engagement_rate)
            
            # Calculate averages
            for content_type in performance_patterns:
                performance_patterns[content_type] = sum(performance_patterns[content_type]) / len(performance_patterns[content_type])
            
            return {"performance_patterns": performance_patterns}
        
        return {}
    
    def _create_dna_insights_prompt(
        self, user_id: int, content_pieces: List[ContentPiece], analytics_records: List[ContentAnalytics], dna_analysis: Dict[str, Any]
    ) -> str:
        """Create prompt for DNA insights"""
        return f"""
        Analyze the content DNA for user {user_id}:
        
        Content Pieces: {len(content_pieces)}
        Analytics Records: {len(analytics_records)}
        
        DNA Analysis: {dna_analysis}
        
        Provide:
        1. Key content DNA characteristics
        2. Performance patterns and trends
        3. Content strengths and weaknesses
        4. Audience engagement insights
        5. Content optimization opportunities
        6. Brand voice and style analysis
        
        Format as comprehensive content DNA insights.
        """
    
    def _create_dna_optimization_prompt(
        self, dna_analysis: Dict[str, Any], dna_insights: str
    ) -> str:
        """Create prompt for DNA optimization"""
        return f"""
        Provide optimization recommendations based on content DNA analysis:
        
        DNA Analysis: {dna_analysis}
        DNA Insights: {dna_insights}
        
        Provide:
        1. Content strategy improvements
        2. Performance optimization tactics
        3. Audience engagement enhancements
        4. Content format recommendations
        5. Timing and frequency optimizations
        6. Brand voice refinements
        
        Format as actionable optimization recommendations.
        """
    
    def _create_heatmap_insights_prompt(
        self, heatmap_data: Dict[str, Any], heatmap_type: str, time_period_days: int
    ) -> str:
        """Create prompt for heatmap insights"""
        return f"""
        Analyze the content heatmap data:
        
        Heatmap Type: {heatmap_type}
        Time Period: {time_period_days} days
        Heatmap Data: {heatmap_data}
        
        Provide:
        1. Key patterns and trends
        2. Performance hotspots
        3. Optimization opportunities
        4. Timing recommendations
        5. Content strategy insights
        6. Actionable recommendations
        
        Format as comprehensive heatmap insights.
        """
    
    def _create_pattern_insights_prompt(
        self, identified_patterns: Dict[str, Any], pattern_types: List[str]
    ) -> str:
        """Create prompt for pattern insights"""
        return f"""
        Analyze the identified content patterns:
        
        Pattern Types: {', '.join(pattern_types)}
        Identified Patterns: {identified_patterns}
        
        Provide:
        1. Pattern significance and implications
        2. Content strategy insights
        3. Performance optimization opportunities
        4. Audience behavior analysis
        5. Content creation recommendations
        6. Trend identification and forecasting
        
        Format as comprehensive pattern insights.
        """
    
    def _create_dna_optimization_strategy_prompt(
        self, current_dna: Dict[str, Any], optimization_goals: List[str], target_metrics: Dict[str, Any]
    ) -> str:
        """Create prompt for DNA optimization strategy"""
        return f"""
        Create content DNA optimization strategy:
        
        Current DNA: {current_dna}
        Optimization Goals: {', '.join(optimization_goals)}
        Target Metrics: {target_metrics}
        
        Provide:
        1. Optimization strategy overview
        2. Content modification recommendations
        3. Performance improvement tactics
        4. Audience engagement strategies
        5. Content creation guidelines
        6. Success metrics and KPIs
        
        Format as comprehensive optimization strategy.
        """
    
    def _create_dna_recommendations_prompt(
        self, current_dna: Dict[str, Any], optimization_goals: List[str], target_metrics: Dict[str, Any], optimization_strategy: str
    ) -> str:
        """Create prompt for DNA recommendations"""
        return f"""
        Provide specific content DNA recommendations:
        
        Current DNA: {current_dna}
        Optimization Goals: {', '.join(optimization_goals)}
        Target Metrics: {target_metrics}
        Optimization Strategy: {optimization_strategy}
        
        Provide:
        1. Specific content modifications
        2. Performance improvement actions
        3. Audience targeting adjustments
        4. Content format optimizations
        5. Timing and frequency changes
        6. Implementation timeline
        
        Format as actionable DNA recommendations.
        """
