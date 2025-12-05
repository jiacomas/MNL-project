from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Path, Query, status
from fastapi.responses import Response

from backend.deps import get_current_user_id
from backend.schemas.reviews import (
    ReviewCreate,
    ReviewListResponse,
    ReviewOut,
    ReviewUpdate,
)
from backend.services import reviews_service as svc
from backend.services.auth_service import get_current_user

router = APIRouter(prefix="/api/movies", tags=["reviews"])

# ---------- Endpoints ----------


@router.get("/{movie_name}/reviews", response_model=ReviewListResponse)
def list_reviews(
    movie_name: str = Path(..., description="Movie Name"),
    limit: int = Query(50, ge=1, le=200, description="Max number of reviews to return"),
    cursor: Optional[int] = Query(0, description="Pagination cursor"),
    min_rating: Optional[int] = Query(
        None, ge=1, le=10, description="Minimum rating filter"
    ),
):
    """List all reviews for a movie (cursor-based pagination)."""
    items, next_cursor = svc.list_reviews(movie_name, limit, cursor, min_rating)
    return ReviewListResponse(items=items, next_cursor=next_cursor)


@router.post(
    "/{movie_name}/reviews",
    response_model=ReviewOut,
    status_code=status.HTTP_201_CREATED,
)
def create_review(
    movie_name: str,
    payload: ReviewCreate,
    user_id: str = Depends(get_current_user_id),
):
    """Create a new review for a specific movie."""
    payload.movie_name = movie_name
    return svc.create_review(payload, user_id)


@router.patch("/{movie_name}/reviews/{review_id}", response_model=ReviewOut)
def update_review(
    movie_name: str,
    review_id: str,
    payload: ReviewUpdate,
    user_id: str = Depends(get_current_user_id),
):
    """Update an existing review (only the author can update).

    The route includes `review_id` for URL compatibility with the frontend,
    but the operation identifies the review by the authenticated user.
    """
    return svc.update_review(movie_name, user_id, payload)


@router.delete("/{movie_name}/reviews")
@router.delete("/{movie_name}/reviews")
def delete_review(movie_name: str, user: dict = Depends(get_current_user)):
    """Delete a review (owner or admin).

    This endpoint accepts the authenticated user and determines whether
    they are an admin or the owner; the service enforces authorization.
    """
    # If `user` is a dict (from get_current_user) extract user_id and role
    user_id = None
    is_admin = False
    if isinstance(user, dict):
        user_id = user.get("user_id")
        is_admin = user.get("role") == "admin"
    else:
        # Fallback: in some code paths get_current_user_id returns the id string
        user_id = str(user)

    svc.delete_review(movie_name, user_id, is_admin=is_admin)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{movie_name}/reviews/id/{review_id}", response_model=ReviewOut)
def get_review_by_id(movie_name: str, review_id: str):
    """Retrieve a review by its review_id for a given movie."""
    return svc.get_review_by_id(movie_name, review_id)


@router.get("/{movie_name}/reviews/me", response_model=Optional[ReviewOut])
def get_my_review(
    movie_name: str,
    user_id: str = Depends(get_current_user_id),
):
    """Retrieve the current user's review for a movie."""
    return svc.get_review_by_user(movie_name, user_id)


@router.get("/{movie_name}/reviews/user/{user_id}", response_model=Optional[ReviewOut])
def get_review_by_user(
    movie_name: str,
    user_id: str,
):
    """Retrieve a specific user's review for a movie."""
    return svc.get_review_by_user(movie_name, user_id)
