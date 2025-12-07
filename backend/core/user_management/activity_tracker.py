import json
import time
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

class ActivityType(Enum):
    """Types of user activities that can be tracked."""
    LOGIN = "login"
    LOGOUT = "logout"
    PROFILE_UPDATE = "profile_update"
    TASK_CREATE = "task_create"
    TASK_UPDATE = "task_update"
    TASK_DELETE = "task_delete"
    AGENT_CREATE = "agent_create"
    AGENT_UPDATE = "agent_update"
    AGENT_DELETE = "agent_delete"
    INTEGRATION_ADD = "integration_add"
    INTEGRATION_REMOVE = "integration_remove"
    PLATFORM_CONNECT = "platform_connect"
    PLATFORM_DISCONNECT = "platform_disconnect"
    BILLING_UPDATE = "billing_update"
    SETTINGS_CHANGE = "settings_change"
    SEARCH_PERFORMED = "search_performed"
    FILE_UPLOAD = "file_upload"
    FILE_DOWNLOAD = "file_download"
    API_CALL = "api_call"
    CUSTOM = "custom"

@dataclass
class ActivityEvent:
    """A single activity event."""
    id: str
    user_id: str
    activity_type: ActivityType
    timestamp: datetime
    description: str
    metadata: Dict[str, Any]
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    duration: Optional[float] = None
    success: bool = True
    error_message: Optional[str] = None

@dataclass
class ActivitySummary:
    """Summary statistics for user activity."""
    total_activities: int
    unique_days: int
    most_active_day: str
    most_common_activity: str
    average_daily_activities: float
    last_activity: str
    activity_breakdown: Dict[str, int]

class ActivityTracker:
    """Tracks and analyzes user activities."""
    
    def __init__(self, retention_days: int = 90, max_events_per_user: int = 10000):
        self.retention_days = retention_days
        self.max_events_per_user = max_events_per_user
        self.activities: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_events_per_user))
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self._cleanup_task = None
        self._initialized = False

    async def initialize(self):
        """Start background cleanup loop inside the running event loop."""
        if self._initialized:
            return
        self._start_cleanup_task()
        self._initialized = True
    
    def _start_cleanup_task(self):
        """Start the background cleanup task."""
        import asyncio
        
        async def cleanup_loop():
            while True:
                try:
                    await asyncio.sleep(3600)  # Run every hour
                    self._cleanup_old_activities()
                except Exception as e:
                    logger.error(f"Error in activity cleanup: {e}")
        
        try:
            loop = asyncio.get_running_loop()
            self._cleanup_task = loop.create_task(cleanup_loop())
        except RuntimeError:
            # If no running loop, don't start now; initialize() will start when called from running loop
            logger.warning("No running loop, cleanup task not started.")

    async def shutdown(self):
        """Cancel background cleanup task during shutdown."""
        try:
            if self._cleanup_task:
                self._cleanup_task.cancel()
                import asyncio
                try:
                    await self._cleanup_task
                except asyncio.CancelledError:
                    pass
                self._cleanup_task = None
        except Exception as e:
            logger.error(f"Error shutting down activity tracker: {e}")
    
    def _cleanup_old_activities(self):
        """Remove activities older than retention period."""
        cutoff_time = datetime.utcnow() - timedelta(days=self.retention_days)
        
        for user_id, activities in self.activities.items():
            # Remove old activities
            while activities and activities[0].timestamp < cutoff_time:
                activities.popleft()
    
    def _generate_activity_id(self, user_id: str, timestamp: datetime) -> str:
        """Generate a unique activity ID."""
        import hashlib
        data = f"{user_id}:{timestamp.isoformat()}:{time.time()}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def track_activity(
        self,
        user_id: str,
        activity_type: ActivityType,
        description: str,
        metadata: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None,
        duration: Optional[float] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> str:
        """
        Track a user activity.
        
        Args:
            user_id: ID of the user
            activity_type: Type of activity
            description: Human-readable description
            metadata: Additional activity data
            ip_address: IP address of the user
            user_agent: User agent string
            session_id: Session identifier
            duration: Duration of the activity in seconds
            success: Whether the activity was successful
            error_message: Error message if activity failed
            
        Returns:
            Activity ID
        """
        try:
            activity_id = self._generate_activity_id(user_id, datetime.utcnow())
            
            event = ActivityEvent(
                id=activity_id,
                user_id=user_id,
                activity_type=activity_type,
                timestamp=datetime.utcnow(),
                description=description,
                metadata=metadata or {},
                ip_address=ip_address,
                user_agent=user_agent,
                session_id=session_id,
                duration=duration,
                success=success,
                error_message=error_message
            )
            
            self.activities[user_id].append(event)
            
            logger.debug(f"Tracked activity: {activity_type.value} for user {user_id}")
            return activity_id
            
        except Exception as e:
            logger.error(f"Failed to track activity: {e}")
            raise
    
    def get_user_activities(
        self,
        user_id: str,
        limit: int = 50,
        activity_type: Optional[ActivityType] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[ActivityEvent]:
        """
        Get activities for a specific user.
        
        Args:
            user_id: ID of the user
            limit: Maximum number of activities to return
            activity_type: Filter by activity type
            start_date: Start date filter
            end_date: End date filter
            
        Returns:
            List of ActivityEvent objects
        """
        try:
            if user_id not in self.activities:
                return []
            
            activities = list(self.activities[user_id])
            
            # Apply filters
            if activity_type:
                activities = [a for a in activities if a.activity_type == activity_type]
            
            if start_date:
                activities = [a for a in activities if a.timestamp >= start_date]
            
            if end_date:
                activities = [a for a in activities if a.timestamp <= end_date]
            
            # Sort by timestamp (newest first) and limit
            activities.sort(key=lambda x: x.timestamp, reverse=True)
            return activities[:limit]
            
        except Exception as e:
            logger.error(f"Failed to get user activities: {e}")
            return []
    
    def get_activity_summary(
        self,
        user_id: str,
        days: int = 30
    ) -> Optional[ActivitySummary]:
        """
        Get activity summary for a user.
        
        Args:
            user_id: ID of the user
            days: Number of days to analyze
            
        Returns:
            ActivitySummary object or None if no data
        """
        try:
            if user_id not in self.activities:
                return None
            
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            activities = [a for a in self.activities[user_id] if a.timestamp >= cutoff_date]
            
            if not activities:
                return None
            
            # Calculate statistics
            total_activities = len(activities)
            
            # Count activities by day
            daily_counts = defaultdict(int)
            for activity in activities:
                day_key = activity.timestamp.strftime("%Y-%m-%d")
                daily_counts[day_key] += 1
            
            unique_days = len(daily_counts)
            most_active_day = max(daily_counts.items(), key=lambda x: x[1])[0] if daily_counts else ""
            average_daily_activities = total_activities / unique_days if unique_days > 0 else 0
            
            # Count activities by type
            activity_counts = defaultdict(int)
            for activity in activities:
                activity_counts[activity.activity_type.value] += 1
            
            most_common_activity = max(activity_counts.items(), key=lambda x: x[1])[0] if activity_counts else ""
            last_activity = max(activities, key=lambda x: x.timestamp).timestamp.isoformat()
            
            return ActivitySummary(
                total_activities=total_activities,
                unique_days=unique_days,
                most_active_day=most_active_day,
                most_common_activity=most_common_activity,
                average_daily_activities=average_daily_activities,
                last_activity=last_activity,
                activity_breakdown=dict(activity_counts)
            )
            
        except Exception as e:
            logger.error(f"Failed to get activity summary: {e}")
            return None
    
    def start_session(self, user_id: str, session_id: str, ip_address: Optional[str] = None, user_agent: Optional[str] = None):
        """
        Start tracking a user session.
        
        Args:
            user_id: ID of the user
            session_id: Session identifier
            ip_address: IP address
            user_agent: User agent string
        """
        try:
            self.sessions[session_id] = {
                "user_id": user_id,
                "start_time": datetime.utcnow(),
                "ip_address": ip_address,
                "user_agent": user_agent,
                "activities": []
            }
            
            logger.debug(f"Started session {session_id} for user {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to start session: {e}")
    
    def end_session(self, session_id: str):
        """
        End tracking a user session.
        
        Args:
            session_id: Session identifier
        """
        try:
            if session_id in self.sessions:
                session = self.sessions[session_id]
                end_time = datetime.utcnow()
                duration = (end_time - session["start_time"]).total_seconds()
                
                # Track session end activity
                self.track_activity(
                    user_id=session["user_id"],
                    activity_type=ActivityType.LOGOUT,
                    description="Session ended",
                    metadata={
                        "session_id": session_id,
                        "session_duration": duration,
                        "activities_count": len(session["activities"])
                    },
                    ip_address=session["ip_address"],
                    user_agent=session["user_agent"],
                    session_id=session_id,
                    duration=duration
                )
                
                del self.sessions[session_id]
                logger.debug(f"Ended session {session_id}")
            
        except Exception as e:
            logger.error(f"Failed to end session: {e}")
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session information or None if not found
        """
        try:
            if session_id not in self.sessions:
                return None
            
            session = self.sessions[session_id]
            current_time = datetime.utcnow()
            duration = (current_time - session["start_time"]).total_seconds()
            
            return {
                "session_id": session_id,
                "user_id": session["user_id"],
                "start_time": session["start_time"].isoformat(),
                "duration_seconds": duration,
                "ip_address": session["ip_address"],
                "user_agent": session["user_agent"],
                "activities_count": len(session["activities"])
            }
            
        except Exception as e:
            logger.error(f"Failed to get session info: {e}")
            return None
    
    def get_user_sessions(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent sessions for a user.
        
        Args:
            user_id: ID of the user
            limit: Maximum number of sessions to return
            
        Returns:
            List of session information
        """
        try:
            user_sessions = []
            
            for session_id, session in self.sessions.items():
                if session["user_id"] == user_id:
                    current_time = datetime.utcnow()
                    duration = (current_time - session["start_time"]).total_seconds()
                    
                    user_sessions.append({
                        "session_id": session_id,
                        "start_time": session["start_time"].isoformat(),
                        "duration_seconds": duration,
                        "ip_address": session["ip_address"],
                        "user_agent": session["user_agent"],
                        "activities_count": len(session["activities"])
                    })
            
            # Sort by start time (newest first) and limit
            user_sessions.sort(key=lambda x: x["start_time"], reverse=True)
            return user_sessions[:limit]
            
        except Exception as e:
            logger.error(f"Failed to get user sessions: {e}")
            return []
    
    def get_activity_trends(
        self,
        user_id: str,
        days: int = 30,
        interval_hours: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Get activity trends over time.
        
        Args:
            user_id: ID of the user
            days: Number of days to analyze
            interval_hours: Time interval in hours
            
        Returns:
            List of trend data points
        """
        try:
            if user_id not in self.activities:
                return []
            
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            activities = [a for a in self.activities[user_id] if a.timestamp >= cutoff_date]
            
            if not activities:
                return []
            
            # Group activities by interval
            intervals = defaultdict(list)
            interval_seconds = interval_hours * 3600
            
            for activity in activities:
                interval_start = activity.timestamp.replace(
                    hour=activity.timestamp.hour - (activity.timestamp.hour % interval_hours),
                    minute=0,
                    second=0,
                    microsecond=0
                )
                intervals[interval_start].append(activity)
            
            # Calculate statistics for each interval
            trends = []
            for interval_start, interval_activities in sorted(intervals.items()):
                activity_types = [a.activity_type.value for a in interval_activities]
                success_count = sum(1 for a in interval_activities if a.success)
                
                trends.append({
                    "timestamp": interval_start.isoformat(),
                    "activities_count": len(interval_activities),
                    "success_count": success_count,
                    "failure_count": len(interval_activities) - success_count,
                    "activity_types": list(set(activity_types)),
                    "unique_types_count": len(set(activity_types))
                })
            
            return trends
            
        except Exception as e:
            logger.error(f"Failed to get activity trends: {e}")
            return []
    
    def export_activities(
        self,
        user_id: str,
        format: str = "json",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> str:
        """
        Export user activities.
        
        Args:
            user_id: ID of the user
            format: Export format (json, csv)
            start_date: Start date filter
            end_date: End date filter
            
        Returns:
            Exported data as string
        """
        try:
            activities = self.get_user_activities(user_id, limit=10000)
            
            # Apply date filters
            if start_date:
                activities = [a for a in activities if a.timestamp >= start_date]
            if end_date:
                activities = [a for a in activities if a.timestamp <= end_date]
            
            if format.lower() == "json":
                export_data = {
                    "user_id": user_id,
                    "exported_at": datetime.utcnow().isoformat(),
                    "activities": [
                        {
                            "id": activity.id,
                            "activity_type": activity.activity_type.value,
                            "timestamp": activity.timestamp.isoformat(),
                            "description": activity.description,
                            "metadata": activity.metadata,
                            "ip_address": activity.ip_address,
                            "user_agent": activity.user_agent,
                            "session_id": activity.session_id,
                            "duration": activity.duration,
                            "success": activity.success,
                            "error_message": activity.error_message
                        }
                        for activity in activities
                    ]
                }
                return json.dumps(export_data, indent=2)
            
            elif format.lower() == "csv":
                csv_lines = ["id,activity_type,timestamp,description,success,duration,ip_address"]
                
                for activity in activities:
                    csv_lines.append(
                        f"{activity.id},{activity.activity_type.value},{activity.timestamp.isoformat()},"
                        f"\"{activity.description}\",{activity.success},{activity.duration or ''},"
                        f"{activity.ip_address or ''}"
                    )
                
                return "\n".join(csv_lines)
            
            else:
                raise ValueError(f"Unsupported export format: {format}")
                
        except Exception as e:
            logger.error(f"Failed to export activities: {e}")
            return ""
    
    def clear_activities(self, user_id: Optional[str] = None):
        """
        Clear activity data.
        
        Args:
            user_id: Specific user to clear, or None to clear all
        """
        try:
            if user_id:
                if user_id in self.activities:
                    self.activities[user_id].clear()
                    logger.info(f"Cleared activities for user {user_id}")
            else:
                self.activities.clear()
                self.sessions.clear()
                logger.info("Cleared all activities")
                
        except Exception as e:
            logger.error(f"Failed to clear activities: {e}")

# Global instance
activity_tracker = ActivityTracker()

async def get_activity_tracker() -> ActivityTracker:
    """Async getter that ensures the activity tracker is initialized."""
    global activity_tracker
    if not activity_tracker._initialized:
        await activity_tracker.initialize()
    return activity_tracker
