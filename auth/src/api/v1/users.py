from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from fastapi_limiter.depends import RateLimiter

from core.config import settings
from models.entity import User
from schemas.entity import (
    Pagination,
    SuperuserUpdate,
    UserRead,
    UserUpdate,
    VisitListRead,
    VisitRead,
)
from services.user import (
    UserService,
    get_current_active_superuser,
    get_current_active_user,
    get_user_service,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/me/visits",
    response_model=VisitListRead,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(RateLimiter(
        times=settings.limiter_times, seconds=settings.limiter_seconds
    ))],
)
async def get_my_visits(
    params: Pagination = Depends(),
    user: User = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service),
) -> VisitListRead:
    """Ручка получения визитов."""
    total_visits, visits = await user_service.get_user_visits(
        user.id, params.limit, params.offset
    )
    return VisitListRead(
        offset=params.offset,
        limit=params.limit,
        total_visits=total_visits,
        visits=[VisitRead.model_validate(visit) for visit in visits],
    )


@router.get(
    "/me",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(RateLimiter(
        times=settings.limiter_times, seconds=settings.limiter_seconds
    ))],
)
async def get_me(
    user: User = Depends(get_current_active_user),
) -> UserRead:
    """Ручка получения профиля."""
    return UserRead.model_validate(user)


@router.patch(
    "/me",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(RateLimiter(
        times=settings.limiter_times, seconds=settings.limiter_seconds
    ))],
)
async def update_me(
    params: UserUpdate,
    user: User = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service),
) -> UserRead:
    """Ручка обновления профиля.

    Опциональные параметры:
    - `email` - email пользователя
    - `password` - пароль пользователя
    - `is_active` - активен ли пользователь

    Параметры `is_superuser` и `is_verified` могут быть переданы,
    но не будут учтены.
    """
    user = await user_service.update_user(user.id, params)
    return UserRead.model_validate(user)


@router.get(
    "/{user_id}/visits",
    response_model=VisitListRead,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(RateLimiter(
        times=settings.limiter_times, seconds=settings.limiter_seconds
    ))],
)
async def get_user_visits(
    user_id: UUID,
    params: Pagination = Depends(),
    _: User = Depends(get_current_active_superuser),
    user_service: UserService = Depends(get_user_service),
) -> VisitListRead:
    """Ручка получения визитов пользователя.

    Доступно только для суперпользователя.
    """
    total_visits, visits = await user_service.get_user_visits(
        user_id, params.limit, params.offset
    )
    return VisitListRead(
        offset=params.offset,
        limit=params.limit,
        total_visits=total_visits,
        visits=[VisitRead.model_validate(visit) for visit in visits],
    )


@router.get(
    "/{user_id}",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(RateLimiter(
        times=settings.limiter_times, seconds=settings.limiter_seconds
    ))],
)
async def get_user(
    user_id: UUID,
    _: User = Depends(get_current_active_superuser),
    user_service: UserService = Depends(get_user_service),
) -> UserRead:
    """Ручка получения профиля пользователя.

    Доступно только для суперпользователя.
    """
    user = await user_service.get_user(user_id)
    return UserRead.model_validate(user)


@router.patch(
    "/{user_id}",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(RateLimiter(
        times=settings.limiter_times, seconds=settings.limiter_seconds
    ))],
)
async def update_user(
    user_id: UUID,
    params: SuperuserUpdate,
    _: User = Depends(get_current_active_superuser),
    user_service: UserService = Depends(get_user_service),
) -> UserRead:
    """Ручка обновления профиля пользователя.

    Опциональные параметры:
    - `email` - email пользователя
    - `password` - пароль пользователя
    - `is_active` - активен ли пользователь
    - `is_superuser` - является ли пользователь суперпользователем
    - `is_verified` - верифицирован ли email пользователя
    - `roles` - роли пользователя

    Доступно только для суперпользователя. Параметры `is_superuser` и
    `is_verified` будут учтены. В качестве ролей необходимо передать спиок
    имен ролей.
    """
    user = await user_service.update_user(user_id, params, safe=False)
    return UserRead.model_validate(user)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(RateLimiter(
        times=settings.limiter_times, seconds=settings.limiter_seconds
    ))],
)
async def delete_user(
    user_id: UUID,
    _: User = Depends(get_current_active_superuser),
    user_service: UserService = Depends(get_user_service),
) -> Response:
    """Ручка удаления пользователя.

    Доступно только для суперпользователя.
    """
    await user_service.delete_user(user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
