from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status

from api.v1.utils import security_jwt
from schemas.entity import ActiveOnlyParams, PaginationParams
from schemas.subs import (
    SubSchema,
    SubListResponse,
    SubEventSchema,
    SubEventListResponse,
)
from services.sub import sub_service

router = APIRouter(prefix="/subs", tags=["subs"])


@router.post(
    "/{sub_id}/cancel",
    status_code=status.HTTP_200_OK,
)
async def cancel_sub(
    sub_id: UUID,
    jwt_payload: dict[Any, Any] = Depends(security_jwt),
) -> Response:
    """Ручка отмены подписки.

    Обязательные path-параметры:
    - `sub_id` - id подписки.
    """
    user_id = jwt_payload.get("sub")
    sub, error = await sub_service.cancel_sub(sub_id, user_id)

    if sub is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sub not found",
        )

    if error is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error,
        )

    return Response(status_code=status.HTTP_200_OK)


@router.get(
    "/{sub_id}/events",
    response_model=SubEventListResponse,
    status_code=status.HTTP_200_OK,
)
async def get_sub_events(
    sub_id: UUID,
    pagination: PaginationParams = Depends(),
    jwt_payload: dict[Any, Any] = Depends(security_jwt),
) -> SubEventListResponse:
    """Ручка получения событий, связанных с подпиской.

    Обязательные path-параметры:
    - `sub_id` - id подписки.

    Опциональные query-параметры:
    - `limit` - лимит событий, по умолчанию 10;
    - `offset` - смещение, по умолчанию 0.

    Возвращает 404 ошибку, если подписка пользователя не была найдена.

    Возвращает пагинированный список связанных событий.
    """
    user_id = jwt_payload.get("sub")
    sub, total, events = await sub_service.get_sub_events(sub_id, user_id, pagination)
    if sub is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found",
        )

    return SubEventListResponse(
        limit=pagination.limit,
        offset=pagination.offset,
        total=total,
        results=[SubEventSchema.model_validate(event) for event in events],
    )


@router.get(
    "/{sub_id}",
    response_model=SubSchema,
    status_code=status.HTTP_200_OK,
)
async def get_sub(
    sub_id: UUID, jwt_payload: dict[Any, Any] = Depends(security_jwt)
) -> SubSchema:
    """Ручка получения подписки.

    Обязательные path-параметры:
    - `sub_id` - id подписки.

    Возвращает 404 ошибку, если подписка пользователя не была найдена.

    Возвращает подписку.
    """
    user_id = jwt_payload.get("sub")
    sub = await sub_service.get_sub(sub_id, user_id)
    if sub is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found",
        )

    return SubSchema.model_validate(sub)


@router.get(
    "",
    response_model=SubListResponse,
    status_code=status.HTTP_200_OK,
)
async def get_subs(
    pagination: PaginationParams = Depends(),
    active_only: ActiveOnlyParams = Depends(),
    jwt_payload: dict[Any, Any] = Depends(security_jwt),
) -> SubListResponse:
    """Ручка получения подписок.

    Опциональные query-параметры:
    - `limit` - лимит событий, по умолчанию 10;
    - `offset` - смещение, по умолчанию 0;
    - `active_only` - только активные, по умолчанию True.

    Возвращает пагинированный список связанных событий.
    """
    user_id = jwt_payload.get("sub")
    total, subs = await sub_service.get_subs(user_id, pagination, active_only)

    return SubListResponse(
        active_only=active_only.active_only,
        limit=pagination.limit,
        offset=pagination.offset,
        total=total,
        results=[SubSchema.model_validate(sub) for sub in subs],
    )
