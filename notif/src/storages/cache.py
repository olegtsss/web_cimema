from redis.asyncio import Redis
from redis.backoff import ExponentialBackoff
from redis.exceptions import BusyLoadingError, ConnectionError, TimeoutError
from redis.retry import Retry

from core.config import settings

cache = Redis.from_url(
    url=settings.redis_dsn,
    retry=Retry(
        backoff=ExponentialBackoff(),
        retries=settings.backoff_tries,
        supported_errors=(BusyLoadingError, ConnectionError, TimeoutError),
    ),
)
