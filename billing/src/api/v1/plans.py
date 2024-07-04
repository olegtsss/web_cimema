from typing import Any, Union
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from api.v1.utils import security_admin_jwt
from schemas.entity import ActiveOnlyParams, PaginationParams
from schemas.plans import (
    CreatePlanSchema,
    PlanSchema,
    PlanListResponse,
    UpdatePlanSchema,
)
from services.plan import plan_service

router = APIRouter(prefix="/plans", tags=["plans"])


@router.post(
    "/{plan_id}/activate",
    response_model=PlanSchema,
    status_code=status.HTTP_200_OK,
)
async def activate_plan(
    plan_id: str,
    _: dict[Any, Any] = Depends(security_admin_jwt),
) -> PlanSchema:
    """Ручка активации плана подписки.

    Обязательные path-параметры:
    - `plan_id` - id плана подписки.

    Возвращает `403` ошибку, если недостаточно прав для активации плана.
    Возвращает `404` ошибку, если план не был найден.

    Возвращает обновленный план подписки.
    """
    updated_plan = await plan_service.update_plan(
        plan_id, UpdatePlanSchema(is_active=True)
    )
    if updated_plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan not found",
        )

    return PlanSchema.model_validate(updated_plan)


@router.post(
    "/{plan_id}/deactivate",
    response_model=PlanSchema,
    status_code=status.HTTP_200_OK,
)
async def deactivate_plan(
    plan_id: str, _: dict[Any, Any] = Depends(security_admin_jwt)
) -> PlanSchema:
    """Ручка деактивации плана подписки.

    Обязательные path-параметры:
    - `plan_id` - id плана подписки.

    Возвращает `403` ошибку, если недостаточно прав для деактивации плана.
    Возвращает `404` ошибку, если план не был найден.

    Возвращает обновленный план подписки.
    """
    updated_plan = await plan_service.update_plan(
        plan_id, UpdatePlanSchema(is_active=False)
    )
    if updated_plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan not found",
        )

    return PlanSchema.model_validate(updated_plan)


@router.get(
    "/{plan_id}",
    response_model=PlanSchema,
    status_code=status.HTTP_200_OK,
)
async def get_plan(plan_id: UUID) -> PlanSchema:
    """Ручка получения плана подписки.

    Обязательные path-параметры:
    - `plan_id` - id плана подписки.

    Возвращает `404` ошибку, если план не был найден.

    Возвращает план подписки.
    """
    plan = await plan_service.get_plan(plan_id)
    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan not found",
        )

    return PlanSchema.model_validate(plan)


@router.get(
    "",
    response_model=PlanListResponse,
    status_code=status.HTTP_200_OK,
)
async def get_plans(
    pagination: PaginationParams = Depends(),
    active_only: ActiveOnlyParams = Depends(),
) -> PlanListResponse:
    """Ручка получения планов подписок.

    Опциональные query-параметры:
    - `limit` - лимит планов, по умолчанию 10;
    - `offset` - смещение, по умолчанию 0;
    - `active_only`- только активные планы, по умолчанию True.

    Возвращает пагинированный список планов подписок.
    """
    total, plans = await plan_service.get_plans(pagination, active_only)

    return PlanListResponse(
        limit=pagination.limit,
        offset=pagination.offset,
        total=total,
        active_only=active_only.active_only,
        results=[PlanSchema.model_validate(plan) for plan in plans],
    )


@router.post(
    "",
    response_model=PlanSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create plan",
)
async def create_plan(
    create_plan_schema: CreatePlanSchema,
    _: dict[Any, Any] = Depends(security_admin_jwt),
) -> PlanSchema:
    """Ручка создания плана подписки.

    Обязательные body-параметры:
    - `title` - название плана (уникальное, до 120 символов);
    - `description` - описание плана (до 500 символов);
    - `unit` - единица периода: `DAY`, `MONTH` или `YEAR`;
    - `period` - кол-во единиц периода (от 0 до 32768). Для рекурентных
    платежей (payment_type = `RECURRENT`) не может быть меньше 2;
    - `price_per_unit` - цена в единицу периода (от 0 до 1000000). Для палнов с
    оплатой (payment_type in [`ONCE`, `RECURRENT`]) должна быть больше 0;
    - `payment_type` - тип оплаты: `NEVER`, `ONCE` или `RECURRENT`;
    - `is_multiple` - является ли план "мультиподпиской".

    `NEVER` - план не предполагает оплаты, `ONCE` - план предполагает разовую
    оплату, `RECURRENT` - план предполагает регулярную оплату.

    Возвращает `403` ошибку, если недостаточно прав для создания плана.
    Возвращает `400` ошибку, если план с указанным `title` уже существует.

    Возвращает новый план подписки.
    """
    created, plan = await plan_service.create_plan(create_plan_schema)
    if not created:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(f"Plan with title '{create_plan_schema.title}'" f" already exists"),
        )

    return PlanSchema.model_validate(plan)
