from functools import wraps
from typing import Callable, Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from core.config import settings
from models.entity import (
    Base,
    OrderModel,
    OrderEventModel,
    PaymentModel,
    PlanModel,
    RefundModel,
    SubModel,
    SubEventModel,
)
from schemas.orders import (
    CreateOrderEventSchema,
    CreateOrderSchema,
    UpdateOrderSchema,
    PaymentSchema,
)
from schemas.plans import CreatePlanSchema, UpdatePlanSchema
from schemas.subs import (
    CreateSubEventSchema,
    CreateSubSchema,
    SubStatusEnum,
    UpdateSubSchema,
)


class StorageManager:
    def __init__(self, engine: Optional[AsyncEngine] = None) -> None:
        self.engine = engine or create_async_engine(settings.pg_dsn)
        self.async_session = async_sessionmaker(self.engine, expire_on_commit=False)

    @staticmethod
    def session_handler(method: Callable) -> Callable:
        @wraps(method)
        async def wrapper(self: "StorageManager", *args, **kwargs):
            session = kwargs.get("session")
            if isinstance(session, AsyncSession):
                return await method(self, *args, **kwargs)

            async with self.async_session() as session:
                kwargs["session"] = session
                return await method(self, *args, **kwargs)

        return wrapper

    # === Plans ===

    @session_handler
    async def count_plans(
        self,
        active_only: bool = True,
        *,
        session: AsyncSession,
    ) -> int:
        """Метод получения кол-ва планов подписок.

        Опциональные параметры:
        - `active_only` - только активные, по умолчанию True.

        Возвращает кол-во подписок.
        """
        query = select(func.count(PlanModel.plan_id))

        if active_only:
            query = query.where(PlanModel.is_active == True)

        result = await session.execute(query)

        return result.scalar()

    @session_handler
    async def get_plans(
        self,
        limit: int = 10,
        offset: int = 0,
        active_only: bool = True,
        *,
        session: AsyncSession,
    ) -> list[PlanModel]:
        """Метод получения планов подписок.

        Опциональные параметры:
        - `limit` - лимит, 10 по умолчанию;
        - `offset` - смещение, 0 по умолчанию.
        - `active_only` - только активные, `True` по умолчанию;

        Возвращает список планов подписок.
        """
        query = (
            select(PlanModel)
            .order_by(PlanModel.created.desc())
            .limit(limit)
            .offset(offset)
        )

        if active_only:
            query = query.where(PlanModel.is_active == True)

        results = await session.execute(query)

        return results.scalars().all()

    @session_handler
    async def create_plan(
        self, create_plan_schema: CreatePlanSchema, *, session: AsyncSession
    ) -> tuple[bool, PlanModel]:
        """Метод создания плана подписки.

        Обязательные параметры:
        - `create_plan_model` - схема создания плана подписки.

        Возвращает кортеж `(created, new_plan)`, где created - признак
        создания плана подписки, new_plan - новый план подписки.
        """
        query = select(PlanModel).where(PlanModel.title == create_plan_schema.title)

        result = await session.execute(query)

        plan = result.scalar_one_or_none()

        if plan is not None:
            return False, plan

        new_plan = PlanModel(**create_plan_schema.model_dump())

        session.add(new_plan)

        await session.commit()
        await session.refresh(new_plan)

        return True, new_plan

    @session_handler
    async def get_plan(
        self,
        plan_id: UUID,
        for_update: bool = False,
        *,
        session: AsyncSession,
    ) -> Optional[PlanModel]:
        """Метод получения плана подписки.

        Обязательные параметры:
        - `plan_id` - id плана подписки.

        Опциональные параметры:
        - `for_update` - для обновления (лок в базе), по умолчанию False.

        Возвращает None, если план не был найден.
        """
        query = select(PlanModel).where(PlanModel.plan_id == plan_id)

        if for_update:
            query = query.with_for_update()

        result = await session.execute(query)

        return result.scalar_one_or_none()

    @session_handler
    async def update_plan(
        self,
        plan_id: UUID,
        update_plan_model: UpdatePlanSchema,
        *,
        session: AsyncSession,
    ) -> Optional[PlanModel]:
        """Метод обновления плана подписки.

        Обязательные параметры:
        - `plan_id` - id плана подписки;
        - `update_plan_model` - схема обновления плана подписки.

        Возвращает None, если план не был найден.
        """
        async with session.begin() as tr:
            plan: PlanModel = await self.get_plan(
                plan_id=plan_id, for_update=True, session=session
            )
            if plan is None:
                return None

            params = update_plan_model.model_dump(exclude_unset=True)
            for key, value in params.items():
                if hasattr(plan, key):
                    setattr(plan, key, value)

            plan.updated = func.now()

            await tr.commit()

        await session.refresh(plan)

        return plan

    # === Orders ===

    @session_handler
    async def count_order_events(
        self,
        order_id: UUID,
        *,
        session: AsyncSession,
    ) -> int:
        """Метод получения кол-ва событий, связанных с заказом.

        Обязательные параметры:
        - `order_id` - id заказа.

        Возвращает кол-во событий.
        """
        query = select(func.count(OrderEventModel.event_id)).where(
            OrderEventModel.order_id == order_id
        )

        result = await session.execute(query)

        return result.scalar()

    @session_handler
    async def get_order_events(
        self,
        order_id: UUID,
        limit: int = 10,
        offset: int = 0,
        *,
        session: AsyncSession,
    ) -> list[OrderEventModel]:
        """Метод получения событий, связанных с заказом.

        Обязательные параметры:
        - `order_id` - id заказа.

        Опциональные параметры:
        - `limit` - лимит оплат, по умолчанию 10.
        - `offset` - сдвиг, по умолчанию 0.

        Возвращает список связанных событий.
        """
        query = (
            select(OrderEventModel)
            .where(OrderEventModel.order_id == order_id)
            .order_by(OrderEventModel.created.desc())
            .limit(limit)
            .offset(offset)
        )

        result = await session.execute(query)

        return result.scalars().all()

    @session_handler
    async def count_order_payments(
        self,
        order_id: UUID,
        *,
        session: AsyncSession,
    ) -> int:
        """Метод получения кол-ва оплат, связанных с заказом.

        Обязательные параметры:
        - `order_id` - id заказа.

        Возвращает кол-во оплат.
        """
        query = select(func.count(PaymentModel.payment_id)).where(
            PaymentModel.order_id == order_id
        )

        result = await session.execute(query)

        return result.scalar()

    @session_handler
    async def get_order_payments(
        self,
        order_id: UUID,
        limit: int = 10,
        offset: int = 0,
        *,
        session: AsyncSession,
    ) -> list[PaymentModel]:
        """Метод получения оплат, связанных с заказом.

        Обязательные параметры:
        - `order_id` - id заказа.

        Опциональные параметры:
        - `limit` - лимит оплат, по умолчанию 10.
        - `offset` - сдвиг, по умолчанию 0.

        Возвращает список связанных оплат.
        """
        query = (
            select(PaymentModel)
            .where(PaymentModel.order_id == order_id)
            .order_by(PaymentModel.created.desc())
            .limit(limit)
            .offset(offset)
        )

        result = await session.execute(query)

        return result.scalars().all()

    @session_handler
    async def count_order_refunds(
        self,
        order_id: UUID,
        *,
        session: AsyncSession,
    ) -> int:
        """Метод получения кол-ва возвратов, связанных с заказом.

        Обязательные параметры:
        - `order_id` - id заказа.

        Возвращает кол-во возвратов.
        """
        query = select(func.count(RefundModel.refund_id)).where(
            RefundModel.order_id == order_id
        )

        result = await session.execute(query)

        return result.scalar()

    @session_handler
    async def get_order_refunds(
        self,
        order_id: UUID,
        limit: int = 10,
        offset: int = 0,
        *,
        session: AsyncSession,
    ) -> list[RefundModel]:
        """Метод получения возвратов, связанных с заказом.

        Обязательные параметры:
        - `order_id` - id заказа.

        Опциональные параметры:
        - `limit` - лимит оплат, по умолчанию 10.
        - `offset` - сдвиг, по умолчанию 0.

        Возвращает список связанных возвратов.
        """
        query = (
            select(RefundModel)
            .where(RefundModel.order_id == order_id)
            .order_by(RefundModel.created.desc())
            .limit(limit)
            .offset(offset)
        )

        result = await session.execute(query)

        return result.scalars().all()

    @session_handler
    async def count_orders(
        self,
        user_id: UUID,
        *,
        session: AsyncSession,
    ) -> int:
        """Метод получения кол-ва заказов.

        Обязательные параметры:
        - `user_id` - id пользователя.
        """
        query = select(func.count(OrderModel.order_id)).where(
            OrderModel.user_id == user_id
        )

        result = await session.execute(query)

        return result.scalar()

    @session_handler
    async def get_orders(
        self,
        user_id: UUID,
        limit: int = 10,
        offset: int = 0,
        *,
        session: AsyncSession,
    ) -> list[OrderModel]:
        """Метод получения заказов.

        Обязательные параметры:
        - `user_id` - id пользователя.

        Опциональные параметры:
        - `limit` - лимит заказов, по умолчанию 10;
        - `offset` - сдвиг, по умолчанию 0.

        Возвращает список заказов.
        """
        query = (
            select(OrderModel)
            .where(OrderModel.user_id == user_id)
            .order_by(OrderModel.created.desc())
            .limit(limit)
            .offset(offset)
        )

        result = await session.execute(query)

        return result.scalars().all()

    @session_handler
    async def create_order(
        self, create_order_schema: CreateOrderSchema, *, session: AsyncSession
    ) -> tuple[bool, OrderModel]:
        """Метод создания заказа.

        Обязательные параметры:
        - `create_order_schema` - схема создания заказа.

        Возвращает кортеж `(created, order)`, где created - признак создания
        заказа, order - заказ.
        """
        new_order = OrderModel(**create_order_schema.model_dump())

        session.add(new_order)

        await session.commit()
        await session.refresh(new_order)

        return new_order

    @session_handler
    async def get_order(
        self,
        order_id: UUID,
        user_id: Optional[UUID] = None,
        for_update: bool = False,
        *,
        session: AsyncSession,
    ) -> Optional[OrderModel]:
        """Метод получения заказа.

        Обязательные параметры:
        - `order_id` - id заказа.

        Опциональные параметры:
        - `user_id` - id пользователя, по умолчанию None;
        - `for_update` - для обновления (лок в базе), по умолчанию False.

        Если передан `user_id`, то поиск будет выполнен по условию
        `OrderModel.order_id == order_id AND OrderModel.user_id == user_id`.

        Возвращает None, если заказ не был найден.
        """
        query = select(OrderModel).where(OrderModel.order_id == order_id)

        if user_id is not None:
            query = query.where(OrderModel.user_id == user_id)

        if for_update:
            query = query.with_for_update()

        result = await session.execute(query)

        return result.scalar_one_or_none()

    @session_handler
    async def update_order(
        self,
        order_id: UUID,
        update_order_schema: UpdateOrderSchema,
        *,
        session: AsyncSession,
    ) -> Optional[OrderModel]:
        """Метод обновления заказа.

        Обязательные параметры:
        - `order_id` - id заказа;
        - `update_order_schema` - схема обновления заказа.

        Возвращает None, если заказ не был найден.
        """
        async with session.begin() as tr:
            order: OrderModel = await self.get_order(
                order_id=order_id, for_update=True, session=session
            )
            if order is None:
                return None

            params = update_order_schema.model_dump(exclude_unset=True)
            for key, value in params.items():
                if hasattr(order, key):
                    setattr(order, key, value)

            order.updated = func.now()

            await tr.commit()

        await session.refresh(order)

        return order

    # === Subs ===

    @session_handler
    async def count_subs(
        self,
        user_id: UUID,
        active_only: bool = True,
        *,
        session: AsyncSession,
    ) -> int:
        """Метод получения кол-ва подписок.

        Обязательные паарметры:
        - `user_id` - id пользователя.

        Опциональные параметры:
        - `active_only` - только активные, по умолчанию True.

        Возвращает кол-во подписок.
        """
        query = select(func.count(SubModel.sub_id)).where(SubModel.user_id == user_id)

        if active_only:
            query = query.where(SubModel.status == SubStatusEnum.ACTIVE)

        result = await session.execute(query)

        return result.scalar()

    @session_handler
    async def get_subs(
        self,
        user_id: UUID,
        limit: int = 10,
        offset: int = 0,
        active_only: bool = True,
        *,
        session: AsyncSession,
    ) -> list[SubModel]:
        """Метод получения подписок пользователя.

        Обязательные параметры:
        - `user_id` - id пользователя.

        Опциональные параметры:
        - `limit` - лимит подписок, по умолчанию 10;
        - `offset` - смещение, по умолчанию 0;
        - `active_only` - только активные, по умолчанию True.

        Возвращает список подписок.
        """
        query = select(SubModel).where(SubModel.user_id == user_id)

        if active_only:
            query = query.where(SubModel.status == SubStatusEnum.ACTIVE)

        query = query.order_by(SubModel.created.desc()).limit(limit).offset(offset)

        result = await session.execute(query)

        return result.scalars().all()

    @session_handler
    async def create_sub(
        self, create_sub_schema: CreateSubSchema, *, session: AsyncSession
    ) -> SubModel:
        """Метод создания подписки.

        Обязательные параметры:
        - `create_sub_schema` - схема параметров создания подписки.

        Возвращает новую подписку.
        """
        new_sub = SubModel(**create_sub_schema.model_dump())

        session.add(new_sub)

        await session.commit()
        await session.refresh(new_sub)

        return new_sub

    @session_handler
    async def get_sub(
        self,
        sub_id: UUID,
        user_id: Optional[UUID] = None,
        for_update: bool = False,
        *,
        session: AsyncSession,
    ) -> Optional[SubModel]:
        """Метод получения подписки.

        Обязательные параметры:
        - `sub_id` - id подписки.

        Опциональные параметры:
        - `user_id` - id пользователя, по умолчанию None;
        - `for_update` - для обновления (лок в базе), по умолчанию False.

        Если передан `user_id`, то поиск будет выполнен по условию
        `SubModel.sub_id == sub_id AND SubModel.user_id == user_id`.

        Возвращает None, если подписка не была найдена.
        """
        query = select(SubModel).where(SubModel.sub_id == sub_id)

        if user_id is not None:
            query = query.where(SubModel.user_id == user_id)

        if for_update:
            query = query.with_for_update()

        result = await session.execute(query)

        return result.scalar_one_or_none()

    @session_handler
    async def update_sub(
        self,
        sub_id: UUID,
        update_sub_schema: UpdateSubSchema,
        user_id: Optional[UUID] = None,
        *,
        session: AsyncSession,
    ) -> Optional[SubModel]:
        """Метод обновления подписки.

        Обязательные параметры:
        - `sub_id` - id подписки;
        - `update_sub_schema` - схема параметров обновления подписки.

        Опциональные параметры:
        - `user_id` - id пользователя, по умолчанию None.

        Если передан `user_id`, то поиск будет выполнен по условию
        `SubModel.sub_id == sub_id AND SubModel.user_id == user_id`.

        Возвращает `None`, если подписка не была найдена.
        """
        async with session.begin() as tr:
            sub: SubModel = await self.get_sub(
                sub_id=sub_id,
                user_id=user_id,
                for_update=True,
                session=session,
            )
            if sub is None:
                return None

            params = update_sub_schema.model_dump(exclude_unset=True)
            for key, value in params.items():
                if hasattr(sub, key):
                    setattr(sub, key, value)

            sub.updated = func.now()

            await tr.commit()

        await session.refresh(sub)

        return sub

    @session_handler
    async def count_sub_events(self, sub_id: UUID, *, session: AsyncSession) -> int:
        """Метод получения кол-ва событий, связанных с подпиской.

        Обязательные паарметры:
        - `sub_id` - id подписки.

        Возвращает кол-во событий.
        """
        query = select(func.count(SubEventModel.event_id)).where(
            SubEventModel.sub_id == sub_id
        )

        result = await session.execute(query)

        return result.scalar()

    @session_handler
    async def get_sub_events(
        self,
        sub_id: UUID,
        limit: int = 10,
        offset: int = 0,
        *,
        session: AsyncSession,
    ) -> list[SubEventModel]:
        """Метод получения событий, связанных с подпиской.

        Обязательные паарметры:
        - `sub_id` - id подписки.

        Опциональные параметры:
        - `limit` - лимит событий, по умолчанию 10;
        - `offset` - смещение, по умолчанию 0.

        Возвращает список событий.
        """
        query = (
            select(SubEventModel)
            .where(SubEventModel.sub_id == sub_id)
            .order_by(SubEventModel.created.desc())
            .limit(limit)
            .offset(offset)
        )

        result = await session.execute(query)

        return result.scalars().all()

    @session_handler
    async def create_sub_event(
        self,
        create_sub_event: CreateSubEventSchema,
        *,
        session: AsyncSession,
    ) -> SubEventModel:
        """Метод создания события, связанного с подпиской.

        Обязательные параметры:
        - `create_sub_event` - схема параметров создания события.

        Возвращает новое событие.
        """
        new_sub_event = SubEventModel(**create_sub_event.model_dump())

        session.add(new_sub_event)

        await session.commit()
        await session.refresh(new_sub_event)

        return new_sub_event

    @session_handler
    async def create_order_event(
        self,
        create_order_event: CreateOrderEventSchema,
        *,
        session: AsyncSession,
    ) -> OrderEventModel:
        """Метод создания события, связанного с заказом.

        Обязательные параметры:
        - `create_order_event` - схема параметров создания события.

        Возвращает новое событие.
        """
        new_order_event = SubEventModel(**create_order_event.model_dump())

        session.add(new_order_event)

        await session.commit()
        await session.refresh(new_order_event)

        return new_order_event

    @session_handler
    async def create_payment(
        self,
        create_payment: PaymentSchema,
        *,
        session: AsyncSession,
    ) -> PaymentModel:
        """Метод создания платежа.

        Обязательные параметры:
        - `create_payment` - схема параметров создания платежа.

        Возвращает новое событие.
        """
        new_payment = PaymentModel(**create_payment.model_dump())

        session.add(new_payment)

        await session.commit()
        await session.refresh(new_payment)

        return new_payment


storage = StorageManager()
