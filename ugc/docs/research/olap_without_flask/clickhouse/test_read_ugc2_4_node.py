import asyncio
import datetime as dt
import uuid
from datetime import timedelta

from aiochclient import ChClient
from aiohttp import ClientSession


BULK_COUNT = 1000
STRING_COUNT = 3 * BULK_COUNT

MAX_STEPS = 5
CREATE_DATA_HEADER = (
    'INSERT INTO benchmarks.test (id, user_id, film_id, rating) VALUES '
)
CREATE_DATA_PAYLOAD = (
    '(generateUUIDv4(), generateUUIDv4(), generateUUIDv4(), 5)'
)
CREATE_DATA_FOOTER = ';'


async def create_data(bulk_count: int, client: ChClient) -> None:
    await client.execute(
        CREATE_DATA_HEADER + CREATE_DATA_PAYLOAD * bulk_count + CREATE_DATA_FOOTER
    )


async def create_control_data(client: ChClient) -> None:
    await client.execute(
        CREATE_DATA_HEADER +
        "(generateUUIDv4(), 'a61caf17-879f-4773-91d0-298bea38d9ff', generateUUIDv4(), 5)" +
        CREATE_DATA_FOOTER
    )

async def time_test(client: ChClient) -> timedelta:
    start_time = dt.datetime.now()
    await client.fetch("""
        SELECT rating
        FROM benchmarks.test
        WHERE user_id == 'a61caf17-879f-4773-91d0-298bea38d9ff'
    """)
    return (dt.datetime.now() - start_time).microseconds


async def cycle(string_count: int, bulk_count: int, max_steps: int) -> None:
    print(f'Подготавливается база данных в {string_count} строк')
    async with ClientSession() as session:
        client = ChClient(session)

        for _ in range(string_count // bulk_count):
            await create_data(bulk_count, client)
        await create_control_data(client)
        time_bunk = [await time_test(client) for _ in range(max_steps)]
        print(
            f'Среднее время запроса: {round(sum(time_bunk) / len(time_bunk))} микросекунд'
        )


if __name__ == '__main__':
    print(f'Вычисление средних результатов по результатам {MAX_STEPS} измерений')
    asyncio.run(cycle(STRING_COUNT, BULK_COUNT, MAX_STEPS))
