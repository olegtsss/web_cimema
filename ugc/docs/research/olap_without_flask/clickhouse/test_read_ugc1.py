from aiochclient import ChClient
from aiohttp import ClientSession
import asyncio
import uuid
import datetime as dt


BULK_COUNT = 1000
STRING_COUNT = 1000 * BULK_COUNT

MAX_STEPS = 1
CREATE_DATA_HEADER = (
    'INSERT INTO benchmarks.test '
    '('
        'id, event_id, request_id, session_id, user_id, '
        'event_time, user_ts, server_ts, eventbus_ts, '
        'url, event_type, event_subtype, payload'
    ') '
    'VALUES '
)
CREATE_DATA_PAYLOAD = (
    '('
        'generateUUIDv4(), '
        "'8fbd9a0a-39b3-4a9d-9d17-6b14c2e7833b', "
        "'a84b0b67-90b2-4f25-a9e2-a253decff17c', "
        "'2146ba3b-c135-47e7-ab15-3c5333ef418f', "
        "'814627ce-7b34-4d21-b8c2-7f33adeeee03', "
        'now(), '
        '1711282788, '
        '1711282788, '
        '1711282788, '
        "'https://practix.ru/movies/ce8f1de0-5c03-4638-ab84-cc462402e008', "
        "'custom', "
        "'quality_changed', "
        "{'payload':'{film_id: ce8f1de0-5c03-4638-ab84-cc462402e008, previous_quality: 1080p, next_quality: 720p}'}"
    ')'
)
CREATE_DATA_FOOTER = ';'


async def prepair_database(bulk_count: int) -> None:
    async with ClientSession() as s:
        client = ChClient(s)
        assert await client.is_alive()  # возвращает True, если соединение успешно
        result = await client.execute('DROP DATABASE IF EXISTS benchmarks;')
        result = await client.execute('CREATE DATABASE benchmarks;')
        result = await client.execute("""
            CREATE TABLE benchmarks.test (
                id UUID,
                event_id UUID,
                request_id UUID,
                session_id UUID,
                user_id UUID,
                event_time DateTime,
                user_ts Int64,
                server_ts Int64,
                eventbus_ts Int64,
                url String,
                event_type String,
                event_subtype String,
                payload Map(String, String)
                ) Engine=MergeTree() ORDER BY id;
        """)


async def create_data(bulk_count: int) -> None:
    async with ClientSession() as s:
        client = ChClient(s)
        await client.execute(CREATE_DATA_HEADER + CREATE_DATA_PAYLOAD * BULK_COUNT + CREATE_DATA_FOOTER)


async def test(bulk_count: int) -> tuple:
    async with ClientSession() as s:
        client = ChClient(s)
        start_time = dt.datetime.now()
        rows = await client.fetch(
            'SELECT user_id, SUM(user_ts) FROM benchmarks.test GROUP BY user_id ORDER BY user_id ASC'
        )
        bulk_all_time = (dt.datetime.now() - start_time).microseconds
        return bulk_all_time


async def cycle(bulk_count: int) -> None:
    print(f'Подготавливается база данных в {STRING_COUNT} строк')
    await prepair_database(bulk_count)
    step = 0
    count = STRING_COUNT / BULK_COUNT
    while step < count:
        await create_data(bulk_count)
        step += 1
    step = 0
    bulk_middle_time_bunk = []
    while step < MAX_STEPS:
        bulk_all_time = await test(bulk_count)
        bulk_middle_time_bunk.append(bulk_all_time)
        step += 1
    print(
        f'Среднее время запроса: '
        f'{round(sum(bulk_middle_time_bunk) / len(bulk_middle_time_bunk))} микросекунд'
        )


if __name__ == '__main__':
    print(f'Вычисление средних результатов по результатам {MAX_STEPS} измерений')
    asyncio.run(cycle(BULK_COUNT))
