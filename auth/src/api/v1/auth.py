from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_limiter.depends import RateLimiter

from core.config import settings
from models.entity import User
from schemas.entity import AccessRead, AccessRefreshRead, UserCreate, UserRead
from services.user import (
    UserService,
    get_current_active_user,
    get_user_service,
    oauth2_scheme,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RateLimiter(
        times=settings.limiter_times, seconds=settings.limiter_seconds
    ))],
)
async def register(
    params: UserCreate,
    user_service: UserService = Depends(get_user_service),
) -> UserRead:
    """Ручка создания профиля.

    Обязательные параметры:
    - `email` - email пользователя
    - `password` - пароль пользователя

    Опциональные параметры:
    - `is_active` - активен ли пользователь

    Параметры `is_superuser` и `is_verified` могут быть переданы,
    но не будут учтены.
    """
    user = await user_service.create_user(params)
    return UserRead.model_validate(user)


@router.post(
    "/login",
    response_model=AccessRefreshRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RateLimiter(
        times=settings.limiter_times, seconds=settings.limiter_seconds
    ))],
)
async def login(
    request: Request,
    credentials: OAuth2PasswordRequestForm = Depends(),
    user_service: UserService = Depends(get_user_service),
) -> AccessRefreshRead:
    """Ручка логина пользователя.

    Обязательные параметры:
    - `username` - email пользователя
    - `password` - пароль пользователя

    Возвращает access и refresh токены.
    """
    access_token, refresh_token = await user_service.login(
        request, credentials.username, credentials.password
    )
    return AccessRefreshRead(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(RateLimiter(
        times=settings.limiter_times, seconds=settings.limiter_seconds
    ))],
)
async def logout(
    _: User = Depends(get_current_active_user),
    access_token: str = Depends(oauth2_scheme),
    user_service: UserService = Depends(get_user_service),
) -> Response:
    """Ручка логаута пользователя."""
    await user_service.logout(access_token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/refresh",
    response_model=AccessRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RateLimiter(
        times=settings.limiter_times, seconds=settings.limiter_seconds
    ))],
)
async def refresh(
    refresh_token: str = Depends(oauth2_scheme),
    user_service: UserService = Depends(get_user_service),
) -> AccessRead:
    """Ручка обновления `access` токена.

    В качестве токена необходимо передать refresh токен.
    Возвращает новый access токен, связанный с переданным refresh.
    """
    access_token = await user_service.refresh(refresh_token)
    return AccessRead(access_token=access_token)


@router.post(
    "/logout_all",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(RateLimiter(
        times=settings.limiter_times, seconds=settings.limiter_seconds
    ))],
)
async def logout_all(
    _: User = Depends(get_current_active_user),
    access_token: str = Depends(oauth2_scheme),
    user_service: UserService = Depends(get_user_service),
) -> Response:
    """Ручка полного логаута пользователя."""
    await user_service.logout_all(access_token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
