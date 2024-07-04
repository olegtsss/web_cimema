from datetime import datetime
from enum import Enum
from typing import Any, Optional, Union
from uuid import UUID

from sqlalchemy import BinaryExpression
from schemas.entity import ActiveOnlyParams, CustomBaseModel, PaginatedResponse


# === Enums ===


class SubUserRoleEnum(str, Enum):
    OWNER: str = "OWNER"
    MEMBER: str = "MEMBER"


class SubStatusEnum(str, Enum):
    ACTIVE: str = "ACTIVE"
    CANCELED: str = "CANCELED"
    EXPIRED: str = "EXPIRED"


class SubEventTypeEnum(str, Enum):
    CREATED: str = "CREATED"
    CANCELED: str = "CANCELED"
    EXPIRED: str = "EXPIRED"


# === Schemas ===


class SubSchema(CustomBaseModel):
    sub_id: UUID
    order_id: UUID
    plan_id: UUID
    user_id: UUID
    user_role: SubUserRoleEnum = SubUserRoleEnum.OWNER
    status: SubStatusEnum = SubStatusEnum.ACTIVE
    created: datetime
    updated: datetime
    expired: Optional[Union[datetime, BinaryExpression]] = None


class CreateSubSchema(CustomBaseModel):
    order_id: UUID
    plan_id: UUID
    user_id: UUID
    user_role: SubUserRoleEnum = SubUserRoleEnum.OWNER
    status: SubStatusEnum = SubStatusEnum.ACTIVE
    expired: Optional[Union[datetime, BinaryExpression]] = None


class UpdateSubSchema(CustomBaseModel):
    status: Optional[SubStatusEnum] = None


class SubEventSchema(CustomBaseModel):
    event_id: UUID
    sub_id: UUID
    event_type: SubEventTypeEnum = SubEventTypeEnum.CREATED
    description: str
    data: dict[Any, Any]
    created: datetime


class CreateSubEventSchema(CustomBaseModel):
    sub_id: UUID
    event_type: SubEventTypeEnum = SubEventTypeEnum.CREATED
    description: str = ""
    data: dict[Any, Any] = {}


# === Responses ===


class SubListResponse(PaginatedResponse, ActiveOnlyParams):
    results: list[SubSchema]


class SubEventListResponse(PaginatedResponse):
    results: list[SubEventSchema]
