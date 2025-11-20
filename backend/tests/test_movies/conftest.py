"""
Fixtures for Movies Router tests.
"""

from unittest.mock import create_autospec

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.repositories.movies_repo import MovieRepository
from backend.schemas.movies import MovieOut


# ----- Mock Repository -----
@pytest.fixture
def mock_repo():
    """Mocked MovieRepository instance."""
    return create_autospec(MovieRepository)


# ----- Test Client -----
@pytest.fixture
def client():
    """FastAPI TestClient for integration tests."""
    return TestClient(app)


# ----- Headers for Auth -----
@pytest.fixture
def user_headers():
    """Simulate normal user headers."""
    return {"X-User-Role": "user", "X-User-Id": "u1"}


@pytest.fixture
def admin_headers():
    """Simulate admin headers."""
    return {"X-User-Role": "admin", "X-User-Id": "admin"}


# ----- Sample Data -----
@pytest.fixture
def sample_movie_data():
    """Sample raw movie dictionary."""
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
        "review_count": 2000000,
    }


@pytest.fixture
def sample_movie_out(sample_movie_data):
    """Sample MovieOut model instance."""
    return MovieOut(**sample_movie_data)
