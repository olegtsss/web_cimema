import json
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional, Union

from loguru import logger

from models.eventbus import Event
from models.nosql import FilmReview, FilmReviewUserRating, FilmUserRating, UserBookmark


class EventSubtype(Enum):
    CREATE_FILM_RATING: str = "create_film_rating"
    UPDATE_FILM_RATING: str = "update_film_rating"
    DELETE_FILM_RATING: str = "delete_film_rating"

    CREATE_FILM_REVIEW: str = "create_film_review"
    UPDATE_FILM_REVIEW: str = "update_film_review"
    DELETE_FILM_REVIEW: str = "delete_film_review"

    CREATE_FILM_REVIEW_RATING: str = "create_film_review_rating"
    UPDATE_FILM_REVIEW_RATING: str = "update_film_review_rating"
    DELETE_FILM_REVIEW_RATING: str = "delete_film_review_rating"

    CREATE_BOOKMARK: str = "create_bookmark"
    DELETE_BOOKMARK: str = "delete_bookmark"


def transform_event_to_nosql(
    event: Event,
) -> Optional[Union[FilmUserRating, FilmReview, FilmReviewUserRating, UserBookmark]]:
    try:
        current_even = event.model_dump()
        event_subtype = current_even.get("event_subtype")
        payload = current_even.get("payload")

        # FilmUserRating
        if event_subtype == EventSubtype.CREATE_FILM_RATING.value:
            return FilmUserRating(
                film_id=str(payload.get("film_id")),
                user_id=str(current_even.get("user_id")),
                value=payload.get("value"),
                created_at=datetime.now(),
                updated_at=None,
            )
        if event_subtype == EventSubtype.UPDATE_FILM_RATING.value:
            return FilmUserRating(
                film_id=str(payload.get("film_id")),
                user_id=str(current_even.get("user_id")),
                value=payload.get("value"),
                updated_at=datetime.now(),
                created_at=None,
            )
        if event_subtype == EventSubtype.DELETE_FILM_RATING.value:
            return FilmUserRating(
                film_id=str(payload.get("film_id")),
                user_id=str(current_even.get("user_id")),
                value=None,
                updated_at=None,
                created_at=None,
            )

        # FilmReview
        if event_subtype == EventSubtype.CREATE_FILM_REVIEW.value:
            return FilmReview(
                film_id=str(payload.get("film_id")),
                user_id=str(current_even.get("user_id")),
                value=payload.get("value"),
                created_at=datetime.now(),
                updated_at=None,
            )
        if event_subtype == EventSubtype.UPDATE_FILM_REVIEW.value:
            return FilmReview(
                film_id=str(payload.get("film_id")),
                user_id=str(current_even.get("user_id")),
                value=payload.get("value"),
                updated_at=datetime.now(),
                created_at=None,
            )
        if event_subtype == EventSubtype.DELETE_FILM_REVIEW.value:
            return FilmReview(
                film_id=str(payload.get("film_id")),
                user_id=str(current_even.get("user_id")),
                value=None,
                updated_at=None,
                created_at=None,
            )

        # ReviewUserRating
        if event_subtype == EventSubtype.CREATE_FILM_REVIEW_RATING.value:
            return FilmReviewUserRating(
                review_id=str(payload.get("review_id")),
                user_id=str(current_even.get("user_id")),
                value=payload.get("value"),
                created_at=datetime.now(),
                updated_at=None,
            )
        if event_subtype == EventSubtype.UPDATE_FILM_REVIEW_RATING.value:
            return FilmReviewUserRating(
                review_id=str(payload.get("review_id")),
                user_id=str(current_even.get("user_id")),
                value=payload.get("value"),
                updated_at=datetime.now(),
                created_at=None,
            )
        if event_subtype == EventSubtype.DELETE_FILM_REVIEW_RATING.value:
            return FilmReviewUserRating(
                review_id=str(payload.get("review_id")),
                user_id=str(current_even.get("user_id")),
                value=None,
                updated_at=None,
                created_at=None,
            )

        # UserBookmark
        if event_subtype == EventSubtype.CREATE_BOOKMARK.value:
            return UserBookmark(
                film_id=str(payload.get("film_id")),
                user_id=str(current_even.get("user_id")),
                created_at=datetime.now(),
            )
        if event_subtype == EventSubtype.DELETE_BOOKMARK.value:
            return UserBookmark(
                film_id=str(payload.get("film_id")),
                user_id=str(current_even.get("user_id")),
                created_at=None,
            )

        logger.warning("Cannot transform unknown event_subtype %s", event_subtype)

    except Exception as err:
        logger.exception(err)
