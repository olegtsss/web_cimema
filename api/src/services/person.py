from functools import lru_cache
from typing import Optional
from uuid import UUID

from fastapi import Depends
from opentelemetry import trace

from core.config import settings
from schemas.schemas import FilmPerson, Person
from storages.elastic import PersonStorage, get_person_storge
from storages.redis_storage import RedisCache, get_cache

tracer = trace.get_tracer(__name__)


class PersonService:
    def __init__(self, cache: RedisCache, storage: PersonStorage):
        self.cache = cache
        self.storage = storage

    async def get_person_by_uuid(self, uuid: UUID) -> Optional[Person]:
        with tracer.start_as_current_span("service"):
            if person := await self.cache.get(str(uuid)):
                person = Person.model_validate_json(person)
            else:
                person = await self.storage.get_by_id(uuid)
                if not person:
                    return None

                await self.cache.put(
                    str(uuid),
                    person.model_dump_json(),
                    settings.persons_cache_lifetime,
                )
            return person

    async def search_by_full_name(
        self, page_number: int, page_size: int, query: str
    ) -> tuple[int, list[Optional[FilmPerson]]]:
        with tracer.start_as_current_span("service"):
            total_pages, persons = await self.storage.search_by_full_name(
                page_number, page_size, query
            )
            return total_pages, persons


@lru_cache()
def get_person_service(
    cache: RedisCache = Depends(get_cache),
    person_storge: PersonStorage = Depends(get_person_storge),
) -> PersonService:
    return PersonService(cache, person_storge)
