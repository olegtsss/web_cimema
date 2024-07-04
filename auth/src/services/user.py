from datetime import datetime, timedelta, timezone
from functools import lru_cache
from typing import Optional
import uuid

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from user_agents import parse

from core.config import (
    PRIVATE_KEY,
    PUBLIC_KEY,
    REDIS_REFRESH_TOKEN_PATTERN,
    settings,
)
from models.entity import User, Visit
from schemas.entity import UserCreate, UserUpdate, VisitCreate, pwd_context
from storages.postgres import DatabaseManager, get_dbm
from storages.redis_storage import Redis, get_redis


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
)


@lru_cache
def get_user_service(
    rds: Redis = Depends(get_redis),
    dbm: DatabaseManager = Depends(get_dbm),
) -> "UserService":
    return UserService(rds, dbm)


async def _get_current_user(
    access_token: str = Depends(oauth2_scheme),
    user_service: "UserService" = Depends(get_user_service),
) -> User:
    payload = await user_service.validate_access_token(access_token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    username = payload.get("sub")
    user = await user_service.dbm.get_user(username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(_get_current_user),
) -> User:
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )
    return current_user


async def get_current_active_superuser(
    current_active_user: User = Depends(get_current_active_user),
) -> User:
    if not current_active_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied",
        )
    return current_active_user


class UserService:
    def __init__(self, rds: Redis, dbm: DatabaseManager) -> None:
        self.rds = rds
        self.dbm = dbm

    @staticmethod
    def verify_password(plain_password, hashed_password):
        """Метод верификации пароля."""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def create_access_token(
        user: User,
        refresh_jti: str,
        algorithm: str = "RS256",
        secret: str = PRIVATE_KEY,
        audience: list[str] = settings.token_audience,
        lifetime: timedelta = settings.access_lifetime,
    ) -> str:
        """Метод генерации access токена.

        Обязательные параметры:
        - `user` - модель пользователя
        - `refresh_jti` - jti связанного refresh токена

        Опциональные параметры:
        - `algorithm` - алгоритм, RS256 по умолчанию
        - `secret` - секрет, PUBLIC_KEY по умолчанию
        - `audience` - аудитория токена, settings.token_audience по умолчанию
        - `lifetime` - время жизни токена, settings.access_lifetime по умолчанию

        Возвращает access токен.
        """
        token_jti = str(uuid.uuid4())
        iat = datetime.now(tz=timezone.utc)
        exp = iat + lifetime
        payload = {
            "jti": token_jti,
            "iss": settings.app_name,
            "sub": str(user.id),
            "aud": audience,
            "iat": iat,
            "exp": exp,
            "token_type": "access",
            "refresh_jti": str(refresh_jti),
            "roles": [str(role.name) for role in user.roles],
        }

        return jwt.encode(payload, secret, algorithm=algorithm)

    @staticmethod
    def create_refresh_token(
        user: User,
        algorithm: str = "HS256",
        secret: str = settings.secret,
        audience: list[str] = settings.token_audience,
        lifetime: timedelta = settings.refresh_lifetime,
    ) -> str:
        """Метод генерации refresh токена.

        Обязательные параметры:
        - `user` - модель пользователя

        Опциональные параметры:
        - `algorithm` - алгоритм, HS256 по умолчанию
        - `secret` - секрет, settings.secret по умолчанию
        - `audience` - аудитория токена, settings.token_audience по умолчанию
        - `lifetime` - время жизни токена, settings.refresh_lifetime по умолчанию

        Возвращает refresh токен.
        """
        token_jti = str(uuid.uuid4())
        iat = datetime.now(tz=timezone.utc)
        exp = iat + lifetime
        payload = {
            "jti": token_jti,
            "iss": settings.app_name,
            "sub": str(user.id),
            "aud": audience,
            "iat": iat,
            "exp": exp,
            "token_type": "refresh",
        }

        return jwt.encode(payload, secret, algorithm=algorithm)

    @staticmethod
    def _verify_access_token(
        access_token: str,
        algorithm: str = "RS256",
        secret: str = PUBLIC_KEY,
    ) -> dict:
        """Метод верификации access токена.

        Обязательные параметры:
        - `token` - access токен

        Опциональные параметры:
        - `algorithm` - алгоритм, RS256 по умолчанию
        - `secret` - секрет, PUBLIC_KEY по умолчанию

        Возвращает payload, если токен валидный, иначе None.
        """
        try:
            return jwt.decode(
                access_token,
                secret,
                issuer=settings.app_name,
                audience=settings.app_name,
                algorithms=[algorithm],
            )
        except Exception:
            return None

    @staticmethod
    def _verify_refresh_token(
        refresh_token: str,
        algorithm: str = "HS256",
        secret: str = settings.secret,
    ) -> dict:
        """Метод верификации refresh токена.

        Обязательные параметры:
        - `token` - refresh токен

        Опциональные параметры:
        - `algorithm` - алгоритм, HS256 по умолчанию
        - `secret` - секрет, settings.secret по умолчанию

        Возвращает payload, если токен валидный, иначе None.
        """
        try:
            return jwt.decode(
                refresh_token,
                secret,
                issuer=settings.app_name,
                audience=settings.app_name,
                algorithms=[algorithm],
            )
        except Exception:
            return None

    async def _refresh_token_is_valid(self, user_id: str, refresh_jti: str):
        """Метод проверки валидности refresh токена.

        Обязательные параметры:
        - `user_id` - id пользователя
        - `refresh_jti` - jti refresh токена

        Возвращает True, если токен валиден, иначе False.
        """
        refresh_redis_key = REDIS_REFRESH_TOKEN_PATTERN.format(
            prefix=settings.app_name, user_uid=user_id, refresh_jti=refresh_jti
        )
        if await self.rds.get(refresh_redis_key):
            return True
        return False

    async def validate_access_token(self, access_token: str):
        """Метод чтения access токена.

        Обязательные параметры:
        - `token` - access токен

        Возвращает payload, если токен валиден, иначе None.
        """
        payload = self._verify_access_token(access_token)
        if payload is None:
            return None

        token_type = payload.get("token_type")
        if token_type != "access":
            return None

        user_id = payload.get("sub")
        refresh_jti = payload.get("refresh_jti")
        if not await self._refresh_token_is_valid(user_id, refresh_jti):
            return None

        return payload

    async def validate_refresh_token(self, refresh_token: str):
        """Метод чтения refresh токена.

        Обязательные параметры:
        - `token` - refresh токен

        Возвращает payload, если токен валиден, иначе None.
        """
        payload = self._verify_refresh_token(refresh_token)
        if payload is None:
            return None

        token_type = payload.get("token_type")
        if token_type != "refresh":
            return None

        user_uid = payload.get("sub")
        refresh_jti = payload.get("jti")
        if not await self._refresh_token_is_valid(user_uid, refresh_jti):
            return None

        return payload

    async def create_tokens(self, user: User) -> tuple[str, str]:
        """Метод генерации access и refresh токенов.

        Обязательные параметры:
        - `user` - модель пользователя

        Возвращает кортеж access и refresh токенов.
        """
        refresh_token = self.create_refresh_token(user)

        refresh_payload = jwt.decode(
            refresh_token,
            key=settings.secret,
            options={"verify_signature": False},
            audience=settings.app_name,
        )
        refresh_jti = refresh_payload.get("jti")
        refresh_exp = refresh_payload.get("exp")

        refresh_redis_key = REDIS_REFRESH_TOKEN_PATTERN.format(
            prefix=settings.app_name,
            user_uid=str(user.id),
            refresh_jti=refresh_jti,
        )
        refresh_redis_value = 0
        refresh_redis_exp = refresh_exp - int(
            datetime.now(tz=timezone.utc).timestamp()
        )
        await self.rds.set(
            refresh_redis_key, refresh_redis_value, refresh_redis_exp
        )

        return self.create_access_token(user, refresh_jti), refresh_token

    async def _refresh_access_token(self, refresh_payload: dict):
        """Метод обновления access токена.

        Обязательные параметры:
        - `refresh_payload` - payload refresh токена

        Возвращает новый access токен.
        """
        refresh_jti = refresh_payload.get("jti")
        user_id = refresh_payload.get("sub")
        user = await self.dbm.get_user(user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with user_id '{user_id}' not found",
            )

        return self.create_access_token(user, refresh_jti)

    async def authenticate(
        self, username: str, password: str
    ) -> Optional[User]:
        """Метод аутентификации пользователя.

        Обязательные параметры:
        - `username` - имя пользователя (email)
        - `password` - пароль пользователя (password)

        Возвращает модель User, если пользователь был найден, иначе None.
        """
        user = await self.dbm.get_user_by_email(username)

        if user is None:
            return None
        if not self.verify_password(password, user.hashed_password):
            return None

        return user

    async def login(
        self, request: Request, username: str, password: str
    ) -> tuple[str, str]:
        """Метод логина пользователя.

        Обязательные параметры:
        - `request` - запрос пользователя
        - `username` - имя пользователя (email)
        - `password` - пароль пользователя (password)

        Возвращает кортеж access и refresh токенов.
        """
        user = await self.authenticate(username, password)
        if user is None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )

        if settings.user_requires_verification and not user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User email not verified",
            )

        user_agent = parse(request.headers.get("User-Agent"))
        device_type = "mobile" if user_agent.is_mobile else "web"
        await self.dbm.create_user_visit(
            VisitCreate(
                user_id=user.id,
                user_agent=user_agent.ua_string,
                device_type=device_type,
            )
        )

        return await self.create_tokens(user)

    async def logout(self, access_token: str) -> None:
        """Метод логаута пользователя.

        Обязательные параметры:
        - `access_token` - access токен
        """
        access_payload = await self.validate_access_token(access_token)
        if access_payload is None:
            return credentials_exception

        user_id = access_payload.get("sub")
        refresh_jti = access_payload.get("refresh_jti")
        refresh_redis_key = REDIS_REFRESH_TOKEN_PATTERN.format(
            prefix=settings.app_name, user_uid=user_id, refresh_jti=refresh_jti
        )
        await self.rds.delete(refresh_redis_key)

    async def refresh(self, refresh_token: str) -> str:
        """Метод обновления access токена пользователя.

        Обязательные параметры:
        - `refresh_token` - refresh токен

        Возвращает новый access токен.
        """
        refresh_payload = await self.validate_refresh_token(refresh_token)
        if refresh_payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )

        return await self._refresh_access_token(refresh_payload)

    async def logout_all(self, access_token: str) -> None:
        """Метод полного логаута пользователя.

        Обязательные параметры:
        - `access_token` - access токен
        """
        access_payload = await self.validate_access_token(access_token)
        if access_payload is None:
            return credentials_exception

        user_id = access_payload.get("sub")
        refresh_redis_pattern = REDIS_REFRESH_TOKEN_PATTERN.format(
            prefix=settings.app_name, user_uid=user_id, refresh_jti="*"
        )
        async for key in self.rds.scan_iter(refresh_redis_pattern):
            await self.rds.delete(key)

    async def create_user(self, params: UserCreate, safe: bool = True) -> User:
        """Метод создания пользователя.

        Обязательные параметры:
        - `params` - модель параметров создания пользователя

        Опциональные параметры:
        - `safe` - создание пользователя без передачи `is_superuser` и
        `is_verified`, по умолчанию True

        Возвращает модель пользователя User.
        """
        if await self.dbm.get_user_by_email(params.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User with email '{params.email}' already exists",
            )

        if safe:
            params.is_superuser = False
            params.is_verified = False

        return await self.dbm.create_user(params)

    async def get_user(self, user_id: str | uuid.UUID) -> Optional[User]:
        """Метод получения пользователя.

        Обязательные параметры:
        - `user_id` - id пользователя

        Возвращает модель пользователя User.
        """
        user = await self.dbm.get_user(user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        return user

    async def update_user(
        self, user_id: str | uuid.UUID, params: UserUpdate, safe: bool = True
    ) -> Optional[User]:
        """Метод создания пользователя.

        Обязательные параметры:
        - `user_id` - id пользователя
        - `params` - модель параметров обновления пользователя

        Опциональные параметры:
        - `safe` - обновление пользователя без передачи `is_superuser` и
        `is_verified`, по умолчанию True

        Возвращает модель пользователя User.
        """
        await self.get_user(user_id)

        if safe:
            params.is_superuser = False
            params.is_verified = False

        if await self.dbm.get_user_by_email(params.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Email '{params.email}' already exists",
            )

        return await self.dbm.update_user(user_id, params)

    async def delete_user(self, user_id: str | uuid.UUID) -> None:
        """Метод удаления пользователя.

        Обязательные параметры:
        - `user_id` - id пользователя
        """
        await self.get_user(user_id)

        await self.dbm.delete_user(user_id)

    async def get_user_visits(
        self, user_id: str | uuid.UUID, limit: int = 10, offset: int = 0
    ) -> tuple[int, list[Visit]]:
        """Метод получения визитов пользователя.

        Обязательные параметры:
        - `user_id` - id пользователя

        Опциональные параметры:
        - `session` - отображение сессии бд
        - `limit` - кол-во визитов (пагинация)
        - `offset` - смещение визитов (пагинация)

        Возвращает кортеж общего числа и список визитов пользователя.
        """
        return await self.dbm.get_user_visits(user_id, limit, offset)
