"""
Tests for MovieSearchFilters schema using multiple testing methodologies.
"""

import pytest
from pydantic import ValidationError

from backend.schemas.movies import MovieSearchFilters


class TestMovieSearchFiltersSchema:
    """Comprehensive tests for MovieSearchFilters schema functionality."""

    def test_complete_valid_filters(self):
        """Test MovieSearchFilters with all valid filter fields."""
        data = {
            "title": "shawshank",
            "genre": "Drama",
            "min_year": 1990,
            "max_year": 2000,
            "min_rating": 8.5,
            "director": "Frank Darabont",
        }

        filters = MovieSearchFilters(**data)
        assert filters.title == data["title"]
        assert filters.genre == data["genre"]
        assert filters.min_year == data["min_year"]
        assert filters.max_year == data["max_year"]
        assert filters.min_rating == data["min_rating"]
        assert filters.director == data["director"]

    @pytest.mark.parametrize(
        "filters",
        [
            {"title": "test"},
            {"genre": "Action"},
            {"min_year": 2000, "max_year": 2010},
            {"min_rating": 8.0},
            {"director": "Director"},
            {"title": "test", "genre": "Action", "min_rating": 7.0},
        ],
    )
    def test_partial_filters(self, filters):
        """Test various filter combinations work correctly."""
        filter_obj = MovieSearchFilters(**filters)

        for key, value in filters.items():
            assert getattr(filter_obj, key) == value

    @pytest.mark.parametrize("invalid_year", [1887, 2101])
    def test_year_validation(self, invalid_year):
        """Test year validation rejects invalid values."""
        with pytest.raises(ValidationError):
            MovieSearchFilters(min_year=invalid_year)

        with pytest.raises(ValidationError):
            MovieSearchFilters(max_year=invalid_year)

    @pytest.mark.parametrize("invalid_rating", [-1, 11])
    def test_rating_validation(self, invalid_rating):
        """Test rating validation rejects invalid values."""
        with pytest.raises(ValidationError):
            MovieSearchFilters(min_rating=invalid_rating)

    @pytest.mark.parametrize("year", [1888, 1889, 2099, 2100])
    def test_year_boundary_values(self, year):
        """Test year boundary values are accepted."""
        filters_min = MovieSearchFilters(min_year=year)
        assert filters_min.min_year == year

        filters_max = MovieSearchFilters(max_year=year)
        assert filters_max.max_year == year

    @pytest.mark.parametrize("rating", [0.0, 0.1, 9.9, 10.0])
    def test_rating_boundary_values(self, rating):
        """Test rating boundary values are accepted."""
        filters = MovieSearchFilters(min_rating=rating)
        assert filters.min_rating == rating

    def test_extra_fields_rejection(self):
        """Test that extra fields are properly rejected."""
        with pytest.raises(ValidationError) as exc_info:
            MovieSearchFilters(title="test", invalid_field="This should not be allowed")

        error_str = str(exc_info.value)
        assert "extra" in error_str.lower() or "forbidden" in error_str.lower()

    @pytest.mark.parametrize(
        "year_pair",
        [
            {"min_year": 2000, "max_year": 1999},
            {"min_year": 2020, "max_year": 2010},
        ],
    )
    def test_invalid_year_ranges(self, year_pair):
        """Test that invalid year ranges don't cause validation errors."""
        # Note: Schema doesn't validate min_year <= max_year
        filters = MovieSearchFilters(**year_pair)
        assert filters.min_year == year_pair["min_year"]
        assert filters.max_year == year_pair["max_year"]
