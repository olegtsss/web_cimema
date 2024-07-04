from functools import lru_cache

from flask import request
from schemas.entity import BaseEvent


@lru_cache
def get_eventbus() -> "EventBus":
    return EventBus()


class EventBus:
    def __init__(self) -> None:
        super().__init__()

    def produce_event(self, event_model: BaseEvent) -> None:
        from buses.kafka import get_kafka
        eventbus: "EventBus" = get_kafka()

        if request.headers.get("eventbus") == "rabbit":
            from buses.rabbit import get_rabbit
            eventbus = get_rabbit()

        return eventbus.produce_event(event_model)
