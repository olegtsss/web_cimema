from pydantic import computed_field, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore", env_file="../.env")

    kafka_cluster: str = Field(
        "kafka-0:9092,kafka-1:9092,kafka-2:9092", alias="KAFKA_CLUSTER"
    )
    kafka_topics_str: str = Field("custom,click,visit", alias="KAFKA_TOPICS")

    clickhouse_host: str = Field("localhost", alias="CLICKHOUSE_HOST")
    clickhouse_port: int = Field(8123, alias="CLICKHOUSE_PORT")
    batch_size: int = 1000
    batch_size_for_olap_loaded: int = 1000

    @computed_field
    @property
    def kafka_topics(self) -> list[str]:
        return self.kafka_topics_str.split(",")

    @computed_field
    @property
    def clickhouse_url(self) -> str:
        return f"http://{self.clickhouse_host}:{self.clickhouse_port}/"


settings = Settings()
