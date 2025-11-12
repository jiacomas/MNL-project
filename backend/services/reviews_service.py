from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from fastapi import HTTPException, status

from repositories.reviews_repo import CSVReviewRepo
from schemas.reviews import ReviewCreate, ReviewOut, ReviewUpdate

_repo = CSVReviewRepo()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_review_or_404(movie_id: str, review_id: str) -> ReviewOut:
    """Return a review for a movie, or raise 404 with 'Review not found.'."""
    # Primary lookup: repository helper
    review = _repo.get_by_id(movie_id, review_id)

    # Fallback: scan all reviews for this movie (helps if repo indexing changes)
    if review is None:
        reviews, _ = _repo.list_by_movie(movie_id, limit=10_000)
        for candidate in reviews:
            if candidate.id == review_id:
                review = candidate
                break

    if review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found.",
        )
    return review


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


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
) -> Tuple[List[ReviewOut], Optional[int]]:
    """List reviews for a movie with pagination and optional filters."""
    return _repo.list_by_movie(
        movie_id,
        limit=limit,
        cursor=cursor,
        min_rating=min_rating,
    )


def _get_review_or_404(movie_id: str, review_id: str) -> ReviewOut:
    """Helper so we always do the same 'not found' behaviour."""
    review = _repo.get_by_id(movie_id, review_id)
    if review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found.",
        )
    return review


def update_review(
    movie_id: str,
    review_id: str,
    current_user_id: str,
    payload: ReviewUpdate,
) -> ReviewOut:
    """Update an existing review (only the author may do this)."""
    review_id = str(review_id)
    existing = _get_review_or_404(movie_id, review_id)

    # Authorization: only the author can update
    if existing.user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this review.",
        )

    updated = ReviewOut(
        **existing.model_dump(exclude={"rating", "comment", "updated_at"}),
        rating=payload.rating if payload.rating is not None else existing.rating,
        comment=payload.comment if payload.comment is not None else existing.comment,
        updated_at=datetime.now(timezone.utc),
    )
    return _repo.update(updated)


def delete_review(movie_id: str, review_id: str, current_user_id: str) -> None:
    """Delete a review.

    Allowed if the current user is the author.
    """
    review_id = str(review_id)
    existing = _get_review_or_404(movie_id, review_id)

    # Authorization: only the author can delete
    if existing.user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this review.",
        )

    _repo.delete(movie_id, review_id)


def get_user_review(movie_id: str, user_id: str) -> Optional[ReviewOut]:
    """Return a user's own review for a movie, or None if not found."""
    return _repo.get_by_user(movie_id, user_id)
