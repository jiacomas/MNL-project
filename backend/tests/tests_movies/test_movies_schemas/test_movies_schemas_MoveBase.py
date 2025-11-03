"""
Tests for MovieBase schema using multiple testing methodologies.
"""
import pytest
from pydantic import ValidationError
from backend.app.schemas.movies import MovieBase


class TestMovieBaseSchema:
    """Comprehensive tests for MovieBase schema with multiple testing methodologies"""

    # Equivalence Partitioning Tests
    @pytest.mark.parametrize("valid_title", [
        "A",  # Minimum length
        "Test Movie",  # Normal case
        "A" * 500,  # Maximum length
        "Movie with 123 numbers",  # Alphanumeric
        "Movie with-special_chars",  # Special characters
    ])
    def test_movie_base_title_equivalence_partitioning_valid(self, valid_title):
        """Test title field with valid equivalence partitions"""
        movie = MovieBase(title=valid_title)
        assert movie.title == valid_title

    @pytest.mark.parametrize("invalid_title", [
        "",  # Empty string
        "   ",  # Only whitespace
        "A" * 501,  # Exceeds maximum length
    ])
    def test_movie_base_title_equivalence_partitioning_invalid(self, invalid_title):
        """Test title field with invalid equivalence partitions"""
        with pytest.raises(ValidationError):
            MovieBase(title=invalid_title)

    @pytest.mark.parametrize("rating,expected", [
        (0.0, 0.0),  # Minimum boundary
        (5.5, 5.5),  # Middle value
        (10.0, 10.0),  # Maximum boundary
        (None, None),  # Optional field
    ])
    def test_movie_base_rating_equivalence_partitioning(self, rating, expected):
        """Test rating field with boundary value analysis"""
        movie = MovieBase(title="Test Movie", rating=rating)
        assert movie.rating == expected

    @pytest.mark.parametrize("invalid_rating", [
        -0.1,  # Below minimum
        10.1,  # Above maximum
        -100.0,  # Far below minimum
        100.0,  # Far above maximum
    ])
    def test_movie_base_rating_fault_injection(self, invalid_rating):
        """Fault injection: Test rating with invalid values"""
        with pytest.raises(ValidationError):
            MovieBase(title="Test Movie", rating=invalid_rating)

    # Fault Injection Tests
    def test_movie_base_invalid_field_types(self):
        """Fault injection: Test with incorrect data types"""
        # Test with string instead of number for release_year
        with pytest.raises(ValidationError):
            MovieBase(title="Test", release_year="not-a-number")

        # Test with string instead of number for rating
        with pytest.raises(ValidationError):
            MovieBase(title="Test", rating="high")

    def test_movie_base_extra_fields_rejection(self):
        """Fault injection: Test that extra fields are rejected"""
        with pytest.raises(ValidationError) as exc_info:
            MovieBase(
                title="Test Movie",
                invalid_field="This should not be allowed",
                another_invalid_field=123
            )
        # Check that validation error was raised for extra fields
        error_str = str(exc_info.value)
        assert "extra" in error_str.lower() or "forbidden" in error_str.lower()

    def test_movie_base_valid_data(self):
        """Test MovieBase with valid data"""
        data = {
            "title": "The Shawshank Redemption",
            "genre": "Drama",
            "release_year": 1994,
            "rating": 9.3,
            "runtime": 142,
            "director": "Frank Darabont",
            "cast": "Tim Robbins, Morgan Freeman",
            "plot": "Two imprisoned men bond over a number of years...",
            "poster_url": "https://example.com/poster.jpg"
        }

        movie = MovieBase(**data)
        assert movie.title == data["title"]
        assert movie.genre == data["genre"]
        assert movie.release_year == data["release_year"]
        assert movie.rating == data["rating"]
        assert movie.runtime == data["runtime"]
        assert movie.director == data["director"]
        assert movie.cast == data["cast"]
        assert movie.plot == data["plot"]
        assert movie.poster_url == data["poster_url"]

    def test_movie_base_optional_fields(self):
        """Test MovieBase with only required fields"""
        data = {
            "title": "Test Movie"
        }

        movie = MovieBase(**data)
        assert movie.title == "Test Movie"
        assert movie.genre is None
        assert movie.release_year is None
        assert movie.rating is None
        assert movie.runtime is None
        assert movie.director is None
        assert movie.cast is None
        assert movie.plot is None
        assert movie.poster_url is None

    def test_movie_base_title_validation(self):
        """Test MovieBase title validation"""
        # Test empty title
        with pytest.raises(ValidationError):
            MovieBase(title="")

        # Test title too long
        with pytest.raises(ValidationError):
            MovieBase(title="a" * 501)

    def test_movie_base_rating_validation(self):
        """Test MovieBase rating validation"""
        # Test rating below minimum
        with pytest.raises(ValidationError):
            MovieBase(title="Test", rating=-1)

        # Test rating above maximum
        with pytest.raises(ValidationError):
            MovieBase(title="Test", rating=11)

    def test_movie_base_year_validation(self):
        """Test MovieBase release year validation"""
        # Test year below minimum
        with pytest.raises(ValidationError):
            MovieBase(title="Test", release_year=1887)

        # Test year above maximum
        with pytest.raises(ValidationError):
            MovieBase(title="Test", release_year=2101)

    def test_movie_base_string_normalization(self):
        """Test string field normalization"""
        data = {
            "title": "  Test Movie  ",
            "genre": "  Drama  ",
            "director": "  Director Name  ",
            "cast": "  Actor 1, Actor 2  ",
            "plot": "  Plot summary  ",
            "poster_url": "  https://example.com/poster.jpg  "
        }

        movie = MovieBase(**data)
        assert movie.title == "Test Movie"
        assert movie.genre == "Drama"
        assert movie.director == "Director Name"
        assert movie.cast == "Actor 1, Actor 2"
        assert movie.plot == "Plot summary"
        assert movie.poster_url == "https://example.com/poster.jpg"

    def test_movie_base_empty_string_normalization(self):
        """Test empty string fields are normalized to None"""
        data = {
            "title": "Test Movie",
            "genre": "   ",
            "director": "",
            "cast": "  ",
            "plot": "",
            "poster_url": "   "
        }

        movie = MovieBase(**data)
        assert movie.genre is None
        assert movie.director is None
        assert movie.cast is None
        assert movie.plot is None
        assert movie.poster_url is None