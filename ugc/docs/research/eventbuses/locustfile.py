from datetime import datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path
import random
import uuid

from locust import FastHttpUser, task, constant, events
from jose import jwt

BASE_DIR = Path(__file__).parent

priv_key_path = BASE_DIR.joinpath("private_key.pem")

PRIV_KEY = None

with open(priv_key_path) as f:
    PRIV_KEY = f.read()


@events.init_command_line_parser.add_listener
def _(parser):
    parser.add_argument(
        "--eventbus",
        choices=["kafka", "rabbit"],
        default="kafka",
        help="Choose eventbus",
    )


class MyUser(FastHttpUser):
    host = "https://localhost:443"
    wait_time = constant(0.1)
    hatch_rate = 20

    def on_start(self):
        self.token = self.get_bearer_token()

    @task
    def create_event(self):
        event = self.get_random_event()
        headers = event.get("headers") or {}
        headers |= {"Authorization": f"Bearer {self.get_bearer_token()}"}
        headers |= {"Eventbus": self.environment.parsed_options.eventbus}

        self.client.post(url=event["url"], json=event["json"], headers=headers)

    @staticmethod
    @lru_cache
    def get_bearer_token() -> str:
        token_jti = str(uuid.uuid4())
        iat = datetime.now(tz=timezone.utc)
        exp = iat + timedelta(days=30)
        payload = {
            "jti": token_jti,
            "iss": "AUTH",
            "sub": str(uuid.uuid4()),
            "aud": ["UGC"],
            "iat": iat,
            "exp": exp,
            "token_type": "access",
            "refresh_jti": str(uuid.uuid4()),
            "roles": ["USER"],
        }

        return jwt.encode(payload, PRIV_KEY, algorithm="RS256")

    @staticmethod
    def get_click_event_data() -> dict:
        return {
            "url": "/api/v1/events/click",
            "json": {
                "payload": {"element_id": "id-1", "element_payload": "some-payload"},
                "session_id": f"session-{random.randint(100000, 999999)}",
                "url": "https://practix.ru/click-page",
                "user_ts": int(datetime.timestamp(datetime.now())),
            },
        }

    @staticmethod
    def get_fully_watched_event_data() -> dict:
        return {
            "url": "/api/v1/events/fully_watched",
            "json": {
                "payload": {
                    "film_id": str(uuid.uuid4()),
                },
                "session_id": f"session-{random.randint(100000, 999999)}",
                "url": "https://practix.ru/fully-watched-page",
                "user_ts": int(datetime.timestamp(datetime.now())),
            },
        }

    @staticmethod
    def get_quality_changed_event_data() -> dict:
        qualities = (
            "240p",
            "360p",
            "480p",
            "720p",
            "1080p",
        )
        return {
            "url": "/api/v1/events/quality_changed",
            "json": {
                "payload": {
                    "film_id": str(uuid.uuid4()),
                    "next_quality": random.choice(qualities),
                    "previous_quality": random.choice(qualities),
                },
                "session_id": f"session-{random.randint(100000, 999999)}",
                "url": "https://practix.ru/quality-changed-page",
                "user_ts": int(datetime.timestamp(datetime.now())),
            },
        }

    @staticmethod
    def get_visit_event_data() -> dict:
        return {
            "url": "/api/v1/events/visit",
            "json": {
                "payload": {},
                "session_id": f"session-{random.randint(100000, 999999)}",
                "url": "https://practix.ru/visit-page",
                "user_ts": int(datetime.timestamp(datetime.now())),
            },
        }

    def get_random_event(self) -> dict:
        return random.choice(
            [
                self.get_click_event_data,
                self.get_fully_watched_event_data,
                self.get_quality_changed_event_data,
                self.get_visit_event_data,
            ]
        )()
