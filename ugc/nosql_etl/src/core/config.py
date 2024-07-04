from pathlib import Path

from pydantic import computed_field, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore", env_file="../.env")

    kafka_cluster: str = Field(
        "localhost:9094,localhost:9095,localhost:9096", alias="KAFKA_CLUSTER"
    )
    kafka_topics_str: str = Field("custom,click,visit", alias="KAFKA_TOPICS")
    mongo_klaster: str = Field("127.0.0.1:27017", alias="MONGO_CLUSTER")
    mongo_user: str = Field("mongo", alias="MONGO_INITDB_ROOT_USERNAME")
    mongo_password: str = Field("mongo", alias="MONGO_INITDB_ROOT_PASSWORD")
    mongo_collection: str = "ugc_2_collection"

    batch_size: int = 1000
    batch_size_for_olap_loaded: int = 10

    extract_storage: str = str(BASE_DIR.joinpath("temp.json"))

    @computed_field
    @property
    def kafka_topics(self) -> list[str]:
        return str(self.kafka_topics_str).split(",")

    @computed_field
    @property
    def mongo_url(self) -> str:
        return f"mongodb://{self.mongo_user}:{self.mongo_password}@{self.mongo_klaster}"


settings = Settings()
