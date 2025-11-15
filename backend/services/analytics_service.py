from __future__ import annotations

import csv
import json
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List

from repositories.reviews_repo import CSVReviewRepo

# Shared review repository (for reading review CSVs)
_repo = CSVReviewRepo()

# ---------------------------------------------------------------------------
# File locations for analytics JSON data
# These are patched in tests with monkeypatch.setattr(...)
# ---------------------------------------------------------------------------

USERS_FILE: Path = Path(os.environ.get("USERS_FILE", "data/users.json"))
REVIEWS_FILE: Path = Path(os.environ.get("REVIEWS_FILE", "data/reviews.json"))
BOOKMARKS_FILE: Path = Path(os.environ.get("BOOKMARKS_FILE", "data/bookmarks.json"))
PENALTIES_FILE: Path = Path(os.environ.get("PENALTIES_FILE", "data/penalties.json"))
ITEMS_FILE: Path = Path(os.environ.get("ITEMS_FILE", "data/items.json"))
EXPORT_DIR: Path = Path(os.environ.get("EXPORT_DIR", "data/exports"))


# ---------------------------------------------------------------------------
# JSON helpers + core stats
# ---------------------------------------------------------------------------


def _read_json_list(path: Path) -> List[Dict[str, Any]]:
    """Read a JSON file and always return a list of dicts.

    The test suite writes simple JSON arrays; this helper also tolerates
    slightly different shapes (single object, or dicts with "items"/"users").
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

    # Fallback – wrap a single object
    return [data]


def compute_stats_and_write_csv() -> Path:
    """Compute platform stats and write them to a CSV file.

    Layout (matches the tests):

    - First line: "metric,value"
    - Metric rows (users, reviews, bookmarks, penalties, etc.)
    - Header row for top genres: "top_genre_rank,genre,count"
    - One row per top genre
    - Final row: "generated_at,<ISO-8601 timestamp>"
    """
    users = _read_json_list(USERS_FILE)
    reviews = _read_json_list(REVIEWS_FILE)
    bookmarks = _read_json_list(BOOKMARKS_FILE)
    penalties = _read_json_list(PENALTIES_FILE)
    items = _read_json_list(ITEMS_FILE)

    # Basic user / activity counts
    user_total = len(users)
    user_active = sum(1 for u in users if not u.get("is_locked"))
    user_locked = sum(1 for u in users if u.get("is_locked"))

    reviews_count = len(reviews)
    bookmarks_count = len(bookmarks)
    penalties_count = len(penalties)

    metrics = [
        ("users_count", str(user_total)),
        ("user_total", str(user_total)),
        ("user_active", str(user_active)),
        ("user_locked", str(user_locked)),
        ("reviews_count", str(reviews_count)),
        ("bookmarks_count", str(bookmarks_count)),
        ("penalties_count", str(penalties_count)),
    ]

    # Top genres: count how often genres appear for reviewed movies
    genres_by_item = {item.get("id"): item.get("genres", []) for item in items}
    genre_counter: Counter[str] = Counter()

    for r in reviews:
        movie_id = r.get("movie_id")
        for g in genres_by_item.get(movie_id, []):
            if g:
                genre_counter[g] += 1

    top_genres = list(genre_counter.most_common())

    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = EXPORT_DIR / "analytics_export.csv"

    now = datetime.now(timezone.utc)

    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        # Metrics section
        writer.writerow(["metric", "value"])
        for name, value in metrics:
            writer.writerow([name, value])

        # Top-genres section header that the test checks for
        writer.writerow(["top_genre_rank", "genre", "count"])
        for idx, (genre, count) in enumerate(top_genres, start=1):
            writer.writerow([idx, genre, count])

        # Footer row with generation timestamp
        writer.writerow(["generated_at", now.isoformat()])

    return out_path


# ---------------------------------------------------------------------------
# Review search helpers used by the admin analytics endpoints
# ---------------------------------------------------------------------------


def _discover_movie_root() -> str:
    """Return the directory where per-movie review CSVs live."""
    # The project normally uses MOVIE_DATA_PATH; fall back to data/movies.
    env_root = os.environ.get("MOVIE_DATA_PATH")
    if env_root:
        return env_root
    return "data/movies"


def _iter_matching_movie_ids(root: str, normalized_q: str) -> Iterable[str]:
    """Yield movie ids under *root* whose folder name matches the query."""
    if not os.path.isdir(root):
        return []

    for entry in sorted(os.listdir(root)):
        if normalized_q and normalized_q not in entry.lower():
            continue
        yield entry


def _load_review_rows_for_movie(movie_id: str) -> List[Dict[str, Any]]:
    """Return review rows for a single movie as plain dicts.

    Any problems reading the CSV for a movie are treated as “no data”.
    """
    try:
        reviews, _ = _repo.list_by_movie(movie_id=movie_id, limit=1_000_000, cursor=0)
    except Exception:
        return []

    rows: List[Dict[str, Any]] = []
    for r in reviews:
        rows.append(
            {
                "id": r.id,
                "movie_title": movie_id,
                "rating": r.rating,
                "created_at": r.created_at,
                "user_id": r.user_id,
            }
        )
    return rows


def _sort_review_rows(
    rows: List[Dict[str, Any]],
    sort_by: str,
    order: str,
) -> List[Dict[str, Any]]:
    """Sort review rows by rating or created_at according to the tests."""
    reverse = order != "asc"
    if sort_by == "rating":
        rows.sort(key=lambda x: (x.get("rating") or 0), reverse=reverse)
    else:
        rows.sort(key=lambda x: x.get("created_at") or 0, reverse=reverse)
    return rows


def search_reviews_by_title(
    title_query: str,
    sort_by: str = "date",
    order: str = "desc",
) -> List[Dict[str, Any]]:
    """Search reviews by (partial, case-insensitive) movie title.

    Returns a list of dicts with keys:
    id, movie_title, rating, created_at, user_id.

    Behaviour matches the admin analytics tests:
    - substring, case-insensitive matching on folder / movie id
    - optional sorting by date or rating
    """
    root = _discover_movie_root()
    normalized_q = (title_query or "").strip().lower()

    rows: List[Dict[str, Any]] = []

    for movie_id in _iter_matching_movie_ids(root, normalized_q):
        rows.extend(_load_review_rows_for_movie(movie_id))

    return _sort_review_rows(rows, sort_by, order)


def write_reviews_csv(rows: List[Dict[str, Any]], out_path: Path) -> Path:
    """Write search results to a CSV for admin download."""
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", newline="", encoding="utf-8") as f:
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
