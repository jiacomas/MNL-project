"""
Test the updated MovieCreate and MovieUpdate schemas.
"""

import pytest
from pydantic import ValidationError

from backend.schemas.movies import MovieCreate, MovieUpdate


def test_movie_create_with_all_required_fields():
    """Test creating a movie with all required fields."""
    movie_data = {
        "title": "Test Movie",
        "movieGenres": "Action, Adventure",
        "directors": "Test Director",
        "datePublished": "2024-01-01",
        "creators": "Test Creator",
        "mainStars": "Actor One, Actor Two",
        "description": "A test movie description",
        "duration": 120,
    }
    movie = MovieCreate(**movie_data)
    assert movie.title == "Test Movie"
    assert movie.duration == 120


def test_movie_create_missing_required_field():
    """Test that missing required fields raise validation error."""
    movie_data = {
        "title": "Test Movie",
        # Missing movieGenres
        "directors": "Test Director",
        "datePublished": "2024-01-01",
        "creators": "Test Creator",
        "mainStars": "Actor One",
        "description": "A test movie",
        "duration": 120,
    }
    with pytest.raises(ValidationError):
        MovieCreate(**movie_data)


def test_movie_create_strips_whitespace():
    """Test that string fields are stripped of whitespace."""
    movie_data = {
        "title": "  Test Movie  ",
        "movieGenres": "  Action  ",
        "directors": "  Test Director  ",
        "datePublished": "2024-01-01",
        "creators": "  Test Creator  ",
        "mainStars": "  Actor One  ",
        "description": "  A test movie  ",
        "duration": 120,
    }
    movie = MovieCreate(**movie_data)
    assert movie.title == "Test Movie"
    assert movie.movieGenres == "Action"


def test_movie_create_empty_string_fails():
    """Test that empty strings fail validation."""
    movie_data = {
        "title": "   ",  # Only whitespace
        "movieGenres": "Action",
        "directors": "Test Director",
        "datePublished": "2024-01-01",
        "creators": "Test Creator",
        "mainStars": "Actor One",
        "description": "A test movie",
        "duration": 120,
    }
    with pytest.raises(ValidationError):
        MovieCreate(**movie_data)


def test_movie_update_all_fields_optional():
    """Test that MovieUpdate requires at least one field."""
    with pytest.raises(ValidationError, match="At least one field must be provided"):
        MovieUpdate()


def test_movie_update_single_field():
    """Test updating a single field."""
    update = MovieUpdate(title="Updated Title")
    assert update.title == "Updated Title"
    assert update.movieGenres is None


def test_movie_update_no_rating_field():
    """Test that movieIMDbRating is not in MovieUpdate."""
    # This should not have movieIMDbRating field
    update_data = {
        "title": "Updated Movie",
        "movieGenres": "Drama",
    }
    update = MovieUpdate(**update_data)
    assert (
        not hasattr(update, "movieIMDbRating")
        or "movieIMDbRating" not in MovieUpdate.model_fields
    )


def test_movie_update_strips_whitespace():
    """Test that update fields are stripped."""
    update = MovieUpdate(title="  Updated  ", movieGenres="  Drama  ")
    assert update.title == "Updated"
    assert update.movieGenres == "Drama"
