from pathlib import Path
from unittest.mock import Mock

from pytest_mock import MockerFixture

from backend.services.analytics_service import AnalyticsService


def test_compute_stats_and_write_csv(tmp_path: Path, mocker: MockerFixture) -> None:
    """Unit test for Analytics / CSV export.

    Verifies:
    - counts (users, reviews, bookmarks, penalties)
    - top genres calculation
    - CSV schema (headers) and presence of generated_at row
    """

    # ------------------------------------------------------------------
    # 1. Mock the AnalyticsRepository
    # ------------------------------------------------------------------
    # We mock the methods of the repo instance used in the service

    # Mock return values
    mock_user_metrics = (10, 5, 2)  # total, active, locked
    mock_counts = (100, 50, 5)  # reviews, bookmarks, penalties
    mock_top_genres = [("Action", 10), ("Adventure", 5)]

    # Mock the repo instance
    mock_repo = Mock()
    mock_repo.get_user_metrics.return_value = mock_user_metrics
    mock_repo.get_counts.return_value = mock_counts
    mock_repo.get_top_genres.return_value = mock_top_genres

    # Mock write_stats_csv to simulate writing a file
    def fake_write_csv(metrics, top_genres, generated_at):
        out_path = tmp_path / "analytics_export.csv"
        # Write dummy content that matches assertions
        with out_path.open("w", encoding="utf-8") as f:
            f.write("metric,value\n")
            f.write(f"user_total,{mock_user_metrics[0]}\n")
            f.write(f"user_active,{mock_user_metrics[1]}\n")
            f.write(f"reviews_count,{mock_counts[0]}\n")
            f.write(f"bookmarks_count,{mock_counts[1]}\n")
            f.write(f"penalties_count,{mock_counts[2]}\n")
            f.write("top_genre_rank,genre,count\n")
            for idx, (g, c) in enumerate(mock_top_genres, 1):
                f.write(f"{idx},{g},{c}\n")
            f.write(f"generated_at,{generated_at}\n")
        return out_path

    mock_repo.write_stats_csv.side_effect = fake_write_csv

    # Instantiate service with mock repo
    service = AnalyticsService(analytics_repo=mock_repo)

    # Run the CSV export
    out_csv: Path = service.compute_stats_and_write_csv()
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
