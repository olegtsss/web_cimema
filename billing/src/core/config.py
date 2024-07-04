import os
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).parent.parent

PUBLIC_KEY_PATH = BASE_DIR.joinpath("creds", "public_key.pem")
if os.access(PUBLIC_KEY_PATH, os.R_OK):
    with open(PUBLIC_KEY_PATH) as f:
        PUBLIC_KEY = f.read()
else:
    raise FileExistsError(f"Public key not found on path '{PUBLIC_KEY_PATH}'")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = Field("BILLING", alias="APP_NAME")
    api_v1_prefix: str = Field("/api/v1", alias="API_V1_PREFIX")
    sentry_dsn: Optional[str] = Field(None, alias="SENTRY_DSN")
    auth_api_url: str = Field("http://127.0.0.1:5020/api/v1", alias="AUTH_API_URL")

    limiter_times: int = Field(5, alias="LIMITER_TIMES")
    limiter_seconds: int = Field(1, alias="LIMITER_SECONDS")

    backoff_tries: int = Field(3, alias="BACKOFF_TRIES")
    backoff_time: int = Field(1, alias="BACKOFF_TIME")

    pg_db: str = Field("postgres", alias="POSTGRES_DB")
    pg_user: str = Field("postgres", alias="POSTGRES_USER")
    pg_password: str = Field("postgres", alias="POSTGRES_PASSWORD")
    pg_host: str = Field("localhost", alias="POSTGRES_HOST")
    pg_port: int = Field(5432, alias="POSTGRES_PORT")

    @property
    def pg_dsn(self) -> str:
        return (
            f"postgresql+asyncpg://{self.pg_user}:{self.pg_password}"
            f"@{self.pg_host}:{self.pg_port}/{self.pg_db}"
        )

    redis_db: int = Field(0, alias="REDIS_DB")
    redis_host: str = Field("localhost", alias="REDIS_HOST")
    redis_port: int = Field(6379, alias="REDIS_PORT")

    @property
    def redis_dsn(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    yandex_merchant_id: str = Field("test_id", alias="YANDEX_PAY_MERCHANT_ID")
    yandex_merchant_key: str = Field("test_key", alias="YANDEX_PAY_MERCHANT_API")
    jwk_cache_lifetime: int = 60 * 60 * 24
    redirect_url_on_abort: str = "https://abort.ru"
    redirec_url_on_error: str = "https://error.ru"
    redirect_url_on_success: str = "https://success.ru"
    yookassa_merchant_id: str = Field("test_id", alias="YOOKASSA_PAY_MERCHANT_ID")
    yookassa_merchant_key: str = Field("test_key", alias="YOOKASSA_PAY_MERCHANT_API")
    yookassa_merchant_ip_addresses: list = [
        "185.71.76.0/27",
        "185.71.77.0/27",
        "77.75.153.0/25",
        "77.75.156.11",
        "77.75.156.35",
        "77.75.154.128/25",
    ]


settings = Settings()
