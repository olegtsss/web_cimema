import datetime as dt
from clickhouse_driver import Client
from concurrent.futures import ThreadPoolExecutor


BULK_COUNT = 1000
TREADS_COUNT = 200

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


def task(number_task: int):
    start_time = dt.datetime.now()
    client = Client(host='127.0.0.1')
    client.execute(CREATE_DATA_HEADER + CREATE_DATA_PAYLOAD * BULK_COUNT + CREATE_DATA_FOOTER)
    bulk_all_time = (dt.datetime.now() - start_time).microseconds
    bulk_middle_time = bulk_all_time / BULK_COUNT
    # print(f'Поток {number_task} - среднее время загрузки одной строки {bulk_middle_time}')
    return bulk_middle_time


if __name__ == '__main__':
    print('Подготовка базы данных')
    client = Client(host='127.0.0.1')
    client.execute('DROP DATABASE IF EXISTS benchmarks;')
    client.execute('CREATE DATABASE benchmarks;')
    client.execute("""
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

    print(f'Загрузка в многопоточном режиме ({TREADS_COUNT} потоков, {BULK_COUNT} записей за запрос)')
    treads_bunk = range(0, TREADS_COUNT)
    with ThreadPoolExecutor(max_workers=TREADS_COUNT) as pool:
        pool_outputs = list(pool.map(task, treads_bunk))
    print(
        'Среднее время загрузки одной строки: '
        f'{round(sum(pool_outputs) / TREADS_COUNT)} микросекунд'
    )
