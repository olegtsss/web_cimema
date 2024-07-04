import uuid
from flask import Flask, request, jsonify
from http import HTTPStatus
import vertica_python


app = Flask(__name__)

connection_info = {
    'host': 'vertica',  # хост докера
    'port': 5433,
    'user': 'dbadmin',
    'password': '',
    'database': 'docker',
    'autocommit': True,
}


@app.route('/create/', methods=['GET'])
def create():
    with vertica_python.connect(**connection_info) as connection:
        cursor = connection.cursor()
        cursor.execute("""
        INSERT INTO test
            (
                event_id, request_id, session_id, user_id,
                user_ts, server_ts, eventbus_ts,
                url, event_type, event_subtype, payload
            )
        VALUES (
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
        );
        """)
    return 'OK', HTTPStatus.CREATED


@app.route('/read/', methods=['GET'])
def read():
    data = []
    with vertica_python.connect(**connection_info) as connection:
        cursor = connection.cursor()
        cursor.execute('SELECT * FROM test;')
        for row in cursor.iterate():
            data.append(row)
    return jsonify(data)


@app.route('/delete/', methods=['GET'])
def delete():
    with vertica_python.connect(**connection_info) as connection:
        cursor = connection.cursor()
        cursor.execute('DELETE FROM test;')
    return 'OK', HTTPStatus.OK
