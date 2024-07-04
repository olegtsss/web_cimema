from http import HTTPStatus

from flask import Blueprint, g, jsonify, request

from api.v1.utils import (
  exception_handler, proccess_event, validate_request_headers
)
from schemas.entity import (
    ChangeQualityEvent,
    CreateFilmRatingEvent,
    CreateFilmReviewEvent,
    CreateFilmReviewRatingEvent,
    CreateUserBookmarkEvent,
    DeleteFilmRatingEvent,
    DeleteFilmReviewEvent,
    DeleteFilmReviewRatingEvent,
    DeleteUserBookmarkEvent,
    FullyWatchEvent,
    UpdateFilmRatingEvent,
    UpdateFilmReviewEvent,
    UpdateFilmReviewRatingEvent,
)
from services.service import get_service

service = get_service()

router = Blueprint("films", __name__)


@router.route("/<film_id>/rating", methods=["GET"])
@exception_handler
@validate_request_headers
def get_film_rating(film_id: str):
    """Ручка получения рейтинга произведения."""
    film_rating = service.get_film_rating(film_id)
    return jsonify(film_rating), HTTPStatus.OK


@router.route("/<film_id>/rating", methods=["POST", "PATCH", "DELETE"])
@exception_handler
@validate_request_headers
def process_film_rating_event(film_id: str):
    """Ручка создания события типа "оценка произведения".

    Тип события определяется типом запроса, где POST - создание,
    PATCH - обновление, DELETE - удаление.
    """
    if request.method == "POST":
        event_model = CreateFilmRatingEvent
    elif request.method == "PATCH":
        event_model = UpdateFilmRatingEvent  # type: ignore
    else:
        event_model = DeleteFilmRatingEvent  # type: ignore

    event_data = g.request_data
    event_data["payload"]["film_id"] = film_id

    return proccess_event(event_model, event_data)  # type: ignore


@router.route("/<film_id>/reviews", methods=["GET"])
@exception_handler
@validate_request_headers
def get_film_reviews(film_id: str):
    """Ручка получения отзывов (рецензий) на произведения."""
    film_reviews = service.get_film_reviews(film_id)
    return jsonify(film_reviews), HTTPStatus.OK


@router.route("/<film_id>/reviews", methods=["POST"])
@exception_handler
@validate_request_headers
def create_film_review_event(film_id: str):
    """Ручка создания события типа "отзыв (рецензия) на произведение".

    Тип события определяется типом запроса, где POST - создание,
    PATCH - обновление, DELETE - удаление.
    """
    event_model = CreateFilmReviewEvent

    event_data = g.request_data
    event_data["payload"]["film_id"] = film_id

    return proccess_event(event_model, event_data)


@router.route("/reviews/<review_id>/", methods=["PATCH", "DELETE"])
@exception_handler
@validate_request_headers
def process_film_review_event(review_id: str):
    """Ручка создания события типа "отзыв (рецензия) на произведение".

    Тип события определяется типом запроса, где POST - создание,
    PATCH - обновление, DELETE - удаление.
    """
    if request.method == "PATCH":
        event_model = UpdateFilmReviewEvent  # type: ignore
    else:
        event_model = DeleteFilmReviewEvent  # type: ignore

    event_data = g.request_data
    event_data["payload"]["review_id"] = review_id

    return proccess_event(event_model, event_data)


@router.route(
    "/reviews/<review_id>/rating",
    methods=["POST", "PATCH", "DELETE"],
)
@exception_handler
@validate_request_headers
def proccess_film_review_rating_event(review_id: str):
    """Ручка создания события типа "оценка отзыва (рецензии)".

    Тип события определяется типом запроса, где POST - создание,
    PATCH - обновление, DELETE - удаление.
    """
    if request.method == "POST":
        event_model = CreateFilmReviewRatingEvent
    elif request.method == "PATCH":
        event_model = UpdateFilmReviewRatingEvent  # type: ignore
    else:
        event_model = DeleteFilmReviewRatingEvent  # type: ignore

    event_data = g.request_data
    event_data["payload"]["review_id"] = review_id

    return proccess_event(event_model, event_data)


@router.route("/bookmarks", methods=["GET"])
@exception_handler
@validate_request_headers
def get_user_bookmarks():
    """Ручка получения произведений, добавленных в закладки."""
    bookmarks = service.get_user_bookmarks(g.request_data["user_id"])
    return jsonify(bookmarks), HTTPStatus.OK


@router.route("/<film_id>/bookmarks", methods=["POST", "DELETE"])
@exception_handler
@validate_request_headers
def proccess_user_bookmark_event(film_id: str):
    """Ручка создания события типа "произведение в закладках".

    Тип события определяется типом запроса, где POST - создание,
    PATCH - обновление, DELETE - удаление.
    """
    if request.method == "POST":
        event_model = CreateUserBookmarkEvent
    else:
        event_model = DeleteUserBookmarkEvent  # type: ignore

    event_data = g.request_data
    event_data["payload"]["film_id"] = film_id

    return proccess_event(event_model, event_data)


@router.route("/<film_id>/fully_watched", methods=["POST"])
@exception_handler
@validate_request_headers
def create_fully_watched_event(film_id: str):
    """Ручка создания события типа "произведение просмотрено полностью"."""
    event_model = FullyWatchEvent

    event_data = g.request_data
    event_data["payload"]["film_id"] = film_id

    return proccess_event(event_model, event_data)


@router.route("/<film_id>/quality_changed", methods=["POST"])
@exception_handler
@validate_request_headers
def create_quality_changed_event(film_id: str):
    """Ручка создания события типа "смена качества произведения"."""
    event_model = ChangeQualityEvent

    event_data = g.request_data
    event_data["payload"]["film_id"] = film_id

    return proccess_event(event_model, event_data)
