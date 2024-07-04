from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from api.v1.utils import security_jwt
from schemas.entity import PaginationParams
from schemas.orders import (
    CreateOrderParams,
    CreateOrderSchema,
    OrderEventSchema,
    OrderEventListResponse,
    OrderListResponse,
    OrderSchema,
    OrderStatusEnum,
    PaymentListResponse,
    PaymentSchema,
    PaymentListResponse,
    RefundSchema,
    RefundListResponse,
)
from services.order import order_service

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get(
    "/{order_id}/events",
    status_code=status.HTTP_200_OK,
)
async def get_order_events(
    order_id: UUID,
    pagination: PaginationParams = Depends(),
    jwt_payload: dict[Any, Any] = Depends(security_jwt),
):
    """Метод получения событий, связанных с ордером.

    Обязательные path-параметры:
    - `order_id` - id заказа.

    Опциональные query-параметры:
    - `limit` - лимит ивентов, по умолчанию 10;
    - `offset` - смещение, по умолчанию 0.

    Возвращает 404 ошибку, если заказ не был найден.

    Возвращает пагинированный список связанных событий.
    """
    user_id = jwt_payload.get("sub")
    order, total, events = await order_service.get_order_events(
        order_id, user_id, pagination
    )
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Order not found"
        )

    return OrderEventListResponse(
        limit=pagination.limit,
        offset=pagination.offset,
        total=total,
        results=[OrderEventSchema.model_validate(event) for event in events],
    )


@router.get(
    "/{order_id}/payments",
    response_model=PaymentListResponse,
    status_code=status.HTTP_200_OK,
)
async def get_order_payments(
    order_id: UUID,
    pagination: PaginationParams = Depends(),
    jwt_payload: dict[Any, Any] = Depends(security_jwt),
) -> PaymentListResponse:
    """Ручка получения оплат, связанных с заказом.

    Обязательные path-параметры:
    - `order_id` - id заказа.

    Опциональные query-параметры:
    - `limit` - лимит оплат, по умолчанию 10;
    - `offset` - смещение, по умолчанию 0.

    Возвращает 404 ошибку, если заказ не был найден.

    Возвращает пагинированный список связанных оплат.
    """
    user_id = jwt_payload.get("sub")
    order, total, payments = await order_service.get_order_payments(
        order_id, user_id, pagination
    )
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Order not found"
        )

    return PaymentListResponse(
        limit=pagination.limit,
        offset=pagination.offset,
        total=total,
        results=[PaymentSchema.model_validate(payment) for payment in payments],
    )


@router.get(
    "/{order_id}/refunds",
    response_model=RefundListResponse,
    status_code=status.HTTP_200_OK,
)
async def get_order_refunds(
    order_id: UUID,
    pagination: PaginationParams = Depends(),
    jwt_payload: dict[Any, Any] = Depends(security_jwt),
) -> RefundListResponse:
    """Ручка получения возвратов, связанных с заказом.

    Обязательные path-параметры:
    - `order_id` - id заказа.

    Опциональные query-параметры:
    - `limit` - лимит возвратов, по умолчанию 10;
    - `offset` - смещение, по умолчанию 0.

    Возвращает 404 ошибку, если заказ не был найден.

    Возвращает пагинированный список связанных возвратов.
    """
    user_id = jwt_payload.get("sub")
    order, total, refunds = await order_service.get_order_refunds(
        order_id, user_id, pagination
    )
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Order not found"
        )

    return RefundListResponse(
        limit=pagination.limit,
        offset=pagination.offset,
        total=total,
        results=[RefundSchema.model_validate(refund) for refund in refunds],
    )


@router.get(
    "/{order_id}",
    response_model=OrderSchema,
    status_code=status.HTTP_200_OK,
)
async def get_order(
    order_id: UUID,
    jwt_payload: dict[Any, Any] = Depends(security_jwt),
) -> OrderSchema:
    """Ручка получения заказа пользователя.

    Обязательные параметры:
    - `order_id` - id заказа.

    Возвращает 404 ошибку, если заказ не был найден.

    Возвращает заказ.
    """
    user_id = jwt_payload.get("sub")
    order = await order_service.get_order(order_id, user_id)
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    return OrderSchema.model_validate(order)


@router.get(
    "",
    response_model=OrderListResponse,
    status_code=status.HTTP_200_OK,
)
async def get_orders(
    pagination: PaginationParams = Depends(),
    jwt_payload: dict[Any, Any] = Depends(security_jwt),
) -> OrderListResponse:
    """Ручка получения заказов пользователя.

    Опциональные query-параметры:
    - `limit` - лимит заказов, по умолчанию 10;
    - `offset` - смещение, по умолчанию 0.

    Возвращает пагинированный список заказов.
    """
    user_id = jwt_payload.get("sub")
    total, orders = await order_service.get_orders(user_id, pagination)

    return OrderListResponse(
        limit=pagination.limit,
        offset=pagination.offset,
        status=status.status,
        total=total,
        results=[OrderSchema.model_validate(order) for order in orders],
    )


@router.post(
    "",
    response_model=OrderSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_order(
    create_order_params: CreateOrderParams,
    jwt_payload: dict[Any, Any] = Depends(security_jwt),
) -> OrderSchema:
    """Ручка создания заказа.

    Обязательные body-параметры:
    - `plan_id` - id плана подписки.

    Опциональные body-параметры:
    - `provider` - провайдер приема платежа: `YAPAY`, `UKASSA`.

    Возвращает 400 ошибку, если для переданного платного плана не был указан
    провайдер.

    Возвращает новый заказ. Если в ответе отсутствует `payment_link` и статус
    нового заказа `FAILED`, то во время обращения к провайдеру для создания
    ссылки платежа возникла ошибка.
    """
    user_id = jwt_payload.get("sub")
    create_order_schema = CreateOrderSchema(
        **create_order_params.model_dump(),
        user_id=user_id,
        status=OrderStatusEnum.NEW,
    )
    order, error = await order_service.create_order(create_order_schema)

    if error is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error,
        )

    return OrderSchema.model_validate(order)
