from functools import lru_cache

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from pymongo.collection import Collection

from core.config import settings


class MongoStorage:
    def __init__(self) -> None:
        self.client: AsyncIOMotorClient = self.get_client()
        self.collection = self.client[settings.mongo_collection]

    @staticmethod
    def get_client() -> AsyncIOMotorClient:
        """Метод получения клиента."""
        return AsyncIOMotorClient(settings.mongo_url)

    async def insert(
        self,
        table: str,
        data: dict | list[dict],
        multiple: bool = False,
    ):
        """Метод вставки документа(-ов).

        Обязательные параметры:
        - `table`: документ
        - `data`: словарь или список словарей с новыми данными

        Опциональные параметры:
        - `multiple`: bulk-вставка, `data` должна быть списком словарей
        """
        if multiple:
            return await self.collection[table].insert_many(data)
        return await self.collection[table].insert_one(data)

    async def find(
        self,
        table: str,
        condition: dict,
        multiple: bool = False,
        skip: int | None = None,
        limit: int | None = None,
    ):
        """Метод поиска документа(-ов).

        Обязательные параметры:
        - `table`: документ
        - `condition`: словарь условий поиска значений

        Опциональные параметры:
        - `multiple`: bulk-поиск
        - `skip`: смещение
        - `limit`: лимит
        """
        if multiple:
            cursor = self.collection[table].find(condition)
            cursor = cursor.skip(skip) if skip is not None else cursor
            cursor = cursor.limit(limit) if limit is not None else cursor
            return [result for result in await cursor]
        return await self.collection[table].find_one(condition)

    async def update(
        self, table: str, condition: dict, new_data: dict, multiple: bool = False
    ):
        """Метод обновления документа(-ов).

        Обязательные параметры:
        - `table`: таблица
        - `condition`: словарь условий поиска значений
        - `new_data`: словарь новых значений

        Опциональные параметры:
        - `multiple`: bulk-обновление
        """
        if multiple:
            return await self.collection.update_many(condition, {"$set": new_data})
        return await self.collection[table].update_one(condition, {"$set": new_data})

    async def replace(
        self,
        table: str,
        condition: dict,
        new_data: dict,
    ):
        """Метод замены документа.

        Обязательные параметры:
        - `table`: таблица
        - `condition`: словарь условий поиска значений
        - `new_data`: словарь новых значений
        """
        return await self.collection[table].replace_one(condition, new_data)

    async def delete(self, table: str, condition: dict, multiple: bool = False):
        """Метод обновления документа(-ов).

        Обязательные параметры:
        - `table`: коллекция
        - `condition`: словарь условий поиска значений

        Опциональные параметры:
        - `multiple`: bulk-удаление
        """
        if multiple:
            return await self.collection[table].delete_many(condition)
        return await self.collection[table].delete_one(condition)


@lru_cache
def get_mongo() -> "MongoStorage":
    return MongoStorage()
