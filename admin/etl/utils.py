import abc
import json
import logging
from functools import wraps
from time import sleep
from typing import Any, Dict

from config import app_settings
from constants import Messages
from elasticsearch import Elasticsearch, helpers
from schema import ElasticsearchData

logger = logging.getLogger(__name__)


class BaseStorage(abc.ABC):

    @abc.abstractmethod
    def save_state(self, state: Dict[str, Any]) -> None:
        """Сохранить состояние в хранилище."""

    @abc.abstractmethod
    def retrieve_state(self) -> Dict[str, Any]:
        """Получить состояние из хранилища."""


class JsonFileStorage(BaseStorage):

    def __init__(self, file_path: str) -> None:
        self.file_path = file_path
        self.mode = 'w'
        self.encoding = 'utf8'

    def save_state(self, state: Dict[str, Any]) -> None:
        with open(self.file_path, self.mode, encoding=self.encoding) as file:
            json.dump(state, file)

    def retrieve_state(self) -> Dict[str, Any]:
        try:
            with open(self.file_path, encoding=self.encoding) as file:
                return json.load(file)
        except (FileNotFoundError, json.decoder.JSONDecodeError):
            return dict()


class State:
    """Класс для работы с состояниями."""

    def __init__(self, storage: BaseStorage) -> None:
        self.storage = storage
        self.state = storage.retrieve_state()

    def set_state(self, key: str, value: Any) -> None:
        """Установить состояние для определённого ключа."""
        self.state[key] = value
        self.storage.save_state(self.state)

    def get_state(self, key: str) -> Any:
        """Получить состояние по определённому ключу."""
        return self.state.get(key, None)


def backoff(start_sleep_time=0.1, factor=2, border_sleep_time=10):
    """
    Функция для повторного выполнения функции через некоторое время,
    если возникла ошибка.
    """
    def func_wrapper(func):
        @wraps(func)
        def inner(error_count: int = 1, *args, **kwargs):
            current_sleep = start_sleep_time
            while True:
                try:
                    return func(*args, **kwargs)
                except Exception as error:
                    logging.info(
                        Messages.BACKOFF_MESSAGE.value, current_sleep, error
                    )
                    if current_sleep < border_sleep_time:
                        current_sleep = (
                            start_sleep_time * (factor ** error_count)
                        )
                        error_count += 1
                    else:
                        current_sleep = border_sleep_time
                    sleep(current_sleep)
        return inner
    return func_wrapper


@backoff()
def create_elk_index() -> None:
    with Elasticsearch(app_settings.elk_dsn) as elk_connect:
        if not elk_connect.ping():
            logger.info(Messages.ELK_SLEEP_OFFLINE.value)
            sleep(app_settings.sleep_time)
        if not elk_connect.indices.exists(
            index=app_settings.elk_index_name
        ):
            elk_connect.indices.create(
                index=app_settings.elk_index_name,
                settings=app_settings.elk_index_settings,
                mappings=app_settings.elk_index_mapping
            )
            logger.info(
                Messages.ELK_INDEX_CREATE.value,
                app_settings.elk_index_name
            )


def transform_data_for_elk(rows: list) -> list:
    transformed_part = []
    for row in rows:
        transformed_row = ElasticsearchData(
            id=row.get('id'),
            imdb_rating=row.get('rating'),
            genre=[
                genre.get('genre_name') for genre in row.get('genres')
            ],
            genres=[genre for genre in row.get('genres')],
            title=row.get('title'),
            description=row.get('description'),
            director=[
                person.get('person_name') for person in row.get('persons')
                if person.get('person_role') == 'director'
            ],
            directors=[
                person for person in row.get('persons')
                if person.get('person_role') == 'director'
            ],
            actors_names=[
                person.get('person_name') for person in row.get('persons')
                if person.get('person_role') == 'actor'
            ],
            writers_names=[
                person.get('person_name') for person in row.get('persons')
                if person.get('person_role') == 'writer'
            ],
            actors=[
                person for person in row.get('persons')
                if person.get('person_role') == 'actor'
            ],
            writers=[
                person for person in row.get('persons')
                if person.get('person_role') == 'writer'
            ],
        )
        transformed_part.append(transformed_row)
    return transformed_part


@backoff()
def download_to_elk(rows: list) -> None:
    with Elasticsearch(app_settings.elk_dsn) as elk_connect:
        helpers.bulk(
            client=elk_connect,
            actions=[
                {
                    '_index': app_settings.elk_index_name,
                    '_id': row.id,
                    '_source': row.model_dump_json()
                }
                for row in rows
            ],
            stats_only=True
        )
        logger.info(Messages.ELK_DOWNLOAD.value, len(rows))
