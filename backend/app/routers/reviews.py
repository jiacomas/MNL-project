# backend/app/routers/reviews.py
from fastapi import APIRouter, Depends, HTTPException, status, Body, Query
from typing import List, Optional

from app.schemas.reviews import ReviewCreate, ReviewUpdate, ReviewOut
from app.services.reviews_service import ReviewService, InMemoryReviewRepo

router = APIRouter(prefix="/api", tags=["reviews"])

# ---- Dependency wiring (simple) ----
def get_service() -> ReviewService:
    # For development we use in-memory repo.
    # Replace with a DB-backed repository in future.
    # In tests, we'll override this dependency.
    repo = InMemoryReviewRepo()
    return ReviewService(repo)

@router.post("/reviews", response_model=ReviewOut, status_code=status.HTTP_201_CREATED)
def create_review(payload: ReviewCreate, svc: ReviewService = Depends(get_service)):
    try:
        return svc.create_review(payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.put("/reviews/{review_id}", response_model=ReviewOut)
def edit_review(
    review_id: str,
    payload: ReviewUpdate,
    user_id: str = Query(..., description="Author user id issuing the edit"),
    svc: ReviewService = Depends(get_service),
):
    try:
        return svc.edit_review(review_id, user_id, payload)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.delete("/reviews/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_review(
    review_id: str,
    user_id: str = Query(..., description="Author user id issuing the deletion"),
    svc: ReviewService = Depends(get_service),
):
    try:
        svc.delete_review(review_id, user_id)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    return

@router.get("/movies/{movie_id}/reviews", response_model=List[ReviewOut])
def list_reviews(movie_id: str, svc: ReviewService = Depends(get_service)):
    return svc.list_reviews(movie_id)

@router.get("/movies/{movie_id}/reviews/{user_id}", response_model=Optional[ReviewOut])
def get_user_review(movie_id: str, user_id: str, svc: ReviewService = Depends(get_service)):
    return svc.get_user_review(movie_id, user_id)
