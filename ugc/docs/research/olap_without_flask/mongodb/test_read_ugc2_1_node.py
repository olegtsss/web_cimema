import asyncio
import datetime as dt
import uuid
from datetime import timedelta
from typing import Any

from motor.motor_asyncio import AsyncIOMotorClient


BULK_COUNT = 1000
STRING_COUNT = 10000 * BULK_COUNT
MAX_STEPS = 10


def prepair_database(client: AsyncIOMotorClient) -> Any:
    client.drop_database('test')
    db = client['test']
    return db


async def create_data(bulk_count: int, db: Any) -> None:
    data = [
        {
            'user_id': str(uuid.uuid4()),
            'film_id': str(uuid.uuid4()),
            'rating': 5
        } for _ in range(bulk_count)
    ]
    await db.rating.insert_many(data)


async def create_control_data(db: Any) -> None:
    data = {
        'user_id': 'a61caf17-879f-4773-91d0-298bea38d9ff',
        'film_id': str(uuid.uuid4()),
        'rating': 6
    }
    await db.rating.insert_one(data)


async def time_test(db: Any) -> timedelta:
    start_time = dt.datetime.now()
    await db.rating.find_one(
        {'user_id': 'a61caf17-879f-4773-91d0-298bea38d9ff'}
    )
    return (dt.datetime.now() - start_time).microseconds


async def cycle(string_count: int, bulk_count: int, max_steps: int) -> None:
    print(f'Подготавливается база данных в {string_count} строк')
    client = AsyncIOMotorClient('mongodb://127.0.0.1:27019')
    db = prepair_database(client)

    for _ in range(string_count // bulk_count):
        await create_data(bulk_count, db)
    await create_control_data(db)
    time_bunk = [await time_test(db) for _ in range(max_steps)]
    print(
        f'Среднее время запроса: {round(sum(time_bunk) / len(time_bunk))} микросекунд'
    )


if __name__ == '__main__':
    print(f'Вычисление средних результатов по результатам {MAX_STEPS} измерений')
    asyncio.run(cycle(STRING_COUNT, BULK_COUNT, MAX_STEPS))
