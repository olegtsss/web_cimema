from datetime import datetime
from enum import Enum
from typing import Any, Optional, Union
from uuid import UUID

from schemas.entity import CustomBaseModel, PaginatedResponse
from sqlalchemy import BinaryExpression


# === Enums ===


class OrderProviderEnum(str, Enum):
    YAPAY: str = "YAPAY"
    UKASSA: str = "UKASSA"


class OrderStatusEnum(str, Enum):
    NEW: str = "NEW"  # новый заказ
    FAILED: str = "FAILED"  # при создании заказа возникла ошибка
    PROCESSED: str = "PROCESSED"  # заказ создан, в ожидании обработки оплаты
    UNPAID: str = "UNPAID"  # не был оплачен/не достаточно средств/заказ просрочен и тд
    ACTIVE: str = "ACTIVE"  # был оплачен, заказ активен
    NOTEXTENDED: str = "NOTEXTENDED"  # не был продлен (касается рекурентных платежей)
    CANCELED: str = "CANCELED"  # был отменен
    EXPIRED: str = "EXPIRED"  # закончился срок действия заказа


class OrderYapayStatus(str, Enum):
    PENDING = "PENDING"  # ожидает оплаты
    FAILED = "FAILED"  # отменый платеж
    CAPTURED = "CAPTURED"  # оплачен
    REFUND = "REFUND"  # полный возврат
    RALLBACK = "success"  # отмененный заказ


class OrderUkassaStatus(str, Enum):
    PENDING = "pending"  # ожидает оплаты
    SUCCEEDED = "succeeded"  # оплачен
    RALLBACK = "canceled"  # отмененный заказ


class OrderEventTypeEnum(str, Enum):
    CREATED: str = "CREATED"
    LINK_CREATED: str = "LINK_CREATED"
    ACTIVATED: str = "ACTIVATED"
    EXTENDED: str = "EXTENDED"
    NOTEXTENDED: str = "NOTEXTENDED"
    PAYMENT_CREATED: str = "PAYMENT_CREATED"
    PAYMENT_FAILED: str = "PAYMENT_FAILED"
    EXPIRED: str = "EXPIRED"
    CANCELED: str = "CANCELED"


# === Params ===


class CreateOrderParams(CustomBaseModel):
    plan_id: UUID
    provider: Optional[OrderProviderEnum] = None


# === Schemas ===


class OrderSchema(CustomBaseModel):
    order_id: UUID
    plan_id: UUID
    user_id: UUID
    provider: Optional[OrderProviderEnum] = None
    payment_link: str = ""
    status: OrderStatusEnum = OrderStatusEnum.NEW
    created: datetime
    updated: datetime
    expired: Optional[Union[datetime, BinaryExpression]] = None


class CreateOrderSchema(CreateOrderParams):
    user_id: UUID
    status: OrderStatusEnum = OrderStatusEnum.NEW
    expired: Optional[Union[datetime, BinaryExpression]] = None


class UpdateOrderSchema(CustomBaseModel):
    payment_link: Optional[str] = None
    status: Optional[OrderStatusEnum] = None


class UpdateOrderSchemaAfterWebhook(CustomBaseModel):
    updated: datetime
    status: Optional[OrderStatusEnum] = None


class OrderEventSchema(CustomBaseModel):
    event_id: UUID
    order_id: UUID
    event_type: OrderEventTypeEnum = OrderEventTypeEnum.CREATED
    description: str
    data: dict[Any, Any]
    created: datetime


class CreateOrderEventSchema(CustomBaseModel):
    order_id: UUID
    event_type: OrderEventTypeEnum = OrderEventTypeEnum.CREATED
    description: str = ""
    data: dict[Any, Any] = {}


class PaymentSchema(CustomBaseModel):
    payment_id: UUID
    order_id: UUID
    data: dict[Any, Any]
    created: datetime


class RefundSchema(CustomBaseModel):
    refund_id: UUID
    order_id: UUID
    data: dict[Any, Any]
    created: datetime


# === Responses ===


class OrderListResponse(PaginatedResponse):
    status: Optional[OrderEventTypeEnum] = None
    results: list[OrderSchema]


class OrderEventListResponse(PaginatedResponse):
    results: list[OrderEventSchema]


class PaymentListResponse(PaginatedResponse):
    results: list[PaymentSchema]


class RefundListResponse(PaginatedResponse):
    results: list[RefundSchema]
