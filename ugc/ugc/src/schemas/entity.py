from datetime import datetime
from typing import Any, List, Union
from uuid import UUID

from pydantic import BaseModel, computed_field, ConfigDict, Field, HttpUrl


class CustomBaseModel(BaseModel):
    model_config = ConfigDict(
        use_enum_values=True,
        from_attributes=True,
    )


# === Payloads ===


class FilmIdPayload(CustomBaseModel):
    film_id: Union[str, UUID]


class ReviewIdPayload(CustomBaseModel):
    review_id: Union[str, UUID]


class RatingValuePayload(CustomBaseModel):
    value: int = Field(..., ge=0, le=10)


class ReviewValuePayload(CustomBaseModel):
    value: str


class ChangeQualityPayload(FilmIdPayload):
    previous_quality: str
    next_quality: str


class ClickPayload(CustomBaseModel):
    element_id: str
    element_payload: str


class CreateFilmRatingPayload(RatingValuePayload, FilmIdPayload):
    ...


class CreateFilmReviewPayload(ReviewValuePayload, FilmIdPayload):
    ...


class UpdateFilmReviewPayload(ReviewValuePayload, ReviewIdPayload):
    ...


class CreateFilmReviewRatingPayload(RatingValuePayload, ReviewIdPayload):
    ...


# === Events ===


class BaseEvent(CustomBaseModel):
    event_id: Union[str, UUID]
    request_id: Union[str, UUID]
    session_id: Union[str, UUID]
    user_id: Union[str, UUID]
    user_ts: int
    url: HttpUrl
    payload: dict = {}

    @computed_field  # type: ignore
    @property
    def server_ts(self) -> int:
        return int(datetime.now().timestamp())

    @computed_field  # type: ignore
    @property
    def event_type(self) -> Any:
        raise NotImplementedError()

    @computed_field  # type: ignore
    @property
    def event_subtype(self) -> Any:
        raise NotImplementedError()


class ChangeQualityEvent(BaseEvent):
    payload: ChangeQualityPayload  # type: ignore

    @computed_field  # type: ignore
    @property
    def event_type(self) -> str:
        return "custom"

    @computed_field  # type: ignore
    @property
    def event_subtype(self) -> str:
        return "quality_changed"


class FullyWatchEvent(BaseEvent):
    payload: FilmIdPayload  # type: ignore

    @computed_field  # type: ignore
    @property
    def event_type(self) -> str:
        return "custom"

    @computed_field  # type: ignore
    @property
    def event_subtype(self) -> str:
        return "fully_watched"


class ClickEvent(BaseEvent):
    payload: ClickPayload  # type: ignore

    @computed_field  # type: ignore
    @property
    def event_type(self) -> str:
        return "click"

    @computed_field  # type: ignore
    @property
    def event_subtype(self) -> None:
        return None


class VisitEvent(BaseEvent):

    @computed_field  # type: ignore
    @property
    def event_type(self) -> str:
        return "visit"

    @computed_field  # type: ignore
    @property
    def event_subtype(self) -> None:
        return None


class CreateFilmRatingEvent(BaseEvent):
    payload: CreateFilmRatingPayload  # type: ignore

    @computed_field  # type: ignore
    @property
    def event_type(self) -> str:
        return "custom"

    @computed_field  # type: ignore
    @property
    def event_subtype(self) -> str:
        return "create_film_rating"


class UpdateFilmRatingEvent(BaseEvent):
    payload: CreateFilmRatingPayload  # type: ignore

    @computed_field  # type: ignore
    @property
    def event_type(self) -> str:
        return "custom"

    @computed_field  # type: ignore
    @property
    def event_subtype(self) -> str:
        return "update_film_rating"


class DeleteFilmRatingEvent(BaseEvent):
    payload: FilmIdPayload  # type: ignore

    @computed_field  # type: ignore
    @property
    def event_type(self) -> str:
        return "custom"

    @computed_field  # type: ignore
    @property
    def event_subtype(self) -> str:
        return "delete_film_rating"


class CreateFilmReviewEvent(BaseEvent):
    payload: CreateFilmReviewPayload  # type: ignore

    @computed_field  # type: ignore
    @property
    def event_type(self) -> str:
        return "custom"

    @computed_field  # type: ignore
    @property
    def event_subtype(self) -> str:
        return "create_film_review"


class UpdateFilmReviewEvent(BaseEvent):
    payload: UpdateFilmReviewPayload  # type: ignore

    @computed_field  # type: ignore
    @property
    def event_type(self) -> str:
        return "custom"

    @computed_field  # type: ignore
    @property
    def event_subtype(self) -> str:
        return "update_film_review"


class DeleteFilmReviewEvent(BaseEvent):
    payload: ReviewIdPayload  # type: ignore

    @computed_field  # type: ignore
    @property
    def event_type(self) -> str:
        return "custom"

    @computed_field  # type: ignore
    @property
    def event_subtype(self) -> str:
        return "delete_film_review"


class CreateFilmReviewRatingEvent(BaseEvent):
    payload: CreateFilmReviewRatingPayload  # type: ignore

    @computed_field  # type: ignore
    @property
    def event_type(self) -> str:
        return "custom"

    @computed_field  # type: ignore
    @property
    def event_subtype(self) -> str:
        return "create_film_review_rating"


class UpdateFilmReviewRatingEvent(BaseEvent):
    payload: CreateFilmReviewRatingPayload  # type: ignore

    @computed_field  # type: ignore
    @property
    def event_type(self) -> str:
        return "custom"

    @computed_field  # type: ignore
    @property
    def event_subtype(self) -> str:
        return "update_film_review_rating"


class DeleteFilmReviewRatingEvent(BaseEvent):
    payload: ReviewIdPayload  # type: ignore

    @computed_field  # type: ignore
    @property
    def event_type(self) -> str:
        return "custom"

    @computed_field  # type: ignore
    @property
    def event_subtype(self) -> str:
        return "delete_film_review_rating"


class CreateUserBookmarkEvent(BaseEvent):
    payload: FilmIdPayload  # type: ignore

    @computed_field  # type: ignore
    @property
    def event_type(self) -> str:
        return "custom"

    @computed_field  # type: ignore
    @property
    def event_subtype(self) -> str:
        return "create_user_bookmark"


class DeleteUserBookmarkEvent(BaseEvent):
    payload: FilmIdPayload  # type: ignore

    @computed_field  # type: ignore
    @property
    def event_type(self) -> str:
        return "custom"

    @computed_field  # type: ignore
    @property
    def event_subtype(self) -> str:
        return "delete_user_bookmark"


# === Responses ===


class FilmRatingResponse(CustomBaseModel):
    film_id: Union[str, UUID]
    like_count: int = 0
    dislike_count: int = 0
    avg_rating: float = 0


class FilmReviewRatingResponse(CustomBaseModel):
    like_count: int = 0
    dislike_count: int = 0
    avg_rating: float = 0


class FilmReviewResponse(CustomBaseModel):
    review_id: Union[str, UUID]
    value: str
    rating: FilmReviewRatingResponse


class FilmReviewListResponse(CustomBaseModel):
    film_id: Union[str, UUID]
    reviews: List[FilmReviewResponse]


class UserBookmarkResponse(CustomBaseModel):
    film_id: Union[str, UUID]
    created_at: int
