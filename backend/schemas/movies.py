# backend/schemas/movies.py
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


# ---------- Base ----------
class MovieBase(BaseModel):
    title: str = Field(..., min_length=1)
    movieIMDbRating: Optional[float] = None
    totalRatingCount: Optional[int] = None
    totalUserReviews: Optional[int] = None
    totalCriticReviews: Optional[int] = None
    metaScore: Optional[int] = None
    movieGenres: Optional[str] = None
    directors: Optional[str] = None
    datePublished: Optional[str] = None
    creators: Optional[str] = None
    mainStars: Optional[str] = None
    description: Optional[str] = None
    duration: Optional[int] = None
    movie_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    review_count: Optional[int] = 0

    # strip title
    @field_validator("title")
    @classmethod
    def clean_title(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("title cannot be empty")
        return v


# ---------- Create ----------
class MovieCreate(BaseModel):
    """
    Schema for creating a new movie.

    Required fields:
    - title: Movie title (used for API lookup if metadata not provided)

    Optional fields (auto-populated from external API if not provided):
    - year: Release year (helps improve API search accuracy)
    - movieGenres: Genre(s) of the movie
    - directors: Director(s) name(s)
    - datePublished: Release date
    - creators: Creator(s)/Writer(s) name(s)
    - mainStars: Main cast members
    - description: Movie description/synopsis
    - duration: Runtime in minutes

    Auto-generated fields (set by backend):
    - movie_id: Generated using UUID5 based on title
    - movieIMDbRating: Starts at 0.0
    - totalRatingCount: Starts at 0
    - totalUserReviews: Starts at 0
    - totalCriticReviews: Starts at 0
    - metaScore: Starts at 0
    - review_count: Starts at 0
    - created_at, updated_at: Set to current time
    """

    # Required fields
    title: str = Field(..., min_length=1, description="Movie title")

    # Optional fields (can be auto-populated from API)
    year: Optional[int] = Field(None, description="Release year (improves API search)")
    movieGenres: Optional[str] = Field(None, min_length=1, description="Movie genre(s)")
    directors: Optional[str] = Field(None, min_length=1, description="Director(s)")
    datePublished: Optional[str] = Field(None, description="Release date")
    creators: Optional[str] = Field(
        None, min_length=1, description="Creator(s)/Writer(s)"
    )
    mainStars: Optional[str] = Field(None, min_length=1, description="Main cast")
    description: Optional[str] = Field(
        None, min_length=1, description="Movie description"
    )
    duration: Optional[int] = Field(None, gt=0, description="Runtime in minutes")

    @field_validator("title")
    @classmethod
    def clean_title(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("title cannot be empty")
        return v

    @field_validator(
        "movieGenres",
        "directors",
        "creators",
        "mainStars",
        "description",
        mode="before",
    )
    @classmethod
    def strip_strings(cls, v):
        if v is None:
            return v
        if isinstance(v, str):
            v = v.strip()
            return v if v else None
        return v


# ---------- Update ----------
class MovieUpdate(BaseModel):
    """
    Schema for updating movie information.

    Allowed fields (all optional):
    - title
    - movieGenres
    - datePublished
    - duration
    - directors
    - creators
    - mainStars
    - description

    NOT allowed:
    - movieIMDbRating (calculated from reviews)
    - totalRatingCount (calculated)
    - totalUserReviews (calculated)
    - totalCriticReviews (calculated)
    - metaScore (calculated)
    - movie_id (immutable)
    """

    title: Optional[str] = Field(None, min_length=1)
    movieGenres: Optional[str] = Field(None, min_length=1)
    datePublished: Optional[str] = None
    duration: Optional[int] = Field(None, gt=0)
    directors: Optional[str] = Field(None, min_length=1)
    creators: Optional[str] = Field(None, min_length=1)
    mainStars: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = Field(None, min_length=1)

    @field_validator("*", mode="before")
    @classmethod
    def strip_all(cls, v):
        if isinstance(v, str):
            return v.strip() or None
        return v

    def model_post_init(self, _):
        if not any(getattr(self, f) is not None for f in self.__class__.model_fields):
            raise ValueError("At least one field must be provided for update")


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
