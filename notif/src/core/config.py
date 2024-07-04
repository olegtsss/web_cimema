import datetime

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    app_name: str = Field("Notif", alias="APP_NAME")
    api_v1_prefix: str = Field("/api/v1", alias="API_V1_PREFIX")

    limiter_times: int = Field(5, alias="LIMITER_TIMES")
    limiter_seconds: int = Field(1, alias="LIMITER_SECONDS")

    backoff_tries: int = Field(5, alias="BACKOFF_TRIES")
    backoff_time: int = Field(30, alias="BACKOFF_TIME")

    pg_db: str = Field("postgres", alias="POSTGRES_DB")
    pg_user: str = Field("postgres", alias="POSTGRES_USER")
    pg_password: str = Field("postgres", alias="POSTGRES_PASSWORD")
    pg_host: str = Field("127.0.0.1", alias="POSTGRES_HOST")
    pg_port: int = Field(5432, alias="POSTGRES_PORT")

    notification_life: datetime.timedelta = datetime.timedelta(hours=4)

    websocket_host: str = Field("127.0.0.1", alias="WEBSOCKET_SERVER")
    websocket_port: int = Field(8765, alias="WEBSOCKET_PORT")

    smtp_host: str = Field("127.0.0.1", alias="SMTP_SERVER")
    smtp_port: int = Field(465, alias="SMTP_PORT")
    smtp_tls: bool = Field(True, alias="SMTP_TLS")
    smtp_login: str = Field("test", alias="EMAIL_LOGIN")
    smtp_password: str = Field("password", alias="EMAIL_PASSWORD")
    smtp_sender: str = Field("test@test.ru", alias="EMAIL_SENDER")

    @property
    def pg_dsn(self) -> str:
        return (
            f"postgresql+asyncpg://{self.pg_user}:{self.pg_password}"
            f"@{self.pg_host}:{self.pg_port}/{self.pg_db}"
        )

    redis_db: int = Field(0, alias="REDIS_DB")
    redis_host: str = Field("127.0.0.1", alias="REDIS_HOST")
    redis_port: int = Field(6379, alias="REDIS_PORT")

    @property
    def redis_dsn(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    rabbit_user: str = Field("guest", alias="RABBITMQ_DEFAULT_USER")
    rabbit_password: str = Field("guest", alias="RABBITMQ_DEFAULT_PASS")
    rabbit_host: str = Field("127.0.0.1", alias="RABBITMQ_DEFAULT_HOST")
    rabbit_port: int = Field(5672, alias="RABBITMQ_DEFAULT_PORT")

    @property
    def rabbit_dsn(self) -> str:
        return (
            f"amqp://{self.rabbit_user}:{self.rabbit_password}"
            f"@{self.rabbit_host}:{self.rabbit_port}/"
        )


settings = Settings()
