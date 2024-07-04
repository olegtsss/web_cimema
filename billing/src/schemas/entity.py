from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class CustomBaseModel(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        use_enum_values=True,
        from_attributes=True,
    )


# === Params ===


class PaginationParams(CustomBaseModel):
    limit: int = Field(10, gt=0)
    offset: int = Field(0, ge=0)


class ActiveOnlyParams(CustomBaseModel):
    active_only: bool = True


# === Responses ===


class PaginatedResponse(PaginationParams):
    total: int = 0
    results: list[Any]
