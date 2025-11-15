# Analytics service
from __future__ import annotations

import csv
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status

from backend.repositories.reviews_repo import CSVReviewRepo
from backend.schemas.reviews import ReviewCreate, ReviewOut, ReviewUpdate

_repo = CSVReviewRepo()


def create_review(payload: ReviewCreate) -> ReviewOut:
    """Create a new review (one per user per movie)."""
    existing = _repo.get_by_user(payload.movie_id, payload.user_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User has already reviewed this movie. Use update instead.",
        )

    now = datetime.now(timezone.utc)
    review = ReviewOut(
        id=str(uuid.uuid4()),
        user_id=payload.user_id,
        movie_id=payload.movie_id,
        rating=payload.rating,
        comment=payload.comment,
        created_at=now,
        updated_at=now,
    )
    return _repo.create(review)


def list_reviews(
    movie_id: str,
    limit: int = 50,
    cursor: Optional[int] = None,
    min_rating: Optional[int] = None,
) -> tuple[List[ReviewOut], Optional[int]]:
    """List reviews for a movie with pagination and optional filters."""
    return _repo.list_by_movie(
        movie_id,
        limit=limit,
        cursor=cursor,
        min_rating=min_rating,
    )


def update_review(
    movie_id: str,
    review_id: str,
    current_user_id: str,
    payload: ReviewUpdate,
) -> ReviewOut:
    """Update an existing review; only the author may update."""
    existing = _repo.get_by_id(movie_id, review_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found.",
        )

    if existing.user_id != current_user_id:
        # Review exists but belongs to someone else -> 403
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this review.",
        )

    updated = ReviewOut(
        # keep immutable fields from existing
        **existing.model_dump(exclude={"rating", "comment", "updated_at"}),
        rating=payload.rating if payload.rating is not None else existing.rating,
        comment=payload.comment if payload.comment is not None else existing.comment,
        updated_at=datetime.now(timezone.utc),
    )
    return _repo.update(updated)


def delete_review(movie_id: str, review_id: str, current_user_id: str) -> None:
    """Delete a review.

    Rules (what the tests expect):
    * If the review does not exist -> 404.
    * If the review exists but current_user_id is not the author -> 403.
    * If the review exists and user is the author -> delete it.
    """
    if not path.exists():
        return []

    with path.open(encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        return list(data)

    if isinstance(data, dict):
        if "items" in data:
            return list(data["items"])
        if "users" in data:
            return list(data["users"])

    # Fallback – wrap in list if it’s a single object
    return [data]


# ---------------------------------------------------------------------------
# Core stats + CSV export
# ---------------------------------------------------------------------------


def _discover_movie_root() -> str:
    """Discover where movie data lives on disk.

    Tries the repo's configured BASE_PATH first (relative to working dir),
    then falls back to the sibling `../data` directory commonly used in this repo.
    """
    # try repo default
    try:
        from repositories import reviews_repo

        candidate = reviews_repo.BASE_PATH
    except Exception:
        candidate = "data/movies"

    # possible absolute/relative locations to check
    candidates = [candidate]
    # relative to this services package -> backend/services/../data
    services_dir = Path(__file__).resolve().parent
    candidates.append(str((services_dir.parent / "data")))
    # also try working directory base
    candidates.append(str(Path.cwd() / candidate))

    for p in candidates:
        if os.path.exists(p) and os.path.isdir(p):
            return p

    # default to candidate even if missing (caller should handle missing)
    return candidate


def search_reviews_by_title(
    title_query: str,
    sort_by: str = "date",
    order: str = "desc",
) -> List[Dict[str, Any]]:
    """Search reviews by movie title (case-insensitive).

    Returns a list of dicts with fields: id, movie_title, rating, created_at, user_id.
    sort_by: 'date' or 'rating'. order: 'asc' or 'desc'.
    """
    root = _discover_movie_root()
    normalized_q = (title_query or "").strip().lower()

    results: List[Dict[str, Any]] = []

    if not os.path.isdir(root):
        return results

    for entry in sorted(os.listdir(root)):
        # entry is movie directory name
        if normalized_q and normalized_q not in entry.lower():
            continue

        movie_id = entry
        # pull all reviews for the movie (pass large limit to get all rows)
        try:
            reviews, _ = _repo.list_by_movie(movie_id=movie_id, limit=1000000, cursor=0)
        except Exception:
            # skip movies with missing/invalid CSV
            continue

        for r in reviews:
            results.append(
                {
                    "id": r.id,
                    "movie_title": movie_id,
                    "rating": r.rating,
                    "created_at": r.created_at,
                    "user_id": r.user_id,
                }
            )

    # sort
    reverse = order != "asc"
    if sort_by == "rating":
        results.sort(key=lambda x: (x.get("rating") or 0), reverse=reverse)
    else:
        # default: sort by date
        results.sort(key=lambda x: x.get("created_at") or 0, reverse=reverse)

    return results


def write_reviews_csv(
    rows: List[Dict[str, Any]], filename: Optional[str] = None
) -> Path:
    """Write given review rows to a CSV file and return the Path.

    The CSV will include headers: id,movie_title,rating,created_at,user_id
    """
    out_dir = Path(_discover_movie_root()) / "exports"
    out_dir.mkdir(parents=True, exist_ok=True)
    if filename:
        out_path = out_dir / filename
    else:
        out_path = (
            out_dir
            / f"reviews_export_{int(datetime.now(timezone.utc).timestamp())}.csv"
        )

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "movie_title", "rating", "created_at", "user_id"])
        for r in rows:
            created = r.get("created_at")
            if isinstance(created, datetime):
                created_s = created.isoformat()
            else:
                created_s = str(created)
            writer.writerow(
                [
                    r.get("id"),
                    r.get("movie_title"),
                    r.get("rating"),
                    created_s,
                    r.get("user_id"),
                ]
            )

    return out_path


# .. note::
#    Parts of this file comments and basic scaffolding were auto-completed by VS Code.
#    Core logic and subsequent modifications were implemented by the author(s).
