# ВНИМАНИЕ:
# Vertica при запуске долго стартует базу данных, около 60 секунд!
import asyncio
import uuid
import datetime as dt
import vertica_python
from typing import Any


BULK_COUNT = 1400


MAX_STEPS = 5
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


def test(bulk_count: int, connection: Any) -> tuple:
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
    start_time = dt.datetime.now()
    cursor.executemany(
        f'{CREATE_DATA_HEADER} (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
        [CREATE_DATA_PAYLOAD] * BULK_COUNT,
        use_prepared_statements=True
    )
    bulk_all_time = (dt.datetime.now() - start_time).microseconds
    bulk_middle_time = bulk_all_time / bulk_count
    cursor.execute('SELECT * FROM test;')
    data = []
    for row in cursor.iterate():
        data.append(row)
    errors = (bulk_count - len(data)) * bulk_count / 100
    return bulk_all_time, bulk_middle_time, errors


def cycle(bulk_count: int) -> None:
    step = 0
    bulk_all_time_bunk = []
    bulk_middle_time_bunk = []
    errors_bunk = []
    with vertica_python.connect(**VERTICA_CONNECTION) as connection:
        while step < MAX_STEPS:
            bulk_all_time, bulk_middle_time, errors = test(bulk_count, connection)
            bulk_all_time_bunk.append(bulk_all_time)
            bulk_middle_time_bunk.append(bulk_middle_time)
            errors_bunk.append(errors)
            step += 1
    print(
        f'Общее время загрузки {bulk_count} строк: '
        f'{round(sum(bulk_all_time_bunk) / len(bulk_all_time_bunk))} микросекунд'
    )
    print(
        f'Среднее время загрузки 1 строки: '
        f'{round(sum(bulk_middle_time_bunk) / len(bulk_middle_time_bunk))} микросекунд'
        )
    print(
        f'Ошибки: '
        f'{round(sum(errors_bunk) / len(errors_bunk))}%'
    )


if __name__ == '__main__':
    print(f'Вычислены средние результаты по результатам {MAX_STEPS} измерений')
    cycle(BULK_COUNT)
