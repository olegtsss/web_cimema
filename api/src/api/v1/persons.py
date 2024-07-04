from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from opentelemetry import trace

from api.v1.utils import security_jwt
from schemas import schemas
from services.person import PersonService, get_person_service

router = APIRouter(prefix="/persons", tags=["persons"])


@router.get(
    "/search",
    response_model=schemas.PersonSearchResponse,
    summary="Получение персон",
)
async def get_searched_persons(
    request: Request,
    payload: dict = Depends(security_jwt),
    params: schemas.PersonSearchParams = Depends(),
    person_service: PersonService = Depends(get_person_service),
) -> schemas.PersonSearchResponse:
    """Ручка получения персон с поиском по имени.

    Обязательные параметры:
    - `query`: запрос (str)

    Опциональные параметры:
    - `page_number`: номер страницы
    - `page_size`: размер страницы
    """
    request_id = request.headers.get("X-Request-Id")
    span = trace.get_current_span()
    span.set_attribute("http.request_id", request_id)

    total_pages, persons = await person_service.search_by_full_name(
        **params.model_dump()
    )
    return schemas.PersonSearchResponse(
        **params.model_dump(),
        total_pages=total_pages,
        results=persons,
    )


@router.get(
    "/{person_uuid}",
    response_model=schemas.Person,
    summary="Получение персоны",
)
async def get_person_details(
    request: Request,
    person_uuid: UUID,
    payload: dict = Depends(security_jwt),
    person_service: PersonService = Depends(get_person_service),
) -> schemas.Person:
    """Ручка получения персоны по uuid.

    Обязательные параметры:
    - `person_uuid`: uuid персоны (uuid)

    Вернет 404 ошибку, если персона не будет найдена.
    """
    request_id = request.headers.get("X-Request-Id")
    span = trace.get_current_span()
    span.set_attribute("http.request_id", request_id)

    person = await person_service.get_person_by_uuid(person_uuid)
    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Person not found"
        )
    return person
