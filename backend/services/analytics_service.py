from __future__ import annotations

import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

# ---------------------------------------------------------------------------
# File locations (tests monkeypatch these)
# ---------------------------------------------------------------------------

# Base directory for movie/platform data; GitHub Actions sets MOVIE_DATA_PATH
MOVIE_DATA_PATH = Path(os.getenv("MOVIE_DATA_PATH", "data/movies"))

USERS_FILE = MOVIE_DATA_PATH / "users.json"
REVIEWS_FILE = MOVIE_DATA_PATH / "reviews.json"
BOOKMARKS_FILE = MOVIE_DATA_PATH / "bookmarks.json"
PENALTIES_FILE = MOVIE_DATA_PATH / "penalties.json"
ITEMS_FILE = MOVIE_DATA_PATH / "items.json"
EXPORT_DIR = MOVIE_DATA_PATH / "exports"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_json_list(path: Path) -> List[Dict[str, Any]]:
    """Load a JSON file and always return a list of dicts.

    Handles shapes like:
    - [] / [{...}]
    - {"items": [...]}, {"users": [...]}, etc.
    - single dict -> wrapped in a list
    - missing file -> []
    """
    if not path.exists():
        return []

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        return list(data)

    if isinstance(data, dict):
        for key in ("items", "users", "reviews", "bookmarks", "penalties"):
            value = data.get(key)
            if isinstance(value, list):
                return list(value)
        return [data]

    return []


def _top_genres_from_bookmarks(
    items: List[Dict[str, Any]],
    bookmarks: List[Dict[str, Any]],
    limit: int = 3,
) -> List[Dict[str, Any]]:
    """Compute top genres by bookmark count."""
    # Map item_id -> list[str] genres
    item_genres: Dict[str, List[str]] = {}
    for item in items:
        item_id = str(item.get("id"))
        genres = item.get("genres") or []
        if isinstance(genres, str):
            genres = [g.strip() for g in genres.split(",") if g.strip()]
        item_genres[item_id] = list(genres)

    genre_counts: Dict[str, int] = {}
    for bm in bookmarks:
        item_id = str(bm.get("item_id") or bm.get("movie_id"))
        for g in item_genres.get(item_id, []):
            genre_counts[g] = genre_counts.get(g, 0) + 1

    sorted_genres = sorted(
        genre_counts.items(),
        key=lambda kv: (-kv[1], kv[0]),
    )

    top: List[Dict[str, Any]] = []
    for name, count in sorted_genres[:limit]:
        top.append({"genre": name, "count": count})
    return top


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def compute_stats_and_write_csv() -> Path:
    """Compute platform stats and write them to a CSV file.

    CSV layout expected by tests:

        metric,value
        users_count,<int>
        user_total,<int>
        user_active,<int>
        user_locked,<int>
        reviews_count,<int>
        bookmarks_count,<int>
        penalties_count,<int>
        generated_at,<ISO UTC>

        top_genre_rank,genre,count
        1,<name>,<count>
        2,<name>,<count>
        ...
    """
    users = _load_json_list(USERS_FILE)
    reviews = _load_json_list(REVIEWS_FILE)
    bookmarks = _load_json_list(BOOKMARKS_FILE)
    penalties = _load_json_list(PENALTIES_FILE)
    items = _load_json_list(ITEMS_FILE)

    users_count = len(users)
    user_locked = sum(1 for u in users if bool(u.get("is_locked")))
    user_active = users_count - user_locked

    reviews_count = len(reviews)
    bookmarks_count = len(bookmarks)
    penalties_count = len(penalties)

    top_genres = _top_genres_from_bookmarks(items, bookmarks, limit=3)

    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = EXPORT_DIR / "platform_stats.csv"
    generated_at = datetime.now(timezone.utc).isoformat()

    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        # --- metrics section ---
        writer.writerow(["metric", "value"])
        writer.writerow(["users_count", users_count])
        writer.writerow(["user_total", users_count])  # test checks for this
        writer.writerow(["user_active", user_active])
        writer.writerow(["user_locked", user_locked])
        writer.writerow(["reviews_count", reviews_count])
        writer.writerow(["bookmarks_count", bookmarks_count])
        writer.writerow(["penalties_count", penalties_count])
        writer.writerow(["generated_at", generated_at])

        # blank line between sections (nice for humans; tests don't mind)
        writer.writerow([])

        # --- top genres section ---
        writer.writerow(["top_genre_rank", "genre", "count"])
        for idx, tg in enumerate(top_genres, start=1):
            writer.writerow([idx, tg["genre"], tg["count"]])

    return out_path
