"""
Tests for MovieUpdate schema using multiple testing methodologies.
"""
import pytest
from pydantic import ValidationError
from backend.app.schemas.movies import MovieUpdate


class TestMovieUpdateSchema:
    """Comprehensive tests for MovieUpdate schema with multiple testing methodologies"""

    def test_movie_update_valid_data(self):
        """Test MovieUpdate with valid data"""
        data = {
            "rating": 9.5,
            "poster_url": "https://updated-poster.com/image.jpg"
        }

        movie_update = MovieUpdate(**data)
        assert movie_update.rating == data["rating"]
        assert movie_update.poster_url == data["poster_url"]

    def test_movie_update_no_fields_provided(self):
        """Test MovieUpdate validation when no fields are provided"""
        with pytest.raises(ValidationError) as exc_info:
            MovieUpdate()

        assert "At least one field must be provided for update" in str(exc_info.value)

    def test_movie_update_string_normalization(self):
        """Test MovieUpdate string field normalization"""
        data = {
            "title": "  Updated Title  ",
            "genre": "  Updated Genre  ",
            "director": "  New Director  "
        }

        movie_update = MovieUpdate(**data)
        assert movie_update.title == "Updated Title"
        assert movie_update.genre == "Updated Genre"
        assert movie_update.director == "New Director"

    def test_movie_update_partial_data(self):
        """Test MovieUpdate with partial data"""
        # Only update rating
        movie_update = MovieUpdate(rating=8.5)
        assert movie_update.rating == 8.5
        assert movie_update.title is None

        # Only update title
        movie_update = MovieUpdate(title="New Title")
        assert movie_update.title == "New Title"
        assert movie_update.rating is None

    # Equivalence Partitioning Tests
    @pytest.mark.parametrize("field_name,valid_value", [
        ("title", "Valid Title"),
        ("genre", "Action"),
        ("release_year", 2020),
        ("rating", 8.5),
        ("runtime", 120),
        ("director", "Director Name"),
        ("cast", "Actor 1, Actor 2"),
        ("plot", "Plot summary"),
        ("poster_url", "https://example.com/poster.jpg"),
    ])
    def test_movie_update_single_field_validation(self, field_name, valid_value):
        """Test MovieUpdate with each field individually"""
        data = {field_name: valid_value}
        movie_update = MovieUpdate(**data)
        assert getattr(movie_update, field_name) == valid_value

    def test_movie_update_extra_fields_rejection(self):
        """Fault injection: Test that extra fields are rejected in MovieUpdate"""
        with pytest.raises(ValidationError) as exc_info:
            MovieUpdate(
                title="Updated Title",
                invalid_field="This should not be allowed"
            )
        # Check that validation error was raised for extra fields
        error_str = str(exc_info.value)
        assert "extra" in error_str.lower() or "forbidden" in error_str.lower()

    # Boundary Value Analysis
    @pytest.mark.parametrize("rating", [0.0, 5.0, 10.0])
    def test_movie_update_rating_boundary_values(self, rating):
        """Test MovieUpdate with rating boundary values"""
        movie_update = MovieUpdate(rating=rating)
        assert movie_update.rating == rating

    @pytest.mark.parametrize("runtime", [1, 100, 999])
    def test_movie_update_runtime_boundary_values(self, runtime):
        """Test MovieUpdate with runtime boundary values"""
        movie_update = MovieUpdate(runtime=runtime)
        assert movie_update.runtime == runtime

    # Fault Injection Tests
    @pytest.mark.parametrize("invalid_rating", [-1.0, 10.1, -100.0, 100.0])
    def test_movie_update_invalid_rating_fault_injection(self, invalid_rating):
        """Fault injection: Test MovieUpdate with invalid rating values"""
        with pytest.raises(ValidationError):
            MovieUpdate(rating=invalid_rating)

    @pytest.mark.parametrize("invalid_year", [1887, 2101])
    def test_movie_update_invalid_year_fault_injection(self, invalid_year):
        """Fault injection: Test MovieUpdate with invalid year values"""
        with pytest.raises(ValidationError):
            MovieUpdate(release_year=invalid_year)