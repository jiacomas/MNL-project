from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator, validator


class MovieBase(BaseModel):
    """Base schema for movie data"""
    title: str = Field(..., min_length=1, max_length=500, description="Movie title")
    genre: Optional[str] = Field(None, description="Movie genre(s)")
    release_year: Optional[int] = Field(None, ge=1888, le=2100, description="Release year")
    rating: Optional[float] = Field(None, ge=0, le=10, description="Average rating")
    runtime: Optional[int] = Field(None, ge=1, le=999, description="Runtime in minutes")
    director: Optional[str] = Field(None, description="Movie director")
    cast: Optional[str] = Field(None, description="Main cast members")
    plot: Optional[str] = Field(None, description="Movie plot summary")
    poster_url: Optional[str] = Field(None, description="URL to movie poster")

    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True,
        extra="forbid",
        json_schema_extra={
            "example": {
                "title": "The Shawshank Redemption",
                "genre": "Drama",
                "release_year": 1994,
                "rating": 9.3,
                "runtime": 142,
                "director": "Frank Darabont",
                "cast": "Tim Robbins, Morgan Freeman, Bob Gunton",
                "plot": "Two imprisoned men bond over a number of years...",
                "poster_url": "https://example.com/poster.jpg"
            }
        }
    )

    @field_validator("genre", "director", "cast", "plot", "poster_url", mode="before")
    @classmethod
    def normalize_string_fields(cls, v: Optional[str]) -> Optional[str]:
        """Normalize string fields by stripping whitespace"""
        if v is not None:
            v = v.strip()
            if v == "":
                return None
        return v


class MovieCreate(MovieBase):
    """Schema for creating a new movie"""
    movie_id: Optional[str] = Field(None, description="Custom movie ID (auto-generated if not provided)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "movie_id": "tt0111161",
                "title": "The Shawshank Redemption",
                "genre": "Drama",
                "release_year": 1994
            }
        }
    )

    @field_validator("movie_id", mode="before")
    @classmethod
    def normalize_movie_id(cls, v: Optional[str]) -> Optional[str]:
        """Normalize movie_id field by stripping whitespace"""
        if v is not None:
            v = v.strip()
            if v == "":
                return None
        return v

    @field_validator('release_year')
    @classmethod
    def validate_release_year(cls, v):
        if v is not None and v < 1895:
            raise ValueError('Release year must be at least 1895')
        return v


class MovieUpdate(BaseModel):
    """Schema for updating movie data"""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    genre: Optional[str] = Field(None)
    release_year: Optional[int] = Field(None, ge=1888, le=2100)
    rating: Optional[float] = Field(None, ge=0, le=10)
    runtime: Optional[int] = Field(None, ge=1,le=999)
    director: Optional[str] = Field(None)
    cast: Optional[str] = Field(None)
    plot: Optional[str] = Field(None)
    poster_url: Optional[str] = Field(None)

    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True,
        extra="forbid",
        json_schema_extra={
            "example": {
                "rating": 9.5,
                "poster_url": "https://updated-poster.com/image.jpg"
            }
        }
    )

    @field_validator("title", "genre", "director", "cast", "plot", "poster_url", mode="before")
    @classmethod
    def normalize_string_fields(cls, v: Optional[str]) -> Optional[str]:
        """Normalize string fields"""
        if v is not None:
            v = v.strip()
            if v == "":
                return None
        return v

    @model_validator(mode="after")
    def ensure_at_least_one_field(self) -> "MovieUpdate":
        """Ensure at least one field is provided for update"""
        if all(field is None for field in [
            self.title, self.genre, self.release_year, self.rating,
            self.runtime, self.director, self.cast, self.plot, self.poster_url
        ]):
            raise ValueError("At least one field must be provided for update")
        return self


class MovieOut(MovieBase):
    """Schema for movie data returned by API"""
    movie_id: str
    created_at: datetime
    updated_at: datetime
    review_count: Optional[int] = Field(0, description="Number of reviews for this movie")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "movie_id": "tt0111161",
                "title": "The Shawshank Redemption",
                "genre": "Drama",
                "release_year": 1994,
                "rating": 9.3,
                "runtime": 142,
                "director": "Frank Darabont",
                "cast": "Tim Robbins, Morgan Freeman, Bob Gunton",
                "plot": "Two imprisoned men bond over a number of years...",
                "poster_url": "https://example.com/poster.jpg",
                "created_at": "2024-01-01T12:00:00Z",
                "updated_at": "2024-01-01T12:00:00Z",
                "review_count": 2500000
            }
        }
    )


class MovieSearchFilters(BaseModel):
    """Schema for movie search filters"""
    title: Optional[str] = Field(None, description="Search in movie titles")
    genre: Optional[str] = Field(None, description="Filter by genre")
    min_year: Optional[int] = Field(None, ge=1888, le=2100, description="Minimum release year")
    max_year: Optional[int] = Field(None, ge=1888, le=2100, description="Maximum release year")
    min_rating: Optional[float] = Field(None, ge=0, le=10, description="Minimum average rating")
    director: Optional[str] = Field(None, description="Filter by director")

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "title": "shawshank",
                "genre": "Drama",
                "min_year": 1990,
                "max_year": 2000,
                "min_rating": 8.5
            }
        }
    )


class MovieListResponse(BaseModel):
    """Schema for paginated movie list response"""
    items: List[MovieOut]
    total: int
    page: int
    page_size: int
    total_pages: int


__all__ = [
    "MovieBase",
    "MovieCreate",
    "MovieUpdate",
    "MovieOut",
    "MovieSearchFilters",
    "MovieListResponse"
]