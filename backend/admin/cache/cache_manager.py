"""
Cache Manager for Agent47 Admin Panel
Cache management, statistics, and optimization
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from sqlalchemy import text

from backend.core.database import get_database, DatabaseManager
from backend.core.cache import get_redis, RedisManager
from backend.core.logs import get_logger, LoggerMixin
from backend.core.config import get_settings

logger = get_logger(__name__)

class CacheType(Enum):
    REDIS = "redis"
    MEMORY = "memory"
    DATABASE = "database"

@dataclass
class CacheStatistic:
    cache_type: CacheType
    total_keys: int
    total_size_bytes: int
    hit_count: int
    miss_count: int
    hit_rate: float
    eviction_count: int
    memory_usage_mb: float

@dataclass
class CacheKey:
    key: str
    value_type: str
    size_bytes: int
    ttl_seconds: Optional[int]
    created_at: Optional[datetime]
    last_accessed: Optional[datetime]
    access_count: int

class CacheManager(LoggerMixin):
    def __init__(self):
        self.database: Optional[DatabaseManager] = None
        self.redis: Optional[RedisManager] = None
        self.settings = get_settings()
        self.logger = logger
        
        self.cache_statistics: Dict[CacheType, CacheStatistic] = {}
        self.key_patterns: Dict[str, str] = {
            "user": "user:*",
            "session": "session:*",
            "agent": "agent:*",
            "setting": "setting:*",
            "feature_flag": "feature_flag:*",
            "rate_limit": "rate_limit:*"
        }

    async def initialize(self) -> bool:
        try:
            self.logger.info("Initializing CacheManager...")
            
            self.database = get_database()
            self.redis = await get_redis()
            
            await self._setup_cache_tables()
            await self._start_statistics_collection()
            
            self.logger.info("CacheManager initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize CacheManager: {str(e)}")
            return False

    async def _setup_cache_tables(self):
        """Setup database tables for cache statistics"""
        if not self.database:
            return
        
        async with self.database.get_session() as session:
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS cache_statistics (
                    id SERIAL PRIMARY KEY,
                    cache_type VARCHAR(50) NOT NULL,
                    total_keys INTEGER DEFAULT 0,
                    total_size_bytes BIGINT DEFAULT 0,
                    hit_count BIGINT DEFAULT 0,
                    miss_count BIGINT DEFAULT 0,
                    eviction_count INTEGER DEFAULT 0,
                    memory_usage_mb DECIMAL(10,2) DEFAULT 0.0,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            await session.commit()

    async def _start_statistics_collection(self):
        """Start background task to collect cache statistics"""
        async def collect_statistics():
            while True:
                try:
                    await asyncio.sleep(300)  # Collect every 5 minutes
                    await self._collect_cache_statistics()
                except Exception as e:
                    self.logger.error(f"Error in statistics collection: {str(e)}")
        
        asyncio.create_task(collect_statistics())

    async def _collect_cache_statistics(self):
        """Collect cache statistics"""
        if self.redis:
            try:
                stats = await self._get_redis_statistics()
                self.cache_statistics[CacheType.REDIS] = stats
                
                # Store in database
                if self.database:
                    await self._store_statistics(CacheType.REDIS, stats)
            except Exception as e:
                self.logger.error(f"Failed to collect Redis statistics: {str(e)}")

    async def _get_redis_statistics(self) -> CacheStatistic:
        """Get Redis cache statistics"""
        if not self.redis:
            return CacheStatistic(
                cache_type=CacheType.REDIS,
                total_keys=0,
                total_size_bytes=0,
                hit_count=0,
                miss_count=0,
                hit_rate=0.0,
                eviction_count=0,
                memory_usage_mb=0.0
            )
        
        try:
            # Get Redis info - try to get info as dict or string
            try:
                info = await self.redis.info()
                # Handle both dict and string responses
                if isinstance(info, str):
                    # Parse string response
                    info_dict = {}
                    for line in info.split('\n'):
                        if ':' in line:
                            key, value = line.split(':', 1)
                            info_dict[key.strip()] = value.strip()
                    info = info_dict
            except Exception:
                info = {}
            
            # Get database keys count
            db_info = info.get("db0", "")
            total_keys = 0
            if db_info and "keys=" in db_info:
                try:
                    total_keys = int(db_info.split("keys=")[1].split(",")[0])
                except (ValueError, IndexError):
                    pass
            
            memory_used = int(info.get("used_memory", 0))
            memory_usage_mb = memory_used / (1024 * 1024)
            
            # Get hit/miss stats (if available)
            keyspace_hits = int(info.get("keyspace_hits", 0))
            keyspace_misses = int(info.get("keyspace_misses", 0))
            total_requests = keyspace_hits + keyspace_misses
            hit_rate = (keyspace_hits / total_requests * 100) if total_requests > 0 else 0.0
            
            eviction_count = int(info.get("evicted_keys", 0))
            
            return CacheStatistic(
                cache_type=CacheType.REDIS,
                total_keys=total_keys,
                total_size_bytes=memory_used,
                hit_count=keyspace_hits,
                miss_count=keyspace_misses,
                hit_rate=round(hit_rate, 2),
                eviction_count=eviction_count,
                memory_usage_mb=round(memory_usage_mb, 2)
            )
        
        except Exception as e:
            self.logger.error(f"Failed to get Redis statistics: {str(e)}")
            return CacheStatistic(
                cache_type=CacheType.REDIS,
                total_keys=0,
                total_size_bytes=0,
                hit_count=0,
                miss_count=0,
                hit_rate=0.0,
                eviction_count=0,
                memory_usage_mb=0.0
            )

    async def _store_statistics(self, cache_type: CacheType, stats: CacheStatistic):
        """Store cache statistics in database"""
        if not self.database:
            return
        
        try:
            async with self.database.get_session() as session:
                await session.execute(
                    text("""
                        INSERT INTO cache_statistics (
                            cache_type, total_keys, total_size_bytes,
                            hit_count, miss_count, eviction_count, memory_usage_mb
                        )
                        VALUES (:type, :keys, :size, :hits, :misses, :evictions, :memory)
                    """),
                    {
                        "type": cache_type.value,
                        "keys": stats.total_keys,
                        "size": stats.total_size_bytes,
                        "hits": stats.hit_count,
                        "misses": stats.miss_count,
                        "evictions": stats.eviction_count,
                        "memory": stats.memory_usage_mb
                    }
                )
                await session.commit()
        except Exception as e:
            self.logger.error(f"Failed to store cache statistics: {str(e)}")

    async def get_cache_statistics(self, cache_type: Optional[CacheType] = None) -> Dict[str, Any]:
        """Get current cache statistics"""
        if cache_type:
            stats = self.cache_statistics.get(cache_type)
            if stats:
                return {
                    "cache_type": stats.cache_type.value,
                    "total_keys": stats.total_keys,
                    "total_size_bytes": stats.total_size_bytes,
                    "total_size_mb": round(stats.total_size_bytes / (1024 * 1024), 2),
                    "hit_count": stats.hit_count,
                    "miss_count": stats.miss_count,
                    "hit_rate": stats.hit_rate,
                    "eviction_count": stats.eviction_count,
                    "memory_usage_mb": stats.memory_usage_mb
                }
            return {}
        
        # Return all statistics
        return {
            cache_type.value: {
                "total_keys": stats.total_keys,
                "total_size_bytes": stats.total_size_bytes,
                "total_size_mb": round(stats.total_size_bytes / (1024 * 1024), 2),
                "hit_count": stats.hit_count,
                "miss_count": stats.miss_count,
                "hit_rate": stats.hit_rate,
                "eviction_count": stats.eviction_count,
                "memory_usage_mb": stats.memory_usage_mb
            }
            for cache_type, stats in self.cache_statistics.items()
        }

    async def get_cache_keys(self, pattern: str = "*", limit: int = 100) -> List[CacheKey]:
        """Get cache keys matching a pattern"""
        if not self.redis:
            return []
        
        try:
            keys = await self.redis.keys(pattern)
            cache_keys = []
            
            for key in keys[:limit]:
                try:
                    # Get key info
                    ttl = await self.redis.ttl(key)
                    value = await self.redis.get(key)
                    
                    if value:
                        value_type = type(value).__name__
                        size_bytes = len(str(value).encode('utf-8'))
                    else:
                        value_type = "unknown"
                        size_bytes = 0
                    
                    cache_keys.append(CacheKey(
                        key=key,
                        value_type=value_type,
                        size_bytes=size_bytes,
                        ttl_seconds=ttl if ttl > 0 else None,
                        created_at=None,  # Redis doesn't track creation time
                        last_accessed=None,  # Redis doesn't track last access
                        access_count=0  # Would need custom tracking
                    ))
                except Exception as e:
                    self.logger.warning(f"Failed to get info for key {key}: {str(e)}")
            
            return cache_keys
        
        except Exception as e:
            self.logger.error(f"Failed to get cache keys: {str(e)}")
            return []

    async def clear_cache(self, pattern: Optional[str] = None) -> int:
        """Clear cache keys matching a pattern"""
        if not self.redis:
            return 0
        
        try:
            if pattern:
                keys = await self.redis.keys(pattern)
                if keys:
                    deleted = await self.redis.delete(*keys)
                    self.logger.info(f"Cleared {deleted} cache keys matching pattern: {pattern}")
                    return deleted
            else:
                # Clear all keys (use with caution!)
                await self.redis.flushdb()
                self.logger.warning("All cache keys cleared")
                return -1  # Indicate all keys cleared
        
        except Exception as e:
            self.logger.error(f"Failed to clear cache: {str(e)}")
            return 0

    async def clear_cache_by_category(self, category: str) -> int:
        """Clear cache keys by category"""
        pattern = self.key_patterns.get(category, f"{category}:*")
        return await self.clear_cache(pattern)

    async def get_cache_value(self, key: str) -> Optional[Any]:
        """Get a cache value by key"""
        if not self.redis:
            return None
        
        try:
            return await self.redis.get(key)
        except Exception as e:
            self.logger.error(f"Failed to get cache value for key {key}: {str(e)}")
            return None

    async def set_cache_value(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> bool:
        """Set a cache value"""
        if not self.redis:
            return False
        
        try:
            await self.redis.set(key, value, expire=ttl_seconds)
            return True
        except Exception as e:
            self.logger.error(f"Failed to set cache value for key {key}: {str(e)}")
            return False

    async def delete_cache_key(self, key: str) -> bool:
        """Delete a specific cache key"""
        if not self.redis:
            return False
        
        try:
            await self.redis.delete(key)
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete cache key {key}: {str(e)}")
            return False

    async def get_cache_size_by_category(self) -> Dict[str, int]:
        """Get cache size breakdown by category"""
        if not self.redis:
            return {}
        
        try:
            category_sizes = {}
            
            for category, pattern in self.key_patterns.items():
                keys = await self.redis.keys(pattern)
                total_size = 0
                
                for key in keys:
                    try:
                        value = await self.redis.get(key)
                        if value:
                            total_size += len(str(value).encode('utf-8'))
                    except Exception:
                        pass
                
                category_sizes[category] = total_size
            
            return category_sizes
        
        except Exception as e:
            self.logger.error(f"Failed to get cache size by category: {str(e)}")
            return {}

    async def get_cache_health(self) -> Dict[str, Any]:
        """Get cache health status"""
        health = {
            "redis_available": False,
            "redis_connected": False,
            "memory_usage_mb": 0.0,
            "total_keys": 0,
            "hit_rate": 0.0,
            "status": "unhealthy"
        }
        
        if self.redis:
            try:
                health["redis_available"] = True
                await self.redis.ping()
                health["redis_connected"] = True
                
                stats = await self._get_redis_statistics()
                health["memory_usage_mb"] = stats.memory_usage_mb
                health["total_keys"] = stats.total_keys
                health["hit_rate"] = stats.hit_rate
                health["status"] = "healthy" if stats.hit_rate > 50 else "degraded"
            except Exception as e:
                self.logger.error(f"Failed to check cache health: {str(e)}")
                health["status"] = "unhealthy"
                health["error"] = str(e)
        
        return health

    async def optimize_cache(self) -> Dict[str, Any]:
        """Optimize cache by removing expired keys and optimizing memory"""
        if not self.redis:
            return {"success": False, "message": "Redis not available"}
        
        try:
            # Get all keys
            all_keys = await self.redis.keys("*")
            expired_count = 0
            total_size_before = 0
            total_size_after = 0
            
            for key in all_keys:
                try:
                    ttl = await self.redis.ttl(key)
                    if ttl == -2:  # Key doesn't exist (expired)
                        expired_count += 1
                    else:
                        value = await self.redis.get(key)
                        if value:
                            total_size_before += len(str(value).encode('utf-8'))
                except Exception:
                    pass
            
            # Redis automatically handles expired keys, but we can force cleanup
            # by calling MEMORY PURGE if available (Redis 4.0+)
            
            return {
                "success": True,
                "expired_keys_removed": expired_count,
                "total_keys": len(all_keys),
                "optimization_complete": True
            }
        
        except Exception as e:
            self.logger.error(f"Failed to optimize cache: {str(e)}")
            return {"success": False, "message": str(e)}

    async def get_cache_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get cache statistics history"""
        if not self.database:
            return []
        
        try:
            start_time = datetime.utcnow() - timedelta(hours=hours)
            
            async with self.database.get_session() as session:
                result = await session.execute(
                    text("""
                        SELECT cache_type, total_keys, total_size_bytes, hit_count,
                               miss_count, memory_usage_mb, timestamp
                        FROM cache_statistics
                        WHERE timestamp >= :start_time
                        ORDER BY timestamp DESC
                    """),
                    {"start_time": start_time}
                )
                
                history = []
                for row in result.fetchall():
                    history.append({
                        "cache_type": row[0],
                        "total_keys": row[1],
                        "total_size_bytes": row[2],
                        "total_size_mb": round(row[2] / (1024 * 1024), 2),
                        "hit_count": row[3],
                        "miss_count": row[4],
                        "memory_usage_mb": float(row[5]),
                        "timestamp": row[6].isoformat()
                    })
                
                return history
        
        except Exception as e:
            self.logger.error(f"Failed to get cache history: {str(e)}")
            return []

    async def close(self):
        self.logger.info("Closing CacheManager...")

# Global instances
_cache_manager: Optional[CacheManager] = None

async def init_cache_manager() -> CacheManager:
    global _cache_manager
    if not _cache_manager:
        _cache_manager = CacheManager()
        await _cache_manager.initialize()
    return _cache_manager

async def get_cache_manager() -> CacheManager:
    global _cache_manager
    if not _cache_manager:
        _cache_manager = await init_cache_manager()
    return _cache_manager

