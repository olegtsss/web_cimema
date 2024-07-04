from fastapi import APIRouter, Depends, Response, status
from fastapi_limiter.depends import RateLimiter

from core.config import settings
from models.entity import User
from schemas.entity import RoleCreate, RoleRead, RoleUpdate
from services.role import RoleService, get_role_service
from services.user import get_current_active_superuser, get_current_active_user

router = APIRouter(prefix="/roles", tags=["roles"])


@router.get(
    "",
    response_model=list[RoleRead],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(RateLimiter(
        times=settings.limiter_times, seconds=settings.limiter_seconds
    ))],
)
async def get_roles(
    _: User = Depends(get_current_active_user),
    role_service: RoleService = Depends(get_role_service),
) -> list[RoleRead]:
    """Ручка получения списка ролей."""
    roles = await role_service.get_roles()
    return [RoleRead.model_validate(role) for role in roles]


@router.post(
    "",
    response_model=RoleRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RateLimiter(
        times=settings.limiter_times, seconds=settings.limiter_seconds
    ))],
)
async def create_role(
    params: RoleCreate,
    _: User = Depends(get_current_active_superuser),
    role_service: RoleService = Depends(get_role_service),
) -> RoleRead:
    """Ручка создания роли.

    Обязательные параметры:
    - `name` - название роли

    Доступно только для суперпользователя.
    """
    role = await role_service.create_role(params)
    return RoleRead.model_validate(role)


@router.get(
    "/{role_name}",
    response_model=RoleRead,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(RateLimiter(
        times=settings.limiter_times, seconds=settings.limiter_seconds
    ))],
)
async def get_role(
    role_name: str,
    _: User = Depends(get_current_active_user),
    role_service: RoleService = Depends(get_role_service),
) -> RoleRead:
    """Ручка получения роли."""
    role = await role_service.get_role(role_name)
    return RoleRead.model_validate(role)


@router.patch(
    "/{role_name}",
    response_model=RoleRead,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(RateLimiter(
        times=settings.limiter_times, seconds=settings.limiter_seconds
    ))],
)
async def update_role(
    role_name: str,
    params: RoleUpdate,
    _: User = Depends(get_current_active_superuser),
    role_service: RoleService = Depends(get_role_service),
) -> RoleRead:
    """Ручка обновления роли.

    Опциональные параметры:
    - `name` - название роли

    Доступно только для суперпользователя.
    """
    role = await role_service.update_role(role_name, params)
    return RoleRead.model_validate(role)


@router.delete(
    "/{role_name}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(RateLimiter(
        times=settings.limiter_times, seconds=settings.limiter_seconds
    ))],
)
async def delete_role(
    role_name: str,
    _: User = Depends(get_current_active_superuser),
    role_service: RoleService = Depends(get_role_service),
) -> Response:
    """Ручка удаления роли.

    Доступно только для суперпользователя.
    """
    await role_service.delete_role(role_name)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
