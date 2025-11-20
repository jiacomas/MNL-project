# backend/schemas/movies.py
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


# ---------- Base ----------
class MovieBase(BaseModel):
    title: str = Field(..., min_length=1)
    genre: Optional[str] = None
    release_year: Optional[int] = None
    rating: Optional[float] = None
    runtime: Optional[int] = None
    director: Optional[str] = None
    cast: Optional[str] = None
    plot: Optional[str] = None
    poster_url: Optional[str] = None

    # strip title
    @field_validator("title")
    @classmethod
    def clean_title(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("title cannot be empty")
        return v


# ---------- Create ----------
class MovieCreate(MovieBase):
    movie_id: Optional[str] = None

    @field_validator("movie_id")
    @classmethod
    def normalize_movie_id(cls, v: Optional[str]):
        if v is None:
            return None
        v = v.strip()
        return v or None  # empty → None


# ---------- Update ----------
class MovieUpdate(BaseModel):
    title: Optional[str] = None
    genre: Optional[str] = None
    release_year: Optional[int] = None
    rating: Optional[float] = None
    runtime: Optional[int] = None
    director: Optional[str] = None
    cast: Optional[str] = None
    plot: Optional[str] = None
    poster_url: Optional[str] = None

    @field_validator("*", mode="before")
    @classmethod
    def strip_all(cls, v):
        if isinstance(v, str):
            return v.strip() or None
        return v

    def model_post_init(self, _):
        if not any(getattr(self, f) is not None for f in self.__class__.model_fields):
            raise ValueError("At least one field must be provided")


# ---------- Out ----------
class MovieOut(MovieBase):
    movie_id: str
    created_at: datetime
    updated_at: datetime
    review_count: int = 0


# ---------- List ----------
class MovieListResponse(BaseModel):
    items: list[MovieOut]
    total: int
    page: int
    page_size: int
    total_pages: int


# ---------- Filters ----------
class MovieSearchFilters(BaseModel):
    title: Optional[str] = None
    genre: Optional[str] = None
    release_year: Optional[int] = None

    @field_validator("title", "genre", mode="before")
    @classmethod
    def normalize_text(cls, v):
        if v is None:
            return v
        v = v.strip()
        return v or None
