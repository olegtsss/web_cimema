from typing import Optional

from redis.asyncio import Redis

rds: Optional[Redis] = None


def get_redis() -> Redis:
    return rds
