from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class UpdatedGeneric(BaseModel):
    updated_at: Optional[datetime]


class CreatedGeneric(BaseModel):
    created_at: Optional[datetime]


class FilmUserRating(UpdatedGeneric, CreatedGeneric):
    film_id: str
    user_id: str
    value: Optional[int]


class FilmReview(UpdatedGeneric, CreatedGeneric):
    film_id: str
    user_id: str
    value: Optional[str]


class FilmReviewUserRating(UpdatedGeneric, CreatedGeneric):
    review_id: str
    user_id: str
    value: Optional[int]


class UserBookmark(CreatedGeneric):
    film_id: str
    user_id: str


class BaseRating(BaseModel):
    like_count: int
    dislike_count: int
    avg_rating: float
    value_count: int


class FilmRating(BaseRating):
    film_id: str


class FilmReviewRating(BaseRating):
    review_id: str
