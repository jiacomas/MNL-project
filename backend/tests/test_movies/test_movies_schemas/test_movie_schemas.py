"""
Consolidated basic schema tests for all movie schemas.
"""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from backend.schemas.movies import (
    MovieBase,
    MovieCreate,
    MovieListResponse,
    MovieOut,
    MovieSearchFilters,
    MovieUpdate,
)


class TestMovieBaseSchema:
    """Tests for MovieBase schema validation."""

    @pytest.mark.parametrize(
        "title,is_valid",
        [
            ("A", True),  # Min length
            ("A" * 500, True),  # Max length
            ("", False),  # Empty
            ("   ", False),  # Only whitespace
            ("A" * 501, False),  # Too long
        ],
    )
    def test_title_validation(self, title, is_valid):
        if is_valid:
            movie = MovieBase(title=title)
            assert movie.title == title.strip() if title.strip() else title
        else:
            with pytest.raises(ValidationError):
                MovieBase(title=title)

    @pytest.mark.parametrize(
        "field,value,is_valid",
        [
            ("rating", 0.0, True),
            ("rating", 10.0, True),
            ("rating", -0.1, False),
            ("rating", 10.1, False),
            ("release_year", 1888, True),
            ("release_year", 2100, True),
            ("release_year", 1887, False),
            ("release_year", 2101, False),
            ("runtime", 1, True),
            ("runtime", 999, True),
            ("runtime", 0, False),
            ("runtime", 1000, False),
        ],
    )
    def test_numeric_field_validation(self, field, value, is_valid):
        data = {"title": "Test Movie", field: value}
        if is_valid:
            movie = MovieBase(**data)
            assert getattr(movie, field) == value
        else:
            with pytest.raises(ValidationError):
                MovieBase(**data)

    def test_string_normalization(self):
        data = {
            "title": "  Test Movie  ",
            "genre": "  Drama  ",
            "director": "  Director  ",
        }
        movie = MovieBase(**data)
        assert movie.title == "Test Movie"
        assert movie.genre == "Drama"
        assert movie.director == "Director"

    def test_empty_strings_become_none(self):
        data = {
            "title": "Test Movie",
            "genre": "   ",
            "director": "",
        }
        movie = MovieBase(**data)
        assert movie.genre is None
        assert movie.director is None


class TestMovieCreateSchema:
    """Tests for MovieCreate schema."""

    def test_movie_id_normalization(self):
        movie = MovieCreate(title="Test", movie_id="  tt123  ")
        assert movie.movie_id == "tt123"

        movie = MovieCreate(title="Test", movie_id="   ")
        assert movie.movie_id is None

    @pytest.mark.parametrize("year", [1890, 1894])
    def test_release_year_validation(self, year):
        with pytest.raises(ValidationError) as exc_info:
            MovieCreate(title="Test", release_year=year)
        assert "Release year must be at least 1895" in str(exc_info.value)


class TestMovieUpdateSchema:
    """Tests for MovieUpdate schema."""

    def test_at_least_one_field_required(self):
        with pytest.raises(ValidationError) as exc_info:
            MovieUpdate()
        assert "At least one field must be provided" in str(exc_info.value)

    def test_partial_update_valid(self):
        update = MovieUpdate(rating=9.5)
        assert update.rating == 9.5
        assert update.title is None


class TestMovieOutSchema:
    """Tests for MovieOut schema."""

    def test_required_fields(self):
        now = datetime.now(timezone.utc)
        data = {
            "movie_id": "tt123",
            "title": "Test Movie",
            "created_at": now,
            "updated_at": now,
        }
        movie = MovieOut(**data)
        assert movie.movie_id == "tt123"
        assert movie.review_count == 0  # Default value

    def test_missing_required_field(self):
        now = datetime.now(timezone.utc)
        data = {
            "title": "Test Movie",
            "created_at": now,
            "updated_at": now,
        }
        with pytest.raises(ValidationError):
            MovieOut(**data)


class TestMovieSearchFiltersSchema:
    """Tests for MovieSearchFilters schema."""

    def test_partial_filters(self):
        filters = MovieSearchFilters(title="test", min_rating=8.0)
        assert filters.title == "test"
        assert filters.min_rating == 8.0
        assert filters.genre is None

    @pytest.mark.parametrize("invalid_year", [1887, 2101])
    def test_year_validation(self, invalid_year):
        with pytest.raises(ValidationError):
            MovieSearchFilters(min_year=invalid_year)


class TestMovieListResponseSchema:
    """Tests for MovieListResponse schema."""

    def test_pagination_fields(self):
        now = datetime.now(timezone.utc)
        movies = [
            MovieOut(
                movie_id="tt123",
                title="Test Movie",
                created_at=now,
                updated_at=now,
            )
        ]
        response = MovieListResponse(
            items=movies, total=100, page=2, page_size=10, total_pages=10
        )
        assert response.total == 100
        assert response.page == 2
        assert response.total_pages == 10

    def test_empty_response(self):
        response = MovieListResponse(
            items=[], total=0, page=1, page_size=10, total_pages=0
        )
        assert len(response.items) == 0
        assert response.total == 0
