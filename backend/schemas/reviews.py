# Reviews Schemas
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

# Field definitions for review schemas
RatingField = Field(..., ge=1, le=10, description="Rating score from 1 to 10")


class ReviewBase(BaseModel):
    # Common fields for review schemas
    rating: int = RatingField

    comment: Optional[str] = Field(
        None, max_length=2000, description="Optional review comment"
    )

    # Model configuration
    # 1. from_attributes: it allows populating models from ORM objects
    # 2. str_strip_whitespace: it trims whitespace from string fields
    # 3. extra="forbid": reject unexpected fields for safer inputs
    # 4. json_schema_extra: example payloads
    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True,
        extra="forbid",
        json_schema_extra={
            "example": [
                {"rating": 8, "comment": "Great movie with stunning visuals!"},
                {"rating": 6},  # comment is optional
            ]
        },
    )

    @field_validator("comment", mode="before")
    @classmethod
    def normalize_comment(cls, v: Optional[str]) -> Optional[str]:
        # Treat blank or whitespace-only comments as None.
        # This avoids storing meaningless empty strings in JSON/CSV.
        if v is not None:
            v = v.strip()
            if v == "":
                return None
        return v


class ReviewCreate(ReviewBase):
    user_id: str = Field(..., min_length=1, description="ID of the reviewer user.")
    movie_id: str = Field(..., min_length=1, description="ID of the reviewed movie.")

    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True,
        extra="forbid",
        json_schema_extra={
            "example": {
                "user_id": "user_12345",
                "movie_id": "movie_67890",
                "rating": 9,
                "comment": "An masterpiece!",
            }
        },
    )


class ReviewUpdate(BaseModel):
    rating: Optional[int] = Field(
        None, ge=1, le=10, description="Updated rating score from 1 to 10"
    )
    comment: Optional[str] = Field(
        None, max_length=2000, description="Updated comment (optional)"
    )

    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True,
        extra="forbid",
        json_schema_extra={
            "example": [
                {"rating": 7},
                {"comment": "Updated comment here."},
                {"rating": 8, "comment": "Great improvement!"},
            ]
        },
    )

    @field_validator("comment", mode="before")
    @classmethod
    def normalize_comment(cls, v: Optional[str]) -> Optional[str]:
        # Treat blank or whitespace-only comments as None.
        if v is not None:
            v = v.strip()
            if v == "":
                return None
        return v

    @model_validator(mode="after")
    def ensure_at_least_one_field(self) -> "ReviewUpdate":
        # Ensure at least one field is provided for update
        if self.rating is None and self.comment is None:
            raise ValueError(
                "At least one of 'rating' or 'comment' must be provided for update."
            )
        return self


class ReviewOut(ReviewBase):
    # What the API returns to clients
    id: str
    user_id: str
    movie_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True,
        extra="ignore",
        json_schema_extra={
            "examples": [
                {
                    "id": "review_abc123",
                    "user_id": "user_12345",
                    "movie_id": "movie_67890",
                    "rating": 9,
                    "comment": "An masterpiece!",
                    "created_at": "2024-01-01T12:00:00Z",
                    "updated_at": "2024-01-02T15:30:00Z",
                }
            ]
        },
    )


# explicit export
__all__ = ["ReviewBase", "ReviewCreate", "ReviewUpdate", "ReviewOut"]
