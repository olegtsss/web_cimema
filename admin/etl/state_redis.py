import abc
from typing import Any, Dict
import json
from redis import Redis


class BaseStorage(abc.ABC):
    """Абстрактное хранилище состояния.

    Позволяет сохранять и получать состояние.
    Способ хранения состояния может варьироваться в зависимости
    от итоговой реализации. Например, можно хранить информацию
    в базе данных или в распределённом файловом хранилище.
    """

    @abc.abstractmethod
    def save_state(self, state: Dict[str, Any]) -> None:
        """Сохранить состояние в хранилище."""

    @abc.abstractmethod
    def retrieve_state(self) -> Dict[str, Any]:
        """Получить состояние из хранилища."""


class JsonFileStorage(BaseStorage):
    """Реализация хранилища, использующего локальный файл.

    Формат хранения: JSON
    """

    def __init__(self, file_path: str) -> None:
        self.file_path = file_path
        self.mode = 'w'
        self.encoding = 'utf8'

    def save_state(self, state: Dict[str, Any]) -> None:
        """Сохранить состояние в хранилище."""
        with open(self.file_path, self.mode, encoding=self.encoding) as file:
            json.dump(state, file)

    def retrieve_state(self) -> Dict[str, Any]:
        """Получить состояние из хранилища."""
        try:
            with open(self.file_path, encoding=self.encoding) as file:
                return json.load(file)
        except (FileNotFoundError, json.decoder.JSONDecodeError):
            return dict()


class RedisStorage(BaseStorage):
    """Реализация хранилища, использующего Redis."""

    def __init__(self, redis_adapter: Redis):
        self.redis_adapter = redis_adapter
        self.encoding = 'utf8'

    def save_state(self, state: Dict[str, Any]) -> None:
        """Сохранить состояние в хранилище."""
        for key, value in state.items():
            self.redis_adapter.set(name=key, value=value)

    def retrieve_state(self) -> Dict[str, Any]:
        """Получить состояние из хранилища."""
        state = dict()
        try:
            for key in self.redis_adapter.keys():
                state[key.decode(self.encoding)] = self.redis_adapter.get(key).decode(self.encoding)
        except Exception:
            ...
        return state


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


if __name__ == "__main__":
    test_storage = JsonFileStorage(file_path = 'test_file')
    test_storage.save_state(state=dict(one=1, two=2))
    test2 = test_storage.retrieve_state()

    test_state = State(storage=test_storage)
    test_state.set_state(key='3', value='three')
    test_state.get_state(key='3')

    redis_backend = Redis()
    test_storage = RedisStorage(redis_adapter=redis_backend)
    test_storage.save_state(state=dict(one=1, two=2))
    test2 = test_storage.retrieve_state()
    print()
