from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status

from backend.repositories import reviews_repo as _repo
from backend.schemas.reviews import ReviewCreate, ReviewOut, ReviewUpdate


# Internal helper: normalize repo return to ReviewOut
def _to_out(r) -> ReviewOut:
    """
    Convert repo object (dict, model, or mock with attributes)
    to a ReviewOut. This guarantees consistent response type.
    """
    if r is None:
        return None

    # Prefer attribute access (works for mocks)
    data = {
        "id": getattr(r, "id", None),
        "user_id": getattr(r, "user_id", None),
        "movie_id": getattr(r, "movie_id", None),
        "rating": getattr(r, "rating", None),
        "comment": getattr(r, "comment", None),
        "created_at": getattr(r, "created_at", None),
        "updated_at": getattr(r, "updated_at", None),
    }
    return ReviewOut(**data)


# Create
def create_review(payload: ReviewCreate, current_user_id: str) -> ReviewOut:
    exists = _repo.get_by_user(movie_id=payload.movie_id, user_id=current_user_id)
    if exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already created a review for this movie.",
        )

    now = datetime.now(timezone.utc)
    new_review = ReviewOut(
        id=str(uuid.uuid4()),
        user_id=current_user_id,
        movie_id=payload.movie_id,
        rating=payload.rating,
        comment=payload.comment,
        created_at=now,
        updated_at=now,
    )

    saved = _repo.create(new_review)
    return _to_out(saved)


def list_reviews(movie_id: str, limit: int, cursor: Optional[int]) -> dict:
    return _repo.list(movie_id, limit, cursor)


def get_review_by_user(movie_id: str, user_id: str) -> Optional[ReviewOut]:
    r = _repo.get_by_user(movie_id, user_id)
    return _to_out(r)


# UPDATE (owner only)
def update_review(
    movie_id: str,
    review_id: str,
    current_user_id: str,
    payload: ReviewUpdate,
) -> Optional[ReviewOut]:
    existing = _repo.get_by_id(movie_id, review_id)
    if not existing or getattr(existing, "user_id", None) != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this review.",
        )

    # Update new values / timestamps
    updated_data = {
        "rating": payload.rating if payload.rating is not None else existing.rating,
        "comment": payload.comment if payload.comment is not None else existing.comment,
        "updated_at": datetime.now(timezone.utc),
    }

    updated = _repo.update(movie_id, review_id, updated_data)
    return _to_out(updated)


# DELETE (owner or admin)


def delete_review(
    movie_id: str,
    review_id: str,
    current_user_id: str,
    is_admin: bool = False,
) -> bool:
    existing = _repo.get_by_id(movie_id, review_id)
    owner = getattr(existing, "user_id", None)

    if not existing or (owner != current_user_id and not is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this review.",
        )

    _repo.delete(movie_id, review_id)
    return True
