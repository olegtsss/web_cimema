import json
from typing import Optional
from urllib.parse import urlencode
from uuid import UUID, uuid4

import aiohttp
from fastapi import HTTPException, status

from core.config import settings
from schemas.entity import OAuthAccountCreate
from services.oauth_providers.provider import OauthProvider


class VkOauthProvider(OauthProvider):
    NAME = "VKID"
    OAUTH_HOST = "id.vk.com"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def get_redirect_url(self) -> str:
        """Метод получения oauth redirect url."""
        auth_base_url = "https://id.vk.com/auth?"
        params = {
            "app_id": settings.oauth_vk_client_id,
            "uuid": str(uuid4()),
            "redirect_uri": f"{settings.api_external_url}/oauth/vk/callback",
            "response_type": "silent_token",
        }

        return auth_base_url + urlencode(params)

    async def get_oauth_account(
        self, silent_token: str, silent_token_uid: str
    ) -> Optional[OAuthAccountCreate]:
        """Метод получения oauth аккаунта пользователя.

        Обязательные параметры:
        - `silent_token` - silent токен
        - `silent_token_uid` - uuid токена

        Возвращает модель создания oauth аккаунта. В случае ошибки
        возвращает None.
        """
        async with aiohttp.ClientSession(raise_for_status=True) as session:
            url = "https://api.vk.com/method/auth.exchangeSilentAuthToken"
            params = {
                "v": "5.131",
                "token": silent_token,
                "access_token": settings.oauth_vk_service_token,
                "uuid": silent_token_uid,
            }

            try:
                async with session.get(url, params=params) as response:
                    data = await response.json()
                    oauth_account_data = data["response"]
            except Exception:
                return None

            try:
                oauth_create_model = OAuthAccountCreate(
                    user_id="unknown",
                    oauth_name=self.NAME,
                    access_token=oauth_account_data["access_token"],
                    expires_at=oauth_account_data["expires_in"],
                    refresh_token=None,
                    account_id=str(oauth_account_data["user_id"]),
                    account_email=oauth_account_data["email"],
                )
            except Exception:
                return None

            return oauth_create_model

    async def process_callback(self, payload: str) -> tuple[str, str]:
        """Метод обработки колбека.

        Обязательные параметры:
        - `payload` - payload ответа провайдера
        """
        try:
            result = json.loads(payload)
            silent_token = result["token"]
            silent_token_uid = result["uuid"]
        except Exception:
            return HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to parse provided payload",
            )

        return await super().process_callback(silent_token, silent_token_uid)

    async def unlink_oauth_account(self, user_id: str | UUID) -> None:
        """Метод отвязки oauth профиля пользователя.

        Обязательные параметры:
        - `user_id` - id пользователя
        """
        return await super().unlink_oauth_account(user_id, self.NAME)
