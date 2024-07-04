from contextlib import asynccontextmanager

from elasticsearch import AsyncElasticsearch
from fastapi import APIRouter, FastAPI, Request, status
from fastapi.exceptions import ValidationException
from fastapi.responses import JSONResponse
from loguru import logger
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
)
from redis.asyncio import Redis
from redis.backoff import ExponentialBackoff
from redis.exceptions import BusyLoadingError, ConnectionError, TimeoutError
from redis.retry import Retry

from api.v1 import films, genres, persons
from core.config import settings
from core.loggers import LOGGER_DEBUG, LOGGER_ERROR
from storages import elastic, redis_storage

logger.add(**LOGGER_DEBUG)
logger.add(**LOGGER_ERROR)


def configure_tracer() -> None:
    trace.set_tracer_provider(TracerProvider())
    trace.get_tracer_provider().add_span_processor(
        BatchSpanProcessor(
            JaegerExporter(
                agent_host_name=settings.jaeger_host,
                agent_port=settings.jaeger_port,
            )
        )
    )
    trace.get_tracer_provider().add_span_processor(
        BatchSpanProcessor(ConsoleSpanExporter())
    )


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
    elastic.esm = AsyncElasticsearch(hosts=[settings.es_dsn])

    yield

    await elastic.esm.close()
    await redis_storage.rds.aclose()


configure_tracer()
app = FastAPI(title="PRACTIX", lifespan=lifespan)
FastAPIInstrumentor.instrument_app(app)

v1_router = APIRouter(prefix="/api/v1")
v1_router.include_router(router=films.router)
v1_router.include_router(router=genres.router)
v1_router.include_router(router=persons.router)
app.include_router(router=v1_router)


@app.middleware("http")
async def before_request(request: Request, call_next):
    request_id = request.headers.get("X-Request-Id")
    if not request_id:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": "X-Request-Id is required"},
        )
    response = await call_next(request)
    return response


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
