import logging
import os
import sqlite3
from contextlib import closing
from dataclasses import astuple, dataclass, fields

import psycopg2
from dotenv import load_dotenv
from psycopg2 import (DatabaseError, DataError, IntegrityError, InterfaceError,
                      InternalError, NotSupportedError, OperationalError,
                      ProgrammingError)
from psycopg2.extensions import connection as _connection
from psycopg2.extras import DictCursor

from db_dataclasses import (Filmwork, Genre, GenreFilmwork, Person,
                            PersonFilmwork)

load_dotenv()


SIZE_BULK = 5
MESSAGE = 'В базу загружена информация из таблицы: %s'
MESSAGE_ERROR = 'При загрузку в базу данных что-то пошло не так: %s'
MESSAGE_ERROR_TEMPLATE = 'ERROR - {error}, VALUES - {bind_values}'
DSL = {
    'dbname': os.environ.get('DB_NAME', 'postgre'),
    'user': os.environ.get('DB_USER', 'postgre'),
    'password': os.environ.get('DB_PASSWORD', 'postgre'),
    'host': os.environ.get('DB_HOST', '127.0.0.1'),
    'port': int(os.environ.get('DB_PORT', '5432')),
    'options': '-c search_path=content'
}
FORMAT = '%Y/%m/%d %H:%M:%S'

SQLITE_GENRE = ('id', 'name', 'created_at', 'updated_at', 'description')
PG_GENRE = ('id', 'name', 'created', 'modified', 'description')

SQLITE_FILM_WORK = (
    'id', 'title', 'description', 'creation_date', 'rating', 'type',
    'created_at', 'updated_at', 'file_path'
)
PG_FILM_WORK = (
    'id', 'title', 'description', 'creation_date', 'rating', 'type',
    'created', 'modified', 'file_path'
)

SQLITE_PERSON = ('id', 'full_name', 'created_at', 'updated_at')
PG_PERSON = ('id', 'full_name', 'created', 'modified')

SQLITE_PERSON_FILMWORK = (
    'id', 'person_id', 'film_work_id', 'role', 'created_at'
)
PG_PERSON_FILMWORK = (
    'id', 'person_id', 'film_work_id', 'role', 'created'
)

SQLITE_GENRE_FIMWORK = ('id', 'genre_id', 'film_work_id', 'created_at')
PG_GENRE_FIMWORK = ('id', 'genre_id', 'film_work_id', 'created')


def load_to_postgre(
    pg_conn: _connection, dataclass_objects: list, pg_table: str,
    decode: str = 'utf-8'
) -> None:
    column_names = [field.name for field in fields(dataclass_objects[0])]
    column_count = ', '.join(['%s'] * len(column_names))
    try:
        with pg_conn.cursor() as cursor:
            bind_values = ', '.join(
                cursor.mogrify(
                    f'({column_count})', astuple(dataclass)
                ).decode(decode)
                for dataclass in dataclass_objects
            )
            cursor.execute(
                f'INSERT INTO content.{pg_table} ({", ".join(column_names)}) '
                f'VALUES {bind_values} ON CONFLICT (id) DO NOTHING'
            )
    except (
        InterfaceError, DatabaseError, DataError, OperationalError,
        IntegrityError, InternalError, ProgrammingError, NotSupportedError
    ) as error:
        logging.warning(
            MESSAGE_ERROR,
            MESSAGE_ERROR_TEMPLATE.format(error=error, bind_values=bind_values)
        )


def load_from_sqlite(
    sqlite_conn: sqlite3.Connection, pg_conn: _connection,
    dataclass: dataclass,
    sqlite_table: str, pg_table: str,
    sqlite_fields: tuple, pg_fields: tuple,
    size: int = SIZE_BULK
) -> None:
    '''Основной метод загрузки данных из SQLite в Postgres'''
    field_string = ', '.join(sqlite_fields)
    # Операции с курсором стоит проводить под with, чтобы гарантированно освободить занятые ресурсы.
    with closing(sqlite_conn.cursor()) as cursor:
        cursor.execute(f'SELECT {field_string} FROM {sqlite_table};')
        try:
            while True:
                results = cursor.fetchmany(size)
                objects = [
                    dataclass(
                        **{
                            pg_fields[result_item]: result[result_item]
                            for result_item in range(len(result))
                        }
                    ) for result in results
                ]
                if not objects:
                    break
                load_to_postgre(
                    pg_conn=pg_conn, dataclass_objects=objects, pg_table=pg_table
                )
        except (
            sqlite3.Error, sqlite3.InterfaceError, sqlite3.DatabaseError,
            sqlite3.DataError, sqlite3.OperationalError, sqlite3.IntegrityError,
            sqlite3.InternalError, sqlite3.ProgrammingError,
            sqlite3.NotSupportedError
        ) as error:
            logging.warning(
            MESSAGE_ERROR,
                MESSAGE_ERROR_TEMPLATE.format(error=error, bind_values=results)
           )
    logging.info(MESSAGE, sqlite_table)


if __name__ == '__main__':
    logging.basicConfig(level=os.environ.get('LOG_LEVEL', 'INFO'))
    try:
        with sqlite3.connect(
            os.environ.get('SQLITE_DB', 'db.sqlite')
        ) as sqlite_conn, psycopg2.connect(
            **DSL, cursor_factory=DictCursor
        ) as pg_conn:
            for table_ttx in (
                (
                    sqlite_conn, pg_conn, Genre, 'genre', 'genre',
                    SQLITE_GENRE, PG_GENRE
                ),
                (
                    sqlite_conn, pg_conn, Person, 'person', 'person',
                    SQLITE_PERSON, PG_PERSON
                ),
                (
                    sqlite_conn, pg_conn, Filmwork, 'film_work', 'film_work',
                    SQLITE_FILM_WORK, PG_FILM_WORK
                ),
                (
                    sqlite_conn, pg_conn, PersonFilmwork, 'person_film_work',
                    'person_film_work', SQLITE_PERSON_FILMWORK,
                    PG_PERSON_FILMWORK
                ),
                (
                    sqlite_conn, pg_conn, GenreFilmwork, 'genre_film_work',
                    'genre_film_work', SQLITE_GENRE_FIMWORK, PG_GENRE_FIMWORK
                )
            ):
                load_from_sqlite(*table_ttx)
    finally:
        sqlite_conn.close()
        pg_conn.close()
