import pytest
from unittest.mock import AsyncMock, MagicMock

from src.libs.event_bus.kafka_producer import KafkaEventPublisher


@pytest.fixture
def mock_aiokafka_producer(monkeypatch):
    """Patches AIOKafkaProducer to return a mock for unit testing."""
    mock_producer = AsyncMock()
    mock_producer.start = AsyncMock()
    mock_producer.stop = AsyncMock()
    mock_producer.send_and_wait = AsyncMock()

    mock_cls = MagicMock(return_value=mock_producer)
    monkeypatch.setattr(
        "src.libs.event_bus.kafka_producer.AIOKafkaProducer",
        mock_cls,
    )
    return mock_producer


@pytest.mark.asyncio
async def test_publisher_start_creates_and_starts_producer(mock_aiokafka_producer):
    publisher = KafkaEventPublisher(bootstrap_servers="localhost:9092")

    await publisher.start()

    mock_aiokafka_producer.start.assert_awaited_once()


@pytest.mark.asyncio
async def test_publisher_stop_shuts_down_producer(mock_aiokafka_producer):
    publisher = KafkaEventPublisher(bootstrap_servers="localhost:9092")
    await publisher.start()

    await publisher.stop()

    mock_aiokafka_producer.stop.assert_awaited_once()


@pytest.mark.asyncio
async def test_publish_sends_message_to_topic(mock_aiokafka_producer):
    publisher = KafkaEventPublisher(bootstrap_servers="localhost:9092")
    await publisher.start()

    payload = {"event_type": "test.event", "data": "test_value"}
    await publisher.publish(topic="test.topic", key="key-1", value=payload)

    mock_aiokafka_producer.send_and_wait.assert_awaited_once_with(
        "test.topic", value=payload, key="key-1"
    )


@pytest.mark.asyncio
async def test_publish_raises_if_not_started():
    publisher = KafkaEventPublisher(bootstrap_servers="localhost:9092")

    with pytest.raises(RuntimeError, match="not started"):
        await publisher.publish(
            topic="test.topic",
            key="key-1",
            value={"data": "test"},
        )
