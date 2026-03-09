from typing import Protocol, Optional, runtime_checkable


@runtime_checkable
class ICacheBackend(Protocol):
    """Protocol defining the contract for an async key-value cache."""

    async def get(self, key: str) -> Optional[str]:
        """Retrieves a value by key from the cache.

        Args:
            key: The cache key to look up.

        Returns:
            The cached string value, or None if not found.
        """
        ...

    async def set(self, key: str, value: str, ttl: Optional[int] = None) -> None:
        """Stores a value under the given key with an optional TTL.

        Args:
            key: The cache key.
            value: The string value to store.
            ttl: Time-to-live in seconds. None means no expiration.
        """
        ...

    async def delete(self, key: str) -> None:
        """Removes a key from the cache.

        Args:
            key: The cache key to delete.
        """
        ...

    async def exists(self, key: str) -> bool:
        """Checks whether a key exists in the cache.

        Args:
            key: The cache key to check.

        Returns:
            True if the key exists, False otherwise.
        """
        ...
