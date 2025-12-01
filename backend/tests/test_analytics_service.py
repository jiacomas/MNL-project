from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock

from pytest_mock import MockerFixture

from backend.services import analytics_service as analytics


def test_compute_stats_and_write_csv(tmp_path: Path, mocker: MockerFixture) -> None:
    """Unit test for Analytics / CSV export.

    Verifies:
    - counts (users, reviews, bookmarks, penalties)
    - top genres calculation
    - CSV schema (headers) and presence of generated_at row
    """

    # Mock the AnalyticsRepository
    mock_user_metrics = (10, 5, 2)  # total, active, locked
    mock_counts = (100, 50, 5)  # reviews, bookmarks, penalties
    mock_top_genres = [("Action", 10), ("Adventure", 5)]

    # Mock the repo instance
    mock_repo = Mock()
    mock_repo.get_user_metrics.return_value = mock_user_metrics
    mock_repo.get_counts.return_value = mock_counts
    mock_repo.get_top_genres.return_value = mock_top_genres

    mocker.patch.object(
        analytics._analytics_repo, "get_user_metrics", return_value=mock_user_metrics
    )
    mocker.patch.object(
        analytics._analytics_repo, "get_counts", return_value=mock_counts
    )
    mocker.patch.object(
        analytics._analytics_repo, "get_top_genres", return_value=mock_top_genres
    )

    # We also need to patch the export_dir of the global repo to use tmp_path
    analytics._analytics_repo.export_dir = tmp_path

    #  Run the CSV export
    out_csv: Path = analytics.compute_stats_and_write_csv()
    assert out_csv.exists()

    # Basic content checks on the CSV
    content = out_csv.read_text(encoding="utf-8")

    # Header / metric rows
    assert "metric,value" in content
    assert "user_active" in content
    assert "user_total" in content
    assert "reviews" in content
    assert "bookmarks" in content
    assert "penalties" in content

    # Check values
    assert "10" in content  # total users
    assert "5" in content  # active users
    assert "100" in content  # reviews

    # Top genres section
    assert "top_genre_rank,genre,count" in content
    assert "Action" in content
    assert "Adventure" in content

    # Tail row with generated_at
    assert "generated_at" in content
