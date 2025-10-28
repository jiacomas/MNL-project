# Reviews service
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional, List

from fastapi import HTTPException, status

from app.schemas.reviews import ReviewCreate, ReviewUpdate, ReviewOut
from app.repositories.reviews_repo import CSVReviewRepo

_repo = CSVReviewRepo()

def create_review(payload: ReviewCreate) -> ReviewOut:
    '''Create a new review (one per user per movie)'''
    existing = _repo.get_by_user(payload.movie_id, payload.user_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User has already reviewed this movie. Use update instead."
        )
    
    now = datetime.now(timezone.utc)
    review = ReviewOut(
        id=str(uuid.uuid4()),
        user_id=payload.user_id,
        movie_id=payload.movie_id,
        rating=payload.rating,
        comment=payload.comment,
        created_at=now,
        updated_at=now
    )
    return _repo.create(review)

def list_reviews(
    movie_id: str,
    limit: int = 50,
    cursor: Optional[int] = None,
    min_rating: Optional[int] = None,
) -> tuple[List[ReviewOut], Optional[int]]:
    '''List reviews for a movie with pagination and optional filters.'''
    return _repo.list_by_movie(movie_id, limit=limit, cursor=cursor, min_rating=min_rating)

def update_review(
    movie_id: str, 
    review_id: str, 
    current_user_id: str, 
    payload: ReviewUpdate
) -> ReviewOut:
    '''Update an existing review only by user for a movie.'''
    existing = _repo.get_by_id(movie_id, review_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found."
        )
    if existing.user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this review."
        )
    
    updated = ReviewOut(
        **existing.model_dump(exclude={"rating", "comment", "updated_at"}),
        rating=payload.rating if payload.rating is not None else existing.rating,
        comment=payload.comment if payload.comment is not None else existing.comment,
        updated_at=datetime.now(timezone.utc)
    )
    return _repo.update(updated)

def delete_review(
    movie_id: str, 
    review_id: str, 
    current_user_id: str
) -> None:
    '''Allowed if:
      - current user is the author, OR
      TODO: - current user is admin (by config)
    '''
    existing = _repo.get_by_id(movie_id, review_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found."
        )
    if existing.user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this review."
        )
    
    _repo.delete(movie_id, review_id)
    
def get_user_review(movie_id: str, user_id: str) -> Optional[ReviewOut]:
    '''Return a user's own review for a movie, or None if not found.'''
    return _repo.get_by_user(movie_id, user_id)

# .. note::
#    Parts of this file comments and basic scaffolding were auto-completed by VS Code.
#    Core logic and subsequent modifications were implemented by the author(s).
