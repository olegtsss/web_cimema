import uuid

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, declarative_base, relationship
from sqlalchemy.sql import func

Base: DeclarativeBase = declarative_base()


def create_partition(target, connection, **kwargs) -> None:
    connection.execute(
        text(
            """CREATE TABLE IF NOT EXISTS "visits_smart" PARTITION OF "visits" FOR VALUES IN ('smart')"""
        )
    )
    connection.execute(
        text(
            """CREATE TABLE IF NOT EXISTS "visits_mobile" PARTITION OF "visits" FOR VALUES IN ('mobile')"""
        )
    )
    connection.execute(
        text(
            """CREATE TABLE IF NOT EXISTS "visits_web" PARTITION OF "visits" FOR VALUES IN ('web')"""
        )
    )


class User(Base):
    __tablename__ = "users"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)

    roles = relationship(
        "Role", secondary="user_role", back_populates="users", lazy="joined"
    )
    visits = relationship("Visit", back_populates="user")
    oauth_accounts = relationship("OAuthAccount", back_populates="user")


class Role(Base):
    __tablename__ = "roles"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True, index=True, nullable=False)

    users = relationship("User", secondary="user_role", back_populates="roles")


class UserRole(Base):
    __tablename__ = "user_role"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID, ForeignKey("users.id", ondelete="cascade"))
    role_id = Column(UUID, ForeignKey("roles.id", ondelete="cascade"))


class Visit(Base):
    __tablename__ = "visits"
    __table_args__ = (
        UniqueConstraint("id", "device_type"),
        {
            "postgresql_partition_by": "LIST (device_type)",
            "listeners": [("after_create", create_partition)],
        },
    )

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID, ForeignKey("users.id", ondelete="cascade"))
    user_agent = Column(String, nullable=False)
    device_type = Column(String, primary_key=True)
    created = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user = relationship("User", back_populates="visits")


class OAuthAccount(Base):
    __tablename__ = "oauth_accounts"
    __table_args__ = (
        UniqueConstraint("user_id", "oauth_name"),
    )

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID, ForeignKey("users.id", ondelete="cascade"))
    oauth_name = Column(String, index=True, nullable=False)
    access_token = Column(String, nullable=False)
    expires_at = Column(Integer)
    refresh_token = Column(String)
    account_id = Column(String, index=True, nullable=False)
    account_email = Column(String, nullable=False)

    user = relationship("User", back_populates="oauth_accounts")
