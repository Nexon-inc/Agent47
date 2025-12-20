import re
import hashlib
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from sqlalchemy import text, inspect
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_database, DatabaseManager
from core.logs import get_logger, LoggerMixin
from core.config import get_settings

logger = get_logger(__name__)

class QueryType(Enum):
    SELECT = "select"
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"
    CREATE = "create"
    ALTER = "alter"
    DROP = "drop"

class QueryStatus(Enum):
    ACTIVE = "active"
    IDLE = "idle"
    IDLE_IN_TRANSACTION = "idle_in_transaction"
    LOCKED = "locked"

@dataclass
class QueryInfo:
    id: str
    query_text: str
    query_type: QueryType
    status: QueryStatus
    duration: float
    start_time: datetime
    user: str
    database: str
    client_addr: str
    application_name: str
    wait_event_type: Optional[str] = None
    wait_event: Optional[str] = None
    state: Optional[str] = None

@dataclass
class QueryAnalysis:
    id: str
    query_text: str
    execution_plan: Dict[str, Any]
    performance_metrics: Dict[str, Any]
    optimization_suggestions: List[str]
    analyzed_at: datetime = field(default_factory=datetime.utcnow)

class QueryAnalyzer:
    def __init__(self):
        self.config = get_settings()
        self.logger = get_logger(__name__)
        self.db = get_database()
    
    async def get_active_queries(self) -> List[QueryInfo]:
        """Get currently active database queries"""
        try:
            active_queries = await self.db.fetch_all("""
                SELECT 
                    pid,
                    query,
                    state,
                    query_start,
                    now() - query_start as duration,
                    usename,
                    datname,
                    client_addr,
                    application_name,
                    wait_event_type,
                    wait_event
                FROM pg_stat_activity 
                WHERE state != 'idle' 
                AND query NOT LIKE '%pg_stat_activity%'
                ORDER BY duration DESC
            """)
            
            queries = []
            for row in active_queries:
                query_type = self._determine_query_type(row["query"])
                status = self._determine_query_status(row["state"])
                
                query_info = QueryInfo(
                    id=str(row["pid"]),
                    query_text=row["query"][:500],  # Truncate long queries
                    query_type=query_type,
                    status=status,
                    duration=row["duration"].total_seconds() if row["duration"] else 0,
                    start_time=row["query_start"],
                    user=row["usename"],
                    database=row["datname"],
                    client_addr=row["client_addr"],
                    application_name=row["application_name"],
                    wait_event_type=row["wait_event_type"],
                    wait_event=row["wait_event"],
                    state=row["state"]
                )
                queries.append(query_info)
            
            return queries
            
        except Exception as e:
            self.logger.error(f"Failed to get active queries: {e}")
            return []
    
    def _determine_query_type(self, query: str) -> QueryType:
        """Determine the type of query"""
        query_lower = query.strip().lower()
        
        if query_lower.startswith('select'):
            return QueryType.SELECT
        elif query_lower.startswith('insert'):
            return QueryType.INSERT
        elif query_lower.startswith('update'):
            return QueryType.UPDATE
        elif query_lower.startswith('delete'):
            return QueryType.DELETE
        elif query_lower.startswith('create'):
            return QueryType.CREATE
        elif query_lower.startswith('alter'):
            return QueryType.ALTER
        elif query_lower.startswith('drop'):
            return QueryType.DROP
        else:
            return QueryType.SELECT
    
    def _determine_query_status(self, state: str) -> QueryStatus:
        """Determine the status of a query"""
        if state == 'active':
            return QueryStatus.ACTIVE
        elif state == 'idle':
            return QueryStatus.IDLE
        elif state == 'idle in transaction':
            return QueryStatus.IDLE_IN_TRANSACTION
        else:
            return QueryStatus.LOCKED
    
    async def analyze_query(self, query_text: str) -> QueryAnalysis:
        """Analyze a specific query for performance and optimization"""
        try:
            analysis_id = f"analysis_{datetime.utcnow().timestamp()}"
            
            # Get execution plan
            execution_plan = await self._get_execution_plan(query_text)
            
            # Analyze performance
            performance_metrics = await self._analyze_query_performance(query_text)
            
            # Generate optimization suggestions
            optimization_suggestions = self._generate_optimization_suggestions(
                execution_plan, performance_metrics
            )
            
            analysis = QueryAnalysis(
                id=analysis_id,
                query_text=query_text,
                execution_plan=execution_plan,
                performance_metrics=performance_metrics,
                optimization_suggestions=optimization_suggestions
            )
            
            # Store analysis
            await self._store_query_analysis(analysis)
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Failed to analyze query: {e}")
            raise
    
    async def _get_execution_plan(self, query_text: str) -> Dict[str, Any]:
        """Get execution plan for a query"""
        try:
            # Use EXPLAIN ANALYZE to get execution plan
            plan_result = await self.db.fetch_all(f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query_text}")
            
            if plan_result:
                # Parse JSON execution plan
                import json
                plan_json = json.loads(plan_result[0][0])
                return plan_json
            else:
                return {}
                
        except Exception as e:
            self.logger.error(f"Failed to get execution plan: {e}")
            return {}
    
    async def _analyze_query_performance(self, query_text: str) -> Dict[str, Any]:
        """Analyze query performance metrics"""
        try:
            # Get query statistics from pg_stat_statements
            stats = await self.db.fetch_one("""
                SELECT 
                    mean_time,
                    stddev_time,
                    min_time,
                    max_time,
                    calls,
                    total_time,
                    rows
                FROM pg_stat_statements 
                WHERE query = :query
            """, {"query": query_text})
            
            if stats:
                return {
                    "mean_time": stats["mean_time"],
                    "stddev_time": stats["stddev_time"],
                    "min_time": stats["min_time"],
                    "max_time": stats["max_time"],
                    "calls": stats["calls"],
                    "total_time": stats["total_time"],
                    "rows": stats["rows"]
                }
            else:
                return {}
                
        except Exception as e:
            self.logger.error(f"Failed to analyze query performance: {e}")
            return {}
    
    def _generate_optimization_suggestions(self, execution_plan: Dict[str, Any], 
                                         performance_metrics: Dict[str, Any]) -> List[str]:
        """Generate optimization suggestions based on analysis"""
        suggestions = []
        
        try:
            # Analyze execution plan
            if execution_plan:
                plan = execution_plan[0] if isinstance(execution_plan, list) else execution_plan
                
                # Check for sequential scans
                if self._has_sequential_scan(plan):
                    suggestions.append("Consider adding indexes to avoid sequential scans")
                
                # Check for nested loops
                if self._has_nested_loops(plan):
                    suggestions.append("Consider optimizing JOIN operations to reduce nested loops")
                
                # Check for large result sets
                if self._has_large_result_set(plan):
                    suggestions.append("Consider adding LIMIT clause or pagination")
            
            # Analyze performance metrics
            if performance_metrics:
                mean_time = performance_metrics.get("mean_time", 0)
                if mean_time > 1000:  # More than 1 second
                    suggestions.append("Query is slow - consider adding indexes or optimizing the query structure")
                
                calls = performance_metrics.get("calls", 0)
                if calls > 1000:
                    suggestions.append("Query is called frequently - consider query result caching")
            
            if not suggestions:
                suggestions.append("Query appears to be well-optimized")
            
            return suggestions
            
        except Exception as e:
            self.logger.error(f"Failed to generate optimization suggestions: {e}")
            return ["Unable to generate optimization suggestions"]
    
    def _has_sequential_scan(self, plan: Dict[str, Any]) -> bool:
        """Check if execution plan has sequential scans"""
        try:
            if "Seq Scan" in str(plan):
                return True
            
            # Recursively check child nodes
            if "Plans" in plan:
                for child in plan["Plans"]:
                    if self._has_sequential_scan(child):
                        return True
            
            return False
            
        except Exception:
            return False
    
    def _has_nested_loops(self, plan: Dict[str, Any]) -> bool:
        """Check if execution plan has nested loops"""
        try:
            if "Nested Loop" in str(plan):
                return True
            
            # Recursively check child nodes
            if "Plans" in plan:
                for child in plan["Plans"]:
                    if self._has_nested_loops(child):
                        return True
            
            return False
            
        except Exception:
            return False
    
    def _has_large_result_set(self, plan: Dict[str, Any]) -> bool:
        """Check if execution plan indicates large result sets"""
        try:
            # Check for large row estimates
            if "Plan Rows" in plan and plan["Plan Rows"] > 10000:
                return True
            
            # Recursively check child nodes
            if "Plans" in plan:
                for child in plan["Plans"]:
                    if self._has_large_result_set(child):
                        return True
            
            return False
            
        except Exception:
            return False
    
    async def get_query_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """Get query statistics for the last N hours"""
        try:
            # Get top queries by execution time
            top_queries = await self.db.fetch_all("""
                SELECT 
                    query,
                    mean_time,
                    calls,
                    total_time,
                    rows
                FROM pg_stat_statements 
                ORDER BY total_time DESC 
                LIMIT 10
            """)
            
            # Get query type distribution
            query_types = await self.db.fetch_all("""
                SELECT 
                    CASE 
                        WHEN query ILIKE 'SELECT%' THEN 'SELECT'
                        WHEN query ILIKE 'INSERT%' THEN 'INSERT'
                        WHEN query ILIKE 'UPDATE%' THEN 'UPDATE'
                        WHEN query ILIKE 'DELETE%' THEN 'DELETE'
                        ELSE 'OTHER'
                    END as query_type,
                    COUNT(*) as count
                FROM pg_stat_statements 
                GROUP BY query_type
            """)
            
            # Get slowest queries
            slowest_queries = await self.db.fetch_all("""
                SELECT 
                    query,
                    mean_time,
                    calls
                FROM pg_stat_statements 
                WHERE mean_time > 100
                ORDER BY mean_time DESC 
                LIMIT 5
            """)
            
            return {
                "top_queries": [
                    {
                        "query": q["query"][:100],
                        "mean_time": q["mean_time"],
                        "calls": q["calls"],
                        "total_time": q["total_time"],
                        "rows": q["rows"]
                    }
                    for q in top_queries
                ],
                "query_type_distribution": [
                    {
                        "type": qt["query_type"],
                        "count": qt["count"]
                    }
                    for qt in query_types
                ],
                "slowest_queries": [
                    {
                        "query": q["query"][:100],
                        "mean_time": q["mean_time"],
                        "calls": q["calls"]
                    }
                    for q in slowest_queries
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get query statistics: {e}")
            return {}
    
    async def _store_query_analysis(self, analysis: QueryAnalysis):
        """Store query analysis in database"""
        try:
            await self.db.execute(
                """
                INSERT INTO query_analyses 
                (id, query_text, execution_plan, performance_metrics, optimization_suggestions, analyzed_at)
                VALUES (:id, :query_text, :execution_plan, :performance_metrics, :optimization_suggestions, :analyzed_at)
                """,
                {
                    "id": analysis.id,
                    "query_text": analysis.query_text,
                    "execution_plan": analysis.execution_plan,
                    "performance_metrics": analysis.performance_metrics,
                    "optimization_suggestions": analysis.optimization_suggestions,
                    "analyzed_at": analysis.analyzed_at
                }
            )
        except Exception as e:
            self.logger.error(f"Failed to store query analysis: {e}")

# Singleton instance
_query_analyzer = None

def get_query_analyzer() -> QueryAnalyzer:
    global _query_analyzer
    if _query_analyzer is None:
        _query_analyzer = QueryAnalyzer()
    return _query_analyzer

def init_query_analyzer():
    """Initialize query analysis system"""
    global _query_analyzer
    _query_analyzer = QueryAnalyzer()
    return _query_analyzer
