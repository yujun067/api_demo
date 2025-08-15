import redis
import json
import hashlib
from typing import Optional, Any, Dict, Callable
from functools import wraps

from .settings import settings
from .logging import get_logger

logger = get_logger("redis")

# Create Redis client
redis_client = redis.Redis.from_url(
    settings.redis_url,
    decode_responses=True,
    socket_connect_timeout=5,
    socket_timeout=5,
    retry_on_timeout=True,
    health_check_interval=30,
)


class AdvancedRedisCache:
    """Advanced Redis caching utility with enhanced features."""

    def __init__(self):
        self.client = redis_client
        self.default_ttl = settings.cache_ttl_seconds
        self.cache_prefix = "hn_cache"
        self.stats = {"hits": 0, "misses": 0, "sets": 0, "deletes": 0}

    def _generate_key(self, key: str, namespace: Optional[str] = None) -> str:
        """Generate a cache key with namespace."""
        if namespace:
            return f"{self.cache_prefix}:{namespace}:{key}"
        return f"{self.cache_prefix}:{key}"

    def _serialize_value(self, value: Any) -> str:
        """Serialize value to JSON string."""
        if isinstance(value, (dict, list)):
            return json.dumps(value, default=str)
        return str(value)

    def _deserialize_value(self, value: str) -> Any:
        """Deserialize value from JSON string."""
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value

    def set(self, key: str, value: Any, ttl: Optional[int] = None, namespace: Optional[str] = None) -> bool:
        """Set a key-value pair in cache."""
        try:
            cache_key = self._generate_key(key, namespace)
            serialized_value = self._serialize_value(value)
            result = self.client.set(cache_key, serialized_value, ex=ttl or self.default_ttl)
            self.stats["sets"] += 1
            logger.debug(f"Cache SET: {cache_key} (TTL: {ttl or self.default_ttl}s)")
            return bool(result)
        except Exception as e:
            logger.error(f"Cache SET error for {key}: {e}")
            return False

    def get(self, key: str, namespace: Optional[str] = None) -> Optional[Any]:
        """Get a value from cache."""
        try:
            cache_key = self._generate_key(key, namespace)
            value = self.client.get(cache_key)

            if value is None:
                self.stats["misses"] += 1
                logger.debug(f"Cache MISS: {cache_key}")
                return None

            self.stats["hits"] += 1
            logger.debug(f"Cache HIT: {cache_key}")
            return self._deserialize_value(value)

        except Exception as e:
            logger.error(f"Cache GET error for {key}: {e}")
            self.stats["misses"] += 1
            return None

    def delete(self, key: str, namespace: Optional[str] = None) -> bool:
        """Delete a key from cache."""
        try:
            cache_key = self._generate_key(key, namespace)
            result = self.client.delete(cache_key)
            self.stats["deletes"] += 1
            logger.debug(f"Cache DELETE: {cache_key}")
            return bool(result)
        except Exception as e:
            logger.error(f"Cache DELETE error for {key}: {e}")
            return False

    def exists(self, key: str, namespace: Optional[str] = None) -> bool:
        """Check if a key exists in cache."""
        try:
            cache_key = self._generate_key(key, namespace)
            return bool(self.client.exists(cache_key))
        except Exception as e:
            logger.error(f"Cache EXISTS error for {key}: {e}")
            return False

    def expire(self, key: str, ttl: int, namespace: Optional[str] = None) -> bool:
        """Set expiration time for a key."""
        try:
            cache_key = self._generate_key(key, namespace)
            return bool(self.client.expire(cache_key, ttl))
        except Exception as e:
            logger.error(f"Cache EXPIRE error for {key}: {e}")
            return False

    def ttl(self, key: str, namespace: Optional[str] = None) -> int:
        """Get remaining TTL for a key."""
        try:
            cache_key = self._generate_key(key, namespace)
            return self.client.ttl(cache_key)
        except Exception as e:
            logger.error(f"Cache TTL error for {key}: {e}")
            return -1

    def clear_namespace(self, namespace: str) -> int:
        """Clear all keys in a namespace."""
        try:
            pattern = f"{self.cache_prefix}:{namespace}:*"
            keys = self.client.keys(pattern)
            if keys:
                deleted = self.client.delete(*keys)
                logger.info(f"Cleared namespace '{namespace}': {deleted} keys")
                return deleted
            return 0
        except Exception as e:
            logger.error(f"Cache CLEAR namespace error for {namespace}: {e}")
            return 0

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        try:
            total_keys = len(self.client.keys(f"{self.cache_prefix}:*"))
            hit_rate = (
                (self.stats["hits"] / (self.stats["hits"] + self.stats["misses"]))
                if (self.stats["hits"] + self.stats["misses"]) > 0
                else 0
            )

            return {
                "total_keys": total_keys,
                "hits": self.stats["hits"],
                "misses": self.stats["misses"],
                "sets": self.stats["sets"],
                "deletes": self.stats["deletes"],
                "hit_rate": round(hit_rate * 100, 2),
                "memory_usage": self.client.info("memory").get("used_memory_human", "N/A"),
            }
        except Exception as e:
            logger.error(f"Cache stats error: {e}")
            return {"error": str(e)}

    def reset_stats(self):
        """Reset cache statistics."""
        self.stats = {"hits": 0, "misses": 0, "sets": 0, "deletes": 0}



    # Legacy methods for backward compatibility
    def set_hash(self, key: str, mapping: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Set a hash in Redis cache."""
        try:
            result = self.client.hset(key, mapping=mapping)
            if ttl:
                self.client.expire(key, ttl)
            return bool(result)
        except Exception as e:
            logger.error(f"Redis set_hash error: {e}")
            return False

    def get_hash(self, key: str) -> Optional[Dict[str, Any]]:
        """Get a hash from Redis cache."""
        try:
            return self.client.hgetall(key)
        except Exception as e:
            logger.error(f"Redis get_hash error: {e}")
            return None


# Cache decorator for function results
def cache_result(ttl: Optional[int] = None, namespace: str = "func", key_generator: Optional[Callable] = None):
    """Decorator to cache function results."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_generator:
                cache_key = key_generator(*args, **kwargs)
            else:
                # Default key generation
                key_parts = [func.__name__]
                if args:
                    key_parts.extend([str(arg) for arg in args])
                if kwargs:
                    key_parts.extend([f"{k}={v}" for k, v in sorted(kwargs.items())])
                cache_key = hashlib.md5(":".join(key_parts).encode()).hexdigest()

            # Try to get from cache
            cached_result = cache.get(cache_key, namespace)
            if cached_result is not None:
                return cached_result

            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl, namespace)
            return result

        return wrapper

    return decorator


# Create global cache instance
cache = AdvancedRedisCache()


def get_redis_client() -> redis.Redis:
    """Get Redis client instance."""
    return redis_client


def health_check() -> bool:
    """Check if Redis is healthy."""
    try:
        redis_client.ping()
        return True
    except Exception:
        return False
