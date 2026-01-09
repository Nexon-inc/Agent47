import redis.asyncio as redis
import json
import pickle
import hashlib
from typing import Any, Optional, Union, Dict, List
from datetime import timedelta
import logging
from ..config import settings

logger = logging.getLogger(__name__)

class AsyncInMemoryRedis:
    """A tiny asyncio-friendly in-memory Redis-like fallback used when a real
    Redis connection can't be established. Implements the subset of methods
    used by the application (ping, get, set, setex, delete, hset, hget, hgetall,
    lrange, rpush, keys, expire, ttl, incr, decr, pipeline, close).
    """
    def __init__(self):
        import asyncio
        self._store = {}
        self._hashes = {}
        self._lists = {}
        self._loop = asyncio.get_event_loop()

    async def ping(self):
        return True

    async def close(self):
        return True

    async def set(self, key, value):
        self._store[key] = value
        return True

    async def setex(self, key, seconds, value):
        self._store[key] = value
        return True

    async def get(self, key):
        return self._store.get(key)

    async def delete(self, *keys):
        count = 0
        for k in keys:
            if k in self._store:
                del self._store[k]
                count += 1
        return count

    async def hset(self, key, mapping=None, **kwargs):
        mapping = mapping or {}
        if key not in self._hashes:
            self._hashes[key] = {}
        self._hashes[key].update(mapping)
        return 1

    async def hget(self, key, field):
        return self._hashes.get(key, {}).get(field)

    async def hgetall(self, key):
        return self._hashes.get(key, {}).copy() if key in self._hashes else {}

    async def lrange(self, key, start, end):
        return self._lists.get(key, [])[start:end+1 if end != -1 else None]

    async def rpush(self, key, *values):
        self._lists.setdefault(key, []).extend(values)
        return len(self._lists[key])

    async def keys(self, pattern):
        # simple glob '*' handling
        if pattern == '*':
            return list(self._store.keys())
        return [k for k in self._store.keys() if pattern in k]

    async def expire(self, key, seconds):
        # no-op for in-memory
        return True

    async def ttl(self, key):
        return -1

    async def incr(self, key, amount=1):
        val = int(self._store.get(key, 0)) + amount
        self._store[key] = val
        return val

    async def decr(self, key, amount=1):
        val = int(self._store.get(key, 0)) - amount
        self._store[key] = val
        return val

    def pipeline(self):
        # minimal pipeline that executes immediately
        class _Pipe:
            def __init__(self, parent):
                self._parent = parent
            def delete(self, key):
                self._parent._store.pop(key, None)
            def rpush(self, key, *vals):
                self._parent._lists.setdefault(key, []).extend(vals)
            def expire(self, key, s):
                return True
            def execute(self):
                return True
        return _Pipe(self)


class RedisManager:
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self._initialized = False
    
    async def initialize(self):
        if self._initialized:
            return
        
        try:
            # Use separate secrets for host, port, password (Upstash compatibility)
            host = settings.redis.host  # e.g., "clear-hamster-30497.upstash.io"
            port = int(settings.redis.port or 6379)
            password = settings.redis.password  # Token from Upstash

            # Upstash requires username "default" with the token as password
            # Handle both formats: "default:token" or just "token"
            username = None
            if password:
                if password.startswith("default:"):
                    # Password already includes username prefix
                    username = "default"
                    password = password[8:]  # Remove "default:" prefix
                else:
                    # For Upstash, use "default" as username
                    username = "default"

            # Build connection parameters
            connection_params = {
                "host": host,
                "port": port,
                "encoding": "utf-8",
                "decode_responses": False,
                "ssl": True,  # Critical for Upstash (TLS required)
                "socket_connect_timeout": 5,
                "socket_timeout": 5,
                "retry_on_timeout": True,
                "health_check_interval": 30
            }
            
            # Add authentication if password is provided
            if password:
                connection_params["password"] = password
                if username:
                    connection_params["username"] = username

            self.redis_client = redis.Redis(**connection_params)
            
            await self.redis_client.ping()
            self._initialized = True
            logger.info("Redis connection initialized successfully (Upstash compatible)")
            
        except Exception as e:
            logger.error("Failed to initialize Redis connection: %s", e)
            
            # Check if we're in development mode
            is_development = not settings.redis.is_production
            
            if is_development:
                logger.warning("Development mode detected - using in-memory Redis fallback")
                self.redis_client = AsyncInMemoryRedis()
                self._initialized = True
            else:
                logger.error("Redis connection failed in production mode. Please ensure Redis is running and properly configured.")
                raise RuntimeError(f"Redis connection failed: {e}. Redis is required for production deployment.")
    
    async def close(self):
        if self.redis_client:
            try:
                await self.redis_client.close()
            except Exception:
                # in-memory client may not need explicit close
                pass
            self._initialized = False
            logger.info("Redis connection closed")
    
    async def health_check(self) -> bool:
        try:
            if not self._initialized:
                await self.initialize()
            
            await self.redis_client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False

    async def execute_command(self, *args) -> Any:
        """Execute a raw Redis command."""
        if not self._initialized:
            await self.initialize()
        try:
            return await self.redis_client.execute_command(*args)
        except Exception as e:
            logger.error(f"Failed to execute Redis command {args}: {e}")
            raise
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate a consistent cache key from arguments"""
        key_parts = [prefix]
        
        for arg in args:
            key_parts.append(str(arg))
        
        for key, value in sorted(kwargs.items()):
            key_parts.append(f"{key}:{value}")
        
        key_string = ":".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    async def set(self, key: str, value: Any, expire: Optional[Union[int, timedelta]] = None) -> bool:
        """Set a key-value pair in cache"""
        if not self._initialized:
            await self.initialize()
        
        try:
            if isinstance(value, (dict, list)):
                serialized_value = json.dumps(value)
            else:
                serialized_value = pickle.dumps(value)
            
            if expire:
                if isinstance(expire, timedelta):
                    expire_seconds = int(expire.total_seconds())
                else:
                    expire_seconds = expire
                
                return await self.redis_client.setex(key, expire_seconds, serialized_value)
            else:
                return await self.redis_client.set(key, serialized_value)
                
        except Exception as e:
            logger.error(f"Failed to set cache key {key}: {e}")
            return False
    
    async def get(self, key: str, default: Any = None) -> Any:
        """Get a value from cache"""
        if not self._initialized:
            await self.initialize()
        
        try:
            value = await self.redis_client.get(key)
            if value is None:
                return default
            
            try:
                return json.loads(value)
            except (json.JSONDecodeError, UnicodeDecodeError):
                return pickle.loads(value)
                
        except Exception as e:
            logger.error(f"Failed to get cache key {key}: {e}")
            return default
    
    async def delete(self, *keys: str) -> int:
        """Delete one or more keys from cache"""
        if not self._initialized:
            await self.initialize()
        
        try:
            return await self.redis_client.delete(*keys)
        except Exception as e:
            logger.error(f"Failed to delete cache keys {keys}: {e}")
            return 0
    
    async def exists(self, key: str) -> bool:
        """Check if a key exists in cache"""
        if not self._initialized:
            await self.initialize()
        
        try:
            return bool(await self.redis_client.exists(key))
        except Exception as e:
            logger.error(f"Failed to check existence of cache key {key}: {e}")
            return False
    
    async def expire(self, key: str, expire: Union[int, timedelta]) -> bool:
        """Set expiration for a key"""
        if not self._initialized:
            await self.initialize()
        
        try:
            if isinstance(expire, timedelta):
                expire_seconds = int(expire.total_seconds())
            else:
                expire_seconds = expire
            
            return await self.redis_client.expire(key, expire_seconds)
        except Exception as e:
            logger.error(f"Failed to set expiration for cache key {key}: {e}")
            return False
    
    async def ttl(self, key: str) -> int:
        """Get time to live for a key"""
        if not self._initialized:
            await self.initialize()
        
        try:
            return await self.redis_client.ttl(key)
        except Exception as e:
            logger.error(f"Failed to get TTL for cache key {key}: {e}")
            return -1
    
    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment a numeric value"""
        if not self._initialized:
            await self.initialize()
        
        try:
            return await self.redis_client.incr(key, amount)
        except Exception as e:
            logger.error(f"Failed to increment cache key {key}: {e}")
            return 0
    
    async def decrement(self, key: str, amount: int = 1) -> int:
        """Decrement a numeric value"""
        if not self._initialized:
            await self.initialize()
        
        try:
            return await self.redis_client.decr(key, amount)
        except Exception as e:
            logger.error(f"Failed to decrement cache key {key}: {e}")
            return 0
    
    async def set_hash(self, key: str, mapping: Dict[str, Any], expire: Optional[Union[int, timedelta]] = None) -> bool:
        """Set a hash in cache"""
        if not self._initialized:
            await self.initialize()
        
        try:
            serialized_mapping = {k: json.dumps(v) if isinstance(v, (dict, list)) else str(v) 
                                for k, v in mapping.items()}
            
            result = await self.redis_client.hset(key, mapping=serialized_mapping)
            
            if expire:
                if isinstance(expire, timedelta):
                    expire_seconds = int(expire.total_seconds())
                else:
                    expire_seconds = expire
                await self.redis_client.expire(key, expire_seconds)
            
            return bool(result)
        except Exception as e:
            logger.error(f"Failed to set hash cache key {key}: {e}")
            return False
    
    async def get_hash(self, key: str, field: Optional[str] = None) -> Any:
        """Get a hash or hash field from cache"""
        if not self._initialized:
            await self.initialize()
        
        try:
            if field:
                value = await self.redis_client.hget(key, field)
                if value is None:
                    return None
                
                try:
                    return json.loads(value)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    return value.decode('utf-8')
            else:
                hash_data = await self.redis_client.hgetall(key)
                if not hash_data:
                    return {}
                
                result = {}
                for k, v in hash_data.items():
                    k_str = k.decode('utf-8') if isinstance(k, bytes) else k
                    try:
                        result[k_str] = json.loads(v)
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        result[k_str] = v.decode('utf-8') if isinstance(v, bytes) else v
                
                return result
                
        except Exception as e:
            logger.error(f"Failed to get hash cache key {key}: {e}")
            return {} if field is None else None
    
    async def delete_hash_field(self, key: str, *fields: str) -> int:
        """Delete fields from a hash"""
        if not self._initialized:
            await self.initialize()
        
        try:
            return await self.redis_client.hdel(key, *fields)
        except Exception as e:
            logger.error(f"Failed to delete hash fields {fields} from key {key}: {e}")
            return 0
    
    async def set_list(self, key: str, values: List[Any], expire: Optional[Union[int, timedelta]] = None) -> bool:
        """Set a list in cache"""
        if not self._initialized:
            await self.initialize()
        
        try:
            serialized_values = [json.dumps(v) if isinstance(v, (dict, list)) else str(v) for v in values]
            
            pipeline = self.redis_client.pipeline()
            pipeline.delete(key)
            pipeline.rpush(key, *serialized_values)
            
            if expire:
                if isinstance(expire, timedelta):
                    expire_seconds = int(expire.total_seconds())
                else:
                    expire_seconds = expire
                pipeline.expire(key, expire_seconds)
            
            pipeline.execute()
            return True
            
        except Exception as e:
            logger.error(f"Failed to set list cache key {key}: {e}")
            return False
    
    async def get_list(self, key: str, start: int = 0, end: int = -1) -> List[Any]:
        """Get a list from cache"""
        if not self._initialized:
            await self.initialize()
        
        try:
            values = await self.redis_client.lrange(key, start, end)
            if not values:
                return []
            
            result = []
            for v in values:
                try:
                    result.append(json.loads(v))
                except (json.JSONDecodeError, UnicodeDecodeError):
                    result.append(v.decode('utf-8') if isinstance(v, bytes) else v)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get list cache key {key}: {e}")
            return []
    
    async def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching a pattern"""
        if not self._initialized:
            await self.initialize()
        
        try:
            keys = await self.redis_client.keys(pattern)
            if keys:
                return await self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Failed to clear pattern {pattern}: {e}")
            return 0
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get Redis statistics"""
        if not self._initialized:
            await self.initialize()
        
        try:
            info = await self.redis_client.info()
            return {
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_human": info.get("used_memory_human", "0B"),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "uptime_in_seconds": info.get("uptime_in_seconds", 0)
            }
        except Exception as e:
            logger.error(f"Failed to get Redis stats: {e}")
            return {}

# Global Redis manager instance
redis_manager = RedisManager()

async def get_redis() -> RedisManager:
    return redis_manager

async def init_redis():
    await redis_manager.initialize()

async def close_redis():
    await redis_manager.close()