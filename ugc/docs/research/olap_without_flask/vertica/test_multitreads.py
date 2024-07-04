import datetime as dt
import vertica_python
from concurrent.futures import ThreadPoolExecutor


BULK_COUNT = 1000
TREADS_COUNT = 10

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


def task(number_task: int):
    start_time = dt.datetime.now()
    with vertica_python.connect(**VERTICA_CONNECTION) as connection:
        cursor = connection.cursor()
        cursor.executemany(
            f'{CREATE_DATA_HEADER} (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
            [CREATE_DATA_PAYLOAD] * BULK_COUNT,
            use_prepared_statements=True
        )
    bulk_all_time = (dt.datetime.now() - start_time).microseconds
    bulk_middle_time = bulk_all_time / BULK_COUNT
    # print(f'Поток {number_task} - среднее время загрузки одной строки {bulk_middle_time}')
    return bulk_middle_time


if __name__ == '__main__':
    print('Подготовка базы данных')
    with vertica_python.connect(**VERTICA_CONNECTION) as connection:
        cursor = connection.cursor()
        # cursor.execute('DROP TABLE test;')
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
    print(f'Загрузка в многопоточном режиме ({TREADS_COUNT} потоков, {BULK_COUNT} записей за запрос)')
    treads_bunk = range(0, TREADS_COUNT)
    with ThreadPoolExecutor(max_workers=TREADS_COUNT) as pool:
        pool_outputs = list(pool.map(task, treads_bunk))
    print(
        'Среднее время загрузки одной строки: '
        f'{round(sum(pool_outputs) / TREADS_COUNT)} микросекунд'
    )
