from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from opentelemetry import trace

from api.v1.utils import security_jwt
from schemas import schemas
from services.film import FilmService, get_film_service

router = APIRouter(prefix="/films", tags=["films"])


@router.get(
    "/",
    response_model=schemas.FilmResponse,
    summary="Получение фильмов",
)
async def get_films(
    request: Request,
    payload: dict = Depends(security_jwt),
    params: schemas.FilmParams = Depends(),
    film_service: FilmService = Depends(get_film_service),
) -> schemas.FilmResponse:
    """Ручка получения фильмов с фильтрацией по жанру.

    Опциональные параметры:
    - `page_number`: номер страницы
    - `page_size`: размер страницы
    - `sort`: сортировка
    - `genre`: жанр (uuid)

    Вернет 404 ошибку, если жанр не будет найден.
    """
    request_id = request.headers.get("X-Request-Id")
    span = trace.get_current_span()
    span.set_attribute("http.request_id", request_id)

    total_pages, films = await film_service.get_films(
        **params.model_dump(exclude=["genre"]),
        genre_uuid=params.genre,
    )
    return schemas.FilmResponse(
        **params.model_dump(),
        total_pages=total_pages,
        results=films,
    )


@router.get(
    "/search",
    response_model=schemas.FilmSearchResponse,
    summary="Поиск фильмов",
)
async def get_searched_films(
    request: Request,
    payload: dict = Depends(security_jwt),
    params: schemas.FilmSearchParams = Depends(),
    film_service: FilmService = Depends(get_film_service),
) -> schemas.FilmSearchResponse:
    """Ручка получения фильмов с поиском по названию.

    Обязательные параметры:
    - `query`: запрос (str)

    Опциональные параметры:
    - `page_number`: номер страницы
    - `page_size`: размер страницы
    - `sort`: сортировка
    """
    request_id = request.headers.get("X-Request-Id")
    span = trace.get_current_span()
    span.set_attribute("http.request_id", request_id)

    total_pages, films = await film_service.search_films(
        **params.model_dump(),
    )
    return schemas.FilmSearchResponse(
        **params.model_dump(),
        total_pages=total_pages,
        results=films,
    )


@router.get(
    "/{film_uuid}",
    response_model=schemas.Film,
    summary="Получение фильма",
)
async def get_film_details(
    request: Request,
    film_uuid: UUID,
    payload: dict = Depends(security_jwt),
    film_service: FilmService = Depends(get_film_service),
) -> schemas.Film:
    """Ручка получения фильма по uuid.

    Обязательные параметры:
    - `film_uuid`: uuid фильма (uuid)

    Вернет 404 ошибку, если фильм не будет найден.
    """
    request_id = request.headers.get("X-Request-Id")
    span = trace.get_current_span()
    span.set_attribute("http.request_id", request_id)

    film = await film_service.get_film_by_uuid(film_uuid)
    if not film:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Film not found"
        )
    return film
