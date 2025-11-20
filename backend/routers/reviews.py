# reviews router
from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from backend.deps import get_fake_is_admin, get_fake_user_id  # use temporary auth
from backend.schemas.reviews import ReviewCreate, ReviewOut, ReviewUpdate
from backend.services import reviews_service as svc

router = APIRouter(prefix="/api/reviews", tags=["reviews"])


# Auth Abstraction Layer
def get_current_user(user_id: str = Depends(get_fake_user_id)) -> str:
    """
    Current authenticated user ID as a plain string.
    Later you can swap get_fake_user_id -> real auth dependency.
    """
    return user_id


def get_current_admin(is_admin: bool = Depends(get_fake_is_admin)):
    """
    Admin-only dependency (replaceable later).
    Tests can patch this function.
    """
    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return True


@router.get("/movie/{movie_id}", response_model=Dict[str, Any])
def list_reviews_endpoint(
    movie_id: str = Path(..., description="Movie ID(directory name under data/movies)"),
    limit: int = Query(50, ge=1, le=200, description="Max number of reviews to return"),
    cursor: Optional[int] = Query(None, description="Pagination cursor"),
    min_rating: Optional[int] = Query(
        None, ge=1, le=10, description="Minimum rating filter"
    ),
):
    '''List reviews for a movie with cursor-based pagination
    Returns a JSON object: {"items": ReviewOut[], "nextCursor": int | null}.
    Frontend can pass nextCursor from the previous response to fetch the next page.
    '''
    items, next_cursor = svc.list_reviews(
        movie_id=movie_id,
        limit=limit,
        cursor=cursor,
        min_rating=min_rating,
    )
    return {"items": items, "nextCursor": next_cursor}


@router.post("", response_model=ReviewOut, status_code=status.HTTP_201_CREATED)
def create_review_endpoint(
    payload: ReviewCreate,
    user: str = Depends(get_current_user),
):
    '''Create a new review for a movie by the current user'''
    return svc.create_review(payload, user)


@router.patch("/movie/{movie_id}/{review_id}", response_model=ReviewOut)
def update_review_endpoint(
    movie_id: str,
    review_id: str,
    payload: ReviewUpdate,
    user: str = Depends(get_current_user),
):
    '''Update an existing review by the current user'''
    return svc.update_review(
        movie_id=movie_id,
        review_id=review_id,
        current_user_id=user,
        payload=payload,
    )


@router.delete("/movie/{movie_id}/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_review_endpoint(
    movie_id: str,
    review_id: str,
    user: str = Depends(get_current_user),
    _: bool = Depends(get_current_admin),
):
    '''Delete an existing review by the current user or admin'''
    svc.delete_review(
        movie_id=movie_id,
        review_id=review_id,
        current_user_id=user,
        admin_override=True,
    )
    return None


@router.get("/movie/{movie_id}/me", response_model=Optional[ReviewOut])
def get_my_review_endpoint(
    movie_id: str,
    user: str = Depends(get_current_user),  # only depends on current_user_id
):
    '''Get the review for a movie by the currently authenticated user'''
    # Use current_user_id
    return svc.get_user_review(movie_id=movie_id, user_id=user)


@router.get("/movie/{movie_id}/user/{user_id}", response_model=Optional[ReviewOut])
def get_review_by_user_endpoint(
    movie_id: str,
    user_id: str,
):
    '''Get the review for a movie by a specific user ID'''
    return svc.get_user_review(movie_id=movie_id, user_id=user_id)


# .. note::
#    Parts of this file comments and basic scaffolding were auto-completed by VS Code.
#    Core logic and subsequent modifications were implemented by the author(s).
