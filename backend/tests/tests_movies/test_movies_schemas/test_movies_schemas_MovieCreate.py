"""
Tests for MovieCreate schema using multiple testing methodologies.
"""
import pytest
from pydantic import ValidationError
from backend.app.schemas.movies import MovieCreate


class TestMovieCreateSchema:
    """Comprehensive tests for MovieCreate schema with multiple testing methodologies"""

    def test_movie_create_valid_data(self):
        """Test MovieCreate with valid data"""
        data = {
            "movie_id": "tt0111161",
            "title": "The Shawshank Redemption",
            "genre": "Drama",
            "release_year": 1994
        }

        movie = MovieCreate(**data)
        assert movie.movie_id == data["movie_id"]
        assert movie.title == data["title"]
        assert movie.genre == data["genre"]
        assert movie.release_year == data["release_year"]

    def test_movie_create_auto_generate_id(self):
        """Test MovieCreate without movie_id"""
        data = {
            "title": "Test Movie"
        }

        movie = MovieCreate(**data)
        assert movie.movie_id is None

    def test_movie_create_movie_id_normalization(self):
        """Test MovieCreate movie_id field normalization"""
        # Test with whitespace-only movie_id
        data = {
            "title": "Test Movie",
            "movie_id": "   "  # Only whitespace
        }

        movie = MovieCreate(**data)
        assert movie.movie_id is None

        # Test with movie_id with leading/trailing whitespace
        data = {
            "title": "Test Movie",
            "movie_id": "  tt0111161  "
        }

        movie = MovieCreate(**data)
        assert movie.movie_id == "tt0111161"

        # Test with empty string movie_id
        data = {
            "title": "Test Movie",
            "movie_id": ""
        }

        movie = MovieCreate(**data)
        assert movie.movie_id is None

    def test_movie_create_extra_fields_rejection(self):
        """Fault injection: Test that extra fields are rejected in MovieCreate"""
        with pytest.raises(ValidationError) as exc_info:
            MovieCreate(
                title="Test Movie",
                movie_id="tt0111161",
                invalid_field="This should not be allowed"
            )
        # Check that validation error was raised for extra fields
        error_str = str(exc_info.value)
        assert "extra" in error_str.lower() or "forbidden" in error_str.lower()

    # Exception Handling Tests
    def test_movie_create_invalid_release_year(self):
        """Test MovieCreate with invalid release year"""
        with pytest.raises(ValidationError) as exc_info:
            MovieCreate(
                title="Test Movie",
                release_year=1890  # Below minimum of 1895
            )
        assert "Release year must be at least 1895" in str(exc_info.value)

    def test_movie_create_valid_release_year_boundary(self):
        """Test MovieCreate with boundary release year values"""
        # Test minimum valid release year
        movie = MovieCreate(title="Test Movie", release_year=1895)
        assert movie.release_year == 1895

        # Test normal release year
        movie = MovieCreate(title="Test Movie", release_year=2020)
        assert movie.release_year == 2020

    # Equivalence Partitioning Tests
    @pytest.mark.parametrize("movie_id_input,expected", [
        (None, None),  # No ID provided
        ("tt0111161", "tt0111161"),  # Normal ID
        ("  tt0111161  ", "tt0111161"),  # ID with whitespace
        ("", None),  # Empty string
        ("   ", None),  # Whitespace only
    ])
    def test_movie_create_movie_id_equivalence_partitioning(self, movie_id_input, expected):
        """Test movie_id field with equivalence partitioning"""
        movie = MovieCreate(title="Test Movie", movie_id=movie_id_input)
        assert movie.movie_id == expected