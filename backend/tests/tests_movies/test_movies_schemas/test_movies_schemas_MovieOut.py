"""
Tests for MovieOut schema using multiple testing methodologies.
"""
import pytest
from datetime import datetime, timezone
from pydantic import ValidationError
from backend.schemas.movies import MovieOut


class TestMovieOutSchema:
    """Comprehensive tests for MovieOut schema with multiple testing methodologies"""

    def test_movie_out_valid_data(self):
        """Test MovieOut with valid data"""
        now = datetime.now(timezone.utc)
        data = {
            "movie_id": "tt0111161",
            "title": "The Shawshank Redemption",
            "genre": "Drama",
            "release_year": 1994,
            "rating": 9.3,
            "runtime": 142,
            "director": "Frank Darabont",
            "cast": "Tim Robbins, Morgan Freeman",
            "plot": "Two imprisoned men bond over a number of years...",
            "poster_url": "https://example.com/poster.jpg",
            "created_at": now,
            "updated_at": now,
            "review_count": 2500000
        }

        movie = MovieOut(**data)
        assert movie.movie_id == data["movie_id"]
        assert movie.title == data["title"]
        assert movie.genre == data["genre"]
        assert movie.release_year == data["release_year"]
        assert movie.rating == data["rating"]
        assert movie.runtime == data["runtime"]
        assert movie.director == data["director"]
        assert movie.cast == data["cast"]
        assert movie.plot == data["plot"]
        assert movie.poster_url == data["poster_url"]
        assert movie.created_at == data["created_at"]
        assert movie.updated_at == data["updated_at"]
        assert movie.review_count == data["review_count"]

    def test_movie_out_default_review_count(self):
        """Test MovieOut default review_count"""
        now = datetime.now(timezone.utc)
        data = {
            "movie_id": "tt0111161",
            "title": "Test Movie",
            "created_at": now,
            "updated_at": now
        }

        movie = MovieOut(**data)
        assert movie.review_count == 0

    # Exception Handling Tests
    def test_movie_out_missing_required_fields(self):
        """Test MovieOut with missing required fields"""
        # Missing movie_id
        with pytest.raises(ValidationError):
            MovieOut(title="Test Movie")

        # Missing created_at
        with pytest.raises(ValidationError):
            MovieOut(movie_id="tt0111161", title="Test Movie", updated_at=datetime.now(timezone.utc))

        # Missing updated_at
        with pytest.raises(ValidationError):
            MovieOut(movie_id="tt0111161", title="Test Movie", created_at=datetime.now(timezone.utc))

    def test_movie_out_extra_fields_rejection(self):
        """Fault injection: Test that extra fields are rejected in MovieOut"""
        now = datetime.now(timezone.utc)
        with pytest.raises(ValidationError) as exc_info:
            MovieOut(
                movie_id="tt0111161",
                title="Test Movie",
                created_at=now,
                updated_at=now,
                invalid_field="This should not be allowed"
            )
        # Check that validation error was raised for extra fields
        error_str = str(exc_info.value)
        assert "extra" in error_str.lower() or "forbidden" in error_str.lower()

    # Equivalence Partitioning Tests
    @pytest.mark.parametrize("review_count,expected", [
        (0, 0),  # Minimum
        (1000, 1000),  # Normal value
        (1000000, 1000000),  # Large value
    ])
    def test_movie_out_review_count_equivalence_partitioning(self, review_count, expected):
        """Test review_count field with equivalence partitioning"""
        now = datetime.now(timezone.utc)
        data = {
            "movie_id": "tt0111161",
            "title": "Test Movie",
            "created_at": now,
            "updated_at": now,
            "review_count": review_count
        }

        movie = MovieOut(**data)
        assert movie.review_count == expected

    # Boundary Value Analysis
    def test_movie_out_datetime_validation(self):
        """Test MovieOut with various datetime formats"""
        now = datetime.now(timezone.utc)
        past_date = datetime(2020, 1, 1, tzinfo=timezone.utc)
        future_date = datetime(2030, 1, 1, tzinfo=timezone.utc)

        # Test with past date
        movie = MovieOut(
            movie_id="tt0111161",
            title="Test Movie",
            created_at=past_date,
            updated_at=now
        )
        assert movie.created_at == past_date

        # Test with future date
        movie = MovieOut(
            movie_id="tt0111161",
            title="Test Movie",
            created_at=now,
            updated_at=future_date
        )
        assert movie.updated_at == future_date