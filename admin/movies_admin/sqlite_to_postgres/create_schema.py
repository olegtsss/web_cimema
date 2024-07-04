import logging
import os

import psycopg2
from dotenv import load_dotenv
from psycopg2 import (DatabaseError, DataError, IntegrityError, InterfaceError,
                      InternalError, NotSupportedError, OperationalError,
                      ProgrammingError)
from psycopg2.extensions import connection as _connection
from psycopg2.extras import DictCursor


load_dotenv()


MESSAGE_ERROR = 'При cоздании схемы в базе данных Postgres что-то пошло не так'
DSL = {
    'dbname': os.environ.get('POSTGRES_DB', 'postgre'),
    'user': os.environ.get('POSTGRES_USER', 'postgre'),
    'password': os.environ.get('POSTGRES_PASSWORD', 'postgre'),
    'host': os.environ.get('DB_HOST', '127.0.0.1'),
    'port': int(os.environ.get('DB_PORT', '5432')),
    'options': '-c search_path=content'
}


if __name__ == '__main__':
    logging.basicConfig(level=os.environ.get('LOG_LEVEL', 'INFO'))
    try:
        with psycopg2.connect(**DSL, cursor_factory=DictCursor) as pg_conn:
            with pg_conn.cursor() as cursor:
                pg_conn.cursor().execute('CREATE SCHEMA IF NOT EXISTS content;')
    except (
        InterfaceError, DatabaseError, DataError, OperationalError,
        IntegrityError, InternalError, ProgrammingError, NotSupportedError
    ) as error:
        logging.warning(MESSAGE_ERROR,)
    finally:
        pg_conn.close()
