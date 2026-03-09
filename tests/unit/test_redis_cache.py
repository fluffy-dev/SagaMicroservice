import pytest
import fakeredis.aioredis

from src.libs.cache.redis_backend import RedisCacheBackend


@pytest.fixture
async def cache_backend():
    """Creates a RedisCacheBackend backed by an in-memory fake Redis."""
    client = fakeredis.aioredis.FakeRedis()
    backend = RedisCacheBackend(redis_client=client)
    yield backend
    await client.aclose()


@pytest.mark.asyncio
async def test_set_and_get(cache_backend):
    await cache_backend.set("key1", "value1")

    result = await cache_backend.get("key1")

    assert result == "value1"


@pytest.mark.asyncio
async def test_get_returns_none_for_missing_key(cache_backend):
    result = await cache_backend.get("nonexistent")

    assert result is None


@pytest.mark.asyncio
async def test_set_with_ttl(cache_backend):
    await cache_backend.set("ttl_key", "ttl_value", ttl=300)

    result = await cache_backend.get("ttl_key")

    assert result == "ttl_value"


@pytest.mark.asyncio
async def test_delete_removes_key(cache_backend):
    await cache_backend.set("to_delete", "value")

    await cache_backend.delete("to_delete")
    result = await cache_backend.get("to_delete")

    assert result is None


@pytest.mark.asyncio
async def test_exists_returns_true_for_existing_key(cache_backend):
    await cache_backend.set("existing", "value")

    assert await cache_backend.exists("existing") is True


@pytest.mark.asyncio
async def test_exists_returns_false_for_missing_key(cache_backend):
    assert await cache_backend.exists("missing") is False
