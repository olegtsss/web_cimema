from functools import lru_cache
import socket
from typing import Optional

from confluent_kafka import Producer  # type: ignore

from buses.bus import EventBus
from core.config import settings
from core.loggers import logger
from schemas.entity import BaseEvent


@lru_cache
def get_kafka() -> "KafkaEventBus":
    return KafkaEventBus()


class KafkaEventBus(EventBus):
    def __init__(
            self,
            kafka_dsn: Optional[str] = None,
            producer: Optional[Producer] = None,
        ) -> None:
        super().__init__()
        self.kafka_dsn = kafka_dsn or settings.kafka_dsn
        self.producer = producer or self.get_producer()

    @lru_cache
    def get_producer(self) -> Producer:
        return Producer({
            "bootstrap.servers": settings.kafka_dsn,
            "client.id": socket.gethostname(),
        })

    @staticmethod
    def acked(err, msg) -> None:
        message = {
            "timestamp": msg.timestamp(),
            "latency": msg.latency(),
            "leader_epoch": msg.leader_epoch(),
            "offset": msg.offset(),
            "partition": msg.partition(),
            "topic": msg.topic(),
            "key": msg.key().decode("utf-8"),
            "value": msg.value().decode("utf-8"),
            "headers": msg.headers(),
        }

        if err is None:
            logger.info(f"Kafka: message produced | {message}")
        else:
            error = {
                "code": err.code(),
                "fatal": err.fatal(),
                "name": err.name(),
                "retriable": err.retriable(),
                "str": err.str(),
                "txn_requires_abort": err.txn_requires_abort(),
            }
            logger.error(
                f"Kafka: failed to deliver message | {message} | {error}"
            )

    def produce_event(self, event_model: BaseEvent) -> None:
        self.producer.produce(
            topic=event_model.event_type,
            key=str(event_model.event_id),
            value=event_model.model_dump_json(),
            callback=self.acked,
        )
        self.producer.poll(1)
