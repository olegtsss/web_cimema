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
    DROP TABLE test;
    """)
    print('OK')
