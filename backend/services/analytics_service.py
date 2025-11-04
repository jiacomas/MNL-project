# Reviews service
from __future__ import annotations

import csv
import json
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

# ---------------------------------------------------------------------------
# Data locations (defaults for the real app – tests monkeypatch these)
# ---------------------------------------------------------------------------

BASE_DATA_DIR = Path(os.environ.get("MOVIE_DATA_PATH", "data"))

USERS_FILE = BASE_DATA_DIR / "users" / "users.json"
REVIEWS_FILE = BASE_DATA_DIR / "reviews" / "reviews.json"
BOOKMARKS_FILE = BASE_DATA_DIR / "bookmarks" / "bookmarks.json"
PENALTIES_FILE = BASE_DATA_DIR / "penalties" / "penalties.json"
ITEMS_FILE = BASE_DATA_DIR / "items.json"

EXPORT_DIR = Path("reports") / "exports"
EXPORT_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_list(path: Path) -> List[Dict[str, Any]]:
    """Load a JSON file and always return a list of dicts.

    Handles a few shapes we might see:

    - plain list: [{...}, {...}]
    - dict with "items" key: {"items": [...]}
    - dict with "users" key: {"users": [...]}
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


def compute_stats() -> Dict[str, Any]:
    """Compute platform statistics used by CSV export.

    Returns a dict with:

    {
        "user_counts": {"active": int, "total": int},
        "review_counts": {"reviews": int},
        "bookmarks_count": int,
        "penalties_count": int,
        "top_genres": [{"genre": str, "count": int}, ...],
    }
    """
    users = _load_list(USERS_FILE)
    reviews = _load_list(REVIEWS_FILE)
    bookmarks = _load_list(BOOKMARKS_FILE)
    penalties = _load_list(PENALTIES_FILE)
    items = _load_list(ITEMS_FILE)

    # Active vs total users (treat missing is_locked as active)
    active_users = [u for u in users if not u.get("is_locked", False)]
    user_counts = {"active": len(active_users), "total": len(users)}

    review_counts = {"reviews": len(reviews)}
    bookmarks_count = len(bookmarks)
    penalties_count = len(penalties)

    # Map movies by id so we can count genres from reviews+bookmarks
    movies_by_id: Dict[str, Dict[str, Any]] = {}
    for movie in items:
        movie_id = movie.get("id") or movie.get("movie_id")
        if movie_id:
            movies_by_id[movie_id] = movie

    genre_counter: Counter[str] = Counter()

    def _bump_genres(collection: List[Dict[str, Any]]) -> None:
        for entry in collection:
            movie = movies_by_id.get(entry.get("movie_id"))
            if not movie:
                continue

            # Support both "genres" and "movieGenres"
            raw_genres = movie.get("genres") or movie.get("movieGenres") or []
            for g in raw_genres:
                genre = str(g)
                if genre:
                    genre_counter[genre] += 1

    _bump_genres(reviews)
    _bump_genres(bookmarks)

    top_genres = [
        {"genre": genre, "count": count}
        for genre, count in genre_counter.most_common(10)
    ]

    return {
        "user_counts": user_counts,
        "review_counts": review_counts,
        "bookmarks_count": bookmarks_count,
        "penalties_count": penalties_count,
        "top_genres": top_genres,
    }


def compute_stats_and_write_csv() -> Path:
    """Compute stats and write them to a CSV file in EXPORT_DIR.

    The CSV has a stable schema:

    - Section 1: high-level counts
        metric,value
        user_active,?
        user_total,?
        reviews,?
        bookmarks,?
        penalties,?

    - (blank row)

    - Section 2: top genres
        top_genre_rank,genre,count
        1,Action,12
        2,Drama,8
        ...

    - (blank row)

    - Tail row:
        generated_at,<UTC timestamp>
    """
    stats = compute_stats()
    generated_at = datetime.now(timezone.utc).isoformat()

    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    safe_ts = generated_at.replace(":", "-")
    out_path = EXPORT_DIR / f"platform_stats_{safe_ts}.csv"

    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        # Section 1: counts
        writer.writerow(["metric", "value"])
        writer.writerow(["user_active", stats["user_counts"]["active"]])
        writer.writerow(["user_total", stats["user_counts"]["total"]])
        writer.writerow(["reviews", stats["review_counts"]["reviews"]])
        writer.writerow(["bookmarks", stats["bookmarks_count"]])
        writer.writerow(["penalties", stats["penalties_count"]])
        writer.writerow([])

        # Section 2: top genres
        writer.writerow(["top_genre_rank", "genre", "count"])
        for idx, entry in enumerate(stats["top_genres"], start=1):
            writer.writerow([idx, entry["genre"], entry["count"]])

        writer.writerow([])
        writer.writerow(["generated_at", generated_at])

    return out_path
