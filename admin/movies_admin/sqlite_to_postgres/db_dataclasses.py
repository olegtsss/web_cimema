import uuid
from dataclasses import dataclass, field, fields
from datetime import datetime


@dataclass
class CreatedMixin:
    created: datetime


@dataclass
class UpdatedMixin:
    modified: datetime


@dataclass
class DescriptionMixin:
    description: str


@dataclass
class FilmWorkIdMixin:
    film_work_id: uuid.UUID


@dataclass
class Genre(CreatedMixin, UpdatedMixin, DescriptionMixin):
    name: str
    id: uuid.UUID = field(default_factory=uuid.uuid4)


@dataclass
class GenreFilmwork(CreatedMixin, FilmWorkIdMixin):
    genre_id: uuid.UUID
    id: uuid.UUID = field(default_factory=uuid.uuid4)


@dataclass
class PersonFilmwork(CreatedMixin, FilmWorkIdMixin):
    person_id: uuid.UUID
    role: str
    id: uuid.UUID = field(default_factory=uuid.uuid4)


@dataclass
class Person(CreatedMixin, UpdatedMixin):
    full_name: str
    id: uuid.UUID = field(default_factory=uuid.uuid4)


@dataclass
class Filmwork(CreatedMixin, UpdatedMixin, DescriptionMixin):
    title: str
    creation_date: datetime
    file_path: str
    type: str
    rating: float = field(default=0.0)
    id: uuid.UUID = field(default_factory=uuid.uuid4)
