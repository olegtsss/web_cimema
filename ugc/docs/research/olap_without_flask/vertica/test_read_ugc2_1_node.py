import asyncio
import datetime as dt
from datetime import timedelta
import uuid

import vertica_python


BULK_COUNT = 1000
STRING_COUNT = 3 * BULK_COUNT

MAX_STEPS = 5
VERTICA_CONNECTION = {
    'host': '127.0.0.1',
    'port': 5433,
    'user': 'dbadmin',
    'password': '',
    'database': 'docker',
    'autocommit': True,
}


def prepair_database(cursor: vertica_python) -> None:
    cursor.execute('DROP TABLE test;')
    cursor.execute("""
        CREATE TABLE test (
            id UUID DEFAULT UUID_GENERATE(),
            user_id UUID,
            film_id UUID,
            rating TINYINT
        );
    """)


def create_data(cursor: vertica_python, bulk_count: int) -> None:
    cursor.executemany(
        'INSERT INTO test (user_id, film_id, rating) VALUES (?, ?, ?)',
        [
            (str(uuid.uuid4()), str(uuid.uuid4()), 5)
        ] * bulk_count,
        use_prepared_statements=True
    )


def create_control_data(cursor: vertica_python) -> None:
    cursor.execute("""
        INSERT INTO test
            (user_id, film_id, rating)
        VALUES (
            'a61caf17-879f-4773-91d0-298bea38d9ff',
            '8fbd9a0a-39b3-4a9d-9999-6b14c2e7833b',
            6
        )
    """)


def time_test(cursor: vertica_python) -> timedelta:
    start_time = dt.datetime.now()
    test = cursor.execute("""
        SELECT rating
        FROM test
        WHERE user_id = 'a61caf17-879f-4773-91d0-298bea38d9ff';
    """)
    return (dt.datetime.now() - start_time).microseconds


def cycle(string_count: int, bulk_count: int, max_steps: int) -> None:
    print(f'Подготавливается база данных в {string_count} строк')
    with vertica_python.connect(**VERTICA_CONNECTION) as connection:
        cursor = connection.cursor()
        prepair_database(cursor)
        for _ in range(string_count // bulk_count):
            create_data(cursor, bulk_count)
        create_control_data(cursor)
        time_bunk = [time_test(cursor) for _ in range(max_steps)]
        print(
            f'Среднее время запроса: {round(sum(time_bunk) / len(time_bunk))} микросекунд'
        )


if __name__ == '__main__':
    print(f'Вычисление средних результатов по результатам {MAX_STEPS} измерений')
    cycle(STRING_COUNT, BULK_COUNT, MAX_STEPS)
