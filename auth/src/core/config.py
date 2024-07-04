from datetime import timedelta
import os
from pathlib import Path
from typing import Optional

from pydantic import Field, HttpUrl, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).parent.parent

PUBLIC_KEY: Optional[str] = None
PRIVATE_KEY: Optional[str] = None

REDIS_REFRESH_TOKEN_PATTERN = "{prefix}_{user_uid}_{refresh_jti}"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../.env", extra="ignore")

    app_name: str = Field("AUTH", alias="APP_NAME")
    api_external_url: HttpUrl = Field(
        "http://localhost:8000/api/v1", alias="API_EXTERNAL_URL"
    )
    secret: str = Field(..., alias="SECRET")
    user_requires_verification: bool = Field(
        False, alias="USER_REQUIRES_VERIFICATION"
    )

    limiter_times: int = Field(2, alias="LIMITER_TIMES")
    limiter_seconds: int = Field(1, alias="LIMITER_SECONDS")

    backoff_tries: int = Field(5, alias="BACKOFF_TRIES")
    backoff_time: int = Field(30, alias="BACKOFF_TIME")

    access_lifetime: timedelta = Field(timedelta(hours=1))
    refresh_lifetime: timedelta = Field(timedelta(days=7))
    audience: list[str] = Field(["ADMIN", "PRACTIX"])

    oauth_vk_client_id: str = Field(..., alias="OAUTH_VK_CLIENT_ID")
    oauth_vk_client_secret: str = Field(..., alias="OAUTH_VK_CLIENT_SECRET")
    oauth_vk_service_token: str = Field(..., alias="OAUTH_VK_SERVICE_TOKEN")

    oauth_yandex_client_id: str = Field(..., alias="OAUTH_YANDEX_CLIENT_ID")
    oauth_yandex_client_secret: str = Field(
        ..., alias="OAUTH_YANDEX_CLIENT_SECRET"
    )

    pg_db: str = Field("postgres", alias="POSTGRES_DB")
    pg_user: str = Field("postgres", alias="POSTGRES_USER")
    pg_password: str = Field("postgres", alias="POSTGRES_PASSWORD")
    pg_host: str = Field("localhost", alias="POSTGRES_HOST")
    pg_port: int = Field(5432, alias="POSTGRES_PORT")

    redis_db: int = Field(0, alias="REDIS_DB")
    redis_host: str = Field("localhost", alias="REDIS_HOST")
    redis_port: int = Field(6379, alias="REDIS_PORT")

    @computed_field
    @property
    def token_audience(self) -> list[str]:
        return self.audience + [self.app_name]

    @computed_field
    @property
    def redis_dsn(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @computed_field
    @property
    def pg_dsn(self) -> str:
        return (
            f"postgresql+asyncpg://{self.pg_user}:{self.pg_password}"
            f"@{self.pg_host}:{self.pg_port}/{self.pg_db}"
        )


settings = Settings()


public_key_path = BASE_DIR.joinpath("creds", "public_key.pem")
if os.access(public_key_path, os.R_OK):
    with open(public_key_path) as f:
        PUBLIC_KEY = f.read()
else:
    raise FileExistsError(f"Public key not found on path '{public_key_path}'")


private_key_path = BASE_DIR.joinpath("creds", "private_key.pem")
if os.access(private_key_path, os.R_OK):
    with open(private_key_path) as f:
        PRIVATE_KEY = f.read()
else:
    raise FileExistsError(
        f"Private key not found on path '{private_key_path}'"
    )
