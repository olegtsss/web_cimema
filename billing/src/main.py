from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI, Depends, Request, Response, status
from fastapi.exceptions import (
    HTTPException,
    RequestValidationError,
    ResponseValidationError,
)
from fastapi.exception_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
)
from fastapi.responses import JSONResponse
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
from loguru import logger
import sentry_sdk
from sentry_sdk.integrations.loguru import LoguruIntegration

from api.v1.orders import router as oreder_router
from api.v1.plans import router as plan_router
from api.v1.subs import router as sub_router
from api.v1.webhooks import router as webhook_router
from core.config import settings
from core.loggers import ERROR_FILE_LOGGER, STDOUT_LOGGER, TRACE_FILE_LOGGER
from services.auth import auth_service
from storages.cache import cache
from storages.storage import storage


# === Sentry integration ===


if settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        integrations=[LoguruIntegration()],
    )


# === Loggers settings ===


logger.remove()
logger.add(**STDOUT_LOGGER)
logger.add(**TRACE_FILE_LOGGER)
logger.add(**ERROR_FILE_LOGGER)


# === Init app ===


@asynccontextmanager
async def lifespan(_: FastAPI):
    await FastAPILimiter.init(cache, prefix=settings.app_name)

    yield

    await FastAPILimiter.close()
    if not auth_service.session.closed:
        await auth_service.session.close()
    await storage.engine.dispose()
    await cache.aclose()


app = FastAPI(
    title=settings.app_name,
    dependencies=[
        Depends(
            RateLimiter(times=settings.limiter_times, seconds=settings.limiter_seconds)
        )
    ],
    lifespan=lifespan,
)


# === API routes ===


v1_router = APIRouter(prefix=settings.api_v1_prefix)
v1_router.include_router(oreder_router)
v1_router.include_router(plan_router)
v1_router.include_router(sub_router)
v1_router.include_router(webhook_router)
app.include_router(router=v1_router)


# === Add requests log middleware ===


@app.middleware("http")
async def log_middleware(request: Request, call_next):
    msg = (
        "{client} - '{method} {path} {protocol}'"
        " {status} {response_length}"
        " '{request_id}' '{referer}' '{user_agent}'"
    )
    msg_params = {
        "client": request.client.host,
        "method": request.method,
        "path": request.url.path,
        "protocol": request.scope["http_version"],
        "status": "-",
        "response_length": "-",
        "request_id": request.headers.get("request-id", "-"),
        "referer": request.headers.get("referer", "-"),
        "user_agent": request.headers.get("user-agent", "-"),
    }

    # logger.debug(msg.format(**msg_params))

    response: Response = await call_next(request)

    msg_params["status"] = response.status_code
    msg_params["response_length"] = response.headers.get("content-length", "-")

    logger.trace(msg.format(**msg_params))

    return response


# === Exception handling ===


@app.exception_handler(HTTPException)
async def http_err_handler(request: Request, exc: HTTPException) -> Response:
    # TODO log if needed
    return await http_exception_handler(request, exc)


@app.exception_handler(RequestValidationError)
async def request_validation_err_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    logger.error(exc)
    return await request_validation_exception_handler(request, exc)


@app.exception_handler(ResponseValidationError)
async def response_validation_err_handler(
    _: Request, exc: ResponseValidationError
) -> JSONResponse:
    logger.error(exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "INTERNAL_SERVER_ERROR"},
    )


@app.exception_handler(Exception)
async def err_handler(_: Request, exc: Exception) -> JSONResponse:
    logger.exception(exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "INTERNAL_SERVER_ERROR"},
    )
