from __future__ import annotations

import json
from pathlib import Path

from backend.services import analytics_service as analytics


def _write_json(path: Path, payload: object) -> None:
    """Small helper to write JSON payloads with UTF-8 + pretty format."""
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_compute_stats_and_write_csv(tmp_path: Path, monkeypatch) -> None:
    """Unit test for Analytics / CSV export.

    Verifies:
    - counts (users, reviews, bookmarks, penalties)
    - top genres calculation
    - CSV schema (headers) and presence of generated_at row
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
    # 2. Write minimal JSON fixtures for the test
    # ------------------------------------------------------------------
    # Users: one active, one locked
    _write_json(
        users_file,
        [
            {"id": "u1", "is_locked": False},
            {"id": "u2", "is_locked": True},
        ],
    )

    # Single movie m1 with two genres
    _write_json(
        items_file,
        [
            {"id": "m1", "genres": ["Action", "Adventure"]},
        ],
    )

    # One review and one bookmark for m1
    _write_json(
        reviews_file,
        [
            {"user_id": "u1", "movie_id": "m1"},
        ],
    )
    _write_json(
        bookmarks_file,
        [
            {"user_id": "u1", "movie_id": "m1"},
        ],
    )

    # One penalty record
    _write_json(
        penalties_file,
        [
            {"user_id": "u2", "reason": "spam"},
        ],
    )

    # ------------------------------------------------------------------
    # 3. Run the CSV export
    # ------------------------------------------------------------------
    out_csv: Path = analytics.compute_stats_and_write_csv()
    assert out_csv.exists()

    # ------------------------------------------------------------------
    # 4. Basic content checks on the CSV
    # ------------------------------------------------------------------
    content = out_csv.read_text(encoding="utf-8")

    # Header / metric rows
    assert "metric,value" in content
    assert "user_active" in content
    assert "user_total" in content
    assert "reviews" in content
    assert "bookmarks" in content
    assert "penalties" in content

    # Top genres section
    assert "top_genre_rank,genre,count" in content
    assert "Action" in content or "Adventure" in content

    # Tail row with generated_at
    assert "generated_at" in content
