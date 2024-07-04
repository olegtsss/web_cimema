import abc
from functools import lru_cache

from confluent_kafka import Consumer
from loguru import logger

from core.config import settings
from models.eventbus import Event


class BaseEventExtractor(abc.ABC):
    @abc.abstractmethod
    def consume_batch(self): ...

    @abc.abstractmethod
    def topics_subscribe(self): ...

    @abc.abstractmethod
    def stop(self): ...


class KafkaEventExtractor(BaseEventExtractor):

    def __init__(self) -> None:
        conf = {
            "bootstrap.servers": settings.kafka_cluster,
            "enable.auto.commit": False,
            "group.id": "etl_process",
            "auto.offset.reset": "earliest",
        }
        self.consumer = Consumer(conf)

    def topics_subscribe(self, topics: str = settings.kafka_topics) -> None:
        self.consumer.subscribe(settings.kafka_topics)

    def consume_batch(
        self, batch_size: int = settings.batch_size
    ) -> list[Event | None]:
        batch = []
        logger.info("Try to get event batch from Kafka")

        events = self.consumer.consume(num_messages=batch_size, timeout=5)

        for event in events:
            if event.error():
                logger.error(f"Error consuming message: {event.error()}")
            else:
                logger.debug(f"Received message: {event.value()}")
            try:
                batch.append(Event.model_validate_json(event.value().decode()))
            except ValueError:
                logger.exception("Event validation data error")
                pass

        self.consumer.commit()
        return batch

    def stop(self):
        self.consumer.close()


@lru_cache
def get_extractor() -> BaseEventExtractor:
    return KafkaEventExtractor()
