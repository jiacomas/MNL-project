"""
Tests for MovieOut schema using multiple testing methodologies.
"""
import pytest
from datetime import datetime, timezone
from pydantic import ValidationError
from schemas.movies import MovieOut


class TestMovieOutSchema:
    """Comprehensive tests for MovieOut schema functionality."""

    def test_complete_valid_data(self):
        """Test MovieOut with all fields populated."""
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

        for field, value in data.items():
            assert getattr(movie, field) == value

    def test_default_review_count(self):
        """Test MovieOut uses default review_count when not provided."""
        now = datetime.now(timezone.utc)
        data = {
            "movie_id": "tt0111161",
            "title": "Test Movie",
            "created_at": now,
            "updated_at": now
        }

        movie = MovieOut(**data)
        assert movie.review_count == 0

    @pytest.mark.parametrize("missing_field", ["movie_id", "created_at", "updated_at"])
    def test_required_fields_validation(self, missing_field):
        """Test MovieOut validation fails when required fields are missing."""
        now = datetime.now(timezone.utc)
        data = {
            "movie_id": "tt0111161",
            "title": "Test Movie",
            "created_at": now,
            "updated_at": now
        }
        data.pop(missing_field)

        with pytest.raises(ValidationError):
            MovieOut(**data)

    def test_extra_fields_rejection(self):
        """Test that extra fields are properly rejected."""
        now = datetime.now(timezone.utc)
        with pytest.raises(ValidationError) as exc_info:
            MovieOut(
                movie_id="tt0111161",
                title="Test Movie",
                created_at=now,
                updated_at=now,
                invalid_field="This should not be allowed"
            )

        error_str = str(exc_info.value)
        assert "extra" in error_str.lower() or "forbidden" in error_str.lower()

    @pytest.mark.parametrize("review_count,expected", [
        (0, 0),  # Minimum
        (1000, 1000),  # Normal value
        (1000000, 1000000),  # Large value
    ])
    def test_review_count_values(self, review_count, expected):
        """Test review_count field accepts various valid values."""
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

    @pytest.mark.parametrize("past_date", [
        datetime(2020, 1, 1, tzinfo=timezone.utc),
        datetime(1990, 1, 1, tzinfo=timezone.utc),
    ])
    def test_past_dates_acceptance(self, past_date):
        """Test MovieOut accepts past datetime values."""
        now = datetime.now(timezone.utc)
        movie = MovieOut(
            movie_id="tt0111161",
            title="Test Movie",
            created_at=past_date,
            updated_at=now
        )
        assert movie.created_at == past_date

    def test_future_dates_acceptance(self):
        """Test MovieOut accepts future datetime values."""
        now = datetime.now(timezone.utc)
        future_date = datetime(2030, 1, 1, tzinfo=timezone.utc)

        movie = MovieOut(
            movie_id="tt0111161",
            title="Test Movie",
            created_at=now,
            updated_at=future_date
        )
        assert movie.updated_at == future_date