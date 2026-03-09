import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from redis.asyncio import Redis

from src.config.kafka import settings as kafka_settings
from src.config.redis import settings as redis_settings
from src.libs.event_bus import KafkaEventPublisher
from src.libs.cache import RedisCacheBackend
from src.checkout.consumers import CheckoutEventConsumer

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manages application startup and shutdown lifecycle.

    Initializes Kafka producer, Redis connection pool, and background
    consumer tasks on startup. Tears them down gracefully on shutdown.

    Args:
        app: The FastAPI application instance.

    Yields:
        Control to the application after startup is complete.
    """
    event_publisher = KafkaEventPublisher(
        bootstrap_servers=kafka_settings.bootstrap_servers,
    )
    await event_publisher.start()
    app.state.event_publisher = event_publisher

    redis_client = Redis.from_url(redis_settings.url, decode_responses=False)
    cache_backend = RedisCacheBackend(redis_client=redis_client)
    app.state.cache_backend = cache_backend
    app.state.redis_client = redis_client
    logger.info(f"Redis connected at {redis_settings.url}")

    checkout_consumer = CheckoutEventConsumer(
        bootstrap_servers=kafka_settings.bootstrap_servers,
        topic=kafka_settings.checkout_topic,
        group_id=kafka_settings.consumer_group_id,
    )
    consumer_task = asyncio.create_task(checkout_consumer.start())
    app.state.checkout_consumer = checkout_consumer

    yield

    await checkout_consumer.stop()
    consumer_task.cancel()
    try:
        await consumer_task
    except asyncio.CancelledError:
        pass

    await event_publisher.stop()
    await redis_client.aclose()
    logger.info("All resources cleaned up")
