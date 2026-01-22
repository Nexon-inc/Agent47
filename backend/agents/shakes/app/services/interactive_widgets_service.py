import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime
from core.ai import get_ai_service_manager, AIServiceManager
from core.integrations.integration_manager import IntegrationManager
from core.event_bus.kafka_manager import EventBus
from ..database import get_shakes_database
from ..models import ShakesContentProject, ShakesContentPiece

logger = logging.getLogger(__name__)

class InteractiveWidgetsService:
    """Service for interactive content widgets and engagement tools"""
    
    def __init__(self):
        self.integration_manager = IntegrationManager()
        self.event_bus = EventBus()
        self._initialized = False
        self.model_config = {
            "model": "grok-llm",
            "max_tokens": 3000,
            "temperature": 0.6
        }
    
    async def initialize(self):
        """Initialize interactive widgets service"""
        if self._initialized:
            return
        
        try:
            await self.integration_manager.initialize()
            await self.event_bus.initialize()
            self._initialized = True
            logger.info("Interactive widgets service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize interactive widgets service: {e}")
            raise
    
    async def create_interactive_widget(
        self,
        content_piece_id: int,
        widget_type: str,
        widget_config: Dict[str, Any],
        target_audience: str
    ) -> Dict[str, Any]:
        """Create interactive widget for content"""
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
                
                # Generate widget content
                widget_content = await self._generate_widget_content(
                    content_piece, widget_type, widget_config, target_audience
                )
                
                # Generate widget code
                widget_code = await self._generate_widget_code(
                    widget_type, widget_content, widget_config
                )
                
                # Generate widget styling
                widget_styling = await self._generate_widget_styling(
                    widget_type, widget_config, target_audience
                )
                
                # Generate widget functionality
                widget_functionality = await self._generate_widget_functionality(
                    widget_type, widget_content, widget_config
                )
                
                # Generate widget analytics
                widget_analytics = await self._generate_widget_analytics(
                    widget_type, widget_config
                )
                
                return {
                    "success": True,
                    "content_piece_id": content_piece_id,
                    "widget_type": widget_type,
                    "widget_config": widget_config,
                    "target_audience": target_audience,
                    "widget_content": widget_content,
                    "widget_code": widget_code,
                    "widget_styling": widget_styling,
                    "widget_functionality": widget_functionality,
                    "widget_analytics": widget_analytics,
                    "widget_id": f"widget_{int(datetime.utcnow().timestamp())}",
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Interactive widget creation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def create_quiz_widget(
        self,
        content_piece_id: int,
        quiz_config: Dict[str, Any],
        question_count: int = 5
    ) -> Dict[str, Any]:
        """Create interactive quiz widget"""
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
                
                # Generate quiz questions
                quiz_questions = await self._generate_quiz_questions(
                    content_piece, quiz_config, question_count
                )
                
                # Generate quiz logic
                quiz_logic = await self._generate_quiz_logic(
                    quiz_questions, quiz_config
                )
                
                # Generate quiz results
                quiz_results = await self._generate_quiz_results(
                    quiz_questions, quiz_config
                )
                
                # Generate quiz styling
                quiz_styling = await self._generate_quiz_styling(
                    quiz_config
                )
                
                return {
                    "success": True,
                    "content_piece_id": content_piece_id,
                    "quiz_config": quiz_config,
                    "question_count": question_count,
                    "quiz_questions": quiz_questions,
                    "quiz_logic": quiz_logic,
                    "quiz_results": quiz_results,
                    "quiz_styling": quiz_styling,
                    "quiz_id": f"quiz_{int(datetime.utcnow().timestamp())}",
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Quiz widget creation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def create_poll_widget(
        self,
        content_piece_id: int,
        poll_config: Dict[str, Any],
        poll_options: List[str]
    ) -> Dict[str, Any]:
        """Create interactive poll widget"""
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
                
                # Generate poll content
                poll_content = await self._generate_poll_content(
                    content_piece, poll_config, poll_options
                )
                
                # Generate poll logic
                poll_logic = await self._generate_poll_logic(
                    poll_options, poll_config
                )
                
                # Generate poll visualization
                poll_visualization = await self._generate_poll_visualization(
                    poll_options, poll_config
                )
                
                # Generate poll analytics
                poll_analytics = await self._generate_poll_analytics(
                    poll_config
                )
                
                return {
                    "success": True,
                    "content_piece_id": content_piece_id,
                    "poll_config": poll_config,
                    "poll_options": poll_options,
                    "poll_content": poll_content,
                    "poll_logic": poll_logic,
                    "poll_visualization": poll_visualization,
                    "poll_analytics": poll_analytics,
                    "poll_id": f"poll_{int(datetime.utcnow().timestamp())}",
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Poll widget creation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def create_survey_widget(
        self,
        content_piece_id: int,
        survey_config: Dict[str, Any],
        survey_questions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create interactive survey widget"""
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
                
                # Generate survey content
                survey_content = await self._generate_survey_content(
                    content_piece, survey_config, survey_questions
                )
                
                # Generate survey logic
                survey_logic = await self._generate_survey_logic(
                    survey_questions, survey_config
                )
                
                # Generate survey validation
                survey_validation = await self._generate_survey_validation(
                    survey_questions, survey_config
                )
                
                # Generate survey analytics
                survey_analytics = await self._generate_survey_analytics(
                    survey_config
                )
                
                return {
                    "success": True,
                    "content_piece_id": content_piece_id,
                    "survey_config": survey_config,
                    "survey_questions": survey_questions,
                    "survey_content": survey_content,
                    "survey_logic": survey_logic,
                    "survey_validation": survey_validation,
                    "survey_analytics": survey_analytics,
                    "survey_id": f"survey_{int(datetime.utcnow().timestamp())}",
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Survey widget creation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def create_interactive_gallery(
        self,
        content_piece_id: int,
        gallery_config: Dict[str, Any],
        media_items: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create interactive media gallery widget"""
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
                
                # Generate gallery layout
                gallery_layout = await self._generate_gallery_layout(
                    media_items, gallery_config
                )
                
                # Generate gallery interactions
                gallery_interactions = await self._generate_gallery_interactions(
                    gallery_config
                )
                
                # Generate gallery styling
                gallery_styling = await self._generate_gallery_styling(
                    gallery_config
                )
                
                # Generate gallery analytics
                gallery_analytics = await self._generate_gallery_analytics(
                    gallery_config
                )
                
                return {
                    "success": True,
                    "content_piece_id": content_piece_id,
                    "gallery_config": gallery_config,
                    "media_items": media_items,
                    "gallery_layout": gallery_layout,
                    "gallery_interactions": gallery_interactions,
                    "gallery_styling": gallery_styling,
                    "gallery_analytics": gallery_analytics,
                    "gallery_id": f"gallery_{int(datetime.utcnow().timestamp())}",
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Interactive gallery creation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _generate_widget_content(
        self, content_piece: ShakesContentPiece, widget_type: str, widget_config: Dict[str, Any], target_audience: str
    ) -> Dict[str, Any]:
        """Generate widget content"""
        content_prompt = self._create_widget_content_prompt(
            content_piece, widget_type, widget_config, target_audience
        )
        # Use AI Service Manager instead of NLPUtils
        ai_manager = await get_ai_service_manager()
        messages = [{"role": "system", "content": "You are an AI assistant that creates interactive widget content."}, {"role": "user", "content": content_prompt}]
        ai_response = await ai_manager.generate_text(messages=messages, max_tokens=3000, temperature=0.6)
        content_result = ai_response.text_content if ai_response.success else ""
        
        return {
            "widget_title": f"Interactive {widget_type.title()}",
            "widget_description": content_result,
            "widget_instructions": "Follow the instructions to interact with this widget",
            "widget_content": content_result
        }
    
    async def _generate_widget_code(
        self, widget_type: str, widget_content: Dict[str, Any], widget_config: Dict[str, Any]
    ) -> str:
        """Generate widget code"""
        code_prompt = self._create_widget_code_prompt(
            widget_type, widget_content, widget_config
        )
        # Use AI Service Manager instead of NLPUtils
        ai_manager = await get_ai_service_manager()
        messages = [{"role": "system", "content": "You are an AI assistant that generates interactive widget code."}, {"role": "user", "content": code_prompt}]
        ai_response = await ai_manager.generate_text(messages=messages, max_tokens=2000, temperature=0.6)
        code_result = ai_response.text_content if ai_response.success else ""
        return code_result
    
    async def _generate_widget_styling(
        self, widget_type: str, widget_config: Dict[str, Any], target_audience: str
    ) -> Dict[str, Any]:
        """Generate widget styling"""
        return {
            "theme": widget_config.get("theme", "modern"),
            "colors": {
                "primary": "#007bff",
                "secondary": "#6c757d",
                "background": "#ffffff",
                "text": "#333333"
            },
            "typography": {
                "font_family": "Arial, sans-serif",
                "font_size": "16px",
                "line_height": "1.5"
            },
            "layout": {
                "width": "100%",
                "max_width": "600px",
                "padding": "20px",
                "border_radius": "8px"
            }
        }
    
    async def _generate_widget_functionality(
        self, widget_type: str, widget_content: Dict[str, Any], widget_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate widget functionality"""
        return {
            "interactions": ["click", "hover", "submit"],
            "animations": ["fade_in", "slide_up"],
            "responsiveness": True,
            "accessibility": True,
            "mobile_optimized": True
        }
    
    async def _generate_widget_analytics(
        self, widget_type: str, widget_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate widget analytics configuration"""
        return {
            "track_interactions": True,
            "track_completions": True,
            "track_time_spent": True,
            "track_errors": True,
            "analytics_events": [
                "widget_viewed",
                "widget_interacted",
                "widget_completed",
                "widget_abandoned"
            ]
        }
    
    async def _generate_quiz_questions(
        self, content_piece: ShakesContentPiece, quiz_config: Dict[str, Any], question_count: int
    ) -> List[Dict[str, Any]]:
        """Generate quiz questions"""
        questions = []
        
        for i in range(question_count):
            question_prompt = self._create_quiz_question_prompt(
                content_piece, quiz_config, i + 1
            )
            # Use AI Service Manager instead of NLPUtils
            ai_manager = await get_ai_service_manager()
            messages = [{"role": "system", "content": "You are an AI assistant that creates quiz questions and options."}, {"role": "user", "content": question_prompt}]
            ai_response = await ai_manager.generate_text(messages=messages, max_tokens=1000, temperature=0.6)
            question_result = ai_response.text_content if ai_response.success else ""
            
            # Parse the generated question and options
            question_data = self._parse_quiz_question(question_result, i + 1)
            questions.append(question_data)
        
        return questions
    
    def _parse_quiz_question(self, question_result: str, question_id: int) -> Dict[str, Any]:
        """Parse generated quiz question into structured format"""
        try:
            # Extract question text (first line or until first option)
            lines = question_result.strip().split('\n')
            question_text = lines[0].strip()
            
            # Extract options (look for A), B), C), D) patterns)
            options = []
            correct_answer = "A"
            explanation = "This is the correct answer based on the content."
            
            for line in lines[1:]:
                line = line.strip()
                if line.startswith(('A)', 'B)', 'C)', 'D)')):
                    option_text = line[2:].strip()
                    options.append(option_text)
                elif line.startswith('Correct:'):
                    correct_answer = line.split(':')[1].strip()
                elif line.startswith('Explanation:'):
                    explanation = line.split(':', 1)[1].strip()
            
            # If no options found, generate default options
            if not options:
                options = [
                    "Option A - Based on the content",
                    "Option B - Alternative interpretation", 
                    "Option C - Different perspective",
                    "Option D - None of the above"
                ]
            
            return {
                "question_id": question_id,
                "question_text": question_text,
                "question_type": "multiple_choice",
                "options": options,
                "correct_answer": correct_answer,
                "explanation": explanation
            }
            
        except Exception as e:
            logger.error(f"Failed to parse quiz question: {e}")
            # Return fallback question
            return {
                "question_id": question_id,
                "question_text": f"Question {question_id} based on the content",
                "question_type": "multiple_choice",
                "options": [
                    "Option A - Based on the content",
                    "Option B - Alternative interpretation",
                    "Option C - Different perspective", 
                    "Option D - None of the above"
                ],
                "correct_answer": "A",
                "explanation": "This is the correct answer based on the content."
            }
    
    async def _generate_quiz_logic(
        self, quiz_questions: List[Dict[str, Any]], quiz_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate quiz logic"""
        return {
            "scoring_system": "points_based",
            "passing_score": 70,
            "time_limit": quiz_config.get("time_limit", 300),
            "retake_allowed": True,
            "show_results": True,
            "show_explanations": True
        }
    
    async def _generate_quiz_results(
        self, quiz_questions: List[Dict[str, Any]], quiz_config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate quiz results"""
        return [
            {
                "score_range": "0-40",
                "result_title": "Keep Learning!",
                "result_message": "You're on the right track. Keep studying to improve your knowledge.",
                "recommendations": ["Review the content", "Take the quiz again", "Explore related topics"]
            },
            {
                "score_range": "41-70",
                "result_title": "Good Progress!",
                "result_message": "You have a solid understanding. A few more areas to focus on.",
                "recommendations": ["Review incorrect answers", "Practice more", "Share your knowledge"]
            },
            {
                "score_range": "71-100",
                "result_title": "Excellent Work!",
                "result_message": "Outstanding! You have mastered this content.",
                "recommendations": ["Share your success", "Help others learn", "Explore advanced topics"]
            }
        ]
    
    async def _generate_quiz_styling(
        self, quiz_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate quiz styling"""
        return {
            "theme": quiz_config.get("theme", "educational"),
            "colors": {
                "primary": "#28a745",
                "secondary": "#6c757d",
                "success": "#28a745",
                "error": "#dc3545"
            },
            "animations": ["question_transition", "answer_feedback"],
            "progress_bar": True
        }
    
    async def _generate_poll_content(
        self, content_piece: ShakesContentPiece, poll_config: Dict[str, Any], poll_options: List[str]
    ) -> Dict[str, Any]:
        """Generate poll content"""
        content_prompt = self._create_poll_content_prompt(
            content_piece, poll_config, poll_options
        )
        # Use AI Service Manager instead of NLPUtils
        ai_manager = await get_ai_service_manager()
        messages = [{"role": "system", "content": "You are an AI assistant that creates interactive widget content."}, {"role": "user", "content": content_prompt}]
        ai_response = await ai_manager.generate_text(messages=messages, max_tokens=3000, temperature=0.6)
        content_result = ai_response.text_content if ai_response.success else ""
        
        return {
            "poll_title": content_result,
            "poll_description": "Share your opinion on this topic",
            "poll_instructions": "Select your preferred option",
            "poll_options": poll_options
        }
    
    async def _generate_poll_logic(
        self, poll_options: List[str], poll_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate poll logic"""
        return {
            "voting_type": "single_choice",
            "allow_multiple_votes": False,
            "show_results": poll_config.get("show_results", True),
            "real_time_updates": True,
            "anonymous_voting": True
        }
    
    async def _generate_poll_visualization(
        self, poll_options: List[str], poll_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate poll visualization"""
        return {
            "chart_type": poll_config.get("chart_type", "bar"),
            "show_percentages": True,
            "show_counts": True,
            "color_scheme": "vibrant",
            "animation": "smooth"
        }
    
    async def _generate_poll_analytics(
        self, poll_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate poll analytics"""
        return {
            "track_votes": True,
            "track_demographics": False,
            "track_time": True,
            "export_data": True
        }
    
    async def _generate_survey_content(
        self, content_piece: ShakesContentPiece, survey_config: Dict[str, Any], survey_questions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate survey content"""
        content_prompt = self._create_survey_content_prompt(
            content_piece, survey_config, survey_questions
        )
        # Use AI Service Manager instead of NLPUtils
        ai_manager = await get_ai_service_manager()
        messages = [{"role": "system", "content": "You are an AI assistant that creates interactive widget content."}, {"role": "user", "content": content_prompt}]
        ai_response = await ai_manager.generate_text(messages=messages, max_tokens=3000, temperature=0.6)
        content_result = ai_response.text_content if ai_response.success else ""
        
        return {
            "survey_title": content_result,
            "survey_description": "Help us improve by sharing your feedback",
            "survey_instructions": "Please answer all questions honestly",
            "estimated_time": "5 minutes"
        }
    
    async def _generate_survey_logic(
        self, survey_questions: List[Dict[str, Any]], survey_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate survey logic"""
        return {
            "question_order": "sequential",
            "required_questions": [q["question_id"] for q in survey_questions if q.get("required", True)],
            "skip_logic": [],
            "progress_saving": True,
            "auto_submit": False
        }
    
    async def _generate_survey_validation(
        self, survey_questions: List[Dict[str, Any]], survey_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate survey validation"""
        return {
            "required_field_validation": True,
            "email_validation": True,
            "number_validation": True,
            "text_length_validation": True,
            "custom_validation": []
        }
    
    async def _generate_survey_analytics(
        self, survey_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate survey analytics"""
        return {
            "track_responses": True,
            "track_completion_rate": True,
            "track_abandonment": True,
            "export_responses": True,
            "generate_reports": True
        }
    
    async def _generate_gallery_layout(
        self, media_items: List[Dict[str, Any]], gallery_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate gallery layout"""
        return {
            "layout_type": gallery_config.get("layout_type", "grid"),
            "columns": gallery_config.get("columns", 3),
            "spacing": "medium",
            "thumbnail_size": "medium",
            "lightbox_enabled": True
        }
    
    async def _generate_gallery_interactions(
        self, gallery_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate gallery interactions"""
        return {
            "click_to_expand": True,
            "swipe_navigation": True,
            "keyboard_navigation": True,
            "zoom_functionality": True,
            "fullscreen_mode": True
        }
    
    async def _generate_gallery_styling(
        self, gallery_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate gallery styling"""
        return {
            "theme": gallery_config.get("theme", "modern"),
            "border_radius": "8px",
            "shadow": "subtle",
            "hover_effects": True,
            "loading_animation": True
        }
    
    async def _generate_gallery_analytics(
        self, gallery_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate gallery analytics"""
        return {
            "track_views": True,
            "track_clicks": True,
            "track_time_spent": True,
            "track_zoom_usage": True,
            "export_analytics": True
        }
    
    def _create_widget_content_prompt(
        self, content_piece: ShakesContentPiece, widget_type: str, widget_config: Dict[str, Any], target_audience: str
    ) -> str:
        """Create prompt for widget content"""
        return f"""
        Create interactive {widget_type} widget content for this content:
        
        Content: {content_piece.title}
        Content Text: {content_piece.content}
        Widget Type: {widget_type}
        Widget Config: {widget_config}
        Target Audience: {target_audience}
        
        Create engaging, interactive content that enhances the user experience.
        """
    
    def _create_widget_code_prompt(
        self, widget_type: str, widget_content: Dict[str, Any], widget_config: Dict[str, Any]
    ) -> str:
        """Create prompt for widget code"""
        return f"""
        Generate {widget_type} widget code:
        
        Widget Type: {widget_type}
        Widget Content: {widget_content}
        Widget Config: {widget_config}
        
        Generate clean, responsive HTML/CSS/JavaScript code for the widget.
        """
    
    def _create_quiz_question_prompt(
        self, content_piece: ShakesContentPiece, quiz_config: Dict[str, Any], question_number: int
    ) -> str:
        """Create prompt for quiz question"""
        return f"""
        Create quiz question {question_number} based on this content:
        
        Content: {content_piece.title}
        Content Text: {content_piece.content}
        Quiz Config: {quiz_config}
        
        Create an engaging, educational question with multiple choice answers.
        """
    
    def _create_poll_content_prompt(
        self, content_piece: ShakesContentPiece, poll_config: Dict[str, Any], poll_options: List[str]
    ) -> str:
        """Create prompt for poll content"""
        return f"""
        Create poll content based on this content:
        
        Content: {content_piece.title}
        Content Text: {content_piece.content}
        Poll Config: {poll_config}
        Poll Options: {poll_options}
        
        Create engaging poll content that encourages participation.
        """
    
    def _create_survey_content_prompt(
        self, content_piece: ShakesContentPiece, survey_config: Dict[str, Any], survey_questions: List[Dict[str, Any]]
    ) -> str:
        """Create prompt for survey content"""
        return f"""
        Create survey content based on this content:
        
        Content: {content_piece.title}
        Content Text: {content_piece.content}
        Survey Config: {survey_config}
        Survey Questions: {survey_questions}
        
        Create comprehensive survey content that gathers valuable feedback.
        """
