# reviews router
from __future__ import annotations

from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, Path, Query, status

from app.schemas.reviews import ReviewCreate, ReviewUpdate, ReviewOut
from app.services import reviews_service as svc

# TODO: import auth and get current user from the app dependency file
# Build a temporary fallback for local dev without auth
try:
    from app.deps import get_current_user_id
except ImportError:
    def get_current_user() -> str:
        return "demo_user"
    
router = APIRouter(prefix="/api/reviews", tags=["reviews"])

@router.get("/movie/{movie_id}", response_model=Dict[str, Any])
def list_reviews_endpoint(
    movie_id: str = Path(..., description="Movie ID(directory name under data/movies)"),
    limit: int = Query(50, ge=1, le=200, description="Max number of reviews to return"),
    cursor: Optional[int] = Query(None, description="Pagination cursor"),
    min_rating: Optional[int] = Query(None, ge=1, le=10, description="Minimum rating filter"),
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
def create_review_endpoint(payload: ReviewCreate):
    '''Create a new review for a movie by the current user
    TODO: In real app, inject current_user_id from the auth'''
    # current_user_id = Depends(get_current_user_id)
    # payload.user_id = current_user_id
    return svc.create_review(payload)

@router.patch("/movie/{movie_id}/{review_id}", response_model=ReviewOut)
def update_review_endpoint(
    movie_id: str,
    review_id: str,
    payload: ReviewUpdate,
    current_user_id: str = Depends(get_current_user_id),
):
    '''Update an existing review by the current user'''
    return svc.update_review(
        movie_id=movie_id,
        review_id=review_id,
        current_user_id=current_user_id,
        payload=payload,
    )

@router.delete("/movie/{movie_id}/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_review_endpoint(
    movie_id: str,
    review_id: str,
    current_user_id: str = Depends(get_current_user_id),
):
    '''Delete an existing review by the current user or admin
    TODO: In real app, check if current user is admin'''
    svc.delete_review(
        movie_id=movie_id,
        review_id=review_id,
        current_user_id=current_user_id,
    )
    return None

@router.get("/movie/{movie_id}/me", response_model=Optional[ReviewOut])
def get_my_review_endpoint(
    movie_id: str,
    current_user_id: str = Depends(get_current_user_id), # only depends on current_user_id
):
    '''Get the review for a movie by the currently authenticated user'''
    # Use current_user_id
    return svc.get_user_review(movie_id=movie_id, user_id=current_user_id)

# .. note::
#    Parts of this file comments and basic scaffolding were auto-completed by VS Code.
#    Core logic and subsequent modifications were implemented by the author(s).
