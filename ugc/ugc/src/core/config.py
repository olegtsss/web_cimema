import os
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).parent.parent
STATIC_DIR = BASE_DIR.joinpath("static")
PUBLIC_KEY_DIR = BASE_DIR.joinpath("creds", "public_key.pem")

if os.access(PUBLIC_KEY_DIR, os.R_OK):
    with open(PUBLIC_KEY_DIR) as f:
        PUBLIC_KEY = f.read()
else:
    raise FileExistsError(f"Public key not found on path '{PUBLIC_KEY_DIR}'")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../.env")

    app_name: str = Field("UGC", alias="APP_NAME")
    api_v1_prefix: str = Field("/api/v1", alias="API_V1_PREFIX")

    kafka_dsn: str = Field("localhost:9092", alias="KAFKA_CLUSTER")
    rabbit_dsn: str = Field("localhost:5672", alias="RABBIT_CLUSTER")
    mongo_dsn: str = Field("localhost:27017", alias="MONGO_CLUSTER")

    sentry_dsn: Optional[str] = Field(None, alias="SENTRY_DSN")

    logstash_host: str = Field("localhost", alias="LOGSTASH_HOST")
    logstash_port: int = Field(5044, alias="LOGSTASH_PORT")

    @property
    def base_dir(self) -> Path:
        return BASE_DIR

    @property
    def static_dir(self) -> Path:
        return STATIC_DIR

    @property
    def public_key(self) -> Optional[str]:
        return PUBLIC_KEY


settings = Settings()
