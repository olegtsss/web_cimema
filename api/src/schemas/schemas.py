from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# === Enums ===


class Sort(str, Enum):
    imdb_asc: str = "asc"
    imdb_desc: str = "desc"


# === Models ===


class CustomBaseModel(BaseModel):
    model_config = ConfigDict(
        use_enum_values=True,
        from_attributes=True,
    )


class FilmGenre(CustomBaseModel):
    id: UUID
    name: str


class FilmPerson(CustomBaseModel):
    id: UUID
    full_name: str


class Film(CustomBaseModel):
    id: UUID
    title: str
    description: str | None = None
    imdb_rating: float | None = None
    genres: list[FilmGenre] = []
    actors: list[FilmPerson] = []
    directors: list[FilmPerson] = []
    writers: list[FilmPerson] = []


class Person(FilmPerson):
    films: list[Film] = []


# === Params ===


class PaginationParams(CustomBaseModel):
    page_number: int = Field(default=1, gt=0)
    page_size: int = Field(default=10, gt=0)


class SortParams(CustomBaseModel):
    sort: Sort = Sort.imdb_desc


class FilmParams(SortParams, PaginationParams):
    genre: UUID | None = None


class FilmSearchParams(SortParams, PaginationParams):
    query: str


class PersonSearchParams(PaginationParams):
    query: str


# === Responses ===


class PaginationResponse(PaginationParams):
    total_pages: int


class FilmResponse(SortParams, PaginationResponse):
    genre: UUID | None = None
    results: list[Film]


class FilmSearchResponse(FilmSearchParams, PaginationResponse):
    results: list[Film]


class PersonSearchResponse(PersonSearchParams, PaginationResponse):
    results: list[FilmPerson]
