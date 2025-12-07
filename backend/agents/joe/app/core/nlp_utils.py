import openai
import json
import re
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
import logging
from backend.core.config import settings
from backend.core.utils.nlp_utils import NLPUtils as CoreNLPUtils

logger = logging.getLogger(__name__)

class NLPUtils(CoreNLPUtils):
    """Extended NLP utilities for Joe research agent"""
    
    def __init__(self):
        super().__init__()
        self._research_model = "gpt-4-turbo"
        self._research_max_tokens = 4000
        self._research_temperature = 0.3
        
    async def analyze_sentiment(self, text: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Analyze sentiment of research data"""
        try:
            if not self._initialized:
                return {"success": False, "error": "NLP utilities not initialized"}
            
            system_prompt = """
            You are a research sentiment analysis expert. Analyze the sentiment of the given text.
            Return a JSON response with:
            - overall_sentiment: float between -1 (very negative) and 1 (very positive)
            - confidence: float between 0 and 1
            - key_emotions: list of detected emotions
            - sentiment_breakdown: detailed analysis
            """
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Analyze sentiment: {text}"}
            ]
            
            response = self.openai_client.chat.completions.create(
                model=self._research_model,
                messages=messages,
                max_tokens=self._research_max_tokens,
                temperature=self._research_temperature
            )
            
            if response.choices and response.choices[0].message.content:
                sentiment_data = json.loads(response.choices[0].message.content)
                return {
                    "success": True,
                    "sentiment": sentiment_data,
                    "raw_response": response.choices[0].message.content
                }
            else:
                return {"success": False, "error": "No response from OpenAI"}
                
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def extract_key_insights(self, text: str, research_type: str) -> Dict[str, Any]:
        """Extract key insights from research data"""
        try:
            if not self._initialized:
                return {"success": False, "error": "NLP utilities not initialized"}
            
            system_prompt = f"""
            You are a research analyst specializing in {research_type}. Extract key insights from the given text.
            Return a JSON response with:
            - main_findings: list of primary insights
            - trends: identified trends
            - opportunities: potential opportunities
            - risks: potential risks
            - recommendations: actionable recommendations
            - confidence_score: float between 0 and 1
            """
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Extract insights from: {text}"}
            ]
            
            response = self.openai_client.chat.completions.create(
                model=self._research_model,
                messages=messages,
                max_tokens=self._research_max_tokens,
                temperature=self._research_temperature
            )
            
            if response.choices and response.choices[0].message.content:
                insights_data = json.loads(response.choices[0].message.content)
                return {
                    "success": True,
                    "insights": insights_data,
                    "raw_response": response.choices[0].message.content
                }
            else:
                return {"success": False, "error": "No response from OpenAI"}
                
        except Exception as e:
            logger.error(f"Insight extraction failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def generate_research_summary(self, data: List[Dict[str, Any]], summary_type: str) -> Dict[str, Any]:
        """Generate research summary from multiple data sources"""
        try:
            if not self._initialized:
                return {"success": False, "error": "NLP utilities not initialized"}
            
            # Prepare data for summary
            data_text = "\n\n".join([str(item) for item in data])
            
            system_prompt = f"""
            You are a research analyst creating a {summary_type} summary. Generate a comprehensive summary from the provided data.
            Return a JSON response with:
            - executive_summary: brief overview
            - key_findings: main discoveries
            - methodology: approach used
            - conclusions: final conclusions
            - recommendations: next steps
            - data_sources: sources referenced
            """
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Generate {summary_type} summary from: {data_text}"}
            ]
            
            response = self.openai_client.chat.completions.create(
                model=self._research_model,
                messages=messages,
                max_tokens=self._research_max_tokens,
                temperature=self._research_temperature
            )
            
            if response.choices and response.choices[0].message.content:
                summary_data = json.loads(response.choices[0].message.content)
                return {
                    "success": True,
                    "summary": summary_data,
                    "raw_response": response.choices[0].message.content
                }
            else:
                return {"success": False, "error": "No response from OpenAI"}
                
        except Exception as e:
            logger.error(f"Summary generation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def analyze_competitor_data(self, competitor_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze competitor data and extract strategic insights"""
        try:
            if not self._initialized:
                return {"success": False, "error": "NLP utilities not initialized"}
            
            system_prompt = """
            You are a competitive intelligence analyst. Analyze the provided competitor data and extract strategic insights.
            Return a JSON response with:
            - strengths: competitor strengths
            - weaknesses: competitor weaknesses
            - opportunities: opportunities for your business
            - threats: potential threats
            - market_position: competitor's market position
            - strategic_recommendations: actionable recommendations
            - competitive_advantage: areas where you can gain advantage
            """
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Analyze competitor data: {json.dumps(competitor_data)}"}
            ]
            
            response = self.openai_client.chat.completions.create(
                model=self._research_model,
                messages=messages,
                max_tokens=self._research_max_tokens,
                temperature=self._research_temperature
            )
            
            if response.choices and response.choices[0].message.content:
                analysis_data = json.loads(response.choices[0].message.content)
                return {
                    "success": True,
                    "analysis": analysis_data,
                    "raw_response": response.choices[0].message.content
                }
            else:
                return {"success": False, "error": "No response from OpenAI"}
                
        except Exception as e:
            logger.error(f"Competitor analysis failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def generate_research_hypothesis(self, research_question: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate research hypotheses based on questions and context"""
        try:
            if not self._initialized:
                return {"success": False, "error": "NLP utilities not initialized"}
            
            system_prompt = """
            You are a research scientist. Generate testable hypotheses based on the research question and context.
            Return a JSON response with:
            - primary_hypothesis: main hypothesis to test
            - alternative_hypotheses: alternative explanations
            - null_hypothesis: null hypothesis
            - variables: key variables to measure
            - methodology_suggestions: suggested research methods
            - expected_outcomes: expected results
            - confidence_level: confidence in hypothesis
            """
            
            context_text = json.dumps(context) if context else "No additional context provided"
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Research question: {research_question}\nContext: {context_text}"}
            ]
            
            response = self.openai_client.chat.completions.create(
                model=self._research_model,
                messages=messages,
                max_tokens=self._research_max_tokens,
                temperature=self._research_temperature
            )
            
            if response.choices and response.choices[0].message.content:
                hypothesis_data = json.loads(response.choices[0].message.content)
                return {
                    "success": True,
                    "hypothesis": hypothesis_data,
                    "raw_response": response.choices[0].message.content
                }
            else:
                return {"success": False, "error": "No response from OpenAI"}
                
        except Exception as e:
            logger.error(f"Hypothesis generation failed: {e}")
            return {"success": False, "error": str(e)}
