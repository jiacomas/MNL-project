"""
Tests for MovieUpdate schema using multiple testing methodologies.
"""

import pytest
from pydantic import ValidationError

from backend.schemas.movies import MovieUpdate


class TestMovieUpdateSchema:
    """Comprehensive tests for MovieUpdate schema functionality."""

    def test_valid_partial_update(self):
        """Test MovieUpdate with valid partial data."""
        data = {"rating": 9.5, "poster_url": "https://updated-poster.com/image.jpg"}

        movie_update = MovieUpdate(**data)
        assert movie_update.rating == data["rating"]
        assert movie_update.poster_url == data["poster_url"]

    def test_empty_update_rejection(self):
        """Test MovieUpdate validation fails when no fields are provided."""
        with pytest.raises(ValidationError) as exc_info:
            MovieUpdate()

        assert "At least one field must be provided for update" in str(exc_info.value)

    def test_string_field_normalization(self):
        """Test string fields are properly normalized."""
        data = {
            "title": "  Updated Title  ",
            "genre": "  Updated Genre  ",
            "director": "  New Director  ",
        }

        movie_update = MovieUpdate(**data)
        assert movie_update.title == "Updated Title"
        assert movie_update.genre == "Updated Genre"
        assert movie_update.director == "New Director"

    @pytest.mark.parametrize(
        "field_name,valid_value",
        [
            ("title", "Valid Title"),
            ("genre", "Action"),
            ("release_year", 2020),
            ("rating", 8.5),
            ("runtime", 120),
            ("director", "Director Name"),
            ("cast", "Actor 1, Actor 2"),
            ("plot", "Plot summary"),
            ("poster_url", "https://example.com/poster.jpg"),
        ],
    )
    def test_individual_field_updates(self, field_name, valid_value):
        """Test each field can be updated individually."""
        data = {field_name: valid_value}
        movie_update = MovieUpdate(**data)
        assert getattr(movie_update, field_name) == valid_value

    def test_extra_fields_rejection(self):
        """Test that extra fields are properly rejected."""
        with pytest.raises(ValidationError) as exc_info:
            MovieUpdate(
                title="Updated Title", invalid_field="This should not be allowed"
            )

        error_str = str(exc_info.value)
        assert "extra" in error_str.lower() or "forbidden" in error_str.lower()

    @pytest.mark.parametrize("rating", [0.0, 5.0, 10.0])
    def test_rating_boundary_values(self, rating):
        """Test rating boundary values are accepted."""
        movie_update = MovieUpdate(rating=rating)
        assert movie_update.rating == rating

    @pytest.mark.parametrize("runtime", [1, 100, 999])
    def test_runtime_boundary_values(self, runtime):
        """Test runtime boundary values are accepted."""
        movie_update = MovieUpdate(runtime=runtime)
        assert movie_update.runtime == runtime

    @pytest.mark.parametrize("invalid_rating", [-1.0, 10.1, -100.0, 100.0])
    def test_invalid_rating_values(self, invalid_rating):
        """Test invalid rating values are rejected."""
        with pytest.raises(ValidationError):
            MovieUpdate(rating=invalid_rating)

    @pytest.mark.parametrize("invalid_year", [1887, 2101])
    def test_invalid_year_values(self, invalid_year):
        """Test invalid year values are rejected."""
        with pytest.raises(ValidationError):
            MovieUpdate(release_year=invalid_year)
