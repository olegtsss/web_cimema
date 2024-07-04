import abc
from functools import lru_cache

import backoff
from aiochclient import ChClient
from aiohttp import ClientSession
from loguru import logger

from core.config import settings
from models.olap import OlapSchema


class BaseLoader(abc.ABC):
    @abc.abstractmethod
    def check_db(self): ...

    @abc.abstractmethod
    def load_batch(self, batch: list): ...


class ClickHouseLoader(BaseLoader):
    @backoff.on_exception(backoff.expo, Exception, logger=logger)
    async def check_db(self):
        async with ClientSession() as s:
            client = ChClient(s, url=settings.clickhouse_url)
            if not await client.is_alive():
                raise ConnectionError

            # await client.execute('DROP DATABASE IF EXISTS olap ON CLUSTER company_cluster')
            # logger.info("DB olap is deleted")

            await client.execute(
                "CREATE DATABASE IF NOT EXISTS olap ON CLUSTER company_cluster"
            )
            logger.info("DB OLAP is created")
            await client.execute(
                """CREATE TABLE IF NOT EXISTS olap.events ON CLUSTER company_cluster (
                id UUID,
                event_id UUID,
                request_id UUID,
                session_id UUID,
                user_id UUID,
                event_time DateTime,
                user_ts DateTime,
                server_ts DateTime,
                eventbus_ts DateTime,
                url String,
                event_type String,
                event_subtype String,
                payload Map(String, String)
                ) Engine=MergeTree() ORDER BY id;
            """
            )
            logger.info("Table EVENTS is created")

    @backoff.on_exception(backoff.expo, Exception, logger=logger)
    async def load_batch(self, batch: list[OlapSchema]):
        async with ClientSession() as s:
            client = ChClient(s, url=settings.clickhouse_url)
            if not await client.is_alive():
                raise ConnectionError

            data = [
                (
                    el.id,
                    el.event_id,
                    el.request_id,
                    el.session_id,
                    el.user_id,
                    el.event_time.replace(microsecond=0, tzinfo=None),
                    el.user_ts.replace(microsecond=0, tzinfo=None),
                    el.server_ts.replace(microsecond=0, tzinfo=None),
                    el.eventbus_ts.replace(microsecond=0, tzinfo=None),
                    str(el.url),
                    el.event_type,
                    el.event_subtype,
                    {"payload": str(el.payload)},
                )
                for el in batch
            ]

            await client.execute(
                "INSERT INTO olap.events "
                "("
                "id, event_id, request_id, session_id, user_id, event_time, user_ts, server_ts, "
                "eventbus_ts, url, event_type, event_subtype, payload"
                ")"
                " VALUES ",
                *data
            )


@lru_cache
def get_loader() -> BaseLoader:
    return ClickHouseLoader()
