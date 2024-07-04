import abc
import json
from typing import Any, Dict, Union

from models.eventbus import Event


class JsonFileStorage:

    def __init__(self, file_path: str) -> None:
        self.file_path = file_path
        self.encoding = "utf8"

    def clear(self) -> None:
        try:
            file = open(self.file_path, "w", encoding=self.encoding)
            file.close()
        except FileNotFoundError:
            ...

    def save_events(self, events: list[Event]) -> None:
        try:
            with open(self.file_path, "a", encoding=self.encoding) as file:
                for event in events:
                    serialize_data = event.dict()
                    serialize_data["event_id"] = str(serialize_data.get("event_id"))
                    serialize_data["request_id"] = str(serialize_data.get("request_id"))
                    serialize_data["session_id"] = str(serialize_data.get("session_id"))
                    serialize_data["user_id"] = str(serialize_data.get("user_id"))
                    serialize_data["user_ts"] = str(serialize_data.get("user_ts"))
                    serialize_data["server_ts"] = str(serialize_data.get("server_ts"))
                    serialize_data["eventbus_ts"] = str(
                        serialize_data.get("eventbus_ts")
                    )
                    serialize_data["url"] = str(serialize_data.get("url"))
                    json.dump(serialize_data, file)
                    file.write("\n")
        except (FileNotFoundError, json.decoder.JSONDecodeError):
            ...

    def read_events(self) -> list:
        try:
            with open(self.file_path, encoding=self.encoding) as file:
                return [Event(**json.loads(line.strip())) for line in file]
        except (FileNotFoundError, json.decoder.JSONDecodeError):
            return []
