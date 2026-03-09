import json
import logging
from abc import ABC, abstractmethod
from typing import Optional

from aiokafka import AIOKafkaConsumer

logger = logging.getLogger(__name__)


class KafkaEventConsumer(ABC):
    """Abstract base class for Kafka consumers with a pluggable message handler."""

    def __init__(
        self,
        bootstrap_servers: str,
        topic: str,
        group_id: str,
    ) -> None:
        """Initializes the consumer with broker and subscription settings.

        Args:
            bootstrap_servers: Comma-separated Kafka broker addresses.
            topic: The Kafka topic to subscribe to.
            group_id: The consumer group identifier for offset management.
        """
        self._bootstrap_servers = bootstrap_servers
        self._topic = topic
        self._group_id = group_id
        self._consumer: Optional[AIOKafkaConsumer] = None
        self._running = False

    async def start(self) -> None:
        """Creates the consumer, subscribes to the topic, and begins polling."""
        self._consumer = AIOKafkaConsumer(
            self._topic,
            bootstrap_servers=self._bootstrap_servers,
            group_id=self._group_id,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        )
        await self._consumer.start()
        self._running = True
        logger.info(f"Kafka consumer started on topic={self._topic}, group={self._group_id}")

        try:
            async for message in self._consumer:
                if not self._running:
                    break
                await self.process_message(message.key, message.value)
        finally:
            await self._consumer.stop()

    async def stop(self) -> None:
        """Signals the consumer loop to terminate gracefully."""
        self._running = False
        logger.info(f"Kafka consumer stopping for topic={self._topic}")

    @abstractmethod
    async def process_message(self, key: bytes, value: dict) -> None:
        """Processes a single deserialized message from Kafka.

        Args:
            key: The raw message key bytes.
            value: The deserialized JSON payload.
        """
        ...
