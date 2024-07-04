import asyncio
import datetime as dt
from datetime import timedelta
import uuid

import asyncpg


BULK_COUNT = 1000
STRING_COUNT = 10000 * BULK_COUNT
MAX_STEPS = 5

DSL = 'postgresql://postgres:postgres@127.0.0.1:5432/database'


async def prepair_database(connection: asyncpg) -> None:
    await connection.fetch('DROP TABLE IF EXISTS test;')
    await connection.fetch("""
        CREATE TABLE test (
            id uuid PRIMARY KEY,
            user_id uuid,
            film_id uuid,
            rating SMALLINT
        );
    """)


async def create_data(bulk_count: int, connection: asyncpg) -> None:
    data = [
        (str(uuid.uuid4()), str(uuid.uuid4()), str(uuid.uuid4()), 5) for _ in range(bulk_count)
    ]
    await connection.copy_records_to_table('test', records=data)


async def create_control_data(connection: asyncpg) -> None:
    await connection.fetch("""
        INSERT INTO test VALUES
            (
                gen_random_uuid(),
                gen_random_uuid(),
                'a61caf17-879f-4773-91d0-298bea38d9ff',
                6
            );
    """)


async def time_test(connection: asyncpg) -> timedelta:
    start_time = dt.datetime.now()
    await connection.fetch("""
        SELECT rating
        FROM test
        WHERE film_id = 'a61caf17-879f-4773-91d0-298bea38d9ff'
    """)
    return (dt.datetime.now() - start_time).microseconds


async def cycle(string_count: int, bulk_count: int, max_steps: int) -> None:
    print(f'Подготавливается база данных в {string_count} строк')
    try:
        connection = await asyncpg.connect(DSL)
        await prepair_database(connection)
        for _ in range(string_count // bulk_count):
            await create_data(bulk_count, connection)
        await create_control_data(connection)
        time_bunk = [await time_test(connection) for _ in range(max_steps)]
        print(
            f'Среднее время запроса: {round(sum(time_bunk) / len(time_bunk))} микросекунд'
        )
    finally:
        await connection.close()


if __name__ == '__main__':
    print(f'Вычисление средних результатов по результатам {MAX_STEPS} измерений')
    asyncio.run(cycle(STRING_COUNT, BULK_COUNT, MAX_STEPS))
