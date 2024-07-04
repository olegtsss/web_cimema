from functools import lru_cache
import json
from typing import Optional
from uuid import UUID

from fastapi import Depends
from opentelemetry import trace

from core.config import settings
from schemas.schemas import FilmGenre
from storages.elastic import GenreStorage, get_genre_storge
from storages.redis_storage import RedisCache, get_cache

tracer = trace.get_tracer(__name__)


class GenreService:
    def __init__(self, cache: RedisCache, storage: GenreStorage):
        self.cache = cache
        self.storage = storage

    async def get_genre_by_uuid(self, uuid: UUID) -> Optional[FilmGenre]:
        with tracer.start_as_current_span("service"):
            if genre := await self.cache.get(str(uuid)):
                genre = FilmGenre.model_validate_json(genre)
            else:
                genre = await self.storage.get_by_id(uuid)
                if not genre:
                    return None

                await self.cache.put(
                    str(uuid),
                    genre.model_dump_json(),
                    settings.genres_cache_lifetime,
                )
            return genre

    async def get_all_genres(self) -> list[Optional[FilmGenre]]:
        with tracer.start_as_current_span("service"):
            genres_cache_key = "es_all_genres"
            if genres := await self.cache.get(genres_cache_key):
                genres = json.loads(genres)
                genres = [
                    FilmGenre.model_validate_json(genre) for genre in genres
                ]
            else:
                genres = await self.storage.get_all_genres()

                await self.cache.put(
                    genres_cache_key,
                    json.dumps([genre.model_dump_json() for genre in genres]),
                    settings.genres_cache_lifetime,
                )
            return genres


@lru_cache()
def get_genre_service(
    cache: RedisCache = Depends(get_cache),
    genre_storage: GenreStorage = Depends(get_genre_storge),
) -> GenreService:
    return GenreService(cache, genre_storage)
