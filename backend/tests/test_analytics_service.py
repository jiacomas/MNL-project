from __future__ import annotations

import csv
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, List

import pytest
from services import analytics_service as analytics


def _write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=4), encoding="utf-8")


def test_compute_stats_and_write_csv(tmp_path, monkeypatch) -> None:
    """Unit test for Analytics / CSV export.

    Verifies:
    - counts (users, reviews, bookmarks, penalties)
    - top genres calculation
    - CSV schema (headers) and values including generated_at timestamp
    """

    # ------------------------------------------------------------------
    # 1. Point analytics_service to temporary data files
    # ------------------------------------------------------------------
    users_file = tmp_path / "users.json"
    reviews_file = tmp_path / "reviews.json"
    bookmarks_file = tmp_path / "bookmarks.json"
    penalties_file = tmp_path / "penalties.json"
    items_file = tmp_path / "items.json"
    export_dir = tmp_path / "exports"

    monkeypatch.setattr(analytics, "USERS_FILE", users_file)
    monkeypatch.setattr(analytics, "REVIEWS_FILE", reviews_file)
    monkeypatch.setattr(analytics, "BOOKMARKS_FILE", bookmarks_file)
    monkeypatch.setattr(analytics, "PENALTIES_FILE", penalties_file)
    monkeypatch.setattr(analytics, "ITEMS_FILE", items_file)
    monkeypatch.setattr(analytics, "EXPORT_DIR", export_dir)

    # ------------------------------------------------------------------
    # 2. Create small synthetic dataset
    # ------------------------------------------------------------------
    users: Dict[str, Dict[str, Any]] = {
        "u1": {"user_id": "u1", "email": "a@example.com", "is_active": True},
        "u2": {"user_id": "u2", "email": "b@example.com", "is_active": False},
        "u3": {"user_id": "u3", "email": "c@example.com", "is_active": True},
    }
    _write_json(users_file, users)

    # these can be lists or dicts; service counts len()
    _write_json(reviews_file, [{"id": "r1"}, {"id": "r2"}])  # 2 reviews
    _write_json(bookmarks_file, [{"id": "b1"}])  # 1 bookmark
    _write_json(
        penalties_file, [{"id": "p1"}, {"id": "p2"}, {"id": "p3"}]
    )  # 3 penalties

    # items with genres -> used for "Top 10 genres by popularity"
    items: List[Dict[str, Any]] = [
        {"id": "m1", "title": "Movie A", "genre": "Action"},
        {"id": "m2", "title": "Movie B", "genre": "Drama"},
        {"id": "m3", "title": "Movie C", "genre": "Action"},
    ]
    _write_json(items_file, items)

    # ------------------------------------------------------------------
    # 3. Compute stats and assert counts / top genres
    # ------------------------------------------------------------------
    stats = analytics.compute_stats()

    assert stats.total_users == 3
    assert stats.active_users == 2
    assert stats.reviews_count == 2
    assert stats.bookmarks_count == 1
    assert stats.penalties_count == 3

    # top_genres is a list of (genre, count) tuples
    assert stats.top_genres[0][0] == "Action"
    assert stats.top_genres[0][1] == 2
    # ensure it recorded at least one genre
    assert len(stats.top_genres) >= 1

    assert isinstance(stats.generated_at, datetime)

    # ------------------------------------------------------------------
    # 4. Write CSV and verify schema & values
    # ------------------------------------------------------------------
    csv_path = analytics.write_stats_csv(stats)
    assert csv_path.exists()
    assert csv_path.parent == export_dir

    with csv_path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Exactly one row written
    assert len(rows) == 1
    row = rows[0]

    # Stable headers
    expected_headers = {
        "generated_at",
        "total_users",
        "active_users",
        "reviews_count",
        "bookmarks_count",
        "penalties_count",
        "top_genres",
    }
    assert expected_headers.issubset(set(reader.fieldnames or []))

    # Values match stats (CSV stores everything as strings)
    assert int(row["total_users"]) == stats.total_users
    assert int(row["active_users"]) == stats.active_users
    assert int(row["reviews_count"]) == stats.reviews_count
    assert int(row["bookmarks_count"]) == stats.bookmarks_count
    assert int(row["penalties_count"]) == stats.penalties_count

    # generated_at present and looks like ISO string
    assert row["generated_at"]
    # Just a sanity check it parses as datetime
    parsed_ts = datetime.fromisoformat(row["generated_at"])
    assert isinstance(parsed_ts, datetime)

    # top_genres non-empty string like "Action:2;Drama:1"
    assert "Action" in row["top_genres"]
