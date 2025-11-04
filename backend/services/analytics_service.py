"""
Analytics / export service.

Computes platform statistics (users, items/movies, etc.)
and writes them to a CSV file for admins to download.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, UTC
from pathlib import Path
from typing import Dict, Any, List


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
# This file lives in backend/app/services/
# parents[0] -> services, parents[1] -> app, parents[2] -> backend, parents[3] -> project root
SERVICES_DIR = Path(__file__).resolve().parent
APP_DIR = SERVICES_DIR.parent
BACKEND_DIR = APP_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent

APP_DATA_DIR = APP_DIR / "data"
ROOT_DATA_DIR = PROJECT_ROOT / "data"

USERS_FILE = ROOT_DATA_DIR / "users" / "users.json"
ITEMS_FILE = APP_DATA_DIR / "items.json"

# Optional future files – if missing we just return 0
REVIEWS_FILE = ROOT_DATA_DIR / "reviews" / "reviews.json"
BOOKMARKS_FILE = ROOT_DATA_DIR / "bookmarks" / "bookmarks.json"
PENALTIES_FILE = ROOT_DATA_DIR / "penalties" / "penalties.json"

EXPORT_DIR = ROOT_DATA_DIR / "exports"
EXPORT_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class PlatformStats:
    total_users: int
    active_users: int
    reviews_count: int
    bookmarks_count: int
    penalties_count: int
    top_genres: List[tuple[str, int]]
    generated_at: datetime


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------
def _load_json(path: Path) -> Any:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _count_records(path: Path) -> int:
    """
    Counts records in a JSON file:
    - if list -> len(list)
    - if dict -> len(dict)
    If file does not exist, returns 0.
    """
    if not path.exists():
        return 0
    data = _load_json(path)
    if isinstance(data, list):
        return len(data)
    if isinstance(data, dict):
        return len(data)
    return 0


def _compute_top_genres(limit: int = 10) -> List[tuple[str, int]]:
    """
    Computes top 'genres' using items.json.

    We treat each item as:
      {
        "id": "...",
        "title": "...",
        "category": "...",   # used as genre fallback
        "tags": [...]
      }
    """
    if not ITEMS_FILE.exists():
        return []

    items = _load_json(ITEMS_FILE)
    if not isinstance(items, list):
        return []

    counter: Counter[str] = Counter()
    for item in items:
        # Prefer explicit 'genre' if you later add it, otherwise use 'category'
        genre = item.get("genre") or item.get("category")
        if genre:
            counter[genre] += 1

    return counter.most_common(limit)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def compute_stats() -> PlatformStats:
    """Computes all statistics required by the export user story."""
    users_data = _load_json(USERS_FILE)
    # Your users.json is a dict keyed by user id :contentReference[oaicite:2]{index=2}
    if isinstance(users_data, dict):
        users = list(users_data.values())
    elif isinstance(users_data, list):
        users = users_data
    else:
        users = []

    total_users = len(users)
    active_users = sum(1 for u in users if u.get("is_active", True))

    reviews_count = _count_records(REVIEWS_FILE)
    bookmarks_count = _count_records(BOOKMARKS_FILE)
    penalties_count = _count_records(PENALTIES_FILE)

    top_genres = _compute_top_genres()
    generated_at = datetime.now(UTC)

    return PlatformStats(
        total_users=total_users,
        active_users=active_users,
        reviews_count=reviews_count,
        bookmarks_count=bookmarks_count,
        penalties_count=penalties_count,
        top_genres=top_genres,
        generated_at=generated_at,
    )


def write_stats_csv(stats: PlatformStats) -> Path:
    """
    Writes a single-row CSV file containing platform stats.

    Headers are stable and include generated_at.
    """
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = stats.generated_at.strftime("%Y%m%d_%H%M%S")
    out_path = EXPORT_DIR / f"platform_stats_{timestamp}.csv"

    headers = [
        "generated_at",
        "total_users",
        "active_users",
        "reviews_count",
        "bookmarks_count",
        "penalties_count",
        "top_genres",  # stored as "Genre1:count;Genre2:count;..."
    ]

    top_genres_str = ";".join(f"{g}:{c}" for g, c in stats.top_genres)

    with out_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        writer.writeheader()
        writer.writerow(
            {
                "generated_at": stats.generated_at.isoformat(),
                "total_users": stats.total_users,
                "active_users": stats.active_users,
                "reviews_count": stats.reviews_count,
                "bookmarks_count": stats.bookmarks_count,
                "penalties_count": stats.penalties_count,
                "top_genres": top_genres_str,
            }
        )

    return out_path
