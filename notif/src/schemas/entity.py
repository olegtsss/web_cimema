from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, model_validator


class CustomBaseModel(BaseModel):
    model_config = ConfigDict(
        use_enum_values=True,
        from_attributes=True,
    )


# === Enums ===


class NotificationDeliveryMode(str, Enum):
    INSTANT: str = "INSTANT"
    SCHEDULED: str = "SCHEDULED"


class NotificationChannel(str, Enum):
    EMAIL: str = "EMAIL"
    WS: str = "WS"


class NotificationStatus(str, Enum):
    NEW: str = "NEW"
    SCHEDULED: str = "SCHEDULED"
    SENT: str = "SENT"


# === Create schemas ===


class CreateTemplate(CustomBaseModel):
    title: str
    description: Optional[str] = None
    body: str


class CreateNotification(CustomBaseModel):
    source_id: UUID
    user_id: UUID
    template_id: Optional[UUID] = None
    delivery_mode: NotificationDeliveryMode = NotificationDeliveryMode.SCHEDULED
    channel: NotificationChannel = NotificationChannel.EMAIL

    @model_validator(mode="before")
    @classmethod
    def check_template_email(cls, data):
        template_id = data.get("template_id")
        channel = data.get("channel")
        if channel == NotificationChannel.EMAIL and template_id is None:
            raise ValueError("'template_id' must be specified")
        return data

    @model_validator(mode="after")
    def set_delivery_mode_ws(self):
        if self.channel == NotificationChannel.WS:
            self.delivery_mode = NotificationDeliveryMode.INSTANT
        return self


class CreateNotificationStatus(CustomBaseModel):
    notification_id: UUID
    status: NotificationStatus = NotificationStatus.NEW


# === Responses ===


class Pagination(CustomBaseModel):
    limit: int = 10
    offset: int = 0


class Tag(CustomBaseModel):
    name: str
    description: Optional[str] = None


class TemplateList(CustomBaseModel):
    template_id: UUID
    title: str
    description: Optional[str] = None
    created_at: datetime


class TemplateListResponse(Pagination):
    templates: list[TemplateList]


class Template(TemplateList):
    body: str


class Notification(CustomBaseModel):
    notification_id: UUID
    source_id: UUID
    user_id: UUID
    template_id: Optional[UUID] = None
    delivery_mode: NotificationDeliveryMode = NotificationDeliveryMode.SCHEDULED
    channel: NotificationChannel = NotificationChannel.EMAIL
    created_at: datetime


class NotificationStatusResponse(CustomBaseModel):
    notification_id: UUID
    status: NotificationStatus = NotificationStatus.NEW
    created_at: datetime


class NotificationListResponse(Pagination):
    notifications: list[Notification]
