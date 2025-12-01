# Reviews Schemas
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

# Field definitions for review schemas
RatingField = Field(..., ge=0, le=10, description="Rating score from 0 to 10")


class ReviewBase(BaseModel):
    # Common fields for review schemas
    review_id: str
    movie_id: str
    username: str
    rating: int = RatingField
    title_review: str
    comment: Optional[str] = Field(
        None, max_length=2000, description="Optional review comment"
    )
    created_at: datetime
    updated_at: datetime
    usefulness: int
    total_votes: int

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


class ReviewCreate(BaseModel):
    """
    Client payload for creating a new review.

    NOTE:
    - `username` must NOT be provided by clients.
    - The backend injects the authenticated user ID using auth dependencies
      (temporary header-based auth or future JWT auth).
    """

    movie_id: str = Field(..., min_length=1, description="ID of the reviewed movie.")
    rating: int = RatingField
    title_review: Optional[str] = Field("", description="Title of the review")
    comment: Optional[str] = Field(
        None, max_length=2000, description="Optional review comment"
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

    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True,
        extra="forbid",
        json_schema_extra={
            "example": {
                "movie_id": "movie_67890",
                "rating": 9,
                "title_review": "Amazing",
                "comment": "An masterpiece!",
            }
        },
    )


class ReviewUpdate(BaseModel):
    """
    Payload for updating an existing review.
    Allows partial update but requires at least one field.
    """

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

    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True,
        extra="ignore",
        json_schema_extra={
            "examples": [
                {
                    "review_id": "review_abc123",
                    "username": "user_12345",
                    "movie_id": "movie_67890",
                    "rating": 9,
                    "title_review": "Amazing",
                    "comment": "An masterpiece!",
                    "created_at": "2024-01-01T12:00:00Z",
                    "updated_at": "2024-01-02T15:30:00Z",
                    "usefulness": 5,
                    "total_votes": 10,
                }
            ]
        },
    )


class ReviewListResponse(BaseModel):
    """Paginated list of reviews with optional cursor for continuation."""

    items: List[ReviewOut]
    next_cursor: Optional[int] = Field(None, alias="nextCursor")

    model_config = ConfigDict(
        from_attributes=True,
        extra="ignore",
    )


# explicit export
__all__ = [
    "ReviewBase",
    "ReviewCreate",
    "ReviewUpdate",
    "ReviewOut",
    "ReviewListResponse",
]
