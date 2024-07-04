from abc import ABC, abstractmethod
from functools import lru_cache
from typing import Any, Optional
from uuid import UUID

import backoff
from elasticsearch import AsyncElasticsearch, ConnectionError, NotFoundError
from opentelemetry import trace

from core import config
from schemas.schemas import Film, FilmGenre, FilmPerson, Person, Sort

tracer = trace.get_tracer(__name__)

esm: Optional[AsyncElasticsearch] = None


class ABCStorage(ABC):
    """
    Абстрактный класс хранилища
    """

    @abstractmethod
    async def get_by_id(self, uuid: UUID) -> Any | None:
        raise NotImplemented


class FilmStorage(ABCStorage):
    """
    Хранилище фильмов
    """

    def __init__(self, es_client: AsyncElasticsearch):
        self.es_client = es_client
        self.index_name = config.settings.movies_es_index

    @backoff.on_exception(
        backoff.expo,
        ConnectionError,
        max_time=config.settings.backoff_time,
        max_tries=config.settings.backoff_tries,
    )
    async def get_by_id(self, uuid: UUID) -> Optional[Film]:
        with tracer.start_as_current_span("elasticsearch"):
            try:
                film = await self.es_client.get(
                    index=self.index_name, id=str(uuid)
                )
            except NotFoundError:
                return None
            return Film(**film["_source"])

    @backoff.on_exception(
        backoff.expo,
        ConnectionError,
        max_time=config.settings.backoff_time,
        max_tries=config.settings.backoff_tries,
    )
    async def get_films(
        self,
        page_number: int,
        page_size: int,
        sort: Sort,
        genre_uuid: UUID | None = None,
    ) -> tuple[int, list[Optional[Film]]]:
        with tracer.start_as_current_span("elasticsearch"):
            query = {"bool": {"must": [{"match_all": {}}]}}
            query_sort = [{"imdb_rating": {"order": sort}}]
            query_size = page_size
            query_scroll = "1m"
            if genre_uuid:
                query["bool"]["must"] += [
                    {
                        "nested": {
                            "path": config.settings.genres_es_index,
                            "query": {
                                "bool": {
                                    "must": [
                                        {
                                            "match": {
                                                f"{config.settings.genres_es_index}.id": genre_uuid
                                            },
                                        }
                                    ]
                                }
                            },
                        }
                    }
                ]
            films = await self.es_client.search(
                index=self.index_name,
                query=query,
                sort=query_sort,
                size=query_size,
                scroll=query_scroll,
            )

            total_values = films["hits"]["total"]["value"]
            total_pages = -(-total_values // page_size)

            for _ in range(page_number - 1):
                films = await self.es_client.scroll(
                    scroll_id=films["_scroll_id"], scroll=query_scroll
                )

            return (
                total_pages,
                [Film(**film["_source"]) for film in films["hits"]["hits"]],
            )

    @backoff.on_exception(
        backoff.expo,
        ConnectionError,
        max_time=config.settings.backoff_time,
        max_tries=config.settings.backoff_tries,
    )
    async def search_films(
        self,
        page_number: int,
        page_size: int,
        query: str,
        sort: Sort,
    ) -> tuple[int, list[Optional[Film]]]:
        with tracer.start_as_current_span("elasticsearch"):
            query_query = {
                "multi_match": {
                    "query": query,
                    "fields": ["title", "description"],
                }
            }
            query_sort = [{"imdb_rating": {"order": sort}}]
            query_size = page_size
            query_scroll = "1m"
            films = await self.es_client.search(
                index=self.index_name,
                query=query_query,
                sort=query_sort,
                size=query_size,
                scroll=query_scroll,
            )

            total_values = films["hits"]["total"]["value"]
            total_pages = -(-total_values // page_size)

            for _ in range(page_number - 1):
                films = await self.es_client.scroll(
                    scroll_id=films["_scroll_id"], scroll=query_scroll
                )

            return (
                total_pages,
                [Film(**film["_source"]) for film in films["hits"]["hits"]],
            )


class GenreStorage(ABCStorage):
    """
    Хранилище жанров
    """

    def __init__(self, es_client: AsyncElasticsearch):
        self.es_client = es_client
        self.index_name = config.settings.genres_es_index

    @backoff.on_exception(
        backoff.expo,
        ConnectionError,
        max_time=config.settings.backoff_time,
        max_tries=config.settings.backoff_tries,
    )
    async def get_by_id(self, uuid: UUID) -> Optional[FilmGenre]:
        with tracer.start_as_current_span("elasticsearch"):
            try:
                genre = await self.es_client.get(
                    index=self.index_name, id=uuid
                )
            except NotFoundError:
                return None
            return FilmGenre(**genre["_source"])

    @backoff.on_exception(
        backoff.expo,
        ConnectionError,
        max_time=config.settings.backoff_time,
        max_tries=config.settings.backoff_tries,
    )
    async def get_all_genres(self) -> list[Optional[FilmGenre]]:
        with tracer.start_as_current_span("elasticsearch"):
            query = {"match_all": {}}
            query_size = 1000
            genres = await self.es_client.search(
                index=self.index_name, query=query, size=query_size
            )
            return [
                FilmGenre(**genre["_source"])
                for genre in genres["hits"]["hits"]
            ]


class PersonStorage(ABCStorage):
    """
    Хранилище персоналий
    """

    def __init__(self, es_client: AsyncElasticsearch):
        self.es_client = es_client
        self.index_name = config.settings.persons_es_index

    @backoff.on_exception(
        backoff.expo,
        ConnectionError,
        max_time=config.settings.backoff_time,
        max_tries=config.settings.backoff_tries,
    )
    async def get_by_id(self, uuid: UUID) -> Optional[Person]:
        with tracer.start_as_current_span("elasticsearch"):
            try:
                person = await self.es_client.get(
                    index=self.index_name, id=uuid
                )
            except NotFoundError:
                return None

            query = {
                "bool": {
                    "should": [
                        {
                            "nested": {
                                "path": "actors",
                                "query": {
                                    "bool": {
                                        "must": [
                                            {"match": {"actors.id": uuid}}
                                        ]
                                    }
                                },
                            }
                        },
                        {
                            "nested": {
                                "path": "directors",
                                "query": {
                                    "bool": {
                                        "must": [
                                            {"match": {"directors.id": uuid}}
                                        ]
                                    }
                                },
                            }
                        },
                        {
                            "nested": {
                                "path": "writers",
                                "query": {
                                    "bool": {
                                        "must": [
                                            {"match": {"writers.id": uuid}}
                                        ]
                                    }
                                },
                            }
                        },
                    ]
                }
            }
            films = await self.es_client.search(
                index=config.settings.movies_es_index, query=query
            )
            return Person(
                **person["_source"],
                films=[
                    Film(**film["_source"]) for film in films["hits"]["hits"]
                ],
            )

    @backoff.on_exception(
        backoff.expo,
        ConnectionError,
        max_time=config.settings.backoff_time,
        max_tries=config.settings.backoff_tries,
    )
    async def search_by_full_name(
        self, page_number: int, page_size: int, query: str
    ) -> tuple[int, list[Optional[FilmPerson]]]:
        with tracer.start_as_current_span("elasticsearch"):
            query_query = {"match": {"full_name": query}}
            query_size = page_size
            query_scroll = "1m"
            persons = await self.es_client.search(
                index=self.index_name,
                query=query_query,
                size=query_size,
                scroll=query_scroll,
            )

            total_values = persons["hits"]["total"]["value"]
            total_pages = -(-total_values // page_size)

            for _ in range(page_number - 1):
                persons = await self.es_client.scroll(
                    scroll_id=persons["_scroll_id"], scroll=query_scroll
                )

            return (
                total_pages,
                [
                    FilmPerson(**person["_source"])
                    for person in persons["hits"]["hits"]
                ],
            )


@lru_cache()
def get_film_storge() -> FilmStorage:
    return FilmStorage(esm)


@lru_cache()
def get_genre_storge() -> GenreStorage:
    return GenreStorage(esm)


@lru_cache()
def get_person_storge() -> PersonStorage:
    return PersonStorage(esm)
