from functools import wraps
from http import HTTPStatus
from typing import Type
import uuid

from flask import abort, g, jsonify, make_response, request
from jose import jwt
from pydantic import ValidationError

from buses.bus import get_eventbus
from core.config import settings
from core.loggers import logger
from schemas.entity import BaseEvent

eventbus = get_eventbus()


def exception_handler(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as err:
            logger.exception(err)
            abort(make_response(
                jsonify({"error": "Internal server error"}),
                HTTPStatus.INTERNAL_SERVER_ERROR,
            ))

    return wrapper


def validate_request_headers(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        unauthorized_error = {
            "error": "Unauthorized. Bearer token not specified or invalid"
        }

        bearer_token = request.headers.get("Authorization")
        if bearer_token is None or not bearer_token.startswith("Bearer "):
            return jsonify(unauthorized_error), HTTPStatus.UNAUTHORIZED
        g.token = bearer_token.replace("Bearer ", "", 1)

        try:
            g.token_payload = jwt.decode(
                g.token,
                settings.public_key,
                algorithms=["RS256"],
                audience=settings.app_name,
            )
        except Exception:
            return jsonify(unauthorized_error), HTTPStatus.UNAUTHORIZED

        g.request_id = request.headers.get("X-Request-Id")
        if g.request_id is None:
            return (
                jsonify({"error": "Header X-Request-Id not specified"}),
                HTTPStatus.BAD_REQUEST,
            )

        data = request.get_json(force=True, silent=True) or dict()
        data["event_id"] = uuid.uuid4()
        data["request_id"] = g.request_id
        data["user_id"] = g.token_payload["sub"]
        g.request_data = data

        return func(*args, **kwargs)

    return wrapper


def proccess_event(event_model: Type[BaseEvent], event_data: dict):
    try:
        event = event_model.model_validate(event_data)
    except ValidationError as err:
        return (
            jsonify({"errors": err.errors()}), HTTPStatus.UNPROCESSABLE_ENTITY
        )

    eventbus.produce_event(event)

    return "", HTTPStatus.OK
