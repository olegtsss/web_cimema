# ВНИМАНИЕ:
# Vertica при запуске долго стартует базу данных, около 60 секунд!

import vertica_python


connection_info = {
    'host': '127.0.0.1',
    'port': 5433,
    'user': 'dbadmin',
    'password': '',
    'database': 'docker',
    'autocommit': True,
}


with vertica_python.connect(**connection_info) as connection:
    cursor = connection.cursor()
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
    print('OK')
