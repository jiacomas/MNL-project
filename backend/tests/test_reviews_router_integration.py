from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.deps import get_current_user_id, require_admin
from backend.schemas.reviews import (
    ReviewCreate,
    ReviewListResponse,
    ReviewOut,
    ReviewUpdate,
)
from backend.services import reviews_service as svc

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/reviews", tags=["reviews"])


# Create a review (auth required)
@router.post("", response_model=ReviewOut, status_code=status.HTTP_201_CREATED)
def create_review_endpoint(
    payload: ReviewCreate,
    user_id: str = Depends(get_current_user_id),
):
    """
    POST /api/reviews
    User creates a review for a movie. `user_id` must come from header.
    """
    return svc.create_review(
        movie_id=payload.movie_id, user_id=user_id, payload=payload
    )


# List reviews for a movie (public)
@router.get("/movie/{movie_id}", response_model=ReviewListResponse)
def list_reviews_endpoint(
    movie_id: str,
    limit: int = Query(10, ge=1, le=100),
    cursor: Optional[int] = Query(None, ge=0),
):
    """
    GET /api/reviews/movie/{movie_id}
    Cursor-based pagination.
    """
    return svc.list_reviews(movie_id=movie_id, limit=limit, cursor=cursor)


# Get review by user id (public)
@router.get(
    "/movie/{movie_id}/user/{other_user_id}", response_model=Optional[ReviewOut]
)
def get_review_by_user_endpoint(
    movie_id: str,
    other_user_id: str,
):
    """
    GET /api/reviews/movie/{movie_id}/user/{uid}
    Public lookup of someone else's review.
    """
    return svc.get_review_by_user(movie_id=movie_id, user_id=other_user_id)


# Get your own review (auth required)
@router.get("/movie/{movie_id}/me", response_model=Optional[ReviewOut])
def get_my_review_endpoint(
    movie_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """
    GET /api/reviews/movie/{movie_id}/me
    Fetch only the caller's review.
    """
    return svc.get_review_by_user(movie_id=movie_id, user_id=user_id)


# Update a review (only owner)
@router.patch("/movie/{movie_id}/{review_id}", response_model=ReviewOut)
def update_review_endpoint(
    movie_id: str,
    review_id: str,
    payload: ReviewUpdate,
    user_id: str = Depends(get_current_user_id),
):
    """
    PATCH /api/reviews/movie/{movie_id}/{review_id}
    Only the owner is allowed to update their review.
    """
    updated = svc.update_review(
        movie_id=movie_id,
        review_id=review_id,
        payload=payload,
        current_user_id=user_id,
    )
    if updated is None:
        raise HTTPException(status_code=403, detail="Not allowed to edit this review.")
    return updated


# Delete a review (owner or admin)
@router.delete("/movie/{movie_id}/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_review_endpoint(
    movie_id: str,
    review_id: str,
    user_id: str = Depends(get_current_user_id),
    admin_user: dict = Depends(require_admin),
):
    """
    DELETE /api/reviews/movie/{movie_id}/{review_id}
    Owner can delete. Admin can delete anyone.
    """
    allowed = svc.delete_review(
        movie_id=movie_id,
        review_id=review_id,
        current_user_id=user_id,
        is_admin=True,
    )
    if not allowed:
        raise HTTPException(
            status_code=403, detail="Not allowed to delete this review."
        )
    return None
