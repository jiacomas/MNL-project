# Reviews service
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import HTTPException, status

from backend.repositories.reviews_repo import CSVReviewRepo
from backend.schemas.reviews import ReviewCreate, ReviewOut, ReviewUpdate

_repo = CSVReviewRepo()


def create_review(payload: ReviewCreate) -> ReviewOut:
    """Create a new review (one per user per movie)."""
    existing = _repo.get_by_user(payload.movie_id, payload.user_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User has already reviewed this movie. Use update instead.",
        )

    now = datetime.now(timezone.utc)
    review = ReviewOut(
        id=str(uuid.uuid4()),
        user_id=payload.user_id,
        movie_id=payload.movie_id,
        rating=payload.rating,
        comment=payload.comment,
        created_at=now,
        updated_at=now,
    )
    return _repo.create(review)


def list_reviews(
    movie_id: str,
    limit: int = 50,
    cursor: Optional[int] = None,
    min_rating: Optional[int] = None,
) -> tuple[List[ReviewOut], Optional[int]]:
    """List reviews for a movie with pagination and optional filters."""
    return _repo.list_by_movie(
        movie_id,
        limit=limit,
        cursor=cursor,
        min_rating=min_rating,
    )


def update_review(
    movie_id: str,
    review_id: str,
    current_user_id: str,
    payload: ReviewUpdate,
) -> ReviewOut:
    """Update an existing review; only the author may update."""
    existing = _repo.get_by_id(movie_id, review_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found.",
        )

    if existing.user_id != current_user_id:
        # Review exists but belongs to someone else -> 403
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this review.",
        )

    updated = ReviewOut(
        # keep immutable fields from existing
        **existing.model_dump(exclude={"rating", "comment", "updated_at"}),
        rating=payload.rating if payload.rating is not None else existing.rating,
        comment=payload.comment if payload.comment is not None else existing.comment,
        updated_at=datetime.now(timezone.utc),
    )
    return _repo.update(updated)


def delete_review(movie_id: str, review_id: str, current_user_id: str) -> None:
    """Delete a review.

    Rules (what the tests expect):
    * If the review does not exist -> 404.
    * If the review exists but current_user_id is not the author -> 403.
    * If the review exists and user is the author -> delete it.
    """
    existing = _repo.get_by_id(movie_id, review_id)
    if not existing:
        # No such review at all -> 404
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found.",
        )

    if existing.user_id != current_user_id:
        # Review exists but belongs to another user -> 403 (this is the failing test)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this review.",
        )

    _repo.delete(movie_id, review_id)


def get_user_review(movie_id: str, user_id: str) -> Optional[ReviewOut]:
    """Return a user's own review for a movie, or None if not found."""
    return _repo.get_by_user(movie_id, user_id)


# .. note::
#    Parts of this file comments and basic scaffolding were auto-completed by VS Code.
#    Core logic and subsequent modifications were implemented by the author(s).
