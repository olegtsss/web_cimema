import uuid

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    func,
    String,
    Text,
    Numeric,
    SmallInteger,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(AsyncAttrs, DeclarativeBase):
    pass


class PlanModel(Base):
    __tablename__ = "plans"

    plan_id = Column(UUID, primary_key=True, default=uuid.uuid4)
    title = Column(String(120), unique=True, nullable=False)
    description = Column(String(500), server_default="", nullable=False)
    unit = Column(String(50), nullable=False)
    period = Column(SmallInteger, nullable=False)
    price_per_unit = Column(Numeric(precision=8, scale=2), nullable=False)
    payment_type = Column(String(50), nullable=False)
    is_multiple = Column(Boolean, server_default="false", nullable=False)
    is_active = Column(Boolean, server_default="true", nullable=False)
    created = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        CheckConstraint("period >= 0"),
        CheckConstraint("price_per_unit >= 0"),
    )

    orders = relationship("OrderModel", back_populates="plan")
    subs = relationship("SubModel", back_populates="plan")


class OrderModel(Base):
    __tablename__ = "orders"

    order_id = Column(UUID, primary_key=True, default=uuid.uuid4)
    plan_id = Column(ForeignKey("plans.plan_id", ondelete="RESTRICT"), nullable=False)
    user_id = Column(UUID, nullable=False)
    provider = Column(String(50))
    payment_link = Column(String(2048), server_default="", nullable=False)
    status = Column(String(50), server_default="NEW", nullable=False)
    created = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expired = Column(DateTime(timezone=True))

    plan = relationship("PlanModel", back_populates="orders")
    sub = relationship("SubModel", back_populates="order")
    payments = relationship("PaymentModel", back_populates="order")
    refunds = relationship("RefundModel", back_populates="order")
    events = relationship("OrderEventModel", back_populates="order")


class OrderEventModel(Base):
    __tablename__ = "order_events"

    event_id = Column(UUID, primary_key=True, default=uuid.uuid4)
    order_id = Column(
        ForeignKey("orders.order_id", ondelete="RESTRICT"), nullable=False
    )
    event_type = Column(String(50), server_default="", nullable=False)
    description = Column(Text, server_default="", nullable=False)
    data = Column(JSONB, server_default="{}", nullable=False)
    created = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    order = relationship("OrderModel", back_populates="events")


class PaymentModel(Base):
    __tablename__ = "payments"

    payment_id = Column(UUID, primary_key=True, default=uuid.uuid4)
    order_id = Column(
        ForeignKey("orders.order_id", ondelete="RESTRICT"), nullable=False
    )
    data = Column(JSONB, server_default="{}", nullable=False)
    created = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    order = relationship("OrderModel", back_populates="payments")


class RefundModel(Base):
    __tablename__ = "refunds"

    refund_id = Column(UUID, primary_key=True, default=uuid.uuid4)
    order_id = Column(
        ForeignKey("orders.order_id", ondelete="RESTRICT"), nullable=False
    )
    data = Column(JSONB, server_default="{}", nullable=False)
    created = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    order = relationship("OrderModel", back_populates="refunds")


class SubModel(Base):
    __tablename__ = "subs"

    sub_id = Column(UUID, primary_key=True, default=uuid.uuid4)
    order_id = Column(
        ForeignKey("orders.order_id", ondelete="RESTRICT"),
        unique=True,
        nullable=False,
    )
    plan_id = Column(ForeignKey("plans.plan_id", ondelete="RESTRICT"), nullable=False)
    user_id = Column(UUID, nullable=False)
    user_role = Column(String(50), server_default="OWNER", nullable=False)
    status = Column(String(50), server_default="ACTIVE", nullable=False)
    created = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expired = Column(DateTime(timezone=True))

    order = relationship("OrderModel", uselist=False, back_populates="sub")
    plan = relationship("PlanModel", back_populates="subs")
    events = relationship("SubEventModel", back_populates="sub")


class SubEventModel(Base):
    __tablename__ = "sub_events"

    event_id = Column(UUID, primary_key=True, default=uuid.uuid4)
    sub_id = Column(ForeignKey("subs.sub_id", ondelete="RESTRICT"), nullable=False)
    event_type = Column(String(50), server_default="", nullable=False)
    description = Column(Text, server_default="", nullable=False)
    data = Column(JSONB, server_default="{}", nullable=False)
    created = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    sub = relationship("SubModel", back_populates="events")
