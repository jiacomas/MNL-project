"""
Pytest configuration file for Movies Service tests
"""

from unittest.mock import create_autospec

import pytest

from backend.repositories.movies_repo import MovieRepository
from backend.schemas.movies import MovieOut


def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line("markers", "unit: mark test as unit test")
    config.addinivalue_line(
        "markers",
        "integration: mark test as integration test (requires external resources)",
    )
    config.addinivalue_line("markers", "performance: mark test as performance test")


@pytest.fixture
def mock_repo():
    """Create a mock movie repository"""
    return create_autospec(MovieRepository)


@pytest.fixture
def sample_movie_out():
    """Provide sample movie data for tests"""
    return MovieOut(
        movie_id="tt0111161",
        title="The Shawshank Redemption",
        genre="Drama",
        release_year=1994,
        rating=9.3,
        runtime=142,
        director="Frank Darabont",
        cast="Tim Robbins, Morgan Freeman",
        plot="Two imprisoned men bond over a number of years...",
        poster_url="https://example.com/poster.jpg",
        created_at="2024-01-01T12:00:00Z",
        updated_at="2024-01-01T12:00:00Z",
        review_count=2500000,
    )
