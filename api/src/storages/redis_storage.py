from abc import ABC, abstractmethod
from functools import lru_cache
from typing import Any, Optional

from opentelemetry import trace
from redis.asyncio import Redis

tracer = trace.get_tracer(__name__)

rds: Optional["RedisCache"] = None


class ABCCache(ABC):
    """
    Абстрактный класс кэша
    """

    @abstractmethod
    async def get(self, key: str) -> Any:
        raise NotImplementedError

    @abstractmethod
    async def put(self, key: str, value: str, ex: int | None = None) -> None:
        raise NotImplementedError


class RedisCache(ABCCache):
    """
    Реализация кэширования на базе Redis
    """

    def __init__(self, redis_client: Redis):
        self.redis_client: Redis = redis_client

    async def get(self, key: str) -> Any:
        with tracer.start_as_current_span("redis"):
            return await self.redis_client.get(key)

    async def put(self, key: str, value: str, ex: int | None = None) -> None:
        with tracer.start_as_current_span("redis"):
            await self.redis_client.set(key, value, ex=ex)


@lru_cache()
def get_cache() -> RedisCache:
    return RedisCache(rds)
