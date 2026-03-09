import logging

from src.libs.event_bus import KafkaEventConsumer

logger = logging.getLogger(__name__)


class CheckoutEventConsumer(KafkaEventConsumer):
    """Consumes checkout domain events from Kafka for downstream processing."""

    async def process_message(self, key: bytes, value: dict) -> None:
        """Handles a single checkout event received from Kafka.

        Args:
            key: The raw message key bytes.
            value: The deserialized event payload dictionary.
        """
        event_type = value.get("event_type", "unknown")
        order_id = value.get("order_id")

        logger.info(
            f"[CheckoutConsumer] Received event_type={event_type} "
            f"for order_id={order_id}"
        )

        if event_type == "checkout.completed":
            logger.info(
                f"[CheckoutConsumer] Order {order_id} completed successfully. "
                f"Ready for downstream processing (notifications, analytics, etc.)"
            )
        elif event_type == "checkout.failed":
            failed_step = value.get("failed_at_step", "unknown")
            logger.warning(
                f"[CheckoutConsumer] Order {order_id} failed at step={failed_step}. "
                f"Compensation was triggered."
            )
