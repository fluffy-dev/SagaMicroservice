from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Redis connection and cache configuration loaded from environment variables."""

    host: str = Field("redis", alias="REDIS_HOST")
    port: int = Field(6379, alias="REDIS_PORT")
    db: int = Field(0, alias="REDIS_DB")
    password: Optional[str] = Field(None, alias="REDIS_PASSWORD")
    checkout_cache_ttl: int = Field(300, alias="REDIS_CHECKOUT_CACHE_TTL")

    @property
    def url(self) -> str:
        """Builds the Redis connection URL from individual settings."""
        auth = f":{self.password}@" if self.password else ""
        return f"redis://{auth}{self.host}:{self.port}/{self.db}"


settings = Settings()
