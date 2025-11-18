"""
Tests for MovieBase schema using multiple testing methodologies.
"""

import pytest
from pydantic import ValidationError

from backend.schemas.movies import MovieBase


class TestMovieBaseSchema:
    """Comprehensive tests for MovieBase schema validation and functionality."""

    # Equivalence Partitioning Tests
    @pytest.mark.parametrize(
        "valid_title",
        [
            "A",  # Minimum length
            "Test Movie",  # Normal case
            "A" * 500,  # Maximum length
            "Movie with 123 numbers",  # Alphanumeric
            "Movie with-special_chars",  # Special characters
        ],
    )
    def test_title_validation_valid_cases(self, valid_title):
        """Test title field accepts valid equivalence partitions."""
        movie = MovieBase(title=valid_title)
        assert movie.title == valid_title

    @pytest.mark.parametrize(
        "invalid_title",
        [
            "",  # Empty string
            "   ",  # Only whitespace
            "A" * 501,  # Exceeds maximum length
        ],
    )
    def test_title_validation_invalid_cases(self, invalid_title):
        """Test title field rejects invalid equivalence partitions."""
        with pytest.raises(ValidationError):
            MovieBase(title=invalid_title)

    @pytest.mark.parametrize(
        "rating,expected",
        [
            (0.0, 0.0),  # Minimum boundary
            (5.5, 5.5),  # Middle value
            (10.0, 10.0),  # Maximum boundary
            (None, None),  # Optional field
        ],
    )
    def test_rating_boundary_values(self, rating, expected):
        """Test rating field with boundary value analysis."""
        movie = MovieBase(title="Test Movie", rating=rating)
        assert movie.rating == expected

    @pytest.mark.parametrize(
        "invalid_rating",
        [
            -0.1,  # Below minimum
            10.1,  # Above maximum
            -100.0,  # Far below minimum
            100.0,  # Far above maximum
        ],
    )
    def test_rating_invalid_values(self, invalid_rating):
        """Test rating field rejects invalid values."""
        with pytest.raises(ValidationError):
            MovieBase(title="Test Movie", rating=invalid_rating)

    def test_complete_valid_data(self):
        """Test MovieBase with all valid fields populated."""
        data = {
            "title": "The Shawshank Redemption",
            "genre": "Drama",
            "release_year": 1994,
            "rating": 9.3,
            "runtime": 142,
            "director": "Frank Darabont",
            "cast": "Tim Robbins, Morgan Freeman",
            "plot": "Two imprisoned men bond over a number of years...",
            "poster_url": "https://example.com/poster.jpg",
        }
        movie = MovieBase(**data)

        for field, value in data.items():
            assert getattr(movie, field) == value

    def test_required_fields_only(self):
        """Test MovieBase with only required title field."""
        movie = MovieBase(title="Test Movie")
        assert movie.title == "Test Movie"
        assert movie.genre is None
        assert movie.release_year is None
        assert movie.rating is None

    @pytest.mark.parametrize("year", [1887, 2101])
    def test_release_year_validation(self, year):
        """Test release year validation with invalid values."""
        with pytest.raises(ValidationError):
            MovieBase(title="Test", release_year=year)

    def test_string_normalization(self):
        """Test string fields are properly normalized with whitespace stripping."""
        data = {
            "title": "  Test Movie  ",
            "genre": "  Drama  ",
            "director": "  Director Name  ",
            "cast": "  Actor 1, Actor 2  ",
            "plot": "  Plot summary  ",
            "poster_url": "  https://example.com/poster.jpg  ",
        }
        movie = MovieBase(**data)

        assert movie.title == "Test Movie"
        assert movie.genre == "Drama"
        assert movie.director == "Director Name"
        assert movie.cast == "Actor 1, Actor 2"
        assert movie.plot == "Plot summary"
        assert movie.poster_url == "https://example.com/poster.jpg"

    def test_empty_string_normalization(self):
        """Test empty string fields are normalized to None."""
        data = {
            "title": "Test Movie",
            "genre": "   ",
            "director": "",
            "cast": "  ",
            "plot": "",
            "poster_url": "   ",
        }
        movie = MovieBase(**data)

        assert movie.genre is None
        assert movie.director is None
        assert movie.cast is None
        assert movie.plot is None
        assert movie.poster_url is None

    def test_invalid_data_types(self):
        """Test validation fails with incorrect data types."""
        with pytest.raises(ValidationError):
            MovieBase(title="Test", release_year="not-a-number")

        with pytest.raises(ValidationError):
            MovieBase(title="Test", rating="high")

    def test_extra_fields_rejection(self):
        """Test that extra fields are properly rejected."""
        with pytest.raises(ValidationError) as exc_info:
            MovieBase(
                title="Test Movie",
                invalid_field="This should not be allowed",
                another_invalid_field=123,
            )

        error_str = str(exc_info.value)
        assert "extra" in error_str.lower() or "forbidden" in error_str.lower()
