from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_limiter.depends import RateLimiter

from core.config import settings
from schemas.entity import (
    CreateNotification,
    Notification,
    NotificationListResponse,
    NotificationStatusResponse,
    Pagination,
)
from services.service import service

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.post(
    "",
    response_model=Notification,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RateLimiter(
        times=settings.limiter_times, seconds=settings.limiter_seconds
    ))],
)
async def create_notification(
    notification_create_model: CreateNotification
) -> Notification:
    """Ручка создания уведомления."""
    notification = await service.create_notification(notification_create_model)
    return Notification.model_validate(notification)


@router.get(
    "/my",
    response_model=NotificationListResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(RateLimiter(
        times=settings.limiter_times, seconds=settings.limiter_seconds
    ))],
)
async def get_my_notifications(
    params: Pagination = Depends()
) -> NotificationListResponse:
    """Ручка получения собственных уведомлений."""
    user_id = UUID("56cff0fd-0446-45b0-b0b3-5be91f43a6e2")
    notifications = await service.get_user_notifications(user_id, params)
    return NotificationListResponse(
        limit=params.limit,
        offset=params.offset,
        notifications=[Notification.model_validate(n) for n in notifications],
    )


@router.get(
    "/{notification_id}",
    response_model=Notification,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(RateLimiter(
        times=settings.limiter_times, seconds=settings.limiter_seconds
    ))],
)
async def get_notification(notification_id: UUID) -> Notification:
    """Ручка получения уведомления по id."""
    notification = await service.get_notification(notification_id)
    if notification is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )

    return Notification.model_validate(notification)


@router.get(
    "/{notification_id}/status",
    response_model=NotificationStatusResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(RateLimiter(
        times=settings.limiter_times, seconds=settings.limiter_seconds
    ))],
)
async def get_notification_status(notification_id: UUID) -> NotificationStatusResponse:
    """Ручка получения статуса уведомления по id."""
    notification_status = await service.get_notification_status(
        notification_id
    )
    if notification_status is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification status not found",
        )

    return NotificationStatusResponse.model_validate(notification_status)
