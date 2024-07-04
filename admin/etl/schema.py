from typing import Optional

from pydantic import BaseModel, Field


class Person(BaseModel):
    id: str = Field(alias='person_id')
    name: str = Field(alias='person_name')


class Genre(BaseModel):
    id: str = Field(alias='genre_id')
    name: str = Field(alias='genre_name')


class ElasticsearchData(BaseModel):
    id: str
    imdb_rating: Optional[float]
    genre: list[str]
    genres: list[Genre]
    title: str
    description: Optional[str]
    director: list[str]
    directors: list[Person]
    actors_names: list[str]
    writers_names: list[str]
    actors: list[Person]
    writers: list[Person]
