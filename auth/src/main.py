from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI, Request, status
from fastapi.exceptions import ValidationException
from fastapi.responses import JSONResponse
from fastapi_limiter import FastAPILimiter
from loguru import logger
from redis.asyncio import Redis
from redis.backoff import ExponentialBackoff
from redis.exceptions import BusyLoadingError, ConnectionError, TimeoutError
from redis.retry import Retry

from api.v1.auth import router as auth_router
from api.v1.oauth import router as oauth_router
from api.v1.roles import router as roles_router
from api.v1.users import router as users_router
from core.config import settings
from core.loggers import LOGGER_DEBUG, LOGGER_ERROR
from storages import postgres, redis_storage

logger.add(**LOGGER_DEBUG)
logger.add(**LOGGER_ERROR)


@asynccontextmanager
async def lifespan(_: FastAPI):
    redis_storage.rds = Redis.from_url(
        url=settings.redis_dsn,
        retry=Retry(
            backoff=ExponentialBackoff(),
            retries=settings.backoff_tries,
            supported_errors=(BusyLoadingError, ConnectionError, TimeoutError),
        ),
    )
    await FastAPILimiter.init(redis_storage.rds, prefix=settings.app_name)

    yield

    await FastAPILimiter.close()
    await postgres.engine.dispose()
    await redis_storage.rds.aclose()


app = FastAPI(title=settings.app_name, lifespan=lifespan)

v1_router = APIRouter(prefix="/api/v1")
v1_router.include_router(auth_router)
v1_router.include_router(oauth_router)
v1_router.include_router(users_router)
v1_router.include_router(roles_router)
app.include_router(router=v1_router)


@app.exception_handler(ValidationException)
async def validation_error_handler(_: Request, exc: ValidationException):
    logger.error(exc)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=exc.errors(),
    )


@app.exception_handler(Exception)
async def exception_handler(_: Request, exc: Exception):
    logger.exception(exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app="main:app",
        host="0.0.0.0",
        port=8000
    )
