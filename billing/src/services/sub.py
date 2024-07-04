from typing import Optional
from uuid import UUID

from models.entity import SubModel, SubEventModel
from schemas.entity import ActiveOnlyParams, PaginationParams
from schemas.orders import (
    CreateOrderEventSchema,
    OrderEventTypeEnum,
    OrderStatusEnum,
    UpdateOrderSchema,
)
from schemas.subs import (
    CreateSubEventSchema,
    SubEventTypeEnum,
    SubStatusEnum,
    UpdateSubSchema,
)
from services.auth import auth_service
from storages.storage import storage


class SubscriptionService:
    def __init__(self) -> None:
        pass

    async def get_subs(
        self,
        user_id: UUID,
        pagination: PaginationParams = PaginationParams(),
        active_only: ActiveOnlyParams = ActiveOnlyParams(),
    ) -> tuple[int, list[SubModel]]:
        """Метод получения подписок пользователя.

        Обязательные параметры:
        - `user_id` - id пользователя.

        Опциональные параметры:
        - `pagination` - схема параметров пагинации;
        - `active_only` - схема параметров активных подписок.

        Возвращает кортеж `(total_subs, subs)`, где total_subs - кол-во
        подписок, subs - список подписок.
        """
        async with storage.async_session() as session:
            total_subs = await storage.count_subs(
                user_id, active_only.active_only, session=session
            )

            subs = await storage.get_subs(
                user_id,
                pagination.limit,
                pagination.offset,
                active_only.active_only,
                session=session,
            )

            return total_subs, subs

    async def get_sub(self, sub_id: UUID, user_id: UUID) -> Optional[SubModel]:
        """Метод получения подписки пользователя.

        Обязательные параметры:
        - `sub_id` - id подписки;
        - `user_id` - id пользователя.

        Возвращает None, если подписка не была найдена.
        """
        return await storage.get_sub(sub_id, user_id)

    async def get_sub_events(
        self,
        sub_id: UUID,
        user_id: UUID,
        pagination: PaginationParams = PaginationParams(),
    ) -> tuple[Optional[SubModel], int, list[SubEventModel]]:
        """Метод получения событий, связанных с подпиской.

        Обязательные параметры:
        - `sub_id` - id подписки;
        - `user_id` - id пользователя.

        Опциональные параметры:
        - `pagination` - схема параметров пагинации.

        Возвращает кортеж `(sub, total_events, events)`, где sub - подписка,
        total_events - кол-во событий, events - список событий.
        """
        sub = None
        total_events = 0
        events = []
        async with storage.async_session() as session:
            sub = await storage.get_sub(sub_id, user_id, session=session)
            if sub is None:
                return sub, total_events, events

            total_events = await storage.count_sub_events(sub_id, session=session)

            events = await storage.get_sub_events(
                sub_id, pagination.limit, pagination.offset, session=session
            )

            return sub, total_events, events

    async def cancel_sub(
        self, sub_id: UUID, user_id: UUID
    ) -> tuple[Optional[SubModel], Optional[str]]:
        """Метод отмены подписки.

        Возвращает кортеж `(sub, error)`, где sub - подписка, error - ошибка.
        """
        async with storage.async_session() as session:
            # Получаем подписку
            sub: SubModel = await storage.get_sub(sub_id, user_id, session=session)
            error = None
            if sub is None:
                error = "Sub not found"
                return sub, error

            # Создаем событие отмены подписки
            create_sub_event = CreateSubEventSchema(
                sub_id=sub.sub_id,
                event_type=SubEventTypeEnum.CANCELED,
                description="Subscription has been canceled",
            )
            new_sub_event = await storage.create_sub_event(
                create_sub_event, session=session
            )

            # Обновляем подписку
            update_sub_schema = UpdateSubSchema(
                status=SubStatusEnum.CANCELED,
            )
            sub = await storage.update_sub(
                sub.sub_id, update_sub_schema, session=session
            )

            # Удаляем подписку в AUTH
            deleted = await auth_service.delete_sub(user_id, sub_id)
            if not deleted:
                error = "Auth sub deletion failed, please try again later"
                return sub, error

            # Создаем событие отмены заказа
            create_order_event = CreateOrderEventSchema(
                sub.order_id,
                OrderEventTypeEnum.CANCELED,
                "The order has been canceled",
            )
            new_order_event = await storage.create_order_event(
                create_order_event, session=session
            )

            # Обновляем заказ
            update_order_schema = UpdateOrderSchema(status=OrderStatusEnum.CANCELED)
            order = await storage.update_order(
                sub.order_id, update_order_schema, session=session
            )

        return sub, error


sub_service = SubscriptionService()
