import pytest
from unittest.mock import AsyncMock

from src.checkout.service.checkout_service import CheckoutService
from src.checkout.dto import CheckoutRequestDTO, OrderDTO
from src.checkout.models.order import OrderStatus


@pytest.fixture
def mock_order_repo():
    """Creates a mock order repository with preconfigured responses."""
    repo = AsyncMock()
    repo.create.return_value = OrderDTO(
        id=1,
        user_id=42,
        item_id="SKU-TEST",
        quantity=2,
        price=5000,
        status=OrderStatus.PENDING,
    )
    repo.update.return_value = OrderDTO(
        id=1,
        user_id=42,
        item_id="SKU-TEST",
        quantity=2,
        price=5000,
        status=OrderStatus.COMPLETED,
    )
    return repo


@pytest.fixture
def mock_event_publisher():
    """Creates a mock event publisher."""
    publisher = AsyncMock()
    publisher.publish = AsyncMock()
    return publisher


@pytest.fixture
def mock_cache():
    """Creates a mock cache backend."""
    cache = AsyncMock()
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock()
    cache.exists = AsyncMock(return_value=False)
    return cache


@pytest.fixture
def checkout_service(mock_order_repo, mock_event_publisher, mock_cache):
    """Creates a CheckoutService with all dependencies mocked."""
    return CheckoutService(
        order_repo=mock_order_repo,
        event_publisher=mock_event_publisher,
        cache=mock_cache,
    )


@pytest.mark.asyncio
async def test_idempotent_checkout_returns_cached_order(
    checkout_service, mock_cache
):
    cached_order = OrderDTO(
        id=1,
        user_id=42,
        item_id="SKU-TEST",
        quantity=2,
        price=5000,
        status=OrderStatus.COMPLETED,
    )
    mock_cache.get.return_value = cached_order.model_dump_json()

    request = CheckoutRequestDTO(
        user_id=42,
        item_id="SKU-TEST",
        quantity=2,
        price=5000,
    )
    result = await checkout_service.process_checkout(request)

    assert result.id == 1
    assert result.status == OrderStatus.COMPLETED
    checkout_service.order_repo.create.assert_not_awaited()


@pytest.mark.asyncio
async def test_new_checkout_creates_order_and_publishes_event(
    checkout_service, mock_event_publisher, mock_cache
):
    request = CheckoutRequestDTO(
        user_id=42,
        item_id="SKU-TEST",
        quantity=2,
        price=5000,
    )

    result = await checkout_service.process_checkout(request)

    assert result.status == OrderStatus.COMPLETED
    checkout_service.order_repo.create.assert_awaited_once()
    mock_event_publisher.publish.assert_awaited()
    mock_cache.set.assert_awaited()


@pytest.mark.asyncio
async def test_failed_checkout_publishes_failure_event(
    checkout_service, mock_event_publisher, mock_order_repo
):
    mock_order_repo.update.return_value = OrderDTO(
        id=1,
        user_id=42,
        item_id="SKU-TEST",
        quantity=2,
        price=5000,
        status=OrderStatus.FAILED,
    )

    request = CheckoutRequestDTO(
        user_id=42,
        item_id="SKU-TEST",
        quantity=2,
        price=5000,
        fail_at_step="PaymentStep",
    )
    result = await checkout_service.process_checkout(request)

    assert result.status == OrderStatus.FAILED
    mock_event_publisher.publish.assert_awaited()
