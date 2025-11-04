"""
Performance and stress tests for Movies Service
"""
import pytest
import time
from unittest.mock import patch, create_autospec

from backend.services.movies_service import (
    get_movies,
    search_movies
)
from backend.schemas.movies import MovieOut, MovieSearchFilters
from backend.repositories.movies_repo import MovieRepository


class TestMoviesServicePerformance:
    """Performance and stress tests for Movies Service"""

    @pytest.fixture
    def mock_repo(self):
        """Create a mock movie repository for performance tests"""
        return create_autospec(MovieRepository)

    @pytest.mark.performance
    def test_get_movies_performance_large_dataset(self, mock_repo):
        """Performance test: get_movies with large dataset"""
        # Create a large mock dataset
        large_movie_list = [
            MovieOut(
                movie_id=f"tt{1000000 + i}",
                title=f"Movie {i}",
                genre="Drama",
                release_year=2000 + (i % 25),
                rating=7.0 + (i % 3) * 0.5,
                runtime=120,
                director="Test Director",
                cast="Test Cast",
                plot="Test plot",
                poster_url="https://example.com/poster.jpg",
                created_at="2024-01-01T12:00:00Z",
                updated_at="2024-01-01T12:00:00Z",
                review_count=1000
            ) for i in range(1000)
        ]

        mock_repo.get_all.return_value = (large_movie_list[:50], 1000)

        with patch('backend.services.movies_service.movie_repo', mock_repo):
            start_time = time.time()

            response = get_movies(page=1, page_size=50)

            end_time = time.time()
            execution_time = end_time - start_time

        assert len(response.items) == 50
        assert execution_time < 1.0  # Should complete within 1 second

    @pytest.mark.performance
    def test_search_movies_performance_complex_filters(self, mock_repo):
        """Performance test: search with complex filters"""
        mock_repo.search.return_value = ([], 0)

        complex_filters = MovieSearchFilters(
            title="complex",
            genre="Drama,Action,Comedy",
            min_year=1990,
            max_year=2020,
            min_rating=7.5,
            director="Christopher Nolan"
        )

        with patch('backend.services.movies_service.movie_repo', mock_repo):
            start_time = time.time()

            search_movies(filters=complex_filters, page=1, page_size=50)

            end_time = time.time()
            execution_time = end_time - start_time

        assert execution_time < 2.0  # Complex search should complete within 2 seconds


# ==================== TEST CONFIGURATION ====================

def pytest_configure(config):
    """Add custom markers for different test types"""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test (requires external resources)"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as performance test"
    )
    config.addinivalue_line(
        "markers", "fault_injection: mark test as fault injection test"
    )