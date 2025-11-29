from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from backend import settings

JsonObj = Dict[str, Any]

# ---------------------------------------------------------------------------
# File locations (can be overridden in tests via mocker.patch.object)
# ---------------------------------------------------------------------------

HISTORY_FILE: Path = settings.HISTORY_FILE  # e.g. backend/data/history.json
ITEMS_FILE: Path = settings.ITEMS_FILE  # existing items/movies file


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _load_json_list(path: Path) -> List[JsonObj]:
    """Load a JSON file and always return a list of dicts."""
    if not path.exists():
        return []

    data = json.loads(path.read_text(encoding="utf-8"))

    if isinstance(data, list):
        return list(data)

    if isinstance(data, dict):
        # allow {"items": [...]} etc. if ever needed
        for key in ("items", "history"):
            if key in data and isinstance(data[key], list):
                return list(data[key])

    return [data]


def _save_json_list(path: Path, rows: List[JsonObj]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rows, indent=4), encoding="utf-8")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_items_index() -> Dict[str, JsonObj]:
    """Return movie_id -> item dict (used to get title + year)."""
    items = _load_json_list(ITEMS_FILE)
    return {str(item.get("id")): item for item in items}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def log_view(
    user_id: str,
    movie_id: str,
    viewed_at: str | datetime | None = None,
) -> None:
    """Record or update a viewing event for a user + movie.

    - If (user_id, movie_id) does not exist, create it.
    - If it exists, update `last_viewed_at` to the latest timestamp.
    """
    history = _load_json_list(HISTORY_FILE)

    if isinstance(viewed_at, datetime):
        ts = viewed_at.astimezone(timezone.utc).isoformat()
    elif isinstance(viewed_at, str):
        ts = viewed_at
    else:
        ts = _now_iso()

    # Update existing entry if present
    for row in history:
        if row.get("user_id") == user_id and row.get("movie_id") == movie_id:
            row["last_viewed_at"] = ts
            _save_json_list(HISTORY_FILE, history)
            return

    # Otherwise append a new row
    history.append(
        {
            "user_id": user_id,
            "movie_id": movie_id,
            "last_viewed_at": ts,
        }
    )
    _save_json_list(HISTORY_FILE, history)


def list_history(user_id: str) -> List[JsonObj]:
    """Return viewing history for a user, joined with movie metadata.

    Each entry contains:
        - movie_id
        - title
        - release_year
        - last_viewed_at
    Sorted by last_viewed_at (most recent first).
    """
    history = _load_json_list(HISTORY_FILE)
    items_by_id = _load_items_index()

    user_rows = [row for row in history if row.get("user_id") == user_id]

    # Sort by timestamp string (ISO-8601 sorts correctly)
    user_rows.sort(key=lambda r: r.get("last_viewed_at") or "", reverse=True)

    result: List[JsonObj] = []
    for row in user_rows:
        movie_id = str(row.get("movie_id"))
        item = items_by_id.get(movie_id, {})
        result.append(
            {
                "movie_id": movie_id,
                "title": item.get("title", movie_id),
                "release_year": item.get("year") or item.get("release_year"),
                "last_viewed_at": row.get("last_viewed_at"),
            }
        )

    return result


def clear_history_item(user_id: str, movie_id: str) -> None:
    """Remove a single movie from a user's viewing history."""
    history = _load_json_list(HISTORY_FILE)

    new_history = [
        row
        for row in history
        if not (row.get("user_id") == user_id and row.get("movie_id") == movie_id)
    ]

    _save_json_list(HISTORY_FILE, new_history)


def clear_history(user_id: str) -> None:
    """Remove all viewing history entries for a user."""
    history = _load_json_list(HISTORY_FILE)

    new_history = [row for row in history if row.get("user_id") != user_id]

    _save_json_list(HISTORY_FILE, new_history)
