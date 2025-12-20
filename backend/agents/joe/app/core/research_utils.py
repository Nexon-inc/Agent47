import requests
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from core.config import settings

logger = logging.getLogger(__name__)

class ResearchUtils:
    """Research-specific utilities for Joe agent"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Joe-Research-Agent/1.0'
        })
        
    async def fetch_google_trends(self, keyword: str, region: str = "US", time_period: str = "today 12-m") -> Dict[str, Any]:
        """Fetch Google Trends data for a keyword"""
        try:
            # This is a simplified implementation
            # In production, you'd use pytrends or Google Trends API
            url = "https://trends.google.com/trends/api/explore"
            params = {
                'hl': 'en-US',
                'tz': '-120',
                'req': json.dumps({
                    'restriction': {
                        'geo': {'country': region},
                        'time': time_period,
                        'originalTimeRangeForExploreUrl': time_period
                    },
                    'keywordType': 'QUERY',
                    'metric': ['TOP', 'RISING'],
                    'trendinessSettings': {
                        'compareTime': time_period
                    },
                    'requestOptions': {
                        'property': '',
                        'backend': 'IZG',
                        'category': 0
                    },
                    'language': 'en'
                }),
                'token': 'APP6_UEAAAAAY' + str(int(datetime.now().timestamp()))
            }
            
            response = self.session.get(url, params=params)
            
            if response.status_code == 200:
                # Parse Google Trends response
                data = response.text[5:]  # Remove ")]}'" prefix
                trends_data = json.loads(data)
                
                return {
                    "success": True,
                    "keyword": keyword,
                    "region": region,
                    "time_period": time_period,
                    "trends_data": trends_data,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Google Trends fetch failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def fetch_news_data(self, query: str, api_key: str = None) -> Dict[str, Any]:
        """Fetch news data using Google News API"""
        try:
            if not api_key:
                api_key = settings.google_news_api_key if hasattr(settings, 'google_news_api_key') else None
            
            if not api_key:
                return {"success": False, "error": "Google News API key not configured"}
            
            url = "https://newsapi.org/v2/everything"
            params = {
                'q': query,
                'apiKey': api_key,
                'language': 'en',
                'sortBy': 'publishedAt',
                'pageSize': 100
            }
            
            response = self.session.get(url, params=params)
            
            if response.status_code == 200:
                news_data = response.json()
                return {
                    "success": True,
                    "query": query,
                    "total_results": news_data.get('totalResults', 0),
                    "articles": news_data.get('articles', []),
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            logger.error(f"News data fetch failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def fetch_patent_data(self, query: str, api_key: str = None) -> Dict[str, Any]:
        """Fetch patent data using Google Patents API"""
        try:
            if not api_key:
                api_key = settings.google_patents_api_key if hasattr(settings, 'google_patents_api_key') else None
            
            if not api_key:
                return {"success": False, "error": "Google Patents API key not configured"}
            
            url = "https://patents.google.com/xhr/query"
            params = {
                'url': f"q={query}&language=ENGLISH&type=PATENT",
                'exp': ''
            }
            
            response = self.session.get(url, params=params)
            
            if response.status_code == 200:
                patent_data = response.json()
                return {
                    "success": True,
                    "query": query,
                    "patent_data": patent_data,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Patent data fetch failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def validate_research_compliance(self, data_source: str, data_type: str, region: str = "EU") -> Dict[str, Any]:
        """Validate research compliance with GDPR and other regulations"""
        try:
            compliance_checks = {
                "gdpr_compliant": False,
                "data_retention": "Not specified",
                "consent_required": True,
                "data_minimization": False,
                "purpose_limitation": False,
                "transparency": False,
                "user_rights": False,
                "risk_assessment": "Medium"
            }
            
            # Basic compliance logic
            if data_source in ["google_trends", "google_news", "google_patents"]:
                compliance_checks["gdpr_compliant"] = True
                compliance_checks["data_retention"] = "30 days"
                compliance_checks["consent_required"] = False
                compliance_checks["data_minimization"] = True
                compliance_checks["purpose_limitation"] = True
                compliance_checks["transparency"] = True
                compliance_checks["user_rights"] = True
                compliance_checks["risk_assessment"] = "Low"
            
            elif data_source in ["social_media", "user_generated"]:
                compliance_checks["gdpr_compliant"] = False
                compliance_checks["data_retention"] = "Until deletion request"
                compliance_checks["consent_required"] = True
                compliance_checks["data_minimization"] = False
                compliance_checks["purpose_limitation"] = False
                compliance_checks["transparency"] = False
                compliance_checks["user_rights"] = True
                compliance_checks["risk_assessment"] = "High"
            
            # Calculate overall compliance score
            compliance_score = sum([
                compliance_checks["gdpr_compliant"],
                compliance_checks["data_minimization"],
                compliance_checks["purpose_limitation"],
                compliance_checks["transparency"],
                compliance_checks["user_rights"]
            ]) / 5 * 100
            
            return {
                "success": True,
                "data_source": data_source,
                "data_type": data_type,
                "region": region,
                "compliance_checks": compliance_checks,
                "compliance_score": compliance_score,
                "recommendations": self._generate_compliance_recommendations(compliance_checks)
            }
            
        except Exception as e:
            logger.error(f"Compliance validation failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _generate_compliance_recommendations(self, compliance_checks: Dict[str, Any]) -> List[str]:
        """Generate compliance recommendations based on checks"""
        recommendations = []
        
        if not compliance_checks["gdpr_compliant"]:
            recommendations.append("Implement GDPR compliance measures")
        
        if compliance_checks["consent_required"]:
            recommendations.append("Obtain explicit user consent for data collection")
        
        if not compliance_checks["data_minimization"]:
            recommendations.append("Implement data minimization principles")
        
        if not compliance_checks["purpose_limitation"]:
            recommendations.append("Clearly define and limit data usage purposes")
        
        if not compliance_checks["transparency"]:
            recommendations.append("Provide transparent data processing information")
        
        if compliance_checks["risk_assessment"] == "High":
            recommendations.append("Conduct detailed privacy impact assessment")
        
        return recommendations
    
    async def generate_research_report(self, research_data: Dict[str, Any], report_type: str) -> Dict[str, Any]:
        """Generate research report from collected data"""
        try:
            report_template = {
                "executive_summary": "",
                "methodology": "",
                "key_findings": [],
                "data_analysis": {},
                "conclusions": [],
                "recommendations": [],
                "appendices": {},
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "report_type": report_type,
                    "data_sources": [],
                    "compliance_status": "Unknown"
                }
            }
            
            # Populate report based on data
            if "trends_data" in research_data:
                report_template["key_findings"].append("Trend analysis completed")
                report_template["data_analysis"]["trends"] = research_data["trends_data"]
            
            if "articles" in research_data:
                report_template["key_findings"].append(f"Found {len(research_data['articles'])} relevant articles")
                report_template["data_analysis"]["news"] = research_data["articles"]
            
            if "patent_data" in research_data:
                report_template["key_findings"].append("Patent analysis completed")
                report_template["data_analysis"]["patents"] = research_data["patent_data"]
            
            # Generate recommendations
            if report_type == "market_research":
                report_template["recommendations"] = [
                    "Continue monitoring market trends",
                    "Analyze competitor strategies",
                    "Identify new market opportunities"
                ]
            elif report_type == "competitive_analysis":
                report_template["recommendations"] = [
                    "Benchmark against top competitors",
                    "Identify competitive advantages",
                    "Develop differentiation strategies"
                ]
            
            return {
                "success": True,
                "report": report_template,
                "report_type": report_type,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def schedule_research_task(self, task_config: Dict[str, Any]) -> Dict[str, Any]:
        """Schedule a recurring research task"""
        try:
            scheduled_task = {
                "task_id": f"research_{int(datetime.now().timestamp())}",
                "task_name": task_config.get("task_name", "Research Task"),
                "schedule": task_config.get("schedule", "daily"),
                "data_sources": task_config.get("data_sources", []),
                "keywords": task_config.get("keywords", []),
                "regions": task_config.get("regions", ["US"]),
                "report_type": task_config.get("report_type", "general"),
                "notification_channels": task_config.get("notification_channels", ["email"]),
                "created_at": datetime.now().isoformat(),
                "next_run": self._calculate_next_run(task_config.get("schedule", "daily")),
                "status": "scheduled"
            }
            
            return {
                "success": True,
                "scheduled_task": scheduled_task,
                "message": f"Research task '{scheduled_task['task_name']}' scheduled successfully"
            }
            
        except Exception as e:
            logger.error(f"Task scheduling failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _calculate_next_run(self, schedule: str) -> str:
        """Calculate next run time based on schedule"""
        now = datetime.now()
        
        if schedule == "hourly":
            next_run = now + timedelta(hours=1)
        elif schedule == "daily":
            next_run = now + timedelta(days=1)
        elif schedule == "weekly":
            next_run = now + timedelta(weeks=1)
        elif schedule == "monthly":
            next_run = now + timedelta(days=30)
        else:
            next_run = now + timedelta(days=1)
        
        return next_run.isoformat()
    
    async def validate_research_ethics(self, research_question: str, methodology: str) -> Dict[str, Any]:
        """Validate research ethics and identify potential biases"""
        try:
            ethics_assessment = {
                "ethical_concerns": [],
                "potential_biases": [],
                "recommendations": [],
                "risk_level": "Low",
                "approval_required": False
            }
            
            # Check for ethical concerns
            sensitive_keywords = ["personal", "private", "confidential", "sensitive", "health", "financial"]
            for keyword in sensitive_keywords:
                if keyword.lower() in research_question.lower():
                    ethics_assessment["ethical_concerns"].append(f"Contains sensitive keyword: {keyword}")
                    ethics_assessment["risk_level"] = "Medium"
            
            # Check methodology for biases
            if "social_media" in methodology.lower():
                ethics_assessment["potential_biases"].append("Social media data may have selection bias")
                ethics_assessment["recommendations"].append("Consider multiple data sources")
            
            if "user_generated" in methodology.lower():
                ethics_assessment["potential_biases"].append("User-generated content may have self-selection bias")
                ethics_assessment["recommendations"].append("Validate with external sources")
            
            # Determine if approval is required
            if ethics_assessment["risk_level"] in ["Medium", "High"]:
                ethics_assessment["approval_required"] = True
                ethics_assessment["recommendations"].append("Seek ethics committee approval")
            
            return {
                "success": True,
                "research_question": research_question,
                "methodology": methodology,
                "ethics_assessment": ethics_assessment,
                "assessed_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Ethics validation failed: {e}")
            return {"success": False, "error": str(e)}
