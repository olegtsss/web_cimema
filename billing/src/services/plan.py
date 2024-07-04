from uuid import UUID
from typing import Optional

from storages.storage import storage

from models.entity import PlanModel
from schemas.entity import ActiveOnlyParams, PaginationParams
from schemas.plans import CreatePlanSchema, UpdatePlanSchema


class PlanService:
    def __init__(self) -> None:
        pass

    async def get_plans(
        self,
        pagination: PaginationParams = PaginationParams(),
        active_only: ActiveOnlyParams = ActiveOnlyParams(),
    ) -> tuple[int, list[PlanModel]]:
        """Метод получения доступных планов подписок.

        Опциональные параметры:
        - `pagination` - схема параметров пагинации;
        - `active_only` - схема параметров активных подписок.

        Возвращает кортеж `(total_plans, plans)`, где total_plans - кол-во
        планов, plans - список планов подписок.
        """
        async with storage.async_session() as session:
            total_plans = await storage.count_plans(
                active_only.active_only, session=session
            )

            plans = await storage.get_plans(
                limit=pagination.limit,
                offset=pagination.offset,
                active_only=active_only.active_only,
                session=session,
            )

            return total_plans, plans

    async def create_plan(
        self, create_plan_schema: CreatePlanSchema
    ) -> tuple[bool, PlanModel]:
        """Метод создания плана подписки.

        Обязательные параметры:
        - `create_plan_model` - схема создания плана подписки.

        Возвращает кортеж `(created, new_plan)`, где created - признак создания
        плана подписки, new_plan - новый план подписки.
        """
        return await storage.create_plan(create_plan_schema)

    async def get_plan(self, plan_id: UUID) -> Optional[PlanModel]:
        """Метод получения плана подписки.

        Обязательные параметры;
        - `plan_id` - id плана подписки.

        Возвращает None, если план не был найден.
        """
        return await storage.get_plan(plan_id)

    async def update_plan(
        self, plan_id: UUID, update_plan_model: UpdatePlanSchema
    ) -> Optional[PlanModel]:
        """Метод обновления плана подписки.

        Обязательные параметры:
        - `plan_id` - id плана подписки;
        - `update_plan_model` - схема обновления плана подписки.

        Возвращает None, если план не был найден.
        """
        return await storage.update_plan(plan_id, update_plan_model)


plan_service = PlanService()
