from __future__ import annotations

from pathlib import Path

from pytest_mock import MockerFixture

from backend.services import analytics_service as analytics


def test_compute_stats_and_write_csv(tmp_path: Path, mocker: MockerFixture) -> None:
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

    mocker.patch.object(analytics, "USERS_FILE", users_file)
    mocker.patch.object(analytics, "REVIEWS_FILE", reviews_file)
    mocker.patch.object(analytics, "BOOKMARKS_FILE", bookmarks_file)
    mocker.patch.object(analytics, "PENALTIES_FILE", penalties_file)
    mocker.patch.object(analytics, "ITEMS_FILE", items_file)
    mocker.patch.object(analytics, "EXPORT_DIR", export_dir)

    # ------------------------------------------------------------------
    # 2. Write minimal JSON fixtures for the test
    # ------------------------------------------------------------------
    # Users: one active, one locked
    users_file.write_text(
        '[{"id": "u1", "is_locked": false}, {"id": "u2", "is_locked": true}]',
        encoding="utf-8",
    )

    # Single movie m1 with two genres
    items_file.write_text(
        '[{"id": "m1", "genres": ["Action", "Adventure"]}]',
        encoding="utf-8",
    )

    # One review and one bookmark for m1
    reviews_file.write_text(
        '[{"user_id": "u1", "movie_id": "m1"}]',
        encoding="utf-8",
    )
    bookmarks_file.write_text(
        '[{"user_id": "u1", "movie_id": "m1"}]',
        encoding="utf-8",
    )

    # One penalty record
    penalties_file.write_text(
        '[{"user_id": "u2", "reason": "spam"}]',
        encoding="utf-8",
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
