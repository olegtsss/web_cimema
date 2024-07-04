import uuid

from sqlalchemy import Column, DateTime, func, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase


class Base(AsyncAttrs, DeclarativeBase): ...


class Template(Base):
    __tablename__ = "templates"

    template_id = Column(UUID, primary_key=True, default=uuid.uuid4)
    title = Column(String(120), unique=True, nullable=False)
    description = Column(String(500))
    body = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Notification(Base):
    __tablename__ = "notifications"

    notification_id = Column(UUID, primary_key=True, default=uuid.uuid4)
    source_id = Column(UUID, nullable=False)
    user_id = Column(UUID, nullable=False)
    template_id = Column(UUID)
    delivery_mode = Column(String(50), nullable=False)
    channel = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class NotificationStatus(Base):
    __tablename__ = "notification_statuses"

    notification_id = Column(UUID, primary_key=True)
    status = Column(String(50), primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
