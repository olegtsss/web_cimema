import abc
from enum import Enum
from functools import lru_cache
from typing import Optional, Union

import backoff
from loguru import logger
from motor.motor_asyncio import AsyncIOMotorClient

from core.config import settings
from models.nosql import (
    FilmRating,
    FilmReview,
    FilmReviewRating,
    FilmReviewUserRating,
    FilmUserRating,
    UserBookmark,
)
from services.mongo import MongoStorage
from services.utils import JsonFileStorage


class ActionRatingGenetor(Enum):
    CREATE: str = "create"
    UPDATE: str = "update"
    DELETE: str = "delete"


class BaseLoader(abc.ABC):

    @abc.abstractmethod
    def load_batch(self, batch: list): ...

    @abc.abstractmethod
    def load_film_user_rating(self, element: FilmUserRating): ...

    @abc.abstractmethod
    def load_film_review(self, element: FilmReview): ...

    @abc.abstractmethod
    def load_film_review_user_rating(self, element: FilmReviewUserRating): ...

    @abc.abstractmethod
    def load_user_bookmark(self, element: UserBookmark): ...


class MongoLoader(BaseLoader):

    def __init__(self) -> None:
        self.client = AsyncIOMotorClient(settings.mongo_url)
        self.collection = self.client[settings.mongo_collection]
        self.storage = MongoStorage

    @backoff.on_exception(backoff.expo, Exception, logger=logger)
    async def ping_server(self):
        try:
            await self.client.admin.command("ping")
            logger.info("Successfully connected to MongoDB!")
        except Exception as error:
            logger.error(error)

    async def load_batch(
        self,
        batch: list[
            [Union[FilmUserRating, FilmReview, FilmReviewUserRating, UserBookmark]]
        ],
    ) -> None:
        await self.ping_server()
        for element in batch:
            if isinstance(element, FilmUserRating):
                await self.load_film_user_rating(element)
                logger.info("Download FilmUserRating object")
                continue
            if isinstance(element, FilmReview):
                await self.load_film_review(element)
                logger.info("Download FilmReview object")
                continue
            if isinstance(element, FilmReviewUserRating):
                await self.load_film_review_user_rating(element)
                logger.info("Download FilmReviewUserRating object")
                continue
            if isinstance(element, UserBookmark):
                await self.load_user_bookmark(element)
                logger.info("Download UserBookmark object")
                continue
            logger.warning("Cannot download unknown object %s", str(element))

    async def load_film_user_rating(self, element: FilmUserRating) -> None:
        # delete
        if element.value is None:
            element_in_collection = await self.storage.find(
                self,
                "FilmUserRating",
                {"film_id": element.film_id, "user_id": element.user_id},
            )
            if not element_in_collection:
                logger.warning("FilmUserRating not found")
                return
            await self.storage.delete(
                self,
                "FilmUserRating",
                {"film_id": element.film_id, "user_id": element.user_id},
            )
            await self.generate_new_rating(
                item=element,
                item_id=element.film_id,
                new_item_rating=None,
                old_item_rating=element_in_collection.get("value"),
                action=ActionRatingGenetor.DELETE.value,
            )
            return
        # create
        if element.created_at:
            if await self.storage.find(
                self,
                "FilmUserRating",
                {"film_id": element.film_id, "user_id": element.user_id},
            ):
                logger.warning("FilmUserRating already exist")
                return
            await self.storage.insert(self, "FilmUserRating", element.dict())
            await self.generate_new_rating(
                item=element,
                item_id=element.film_id,
                new_item_rating=element.value,
                old_item_rating=None,
                action=ActionRatingGenetor.CREATE.value,
            )
            return
        # update
        if element.updated_at:
            element_in_collection = await self.storage.find(
                self,
                "FilmUserRating",
                {"film_id": element.film_id, "user_id": element.user_id},
            )
            if not element_in_collection:
                logger.warning("FilmUserRating not found")
                return
            await self.storage.update(
                self,
                "FilmUserRating",
                {"_id": element_in_collection.get("_id")},
                {"value": element.value, "updated_at": element.updated_at},
            )
            await self.generate_new_rating(
                item=element,
                item_id=element.film_id,
                new_item_rating=element.value,
                old_item_rating=element_in_collection.get("value"),
                action=ActionRatingGenetor.UPDATE.value,
            )

    async def load_film_review(self, element: FilmReview) -> None:
        # delete
        if element.value is None:
            element_in_collection = await self.storage.find(
                self,
                "FilmReview",
                {"film_id": element.film_id, "user_id": element.user_id},
            )
            if not element_in_collection:
                logger.warning("FilmReview not found")
                return
            await self.storage.delete(
                self,
                "FilmReview",
                {"film_id": element.film_id, "user_id": element.user_id},
            )
            # Каскадное удаление всех связанных рейтингов
            await self.storage.delete(
                self,
                "FilmReviewRating",
                {"review_id": str(element_in_collection.get("_id"))},
                True,
            )
            return
        # create
        if element.created_at:
            if await self.storage.find(
                self,
                "FilmReview",
                {"film_id": element.film_id, "user_id": element.user_id},
            ):
                logger.warning("FilmReview already exist")
                return
            await self.storage.insert(self, "FilmReview", element.dict())
            return
        # update
        if element.updated_at:
            element_in_collection = await self.storage.find(
                self,
                "FilmReview",
                {"film_id": element.film_id, "user_id": element.user_id},
            )
            if not element_in_collection:
                logger.warning("FilmReview not found")
                return
            await self.storage.update(
                self,
                "FilmReview",
                {"_id": element_in_collection.get("_id")},
                {"value": element.value, "updated_at": element.updated_at},
            )

    async def load_film_review_user_rating(self, element: FilmReviewUserRating) -> None:
        # delete
        if element.value is None:
            element_in_collection = await self.storage.find(
                self,
                "FilmReviewUserRating",
                {"review_id": element.review_id, "user_id": element.user_id},
            )
            if not element_in_collection:
                logger.warning("FilmReviewUserRating not found")
                return
            await self.storage.delete(
                self,
                "FilmReviewUserRating",
                {"review_id": element.review_id, "user_id": element.user_id},
            )
            await self.generate_new_rating(
                item=element,
                item_id=element.review_id,
                new_item_rating=None,
                old_item_rating=element_in_collection.get("value"),
                action=ActionRatingGenetor.DELETE.value,
            )
            return
        # create
        if element.created_at:
            if await self.storage.find(
                self,
                "FilmReviewUserRating",
                {"review_id": element.review_id, "user_id": element.user_id},
            ):
                logger.warning("FilmReviewUserRating already exist")
                return
            element_in_collection = await self.storage.insert(
                self, "FilmReviewUserRating", element.dict()
            )
            await self.generate_new_rating(
                item=element,
                item_id=element.review_id,
                new_item_rating=element.value,
                old_item_rating=None,
                action=ActionRatingGenetor.CREATE.value,
            )
            return
        # update
        if element.updated_at:
            element_in_collection = await self.storage.find(
                self,
                "FilmReviewUserRating",
                {
                    "review_id": element.review_id,
                    "user_id": element.user_id,
                },
            )
            if not element_in_collection:
                logger.warning("FilmReviewUserRating not found")
                return
            await self.storage.update(
                self,
                "FilmReviewUserRating",
                {"_id": element_in_collection.get("_id")},
                {"value": element.value, "updated_at": element.updated_at},
            )
            await self.generate_new_rating(
                item=element,
                item_id=element.review_id,
                old_item_rating=element_in_collection.get("value"),
                new_item_rating=element.value,
                action=ActionRatingGenetor.UPDATE.value,
            )

    async def load_user_bookmark(self, element: UserBookmark) -> None:
        # create
        if element.created_at:
            if await self.storage.find(
                self,
                "UserBookmark",
                {"film_id": element.film_id, "user_id": element.user_id},
            ):
                logger.warning("UserBookmark already exist")
                return
            await self.storage.insert(self, "UserBookmark", element.dict())
            return
        # delete
        if not await self.storage.find(
            self,
            "UserBookmark",
            {"film_id": element.film_id, "user_id": element.user_id},
        ):
            logger.warning("UserBookmark not found")
            return
        await self.storage.delete(
            self,
            "UserBookmark",
            {"film_id": element.film_id, "user_id": element.user_id},
        )

    async def generate_new_rating(
        self,
        item: Union[FilmUserRating, FilmReviewUserRating],
        item_id: str,
        action: str,
        old_item_rating: Optional[int],
        new_item_rating: Optional[int],
    ) -> None:
        if isinstance(item, FilmUserRating):
            item_rating = await self.storage.find(
                self, "FilmRating", {"film_id": item_id}
            )
            if not item_rating:
                item_rating = FilmRating(
                    film_id=item_id,
                    like_count=0,
                    dislike_count=0,
                    avg_rating=0,
                    value_count=0,
                )
                result = await self.storage.insert(
                    self, "FilmRating", item_rating.dict()
                )
                item_rating_id = result.inserted_id
            else:
                item_rating_id = item_rating.pop("_id")
                item_rating = FilmRating(**item_rating)
        elif isinstance(item, FilmReviewUserRating):
            item_rating = await self.storage.find(
                self, "FilmReviewRating", {"review_id": item_id}
            )
            if not item_rating:
                item_rating = FilmReviewRating(
                    review_id=item_id,
                    like_count=0,
                    dislike_count=0,
                    avg_rating=0,
                    value_count=0,
                )
                result = await self.storage.insert(
                    self, "FilmReviewRating", item_rating.dict()
                )
                item_rating_id = result.inserted_id
            else:
                item_rating_id = item_rating.pop("_id")
                item_rating = FilmReviewRating(**item_rating)
        else:
            logger.warning(
                "Cannot generate new rating for unknown object: %s", str(item)
            )
            return

        try:
            # delete
            if action == ActionRatingGenetor.DELETE.value:
                if old_item_rating == 0:
                    item_rating.dislike_count -= 1
                if old_item_rating == 10:
                    item_rating.like_count -= 1
                item_rating.value_count -= 1
                if item_rating.value_count == 0:
                    item_rating.avg_rating = 0
                else:
                    item_rating.avg_rating = (
                        item_rating.avg_rating * item_rating.value_count
                        - old_item_rating
                    ) / item_rating.value_count
            # update
            elif action == ActionRatingGenetor.UPDATE.value:
                if new_item_rating == 0:
                    item_rating.dislike_count += 1
                    if old_item_rating == 10:
                        item_rating.like_count -= 1
                if new_item_rating == 10:
                    item_rating.like_count += 1
                    if old_item_rating == 0:
                        item_rating.dislike_count -= 1
                item_rating.avg_rating = (
                    item_rating.avg_rating * item_rating.value_count
                    - old_item_rating
                    + new_item_rating
                ) / item_rating.value_count
            # create
            elif action == ActionRatingGenetor.CREATE.value:
                if new_item_rating == 0:
                    item_rating.dislike_count += 1
                if new_item_rating == 10:
                    item_rating.like_count += 1
                item_rating.avg_rating = (
                    item_rating.avg_rating * item_rating.value_count + new_item_rating
                ) / (item_rating.value_count + 1)
                item_rating.value_count += 1

            # generate_new_rating
            if isinstance(item, FilmUserRating):
                await self.storage.replace(
                    self, "FilmRating", {"_id": item_rating_id}, item_rating.dict()
                )
            else:
                await self.storage.replace(
                    self,
                    "FilmReviewRating",
                    {"_id": item_rating_id},
                    item_rating.dict(),
                )
        except Exception as err:
            logger.exception(err)


@lru_cache
def get_loader() -> BaseLoader:
    return MongoLoader()
