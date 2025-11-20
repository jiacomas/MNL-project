from __future__ import annotations

from typing import Dict, Optional

from fastapi import APIRouter, Depends, Path, Query, status

from backend.deps import get_current_user_id, require_admin
from backend.schemas.reviews import (
    ReviewCreate,
    ReviewListResponse,
    ReviewOut,
    ReviewUpdate,
)
from backend.services import reviews_service as svc

router = APIRouter(prefix="/api/movies", tags=["reviews"])

# ---------- Endpoints ----------


@router.get("/{movie_id}/reviews", response_model=ReviewListResponse)
def list_reviews(
    movie_id: str = Path(..., description="Movie ID"),
    limit: int = Query(50, ge=1, le=200, description="Max number of reviews to return"),
    cursor: Optional[int] = Query(None, description="Pagination cursor"),
    min_rating: Optional[int] = Query(
        None, ge=1, le=10, description="Minimum rating filter"
    ),
):
    """List all reviews for a movie (cursor-based pagination)."""
    items, next_cursor = svc.list_reviews(movie_id, limit, cursor, min_rating)
    return ReviewListResponse(items=items, next_cursor=next_cursor)


@router.post(
    "/{movie_id}/reviews", response_model=ReviewOut, status_code=status.HTTP_201_CREATED
)
def create_review(
    movie_id: str,
    payload: ReviewCreate,
    user_id: str = Depends(get_current_user_id),
):
    """Create a new review for a specific movie."""
    payload.movie_id = movie_id
    return svc.create_review(payload.model_dump(), user_id)


@router.patch("/{movie_id}/reviews/{review_id}", response_model=ReviewOut)
def update_review(
    movie_id: str,
    review_id: str,
    payload: ReviewUpdate,
    user_id: str = Depends(get_current_user_id),
):
    """Update an existing review (only the author can update)."""
    return svc.update_review(
        movie_id, review_id, user_id, payload.model_dump(exclude_none=True)
    )


@router.delete(
    "/{movie_id}/reviews/{review_id}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_review(
    movie_id: str,
    review_id: str,
    user_id: str = Depends(get_current_user_id),
    _: Dict = Depends(require_admin),
):
    """Delete a review (owner or admin)."""
    svc.delete_review(movie_id, review_id, user_id, is_admin=True)
    return None


@router.get("/{movie_id}/reviews/me", response_model=Optional[ReviewOut])
def get_my_review(
    movie_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """Retrieve the current user's review for a movie."""
    return svc.get_review_by_user(movie_id, user_id)


@router.get("/{movie_id}/reviews/user/{user_id}", response_model=Optional[ReviewOut])
def get_review_by_user(
    movie_id: str,
    user_id: str,
):
    """Retrieve a specific user's review for a movie."""
    return svc.get_review_by_user(movie_id, user_id)
