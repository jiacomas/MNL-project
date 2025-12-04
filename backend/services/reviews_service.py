from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status

from backend.repositories.reviews_repo import CSVReviewRepo
from backend.schemas.reviews import ReviewCreate, ReviewOut, ReviewUpdate


class ReviewsService:
    def __init__(self, repo: CSVReviewRepo):
        self.repo = repo

    # Helpers
    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def _new_id(self) -> str:
        # Let service generate UUIDv4, repo stays agnostic
        return str(uuid.uuid4())

    def _get_review_or_404(self, movie_name: str, review_id: str) -> ReviewOut:
        review = self.repo.get_review_by_id(movie_name, review_id)
        if review is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Review not found."
            )
        return review

    # CREATE
    def create_review(
        self,
        movie_name: str,
        payload: ReviewCreate,
        username: str,
    ) -> ReviewOut:
        # 1 review per user per movie
        if self.repo.get_review_by_user(movie_name, username):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User already reviewed this movie.",
            )

        now = self._now()

        out = ReviewOut(
            review_id=self._new_id(),
            movie_name=movie_name,
            username=username,
            rating=payload.rating,
            title_review=(payload.title_review or "").strip(),
            comment=payload.comment,
            created_at=now,
            updated_at=now,
            usefulness=0,
            total_votes=0,
        )

        return self.repo.create(out)

    # UPDATE
    def update_review(
        self,
        movie_name: str,
        review_id: str,
        payload: ReviewUpdate,
        username: str,
        is_admin: bool = False,
    ) -> ReviewOut:
        existing = self._get_review_or_404(movie_name, review_id)

        # permission check
        if not is_admin and existing.username != username:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this review.",
            )

        updated = existing.model_copy(
            update={
                "rating": (
                    payload.rating if payload.rating is not None else existing.rating
                ),
                "title_review": (
                    payload.title_review.strip()
                    if payload.title_review is not None
                    else existing.title_review
                ),
                "comment": (
                    payload.comment if payload.comment is not None else existing.comment
                ),
                "updated_at": self._now(),
            }
        )

        return self.repo.update(updated)

    # DELETE
    def delete_review(
        self,
        movie_name: str,
        review_id: str,
        username: str,
        is_admin: bool = False,
    ) -> None:
        existing = self._get_review_or_404(movie_name, review_id)

        if not is_admin and existing.username != username:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this review.",
            )

        self.repo.delete(movie_name, review_id)

    # LIST
    def list_reviews(
        self,
        movie_name: str,
        limit: int = 50,
        cursor: int | None = 0,
        min_rating: int | None = None,
    ):
        return self.repo.list_by_movie(
            movie_name,
            limit=limit,
            cursor=cursor,
            min_rating=min_rating,
        )

    # GET
    def get_review(self, movie_name: str, review_id: str) -> ReviewOut:
        return self._get_review_or_404(movie_name, review_id)

    def get_review_by_user(self, movie_name: str, username: str) -> ReviewOut | None:
        return self.repo.get_review_by_user(movie_name, username)
