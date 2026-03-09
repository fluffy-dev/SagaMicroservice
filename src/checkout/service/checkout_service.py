import json
import logging

from src.checkout.dto import CheckoutRequestDTO, CreateOrderDTO, OrderDTO, UpdateOrderDTO
from src.checkout.models.order import OrderStatus
from src.checkout.entities import SagaContext
from src.checkout.dependencies.order.repository import IOrderRepository
from src.checkout.dependencies.events.publisher import IEventPublisherDep
from src.checkout.dependencies.cache.backend import ICacheBackendDep
from src.checkout.events import (
    CheckoutCompletedEvent,
    CheckoutFailedEvent,
    build_checkout_event,
)
from src.libs.saga import SagaOrchestrator, SagaExecutionError
from src.checkout.service.steps import PaymentStep, InventoryStep, ShippingStep
from src.config.kafka import settings as kafka_settings
from src.config.redis import settings as redis_settings

logger = logging.getLogger(__name__)


class CheckoutService:
    """Service layer coordinating checkout operations using the Saga Pattern.

    Integrates Kafka event publishing for domain events and Redis caching
    for idempotency and fast order lookups.
    """

    def __init__(
        self,
        order_repo: IOrderRepository,
        event_publisher: IEventPublisherDep,
        cache: ICacheBackendDep,
    ) -> None:
        """Initializes the CheckoutService with required dependencies.

        Args:
            order_repo: The repository handling order persistence.
            event_publisher: The event publisher for domain events.
            cache: The cache backend for idempotency and order caching.
        """
        self.order_repo = order_repo
        self.event_publisher = event_publisher
        self.cache = cache

    def _build_idempotency_key(self, request: CheckoutRequestDTO) -> str:
        """Constructs a deterministic cache key for checkout deduplication.

        Args:
            request: The checkout request to derive the key from.

        Returns:
            A string key uniquely identifying this checkout attempt.
        """
        return f"checkout:idemp:{request.user_id}:{request.item_id}:{request.quantity}:{request.price}"

    def _build_order_cache_key(self, order_id: int) -> str:
        """Constructs the cache key for a specific order.

        Args:
            order_id: The order primary key.

        Returns:
            A string cache key for the order.
        """
        return f"checkout:order:{order_id}"

    async def get_order(self, order_id: int) -> OrderDTO | None:
        """Retrieves an order by ID, checking Redis cache first.

        Args:
            order_id: The order primary key.

        Returns:
            The order DTO if found, None otherwise.
        """
        cache_key = self._build_order_cache_key(order_id)
        cached = await self.cache.get(cache_key)
        if cached:
            logger.info(f"Order {order_id} served from cache")
            return OrderDTO.model_validate_json(cached)

        order = await self.order_repo.get(order_id)
        if order:
            await self.cache.set(
                cache_key,
                order.model_dump_json(),
                ttl=redis_settings.checkout_cache_ttl,
            )
        return order

    async def process_checkout(self, request: CheckoutRequestDTO) -> OrderDTO:
        """Processes a checkout request with idempotency and event publishing.

        Checks for duplicate requests via Redis before executing the saga.
        Publishes domain events to Kafka upon completion or failure.

        Args:
            request: The checkout details including items and user identifiers.

        Returns:
            The processed order representation.

        Raises:
            Exception: If an unhandled failure occurs during checkout orchestration.
        """
        idemp_key = self._build_idempotency_key(request)
        cached_order = await self.cache.get(idemp_key)
        if cached_order:
            logger.info(f"Idempotent checkout hit for key={idemp_key}")
            return OrderDTO.model_validate_json(cached_order)

        order_dto = await self.order_repo.create(CreateOrderDTO(
            user_id=request.user_id,
            item_id=request.item_id,
            quantity=request.quantity,
            price=request.price,
        ))

        context = SagaContext(
            order_id=order_dto.id,
            user_id=request.user_id,
            item_id=request.item_id,
            quantity=request.quantity,
            price=request.price,
            fail_at_step=request.fail_at_step,
        )

        orchestrator = SagaOrchestrator[SagaContext](
            steps=[PaymentStep(), InventoryStep(), ShippingStep()],
            event_publisher=self.event_publisher,
            event_topic=kafka_settings.saga_topic,
        )

        try:
            logger.info(f"Starting checkout Saga for order {order_dto.id}")
            await orchestrator.execute(context)

            logger.info(f"Saga completed successfully for order {order_dto.id}")
            final_order = await self.order_repo.update(
                UpdateOrderDTO(status=OrderStatus.COMPLETED), pk=order_dto.id
            )

            await self._publish_event(
                CheckoutCompletedEvent,
                final_order,
                request,
            )
            await self._cache_order(idemp_key, final_order)
            return final_order

        except SagaExecutionError as e:
            logger.error(f"Saga failed during checkout for order {order_dto.id}")
            final_order = await self.order_repo.update(
                UpdateOrderDTO(status=OrderStatus.FAILED), pk=order_dto.id
            )

            await self._publish_event(
                CheckoutFailedEvent,
                final_order,
                request,
                failed_at_step=e.step_name,
            )
            await self._cache_order(idemp_key, final_order)
            return final_order

        except Exception as e:
            logger.critical(f"Unexpected error in CheckoutService: {e}")
            raise

    async def _publish_event(
        self,
        event_cls: type,
        order: OrderDTO,
        request: CheckoutRequestDTO,
        **kwargs,
    ) -> None:
        """Publishes a checkout domain event to Kafka.

        Args:
            event_cls: The event class to instantiate.
            order: The order DTO providing event data.
            request: The original checkout request.
            **kwargs: Additional fields for the event.
        """
        event_data = build_checkout_event(
            event_cls,
            order_id=order.id,
            user_id=request.user_id,
            item_id=request.item_id,
            quantity=request.quantity,
            price=request.price,
            **kwargs,
        )
        await self.event_publisher.publish(
            topic=kafka_settings.checkout_topic,
            key=str(order.id),
            value=event_data,
        )

    async def _cache_order(self, idemp_key: str, order: OrderDTO) -> None:
        """Caches the order for idempotency and fast lookups.

        Args:
            idemp_key: The idempotency cache key.
            order: The order DTO to cache.
        """
        order_json = order.model_dump_json()
        ttl = redis_settings.checkout_cache_ttl

        await self.cache.set(idemp_key, order_json, ttl=ttl)
        await self.cache.set(
            self._build_order_cache_key(order.id), order_json, ttl=ttl
        )
