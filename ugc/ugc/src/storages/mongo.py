from functools import lru_cache
from typing import Any, List, Optional, Union

from pymongo import MongoClient  # type: ignore
from pymongo.collection import Collection  # type: ignore

from core.config import settings


@lru_cache
def get_mongo() -> "MongoStorage":
    return MongoStorage()


class MongoStorage():
    def __init__(self) -> None:
        self.client: MongoClient = self.get_client()
        self.db = self.client["practixDb"]

    @staticmethod
    def get_client() -> MongoClient:
        """Метод получения клиента."""
        return MongoClient(settings.mongo_dsn)

    @staticmethod
    def find(
        *,
        collection: Collection,
        condition: dict,
        multiple: bool = False,
        skip: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> Union[Optional[dict], List[dict], Any]:
        """Метод поиска документа(-ов).

        Обязательные параметры:
        - `collection`: коллекция
        - `condition`: словарь условий поиска значений

        Опциональные параметры:
        - `multiple`: флаг поиска набора значений
        - `skip`: смещение
        - `limit`: лимит
        """
        if multiple:
            query = collection.find(condition)
            query = query.skip(skip) if skip is not None else query
            query = query.limit(limit) if limit is not None else query
            return [item for item in query]
        return collection.find_one(condition)

    @staticmethod
    def aggregate(*, collection: Collection, pipeline: List[dict]) -> List[dict]:
        """Метод агрегации документа(-ов).
        
        Обязательные параметры:
        - `collection`: коллекция
        - `pipeline`: шаги агрегации
        """
        query = collection.aggregate(pipeline)
        return [item for item in query]
