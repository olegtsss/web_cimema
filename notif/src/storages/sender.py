from abc import ABC, abstractmethod
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from functools import lru_cache
from typing import Any

import aiosmtplib
import websockets
from websockets.sync.client import connect
from core.config import settings


class ABCSender(ABC):
    """Абстрактный класс отправителя сообщений."""

    @abstractmethod
    def connect_with_server(self, *args, **kwargs) -> Any:
        raise NotImplementedError

    @abstractmethod
    def disconnect_with_server(self, *args, **kwargs) -> None:
        raise NotImplementedError

    @abstractmethod
    def send(self, *args, **kwargs) -> None:
        raise NotImplementedError


class WebsocketSender(ABCSender):
    def __init__(self):
        self.url = f"ws://{settings.websocket_host}:{settings.websocket_port}/"

    def connect_with_server(self) -> websockets.WebSocketServerProtocol:
        return connect(self.url)

    def disconnect_with_server(
        self, websocket: websockets.WebSocketServerProtocol
    ) -> None:
        websocket.close()

    def send(self, websocket: websockets.WebSocketServerProtocol, message: str) -> None:
        websocket.send(message)


class EmailSender(ABCSender):
    def __init__(self):
        self.format = "utf-8"

    async def connect_with_server(self) -> aiosmtplib.SMTP:
        smtp = aiosmtplib.SMTP(
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            use_tls=settings.smtp_tls,
        )
        await smtp.connect()
        await smtp.login(settings.smtp_login, settings.smtp_password)
        return smtp

    async def disconnect_with_server(self, smtp: aiosmtplib.SMTP) -> None:
        await smtp.quit()

    async def send(
        self,
        smtp: aiosmtplib.SMTP,
        to: list[str],
        subject: str,
        body: str,
        body_type: str = "html",
        subject_default: str = "Test",
    ):
        message = MIMEMultipart()
        message.preamble = subject_default
        message["Subject"] = subject
        message["From"] = settings.smtp_sender
        message["To"] = ", ".join(to)
        message.attach(MIMEText(body, body_type, self.format))
        await smtp.send_message(message)


@lru_cache()
def get_email_sender_service() -> EmailSender:
    return EmailSender()


@lru_cache()
def get_websocket_sender_service() -> WebsocketSender:
    return WebsocketSender()


email_sender = get_email_sender_service()
ws_sender = get_websocket_sender_service()
