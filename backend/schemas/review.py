from pydantic import BaseModel

class Review(BaseModel):
    review_id: str
    user_id: str
    movie_id: str
    rating: int
    comment: str