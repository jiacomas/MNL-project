from __future__ import annotations

import csv
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List

# Paths are overridable via env vars so tests can patch them easily
USERS_FILE: Path = Path(os.environ.get("USERS_FILE", "data/users.json"))
REVIEWS_FILE: Path = Path(os.environ.get("REVIEWS_FILE", "data/reviews.json"))
SUMMARY_EXPORT_DIR: Path = Path(
    os.environ.get("SUMMARY_EXPORT_DIR", "data/exports")
)


JsonObj = Dict[str, Any]


# ---------------------------------------------------------------------------
# Helpers for reading data
# ---------------------------------------------------------------------------

def _read_json_list(path: Path) -> List[JsonObj]:
    """Read JSON and always return a list of dicts.

    Accepts:
    - plain arrays: [ {...}, {...} ]
    - wrapped: { "items": [...] }, { "users": [...] }, { "reviews": [...] }
    - single objects: { ... } -> wrapped into a list
    """
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
# Core metrics
# ---------------------------------------------------------------------------

def _total_users(users: List[JsonObj]) -> int:
    return len(users)


def _total_reviews(reviews: List[JsonObj]) -> int:
    return len(reviews)


def _active_users_last_24h(
    users: List[JsonObj],
    reviews: List[JsonObj],
    now: datetime | None = None,
) -> int:
    """Count active users in the last 24h.

    Priority:
    1) If a user has last_active_at or last_login_at (ISO string), use that.
    2) Otherwise fall back to users who wrote a review in the last 24h.
    """
    if now is None:
        now = datetime.now(timezone.utc)

    cutoff = now - timedelta(hours=24)
    active_ids: set[str] = set()

    # 1) Prefer explicit last_active_at / last_login_at fields
    for u in users:
        last_active = u.get("last_active_at") or u.get("last_login_at")
        if not isinstance(last_active, str):
            continue

        try:
            dt = datetime.fromisoformat(last_active)
        except ValueError:
            continue

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        if dt >= cutoff:
            uid = str(u.get("user_id") or u.get("id"))
            active_ids.add(uid)

    # 2) Fallback – activity via reviews
    if not active_ids:
        for r in reviews:
            created = r.get("created_at")
            if isinstance(created, str):
                try:
                    dt = datetime.fromisoformat(created)
                except ValueError:
                    continue
            elif isinstance(created, datetime):
                dt = created
            else:
                continue

            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)

            if dt >= cutoff:
                uid = str(r.get("user_id"))
                active_ids.add(uid)

    return len(active_ids)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_admin_summary() -> Dict[str, int]:
    """Return engagement stats for admin dashboard summary cards."""
    users = _read_json_list(USERS_FILE)
    reviews = _read_json_list(REVIEWS_FILE)

    users_total = _total_users(users)
    reviews_total = _total_reviews(reviews)
    active_users_24h = _active_users_last_24h(users, reviews)

    return {
        "users_total": users_total,
        "active_users_24h": active_users_24h,
        "reviews_total": reviews_total,
    }


def write_summary_csv() -> Path:
    """Export current summary metrics to CSV and return the file path.

    CSV layout:

        metric,value
        users_total,<int>
        active_users_24h,<int>
        reviews_total,<int>
        generated_at,<ISO-8601 timestamp>
    """
    SUMMARY_EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = SUMMARY_EXPORT_DIR / "admin_summary_export.csv"

    summary = get_admin_summary()
    now = datetime.now(timezone.utc).isoformat()

    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value"])
        writer.writerow(["users_total", summary["users_total"]])
        writer.writerow(["active_users_24h", summary["active_users_24h"]])
        writer.writerow(["reviews_total", summary["reviews_total"]])
        writer.writerow(["generated_at", now])

    return out_path
