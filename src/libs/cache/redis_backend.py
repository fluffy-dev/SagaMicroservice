import logging
from typing import Optional

from redis.asyncio import Redis

logger = logging.getLogger(__name__)


class RedisCacheBackend:
    """Async Redis cache backend implementing the ICacheBackend protocol."""

    def __init__(self, redis_client: Redis) -> None:
        """Initializes the backend with an existing async Redis connection.

        Args:
            redis_client: A configured redis.asyncio.Redis instance.
        """
        self._client = redis_client

    async def get(self, key: str) -> Optional[str]:
        """Retrieves a value by key from Redis.

        Args:
            key: The cache key to look up.

        Returns:
            The cached string value, or None if not found.
        """
        value = await self._client.get(key)
        if value is not None:
            logger.debug(f"Cache HIT for key={key}")
            return value.decode("utf-8") if isinstance(value, bytes) else value
        logger.debug(f"Cache MISS for key={key}")
        return None

    async def set(self, key: str, value: str, ttl: Optional[int] = None) -> None:
        """Stores a value in Redis with an optional TTL.

        Args:
            key: The cache key.
            value: The string value to store.
            ttl: Time-to-live in seconds. None means no expiration.
        """
        if ttl:
            await self._client.setex(key, ttl, value)
        else:
            await self._client.set(key, value)
        logger.debug(f"Cache SET for key={key}, ttl={ttl}")

    async def delete(self, key: str) -> None:
        """Removes a key from Redis.

        Args:
            key: The cache key to delete.
        """
        await self._client.delete(key)
        logger.debug(f"Cache DELETE for key={key}")

    async def exists(self, key: str) -> bool:
        """Checks whether a key exists in Redis.

        Args:
            key: The cache key to check.

        Returns:
            True if the key exists, False otherwise.
        """
        result = await self._client.exists(key)
        return bool(result)
