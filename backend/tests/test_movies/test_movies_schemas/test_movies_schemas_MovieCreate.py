"""
Tests for MovieCreate schema using multiple testing methodologies.
"""

import pytest
from pydantic import ValidationError

from schemas.movies import MovieCreate


class TestMovieCreateSchema:
    """Comprehensive tests for MovieCreate schema functionality."""

    def test_complete_valid_data(self):
        """Test MovieCreate with all fields populated."""
        data = {
            "movie_id": "tt0111161",
            "title": "The Shawshank Redemption",
            "genre": "Drama",
            "release_year": 1994,
        }

        movie = MovieCreate(**data)
        assert movie.movie_id == data["movie_id"]
        assert movie.title == data["title"]
        assert movie.genre == data["genre"]
        assert movie.release_year == data["release_year"]

    def test_auto_generated_id_scenario(self):
        """Test MovieCreate without movie_id field."""
        movie = MovieCreate(title="Test Movie")
        assert movie.movie_id is None

    @pytest.mark.parametrize(
        "movie_id_input,expected",
        [
            (None, None),  # No ID provided
            ("tt0111161", "tt0111161"),  # Normal ID
            ("  tt0111161  ", "tt0111161"),  # ID with whitespace
            ("", None),  # Empty string
            ("   ", None),  # Whitespace only
        ],
    )
    def test_movie_id_normalization(self, movie_id_input, expected):
        """Test movie_id field normalization with various inputs."""
        movie = MovieCreate(title="Test Movie", movie_id=movie_id_input)
        assert movie.movie_id == expected

    def test_extra_fields_rejection(self):
        """Test that extra fields are properly rejected."""
        with pytest.raises(ValidationError) as exc_info:
            MovieCreate(
                title="Test Movie",
                movie_id="tt0111161",
                invalid_field="This should not be allowed",
            )

        error_str = str(exc_info.value)
        assert "extra" in error_str.lower() or "forbidden" in error_str.lower()

    def test_invalid_release_year_validation(self):
        """Test custom release year validation."""
        with pytest.raises(ValidationError) as exc_info:
            MovieCreate(title="Test Movie", release_year=1890)

        assert "Release year must be at least 1895" in str(exc_info.value)

    @pytest.mark.parametrize("valid_year", [1895, 2000, 2020])
    def test_valid_release_years(self, valid_year):
        """Test valid release year values are accepted."""
        movie = MovieCreate(title="Test Movie", release_year=valid_year)
        assert movie.release_year == valid_year
