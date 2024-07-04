from typing import Optional
from urllib.parse import urlencode
from uuid import UUID

import aiohttp

from core.config import settings
from schemas.entity import OAuthAccountCreate
from services.oauth_providers.provider import OauthProvider
from services.user import UserService


class YandexOauthProvider(OauthProvider):
    NAME = "YANDEX"
    OAUTH_HOST = "oauth.yandex.ru"

    def __init__(self, user_service: UserService) -> None:
        super().__init__(user_service)

    def get_redirect_url(self) -> str:
        """Метод получения oauth redirect url."""
        ya_auth_base_url = "https://oauth.yandex.ru/authorize?"
        params = {
            "response_type": "code",
            "client_id": settings.oauth_yandex_client_id,
        }

        return ya_auth_base_url + urlencode(params)

    async def get_oauth_account(
        self, code: str
    ) -> Optional[OAuthAccountCreate]:
        """Метод получения oauth аккаунта пользователя.

        Обязательные параметры:
        - `code` - код yandex

        Возвращает модель создания oauth аккаунта. В случае ошибки
        возвращает None.
        """
        async with aiohttp.ClientSession(raise_for_status=True) as session:
            url = "https://oauth.yandex.ru/token"
            data = {
                "grant_type": "authorization_code",
                "code": code,
                "client_id": settings.oauth_yandex_client_id,
                "client_secret": settings.oauth_yandex_client_secret,
            }

            try:
                async with session.post(url, data=data) as response:
                    credentials = await response.json()
                    access_token = credentials["access_token"]
            except Exception:
                return None

            url = "https://login.yandex.ru/info"
            params = {
                "format": "json",
                "jwt_secret": settings.oauth_yandex_client_secret,
                "client_id": settings.oauth_yandex_client_id,
                "client_secret": settings.oauth_yandex_client_secret,
            }
            headers = {"Authorization": "OAuth " + access_token}

            try:
                async with session.get(
                    url, headers=headers, params=params
                ) as response:
                    oauth_account_data = await response.json()
            except Exception:
                return None

            try:
                oauth_create_model = OAuthAccountCreate(
                    user_id="unknown",
                    oauth_name=self.NAME,
                    access_token=credentials["access_token"],
                    expires_at=credentials["expires_in"],
                    refresh_token=credentials["refresh_token"],
                    account_id=oauth_account_data["id"],
                    account_email=oauth_account_data["default_email"],
                )
            except Exception:
                return None

            return oauth_create_model

    async def process_callback(self, code: str) -> tuple[str, str]:
        """Метод обработки колбека.

        Обязательные параметры:
        - `code` - код yandex
        """
        return await super().process_callback(code)

    async def unlink_oauth_account(self, user_id: str | UUID) -> None:
        """Метод отвязки oauth профиля пользователя.

        Обязательные параметры:
        - `user_id` - id пользователя
        """
        return await super().unlink_oauth_account(user_id, self.NAME)
