from functools import lru_cache
from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status

from services.oauth_providers.provider import OauthProvider
from services.oauth_providers.vk import VkOauthProvider
from services.oauth_providers.yandex import YandexOauthProvider
from services.user import UserService, get_user_service


@lru_cache
def get_oauth_service(
    user_service: UserService = Depends(get_user_service),
):
    return OauthService(user_service)


class OauthService:
    PROVIDER_CLASSES = (VkOauthProvider, YandexOauthProvider,)

    def __init__(self, user_service: UserService) -> None:
        self.user_service = user_service

    def _get_provider_class(
        self, name_or_oauth_host: str
    ) -> Optional[OauthProvider]:
        for provider_cls in self.PROVIDER_CLASSES:
            if name_or_oauth_host in [
                provider_cls.NAME, provider_cls.OAUTH_HOST
            ]:
                return provider_cls
        return None

    @lru_cache
    def _get_provider(self, name_or_oauth_host: str) -> OauthProvider:
        provider_cls = self._get_provider_class(name_or_oauth_host)
        if provider_cls is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Oauth provider not found",
            )
        return provider_cls(self.user_service)

    def get_redirect_url(self, provider_name_or_oauth_host: str) -> str:
        provider = self._get_provider(provider_name_or_oauth_host)
        return provider.get_redirect_url()

    async def process_vk_callback(self, request: Request) -> tuple[str, str]:
        provider = self._get_provider(VkOauthProvider.NAME)
        return await provider.process_callback(**dict(request.query_params))

    async def process_ya_callback(self, request: Request) -> tuple[str, str]:
        provider = self._get_provider(YandexOauthProvider.NAME)
        return await provider.process_callback(**dict(request.query_params))

    async def unlink_oauth_account(
        self, user_id: UUID, provider_name_or_oauth_host: str
    ) -> None:
        provider = self._get_provider(provider_name_or_oauth_host)
        return await provider.unlink_oauth_account(user_id)
