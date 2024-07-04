from datetime import datetime
from typing import Optional
from uuid import UUID

from passlib.context import CryptContext
from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    HttpUrl,
    computed_field,
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class CustomBaseModel(BaseModel):
    model_config = ConfigDict(
        use_enum_values=True,
        from_attributes=True,
    )


# === Pagination ===


class Pagination(CustomBaseModel):
    offset: int = Field(0, ge=0)
    limit: int = Field(10, gt=0)


# === Auth ===


class AccessRead(CustomBaseModel):
    access_token: str


class RefreshRead(CustomBaseModel):
    refresh_token: str


class AccessRefreshRead(RefreshRead, AccessRead):
    ...


# === Roles ===


class RoleRead(CustomBaseModel):
    id: UUID
    name: str


class RoleCreate(CustomBaseModel):
    name: str


class RoleUpdate(CustomBaseModel):
    name: str


# === Users ===


class UserRead(CustomBaseModel):
    id: UUID
    email: EmailStr
    is_active: bool = True
    is_superuser: bool = False
    is_verified: bool = False
    roles: list[RoleRead]


class UserCreate(CustomBaseModel):
    email: EmailStr
    password: str = Field(..., exclude=True)
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False
    is_verified: Optional[bool] = False

    @computed_field
    @property
    def hashed_password(self) -> str:
        return pwd_context.hash(self.password)


class UserUpdate(CustomBaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
    is_verified: Optional[bool] = None


class SuperuserUpdate(UserUpdate):
    roles: Optional[list[str]] = None


# === Visits ===


class VisitRead(CustomBaseModel):
    user_agent: str
    device_type: str
    created: datetime


class VisitCreate(CustomBaseModel):
    user_id: str | UUID
    user_agent: str
    device_type: str


class VisitListRead(Pagination):
    total_visits: int
    visits: list[VisitRead]


# === OAuth ===


class OAuthAccountCreate(CustomBaseModel):
    user_id: str | UUID
    oauth_name: str
    access_token: str
    expires_at: int | None = None
    refresh_token: str | None = None
    account_id: str
    account_email: EmailStr


class OAuthAccountUpdate(CustomBaseModel):
    access_token: str | None = None
    expires_at: int | None = None
    refresh_token: str | None = None
    account_id: str | None = None
    account_email: EmailStr | None = None


class RedirectUrlRead(CustomBaseModel):
    redirect_url: HttpUrl
