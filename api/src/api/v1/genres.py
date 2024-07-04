from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from opentelemetry import trace

from api.v1.utils import security_jwt
from schemas import schemas
from services.genre import GenreService, get_genre_service

router = APIRouter(prefix="/genres", tags=["genres"])


@router.get(
    "/",
    response_model=list[schemas.FilmGenre],
    summary="Получение жанров",
)
async def get_genres(
    request: Request,
    payload: dict = Depends(security_jwt),
    genre_service: GenreService = Depends(get_genre_service),
) -> list[schemas.FilmGenre]:
    """Ручка получения всех жанров."""
    request_id = request.headers.get("X-Request-Id")
    span = trace.get_current_span()
    span.set_attribute("http.request_id", request_id)

    return await genre_service.get_all_genres()


@router.get(
    "/{genre_uuid}",
    response_model=schemas.FilmGenre,
    summary="Получение жанра",
)
async def get_genre_details(
    request: Request,
    genre_uuid: UUID,
    payload: dict = Depends(security_jwt),
    genre_service: GenreService = Depends(get_genre_service),
) -> schemas.FilmGenre:
    """Ручка получения жанра по uuid.

    Обязательные параметры:
    - `genre_uuid`: uuid жанра (uuid)

    Вернет 404 ошибку, если жанр не будет найден.
    """
    request_id = request.headers.get("X-Request-Id")
    span = trace.get_current_span()
    span.set_attribute("http.request_id", request_id)

    genre = await genre_service.get_genre_by_uuid(genre_uuid)
    if not genre:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Genre not found"
        )
    return genre
