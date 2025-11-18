from __future__ import annotations

from pydantic import BaseModel


class RecommendationOut(BaseModel):
    """Single movie recommendation returned to the client."""

    movie_id: str
    title: str
    reason: str
