import asyncio
import sys

import backoff
import uvloop
from loguru import logger

from core.config import settings
from core.loggers import LOGGER_DEBUG, LOGGER_ERROR
from services.extract import BaseEventExtractor, get_extractor
from services.load import get_loader
from services.transform import transform_event_to_olap

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

logger.add(**LOGGER_DEBUG)
logger.add(**LOGGER_ERROR)


class EventsNotEnough(Exception): ...


@backoff.on_exception(backoff.expo, EventsNotEnough, max_time=180, logger=logger)
def consume_events(consumer: BaseEventExtractor) -> list:
    events = consumer.consume_batch()
    if not events:
        logger.info("No new events")
        raise EventsNotEnough
    events_count = len(events)
    if events_count < settings.batch_size_for_olap_loaded:
        logger.info(f"Count new events: {events_count}. It's small for olap download")
        raise EventsNotEnough
    return events


async def run():
    consumer = get_extractor()
    consumer.topics_subscribe()

    loader = get_loader()
    await loader.check_db()

    while True:
        try:
            # Extract
            events = consume_events(consumer)

            # Transform
            transformed_events = map(transform_event_to_olap, events)
            not_empty_transformed_events = filter(
                lambda item: item is not None, transformed_events
            )
            loaded_events = list(not_empty_transformed_events)

            # Load
            await loader.load_batch(loaded_events)
        except (KeyboardInterrupt, SystemExit):
            logger.info("Stop etl process")
            sys.exit()
        except Exception as err:
            logger.exception(err)
        else:
            logger.info(f"Обработано {len(loaded_events)} событий для OLAP")
        finally:
            if "consumer" in locals():
                logger.info("Stop consumer")
                consumer.stop()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
