from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI, Request, status
from fastapi.exceptions import ValidationException
from fastapi.responses import JSONResponse
from fastapi_limiter import FastAPILimiter
from loguru import logger

from api.v1.notifications import router as notification_router
from api.v1.templates import router as template_router
from core.config import settings
from storages.cache import cache
from storages.storage import storage


@asynccontextmanager
async def lifespan(_: FastAPI):
    await FastAPILimiter.init(cache, prefix=settings.app_name)
    yield

    await FastAPILimiter.close()
    await storage.engine.dispose()
    await cache.aclose()


app = FastAPI(title=settings.app_name, lifespan=lifespan)

v1_router = APIRouter(prefix=settings.api_v1_prefix)
v1_router.include_router(notification_router)
v1_router.include_router(template_router)
app.include_router(router=v1_router)


@app.exception_handler(ValidationException)
async def validation_error_handler(request: Request, exc: ValidationException):
    logger.error(exc)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=exc.errors(),
    )


@app.exception_handler(Exception)
async def exception_handler(request: Request, exc: Exception):
    logger.exception(exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )
