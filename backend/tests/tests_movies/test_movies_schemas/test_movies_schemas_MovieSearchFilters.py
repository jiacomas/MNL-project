"""
Tests for MovieSearchFilters schema using multiple testing methodologies.
"""
import pytest
from pydantic import ValidationError
from backend.schemas.movies import MovieSearchFilters


class TestMovieSearchFiltersSchema:
    """Comprehensive tests for MovieSearchFilters schema with multiple testing methodologies"""

    def test_movie_search_filters_valid_data(self):
        """Test MovieSearchFilters with valid data"""
        data = {
            "title": "shawshank",
            "genre": "Drama",
            "min_year": 1990,
            "max_year": 2000,
            "min_rating": 8.5,
            "director": "Frank Darabont"
        }

        filters = MovieSearchFilters(**data)
        assert filters.title == data["title"]
        assert filters.genre == data["genre"]
        assert filters.min_year == data["min_year"]
        assert filters.max_year == data["max_year"]
        assert filters.min_rating == data["min_rating"]
        assert filters.director == data["director"]

    def test_movie_search_filters_partial_data(self):
        """Test MovieSearchFilters with partial data"""
        # Only title filter
        filters = MovieSearchFilters(title="test")
        assert filters.title == "test"
        assert filters.genre is None
        assert filters.min_year is None
        assert filters.max_year is None
        assert filters.min_rating is None
        assert filters.director is None

        # Only genre and min_rating
        filters = MovieSearchFilters(genre="Action", min_rating=7.0)
        assert filters.title is None
        assert filters.genre == "Action"
        assert filters.min_rating == 7.0
        assert filters.max_year is None

    def test_movie_search_filters_year_validation(self):
        """Test MovieSearchFilters year validation"""
        # Test min_year below minimum
        with pytest.raises(ValidationError):
            MovieSearchFilters(min_year=1887)

        # Test max_year above maximum
        with pytest.raises(ValidationError):
            MovieSearchFilters(max_year=2101)

        # Test min_rating validation
        with pytest.raises(ValidationError):
            MovieSearchFilters(min_rating=-1)

        with pytest.raises(ValidationError):
            MovieSearchFilters(min_rating=11)

    # Boundary Value Analysis
    @pytest.mark.parametrize("year", [1888, 1889, 2099, 2100])
    def test_movie_search_filters_year_boundary_values(self, year):
        """Test MovieSearchFilters with year boundary values"""
        # Test min_year boundary values
        filters = MovieSearchFilters(min_year=year)
        assert filters.min_year == year

        # Test max_year boundary values
        filters = MovieSearchFilters(max_year=year)
        assert filters.max_year == year

    @pytest.mark.parametrize("rating", [0.0, 0.1, 9.9, 10.0])
    def test_movie_search_filters_rating_boundary_values(self, rating):
        """Test MovieSearchFilters with rating boundary values"""
        filters = MovieSearchFilters(min_rating=rating)
        assert filters.min_rating == rating

    def test_movie_search_filters_extra_fields_rejection(self):
        """Fault injection: Test that extra fields are rejected in MovieSearchFilters"""
        with pytest.raises(ValidationError) as exc_info:
            MovieSearchFilters(
                title="test",
                invalid_field="This should not be allowed"
            )
        # Check that validation error was raised for extra fields
        error_str = str(exc_info.value)
        assert "extra" in error_str.lower() or "forbidden" in error_str.lower()

    # Equivalence Partitioning Tests
    @pytest.mark.parametrize("filter_combination", [
        {"title": "test"},  # Only title
        {"genre": "Drama"},  # Only genre
        {"min_year": 2000, "max_year": 2010},  # Year range
        {"min_rating": 8.0},  # Only rating
        {"director": "Director"},  # Only director
        {"title": "test", "genre": "Action", "min_rating": 7.0},  # Multiple filters
    ])
    def test_movie_search_filters_combination_equivalence(self, filter_combination):
        """Test various filter combinations with equivalence partitioning"""
        filters = MovieSearchFilters(**filter_combination)

        for key, value in filter_combination.items():
            assert getattr(filters, key) == value

    # Fault Injection Tests
    @pytest.mark.parametrize("invalid_year_pair", [
        {"min_year": 2000, "max_year": 1999},  # min > max
        {"min_year": 2020, "max_year": 2010},  # min > max
    ])
    def test_movie_search_filters_invalid_year_range_fault_injection(self, invalid_year_pair):
        """Fault injection: Test invalid year ranges (note: schema doesn't validate min <= max)"""
        # This test documents that the schema doesn't validate min_year <= max_year
        # If this validation is added later, this test should be updated
        filters = MovieSearchFilters(**invalid_year_pair)
        assert filters.min_year == invalid_year_pair["min_year"]
        assert filters.max_year == invalid_year_pair["max_year"]