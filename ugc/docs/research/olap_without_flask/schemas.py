from pydantic import BaseModel, UUID4


class Rating(BaseModel):
    id: UUID4
    user_id: UUID4
    film_id: UUID4
    rating: int
