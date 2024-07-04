import asyncio
import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional
from uuid import UUID

import aio_pika
import aiohttp
import aiosmtplib
import uvloop
import websockets
from aiosmtplib.errors import SMTPException
from core.config import settings
from jinja2 import Template as JinjaTemplate
from loguru import logger
from models.entity import Template
from schemas.entity import Notification, NotificationChannel
from storages.sender import email_sender, ws_sender
from storages.storage import storage
from websockets.exceptions import WebSocketException
from websockets.sync.client import connect

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


class Worker:
    def __init__(self):
        self.smtp = email_sender.connect_with_server()
        # self.websocket = ws_sender.connect_with_server()  # Для запуска необходим ws server

    @staticmethod
    def error_handling(func):
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as err:
                logger.exception(err)
        return wrapper

    @error_handling
    async def process_message(
        self, message: aio_pika.abc.AbstractIncomingMessage
    ):
        """Метод процессинга новых сообщений."""
        async with message.process():
            notification = Notification.model_validate_json(message.body)

        if notification.channel == NotificationChannel.EMAIL:
            await self.send_email(notification)
        else:
            await self.send_ws(notification)

    async def consume(self):
        """Метод консьюминга уведомлений из очереди."""
        connection = await aio_pika.connect_robust(settings.rabbit_dsn)
        channel = await connection.channel()

        instant_queue_name = "instant_queue"
        instant_queue = await channel.declare_queue(
            instant_queue_name, durable=True
        )

        await instant_queue.consume(self.process_message)

        try:
            await asyncio.Future()
        finally:
            await connection.close()
            email_sender.disconnect_with_server(self.smtp)
            ws_sender.disconnect_with_server(self.websocket)


    async def get_tags(self, user_id: UUID) -> list[dict[str, str]]:
        """Метод получения тегов."""
        async with aiohttp.ClientSession(raise_for_status=True) as session:
            async with session.get(
                f"http://auth:8000/api/v1/users/{user_id}/profile"
            ) as resp:
                return await resp.json()

    async def get_template(self, template_id: UUID) -> Optional[Template]:
        """Метод получения шаблона."""
        return await storage.get_template(template_id)

    async def get_user_email(self, user_id: UUID) -> dict:
        """Метод получения email пользователя."""
        async with aiohttp.ClientSession(raise_for_status=True) as session:
            async with session.get(
                f"http://auth:8000/api/v1/users/{user_id}/email"
            ) as resp:
                return await resp.json()

    async def send_email(
        self,
        notification: Notification,
        subject: str = "Test"
    ) -> None:
        """Метод отправки email."""
        tags = await self.get_tags(notification.user_id)        
        template = await self.get_template(notification.template_id)

        template = JinjaTemplate(template.body, enable_async=True)
        body = await template.render_async(tags)

        to_email = await self.get_user_email(notification.user_id)
        to_email = to_email.get("email")

        if (
            not to_email
            or not body
            or datetime.datetime.now()
            > notification.created_at + settings.notification_life
        ):
            logger.warning(
                "Ошибка отправки email. Поле to: %s, поле body: %s, поле created_at: %s",
                to_email,
                body,
                notification.created_at,
            )
            return
        try:
            await email_sender.send(
                smtp=self.smtp,
                to=to_email.split(),
                subject=subject,
                body=body,
            )
        except SMTPException as error:
            logger.warning("Ошибка отправки email: %s", error)

    async def send_ws(
        self,
        notification: Notification,
        websocket_message: str = "Test {email}, {name}, {surname}"
    ) -> None:
        """Метод отправки ws."""
        tags = await self.get_tags(notification.user_id)
        body = websocket_message.format(**tags.dict())

        to_email = await self.get_user_email(notification.user_id)
        to_email = to_email.get("email")

        if (
            not to_email
            or len(to_email.split()) != 1
            or datetime.datetime.now()
            > notification.created_at + settings.notification_life
        ):
            logger.warning(
                "Ошибка отправки email. Поле to: %s, поле body: %s, поле created_at: %s",
                to_email,
                body,
                notification.created_at,
            )
            return
        message = "To: {to_email}. " + body
        try:
            ws_sender.send(
                websocket=self.websocket, message=message.format(to=to_email)
            )
        except WebSocketException as error:
            logger.warning("Ошибка отправки ws сообщения: %s", error)


worker = Worker()


if __name__ == "__main__":
    asyncio.run(worker.consume())
