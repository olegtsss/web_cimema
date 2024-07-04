import logging

from flasgger import Swagger  # type: ignore
from flask import Flask, request
import logstash  # type: ignore
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

from api.v1.events import router as event_router
from api.v1.films import router as film_router
from core.config import settings
from core.loggers import logger

if settings.sentry_dsn is not None:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        enable_tracing=True,
        integrations=[FlaskIntegration(transaction_style="url")],
    )


class RequestIdFilter(logging.Filter):
    def filter(self, record):
        record.request_id = request.headers.get("X-Request-Id")
        return True


logger.addFilter(RequestIdFilter())
logger.addHandler(logstash.LogstashHandler(
    settings.logstash_host, settings.logstash_port, version=2
))


app = Flask(__name__, static_url_path="/static")
app.logger = logger
app.register_blueprint(
    event_router, url_prefix=settings.api_v1_prefix + "/events"
)
app.register_blueprint(
    film_router, url_prefix=settings.api_v1_prefix + "/films"
)
app.config["SWAGGER"] = {
    "title": "UGC documentation",
    "static_url_path": "/static/swagger",
    "static_folder": settings.static_dir.joinpath("swagger"),
}

swagger_config = {
    "headers": [
    ],
    "specs": [
        {
            "endpoint": 'apispec',
            "route": '/static/swagger/apispec.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "swagger_ui": True,
    "specs_route": "/docs"
}

swagger = Swagger(app, config=swagger_config)


@app.before_request
def check_request_id():
    request_id = request.headers.get("X-Request-Id")
    if not request_id:
        raise RuntimeError("Missed required 'X-Request-Id' header")


@app.after_request
def log_request(response):
    params = {
        "ip": request.headers.get("X-Real-Ip"),
        "method": request.method,
        "path": request.full_path,
        "request_id": request.headers.get("X-Request-Id"),
        "eventbus": request.headers.get("Eventbus"),
        "status": response.status,
    }
    logger.info(f"Access: {params}")

    return response
