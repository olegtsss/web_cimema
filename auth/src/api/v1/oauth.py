from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Request, Response, status
from fastapi_limiter.depends import RateLimiter

from core.config import settings
from models.entity import User
from schemas.entity import AccessRefreshRead, RedirectUrlRead
from services.oauth import OauthService, get_oauth_service
from services.user import get_current_active_user

router = APIRouter(prefix="/oauth", tags=["oauth"])


@router.get(
    "/redirect_url",
    response_model=RedirectUrlRead,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(RateLimiter(
        times=settings.limiter_times, seconds=settings.limiter_seconds
    ))],
)
async def get_redirect_url(
    provider_name_or_oauth_host: str,
    oauth_service: OauthService = Depends(get_oauth_service),
) -> RedirectUrlRead:
    """Ручка получения redirect url.

    Список доступных провайдеров: `VKID`, `YANDEX`.
    """
    redirect_url = oauth_service.get_redirect_url(provider_name_or_oauth_host)
    return RedirectUrlRead(redirect_url=redirect_url)


@router.get(
    "/vk/callback",
    response_model=AccessRefreshRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RateLimiter(
        times=settings.limiter_times, seconds=settings.limiter_seconds
    ))],
)
async def process_vk_callback(
    request: Request,
    oauth_service: OauthService = Depends(get_oauth_service),
) -> AccessRefreshRead:
    """Ручка обработки колбека.

    Возвращает кортеж access и refresh токенов.
    """
    access_token, refresh_token = await oauth_service.process_vk_callback(
        request
    )
    return AccessRefreshRead(
        access_token=access_token, refresh_token=refresh_token
    )


@router.get(
    "/ya/callback",
    response_model=AccessRefreshRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RateLimiter(
        times=settings.limiter_times, seconds=settings.limiter_seconds
    ))],
)
async def process_ya_callback(
    request: Request,
    oauth_service: OauthService = Depends(get_oauth_service),
) -> AccessRefreshRead:
    """Ручка обработки колбека.

    Возвращает кортеж access и refresh токенов.
    """
    access_token, refresh_token = await oauth_service.process_ya_callback(
        request
    )
    return AccessRefreshRead(
        access_token=access_token, refresh_token=refresh_token
    )


@router.delete(
    "",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(RateLimiter(
        times=settings.limiter_times, seconds=settings.limiter_seconds
    ))],
)
async def unlink_oauth_account(
    provider_name_or_oauth_host: str,
    user: User = Depends(get_current_active_user),
    oauth_service: OauthService = Depends(get_oauth_service),
) -> Response:
    """Ручка удаления oauth аккаунта пользователя.

    Список доступных провайдеров: `VKID`, `YANDEX`.
    """
    await oauth_service.unlink_oauth_account(
        user.id, provider_name_or_oauth_host
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
