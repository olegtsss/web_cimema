from datetime import timedelta
from typing import Optional

from loguru import logger
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncEngine, create_async_engine

from core.config import settings
from models.entity import (
    OrderEventModel,
    OrderModel,
    PaymentModel,
    PlanModel,
    SubEventModel,
    SubModel,
)
from providers.ukassa import ukassa_service
from providers.yapay import yapay_service
from schemas.orders import (
    OrderEventTypeEnum,
    OrderProviderEnum,
    OrderStatusEnum,
    OrderUkassaStatus,
    OrderYapayStatus,
)
from services.auth import auth_service
from schemas.auth import SubCreationSchema
from schemas.plans import PlanPaymentTypeEnum
from schemas.subs import SubEventTypeEnum, SubStatusEnum


class JobService:
    def __init__(self, engine: Optional[AsyncEngine] = None) -> None:
        self.engine = engine or create_async_engine(settings.pg_dsn)
        self.async_session = async_sessionmaker(self.engine, expire_on_commit=False)

    async def check_new_free_orders(self):
        async with self.async_session() as session:
            # Получаем NEW заказы с FREE планом
            subquery = select(PlanModel.plan_id).where(
                PlanModel.payment_type == PlanPaymentTypeEnum.NEVER
            )

            query = select(OrderModel).where(
                OrderModel.plan_id.in_(subquery),
                OrderModel.status == OrderStatusEnum.NEW,
            )

            result = await session.execute(query)

            new_free_orders = result.scalars().all()

            for order in new_free_orders:
                try:
                    # Обновляем статус заказа на ACTIVE
                    order.status = OrderStatusEnum.ACTIVE
                    order.updated = func.now()

                    # Создаем событие активации для заказа
                    new_order_event = OrderEventModel(
                        order_id=order.order_id,
                        event_type=OrderEventTypeEnum.ACTIVATED,
                        description="The order has been activated",
                    )
                    session.add(new_order_event)

                    # Создаем соответствующую подписку пользователя
                    new_sub = SubModel(
                        order_id=order.order_id,
                        plan_id=order.plan_id,
                        user_id=order.user_id,
                        expired=order.expired,
                    )
                    session.add(new_sub)

                    await session.flush()

                    # Создаем событие создания для подписки
                    new_sub_event = SubEventModel(
                        sub_id=new_sub.sub_id,
                        event_type=SubEventTypeEnum.CREATED,
                        description="Subscription has been created",
                    )
                    session.add(new_sub_event)

                    # Коммитим изменения в базу
                    await session.commit()

                except Exception:
                    # Логируем ошибку транзы
                    logger.exception(f"Order '{order.order_id}' activation failed")

                # Уведомляем о новой подписке AUTH
                create_sub_schema = SubCreationSchema(
                    sub_id=new_sub.sub_id,
                    plan_id=new_sub.plan_id,
                    user_role=new_sub.user_role,
                    created=new_sub.created,
                    expired=new_sub.expired,
                )
                await auth_service.create_sub(create_sub_schema)

    async def check_new_orders(self):
        async with self.async_session() as session:
            # Получаем PROCESSED заказы, для которых expired < NOW() - 1 hour
            query = select(OrderModel).where(
                OrderModel.status == OrderStatusEnum.PROCESSED,
                OrderModel.expired < (func.now() - timedelta(hours=1)),
            )

            result = await session.execute(query)

            new_orders = result.scalars().all()

            final_provider_statuses = ["PAID", "FAILED", "CANCELED", "EXPIRED"]
            for order in new_orders:
                order: OrderModel

                if order.provider == OrderProviderEnum.YAPAY:
                    status = await yapay_service.get_order_payment_status(
                        order.order_id
                    )
                elif order.provider == OrderProviderEnum.UKASSA:
                    status = await ukassa_service.get_order_payment_status(
                        order.order_id
                    )
                else:
                    status = None

                try:
                    if status in (
                        OrderUkassaStatus.SUCCEEDED,
                        OrderYapayStatus.CAPTURED,
                    ):
                        # Успешная оплата

                        # Получаем план
                        plan = await session.execute(
                            (
                                select(PlanModel).where(
                                    PlanModel.plan_id == order.plan_id
                                )
                            )
                        )
                        plan = plan.scalar()

                        # Создаем оплату заказа
                        new_order_payment = PaymentModel(
                            order_id=order.order_id,
                            data={"info": "There must be some data from provider"},
                        )
                        session.add(new_order_payment)

                        # Создаем событие оплаты заказа
                        new_order_event = OrderEventModel(
                            order_id=order.order_id,
                            event_type=OrderEventTypeEnum.PAYMENT_CREATED,
                            description=f"The order has been paid",
                        )
                        session.add(new_order_event)

                        # Обновляем заказ
                        order.status = OrderStatusEnum.ACTIVE
                        order.updated = func.now()
                        interval = f"interval '{plan.period} {plan.unit.lower()}'"
                        order.expired = func.now() + text(interval)

                        # Создаем событие активации заказа
                        new_order_event = OrderEventModel(
                            order_id=order.order_id,
                            event_type=OrderEventTypeEnum.ACTIVATED,
                            description="The order has been activated",
                        )
                        session.add(new_order_event)

                        # Создаем соответствующую подписку пользователя
                        new_sub = SubModel(
                            order_id=order.order_id,
                            plan_id=order.plan_id,
                            user_id=order.user_id,
                            expired=order.expired,
                        )
                        session.add(new_sub)

                        await session.flush()

                        # Создаем событие создания для подписки
                        new_sub_event = SubEventModel(
                            sub_id=new_sub.sub_id,
                            event_type=SubEventTypeEnum.CREATED,
                            description="Subscription has been created",
                        )
                        session.add(new_sub_event)

                        # Уведомляем о новой подписке AUTH
                        create_sub_schema = SubCreationSchema(
                            sub_id=new_sub.sub_id,
                            plan_id=new_sub.plan_id,
                            user_role=new_sub.user_role,
                            created=new_sub.created,
                            expired=new_sub.expired,
                        )
                        await auth_service.create_sub(create_sub_schema)

                    elif status is not None:
                        # Заказ не был оплачен

                        # Создаем событие неуспешной оплаты заказа
                        new_order_event = OrderEventModel(
                            order_id=order.order_id,
                            event_type=OrderEventTypeEnum.PAYMENT_FAILED,
                            description="The order has not been paid",
                        )
                        session.add(new_order_event)

                        # Обновляем заказ
                        order.status = OrderStatusEnum.UNPAID
                        order.updated = func.now()
                        order.expired = func.now()

                    # Коммитим изменения в базу
                    await session.commit()

                except Exception:
                    # Логируем ошибку
                    logger.exception(f"Order '{order.order_id}' activation failed")

    async def check_active_recurent_orders(self):
        async with self.async_session() as session:
            # Получаем id планов с типом оплаты RECURENT
            subquery = select(PlanModel.plan_id).where(
                PlanModel.payment_type == PlanPaymentTypeEnum.RECURRENT
            )

            # Получаем ACTIVE заказы, с expired < now() и RECURENT планом
            query = select(OrderModel).where(
                OrderModel.status == OrderStatusEnum.ACTIVE,
                OrderModel.expired < func.now(),
                OrderModel.plan_id.in_(subquery),
            )

            result = await session.execute(query)

            recurent_orders = result.scalars().all()

            for order in recurent_orders:
                order: OrderModel

                if order.provider == OrderProviderEnum.YAPAY:
                    status = await yapay_service.get_order_payment_status(
                        order.order_id
                    )
                elif order.provider == OrderProviderEnum.UKASSA:
                    status = await ukassa_service.get_order_payment_status(
                        order.order_id
                    )
                else:
                    status = None

                try:
                    if status in (
                        OrderUkassaStatus.SUCCEEDED,
                        OrderYapayStatus.CAPTURED,
                    ):
                        # Успешно продлен

                        # Получаем план
                        plan = await session.execute(
                            (
                                select(PlanModel).where(
                                    PlanModel.plan_id == order.plan_id
                                )
                            )
                        )
                        plan = plan.scalar()

                        # Создаем оплату заказа
                        new_order_payment = PaymentModel(
                            order_id=order.order_id,
                            data={"info": "There must be some data from provider"},
                        )
                        session.add(new_order_payment)

                        # Создаем событие оплаты заказа
                        new_order_event = OrderEventModel(
                            order_id=order.order_id,
                            event_type=OrderEventTypeEnum.PAYMENT_CREATED,
                            description=f"The order has been paid",
                        )
                        session.add(new_order_event)

                        # Обновляем заказ
                        order.updated = func.now()
                        interval = f"interval '{plan.period} {plan.unit.lower()}'"
                        order.expired = func.now() + text(interval)

                        # Создаем событие продления заказа
                        new_order_event = OrderEventModel(
                            order_id=order.order_id,
                            event_type=OrderEventTypeEnum.EXTENDED,
                            description="The order has been extended",
                        )
                        session.add(new_order_event)

                    elif status is not None:
                        # Ошибка продления

                        # Создаем событие ошибки оплаты продления заказа
                        new_order_event = OrderEventModel(
                            order_id=order.order_id,
                            event_type=OrderEventTypeEnum.PAYMENT_FAILED,
                            description=f"The order extension payment failed",
                        )
                        session.add(new_order_event)

                        # Обновляем заказ
                        order.updated = func.now()
                        order.status = OrderStatusEnum.NOTEXTENDED
                        order.expired = func.now()

                        # Создаем событие непродления заказа
                        new_order_event = OrderEventModel(
                            order_id=order.order_id,
                            event_type=OrderEventTypeEnum.NOTEXTENDED,
                            description=f"The order has not been extended",
                        )
                        session.add(new_order_event)

                        # Получаем подписку
                        query = select(SubModel).where(
                            SubModel.order_id == order.order_id
                        )

                        result = await session.execute(query)

                        sub: SubModel = result.scalar_one_or_none()
                        if sub is not None:
                            # Создаем событие отмены подписки
                            new_sub_event = SubEventModel(
                                sub_id=sub.sub_id,
                                event_type=SubEventTypeEnum.CANCELED,
                                description="Subscription has been canceled",
                            )
                            session.add(new_sub_event)

                            # Обновляем подписку
                            sub.status = SubStatusEnum.CANCELED
                            sub.updated = func.now()
                            sub.expired = func.now()

                        # Удаляем подписку auth
                        await auth_service.delete_sub(sub.user_id, sub.sub_id)

                    # Коммитим изменения в базу
                    await session.commit()

                except Exception:
                    # Логируем ошибку
                    logger.exception(f"Order '{order.order_id}' activation failed")

    async def check_expired_orders(self):
        async with self.async_session() as session:
            # Получаем ACTIVE заказы, для которых expired < NOW() - 3 hour
            subquery = select(OrderModel.order_id).where(
                OrderModel.status == OrderStatusEnum.ACTIVE,
                OrderModel.expired < (func.now() - timedelta(hours=3)),
            )

            query = (
                select(OrderModel)
                .join(PlanModel, OrderModel.plan_id == PlanModel.plan_id)
                .where(
                    OrderModel.order_id.in_(subquery),
                    OrderModel.created
                    + text(
                        "interval ' || "
                        + PlanModel.period
                        + " || "
                        + PlanModel.unit
                        + " || '"
                    )
                    < func.now(),
                )
            )

            result = await session.execute(query)

            expired_orders = result.scalars().all()

            for order in expired_orders:
                order: OrderModel

                try:
                    # Создать событие для заказа expired
                    new_order_event = OrderEventModel(
                        order_id=order.order_id,
                        event_type=OrderEventTypeEnum.EXPIRED,
                        description=f"The order has been expired",
                    )
                    session.add(new_order_event)

                    # Обновить заказ на expired
                    order.status = OrderStatusEnum.EXPIRED
                    order.updated = func.now()
                    order.expired = func.now()

                    # Получаем подписку
                    query = select(SubModel).where(SubModel.order_id == order.order_id)

                    result = await session.execute(query)

                    sub: SubModel = result.scalar_one_or_none()
                    if sub is not None:
                        # Создаем событие исполнения подписки
                        new_sub_event = SubEventModel(
                            sub_id=sub.sub_id,
                            event_type=SubEventTypeEnum.EXPIRED,
                            description="Subscription has been expired",
                        )
                        session.add(new_sub_event)

                        # Обновляем подписку
                        sub.status = SubStatusEnum.EXPIRED
                        sub.updated = func.now()
                        sub.expired = func.now()

                    # Отменить подписку в AUTH
                    await auth_service.delete_sub(sub.user_id, sub.sub_id)

                    # Коммитим изменения в базу
                    await session.commit()

                except Exception:
                    # Логируем ошибку
                    logger.exception(f"Order '{order.order_id}' activation failed")


job_service = JobService()
