from __future__ import annotations

import csv
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List

from backend.utils.datetime_utils import parse_iso_like

# ---------------------------------------------------------------------------
# Configuration (local to this feature so tests can patch easily)
# ---------------------------------------------------------------------------

DATA_ROOT = Path(os.getenv("ADMIN_SUMMARY_DATA_ROOT", "data"))
USERS_FILE = DATA_ROOT / "users.json"
REVIEWS_FILE = DATA_ROOT / "reviews.json"

# Tests patch this in test_write_summary_csv
SUMMARY_EXPORT_DIR = DATA_ROOT / "exports"


# ---------------------------------------------------------------------------
# IO helpers
# ---------------------------------------------------------------------------


def _load_json_list(path: Path) -> List[Dict[str, Any]]:
    """Load JSON file and always return a list of dicts."""
    if not path.exists():
        return []

    data = json.loads(path.read_text(encoding="utf-8"))

    if isinstance(data, list):
        return list(data)

    if isinstance(data, dict):
        for key in ("items", "users", "reviews"):
            if key in data and isinstance(data[key], list):
                return list(data[key])

    return [data]


# ---------------------------------------------------------------------------
# Time helpers
# ---------------------------------------------------------------------------


def _is_within_last_24h(ts: datetime | None, now: datetime) -> bool:
    """Return True if ts is within the last 24 hours."""
    if ts is None:
        return False
    window_start = now - timedelta(days=1)
    return window_start <= ts <= now


# ---------------------------------------------------------------------------
# Core metrics
# ---------------------------------------------------------------------------


def _active_users_last_24h(
    users: List[Dict[str, Any]],
    reviews: List[Dict[str, Any]],
    *,
    now: datetime | None = None,
) -> int:
    """Compute number of distinct users active in the last 24 hours.

    Activity sources:
    - user.last_active_at / last_login / last_seen
    - review.created_at
    """
    now = now or datetime.now(timezone.utc)
    active_ids: set[str] = set()

    # From user records
    for user in users:
        ts_raw = (
            user.get("last_active_at")
            or user.get("last_login")
            or user.get("last_seen")
        )
        ts = parse_iso_like(ts_raw)
        if _is_within_last_24h(ts, now):
            uid = str(user.get("user_id") or user.get("id"))
            if uid:
                active_ids.add(uid)

    # From recent reviews
    for review in reviews:
        ts = parse_iso_like(review.get("created_at"))
        if _is_within_last_24h(ts, now):
            uid = str(review.get("user_id"))
            if uid:
                active_ids.add(uid)

    return len(active_ids)


def _total_users(users: List[Dict[str, Any]]) -> int:
    return len(users)


def _total_reviews(reviews: List[Dict[str, Any]]) -> int:
    return len(reviews)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_admin_summary() -> Dict[str, Any]:
    """Return engagement summary for admin dashboard cards as a dict.

    Keys:
    - users_total
    - reviews_total
    - active_users_24h
    - generated_at (ISO-8601 string)
    """
    users = _load_json_list(USERS_FILE)
    reviews = _load_json_list(REVIEWS_FILE)
    now = datetime.now(timezone.utc)

    return {
        "users_total": _total_users(users),
        "reviews_total": _total_reviews(reviews),
        "active_users_24h": _active_users_last_24h(users, reviews, now=now),
        "generated_at": now.isoformat(),
    }


def write_summary_csv() -> Path:
    """Export the current summary as a metrics CSV file.

    Layout:
    - Header row: "metric,value"
    - One row per metric (users_total, reviews_total, active_users_24h, generated_at)
    """
    summary = get_admin_summary()

    SUMMARY_EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = SUMMARY_EXPORT_DIR / "admin_summary_export.csv"

    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value"])
        for key in ("users_total", "reviews_total", "active_users_24h", "generated_at"):
            writer.writerow([key, summary[key]])

    return out_path
