from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_limiter.depends import RateLimiter

from core.config import settings
from schemas.entity import (
    CreateTemplate, Tag, Template, TemplateList, TemplateListResponse
)
from services.service import service
from schemas.entity import Pagination

router = APIRouter(prefix="/templates", tags=["templates"])


@router.get(
    "/tags",
    response_model=list[Tag],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(RateLimiter(
        times=settings.limiter_times, seconds=settings.limiter_seconds
    ))],
)
async def get_tags() -> list[Tag]:
    """Ручка получения тегов."""
    tags = await service.get_tags()
    return [Tag(**tag) for tag in tags]


@router.get(
    "",
    response_model=TemplateListResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(RateLimiter(
        times=settings.limiter_times, seconds=settings.limiter_seconds
    ))],
)
async def get_templates(
    params: Pagination = Depends()
) -> TemplateListResponse:
    """Ручка получения шаблонов."""
    templates = await service.get_templates(params)
    return TemplateListResponse(
        limit=params.limit,
        offset=params.offset,
        templates=[TemplateList.model_validate(tmp) for tmp in templates],
    )


@router.post(
    "",
    response_model=Template,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RateLimiter(
        times=settings.limiter_times, seconds=settings.limiter_seconds
    ))],
)
async def create_template(template_create_model: CreateTemplate) -> Template:
    """Ручка создания шаблона."""
    template = await service.create_template(template_create_model)
    return Template.model_validate(template)


@router.get(
    "/{template_id}",
    response_model=Template,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(RateLimiter(
        times=settings.limiter_times, seconds=settings.limiter_seconds
    ))],
)
async def get_template(template_id: UUID) -> Template:
    """Ручка получения шаблона по id."""
    template = await service.get_template(template_id)
    if template is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found",
        )

    return Template.model_validate(template)
