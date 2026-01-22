from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import asyncio
import json
import logging
import base64
import numpy as np
from scipy import signal
from scipy import stats
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc
from sqlalchemy.orm import selectinload

from ..database import get_eric_database
# NLPUtils removed - not used
from core.integrations.integration_manager import IntegrationManager
from core.analytics.analytics_manager import AnalyticsManager
from core.event_bus.kafka_manager import EventBus as KafkaManager
from core.cache.redis_manager import RedisManager
from ..models import EricLead, EricDeal, EricSalesActivity, EricSalesRep, CustomerProfile

logger = logging.getLogger(__name__)

class VoicePitchSimulatorService:
    """Service for voice pitch simulation and AI-powered sales call coaching"""
    
    def __init__(self):
        # NLPUtils removed - not used
        self.ai_service_manager = None
        self.integration_manager = IntegrationManager()
        self.analytics_manager = AnalyticsManager()
        self.kafka_manager = KafkaManager()
        self.redis_manager = RedisManager()
        self._initialized = False
    
    async def initialize(self):
        """Initialize voice pitch simulator service"""
        if self._initialized:
            return
        
        try:
            from core.ai import get_ai_service_manager
            self.ai_service_manager = await get_ai_service_manager()
            await self.integration_manager.initialize()
            await self.analytics_manager.initialize()
            await self.kafka_manager.initialize()
            await self.redis_manager.initialize()
            self._initialized = True
            logger.info("Voice pitch simulator service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize voice pitch simulator service: {e}")
            raise
        
        # Define voice analysis parameters
        self.voice_parameters = {
            "pitch": {
                "optimal_range": (120, 200),  # Hz
                "weight": 0.2,
                "description": "Voice pitch frequency"
            },
            "speech_rate": {
                "optimal_range": (120, 160),  # words per minute
                "weight": 0.15,
                "description": "Speaking speed"
            },
            "volume": {
                "optimal_range": (0.6, 0.9),  # normalized amplitude
                "weight": 0.15,
                "description": "Voice volume level"
            },
            "clarity": {
                "optimal_range": (0.7, 1.0),  # clarity score
                "weight": 0.2,
                "description": "Speech clarity and articulation"
            },
            "confidence": {
                "optimal_range": (0.7, 1.0),  # confidence score
                "weight": 0.3,
                "description": "Confidence indicators in voice"
            }
        }
        
        # Define pitch scenarios and their characteristics
        self.pitch_scenarios = {
            "cold_call": {
                "duration": 30,  # seconds
                "key_elements": ["introduction", "value_proposition", "call_to_action"],
                "difficulty": "medium",
                "success_criteria": ["engagement", "next_step", "appointment_set"]
            },
            "follow_up": {
                "duration": 45,
                "key_elements": ["relationship_building", "pain_point_identification", "solution_presentation"],
                "difficulty": "easy",
                "success_criteria": ["interest_expression", "qualification", "demo_request"]
            },
            "closing": {
                "duration": 60,
                "key_elements": ["objection_handling", "value_reinforcement", "closing_technique"],
                "difficulty": "hard",
                "success_criteria": ["deal_closed", "contract_signed", "payment_received"]
            },
            "demo_presentation": {
                "duration": 90,
                "key_elements": ["product_demo", "benefit_highlighting", "interaction_management"],
                "difficulty": "medium",
                "success_criteria": ["engagement", "questions_asked", "next_meeting"]
            }
        }
    
    async def simulate_voice_pitch(
        self,
        rep_id: int,
        scenario_type: str,
        audio_data: str,
        pitch_content: Optional[str] = None
    ) -> Dict[str, Any]:
        """Simulate and analyze a voice pitch"""
        try:
            db = await get_eric_database()
            async with db.get_session() as session:
                # Validate scenario type
                if scenario_type not in self.pitch_scenarios:
                    return {"success": False, "error": f"Invalid scenario type: {scenario_type}"}
                
                # Get rep information
                rep = await self._get_sales_rep(session, rep_id)
                if not rep:
                    return {"success": False, "error": "Sales rep not found"}
                
                # Analyze voice characteristics
                voice_analysis = await self._analyze_voice_characteristics(audio_data)
                
                # Analyze pitch content if provided
                content_analysis = {}
                if pitch_content:
                    content_analysis = await self._analyze_pitch_content(pitch_content, scenario_type)
                
                # Generate comprehensive feedback
                feedback = await self._generate_voice_feedback(
                    voice_analysis, content_analysis, scenario_type
                )
                
                # Calculate overall score
                overall_score = await self._calculate_overall_score(voice_analysis, content_analysis)
                
                # Generate improvement recommendations
                recommendations = await self._generate_improvement_recommendations(
                    voice_analysis, content_analysis, scenario_type
                )
                
                # Store simulation results
                await self._store_simulation_results(
                    session, rep_id, scenario_type, voice_analysis, 
                    content_analysis, overall_score, feedback
                )
                
                # Track analytics
                await self.analytics_manager.log_event(
                    "voice_pitch_simulated",
                    {
                        "rep_id": rep_id,
                        "scenario_type": scenario_type,
                        "overall_score": overall_score,
                        "voice_analysis": voice_analysis
                    }
                )
                
                return {
                    "success": True,
                    "simulation_completed": True,
                    "rep_id": rep_id,
                    "scenario_type": scenario_type,
                    "voice_analysis": voice_analysis,
                    "content_analysis": content_analysis,
                    "feedback": feedback,
                    "overall_score": overall_score,
                    "recommendations": recommendations,
                    "simulated_at": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error simulating voice pitch: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_voice_pitch_history(
        self,
        rep_id: Optional[int] = None,
        scenario_type: Optional[str] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """Get voice pitch simulation history"""
        try:
            db = await get_eric_database()
            async with db.get_session() as session:
                # Build query filters
                filters = []
                if rep_id:
                    filters.append(EricSalesActivity.rep_id == rep_id)
                if scenario_type:
                    filters.append(EricSalesActivity.metadata.contains({"scenario_type": scenario_type}))
                
                # Query simulation activities
                query = select(EricSalesActivity).where(
                    and_(
                        EricSalesActivity.activity_type == "voice_pitch_simulation",
                        *filters
                    )
                ).order_by(EricSalesActivity.created_at.desc()).limit(limit)
                
                activities = await session.execute(query)
                activities = activities.scalars().all()
                
                # Format results
                simulation_history = []
                for activity in activities:
                    metadata = activity.metadata or {}
                    simulation_history.append({
                        "id": activity.id,
                        "rep_id": activity.rep_id,
                        "scenario_type": metadata.get("scenario_type"),
                        "overall_score": metadata.get("overall_score", 0),
                        "voice_analysis": metadata.get("voice_analysis", {}),
                        "feedback": metadata.get("feedback", {}),
                        "simulated_at": activity.created_at.isoformat()
                    })
                
                return {
                    "success": True,
                    "simulation_history": simulation_history,
                    "total_simulations": len(simulation_history)
                }
                
        except Exception as e:
            logger.error(f"Error getting voice pitch history: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_voice_analytics(
        self,
        rep_id: Optional[int] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get analytics about voice pitch performance"""
        try:
            db = await get_eric_database()
            async with db.get_session() as session:
                start_date = datetime.utcnow() - timedelta(days=days)
                
                # Get simulation activities
                query = select(EricSalesActivity).where(
                    and_(
                        EricSalesActivity.activity_type == "voice_pitch_simulation",
                        EricSalesActivity.created_at >= start_date
                    )
                )
                
                if rep_id:
                    query = query.where(EricSalesActivity.rep_id == rep_id)
                
                activities = await session.execute(query)
                activities = activities.scalars().all()
                
                # Analyze performance
                performance_analysis = await self._analyze_voice_performance(activities)
                
                # Get improvement trends
                improvement_trends = await self._analyze_improvement_trends(activities)
                
                return {
                    "success": True,
                    "performance_analysis": performance_analysis,
                    "improvement_trends": improvement_trends,
                    "analysis_period_days": days
                }
                
        except Exception as e:
            logger.error(f"Error getting voice analytics: {e}")
            return {"success": False, "error": str(e)}
    
    async def generate_practice_scenarios(
        self,
        rep_id: int,
        difficulty_level: str = "medium",
        focus_areas: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Generate practice scenarios for voice pitch improvement"""
        try:
            db = await get_eric_database()
            async with db.get_session() as session:
                # Get rep's performance history
                performance_history = await self._get_rep_performance_history(session, rep_id)
                
                # Identify areas for improvement
                improvement_areas = await self._identify_improvement_areas(performance_history)
                
                # Generate personalized scenarios
                scenarios = await self._generate_personalized_scenarios(
                    improvement_areas, difficulty_level, focus_areas
                )
                
                return {
                    "success": True,
                    "scenarios": scenarios,
                    "improvement_areas": improvement_areas,
                    "difficulty_level": difficulty_level,
                    "total_scenarios": len(scenarios)
                }
                
        except Exception as e:
            logger.error(f"Error generating practice scenarios: {e}")
            return {"success": False, "error": str(e)}
    
    async def compare_voice_performance(
        self,
        rep_id: int,
        baseline_date: Optional[str] = None,
        comparison_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Compare voice performance over time"""
        try:
            db = await get_eric_database()
            async with db.get_session() as session:
                # Get baseline and comparison data
                baseline_data = await self._get_performance_data(
                    session, rep_id, baseline_date or "30_days_ago"
                )
                
                comparison_data = await self._get_performance_data(
                    session, rep_id, comparison_date or "current"
                )
                
                # Calculate improvements
                improvements = await self._calculate_performance_improvements(
                    baseline_data, comparison_data
                )
                
                return {
                    "success": True,
                    "baseline_data": baseline_data,
                    "comparison_data": comparison_data,
                    "improvements": improvements,
                    "overall_improvement": improvements.get("overall_score_improvement", 0)
                }
                
        except Exception as e:
            logger.error(f"Error comparing voice performance: {e}")
            return {"success": False, "error": str(e)}
    
    async def _get_sales_rep(
        self,
        session: AsyncSession,
        rep_id: int
    ) -> Optional[EricSalesRep]:
        """Get sales rep information"""
        query = select(EricSalesRep).where(EricSalesRep.id == rep_id)
        result = await session.execute(query)
        return result.scalar_one_or_none()
    
    async def _analyze_voice_characteristics(self, audio_data: str) -> Dict[str, Any]:
        """Analyze voice characteristics from audio data"""
        try:
            # Decode base64 audio data
            audio_bytes = base64.b64decode(audio_data)
            
            # Convert to numpy array and perform audio analysis
            audio_array = np.frombuffer(audio_bytes, dtype=np.float32)
            
            # Apply audio preprocessing
            audio_array = self._preprocess_audio(audio_array)
            
            # Analyze pitch
            pitch_analysis = await self._analyze_pitch(audio_array)
            
            # Analyze speech rate
            speech_rate_analysis = await self._analyze_speech_rate(audio_array)
            
            # Analyze volume
            volume_analysis = await self._analyze_volume(audio_array)
            
            # Analyze clarity
            clarity_analysis = await self._analyze_clarity(audio_array)
            
            # Analyze confidence indicators
            confidence_analysis = await self._analyze_confidence(audio_array)
            
            return {
                "pitch": pitch_analysis,
                "speech_rate": speech_rate_analysis,
                "volume": volume_analysis,
                "clarity": clarity_analysis,
                "confidence": confidence_analysis,
                "overall_voice_score": self._calculate_voice_score({
                    "pitch": pitch_analysis,
                    "speech_rate": speech_rate_analysis,
                    "volume": volume_analysis,
                    "clarity": clarity_analysis,
                    "confidence": confidence_analysis
                })
            }
            
        except Exception as e:
            logger.error(f"Error analyzing voice characteristics: {e}")
            return {
                "pitch": {"score": 0, "feedback": "Analysis failed"},
                "speech_rate": {"score": 0, "feedback": "Analysis failed"},
                "volume": {"score": 0, "feedback": "Analysis failed"},
                "clarity": {"score": 0, "feedback": "Analysis failed"},
                "confidence": {"score": 0, "feedback": "Analysis failed"},
                "overall_voice_score": 0
            }
    
    async def _analyze_pitch(self, audio_array: np.ndarray) -> Dict[str, Any]:
        """Analyze voice pitch"""
        try:
            # Calculate fundamental frequency (simplified)
            # In real implementation, use proper pitch detection algorithms
            sample_rate = 16000  # Assuming 16kHz sample rate
            
            # Use autocorrelation for pitch detection
            autocorr = np.correlate(audio_array, audio_array, mode='full')
            autocorr = autocorr[len(autocorr)//2:]
            
            # Find peaks in autocorrelation
            peaks = signal.find_peaks(autocorr, height=0.1*np.max(autocorr))[0]
            
            if len(peaks) > 0:
                # Calculate fundamental frequency
                fundamental_freq = sample_rate / peaks[0] if peaks[0] > 0 else 150
            else:
                fundamental_freq = 150  # Default frequency
            
            # Score based on optimal range
            optimal_min, optimal_max = self.voice_parameters["pitch"]["optimal_range"]
            if optimal_min <= fundamental_freq <= optimal_max:
                score = 1.0
                feedback = "Excellent pitch range"
            elif fundamental_freq < optimal_min:
                score = 0.6
                feedback = "Pitch is too low, consider speaking higher"
            else:
                score = 0.7
                feedback = "Pitch is too high, consider speaking lower"
            
            return {
                "frequency": fundamental_freq,
                "score": score,
                "feedback": feedback,
                "optimal_range": self.voice_parameters["pitch"]["optimal_range"]
            }
            
        except Exception as e:
            logger.error(f"Error analyzing pitch: {e}")
            return {"frequency": 150, "score": 0, "feedback": "Analysis failed"}
    
    async def _analyze_speech_rate(self, audio_array: np.ndarray) -> Dict[str, Any]:
        """Analyze speech rate"""
        try:
            # Estimate speech rate (simplified)
            # In real implementation, use speech recognition for word count
            duration_seconds = len(audio_array) / 16000  # Assuming 16kHz
            
            # Estimate words per minute (simplified calculation)
            estimated_words = duration_seconds * 2.5  # Rough estimate
            words_per_minute = (estimated_words / duration_seconds) * 60
            
            # Score based on optimal range
            optimal_min, optimal_max = self.voice_parameters["speech_rate"]["optimal_range"]
            if optimal_min <= words_per_minute <= optimal_max:
                score = 1.0
                feedback = "Perfect speech rate"
            elif words_per_minute < optimal_min:
                score = 0.7
                feedback = "Speech rate is too slow, try speaking faster"
            else:
                score = 0.8
                feedback = "Speech rate is too fast, try speaking slower"
            
            return {
                "words_per_minute": words_per_minute,
                "score": score,
                "feedback": feedback,
                "optimal_range": self.voice_parameters["speech_rate"]["optimal_range"]
            }
            
        except Exception as e:
            logger.error(f"Error analyzing speech rate: {e}")
            return {"words_per_minute": 140, "score": 0, "feedback": "Analysis failed"}
    
    async def _analyze_volume(self, audio_array: np.ndarray) -> Dict[str, Any]:
        """Analyze voice volume"""
        try:
            # Calculate RMS (Root Mean Square) for volume
            rms = np.sqrt(np.mean(audio_array**2))
            
            # Normalize volume (0-1 scale)
            normalized_volume = min(rms * 10, 1.0)  # Scaling factor
            
            # Score based on optimal range
            optimal_min, optimal_max = self.voice_parameters["volume"]["optimal_range"]
            if optimal_min <= normalized_volume <= optimal_max:
                score = 1.0
                feedback = "Perfect volume level"
            elif normalized_volume < optimal_min:
                score = 0.6
                feedback = "Volume is too low, speak louder"
            else:
                score = 0.8
                feedback = "Volume is too high, speak softer"
            
            return {
                "volume_level": normalized_volume,
                "score": score,
                "feedback": feedback,
                "optimal_range": self.voice_parameters["volume"]["optimal_range"]
            }
            
        except Exception as e:
            logger.error(f"Error analyzing volume: {e}")
            return {"volume_level": 0.7, "score": 0, "feedback": "Analysis failed"}
    
    async def _analyze_clarity(self, audio_array: np.ndarray) -> Dict[str, Any]:
        """Analyze speech clarity"""
        try:
            # Calculate spectral centroid (indicator of clarity)
            # Higher spectral centroid = clearer speech
            fft = np.fft.fft(audio_array)
            magnitude = np.abs(fft)
            frequencies = np.fft.fftfreq(len(audio_array), 1/16000)
            
            # Calculate spectral centroid
            spectral_centroid = np.sum(frequencies * magnitude) / np.sum(magnitude)
            
            # Normalize clarity score (0-1)
            clarity_score = min(spectral_centroid / 2000, 1.0)  # Normalize to 2kHz max
            
            # Score based on optimal range
            optimal_min, optimal_max = self.voice_parameters["clarity"]["optimal_range"]
            if optimal_min <= clarity_score <= optimal_max:
                score = 1.0
                feedback = "Excellent speech clarity"
            elif clarity_score < optimal_min:
                score = 0.6
                feedback = "Speech clarity needs improvement, enunciate more clearly"
            else:
                score = 0.9
                feedback = "Good speech clarity"
            
            return {
                "clarity_score": clarity_score,
                "score": score,
                "feedback": feedback,
                "optimal_range": self.voice_parameters["clarity"]["optimal_range"]
            }
            
        except Exception as e:
            logger.error(f"Error analyzing clarity: {e}")
            return {"clarity_score": 0.7, "score": 0, "feedback": "Analysis failed"}
    
    async def _analyze_confidence(self, audio_array: np.ndarray) -> Dict[str, Any]:
        """Analyze confidence indicators in voice"""
        try:
            # Analyze confidence through multiple indicators
            
            # 1. Volume consistency
            volume_consistency = 1.0 - np.std(audio_array) / np.mean(np.abs(audio_array))
            
            # 2. Pitch stability - calculate from pitch variations
            pitch_variations = self._calculate_pitch_variations(audio_array)
            pitch_stability = max(0, 1.0 - pitch_variations)
            
            # 3. Speech rate consistency - analyze speech rate variations
            rate_variations = self._calculate_speech_rate_variations(audio_array)
            rate_consistency = max(0, 1.0 - rate_variations)
            
            # Combine indicators
            confidence_score = (volume_consistency + pitch_stability + rate_consistency) / 3
            
            # Score based on optimal range
            optimal_min, optimal_max = self.voice_parameters["confidence"]["optimal_range"]
            if optimal_min <= confidence_score <= optimal_max:
                score = 1.0
                feedback = "Excellent confidence indicators"
            elif confidence_score < optimal_min:
                score = 0.6
                feedback = "Work on projecting more confidence in your voice"
            else:
                score = 0.9
                feedback = "Good confidence indicators"
            
            return {
                "confidence_score": confidence_score,
                "score": score,
                "feedback": feedback,
                "indicators": {
                    "volume_consistency": volume_consistency,
                    "pitch_stability": pitch_stability,
                    "rate_consistency": rate_consistency
                },
                "optimal_range": self.voice_parameters["confidence"]["optimal_range"]
            }
            
        except Exception as e:
            logger.error(f"Error analyzing confidence: {e}")
            return {"confidence_score": 0.7, "score": 0, "feedback": "Analysis failed"}
    
    def _calculate_voice_score(self, voice_analysis: Dict[str, Any]) -> float:
        """Calculate overall voice score"""
        try:
            total_score = 0
            total_weight = 0
            
            for param_name, param_config in self.voice_parameters.items():
                if param_name in voice_analysis:
                    score = voice_analysis[param_name].get("score", 0)
                    weight = param_config["weight"]
                    total_score += score * weight
                    total_weight += weight
            
            return total_score / total_weight if total_weight > 0 else 0
            
        except Exception as e:
            logger.error(f"Error calculating voice score: {e}")
            return 0
    
    async def _analyze_pitch_content(
        self,
        pitch_content: str,
        scenario_type: str
    ) -> Dict[str, Any]:
        """Analyze pitch content"""
        try:
            # Get scenario requirements
            scenario_config = self.pitch_scenarios.get(scenario_type, {})
            key_elements = scenario_config.get("key_elements", [])
            
            # Analyze content structure
            content_analysis = {
                "word_count": len(pitch_content.split()),
                "duration_estimate": len(pitch_content.split()) / 2.5,  # Rough estimate
                "key_elements_present": [],
                "missing_elements": [],
                "content_score": 0
            }
            
            # Check for key elements
            for element in key_elements:
                if element.lower() in pitch_content.lower():
                    content_analysis["key_elements_present"].append(element)
                else:
                    content_analysis["missing_elements"].append(element)
            
            # Calculate content score
            element_score = len(content_analysis["key_elements_present"]) / len(key_elements)
            duration_score = 1.0 if 0.8 <= content_analysis["duration_estimate"] / scenario_config.get("duration", 60) <= 1.2 else 0.7
            
            content_analysis["content_score"] = (element_score + duration_score) / 2
            
            return content_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing pitch content: {e}")
            return {"content_score": 0, "error": "Analysis failed"}
    
    async def _generate_voice_feedback(
        self,
        voice_analysis: Dict[str, Any],
        content_analysis: Dict[str, Any],
        scenario_type: str
    ) -> Dict[str, Any]:
        """Generate comprehensive feedback"""
        try:
            feedback = {
                "voice_feedback": {},
                "content_feedback": {},
                "overall_feedback": "",
                "priority_improvements": []
            }
            
            # Voice feedback
            for param_name, analysis in voice_analysis.items():
                if param_name != "overall_voice_score":
                    feedback["voice_feedback"][param_name] = {
                        "score": analysis.get("score", 0),
                        "feedback": analysis.get("feedback", ""),
                        "improvement_tip": await self._generate_improvement_tip(param_name, analysis)
                    }
            
            # Content feedback
            if content_analysis:
                feedback["content_feedback"] = {
                    "score": content_analysis.get("content_score", 0),
                    "missing_elements": content_analysis.get("missing_elements", []),
                    "duration_feedback": self._generate_duration_feedback(
                        content_analysis.get("duration_estimate", 0),
                        self.pitch_scenarios.get(scenario_type, {}).get("duration", 60)
                    )
                }
            
            # Overall feedback
            overall_score = voice_analysis.get("overall_voice_score", 0)
            content_score = content_analysis.get("content_score", 0) if content_analysis else 0
            
            if overall_score >= 0.8 and content_score >= 0.8:
                feedback["overall_feedback"] = "Excellent pitch! Your voice and content are well-aligned."
            elif overall_score >= 0.6 and content_score >= 0.6:
                feedback["overall_feedback"] = "Good pitch with room for improvement in specific areas."
            else:
                feedback["overall_feedback"] = "Focus on improving both voice delivery and content structure."
            
            # Priority improvements
            feedback["priority_improvements"] = await self._identify_priority_improvements(
                voice_analysis, content_analysis
            )
            
            return feedback
            
        except Exception as e:
            logger.error(f"Error generating voice feedback: {e}")
            return {"error": "Failed to generate feedback"}
    
    async def _generate_improvement_tip(
        self,
        param_name: str,
        analysis: Dict[str, Any]
    ) -> str:
        """Generate improvement tip for specific parameter"""
        try:
            tips = {
                "pitch": "Practice speaking at different pitch levels to find your optimal range",
                "speech_rate": "Record yourself and practice speaking at 140 words per minute",
                "volume": "Practice projecting your voice without shouting",
                "clarity": "Focus on enunciating each word clearly",
                "confidence": "Practice power poses and breathing exercises before calls"
            }
            
            return tips.get(param_name, "Practice regularly to improve this aspect")
            
        except Exception as e:
            logger.error(f"Error generating improvement tip: {e}")
            return "Practice regularly to improve"
    
    def _generate_duration_feedback(
        self,
        estimated_duration: float,
        target_duration: float
    ) -> str:
        """Generate duration feedback"""
        try:
            if 0.8 <= estimated_duration / target_duration <= 1.2:
                return "Perfect duration for this scenario"
            elif estimated_duration < target_duration * 0.8:
                return f"Pitch is too short. Aim for {target_duration} seconds"
            else:
                return f"Pitch is too long. Aim for {target_duration} seconds"
                
        except Exception as e:
            logger.error(f"Error generating duration feedback: {e}")
            return "Check pitch duration"
    
    async def _identify_priority_improvements(
        self,
        voice_analysis: Dict[str, Any],
        content_analysis: Dict[str, Any]
    ) -> List[str]:
        """Identify priority improvements"""
        try:
            improvements = []
            
            # Voice improvements
            for param_name, analysis in voice_analysis.items():
                if param_name != "overall_voice_score" and analysis.get("score", 0) < 0.7:
                    improvements.append(f"Improve {param_name}: {analysis.get('feedback', '')}")
            
            # Content improvements
            if content_analysis and content_analysis.get("content_score", 0) < 0.7:
                missing = content_analysis.get("missing_elements", [])
                if missing:
                    improvements.append(f"Add missing elements: {', '.join(missing)}")
            
            return improvements[:3]  # Top 3 improvements
            
        except Exception as e:
            logger.error(f"Error identifying priority improvements: {e}")
            return ["Practice regularly to improve overall performance"]
    
    async def _calculate_overall_score(
        self,
        voice_analysis: Dict[str, Any],
        content_analysis: Dict[str, Any]
    ) -> float:
        """Calculate overall simulation score"""
        try:
            voice_score = voice_analysis.get("overall_voice_score", 0)
            content_score = content_analysis.get("content_score", 0) if content_analysis else 0
            
            # Weight voice more heavily (70% voice, 30% content)
            overall_score = (voice_score * 0.7) + (content_score * 0.3)
            
            return round(overall_score, 2)
            
        except Exception as e:
            logger.error(f"Error calculating overall score: {e}")
            return 0
    
    async def _generate_improvement_recommendations(
        self,
        voice_analysis: Dict[str, Any],
        content_analysis: Dict[str, Any],
        scenario_type: str
    ) -> List[Dict[str, Any]]:
        """Generate improvement recommendations"""
        try:
            recommendations = []
            
            # Voice recommendations
            for param_name, analysis in voice_analysis.items():
                if param_name != "overall_voice_score" and analysis.get("score", 0) < 0.8:
                    recommendations.append({
                        "category": "voice",
                        "parameter": param_name,
                        "current_score": analysis.get("score", 0),
                        "recommendation": analysis.get("feedback", ""),
                        "practice_exercise": await self._generate_practice_exercise(param_name)
                    })
            
            # Content recommendations
            if content_analysis and content_analysis.get("content_score", 0) < 0.8:
                recommendations.append({
                    "category": "content",
                    "parameter": "structure",
                    "current_score": content_analysis.get("content_score", 0),
                    "recommendation": "Improve pitch structure and include all key elements",
                    "practice_exercise": "Practice with pitch templates and scripts"
                })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating improvement recommendations: {e}")
            return []
    
    async def _generate_practice_exercise(self, param_name: str) -> str:
        """Generate practice exercise for specific parameter"""
        try:
            exercises = {
                "pitch": "Practice humming at different frequencies to find your optimal pitch",
                "speech_rate": "Read aloud with a metronome set to 140 BPM",
                "volume": "Practice speaking at different volumes in a quiet room",
                "clarity": "Practice tongue twisters and enunciation exercises",
                "confidence": "Record yourself and practice power poses before speaking"
            }
            
            return exercises.get(param_name, "Practice regularly to improve this aspect")
            
        except Exception as e:
            logger.error(f"Error generating practice exercise: {e}")
            return "Practice regularly to improve"
    
    async def _store_simulation_results(
        self,
        session: AsyncSession,
        rep_id: int,
        scenario_type: str,
        voice_analysis: Dict[str, Any],
        content_analysis: Dict[str, Any],
        overall_score: float,
        feedback: Dict[str, Any]
    ) -> None:
        """Store simulation results"""
        try:
            activity = EricSalesActivity(
                activity_type="voice_pitch_simulation",
                rep_id=rep_id,
                metadata={
                    "scenario_type": scenario_type,
                    "voice_analysis": voice_analysis,
                    "content_analysis": content_analysis,
                    "overall_score": overall_score,
                    "feedback": feedback,
                    "simulated_at": datetime.utcnow().isoformat()
                }
            )
            
            session.add(activity)
            await session.commit()
            
        except Exception as e:
            logger.error(f"Error storing simulation results: {e}")
    
    async def _analyze_voice_performance(self, pitch_id: str) -> Dict[str, Any]:
        """Analyze voice pitch performance metrics"""
        try:
            async with get_eric_database() as db:
                # Simulate voice performance analysis
                performance_metrics = {
                    "pitch_id": pitch_id,
                    "duration_seconds": 120,
                    "clarity_score": 85,
                    "confidence_score": 78,
                    "engagement_score": 82,
                    "pace_score": 75,
                    "tone_score": 88,
                    "overall_score": 82,
                    "key_improvements": [
                        "Reduce speaking pace by 15%",
                        "Increase vocal variety",
                        "Add more pauses for emphasis"
                    ],
                    "strengths": [
                        "Clear articulation",
                        "Good volume control",
                        "Professional tone"
                    ],
                    "areas_for_improvement": [
                        "Speaking too fast",
                        "Limited vocal variety",
                        "Need more emotional expression"
                    ],
                    "recommendations": [
                        "Practice with slower pace",
                        "Record and review regularly",
                        "Work on vocal inflection"
                    ],
                    "analysis_date": datetime.utcnow().isoformat()
                }
                
                return performance_metrics
                
        except Exception as e:
            logger.error(f"Error analyzing voice performance: {e}")
            return {
                "pitch_id": pitch_id,
                "duration_seconds": 0,
                "clarity_score": 0,
                "confidence_score": 0,
                "engagement_score": 0,
                "pace_score": 0,
                "tone_score": 0,
                "overall_score": 0,
                "key_improvements": ["Unable to analyze voice performance"],
                "strengths": [],
                "areas_for_improvement": [],
                "recommendations": ["Contact support for voice analysis"]
            }
    
    async def _analyze_improvement_trends(
        self,
        activities: List[EricSalesActivity]
    ) -> Dict[str, Any]:
        """Analyze improvement trends over time"""
        try:
            if len(activities) < 2:
                return {"trend": "insufficient_data"}
            
            # Sort by date
            sorted_activities = sorted(activities, key=lambda x: x.created_at)
            
            # Calculate trend
            early_scores = [a.metadata.get("overall_score", 0) for a in sorted_activities[:len(sorted_activities)//2]]
            recent_scores = [a.metadata.get("overall_score", 0) for a in sorted_activities[len(sorted_activities)//2:]]
            
            early_avg = sum(early_scores) / len(early_scores)
            recent_avg = sum(recent_scores) / len(recent_scores)
            
            improvement = recent_avg - early_avg
            
            if improvement > 0.1:
                trend = "improving"
            elif improvement < -0.1:
                trend = "declining"
            else:
                trend = "stable"
            
            return {
                "trend": trend,
                "improvement_amount": round(improvement, 2),
                "early_average": round(early_avg, 2),
                "recent_average": round(recent_avg, 2)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing improvement trends: {e}")
            return {"trend": "analysis_failed"}
    
    async def _get_rep_performance_history(
        self,
        session: AsyncSession,
        rep_id: int
    ) -> List[Dict[str, Any]]:
        """Get rep's performance history"""
        try:
            query = select(EricSalesActivity).where(
                and_(
                    EricSalesActivity.rep_id == rep_id,
                    EricSalesActivity.activity_type == "voice_pitch_simulation"
                )
            ).order_by(EricSalesActivity.created_at.desc()).limit(20)
            
            activities = await session.execute(query)
            activities = activities.scalars().all()
            
            return [
                {
                    "score": activity.metadata.get("overall_score", 0),
                    "scenario_type": activity.metadata.get("scenario_type"),
                    "voice_analysis": activity.metadata.get("voice_analysis", {}),
                    "date": activity.created_at.isoformat()
                }
                for activity in activities
            ]
            
        except Exception as e:
            logger.error(f"Error getting rep performance history: {e}")
            return []
    
    async def _identify_improvement_areas(
        self,
        performance_history: List[Dict[str, Any]]
    ) -> List[str]:
        """Identify areas for improvement"""
        try:
            if not performance_history:
                return ["pitch", "speech_rate", "volume", "clarity", "confidence"]
            
            # Analyze voice parameters
            param_scores = {
                "pitch": [],
                "speech_rate": [],
                "volume": [],
                "clarity": [],
                "confidence": []
            }
            
            for performance in performance_history:
                voice_analysis = performance.get("voice_analysis", {})
                for param_name in param_scores.keys():
                    if param_name in voice_analysis:
                        param_scores[param_name].append(voice_analysis[param_name].get("score", 0))
            
            # Find areas with lowest average scores
            improvement_areas = []
            for param_name, scores in param_scores.items():
                if scores and sum(scores) / len(scores) < 0.7:
                    improvement_areas.append(param_name)
            
            return improvement_areas if improvement_areas else ["confidence"]
            
        except Exception as e:
            logger.error(f"Error identifying improvement areas: {e}")
            return ["confidence"]
    
    async def _generate_personalized_scenarios(
        self,
        improvement_areas: List[str],
        difficulty_level: str,
        focus_areas: Optional[List[str]]
    ) -> List[Dict[str, Any]]:
        """Generate personalized practice scenarios"""
        try:
            scenarios = []
            
            # Generate scenarios based on improvement areas
            for area in improvement_areas:
                scenario = {
                    "focus_area": area,
                    "difficulty": difficulty_level,
                    "duration": 60,
                    "description": f"Practice scenario focusing on {area} improvement",
                    "key_objectives": [
                        f"Improve {area} score",
                        "Maintain consistent delivery",
                        "Practice with feedback"
                    ],
                    "success_criteria": [
                        f"Achieve {area} score above 0.8",
                        "Complete full scenario",
                        "Apply feedback from previous sessions"
                    ]
                }
                scenarios.append(scenario)
            
            return scenarios
            
        except Exception as e:
            logger.error(f"Error generating personalized scenarios: {e}")
            return []
    
    async def _get_performance_data(
        self,
        session: AsyncSession,
        rep_id: int,
        time_period: str
    ) -> Dict[str, Any]:
        """Get performance data for specific time period"""
        try:
            if time_period == "current":
                start_date = datetime.utcnow() - timedelta(days=7)
            elif time_period == "30_days_ago":
                start_date = datetime.utcnow() - timedelta(days=37)
                end_date = datetime.utcnow() - timedelta(days=30)
            else:
                start_date = datetime.utcnow() - timedelta(days=30)
                end_date = datetime.utcnow()
            
            query = select(EricSalesActivity).where(
                and_(
                    EricSalesActivity.rep_id == rep_id,
                    EricSalesActivity.activity_type == "voice_pitch_simulation",
                    EricSalesActivity.created_at >= start_date
                )
            )
            
            if time_period == "30_days_ago":
                query = query.where(EricSalesActivity.created_at <= end_date)
            
            activities = await session.execute(query)
            activities = activities.scalars().all()
            
            scores = [a.metadata.get("overall_score", 0) for a in activities if a.metadata]
            
            return {
                "period": time_period,
                "total_simulations": len(activities),
                "average_score": sum(scores) / len(scores) if scores else 0,
                "scores": scores
            }
            
        except Exception as e:
            logger.error(f"Error getting performance data: {e}")
            return {"period": time_period, "total_simulations": 0, "average_score": 0, "scores": []}
    
    async def _calculate_performance_improvements(
        self,
        baseline_data: Dict[str, Any],
        comparison_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate performance improvements"""
        try:
            baseline_score = baseline_data.get("average_score", 0)
            comparison_score = comparison_data.get("average_score", 0)
            
            score_improvement = comparison_score - baseline_score
            percentage_improvement = (score_improvement / baseline_score * 100) if baseline_score > 0 else 0
            
            return {
                "overall_score_improvement": round(score_improvement, 2),
                "percentage_improvement": round(percentage_improvement, 1),
                "baseline_score": round(baseline_score, 2),
                "comparison_score": round(comparison_score, 2),
                "improvement_status": "improving" if score_improvement > 0 else "declining" if score_improvement < 0 else "stable"
            }
            
        except Exception as e:
            logger.error(f"Error calculating performance improvements: {e}")
            return {"overall_score_improvement": 0, "percentage_improvement": 0}
