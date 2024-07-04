from contextlib import asynccontextmanager
from functools import lru_cache, wraps
from typing import AsyncGenerator, Callable, Optional
from uuid import UUID

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from core.config import settings
from models.entity import Base, OAuthAccount, Role, User, Visit
from schemas.entity import (
    OAuthAccountCreate,
    OAuthAccountUpdate,
    RoleCreate,
    RoleUpdate,
    UserCreate,
    UserUpdate,
    VisitCreate,
)

engine = create_async_engine(settings.pg_dsn)
async_session = async_sessionmaker(engine, expire_on_commit=False)


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session


@lru_cache
def get_dbm() -> "DatabaseManager":
    return DatabaseManager()


class DatabaseManager:
    @staticmethod
    def session_handler(method: Callable) -> Callable:
        @wraps(method)
        async def wrapper(self: "DatabaseManager", *args, **kwargs):
            if kwargs.get("session"):
                return await method(self, *args, **kwargs)

            async with get_session() as session:
                kwargs["session"] = session
                return await method(self, *args, **kwargs)

        return wrapper

    # === Users ===

    @session_handler
    async def get_user(
        self, user_id: str | UUID, *, session: AsyncSession
    ) -> Optional[User]:
        """Метод получения пользователя.

        Обязательные параметры:
        - `user_id` - id пользователя

        Опциональные параметры:
        - `session` - отображение сессии бд

        Возвращает модель User, если пользователь был найден, иначе None.
        """
        user = await session.execute(select(User).where(User.id == user_id))

        return user.unique().scalar_one_or_none()

    @session_handler
    async def get_user_by_email(
        self, email: str, *, session: AsyncSession
    ) -> Optional[User]:
        """Метод получения пользователя по email.

        Обязательные параметры:
        - `email` - email пользователя

        Опциональные параметры:
        - `session` - отображение сессии бд

        Возвращает модель User, если пользователь был найден, иначе None.
        """
        user = await session.execute(select(User).where(User.email == email))

        return user.unique().scalar_one_or_none()

    @session_handler
    async def create_user(
        self,
        user_model: UserCreate,
        *,
        session: AsyncSession,
    ) -> User:
        """Метод создания пользователя.

        Обязательные параметры:
        - `user_model` - модель создания пользователя

        Опциональные параметры:
        - `session` - отображение сессии бд

        Возвращает модель User.
        """
        new_user = User(**user_model.model_dump())

        session.add(new_user)

        await session.commit()
        await session.refresh(new_user)

        return new_user

    @session_handler
    async def update_user(
        self, user_id: str | UUID, params: UserUpdate, *, session: AsyncSession
    ) -> Optional[User]:
        """Метод обновления пользователя.

        Обязательные параметры:
        - `user_id` - id пользователя
        - `params` - модель параметров обновления пользователя

        Опциональные параметры:
        - `session` - отображение сессии бд

        Возвращает модель User, если пользователь был найден, иначе None.
        """
        user = await self.get_user(user_id, session=session)
        if user is None:
            return None

        for key, value in params.model_dump(exclude_unset=True).items():
            if key == "roles":
                roles = await session.execute(
                    select(Role).filter(Role.name.in_(value))
                )
                value = roles.scalars().all()

            if hasattr(user, key):
                setattr(user, key, value)

        await session.commit()

        return user

    @session_handler
    async def delete_user(
        self, user_id: str | UUID, *, session: AsyncSession
    ) -> None:
        """Метод удаления пользователя.

        Обязательные параметры:
        - `user_id` - id пользователя

        Опциональные параметры:
        - `session` - отображение сессии бд
        """
        user = await self.get_user(user_id, session=session)
        if user is None:
            return None

        await session.delete(user)

        await session.commit()

    # === Visits ===

    @session_handler
    async def get_user_visits(
        self,
        user_id: str | UUID,
        limit: int = 10,
        offset: int = 0,
        *,
        session: AsyncSession,
    ) -> tuple[int, list[Visit]]:
        """Метод получения визитов пользователя.

        Обязательные параметры:
        - `user_id` - id пользователя

        Опциональные параметры:
        - `limit` - кол-во визитов (пагинация)
        - `offset` - смещение визитов (пагинация)
        - `session` - отображение сессии бд

        Возвращает кортеж общего числа и список визитов пользователя.
        """
        total_user_visits = await session.execute(
            (
                select(func.count())
                .select_from(Visit)
                .where(Visit.user_id == user_id)
            )
        )

        user_visits = await session.execute(
            (
                select(Visit)
                .where(Visit.user_id == user_id)
                .order_by(desc(Visit.created))
                .limit(limit)
                .offset(offset)
            )
        )

        return total_user_visits.scalar(), user_visits.scalars()

    @session_handler
    async def create_user_visit(
        self, params: VisitCreate, *, session: AsyncSession
    ) -> Visit:
        """Метод создания визита пользователя.

        Обязательные параметры:
        - `params` - модель параметров создания визита пользователя

        Опциональные параметры:
        - `session` - отображение сессии бд

        Возвращает модель Visit.
        """
        new_user_visit = Visit(**params.model_dump())

        session.add(new_user_visit)

        await session.commit()

        return new_user_visit

    # === Roles ===

    @session_handler
    async def get_roles(self, *, session: AsyncSession) -> list[Role]:
        """Метод получения ролей.

        Опциональные параметры:
        - `session` - отображение сессии бд

        Возвращает список существующих ролей Role (может быть пустым).
        """
        roles = await session.execute(select(Role))

        return roles.scalars()

    @session_handler
    async def get_role(
        self,
        name: str,
        *,
        session: AsyncSession,
    ) -> Optional[Role]:
        """Метод получения роли.

        Обязательные параметры:
        - `name` - название роли

        Опциональные параметры:
        - `session` - отображение сессии бд

        Возвращает модель Role.
        """
        role = await session.execute(select(Role).where(Role.name == name))

        return role.scalar_one_or_none()

    @session_handler
    async def create_role(
        self, params: RoleCreate, *, session: AsyncSession
    ) -> Role:
        """Метод создания роли.

        Обязательные параметры:
        - `params` - модель параметров создания роли

        Опциональные параметры:
        - `session` - отображение сессии бд

        Возвращает модель Role.
        """
        role = Role(**params.model_dump())

        session.add(role)

        await session.commit()

        return role

    @session_handler
    async def update_role(
        self, name: str, params: RoleUpdate, *, session: AsyncSession
    ) -> Optional[Role]:
        """Метод обновления роли.

        Обязательные параметры:
        - `name` - название роли
        - `params` - модель параметров обновления роли

        Опциональные параметры:
        - `session` - отображение сессии бд

        Возвращает модель Role, если роль была найдена, иначе None.
        """
        role = await self.get_role(name, session=session)
        if not role:
            return None

        for key, value in params.model_dump(exclude_unset=True).items():
            if hasattr(role, key):
                setattr(role, key, value)

        await session.commit()

        return role

    @session_handler
    async def delete_role(self, name: str, *, session: AsyncSession) -> None:
        """Метод удаления роли.

        Обязательные параметры:
        - `name` - название роли

        Опциональные параметры:
        - `session` - отображение сессии бд
        """
        role = await self.get_role(name, session=session)
        if role is None:
            return None

        await session.delete(role)

        await session.commit()

    # === Oauth ===

    @session_handler
    async def get_oauth_account(
        self,
        user_id: str | UUID,
        oauth_name: str,
        *,
        session: AsyncSession,
    ) -> Optional[OAuthAccount]:
        """Метод получения oauth аккаунта пользователя.

        Обязательные параметры:
        - `user_id` - id пользователя
        - `oauth_name` - название oauth провайдера

        Опциональные параметры:
        - `session` - отображение сессии бд

        Возвращает модель OAuthAccount, если аккаунт был найден, иначе None.
        """
        oauth_account = await session.execute(
            select(OAuthAccount)
            .where(OAuthAccount.user_id == user_id)
            .where(OAuthAccount.oauth_name == oauth_name)
        )

        return oauth_account.scalar_one_or_none()

    @session_handler
    async def create_oauth_account(
        self, oauth_model: OAuthAccountCreate, *, session: AsyncSession
    ) -> OAuthAccount:
        """Метод создания oauth аккаунта пользователя.

        Обязательные параметры:
        - `oauth_model` - модель создания oauth аккаунта пользователя

        Опциональные параметры:
        - `session` - отображение сессии бд

        Возвращает новую или существующую модель OAuthAccount.
        """
        oauth_account = await self.get_oauth_account(
            oauth_model.user_id, oauth_model.oauth_name, session=session
        )
        if oauth_account is not None:
            return oauth_account

        oauth_account = OAuthAccount(**oauth_model.model_dump())

        session.add(oauth_account)

        await session.commit()

        return oauth_account

    @session_handler
    async def update_oauth_account(
        self,
        user_id: str | UUID,
        oauth_name: str,
        oauth_model: OAuthAccountUpdate,
        *,
        session: AsyncSession,
    ) -> Optional[OAuthAccount]:
        """Метод обновления oauth аккаунта пользователя.

        Обязательные параметры:
        - `user_id` - id пользователя
        - `oauth_name` - название oauth провайдера
        - `oauth_model` - модель обновления oauth аккаунта пользователя

        Опциональные параметры:
        - `session` - отображение сессии бд

        Возвращает обновленную модель OAuthAccount, если аккаунт был найден,
        иначе None.
        """
        oauth_account = await self.get_oauth_account(
            user_id, oauth_name, session=session
        )
        if oauth_account is None:
            return None

        for key, value in oauth_model.model_dump(exclude_unset=True).items():
            if hasattr(oauth_account, key):
                setattr(oauth_account, key, value)

        await session.commit()

        return oauth_account

    @session_handler
    async def delete_oauth_account(
        self, user_id: str | UUID, oauth_name: str, *, session: AsyncSession
    ) -> None:
        """Метод удаления oauth аккаунта пользователя.

        Обязательные параметры:
        - `user_id` - id пользователя
        - `oauth_name` - название oauth провайдера

        Опциональные параметры:
        - `session` - отображение сессии бд
        """
        oauth_account = await self.get_oauth_account(
            user_id, oauth_name, session=session
        )
        if oauth_account is not None:
            await session.delete(oauth_account)

            await session.commit()
