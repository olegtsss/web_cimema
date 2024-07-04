from functools import lru_cache
from typing import Optional
from uuid import UUID

from fastapi import Depends
from opentelemetry import trace

from core.config import settings
from schemas.schemas import Film, Sort
from storages.elastic import FilmStorage, get_film_storge
from storages.redis_storage import RedisCache, get_cache

tracer = trace.get_tracer(__name__)


class FilmService:
    def __init__(self, cache: RedisCache, storage: FilmStorage):
        self.cache = cache
        self.storage = storage

    async def get_film_by_uuid(self, uuid: UUID) -> Optional[Film]:
        with tracer.start_as_current_span("service"):
            if film := await self.cache.get(str(uuid)):
                film = Film.model_validate_json(film)
            else:
                film = await self.storage.get_by_id(uuid)
                if not film:
                    return None

                await self.cache.put(
                    str(uuid),
                    film.model_dump_json(),
                    ex=settings.movies_cache_lifetime,
                )
            return film

    async def get_films(
        self,
        page_number: int,
        page_size: int,
        sort: Sort,
        genre_uuid: UUID | None = None,
    ) -> tuple[int, list[Optional[Film]]]:
        with tracer.start_as_current_span("service"):
            total_pages, films = await self.storage.get_films(
                page_number, page_size, sort, genre_uuid
            )
            return total_pages, films

    async def search_films(
        self,
        page_number: int,
        page_size: int,
        query: str,
        sort: Sort,
    ) -> tuple[int, list[Optional[Film]]]:
        with tracer.start_as_current_span("service"):
            total_pages, films = await self.storage.search_films(
                page_number, page_size, query, sort
            )
            return total_pages, films


@lru_cache()
def get_film_service(
    cache: RedisCache = Depends(get_cache),
    film_storage: FilmStorage = Depends(get_film_storge),
) -> FilmService:
    return FilmService(cache, film_storage)
