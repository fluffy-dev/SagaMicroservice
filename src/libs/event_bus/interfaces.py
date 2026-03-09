from typing import Protocol, runtime_checkable


@runtime_checkable
class IEventPublisher(Protocol):
    """Protocol defining the contract for publishing events to a message broker."""

    async def publish(self, topic: str, key: str, value: dict) -> None:
        """Publishes a single event to the specified topic.

        Args:
            topic: The target topic/channel name.
            key: The partitioning key for the event.
            value: The event payload as a dictionary.
        """
        ...

    async def start(self) -> None:
        """Initializes the underlying connection to the broker."""
        ...

    async def stop(self) -> None:
        """Gracefully shuts down the broker connection."""
        ...


@runtime_checkable
class IEventConsumer(Protocol):
    """Protocol defining the contract for consuming events from a message broker."""

    async def start(self) -> None:
        """Starts the consumer loop, subscribing to the configured topics."""
        ...

    async def stop(self) -> None:
        """Gracefully stops the consumer and releases resources."""
        ...
