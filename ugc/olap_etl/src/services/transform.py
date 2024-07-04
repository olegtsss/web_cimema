import uuid
from datetime import datetime

from loguru import logger

from models.eventbus import Event
from models.olap import OlapSchema


def transform_event_to_olap(event: Event) -> OlapSchema | None:
    try:
        curr = event.model_dump()
        return OlapSchema(**curr, id=uuid.uuid4(), event_time=datetime.now())
    except Exception as err:
        logger.exception(err)
        return None
