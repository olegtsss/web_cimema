import os
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).parent.parent

PUBLIC_KEY: Optional[str] = None


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../.env")

    app_name: str = Field("PRACTIX", alias="APP_NAME")

    backoff_tries: int = Field(5, alias="BACKOFF_TRIES")
    backoff_time: int = Field(30, alias="BACKOFF_TIME")

    redis_host: str = Field("localhost", alias="REDIS_HOST")
    redis_port: int = Field(6379, alias="REDIS_PORT")
    redis_db: int = Field(0, alias="REDIS_DB")

    es_host: str = Field("localhost", alias="ES_HOST")
    es_port: int = Field(9200, alias="ES_PORT")

    jaeger_host: str = Field("localhost", alias="JAEGER_HOST")
    jaeger_port: int = Field(6831, alias="JAEGER_PORT")

    movies_es_index: str = Field("movies", alias="MOVIES_ES_INDEX")
    movies_cache_lifetime: int = Field(86400, alias="MOVIES_CACHE_LIFETIME")
    persons_es_index: str = Field("persons", alias="PERSONS_ES_INDEX")
    persons_cache_lifetime: int = Field(86400, alias="PERSONS_CACHE_LIFETIME")
    genres_es_index: str = Field("genres", alias="GENRES_ES_INDEX")
    genres_cache_lifetime: int = Field(86400, alias="GENRES_CACHE_LIFETIME")

    @property
    def redis_dsn(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @property
    def es_dsn(self) -> str:
        return f"http://{self.es_host}:{self.es_port}"


settings = Settings()


public_key_path = BASE_DIR.joinpath("creds", "public_key.pem")
if os.access(public_key_path, os.R_OK):
    with open(public_key_path) as f:
        PUBLIC_KEY = f.read()
else:
    raise FileExistsError(f"Public key not found on path '{public_key_path}'")
