import pytest
import asyncio
from typing import AsyncGenerator
from unittest.mock import AsyncMock

from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from src.app import app
from src.libs.base_model import Base
from src.config.database.engine import db_helper

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    TEST_DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=None
)

TestingSessionLocal = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
)


@pytest.fixture(scope="session")
def event_loop():
    """Creates an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Creates a fresh database session for each test.

    Handles the creation and dropping of tables for isolation.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
def mock_event_publisher():
    """Creates a mock event publisher for integration tests."""
    publisher = AsyncMock()
    publisher.publish = AsyncMock()
    publisher.start = AsyncMock()
    publisher.stop = AsyncMock()
    return publisher


@pytest.fixture(scope="function")
def mock_cache_backend():
    """Creates a mock cache backend for integration tests."""
    cache = AsyncMock()
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock()
    cache.delete = AsyncMock()
    cache.exists = AsyncMock(return_value=False)
    return cache


@pytest.fixture(scope="function")
async def client(
    db_session,
    mock_event_publisher,
    mock_cache_backend,
) -> AsyncGenerator[AsyncClient, None]:
    """Creates an asynchronous HTTP client for E2E testing.

    Overrides the production database dependency with the test session
    and injects mock Kafka/Redis dependencies into app.state.
    """
    async def override_get_db():
        yield db_session

    app.dependency_overrides[db_helper.get_session] = override_get_db

    from src.checkout.dependencies.events.publisher import get_event_publisher
    from src.checkout.dependencies.cache.backend import get_cache_backend

    app.dependency_overrides[get_event_publisher] = lambda: mock_event_publisher
    app.dependency_overrides[get_cache_backend] = lambda: mock_cache_backend

    app.state.event_publisher = mock_event_publisher
    app.state.cache_backend = mock_cache_backend

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="https://test"
    ) as c:
        yield c

    app.dependency_overrides.clear()
