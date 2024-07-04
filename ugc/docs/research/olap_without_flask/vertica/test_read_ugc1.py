import vertica_python
from typing import Any
import asyncio
import uuid
import datetime as dt


BULK_COUNT = 1000
STRING_COUNT = 10 * BULK_COUNT

MAX_STEPS = 1
VERTICA_CONNECTION = {
    'host': '127.0.0.1',
    'port': 5433,
    'user': 'dbadmin',
    'password': '',
    'database': 'docker',
    'autocommit': True,
}
CREATE_DATA_HEADER = ("""
    INSERT INTO test
        (
            event_id, request_id, session_id, user_id,
            user_ts, server_ts, eventbus_ts,
            url, event_type, event_subtype, payload
        )
    VALUES
""")
CREATE_DATA_PAYLOAD = (
    '8fbd9a0a-39b3-4a9d-9d17-6b14c2e7833b',
    'a84b0b67-90b2-4f25-a9e2-a253decff17c',
    '2146ba3b-c135-47e7-ab15-3c5333ef418f',
    '814627ce-7b34-4d21-b8c2-7f33adeeee03',
    1711282788,
    1711282788,
    1711282788,
    'https://practix.ru/movies/ce8f1de0-5c03-4638-ab84-cc462402e008',
    'custom',
    'quality_changed',
    '{payload: {film_id: ce8f1de0-5c03-4638-ab84-cc462402e008, previous_quality: 1080p, next_quality: 720p}}'
)


def prepair_database(connection: Any, bulk_count: int) -> None:
    cursor = connection.cursor()
    cursor.execute('DROP TABLE test;')
    cursor.execute("""
        CREATE TABLE test (
            id UUID DEFAULT UUID_GENERATE(),
            event_id UUID,
            request_id UUID,
            session_id UUID,
            user_id UUID,
            event_time TIMESTAMP DEFAULT NOW(),
            user_ts INTEGER,
            server_ts INTEGER,
            eventbus_ts INTEGER,
            url VARCHAR(256),
            event_type VARCHAR(256),
            event_subtype VARCHAR(256),
            payload VARCHAR(512)
        );
    """)    


def create_data(connection: Any, bulk_count: int) -> None:
    cursor = connection.cursor()
    cursor.executemany(
        f'{CREATE_DATA_HEADER} (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
        [CREATE_DATA_PAYLOAD] * BULK_COUNT,
        use_prepared_statements=True
    )


def test(connection: Any, bulk_count: int):
    cursor = connection.cursor()
    start_time = dt.datetime.now()
    cursor.execute(
        'SELECT user_id, SUM(user_ts) FROM test GROUP BY user_id ORDER BY user_id ASC'
    )
    bulk_all_time = (dt.datetime.now() - start_time).microseconds
    return bulk_all_time


def cycle(bulk_count: int) -> None:
    print(f'Подготавливается база данных в {STRING_COUNT} строк')
    with vertica_python.connect(**VERTICA_CONNECTION) as connection:
        prepair_database(connection, bulk_count)
        step = 0
        count = STRING_COUNT / bulk_count
        while step < count:
            create_data(connection, bulk_count)
            step += 1
        step = 0
        bulk_middle_time_bunk = []
        while step < MAX_STEPS:
            bulk_all_time = test(connection, bulk_count)
            bulk_middle_time_bunk.append(bulk_all_time)
            step += 1
        print(
            f'Среднее время запроса: '
            f'{round(sum(bulk_middle_time_bunk) / len(bulk_middle_time_bunk))} микросекунд'
            )


if __name__ == '__main__':
    print(f'Вычисление средних результатов по результатам {MAX_STEPS} измерений')
    cycle(BULK_COUNT)
