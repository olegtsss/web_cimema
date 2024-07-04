from datetime import datetime
from typing import Optional
from uuid import UUID

from schemas.entity import CustomBaseModel
from schemas.subs import SubUserRoleEnum


# === Schemas ===


class SubCreationSchema(CustomBaseModel):
    sub_id: UUID
    plan_id: UUID
    user_role: SubUserRoleEnum = SubUserRoleEnum.OWNER
    created: datetime
    expired: Optional[datetime] = None
