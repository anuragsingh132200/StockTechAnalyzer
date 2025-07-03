import json
import hashlib
import logging
from typing import Any, Optional
import redis.asyncio as redis
from config import settings

class CacheService:
    """Service for caching frequently accessed data"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.redis_client: Optional[redis.Redis] = None
        self._initialize_redis()

    def _initialize_redis(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            self.logger.info("Redis connection initialized")
        except Exception as e:
            self.logger.warning(f"Failed to connect to Redis: {e}. Caching disabled.")
            self.redis_client = None

    def _generate_cache_key(self, prefix: str, **kwargs) -> str:
        """Generate a cache key from parameters"""
        key_data = json.dumps(kwargs, sort_keys=True, default=str)
        key_hash = hashlib.md5(key_data.encode()).hexdigest()
        return f"{prefix}:{key_hash}"

    async def get(self, prefix: str, **kwargs) -> Optional[Any]:
        """Get data from cache"""
        if not self.redis_client:
            return None
        
        try:
            cache_key = self._generate_cache_key(prefix, **kwargs)
            cached_data = await self.redis_client.get(cache_key)
            
            if cached_data:
                self.logger.debug(f"Cache hit for key: {cache_key}")
                return json.loads(cached_data)
            
            self.logger.debug(f"Cache miss for key: {cache_key}")
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting data from cache: {e}")
            return None

    async def set(self, prefix: str, data: Any, ttl: Optional[int] = None, **kwargs):
        """Set data in cache"""
        if not self.redis_client:
            return
        
        try:
            cache_key = self._generate_cache_key(prefix, **kwargs)
            serialized_data = json.dumps(data, default=str)
            
            ttl = ttl or settings.CACHE_TTL
            await self.redis_client.setex(cache_key, ttl, serialized_data)
            
            self.logger.debug(f"Data cached with key: {cache_key}, TTL: {ttl}")
            
        except Exception as e:
            self.logger.error(f"Error setting data in cache: {e}")

    async def delete(self, prefix: str, **kwargs):
        """Delete data from cache"""
        if not self.redis_client:
            return
        
        try:
            cache_key = self._generate_cache_key(prefix, **kwargs)
            await self.redis_client.delete(cache_key)
            self.logger.debug(f"Cache deleted for key: {cache_key}")
            
        except Exception as e:
            self.logger.error(f"Error deleting data from cache: {e}")

    async def invalidate_pattern(self, pattern: str):
        """Invalidate cache entries matching a pattern"""
        if not self.redis_client:
            return
        
        try:
            keys = await self.redis_client.keys(pattern)
            if keys:
                await self.redis_client.delete(*keys)
                self.logger.debug(f"Invalidated {len(keys)} cache entries matching pattern: {pattern}")
                
        except Exception as e:
            self.logger.error(f"Error invalidating cache pattern: {e}")

    async def health_check(self) -> bool:
        """Check if Redis is healthy"""
        if not self.redis_client:
            return False
        
        try:
            await self.redis_client.ping()
            return True
        except Exception:
            return False
