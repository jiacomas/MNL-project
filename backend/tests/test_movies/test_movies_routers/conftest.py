"""
Shared test fixtures for movies router tests.
"""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.schemas.movies import MovieOut


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment for all tests"""
    with patch('backend.routers.movies._AUTH_ENABLED', True):
        yield


@pytest.fixture
def client():
    """Create test client for FastAPI app"""
    return TestClient(app)


@pytest.fixture
def sample_movie_data():
    """Sample movie data for testing"""
    return {
        "movie_id": "tt0111161",
        "title": "The Shawshank Redemption",
        "genre": "Drama",
        "release_year": 1994,
        "rating": 9.3,
        "runtime": 142,
        "director": "Frank Darabont",
        "cast": "Tim Robbins, Morgan Freeman",
        "plot": "Two imprisoned men bond over a number of years...",
        "poster_url": "https://example.com/poster.jpg",
        "created_at": "2024-01-01T12:00:00Z",
        "updated_at": "2024-01-01T12:00:00Z",
        "review_count": 2500000,
    }


@pytest.fixture
def sample_movie_out(sample_movie_data):
    """Create MovieOut instance from sample data"""
    return MovieOut(**sample_movie_data)


@pytest.fixture
def mock_current_user():
    """Mock current user for authentication"""
    return {"user_id": "test_user", "role": "user"}


@pytest.fixture
def mock_current_admin():
    """Mock admin user for authentication"""
    return {"user_id": "admin_user", "role": "admin"}
