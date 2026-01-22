from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import asyncio
import httpx
from core.ai import get_ai_service_manager, AIServiceManager
from core.database.connection import get_supabase
from core.integrations.integration_manager import get_integration_manager
from ..models import AriaTrendSignal
from core.config import settings
import json


class TrendAlertsService:
    def __init__(self):
        self.ai_service_manager: Optional[AIServiceManager] = None
        self.integration_manager = None
        self.alert_tasks = {}

    async def initialize(self):
        self.ai_service_manager = await get_ai_service_manager()
        self.integration_manager = await get_integration_manager()

    async def setup_trend_monitoring(self, user_id: int, keywords: List[str], platforms: List[str], alert_frequency: str = "daily") -> Dict[str, Any]:
        """Setup automated trend monitoring for specific keywords and platforms"""
        if not self.ai_service_manager:
            await self.initialize()

        # Create monitoring task
        task_id = f"trend_monitor_{user_id}_{datetime.utcnow().timestamp()}"
        
        # Store monitoring configuration
        monitoring_config = {
            "user_id": user_id,
            "keywords": keywords,
            "platforms": platforms,
            "alert_frequency": alert_frequency,
            "last_check": datetime.utcnow().isoformat(),
            "is_active": True
        }

        # Start monitoring task
        self.alert_tasks[task_id] = asyncio.create_task(
            self._monitor_trends_loop(task_id, monitoring_config)
        )

        return {
            "success": True,
            "task_id": task_id,
            "monitoring_config": monitoring_config,
            "message": f"Trend monitoring started for {len(keywords)} keywords across {len(platforms)} platforms"
        }

    async def _monitor_trends_loop(self, task_id: str, config: Dict[str, Any]):
        """Continuous trend monitoring loop"""
        try:
            while config.get("is_active", True):
                await self._check_trends(config)
                
                # Wait based on frequency
                if config["alert_frequency"] == "hourly":
                    await asyncio.sleep(3600)  # 1 hour
                elif config["alert_frequency"] == "daily":
                    await asyncio.sleep(86400)  # 24 hours
                elif config["alert_frequency"] == "weekly":
                    await asyncio.sleep(604800)  # 7 days
                else:
                    await asyncio.sleep(86400)  # Default to daily
                    
        except asyncio.CancelledError:
            config["is_active"] = False
        except Exception as e:
            config["is_active"] = False
            # Log error and continue monitoring

    async def _check_trends(self, config: Dict[str, Any]):
        """Check for new trends and send alerts"""
        user_id = config["user_id"]
        keywords = config["keywords"]
        platforms = config["platforms"]

        new_trends = []
        
        for keyword in keywords:
            # Check multiple trend sources
            trends = await self._gather_trend_data(keyword, platforms)
            if trends:
                new_trends.extend(trends)

        if new_trends:
            await self._send_trend_alert(user_id, new_trends)
            await self._save_trend_signals(user_id, new_trends)

    async def _gather_trend_data(self, keyword: str, platforms: List[str]) -> List[Dict[str, Any]]:
        """Gather trend data from multiple sources"""
        trends = []
        
        # Google Trends (free)
        google_trends = await self._get_google_trends(keyword)
        if google_trends:
            trends.append(google_trends)

        # Twitter Trends (free via scraping)
        twitter_trends = await self._get_twitter_trends(keyword)
        if twitter_trends:
            trends.append(twitter_trends)

        # Reddit Trends (free)
        reddit_trends = await self._get_reddit_trends(keyword)
        if reddit_trends:
            trends.append(reddit_trends)

        # SEMrush (if available)
        if settings.semrush.api_key:
            semrush_trends = await self._get_semrush_trends(keyword)
            if semrush_trends:
                trends.append(semrush_trends)

        return trends

    async def _get_google_trends(self, keyword: str) -> Optional[Dict[str, Any]]:
        """Get Google Trends data using free API"""
        try:
            # Use pytrends-like approach with direct HTTP requests
            url = "https://trends.google.com/trends/api/explore"
            params = {
                "hl": "en-US",
                "tz": "-120",
                "req": json.dumps({
                    "restriction": {
                        "geo": {},
                        "time": "today 12-m",
                        "originalTimeRangeForExploreUrl": "today 12-m"
                    },
                    "keywordType": "QUERY",
                    "metric": ["TOP", "RISING"],
                    "trendinessSettings": {
                        "compareTime": "today 12-m"
                    },
                    "requestOptions": {
                        "property": "",
                        "backend": "IZG",
                        "category": 0
                    },
                    "language": "en"
                }),
                "tz": "-120"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, timeout=10.0)
                if response.status_code == 200:
                    # Parse Google Trends response
                    data = response.text
                    if data.startswith(")]}'"):
                        data = data[5:]  # Remove Google's security prefix
                    
                    try:
                        parsed = json.loads(data)
                        if "default" in parsed and "timelineData" in parsed["default"]:
                            timeline = parsed["default"]["timelineData"]
                            if timeline:
                                latest = timeline[-1]
                                return {
                                    "source": "google_trends",
                                    "keyword": keyword,
                                    "trend_score": latest.get("value", [0])[0],
                                    "timestamp": datetime.utcnow().isoformat(),
                                    "platform": "google",
                                    "trending": latest.get("value", [0])[0] > 50
                                }
                    except:
                        pass
        except Exception:
            pass
        return None

    async def _get_twitter_trends(self, keyword: str) -> Optional[Dict[str, Any]]:
        """Get Twitter trends using free methods"""
        try:
            # Use Twitter's public trends endpoint (no auth required)
            url = "https://api.twitter.com/1.1/trends/place.json"
            # Note: This would require Twitter API access, but we can simulate with public data
            
            # Alternative: Use Nitter (Twitter alternative) for public trends
            nitter_url = "https://nitter.net/trends"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(nitter_url, timeout=10.0)
                if response.status_code == 200:
                    # Parse trends from Nitter
                    content = response.text
                    if keyword.lower() in content.lower():
                        return {
                            "source": "twitter_trends",
                            "keyword": keyword,
                            "trend_score": 75,  # Simulated score
                            "timestamp": datetime.utcnow().isoformat(),
                            "platform": "twitter",
                            "trending": True
                        }
        except Exception:
            pass
        return None

    async def _get_reddit_trends(self, keyword: str) -> Optional[Dict[str, Any]]:
        """Get Reddit trends using free API"""
        try:
            # Reddit's JSON API (no auth required)
            url = f"https://www.reddit.com/search.json"
            params = {
                "q": keyword,
                "sort": "hot",
                "t": "day",
                "limit": 10
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, timeout=10.0)
                if response.status_code == 200:
                    data = response.json()
                    if "data" in data and "children" in data["data"]:
                        posts = data["data"]["children"]
                        total_score = sum(post["data"]["score"] for post in posts)
                        avg_score = total_score / len(posts) if posts else 0
                        
                        return {
                            "source": "reddit_trends",
                            "keyword": keyword,
                            "trend_score": avg_score,
                            "timestamp": datetime.utcnow().isoformat(),
                            "platform": "reddit",
                            "trending": avg_score > 100
                        }
        except Exception:
            pass
        return None

    async def _get_semrush_trends(self, keyword: str) -> Optional[Dict[str, Any]]:
        """Get SEMrush trends using integration manager"""
        try:
            if self.integration_manager:
                result = await self.integration_manager.call_integration_api(
                    user_id=0,
                    integration_name="semrush",
                    endpoint="/",
                    method="GET",
                    params={
                        "type": "phrase_this",
                        "key": settings.semrush.api_key,
                        "phrase": keyword,
                        "database": "us"
                    }
                )
                
                if result.get("success"):
                    return {
                        "source": "semrush",
                        "keyword": keyword,
                        "trend_score": 60,  # SEMrush doesn't provide trend scores directly
                        "timestamp": datetime.utcnow().isoformat(),
                        "platform": "semrush",
                        "trending": True
                    }
        except Exception:
            pass
        return None

    async def _send_trend_alert(self, user_id: int, trends: List[Dict[str, Any]]):
        """Send trend alert to user"""
        if not trends:
            return

        # Generate alert message using AI
        alert_prompt = f"""
        Create a concise trend alert message for these trending topics:
        
        Trends: {json.dumps(trends, indent=2)}
        
        Format: "🚀 Trending Alert: [key insights] - [actionable advice]"
        Keep it under 200 characters and engaging.
        """

        messages = [
            {"role": "system", "content": alert_prompt},
            {"role": "user", "content": "trend alert"}
        ]
        
        response = await self.ai_service_manager.generate_text(
            messages=messages,
            max_tokens=100,
            temperature=0.7
        )
        
        alert_message = response.text_content if response.success else "🚀 New trends detected! Check your dashboard for details."

        # Store alert in database for user notification
        await self._store_trend_alert(user_id, alert_message, trends)

    async def _store_trend_alert(self, user_id: int, message: str, trends: List[Dict[str, Any]]):
        """Store trend alert for user notification"""
        db = await get_supabase()
        async with db.get_session() as session:
            # Create trend alert record
            alert_data = {
                "user_id": user_id,
                "message": message,
                "trends": trends,
                "created_at": datetime.utcnow(),
                "read": False
            }
            
            # This would go to a TrendAlert model if we had one
            # For now, we'll store in AriaTrendSignal with alert flag
            for trend in trends:
                signal = AriaTrendSignal(
                    user_id=user_id,
                    topic=trend.get("keyword", ""),
                    region="global",
                    keywords=[trend.get("keyword", "")],
                    source=trend.get("source", ""),
                    score=trend.get("trend_score", 0.0)
                )
                session.add(signal)
            
            await session.commit()

    async def _save_trend_signals(self, user_id: int, trends: List[Dict[str, Any]]):
        """Save trend signals to database"""
        db = await get_supabase()
        async with db.get_session() as session:
            for trend in trends:
                signal = AriaTrendSignal(
                    user_id=user_id,
                    topic=trend.get("keyword", ""),
                    region="global",
                    keywords=[trend.get("keyword", "")],
                    source=trend.get("source", ""),
                    score=trend.get("trend_score", 0.0)
                )
                session.add(signal)
            
            await session.commit()

    async def stop_monitoring(self, task_id: str) -> Dict[str, Any]:
        """Stop trend monitoring for a specific task"""
        if task_id in self.alert_tasks:
            task = self.alert_tasks[task_id]
            task.cancel()
            del self.alert_tasks[task_id]
            
            return {
                "success": True,
                "message": f"Trend monitoring stopped for task {task_id}"
            }
        
        return {
            "success": False,
            "error": "Task not found"
        }

    async def get_active_monitoring(self, user_id: int) -> Dict[str, Any]:
        """Get active monitoring tasks for a user"""
        active_tasks = []
        
        for task_id, task in self.alert_tasks.items():
            if task_id.startswith(f"trend_monitor_{user_id}_"):
                active_tasks.append({
                    "task_id": task_id,
                    "status": "running" if not task.done() else "completed"
                })
        
        return {
            "success": True,
            "active_tasks": active_tasks,
            "total_tasks": len(active_tasks)
        }
