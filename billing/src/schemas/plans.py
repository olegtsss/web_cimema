from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import Field, model_validator
from typing_extensions import Self

from schemas.entity import ActiveOnlyParams, CustomBaseModel, PaginatedResponse


# === Enums ===


class PlanUnitEnum(str, Enum):
    DAY: str = "DAY"
    MONTH: str = "MONTH"
    YEAR: str = "YEAR"


class PlanPaymentTypeEnum(str, Enum):
    NEVER: str = "NEVER"
    ONCE: str = "ONCE"
    RECURRENT: str = "RECURRENT"


# === Schemas ===


class PlanSchema(CustomBaseModel):
    plan_id: UUID
    title: str = Field(..., max_length=120)
    description: str = Field("", max_length=500)
    unit: PlanUnitEnum
    period: int = Field(..., ge=0, lt=32768)
    price_per_unit: Decimal = Field(..., ge=0, lt=1000000)
    payment_type: PlanPaymentTypeEnum
    is_multiple: bool = False
    is_active: bool = True
    created: datetime
    updated: datetime


class CreatePlanSchema(CustomBaseModel):
    title: str = Field(..., max_length=120)
    description: str = Field("", max_length=500)
    unit: PlanUnitEnum
    period: int = Field(..., ge=0, lt=32768)
    price_per_unit: Decimal = Field(..., ge=0, lt=1000000)
    payment_type: PlanPaymentTypeEnum
    is_multiple: bool = False

    @model_validator(mode="after")
    def check_period(self) -> Self:
        payment_type = self.payment_type
        period = self.period
        if payment_type == PlanPaymentTypeEnum.RECURRENT:
            if period <= 1:
                raise ValueError(
                    "'period' must be greater than 1 if payment type `RECURRENT`"
                )
        return self

    @model_validator(mode="after")
    def check_price_per_unit(self) -> Self:
        payment_type = self.payment_type
        price_per_unit = self.price_per_unit

        if (
            payment_type in [PlanPaymentTypeEnum.ONCE, PlanPaymentTypeEnum.RECURRENT]
            and price_per_unit == 0
        ):
            raise ValueError(
                "'price_per_unit' must be greater than 0 if payment type `ONCE` or `RECURRENT`"
            )

        if payment_type == PlanPaymentTypeEnum.NEVER:
            self.price_per_unit = Decimal("0.00")

        return self


class UpdatePlanSchema(CustomBaseModel):
    is_active: Optional[bool] = None


# === Responses ===


class PlanListResponse(PaginatedResponse, ActiveOnlyParams):
    results: list[PlanSchema]
