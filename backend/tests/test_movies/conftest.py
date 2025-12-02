"""
Test fixtures and helpers for movie tests.
"""

from datetime import datetime, timezone

from backend.schemas.movies import MovieCreate, MovieOut


def create_valid_movie_create(**overrides) -> MovieCreate:
    """
    Helper function to create a valid MovieCreate object with all required fields.

    Args:
        **overrides: Any fields to override from the defaults

    Returns:
        MovieCreate object with all required fields populated
    """
    defaults = {
        "title": "Test Movie",
        "movieGenres": "Action, Adventure",
        "directors": "Test Director",
        "datePublished": "2024-01-01",
        "creators": "Test Creator",
        "mainStars": "Actor One, Actor Two",
        "description": "A test movie description",
        "duration": 120,
    }
    defaults.update(overrides)
    return MovieCreate(**defaults)


def create_sample_movie_out(**overrides) -> MovieOut:
    """
    Helper function to create a sample MovieOut object.

    Args:
        **overrides: Any fields to override from the defaults

    Returns:
        MovieOut object with all fields populated
    """
    defaults = {
        "movie_id": "test-movie-id",
        "title": "Sample Movie",
        "movieGenres": "Action",
        "directors": "Director X",
        "datePublished": "2000-01-01",
        "creators": "Creator Y",
        "mainStars": "Actor Z",
        "description": "A sample movie",
        "duration": 120,
        "movieIMDbRating": 8.5,
        "totalRatingCount": 1000,
        "totalUserReviews": 500,
        "totalCriticReviews": 50,
        "metaScore": 85,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "review_count": 5,
    }
    defaults.update(overrides)
    return MovieOut(**defaults)
