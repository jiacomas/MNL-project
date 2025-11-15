from __future__ import annotations

import csv
import json
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from repositories.reviews_repo import CSVReviewRepo

# Reuse repository logic for reading review CSVs
_repo = CSVReviewRepo()

# ---------------------------------------------------------------------------
# JSON helpers for platform-wide stats
# ---------------------------------------------------------------------------

# Default locations – tests monkeypatch these to point at temporary files
DATA_ROOT = Path(os.getenv("MOVIE_DATA_PATH", "data"))

USERS_FILE: Path = DATA_ROOT / "users.json"
REVIEWS_FILE: Path = DATA_ROOT / "reviews.json"
BOOKMARKS_FILE: Path = DATA_ROOT / "bookmarks.json"
PENALTIES_FILE: Path = DATA_ROOT / "penalties.json"
ITEMS_FILE: Path = DATA_ROOT / "items.json"
EXPORT_DIR: Path = DATA_ROOT / "exports"


def _read_json_list(path: Path) -> List[Dict[str, Any]]:
    """Read a JSON file and always return a list of dicts.

    * Missing files -> [].
    * If the JSON root is a dict, it is wrapped in a one-element list.
    * If the JSON has a top-level "items" / "users" list, that list is returned.
    """
    if not path.exists():
        return []

    with path.open(encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        return list(data)

    if isinstance(data, dict):
        if "items" in data and isinstance(data["items"], list):
            return list(data["items"])
        if "users" in data and isinstance(data["users"], list):
            return list(data["users"])

    return [data]


def _compute_top_genres(
    items: Iterable[Dict[str, Any]],
    reviews: Iterable[Dict[str, Any]],
) -> List[Tuple[str, int]]:
    """Return a list of (genre, count) sorted by popularity.

    A movie contributes +1 to each of its genres if it has at least one review.
    """
    # Movie ids that have at least one review
    reviewed_movie_ids = {r.get("movie_id") for r in reviews}

    genre_counts: Counter[str] = Counter()
    for movie in items:
        movie_id = movie.get("id")
        if movie_id not in reviewed_movie_ids:
            continue
        for g in movie.get("genres", []):
            genre_counts[str(g)] += 1

    # Sort by count desc, then genre name asc for deterministic order
    return sorted(
        genre_counts.items(),
        key=lambda gc: (-gc[1], gc[0].lower()),
    )


def compute_stats_and_write_csv() -> Path:
    """Aggregate high-level platform stats and write them to a CSV file.

    The CSV has two logical sections:

    1) Metric summary:

        metric,value
        users_count,2
        user_total,2
        user_active,1
        user_locked,1
        reviews_count,1
        bookmarks_count,1
        penalties_count,1
        generated_at,2025-...

    2) Top genres table (if any genres are present):

        top_genre_rank,genre,count
        1,Action,10
        2,Adventure,7
        ...

    The path to the created CSV file is returned.
    """
    users = _read_json_list(Path(USERS_FILE))
    reviews = _read_json_list(Path(REVIEWS_FILE))
    bookmarks = _read_json_list(Path(BOOKMARKS_FILE))
    penalties = _read_json_list(Path(PENALTIES_FILE))
    items = _read_json_list(Path(ITEMS_FILE))

    total_users = len(users)
    active_users = sum(1 for u in users if not u.get("is_locked"))
    locked_users = sum(1 for u in users if u.get("is_locked"))

    metrics: List[Tuple[str, Any]] = [
        ("users_count", total_users),
        ("user_total", total_users),
        ("user_active", active_users),
        ("user_locked", locked_users),
        ("reviews_count", len(reviews)),
        ("bookmarks_count", len(bookmarks)),
        ("penalties_count", len(penalties)),
    ]

    top_genres = _compute_top_genres(items, reviews)

    # Ensure export directory exists
    export_dir = Path(EXPORT_DIR)
    export_dir.mkdir(parents=True, exist_ok=True)

    out_path = export_dir / f"platform_stats_{int(datetime.now(timezone.utc).timestamp())}.csv"

    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        # Section 1: metrics
        writer.writerow(["metric", "value"])
        for name, value in metrics:
            writer.writerow([name, value])

        # generated_at row
        writer.writerow(
            ["generated_at", datetime.now(timezone.utc).isoformat()],
        )

        # Section 2: top genres, only if we have any
        if top_genres:
            writer.writerow([])  # blank line as separator
            writer.writerow(["top_genre_rank", "genre", "count"])
            for rank, (genre, count) in enumerate(top_genres, start=1):
                writer.writerow([rank, genre, count])

    return out_path


# ---------------------------------------------------------------------------
# Admin review search helpers
# ---------------------------------------------------------------------------


def _discover_movie_root() -> Path:
    """Return the directory that contains per-movie CSV data.

    We reuse the BASE_PATH constant from `repositories.reviews_repo` so that
    tests can control the location via their usual fixtures.
    """
    from repositories import reviews_repo

    base = getattr(reviews_repo, "BASE_PATH", "data/movies")
    return Path(base)


def search_reviews_by_title(
    title_query: str,
    sort_by: str = "date",
    order: str = "desc",
) -> List[Dict[str, Any]]:
    """Search all reviews, filtered by (partial, case-insensitive) movie title.

    Returns a list of dicts with at least:

    * id
    * movie_title
    * rating
    * created_at
    * user_id
    """
    root = _discover_movie_root()
    q = (title_query or "").strip().lower()

    results: List[Dict[str, Any]] = []

    if not root.exists() or not root.is_dir():
        return results

    for movie_dir in sorted(os.listdir(root)):
        # movie_dir is the movie id / title slug
        if q and q not in movie_dir.lower():
            continue

        movie_id = movie_dir

        try:
            reviews, _ = _repo.list_by_movie(movie_id=movie_id, limit=1_000_000)
        except Exception:
            # If a movie has no reviews.csv yet, skip it.
            continue

        for r in reviews:
            created_at = getattr(r, "created_at", None)
            results.append(
                {
                    "id": r.id,
                    "movie_title": movie_id,
                    "rating": r.rating,
                    "created_at": created_at,
                    "user_id": r.user_id,
                }
            )

    reverse = order != "asc"

    def _safe_created_at(row: Dict[str, Any]) -> datetime:
        value = row.get("created_at")
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                pass
        return datetime.min.replace(tzinfo=timezone.utc)

    if sort_by == "rating":
        results.sort(
            key=lambda row: (row.get("rating") or 0, _safe_created_at(row)),
            reverse=reverse,
        )
    else:
        # default: date
        results.sort(
            key=lambda row: (_safe_created_at(row), row.get("rating") or 0),
            reverse=reverse,
        )

    return results


def write_reviews_csv(
    rows: List[Dict[str, Any]],
    out_dir: Optional[Path] = None,
) -> Path:
    """Write review rows (as returned by :func:`search_reviews_by_title`) to CSV.

    If *out_dir* is provided, the file is created inside that directory; otherwise
    an ``exports`` directory next to the movie data is used.

    The CSV schema is:

        id,movie_title,rating,created_at,user_id
    """
    if out_dir is None:
        out_dir = _discover_movie_root() / "exports"
    else:
        out_dir = Path(out_dir)

    out_dir.mkdir(parents=True, exist_ok=True)

    out_path = out_dir / "reviews_export.csv"

    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "movie_title", "rating", "created_at", "user_id"])
        for row in rows:
            created = row.get("created_at")
            if isinstance(created, datetime):
                created_s = created.isoformat()
            else:
                created_s = str(created) if created is not None else ""
            writer.writerow(
                [
                    row.get("id"),
                    row.get("movie_title"),
                    row.get("rating"),
                    created_s,
                    row.get("user_id"),
                ]
            )

    return out_path
