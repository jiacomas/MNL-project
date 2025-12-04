from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status

from backend.deps import get_current_user
from backend.repositories.reviews_repo import CSVReviewRepo
from backend.schemas.reviews import (
    ReviewCreate,
    ReviewListResponse,
    ReviewOut,
    ReviewUpdate,
)
from backend.services.reviews_service import ReviewsService

router = APIRouter(prefix="/reviews", tags=["reviews"])

# instantiate repo + service
repo = CSVReviewRepo()
service = ReviewsService(repo)


# CREATE
@router.post(
    "/{movie_name}",
    response_model=ReviewOut,
    status_code=status.HTTP_201_CREATED,
)
def create_review(
    movie_name: str,
    payload: ReviewCreate,
    user: str = Depends(get_current_user),
):
    return service.create_review(
        movie_name=movie_name,
        payload=payload,
        username=user["username"],
    )


# GET my review (owner)
@router.get(
    "/{movie_name}/my",
    response_model=ReviewOut | None,
)
def get_my_review(
    movie_name: str,
    user: str = Depends(get_current_user),
):
    # If no review → returns None (router returns null)
    return service.get_review_by_user(movie_name, user["username"])


@router.get(
    "/{movie_name}/{review_id}",
    response_model=ReviewOut,
)
def get_review(movie_name: str, review_id: str):
    return service.get_review(movie_name, review_id)


# LIST
@router.get(
    "/{movie_name}",
    response_model=ReviewListResponse,
)
def list_reviews(
    movie_name: str,
    limit: int = Query(50, ge=1, le=200),
    cursor: int | None = Query(0, ge=0),
    min_rating: int | None = Query(None, ge=0, le=10),
):
    items, next_cursor = service.list_reviews(
        movie_name=movie_name,
        limit=limit,
        cursor=cursor,
        min_rating=min_rating,
    )
    return ReviewListResponse(items=items, nextCursor=next_cursor)


# UPDATE  (Admin OR Owner — controlled by service)
@router.put(
    "/{movie_name}/{review_id}",
    response_model=ReviewOut,
)
def update_review(
    movie_name: str,
    review_id: str,
    payload: ReviewUpdate,
    user: dict = Depends(get_current_user),
):
    is_admin = user.get("role") == "admin"

    return service.update_review(
        movie_name=movie_name,
        review_id=review_id,
        payload=payload,
        username=user["username"],
        is_admin=is_admin,
    )


# DELETE (Admin OR Owner — controlled by service)
@router.delete(
    "/{movie_name}/{review_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_review(
    movie_name: str,
    review_id: str,
    user: str = Depends(get_current_user),
):
    is_admin = user.get("role") == "admin"

    service.delete_review(
        movie_name=movie_name,
        review_id=review_id,
        username=user["username"],
        is_admin=is_admin,
    )
