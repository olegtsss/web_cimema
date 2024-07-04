from functools import lru_cache
from uuid import UUID
from typing import List, Optional, Union

from storages.mongo import get_mongo, MongoStorage
from schemas.entity import (
    FilmRatingResponse, FilmReviewResponse, UserBookmarkResponse, FilmReviewListResponse
)


@lru_cache
def get_service() -> "Service":
    return Service()


class Service:
    def __init__(self) -> None:
        self.storage: MongoStorage = get_mongo()

    def get_film_rating(self, film_id: Union[str, UUID]) -> dict:
        """Метод получения рейтинга произведения.

        Обязательные параметры:
        - `film_id`: id произведения
        """
        film_rating = self.storage.find(
            collection=self.storage.db.filmRating,
            condition={"film_id": film_id},
        )
        if film_rating is not None:
            film_rating_model = FilmRatingResponse(**film_rating)  # type: ignore
        else:
            film_rating_model = FilmRatingResponse(film_id=film_id)
        return film_rating_model.model_dump()

    def get_film_reviews(
        self,
        film_id: Union[str, UUID],
        skip: Optional[int] = None,
        limit: Optional[int] = None,
    ):
        """Метод получения отзывов (рецензий) на произведение.

        Обязательные параметры:
        - `film_id`: id произведения

        Опциональные параметры:
        - `skip`: смещение
        - `limit`: лимит
        """
        pipeline: List[dict] = [
            {
                "$match": {"film_id": film_id}
            },
            {
                "$addFields": {
                    "review_id": {"$toString": "$_id"}
                }
            },
            {
                "$lookup": {
                    "from": "filmReviewRating",
                    "localField": "review_id",
                    "foreignField": "review_id",
                    "as": "rating"
                }
            },
            {
                "$unwind": "$rating"
            },
            {
                "$project": {
                    "review_id": 1,
                    "film_id": 1,
                    "user_id": 1,
                    "value": 1,
                    "rating": {
                        "_id": 1,
                        "like_count": 1,
                        "dislike_count": 1,
                        "avg_rating": 1,
                        "value_count": 1
                    },
                    "created_at": 1,
                    "updated_at": 1,
                }
            }
        ]
        if skip is not None:
            pipeline.append({"$skip": skip})
        if limit is not None:
            pipeline.append({"$limit": limit})
        film_reviews = self.storage.aggregate(  # type: ignore
            collection=self.storage.db.filmReview, pipeline=pipeline
        )
        return FilmReviewListResponse(
            film_id=film_id,
            reviews=[FilmReviewResponse(**r) for r in film_reviews],
        ).model_dump()

    def get_user_bookmarks(
        self,
        user_id: Union[str, UUID],
        skip: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[dict]:
        """Метод получения закладок пользователя.

        Обязательные параметры:
        - `user_id`: id произведения

        Опциональные параметры:
        - `skip`: смещение
        - `limit`: лимит
        """
        user_bookmarks = self.storage.find(
            collection=self.storage.db.userBookmark,
            condition={"user_id": user_id},
            multiple=True,
            skip=skip,
            limit=limit,
        )
        return [UserBookmarkResponse(**b).model_dump() for b in user_bookmarks]  # type: ignore
