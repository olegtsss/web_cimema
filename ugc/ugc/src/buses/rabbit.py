import functools
from typing import Optional

import pika
from pika.exceptions import StreamLostError

from buses.bus import EventBus
from core.config import settings
from schemas.entity import BaseEvent


@functools.lru_cache
def get_rabbit() -> "RabbitEventBus":
    return RabbitEventBus()


class RabbitEventBus(EventBus):
    def __init__(self, rabbit_dsn: Optional[str] = None) -> None:
        super().__init__()
        self.rabbit_dsn = rabbit_dsn or settings.rabbit_dsn
        self.exchange_name = "events"
        self.queues = ("click", "custom", "visit")

        self.connect()

    def connect(self):
        self.connection = pika.BlockingConnection(
            pika.URLParameters(self.rabbit_dsn),
        )
        self.channel = self.connection.channel()
        self.channel.exchange_declare(
            exchange=self.exchange_name,
            exchange_type="direct",
            durable=True,
        )
        for queue in self.queues:
            self.channel.queue_declare(queue, durable=True)
            self.channel.queue_bind(
                queue, self.exchange_name, routing_key=queue
            )

    def disconnect(self):
        if self.connection and self.connection.is_open:
            self.connection.close()

    def produce_event(self, event_model: BaseEvent) -> None:
        msg = {
            "exchange": self.exchange_name,
            "routing_key": event_model.event_type,
            "body": event_model.model_dump_json(),
            "properties": pika.BasicProperties(
                content_type="application/json",
                content_encoding="utf-8",
                delivery_mode=2,
            )
        }
        try:
            self.channel.basic_publish(**msg)
        except StreamLostError:
            self.connect()
            self.channel.basic_publish(**msg)
