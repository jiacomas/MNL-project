from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

from backend.repositories.analytics_repo import AnalyticsRepository
from backend.repositories.reviews_repo import CSVReviewRepo

# Instantiate repositories
_analytics_repo = AnalyticsRepository()
_review_repo = (
    CSVReviewRepo()
)  # Still used for search helpers if needed, or we can move search to repo


def compute_stats() -> Tuple[List[Tuple[str, str]], List[Tuple[str, int]]]:
    """Compute platform stats."""
    user_total, user_active, user_locked = _analytics_repo.get_user_metrics()
    reviews_count, bookmarks_count, penalties_count = _analytics_repo.get_counts()

    metrics = [
        ("users_count", str(user_total)),
        ("user_total", str(user_total)),
        ("user_active", str(user_active)),
        ("user_locked", str(user_locked)),
        ("reviews_count", str(reviews_count)),
        ("bookmarks_count", str(bookmarks_count)),
        ("penalties_count", str(penalties_count)),
    ]

    top_genres = _analytics_repo.get_top_genres()
    return metrics, top_genres


def compute_stats_and_write_csv() -> Path:
    """Compute platform stats and write them to a CSV file."""
    metrics, top_genres = compute_stats()
    now = datetime.now(timezone.utc)
    return _analytics_repo.write_stats_csv(metrics, top_genres, now.isoformat())


# ---------------------------------------------------------------------------
# Review search helpers used by the admin analytics endpoints
# ---------------------------------------------------------------------------


def search_reviews_by_title(
    title_query: str,
    sort_by: str = "date",
    order: str = "desc",
) -> List[Dict[str, Any]]:
    """Search reviews by (partial, case-insensitive) movie title."""
    # This logic is a bit complex to move entirely to repo without changing signatures significantly
    # because it involves "discovering" movies matching a title and then loading their reviews.
    # We can keep the orchestration here but use repos for data access.

    # We need to find movies that match the title.
    # MovieRepository has search, but it returns MovieOut objects.
    # We can use that.
    from backend.repositories.movies_repo import MovieRepository

    movie_repo = MovieRepository()

    # Search movies by title
    movies, _ = movie_repo.search(title=title_query, limit=1000)

    rows: List[Dict[str, Any]] = []
    for movie in movies:
        # Get reviews for each movie
        reviews, _ = _review_repo.list_by_movie(movie.movie_id, limit=10000)
        for review in reviews:
            rows.append(
                {
                    "id": review.id,
                    "movie_title": movie.movie_id,  # The original code used movie_id as title in some places or directory name
                    "rating": review.rating,
                    "created_at": review.created_at,
                    "user_id": review.user_id,
                }
            )

    # Sort
    reverse = order != "asc"

    def _key_by_rating(x):
        return x.get("rating") or 0

    def _key_by_created_at(x):
        return x.get("created_at") or datetime.min.replace(tzinfo=timezone.utc)

    if sort_by == "rating":
        key = _key_by_rating
    else:
        key = _key_by_created_at

    rows.sort(key=key, reverse=reverse)
    return rows


def write_reviews_csv(
    rows: List[Dict[str, Any]],
    out_path: Path | None = None,
    filename: str | None = None,
) -> Path:
    """Write search results to a CSV for admin download."""
    # If out_path is provided, we might need to handle it, but repo expects filename or uses default in export dir.
    # The original code handled out_path flexibility.
    # Let's try to map it.

    if out_path:
        # If out_path is a directory, use filename or default
        if out_path.is_dir():
            fname = filename or "reviews_export.csv"
            final_path = out_path / fname
        else:
            final_path = out_path

        # We can't easily force repo to write to arbitrary path if it's locked to export_dir
        # But we can just write it here using the repo's logic or just use the repo's method if it allows path override?
        # My new repo method takes filename and writes to export_dir.
        # To maintain exact backward compatibility with tests that might pass a full path:
        # We might need to adjust the repo or just handle it here.

        # Actually, let's just use the repo's method but we might need to be careful about the path.
        # If the test passes a tmp_path, we want to write there.
        # The repo uses self.export_dir.
        # We can temporarily override export_dir or just instantiate a new repo with that dir.

        repo = AnalyticsRepository(export_dir=final_path.parent)
        return repo.write_reviews_csv(rows, filename=final_path.name)

    return _analytics_repo.write_reviews_csv(rows, filename=filename)
