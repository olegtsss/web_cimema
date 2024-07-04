from clickhouse_driver import Client
import uuid
from flask import Flask, request, jsonify
from http import HTTPStatus


app = Flask(__name__)
client = Client(host='clickhouse-node1')  # хост докера
# client = Client(host='localhost')  # хост для локального запуска

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

@app.route('/create/', methods=['GET'])
def create():
    # data = request.get_json()
    # short = data.get('custom_id')
    client.execute(CREATE_DATA_HEADER + CREATE_DATA_PAYLOAD + CREATE_DATA_FOOTER)
    return 'OK', HTTPStatus.CREATED


@app.route('/read/', methods=['GET'])
def read():
    data = client.execute('SELECT * FROM benchmarks.test;')
    return jsonify(data)


@app.route('/delete/', methods=['GET'])
def delete():
    data = client.execute('DELETE FROM benchmarks.test WHERE _row_exists;')
    return 'OK', HTTPStatus.OK


@app.route('/bulk/<int:count>/', methods=['GET'])
def bulk_create(count: int):
    client.execute(CREATE_DATA_HEADER + CREATE_DATA_PAYLOAD * count + CREATE_DATA_FOOTER)
    return 'OK', HTTPStatus.CREATED
