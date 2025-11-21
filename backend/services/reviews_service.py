from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from fastapi import HTTPException, status

from backend.repositories.reviews_repo import CSVReviewRepo
from backend.schemas.reviews import ReviewCreate, ReviewOut, ReviewUpdate

_repo = CSVReviewRepo()

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _utc_now() -> datetime:
    """Return UTC-aware current time."""
    return datetime.now(timezone.utc)


def _raise_not_found() -> None:
    """Standardized 404 error for missing review."""
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Review not found.",
    )


def _get_review_or_404(movie_id: str, review_id: str) -> ReviewOut:
    """Return a review for a movie or raise 404."""
    # Try direct lookup
    review = _repo.get_review_by_id(movie_id, review_id)

    # Fallback: scan repo list in case storage ordering differs
    if review is None:
        reviews, _ = _repo.list_by_movie(movie_id, limit=2000)
        review = next((r for r in reviews if r.id == review_id), None)

    if review is None:
        _raise_not_found()

    return review


def _ensure_authorization(existing: ReviewOut, user_id: str, is_admin: bool) -> None:
    """Ensure user is allowed to update/delete a review."""
    if not is_admin and existing.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this review.",
        )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def create_review(payload: ReviewCreate, user_id: str) -> ReviewOut:
    """
    Create a new review for a movie.
    Enforces: one review per user per movie.
    """
    if _repo.get_review_by_user(payload.movie_id, user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User has already reviewed this movie. Use update instead.",
        )

    now = _utc_now()
    review = ReviewOut(
        id=str(uuid.uuid4()),
        user_id=user_id,
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
    """List reviews for a movie with pagination + rating filter."""
    return _repo.list_by_movie(
        movie_id,
        limit=limit,
        cursor=cursor,
        min_rating=min_rating,
    )


def update_review(
    movie_id: str,
    review_id: str,
    user_id: str,
    payload: ReviewUpdate,
) -> ReviewOut:
    """
    Update an existing review.
    Only the review author can update.
    """
    review_id = str(review_id)
    existing = _get_review_or_404(movie_id, review_id)

    _ensure_authorization(existing, user_id, is_admin=False)

    updated = existing.model_copy(
        update={
            "rating": payload.rating if payload.rating is not None else existing.rating,
            "comment": (
                payload.comment if payload.comment is not None else existing.comment
            ),
            "updated_at": _utc_now(),
        }
    )
    return _repo.update(updated)


def delete_review(
    movie_id: str,
    review_id: str,
    user_id: str,
    is_admin: bool = False,
) -> None:
    """
    Delete a review.
    Author or admin only.
    """
    review_id = str(review_id)
    existing = _get_review_or_404(movie_id, review_id)

    _ensure_authorization(existing, user_id, is_admin=is_admin)

    _repo.delete(movie_id, review_id)


def get_review_by_user(movie_id: str, user_id: str) -> Optional[ReviewOut]:
    """Return a user's review for a movie."""
    return _repo.get_review_by_user(movie_id, user_id)
