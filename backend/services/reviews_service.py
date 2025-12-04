from __future__ import annotations

from typing import List, Optional, Tuple

from fastapi import HTTPException, status

from backend.repositories.reviews_repo import CSVReviewRepo, _stable_uuid5
from backend.repositories.users_repo import UserRepository
from backend.schemas.reviews import ReviewCreate, ReviewOut, ReviewUpdate
from backend.utils.datetime_utils import now_utc

_repo = CSVReviewRepo()

# Helpers


def _get_review_or_404(movie_name: str, user_id: str) -> ReviewOut:
    """Return a review for a movie, or raise 404 (assuming each user can only review it ones)"""
    # Primary lookup
    review = _repo.get_review_by_user(movie_name, user_id)

    # Fallback: scan current movie reviews in case repo index differs by type
    if review is None:
        next_cursor = 0
        page_size = 100  # Define a suitable page size
        while True:
            reviews, next_cursor = _repo.list_by_movie(
                movie_name, cursor=next_cursor, limit=page_size
            )
            if not reviews:
                break  # No more reviews to fetch

            for candidate in reviews:
                # candidate may have user_id (preferred) or username storing the id
                if (
                    getattr(candidate, "user_id", None) == user_id
                    or candidate.username == user_id
                ):
                    review = candidate
                    break

            if review is not None:
                break  # Exit outer loop if review was found

    if review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found.",
        )
    return review


def create_review(payload: ReviewCreate, user_id: str) -> ReviewOut:
    """Create a new review (one per user per movie)."""
    existing = _repo.get_review_by_user(payload.movie_name, user_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User has already reviewed this movie. Use update instead.",
        )

    # Attempt to resolve a friendly username for display
    repo = UserRepository()
    user = repo.get_by_id(user_id)
    display_name = getattr(user, "username", None) if user else None

    now = now_utc()
    review = ReviewOut(
        review_id=_stable_uuid5(payload.movie_name, user_id, now, payload.title_review),
        username=display_name or user_id,
        user_id=user_id,
        movie_name=payload.movie_name,
        rating=payload.rating,
        title_review=payload.title_review or "",  # Default empty title
        comment=payload.comment,
        created_at=now,
        updated_at=now,
        usefulness=0,
        total_votes=0,
    )
    return _repo.create(review)


def list_reviews(
    movie_name: str,
    limit: int = 50,
    cursor: Optional[int] = None,
    min_rating: Optional[int] = None,
) -> Tuple[List[ReviewOut], Optional[int]]:
    """List reviews for a movie with pagination and optional filters."""
    return _repo.list_by_movie(
        movie_name,
        limit=limit,
        cursor=cursor,
        min_rating=min_rating,
    )


def update_review(
    movie_name: str,
    user_id: str,
    payload: ReviewUpdate,
) -> ReviewOut:
    """Update an existing review (only the author may do this)."""
    existing = _get_review_or_404(movie_name, user_id)

    # Allow match by explicit user_id or legacy username-stored-id
    if not (
        getattr(existing, "user_id", None) == user_id or existing.username == user_id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this review.",
        )

    updated = ReviewOut(
        **existing.model_dump(
            exclude={"rating", "title_review", "comment", "updated_at"}
        ),
        title_review=(
            payload.title_review
            if payload.title_review is not None
            else existing.title_review
        ),
        rating=payload.rating if payload.rating is not None else existing.rating,
        comment=payload.comment if payload.comment is not None else existing.comment,
        updated_at=now_utc(),
    )
    return _repo.update(updated)


def delete_review(movie_name: str, user_id: str, is_admin: bool = False) -> None:
    """Delete a review; only the author or an admin may delete."""
    existing = _get_review_or_404(movie_name, user_id)

    if not is_admin and not (
        getattr(existing, "user_id", None) == user_id or existing.username == user_id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this review.",
        )

    _repo.delete(movie_name, existing.review_id)


def get_review_by_user(movie_name: str, user_id: str) -> Optional[ReviewOut]:
    """Return a user's own review for a movie, or None if not found."""
    return _repo.get_review_by_user(movie_name, user_id)


def get_all_reviews_for_user(user_id: str) -> List[ReviewOut]:
    """Retrieve all reviews written by a specific user across all movies."""
    # Note: This scans all movies, which is expensive.
    all_reviews = _repo.get_all_reviews_flat()
    return [
        r
        for r in all_reviews
        if getattr(r, "user_id", None) == user_id or r.username == user_id
    ]
