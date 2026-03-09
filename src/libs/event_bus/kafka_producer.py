import json
import logging
from typing import Optional

from aiokafka import AIOKafkaProducer

from src.libs.event_bus.interfaces import IEventPublisher

logger = logging.getLogger(__name__)


class KafkaEventPublisher:
    """Async Kafka producer wrapping aiokafka for structured event publishing."""

    def __init__(self, bootstrap_servers: str) -> None:
        """Initializes the publisher with broker connection settings.

        Args:
            bootstrap_servers: Comma-separated Kafka broker addresses.
        """
        self._bootstrap_servers = bootstrap_servers
        self._producer: Optional[AIOKafkaProducer] = None

    async def start(self) -> None:
        """Creates and starts the underlying AIOKafkaProducer."""
        self._producer = AIOKafkaProducer(
            bootstrap_servers=self._bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            key_serializer=lambda k: k.encode("utf-8") if k else None,
        )
        await self._producer.start()
        logger.info(f"Kafka producer connected to {self._bootstrap_servers}")

    async def stop(self) -> None:
        """Flushes pending messages and closes the producer connection."""
        if self._producer:
            await self._producer.stop()
            logger.info("Kafka producer stopped")

    async def publish(self, topic: str, key: str, value: dict) -> None:
        """Publishes a JSON-serialized event to the specified Kafka topic.

        Args:
            topic: The Kafka topic to publish to.
            key: The message key used for partition routing.
            value: The event payload dictionary to serialize as JSON.

        Raises:
            RuntimeError: If the producer has not been started.
        """
        if not self._producer:
            raise RuntimeError("Kafka producer is not started")

        await self._producer.send_and_wait(topic, value=value, key=key)
        logger.debug(f"Published event to {topic} with key={key}")
