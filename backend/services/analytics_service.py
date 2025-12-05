from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Tuple

from backend.repositories.analytics_repo import AnalyticsRepository
from backend.repositories.reviews_repo import CSVReviewRepo
from backend.utils.datetime_utils import now_utc, to_iso_string


class AnalyticsService:
    def __init__(
        self,
        analytics_repo: AnalyticsRepository | None = None,
        review_repo: CSVReviewRepo | None = None,
    ):
        self.analytics_repo = analytics_repo or AnalyticsRepository()
        self.review_repo = review_repo or CSVReviewRepo()

    def compute_stats(self) -> Tuple[List[Tuple[str, str]], List[Tuple[str, int]]]:
        """Compute platform stats."""
        user_total, user_active, user_locked = self.analytics_repo.get_user_metrics()
        reviews_count, bookmarks_count, penalties_count = (
            self.analytics_repo.get_counts()
        )

        metrics = [
            ("users_count", str(user_total)),
            ("user_total", str(user_total)),
            ("user_active", str(user_active)),
            ("user_locked", str(user_locked)),
            ("reviews_count", str(reviews_count)),
            ("bookmarks_count", str(bookmarks_count)),
            ("penalties_count", str(penalties_count)),
        ]

        top_genres = self.analytics_repo.get_top_genres()
        return metrics, top_genres

    def compute_stats_and_write_csv(self) -> Path:
        """Compute platform stats and write them to a CSV file."""
        metrics, top_genres = self.compute_stats()
        now = now_utc()
        return self.analytics_repo.write_stats_csv(
            metrics, top_genres, to_iso_string(now)
        )

    def search_reviews_by_title(
        self,
        title_query: str,
        sort_by: str = "date",
        order: str = "desc",
    ) -> List[Dict[str, Any]]:
        """Search reviews by (partial, case-insensitive) movie title."""
        from backend.repositories.movies_repo import MovieRepository

        movie_repo = MovieRepository()

        movies, _ = movie_repo.search(title=title_query, limit=1000)

        rows: List[Dict[str, Any]] = []
        for movie in movies:
            reviews, _ = self.review_repo.list_by_movie(movie.title, limit=10000)
            for review in reviews:
                rows.append(
                    {
                        "id": review.id,
                        "movie_title": movie.movie_id,
                        "rating": review.rating,
                        "created_at": review.created_at,
                        "user_id": review.user_id,
                    }
                )

        reverse = order != "asc"
        if sort_by == "rating":

            def key(x):
                return x.get("rating") or 0

        else:

            def key(x):
                # created_at may be ISO string or datetime; rely on raw value
                return x.get("created_at")

        rows.sort(key=key, reverse=reverse)
        return rows

    def write_reviews_csv(
        self,
        rows: List[Dict[str, Any]],
        out_path: Path | None = None,
        filename: str | None = None,
    ) -> Path:
        """Write search results to a CSV for admin download."""
        if out_path:
            if out_path.is_dir():
                fname = filename or "reviews_export.csv"
                final_path = out_path / fname
            else:
                final_path = out_path

            # Use a temporary repo instance pointing to the custom dir
            repo = AnalyticsRepository(export_dir=final_path.parent)
            return repo.write_reviews_csv(rows, filename=final_path.name)

        return self.analytics_repo.write_reviews_csv(rows, filename=filename)


# Singleton instance
analytics_service = AnalyticsService()
