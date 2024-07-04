from typing import Optional
from uuid import UUID

from sqlalchemy import func, text

from models.entity import (
    OrderEventModel,
    OrderModel,
    PaymentModel,
    PlanModel,
    RefundModel,
)
from providers.ukassa import ukassa_service
from providers.yapay import yapay_service
from schemas.entity import PaginationParams
from schemas.orders import (
    CreateOrderSchema,
    OrderEventTypeEnum,
    OrderProviderEnum,
    OrderStatusEnum,
    UpdateOrderSchema,
)
from schemas.plans import PlanPaymentTypeEnum
from storages.storage import storage


class OrderService:
    def __init__(self) -> None:
        pass

    async def get_order_events(
        self,
        order_id: UUID,
        user_id: UUID,
        pagination: PaginationParams = PaginationParams(),
    ) -> tuple[Optional[OrderModel], int, list[OrderEventModel]]:
        """Метод получения событий, связанных с заказом.

        Обязательные параметры:
        - `order_id` - id заказа;
        - `user_id` - id пользователя.

        Опциональные параметры:
        - `pagination` - схема параметров пагинации.

        Возвращает кортеж `(order, total_events, events)`, где order -
        связанный заказ, total_events - кол-во событий, events - список
        событий.

        Если связанный заказ не был найден, возвращает `(None, 0, [])`.
        """
        order = None
        total_events = 0
        events = []
        async with storage.async_session() as session:
            order = await storage.get_order(order_id, user_id, session=session)
            if order is None:
                return order, total_events, events

            total_events = await storage.count_order_events(order_id, session=session)

            events = await storage.get_order_events(
                order_id, pagination.limit, pagination.offset, session=session
            )

            return order, total_events, events

    async def get_order_payments(
        self,
        order_id: UUID,
        user_id: UUID,
        pagination: PaginationParams = PaginationParams(),
    ) -> tuple[Optional[OrderModel], int, list[PaymentModel]]:
        """Метод получения оплат, связанных с заказом.

        Обязательные параметры:
        - `order_id` - id заказа;
        - `user_id` - id пользователя.

        Опциональные параметры:
        - `pagination` - схема параметров пагинации.

        Возвращает кортеж `(order, total_payments, payments)`, где order -
        связанный заказ, total_payments - кол-во оплат, payments - список
        оплат.

        Если связанный заказ не был найден, возвращает `(None, 0, [])`.
        """
        order = None
        total_payments = 0
        payments = []
        async with storage.async_session() as session:
            order = await storage.get_order(order_id, user_id, session=session)
            if order is None:
                return order, total_payments, payments

            total_payments = await storage.count_order_payments(
                order_id, session=session
            )

            payments = await storage.get_order_payments(
                order_id, pagination.limit, pagination.offset, session=session
            )

            return order, total_payments, payments

    async def get_order_refunds(
        self,
        order_id: UUID,
        user_id: UUID,
        pagination: PaginationParams = PaginationParams(),
    ) -> tuple[Optional[OrderModel], int, list[RefundModel]]:
        """Метод получения возвратов, связанных с заказом.

        Обязательные параметры:
        - `order_id` - id заказа;
        - `user_id` - id пользователя.

        Опциональные параметры:
        - `pagination` - схема параметров пагинации.

        Возвращает кортеж `(order, total_refunds, refunds)`, где order -
        связанный заказ, total_refunds - кол-во возвратов, refunds - список
        возвратов.

        Если связанный заказ не был найден, возвращает `(None, 0, [])`.
        """
        order = None
        total_refunds = 0
        refunds = []
        async with storage.async_session() as session:
            order = await storage.get_order(order_id, user_id, session=session)
            if order is None:
                return order, total_refunds, refunds

            total_refunds = await storage.count_order_refunds(order_id, session=session)

            refunds = await storage.get_order_refunds(
                order_id, pagination.limit, pagination.offset, session=session
            )

            return order, total_refunds, refunds

    async def get_orders(
        self,
        user_id: UUID,
        pagination: PaginationParams = PaginationParams(),
    ) -> tuple[int, list[OrderModel]]:
        """Метод получения заказов пользователя.

        Обязательные параметры:
        - `user_id` - id пользователя.

        Опциональные параметры:
        - `pagination` - моедль параметров пагинации.

        Возвращает кортеж `(total_orders, orders)`, где total_orders - кол-во
        заказов, orders - заказов возвратов.
        """
        async with storage.async_session() as session:
            total_orders = await storage.count_orders(user_id, session=session)

            orders = await storage.get_orders(
                user_id,
                pagination.limit,
                pagination.offset,
                session=session,
            )

            return total_orders, orders

    async def create_order(
        self, create_order_schema: CreateOrderSchema
    ) -> tuple[Optional[OrderModel], Optional[str]]:
        """Метод создания заказа.

        Обязательные параметры:
        - `create_order_schema` - схема создания заказа.

        Возвращает кортеж `(order, error)`, где order - новый заказ, error -
        описанмие ошибки, возникшей при создании заказа.

        Факт создания заказа отделен от получения ссылки на оплату заказа на
        провайдере. Если заказ был создан, но `payment_link` нового заказа пуст
        и статус заказа `FAILED`, то в момент обращения к провайдеру произошла
        ошибка.
        """
        new_order = None
        error = None
        async with storage.async_session() as session:
            plan: PlanModel = await storage.get_plan(
                create_order_schema.plan_id, session=session
            )
            if plan is None:
                error = "Plan not found"
                return new_order, error
            if not plan.is_active:
                error = "Plan is inactive"
                return new_order, error

            if plan.payment_type == PlanPaymentTypeEnum.NEVER:
                create_order_schema.provider = None

                if plan.period > 0:
                    interval = f"{plan.period} {plan.unit.lower()}"
                    create_order_schema.expired = func.now() + text(
                        f"interval '{interval}'"
                    )
            else:
                if create_order_schema.provider is None:
                    error = (
                        "'provider' must not be empty if plan 'payment_type'"
                        " is 'ONCE' or 'RECURRENT'"
                    )
                    return new_order, error

                create_order_schema.expired = func.now() + text("interval '1 hour'")

            new_order = OrderModel(**create_order_schema.model_dump())
            session.add(new_order)

            await session.flush()

            new_order_event = OrderEventModel(
                order_id=new_order.order_id,
                event_type=OrderEventTypeEnum.CREATED,
                description="The order has been created",
            )
            session.add(new_order_event)

            await session.commit()

        if plan.payment_type in [
            PlanPaymentTypeEnum.ONCE,
            PlanPaymentTypeEnum.RECURRENT,
        ]:
            if create_order_schema.provider == OrderProviderEnum.YAPAY:
                payment_link = await yapay_service.get_payment_url(
                    product_id=new_order.plan_id,
                    order_id=new_order.order_id,
                    price=plan.price_per_unit,
                )
                status = OrderStatusEnum.PROCESSED
            elif create_order_schema.provider == OrderProviderEnum.UKASSA:
                payment_link = await ukassa_service.get_payment_url(
                    price=plan.price_per_unit
                )
                status = OrderStatusEnum.PROCESSED
            else:
                payment_link = ""
                status = OrderStatusEnum.FAILED

            new_order = await storage.update_order(
                new_order.order_id,
                UpdateOrderSchema(payment_link=payment_link, status=status),
            )

        return new_order, error

    async def get_order(self, order_id: UUID, user_id: UUID) -> Optional[OrderModel]:
        """Метод получения заказа.

        Обязательные параметры;
        - `order_id` - id заказа.
        - `user_id` - id пользователя.

        Возвращает `None`, если заказ не был найден.
        """
        return await storage.get_order(order_id, user_id)


order_service = OrderService()
