# backend/schemas/bookmarks.py
from datetime import datetime, timezone

from pydantic import UUID4, BaseModel, ConfigDict, Field, field_validator

# Field definitions for review schemas
UserIdField = Field(..., min_length=1, description="ID of the user who bookmarked.")
MovieIdField = Field(..., min_length=1, description="ID of the bookmarked movie.")


# Base schema
class BookmarkBase(BaseModel):
    '''Common fields shared by all bookmark schemas.
    Represents a single bookmark linking a user and a movie.'''

    user_id: str = UserIdField
    movie_id: str = MovieIdField

    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True,
        extra="forbid",
        json_schema_extra={
            "example": [
                {
                    "user_id": "user_12345",
                    "movie_id": "movie_67890",
                },
                {
                    "user_id": "user_54321",
                    "movie_id": "movie_09876",
                },
            ]
        },
    )

    # normalize blank strings -> error
    @field_validator("user_id", "movie_id", mode="before")
    @classmethod
    def non_blank(cls, v: str) -> str:
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError("must not be blank")
        return v


# Create Schema
class BookmarkCreate(BookmarkBase):
    '''Schema used when creating a new bookmark entry.'''

    # id, created_at, updated_at are system-generated
    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True,
        extra="forbid",
        json_schema_extra={
            "example": {
                "user_id": "user_12345",
                "movie_id": "movie_67890",
            }
        },
    )


# Output Schema
class BookmarkOut(BookmarkBase):
    '''Schema representing a bookmark returned to the client.'''

    id: UUID4 = Field(..., description="System-generated unique bookmark ID (UUIDv4).")
    created_at: datetime = Field(
        ..., description="Timestamp when the bookmark was created."
    )
    updated_at: datetime = Field(
        ..., description="Timestamp when the bookmark was last updated."
    )

    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True,
        extra="ignore",
        json_schema_extra={
            "example": [
                {
                    "id": "bookmark_abc123",
                    "user_id": "user_12345",
                    "movie_id": "movie_67890",
                    "created_at": "2024-01-01T12:00:00Z",
                    "updated_at": "2024-01-02T12:00:00Z",
                }
            ]
        },
    )

    # enforce timezone-aware datetimes
    @field_validator("created_at", "updated_at", mode="before")
    @classmethod
    def ensure_tzaware(cls, v: datetime) -> datetime:
        if isinstance(v, str):
            return v  # let Pydantic parse ISO strings itself
        if isinstance(v, datetime) and v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v


# explicit export
__all__ = ["BookmarkBase", "BookmarkCreate", "BookmarkOut"]
