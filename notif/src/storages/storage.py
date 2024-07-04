from contextlib import asynccontextmanager
from functools import wraps
from typing import AsyncGenerator, Optional
from uuid import UUID

from jinja2 import Template as JinjaTemplate
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from core.config import settings
from models.entity import Template, Notification, NotificationStatus
from schemas.entity import (
    CreateNotification, CreateNotificationStatus, CreateTemplate
)


class StorageManager:
    """Менеджер базы данных."""

    def __init__(self, engine: Optional[AsyncEngine] = None) -> None:
        self.engine = engine or create_async_engine(settings.pg_dsn)
        self.async_session = async_sessionmaker(
            self.engine, expire_on_commit=False
        )

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        async with self.async_session() as session:
            yield session

    @staticmethod
    def session_handler(method):
        @wraps(method)
        async def wrapper(self: "StorageManager", *args, **kwargs):
            session = kwargs.get("session")
            if session is not None:
                return await method(self, *args, **kwargs)

            async with self.get_session() as session:
                kwargs["session"] = session
                return await method(self, *args, **kwargs)

        return wrapper

    # === Tags ===

    @staticmethod
    def get_tags() -> list[dict[str, str]]:
        """Метод получения доступных тегов."""
        return [
            {
                "name": "first_name",
                "description": "Имя пользователя",   
            },
            {
                "name": "last_name",
                "description": "Фамилия пользователя",   
            },
            {
                "name": "user_tz",
                "description": "Таймзона пользователя",   
            },
            {
                "name": "email",
                "description": "Email пользователя",   
            },
        ]

    # === Templates ===

    @session_handler
    async def get_template(
        self, template_id: UUID, *, session: AsyncSession
    ) -> Optional[Template]:
        """Метод получения шаблона.

        Обязательные параметры:
        - `template_id` - id шаблона.
        """
        query = select(Template).where(Template.template_id == template_id)

        result = await session.execute(query)

        return result.scalar_one_or_none()

    @session_handler
    async def get_templates(
        self, limit: int = 10, offset: int = 0, *, session: AsyncSession
    ) -> list[Template]:
        """Метод получения шаблонов.

        Опциональные параметры:
        - `limit` - лимит;
        - `offset` - сдвиг.
        """
        query = (
            select(Template)
            .order_by(Template.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        result = await session.execute(query)

        return result.scalars().all()

    @staticmethod
    async def _validate_template(body: str) -> bool:
        """Метод валидации шаблона."""
        USER_TAGS_SET_EXAMPLE = {
            "first_name": "Fname",
            "last_name": "Lname",
            "user_tz": "Europe/Moscow",
            "email": "test@mail.ru",
        }

        try:
            template = JinjaTemplate(body, enable_async=True)
            await template.render_async(USER_TAGS_SET_EXAMPLE)
        except Exception as err:
            logger.error(err)
            return False
        else:
            return True

    @session_handler
    async def create_template(
        self, template_create_model: CreateTemplate, *, session: AsyncSession
    ) -> Optional[Template]:
        """Метод создания шаблона.

        Обязательные параметры:
        - `template_create_model` - модель создания шаблона.

        В случае ошибки рендеринга шаблона возращает `None`.
        """
        if not await self._validate_template(template_create_model.body):
            return None

        new_template = Template(**template_create_model.model_dump())

        session.add(new_template)
        await session.commit()

        return new_template

    # === Notifications ===

    @session_handler
    async def get_notification(
        self, notification_id: str, *, session: AsyncSession
    ) -> Optional[Template]:
        """Метод получения уведомления.

        Обязательные параметры:
        - `notification_id` - id уведомления.
        """
        query = (
            select(Notification)
            .where(Notification.notification_id == notification_id)
        )

        result = await session.execute(query)

        return result.scalar_one_or_none()

    @session_handler
    async def get_user_notifications(
        self,
        user_id: UUID,
        limit: int = 10,
        offset: int = 0,
        *,
        session: AsyncSession,
    ) -> list[Notification]:
        """Метод получения уведомлений пользователя.

        Обязательные параметры:
        - `user_id` - id пользователя.

        Опциональные параметры:
        - `limit` - лимит;
        - `offset` - сдвиг.
        """
        query = (
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        result = await session.execute(query)

        return result.scalars().all()

    @session_handler
    async def create_notification(
        self,
        notification_create_model: CreateNotification,
        *,
        session: AsyncSession,
    ) -> Notification:
        """Метод создания уведомления.

        Обязательные параметры:
        - `notification_create_model` - модель создания уведомления.
        """
        new_notification = Notification(**notification_create_model.model_dump())

        session.add(new_notification)
        await session.commit()

        return new_notification

    @session_handler
    async def get_notification_status(
        self,
        notification_id: str,
        *,
        session: AsyncSession,
    ) -> Optional[NotificationStatus]:
        """Метод получения статуса уведомления.

        Обязательные параметры:
        - `notification_id` - id уведомления.
        """
        query = (
            select(NotificationStatus)
            .where(NotificationStatus.notification_id == notification_id)
            .order_by(NotificationStatus.created_at.desc())
            .limit(1)
        )

        result = await session.execute(query)

        return result.scalar_one_or_none()

    @session_handler
    async def create_notification_status(
        self,
        notification_status_create_model: CreateNotificationStatus,
        *,
        session: AsyncSession,
    ) -> NotificationStatus:
        """Метод создания статуса уведомления.

        Обязательные параметры:
        - `notification_status_create_model` - модель создания статуса
        уведомления.
        """
        new_notification_status = NotificationStatus(
            **notification_status_create_model.model_dump()
        )

        session.add(new_notification_status)
        await session.commit()

        return new_notification_status


storage = StorageManager()
