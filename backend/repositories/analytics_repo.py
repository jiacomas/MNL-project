from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Dict, List, Tuple

from backend import settings
from backend.repositories.bookmarks_repo import JSONBookmarkRepo
from backend.repositories.movies_repo import MovieRepository
from backend.repositories.penalties_repo import JSONPenaltyRepository
from backend.repositories.reviews_repo import CSVReviewRepo
from backend.repositories.users_repo import UserRepository

EXPORT_DIR = Path(settings.EXPORT_DIR)


class AnalyticsRepository:
    """Repository for aggregating data for analytics."""

    def __init__(
        self,
        user_repo: UserRepository | None = None,
        movie_repo: MovieRepository | None = None,
        review_repo: CSVReviewRepo | None = None,
        bookmark_repo: JSONBookmarkRepo | None = None,
        penalty_repo: JSONPenaltyRepository | None = None,
        export_dir: Path = EXPORT_DIR,
    ):
        self.user_repo = user_repo or UserRepository()
        self.movie_repo = movie_repo or MovieRepository()
        self.review_repo = review_repo or CSVReviewRepo()
        self.bookmark_repo = bookmark_repo or JSONBookmarkRepo()
        self.penalty_repo = penalty_repo or JSONPenaltyRepository()
        self.export_dir = export_dir

    def get_user_metrics(self) -> Tuple[int, int, int]:
        """Return (total, active, locked) user counts."""
        users = self.user_repo.users  # Accessing loaded users directly
        total = len(users)
        active = sum(1 for u in users if not u.is_locked)
        locked = sum(1 for u in users if u.is_locked)
        return total, active, locked

    def get_counts(self) -> Tuple[int, int, int]:
        """Return counts for reviews, bookmarks, and penalties."""
        # This might be expensive if lists are huge, but matches current logic
        # For reviews, we need a way to count all without loading everything if possible,
        # but current logic loads all.
        reviews = self.review_repo.get_all_reviews_flat()
        bookmarks = self.bookmark_repo.list_all()
        penalties = self.penalty_repo._load()  # Accessing raw load for count

        return len(reviews), len(bookmarks), len(penalties)

    def get_top_genres(self) -> List[Tuple[str, int]]:
        """Compute top genres based on reviewed movies."""
        from collections import Counter

        reviews = self.review_repo.get_all_reviews_flat()
        movies, _ = self.movie_repo.get_all(limit=10000)  # Get all movies

        genres_by_item = {m.movie_id: m.movieGenres for m in movies}
        genre_counter: Counter[str] = Counter()

        for review in reviews:
            # review is ReviewOut object
            movie_genres = genres_by_item.get(review.movie_id)
            if not movie_genres:
                continue

            # Handle pipe or comma separated
            if "|" in movie_genres:
                parts = [p.strip() for p in movie_genres.split("|")]
            else:
                parts = [p.strip() for p in movie_genres.split(",")]

            for genre in parts:
                if genre:
                    genre_counter[genre] += 1

        return list(genre_counter.most_common())

    def write_stats_csv(
        self,
        metrics: List[Tuple[str, str]],
        top_genres: List[Tuple[str, int]],
        generated_at: str,
    ) -> Path:
        """Write stats to CSV."""
        self.export_dir.mkdir(parents=True, exist_ok=True)
        out_path = self.export_dir / "analytics_export.csv"

        with out_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            # Metrics section
            writer.writerow(["metric", "value"])
            for name, value in metrics:
                writer.writerow([name, value])

            # Top-genres section header
            writer.writerow(["top_genre_rank", "genre", "count"])
            for idx, (genre, count) in enumerate(top_genres, start=1):
                writer.writerow([idx, genre, count])

            # Footer row
            writer.writerow(["generated_at", generated_at])

        return out_path

    def write_reviews_csv(
        self, rows: List[Dict[str, Any]], filename: str | None = None
    ) -> Path:
        """Write review search results to CSV."""
        if filename:
            out_path = self.export_dir / filename
        else:
            out_path = self.export_dir / "reviews_export.csv"

        out_path.parent.mkdir(parents=True, exist_ok=True)

        with out_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "review_id",
                    "movie_title",
                    "username",
                    "user_id",
                    "rating",
                    "title_review",
                    "comment",
                    "created_at",
                    "updated_at",
                    "usefulness",
                    "total_votes",
                ]
            )

            for row in rows:
                # Format dates
                created_at = row.get("created_at")
                if hasattr(created_at, "isoformat"):
                    created_at = created_at.isoformat()

                updated_at = row.get("updated_at")
                if hasattr(updated_at, "isoformat"):
                    updated_at = updated_at.isoformat()

                writer.writerow(
                    [
                        row.get("review_id"),
                        row.get("movie_title"),
                        row.get("username"),
                        row.get("user_id"),
                        row.get("rating"),
                        row.get("title_review"),
                        row.get("comment"),
                        created_at,
                        updated_at,
                        row.get("usefulness"),
                        row.get("total_votes"),
                    ]
                )

        return out_path
