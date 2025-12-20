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

class StoryboardGeneratorService:
    """Service for AI-powered storyboard generation"""
    
    def __init__(self):
        self.integration_manager = IntegrationManager()
        self.event_bus = EventBus()
        self._initialized = False
    
    async def initialize(self):
        """Initialize storyboard generator service"""
        if self._initialized:
            return
        
        try:
            await self.integration_manager.initialize()
            await self.event_bus.initialize()
            self._initialized = True
            logger.info("Storyboard generator service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize storyboard generator service: {e}")
            raise
    
    async def generate_storyboard(
        self,
        content_piece_id: int,
        storyboard_type: str,
        visual_style: str,
        duration_minutes: int = 2,
        scene_count: int = 8
    ) -> Dict[str, Any]:
        """Generate AI-powered storyboard for content"""
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
                
                # Generate storyboard structure
                storyboard_structure = await self._generate_storyboard_structure(
                    content_piece, storyboard_type, duration_minutes, scene_count
                )
                
                # Generate visual descriptions
                visual_descriptions = await self._generate_visual_descriptions(
                    content_piece, storyboard_structure, visual_style
                )
                
                # Generate scene transitions
                scene_transitions = await self._generate_scene_transitions(
                    storyboard_structure, visual_descriptions
                )
                
                # Generate storyboard script
                storyboard_script = await self._generate_storyboard_script(
                    content_piece, storyboard_structure, visual_descriptions, scene_transitions
                )
                
                # Generate production notes
                production_notes = await self._generate_production_notes(
                    storyboard_structure, visual_descriptions, scene_transitions
                )
                
                return {
                    "success": True,
                    "content_piece_id": content_piece_id,
                    "storyboard_type": storyboard_type,
                    "visual_style": visual_style,
                    "duration_minutes": duration_minutes,
                    "scene_count": scene_count,
                    "storyboard_structure": storyboard_structure,
                    "visual_descriptions": visual_descriptions,
                    "scene_transitions": scene_transitions,
                    "storyboard_script": storyboard_script,
                    "production_notes": production_notes,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Storyboard generation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def generate_video_storyboard(
        self,
        content_piece_id: int,
        video_format: str,
        target_audience: str,
        video_goals: List[str]
    ) -> Dict[str, Any]:
        """Generate storyboard specifically for video content"""
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
                
                # Generate video storyboard
                video_storyboard = await self._generate_video_storyboard(
                    content_piece, video_format, target_audience, video_goals
                )
                
                # Generate shot list
                shot_list = await self._generate_shot_list(
                    video_storyboard, video_format
                )
                
                # Generate timing breakdown
                timing_breakdown = await self._generate_timing_breakdown(
                    video_storyboard, shot_list
                )
                
                # Generate technical specifications
                technical_specs = await self._generate_technical_specifications(
                    video_format, target_audience, video_goals
                )
                
                return {
                    "success": True,
                    "content_piece_id": content_piece_id,
                    "video_format": video_format,
                    "target_audience": target_audience,
                    "video_goals": video_goals,
                    "video_storyboard": video_storyboard,
                    "shot_list": shot_list,
                    "timing_breakdown": timing_breakdown,
                    "technical_specifications": technical_specs,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Video storyboard generation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def generate_campaign_storyboard(
        self,
        campaign_concept: str,
        campaign_goals: List[str],
        target_audience: str,
        campaign_duration_days: int,
        content_variations: int = 3
    ) -> Dict[str, Any]:
        """Generate storyboard for marketing campaign"""
        if not self._initialized:
            await self.initialize()
        
        try:
            # Generate campaign storyboard
            campaign_storyboard = await self._generate_campaign_storyboard(
                campaign_concept, campaign_goals, target_audience, campaign_duration_days
            )
            
            # Generate content variations
            content_variations_list = await self._generate_content_variations(
                campaign_storyboard, content_variations
            )
            
            # Generate campaign timeline
            campaign_timeline = await self._generate_campaign_timeline(
                campaign_storyboard, campaign_duration_days
            )
            
            # Generate platform adaptations
            platform_adaptations = await self._generate_platform_adaptations(
                campaign_storyboard, content_variations_list
            )
            
            return {
                "success": True,
                "campaign_concept": campaign_concept,
                "campaign_goals": campaign_goals,
                "target_audience": target_audience,
                "campaign_duration_days": campaign_duration_days,
                "content_variations": content_variations,
                "campaign_storyboard": campaign_storyboard,
                "content_variations_list": content_variations_list,
                "campaign_timeline": campaign_timeline,
                "platform_adaptations": platform_adaptations,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Campaign storyboard generation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def optimize_storyboard(
        self,
        storyboard_data: Dict[str, Any],
        optimization_goals: List[str],
        constraints: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Optimize existing storyboard based on goals and constraints"""
        if not self._initialized:
            await self.initialize()
        
        try:
            # Analyze current storyboard
            storyboard_analysis = await self._analyze_storyboard(
                storyboard_data, optimization_goals, constraints
            )
            
            # Generate optimization recommendations
            optimization_recommendations = await self._generate_optimization_recommendations(
                storyboard_analysis, optimization_goals, constraints
            )
            
            # Generate optimized storyboard
            optimized_storyboard = await self._generate_optimized_storyboard(
                storyboard_data, optimization_recommendations, constraints
            )
            
            # Generate optimization report
            optimization_report = await self._generate_optimization_report(
                storyboard_analysis, optimization_recommendations, optimized_storyboard
            )
            
            return {
                "success": True,
                "original_storyboard": storyboard_data,
                "optimization_goals": optimization_goals,
                "constraints": constraints,
                "storyboard_analysis": storyboard_analysis,
                "optimization_recommendations": optimization_recommendations,
                "optimized_storyboard": optimized_storyboard,
                "optimization_report": optimization_report,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Storyboard optimization failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _generate_storyboard_structure(
        self, content_piece: ContentPiece, storyboard_type: str, duration_minutes: int, scene_count: int
    ) -> List[Dict[str, Any]]:
        """Generate storyboard structure"""
        structure_prompt = self._create_structure_prompt(
            content_piece, storyboard_type, duration_minutes, scene_count
        )
        # Use AI Service Manager instead of NLPUtils
        ai_manager = await get_ai_service_manager()
        messages = [{"role": "system", "content": "You are an AI assistant that creates storyboard structures."}, {"role": "user", "content": structure_prompt}]
        ai_response = await ai_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
        structure_result = ai_response.text_content if ai_response.success else ""
        
        # Parse structure result into scenes
        scenes = []
        for i in range(scene_count):
            scenes.append({
                "scene_number": i + 1,
                "duration_seconds": (duration_minutes * 60) // scene_count,
                "description": f"Scene {i + 1} description",
                "key_elements": [],
                "visual_focus": "",
                "audio_notes": ""
            })
        
        return scenes
    
    async def _generate_visual_descriptions(
        self, content_piece: ContentPiece, storyboard_structure: List[Dict[str, Any]], visual_style: str
    ) -> List[Dict[str, Any]]:
        """Generate visual descriptions for each scene"""
        visual_descriptions = []
        
        for scene in storyboard_structure:
            visual_prompt = self._create_visual_prompt(
                content_piece, scene, visual_style
            )
            # Use AI Service Manager instead of NLPUtils
            ai_manager = await get_ai_service_manager()
            messages = [{"role": "system", "content": "You are an AI assistant that creates visual descriptions for storyboards."}, {"role": "user", "content": visual_prompt}]
            ai_response = await ai_manager.generate_text(messages=messages, max_tokens=500, temperature=0.7)
            visual_result = ai_response.text_content if ai_response.success else ""
            
            visual_descriptions.append({
                "scene_number": scene["scene_number"],
                "visual_description": visual_result,
                "camera_angles": [],
                "lighting": "",
                "color_palette": "",
                "composition": ""
            })
        
        return visual_descriptions
    
    async def _generate_scene_transitions(
        self, storyboard_structure: List[Dict[str, Any]], visual_descriptions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate scene transitions"""
        transitions = []
        
        for i in range(len(storyboard_structure) - 1):
            current_scene = storyboard_structure[i]
            next_scene = storyboard_structure[i + 1]
            
            transition_prompt = self._create_transition_prompt(
                current_scene, next_scene, visual_descriptions[i], visual_descriptions[i + 1]
            )
            # Use AI Service Manager instead of NLPUtils
            ai_manager = await get_ai_service_manager()
            messages = [{"role": "system", "content": "You are an AI assistant that creates transitions for storyboards."}, {"role": "user", "content": transition_prompt}]
            ai_response = await ai_manager.generate_text(messages=messages, max_tokens=300, temperature=0.7)
            transition_result = ai_response.text_content if ai_response.success else ""
            
            transitions.append({
                "from_scene": current_scene["scene_number"],
                "to_scene": next_scene["scene_number"],
                "transition_type": "cut",
                "transition_description": transition_result,
                "duration_seconds": 1
            })
        
        return transitions
    
    async def _generate_storyboard_script(
        self, content_piece: ContentPiece, storyboard_structure: List[Dict[str, Any]], 
        visual_descriptions: List[Dict[str, Any]], scene_transitions: List[Dict[str, Any]]
    ) -> str:
        """Generate complete storyboard script"""
        script_prompt = self._create_script_prompt(
            content_piece, storyboard_structure, visual_descriptions, scene_transitions
        )
        # Use AI Service Manager instead of NLPUtils
        ai_manager = await get_ai_service_manager()
        messages = [{"role": "system", "content": "You are an AI assistant that creates storyboard scripts."}, {"role": "user", "content": script_prompt}]
        ai_response = await ai_manager.generate_text(messages=messages, max_tokens=1000, temperature=0.7)
        script_result = ai_response.text_content if ai_response.success else ""
        return script_result
    
    async def _generate_production_notes(
        self, storyboard_structure: List[Dict[str, Any]], visual_descriptions: List[Dict[str, Any]], scene_transitions: List[Dict[str, Any]]
    ) -> str:
        """Generate production notes"""
        notes_prompt = self._create_notes_prompt(
            storyboard_structure, visual_descriptions, scene_transitions
        )
        # Use AI Service Manager instead of NLPUtils
        ai_manager = await get_ai_service_manager()
        messages = [{"role": "system", "content": "You are an AI assistant that creates production notes for storyboards."}, {"role": "user", "content": notes_prompt}]
        ai_response = await ai_manager.generate_text(messages=messages, max_tokens=1000, temperature=0.7)
        notes_result = ai_response.text_content if ai_response.success else ""
        return notes_result
    
    async def _generate_video_storyboard(
        self, content_piece: ContentPiece, video_format: str, target_audience: str, video_goals: List[str]
    ) -> List[Dict[str, Any]]:
        """Generate video-specific storyboard"""
        video_prompt = self._create_video_prompt(
            content_piece, video_format, target_audience, video_goals
        )
        # Use AI Service Manager instead of NLPUtils
        ai_manager = await get_ai_service_manager()
        messages = [{"role": "system", "content": "You are an AI assistant that creates video storyboards."}, {"role": "user", "content": video_prompt}]
        ai_response = await ai_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.7)
        video_result = ai_response.text_content if ai_response.success else ""
        
        # Parse into video storyboard format
        return [
            {
                "shot_number": 1,
                "shot_type": "wide",
                "description": "Opening shot",
                "duration_seconds": 3,
                "camera_movement": "static",
                "audio": "background_music"
            }
        ]
    
    async def _generate_shot_list(
        self, video_storyboard: List[Dict[str, Any]], video_format: str
    ) -> List[Dict[str, Any]]:
        """Generate detailed shot list"""
        shot_list = []
        
        for shot in video_storyboard:
            shot_list.append({
                "shot_number": shot["shot_number"],
                "shot_type": shot["shot_type"],
                "description": shot["description"],
                "duration_seconds": shot["duration_seconds"],
                "camera_movement": shot["camera_movement"],
                "audio": shot["audio"],
                "equipment_needed": [],
                "location_notes": "",
                "talent_notes": ""
            })
        
        return shot_list
    
    async def _generate_timing_breakdown(
        self, video_storyboard: List[Dict[str, Any]], shot_list: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate timing breakdown"""
        total_duration = sum(shot["duration_seconds"] for shot in shot_list)
        
        return {
            "total_duration_seconds": total_duration,
            "total_duration_minutes": total_duration / 60,
            "shot_count": len(shot_list),
            "average_shot_duration": total_duration / len(shot_list) if shot_list else 0,
            "timing_breakdown": shot_list
        }
    
    async def _generate_technical_specifications(
        self, video_format: str, target_audience: str, video_goals: List[str]
    ) -> Dict[str, Any]:
        """Generate technical specifications"""
        return {
            "video_format": video_format,
            "resolution": "1920x1080",
            "frame_rate": "30fps",
            "aspect_ratio": "16:9",
            "audio_format": "stereo",
            "target_audience": target_audience,
            "video_goals": video_goals,
            "technical_requirements": [],
            "equipment_recommendations": []
        }
    
    async def _generate_campaign_storyboard(
        self, campaign_concept: str, campaign_goals: List[str], target_audience: str, campaign_duration_days: int
    ) -> List[Dict[str, Any]]:
        """Generate campaign storyboard"""
        campaign_prompt = self._create_campaign_prompt(
            campaign_concept, campaign_goals, target_audience, campaign_duration_days
        )
        # Use AI Service Manager instead of NLPUtils
        ai_manager = await get_ai_service_manager()
        messages = [{"role": "system", "content": "You are an AI assistant that creates storyboard campaigns."}, {"role": "user", "content": campaign_prompt}]
        ai_response = await ai_manager.generate_text(messages=messages, max_tokens=1500, temperature=0.7)
        campaign_result = ai_response.text_content if ai_response.success else ""
        
        return [
            {
                "phase": "launch",
                "duration_days": campaign_duration_days // 3,
                "content_focus": "awareness",
                "key_messages": [],
                "visual_style": "bold",
                "call_to_action": "learn_more"
            }
        ]
    
    async def _generate_content_variations(
        self, campaign_storyboard: List[Dict[str, Any]], content_variations: int
    ) -> List[Dict[str, Any]]:
        """Generate content variations"""
        variations = []
        
        for i in range(content_variations):
            variations.append({
                "variation_number": i + 1,
                "variation_type": "format",
                "description": f"Content variation {i + 1}",
                "target_platform": "social_media",
                "adaptations": []
            })
        
        return variations
    
    async def _generate_campaign_timeline(
        self, campaign_storyboard: List[Dict[str, Any]], campaign_duration_days: int
    ) -> List[Dict[str, Any]]:
        """Generate campaign timeline"""
        timeline = []
        
        for phase in campaign_storyboard:
            timeline.append({
                "phase": phase["phase"],
                "start_day": 1,
                "end_day": phase["duration_days"],
                "milestones": [],
                "deliverables": []
            })
        
        return timeline
    
    async def _generate_platform_adaptations(
        self, campaign_storyboard: List[Dict[str, Any]], content_variations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate platform adaptations"""
        return {
            "platform_adaptations": {
                "instagram": {"format": "square", "duration": "15s"},
                "facebook": {"format": "landscape", "duration": "30s"},
                "twitter": {"format": "square", "duration": "15s"},
                "youtube": {"format": "landscape", "duration": "60s"}
            }
        }
    
    async def _analyze_storyboard(
        self, storyboard_data: Dict[str, Any], optimization_goals: List[str], constraints: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze current storyboard"""
        analysis_prompt = self._create_analysis_prompt(
            storyboard_data, optimization_goals, constraints
        )
        # Use AI Service Manager instead of NLPUtils
        ai_manager = await get_ai_service_manager()
        messages = [{"role": "system", "content": "You are an AI assistant that analyzes storyboards."}, {"role": "user", "content": analysis_prompt}]
        ai_response = await ai_manager.generate_text(messages=messages, max_tokens=1000, temperature=0.7)
        analysis_result = ai_response.text_content if ai_response.success else ""
        
        return {
            "analysis_result": analysis_result,
            "strengths": [],
            "weaknesses": [],
            "optimization_opportunities": []
        }
    
    async def _generate_optimization_recommendations(
        self, storyboard_analysis: Dict[str, Any], optimization_goals: List[str], constraints: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate optimization recommendations"""
        recommendations_prompt = self._create_recommendations_prompt(
            storyboard_analysis, optimization_goals, constraints
        )
        # Use AI Service Manager instead of NLPUtils
        ai_manager = await get_ai_service_manager()
        messages = [{"role": "system", "content": "You are an AI assistant that provides storyboard recommendations."}, {"role": "user", "content": recommendations_prompt}]
        ai_response = await ai_manager.generate_text(messages=messages, max_tokens=800, temperature=0.7)
        recommendations_result = ai_response.text_content if ai_response.success else ""
        
        return [
            {
                "recommendation_type": "visual",
                "description": "Improve visual composition",
                "priority": "high",
                "implementation": "easy"
            }
        ]
    
    async def _generate_optimized_storyboard(
        self, storyboard_data: Dict[str, Any], optimization_recommendations: List[Dict[str, Any]], constraints: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate optimized storyboard"""
        optimized_prompt = self._create_optimized_prompt(
            storyboard_data, optimization_recommendations, constraints
        )
        # Use AI Service Manager instead of NLPUtils
        ai_manager = await get_ai_service_manager()
        messages = [{"role": "system", "content": "You are an AI assistant that optimizes storyboards."}, {"role": "user", "content": optimized_prompt}]
        ai_response = await ai_manager.generate_text(messages=messages, max_tokens=1500, temperature=0.7)
        optimized_result = ai_response.text_content if ai_response.success else ""
        
        return {
            "optimized_storyboard": optimized_result,
            "changes_made": [],
            "improvements": []
        }
    
    async def _generate_optimization_report(
        self, storyboard_analysis: Dict[str, Any], optimization_recommendations: List[Dict[str, Any]], optimized_storyboard: Dict[str, Any]
    ) -> str:
        """Generate optimization report"""
        report_prompt = self._create_report_prompt(
            storyboard_analysis, optimization_recommendations, optimized_storyboard
        )
        # Use AI Service Manager instead of NLPUtils
        ai_manager = await get_ai_service_manager()
        messages = [{"role": "system", "content": "You are an AI assistant that generates storyboard reports."}, {"role": "user", "content": report_prompt}]
        ai_response = await ai_manager.generate_text(messages=messages, max_tokens=1000, temperature=0.7)
        report_result = ai_response.text_content if ai_response.success else ""
        return report_result
    
    def _create_structure_prompt(
        self, content_piece: ContentPiece, storyboard_type: str, duration_minutes: int, scene_count: int
    ) -> str:
        """Create prompt for storyboard structure"""
        return f"""
        Create storyboard structure for this content:
        
        Content: {content_piece.title}
        Content Type: {content_piece.content_type}
        Content Text: {content_piece.content}
        Storyboard Type: {storyboard_type}
        Duration: {duration_minutes} minutes
        Scene Count: {scene_count}
        
        Create a logical flow of scenes that tells the story effectively.
        """
    
    def _create_visual_prompt(
        self, content_piece: ContentPiece, scene: Dict[str, Any], visual_style: str
    ) -> str:
        """Create prompt for visual descriptions"""
        return f"""
        Create visual description for this scene:
        
        Content: {content_piece.title}
        Scene: {scene}
        Visual Style: {visual_style}
        
        Provide detailed visual description including composition, lighting, and mood.
        """
    
    def _create_transition_prompt(
        self, current_scene: Dict[str, Any], next_scene: Dict[str, Any], 
        current_visual: Dict[str, Any], next_visual: Dict[str, Any]
    ) -> str:
        """Create prompt for scene transitions"""
        return f"""
        Create transition between these scenes:
        
        Current Scene: {current_scene}
        Next Scene: {next_scene}
        Current Visual: {current_visual}
        Next Visual: {next_visual}
        
        Provide smooth transition description.
        """
    
    def _create_script_prompt(
        self, content_piece: ContentPiece, storyboard_structure: List[Dict[str, Any]], 
        visual_descriptions: List[Dict[str, Any]], scene_transitions: List[Dict[str, Any]]
    ) -> str:
        """Create prompt for storyboard script"""
        return f"""
        Create complete storyboard script:
        
        Content: {content_piece.title}
        Structure: {storyboard_structure}
        Visual Descriptions: {visual_descriptions}
        Transitions: {scene_transitions}
        
        Create comprehensive storyboard script with all details.
        """
    
    def _create_notes_prompt(
        self, storyboard_structure: List[Dict[str, Any]], visual_descriptions: List[Dict[str, Any]], scene_transitions: List[Dict[str, Any]]
    ) -> str:
        """Create prompt for production notes"""
        return f"""
        Create production notes for this storyboard:
        
        Structure: {storyboard_structure}
        Visual Descriptions: {visual_descriptions}
        Transitions: {scene_transitions}
        
        Provide detailed production notes and requirements.
        """
    
    def _create_video_prompt(
        self, content_piece: ContentPiece, video_format: str, target_audience: str, video_goals: List[str]
    ) -> str:
        """Create prompt for video storyboard"""
        return f"""
        Create video storyboard for this content:
        
        Content: {content_piece.title}
        Video Format: {video_format}
        Target Audience: {target_audience}
        Video Goals: {', '.join(video_goals)}
        
        Create video-specific storyboard with shot details.
        """
    
    def _create_campaign_prompt(
        self, campaign_concept: str, campaign_goals: List[str], target_audience: str, campaign_duration_days: int
    ) -> str:
        """Create prompt for campaign storyboard"""
        return f"""
        Create campaign storyboard:
        
        Campaign Concept: {campaign_concept}
        Campaign Goals: {', '.join(campaign_goals)}
        Target Audience: {target_audience}
        Duration: {campaign_duration_days} days
        
        Create comprehensive campaign storyboard.
        """
    
    def _create_analysis_prompt(
        self, storyboard_data: Dict[str, Any], optimization_goals: List[str], constraints: Dict[str, Any]
    ) -> str:
        """Create prompt for storyboard analysis"""
        return f"""
        Analyze this storyboard:
        
        Storyboard Data: {storyboard_data}
        Optimization Goals: {', '.join(optimization_goals)}
        Constraints: {constraints}
        
        Provide detailed analysis of strengths, weaknesses, and opportunities.
        """
    
    def _create_recommendations_prompt(
        self, storyboard_analysis: Dict[str, Any], optimization_goals: List[str], constraints: Dict[str, Any]
    ) -> str:
        """Create prompt for optimization recommendations"""
        return f"""
        Provide optimization recommendations:
        
        Analysis: {storyboard_analysis}
        Goals: {', '.join(optimization_goals)}
        Constraints: {constraints}
        
        Provide specific, actionable recommendations.
        """
    
    def _create_optimized_prompt(
        self, storyboard_data: Dict[str, Any], optimization_recommendations: List[Dict[str, Any]], constraints: Dict[str, Any]
    ) -> str:
        """Create prompt for optimized storyboard"""
        return f"""
        Create optimized storyboard:
        
        Original: {storyboard_data}
        Recommendations: {optimization_recommendations}
        Constraints: {constraints}
        
        Create improved storyboard based on recommendations.
        """
    
    def _create_report_prompt(
        self, storyboard_analysis: Dict[str, Any], optimization_recommendations: List[Dict[str, Any]], optimized_storyboard: Dict[str, Any]
    ) -> str:
        """Create prompt for optimization report"""
        return f"""
        Create optimization report:
        
        Analysis: {storyboard_analysis}
        Recommendations: {optimization_recommendations}
        Optimized Storyboard: {optimized_storyboard}
        
        Create comprehensive optimization report.
        """
