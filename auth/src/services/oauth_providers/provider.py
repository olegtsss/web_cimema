from abc import ABC, abstractmethod
import random
import string
from uuid import UUID
from typing import Optional

from fastapi import HTTPException, status

from models.entity import User
from schemas.entity import OAuthAccountCreate, OAuthAccountUpdate, UserCreate
from services.user import UserService


def generate_user_password(length: int = 20) -> str:
    """Ф-ия генерации пароля пользователя."""
    chars = string.ascii_letters + string.digits + "!@#$%^&*()"
    return "".join(random.choices(chars, k=length))


class OauthProvider(ABC):
    NAME = "NOTIMPLEMENTED"
    OAUTH_HOST = "NOTIMPLEMENTED"

    def __init__(self, user_service: UserService) -> None:
        self.user_service = user_service

    @abstractmethod
    def get_redirect_url(self) -> str:
        """Метод получения oauth redirect url."""
        raise NotImplementedError()

    @abstractmethod
    async def get_oauth_account(self) -> Optional[OAuthAccountCreate]:
        """Метод получения oauth аккаунта пользователя.

        Возвращает модель создания oauth аккаунта. В случае ошибки
        возвращает None.
        """
        raise NotImplementedError()

    @abstractmethod
    async def process_callback(self, *args, **kwargs) -> tuple[str, str]:
        """Метод обработки колбека.

        Возвращает кортеж access и refresh токенов.
        """
        oauth_create_model = await self.get_oauth_account(*args, **kwargs)
        if oauth_create_model is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get user oauth account",
            )

        user: User = await self.user_service.dbm.get_user_by_email(
            oauth_create_model.account_email
        )
        if user is None:
            user: User = await self.user_service.dbm.create_user(
                UserCreate(
                    email=oauth_create_model.account_email,
                    password=generate_user_password(),
                ),
            )

        oauth_create_model.user_id = user.id

        oauth_account = await self.user_service.dbm.update_oauth_account(
            oauth_create_model.user_id,
            oauth_create_model.oauth_name,
            OAuthAccountUpdate(**oauth_create_model.model_dump()),
        )
        if oauth_account is None:
            await self.user_service.dbm.create_oauth_account(
                oauth_create_model
            )

        return await self.user_service.create_tokens(user)

    @abstractmethod
    async def unlink_oauth_account(
        self, user_id: str | UUID, oauth_name: str
    ) -> None:
        """Метод отвязки oauth профиля пользователя.

        Обязательные параметры:
        - `user_id` - id пользователя
        - `oauth_name` - название oauth провайдера
        """
        await self.user_service.get_user(user_id)

        oauth_account = await self.user_service.dbm.get_oauth_account(
            user_id, oauth_name
        )
        if oauth_account is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Oauth account not found",
            )

        return await self.user_service.dbm.delete_oauth_account(
            user_id, oauth_name
        )
