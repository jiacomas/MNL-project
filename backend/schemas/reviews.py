from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

RatingField = Field(..., ge=0, le=10, description="Rating score from 0 to 10")


class ReviewBase(BaseModel):
    review_id: str
    movie_name: str
    username: str
    rating: int = RatingField
    title_review: str
    comment: Optional[str] = Field(None, max_length=2000)
    created_at: datetime
    updated_at: datetime
    usefulness: int
    total_votes: int

    @field_validator("comment", mode="before")
    @classmethod
    def normalize_comment(cls, v):
        if v is None:
            return None
        v = v.strip()
        return v or None


class ReviewCreate(BaseModel):
    rating: int = RatingField
    title_review: Optional[str] = Field("", description="Title of the review")
    comment: Optional[str] = Field(None, max_length=2000)

    @field_validator("comment", mode="before")
    @classmethod
    def normalize_comment(cls, v):
        if v is None:
            return None
        v = v.strip()
        return v or None

    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True,
        extra="forbid",
    )


class ReviewUpdate(BaseModel):
    title_review: Optional[str] = Field(None)
    rating: Optional[int] = Field(None, ge=1, le=10)
    comment: Optional[str] = Field(None, max_length=2000)

    @field_validator("comment", mode="before")
    @classmethod
    def normalize_comment(cls, v):
        if v is None:
            return None
        v = v.strip()
        return v or None

    @model_validator(mode="after")
    def ensure_not_empty(self):
        if self.title_review is None and self.rating is None and self.comment is None:
            raise ValueError("At least one field must be provided to update a review.")
        return self

    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
        str_strip_whitespace=True,
    )


class ReviewOut(ReviewBase):
    model_config = ConfigDict(
        from_attributes=True,
        extra="ignore",
    )


class ReviewListResponse(BaseModel):
    items: List[ReviewOut]
    next_cursor: Optional[int] = Field(None, alias="nextCursor")

    model_config = ConfigDict(
        from_attributes=True,
        extra="ignore",
        populate_by_name=True,
    )
