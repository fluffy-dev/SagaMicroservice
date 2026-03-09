from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Kafka broker configuration loaded from environment variables."""

    bootstrap_servers: str = Field("kafka:9092", alias="KAFKA_BOOTSTRAP_SERVERS")
    checkout_topic: str = Field("checkout.events", alias="KAFKA_CHECKOUT_TOPIC")
    saga_topic: str = Field("saga.events", alias="KAFKA_SAGA_TOPIC")
    consumer_group_id: str = Field("saga-microservice", alias="KAFKA_CONSUMER_GROUP_ID")


settings = Settings()
