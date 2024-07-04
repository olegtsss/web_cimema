from uuid import UUID

import aio_pika
from fastapi import HTTPException, status

from core.config import settings
from models.entity import Template, NotificationStatus
from schemas.entity import (
    CreateNotification,
    CreateNotificationStatus,
    CreateTemplate,
    Notification,
    NotificationDeliveryMode,
    Pagination,
)
from storages.storage import storage


class Service:
    def __init__(self) -> None:
        pass

    async def get_tags(self) -> list[dict[str, str]]:
        """Метод получения тегов."""
        return storage.get_tags()

    async def get_templates(self, params: Pagination) -> list[Template]:
        """Метод получения шаблонов."""
        return await storage.get_templates(**params.model_dump())

    async def create_template(self, template_create_model: CreateTemplate):
        """Метод создания шаблона."""
        return await storage.create_template(template_create_model)

    async def get_template(self, template_id: UUID) -> Template:
        """Метод получения шаблона по id."""
        return await storage.get_template(template_id)

    async def produce_notification(self, notification: Notification):
        connection = await aio_pika.connect_robust(settings.rabbit_dsn)

        async with connection:
            channel = await connection.channel()

            await channel.declare_exchange(
                "direct_exchange", aio_pika.ExchangeType.DIRECT, durable=True
            )

            instant_queue_name = "instant_queue"
            scheduled_queue_name = "scheduled_queue"

            await channel.declare_queue(instant_queue_name, durable=True)
            await channel.declare_queue(scheduled_queue_name, durable=True)

            if notification.delivery_mode == NotificationDeliveryMode.INSTANT:
                routing_key = instant_queue_name
            else:
                routing_key = scheduled_queue_name

            body = notification.model_dump_json()

            await channel.default_exchange.publish(
                aio_pika.Message(body=body.encode()),
                routing_key=routing_key,
            )

    async def create_notification(
        self, notification_create_model: CreateNotification
    ):
        """Метод создания уведомления."""
        if notification_create_model.template_id is not None:
            if await storage.get_template(
                notification_create_model.template_id
            ) is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Template not found",
                )

        async with storage.get_session() as session:
            async with session.begin() as tr:
                new_notification = await storage.create_notification(
                    notification_create_model
                )

                await storage.create_notification_status(CreateNotificationStatus(
                    notification_id=new_notification.notification_id
                ))

                await tr.commit()

        await self.produce_notification(
            Notification.model_validate(new_notification)
        )

        return new_notification

    async def get_notification(self, notification_id: UUID):
        """Метод получения уведомления по id."""
        return await storage.get_notification(notification_id)

    async def get_user_notifications(self, user_id: UUID, params: Pagination):
        """Метод получения уведомлений пользователя."""
        return await storage.get_user_notifications(
            user_id, **params.model_dump()
        )

    async def get_notification_status(
        self, notification_id: UUID
    ) -> NotificationStatus:
        """Метод получения статуса уведомления по id."""
        return await storage.get_notification_status(notification_id)

service = Service()
