"""
Tests for Movies Repository helper functions.
Tests data transformation, validation, and utility functions with comprehensive coverage.
"""
import uuid
from datetime import datetime, timezone

import pytest

from backend.repositories.movies_repo import _movie_to_dict, _dict_to_movie_dict


class TestMoviesRepoHelpers:
    """Test cases for Movies Repository helper functions"""

    # ========== _movie_to_dict TESTS ==========

    def test_movies_repo_movie_to_dict_complete_data(self):
        """Test _movie_to_dict with complete movie data"""
        movie_data = {
            "movie_id": "tt0111161",
            "title": "Test Movie",
            "genre": "Drama",
            "release_year": 1994,
            "rating": 9.3,
            "runtime": 142,
            "director": "Test Director",
            "cast": "Test Cast",
            "plot": "Test Plot",
            "poster_url": "https://test.com/poster.jpg",
            "created_at": datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            "updated_at": datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            "review_count": 5  # Extra field should be handled
        }

        result = _movie_to_dict(movie_data)

        assert result["movie_id"] == "tt0111161"
        assert result["title"] == "Test Movie"
        assert result["genre"] == "Drama"
        assert result["release_year"] == 1994
        assert result["rating"] == 9.3
        assert result["runtime"] == 142
        assert result["director"] == "Test Director"
        assert result["cast"] == "Test Cast"
        assert result["plot"] == "Test Plot"
        assert result["poster_url"] == "https://test.com/poster.jpg"
        assert result["review_count"] == 5

    def test_movies_repo_movie_to_dict_partial_data(self):
        """Test _movie_to_dict with partial movie data"""
        movie_data = {
            "movie_id": "partial123",
            "title": "Partial Movie"
            # Missing most optional fields
        }

        result = _movie_to_dict(movie_data)

        assert result["movie_id"] == "partial123"
        assert result["title"] == "Partial Movie"
        assert result["genre"] is None
        assert result["release_year"] is None
        assert result["rating"] is None
        assert result["runtime"] is None
        assert result["director"] is None
        assert result["cast"] is None
        assert result["plot"] is None
        assert result["poster_url"] is None
        assert result["review_count"] == 0
        assert isinstance(result["created_at"], datetime)
        assert isinstance(result["updated_at"], datetime)

    def test_movies_repo_movie_to_dict_timezone_handling(self):
        """Test _movie_to_dict timezone handling"""
        # Test with naive datetime (should be made timezone-aware)
        naive_dt = datetime(2024, 1, 1, 12, 0, 0)
        movie_data = {
            "movie_id": "timezone_test",
            "title": "Timezone Test",
            "created_at": naive_dt,
            "updated_at": naive_dt
        }

        result = _movie_to_dict(movie_data)

        assert result["created_at"].tzinfo is not None
        assert result["updated_at"].tzinfo is not None
        assert result["created_at"].tzinfo == timezone.utc
        assert result["updated_at"].tzinfo == timezone.utc

    def test_movies_repo_movie_to_dict_none_values(self):
        """Test _movie_to_dict with explicit None values"""
        movie_data = {
            "movie_id": "none_test",
            "title": "None Values Test",
            "genre": None,
            "release_year": None,
            "rating": None,
            "runtime": None,
            "director": None,
            "cast": None,
            "plot": None,
            "poster_url": None
        }

        result = _movie_to_dict(movie_data)

        assert result["movie_id"] == "none_test"
        assert result["title"] == "None Values Test"
        assert result["genre"] is None
        assert result["release_year"] is None
        assert result["rating"] is None
        assert result["runtime"] is None
        assert result["director"] is None
        assert result["cast"] is None
        assert result["plot"] is None
        assert result["poster_url"] is None

    def test_movies_repo_movie_to_dict_extra_fields(self):
        """Test _movie_to_dict with extra fields not in schema"""
        movie_data = {
            "movie_id": "extra_fields",
            "title": "Extra Fields Movie",
            "genre": "Drama",
            "unknown_field": "This should be ignored",
            "another_unknown": 12345
        }

        result = _movie_to_dict(movie_data)

        # Known fields should be present
        assert result["movie_id"] == "extra_fields"
        assert result["title"] == "Extra Fields Movie"
        assert result["genre"] == "Drama"
        # Unknown fields should not be in result
        assert "unknown_field" not in result
        assert "another_unknown" not in result

    # ========== _dict_to_movie_dict TESTS ==========

    def test_movies_repo_dict_to_movie_dict_complete_data(self):
        """Test _dict_to_movie_dict with complete data"""
        data = {
            "movie_id": "custom123",
            "title": "Complete Movie",
            "genre": "Action",
            "release_year": 2024,
            "rating": 8.5,
            "runtime": 120,
            "director": "Test Director",
            "cast": "Test Cast",
            "plot": "Test Plot",
            "poster_url": "https://test.com/poster.jpg",
            "created_at": datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            "updated_at": datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        }

        result = _dict_to_movie_dict(data)

        assert result["movie_id"] == "custom123"
        assert result["title"] == "Complete Movie"
        assert result["genre"] == "Action"
        assert result["release_year"] == 2024
        assert result["rating"] == 8.5
        assert result["runtime"] == 120
        assert result["director"] == "Test Director"
        assert result["cast"] == "Test Cast"
        assert result["plot"] == "Test Plot"
        assert result["poster_url"] == "https://test.com/poster.jpg"

    def test_movies_repo_dict_to_movie_dict_empty_strings(self):
        """Test _dict_to_movie_dict converts empty strings to None"""
        data = {
            "title": "Empty Fields Movie",
            "genre": "",  # Should become None
            "director": "",  # Should become None
            "cast": "",  # Should become None
            "plot": "",  # Should become None
            "poster_url": ""  # Should become None
        }

        result = _dict_to_movie_dict(data)

        assert result["title"] == "Empty Fields Movie"
        assert result["genre"] is None
        assert result["director"] is None
        assert result["cast"] is None
        assert result["plot"] is None
        assert result["poster_url"] is None

    def test_movies_repo_dict_to_movie_dict_auto_generate_id(self):
        """Test _dict_to_movie_dict auto-generates ID when not provided"""
        data = {
            "title": "Auto ID Movie"
        }

        result = _dict_to_movie_dict(data)

        assert "movie_id" in result
        assert result["movie_id"] is not None
        assert result["movie_id"] != ""
        # Should be a valid UUID
        try:
            uuid.UUID(result["movie_id"])
        except ValueError:
            pytest.fail("Generated movie_id is not a valid UUID")

    def test_movies_repo_dict_to_movie_dict_preserves_custom_id(self):
        """Test _dict_to_movie_dict preserves custom movie_id"""
        custom_id = "custom_movie_123"
        data = {
            "movie_id": custom_id,
            "title": "Custom ID Movie"
        }

        result = _dict_to_movie_dict(data)
        assert result["movie_id"] == custom_id

    def test_movies_repo_dict_to_movie_dict_none_values(self):
        """Test _dict_to_movie_dict handles None values correctly"""
        data = {
            "title": "None Values Movie",
            "genre": None,
            "release_year": None,
            "rating": None,
            "runtime": None,
            "director": None,
            "cast": None,
            "plot": None,
            "poster_url": None
        }

        result = _dict_to_movie_dict(data)

        assert result["title"] == "None Values Movie"
        assert result["genre"] is None
        assert result["release_year"] is None
        assert result["rating"] is None
        assert result["runtime"] is None
        assert result["director"] is None
        assert result["cast"] is None
        assert result["plot"] is None
        assert result["poster_url"] is None

    def test_movies_repo_dict_to_movie_dict_timestamps(self):
        """Test _dict_to_movie_dict timestamp generation"""
        data = {
            "title": "Timestamp Test Movie"
        }

        result = _dict_to_movie_dict(data)

        # Should have created_at and updated_at
        assert "created_at" in result
        assert "updated_at" in result

        # Should be datetime objects
        assert isinstance(result["created_at"], datetime)
        assert isinstance(result["updated_at"], datetime)

        # Should be timezone-aware
        assert result["created_at"].tzinfo is not None
        assert result["updated_at"].tzinfo is not None

        # Should be approximately the same time
        time_diff = abs(result["created_at"] - result["updated_at"])
        assert time_diff.total_seconds() < 1  # Within 1 second

    def test_movies_repo_dict_to_movie_dict_custom_timestamps(self):
        """Test _dict_to_movie_dict with custom timestamps"""
        custom_time = datetime(2023, 12, 1, 10, 30, 0, tzinfo=timezone.utc)
        data = {
            "title": "Custom Timestamps",
            "created_at": custom_time,
            "updated_at": custom_time
        }

        result = _dict_to_movie_dict(data)

        assert result["created_at"] == custom_time
        assert result["updated_at"] == custom_time

    def test_movies_repo_dict_to_movie_dict_partial_update(self):
        """Test _dict_to_movie_dict with partial update data"""
        data = {
            "title": "Partial Update Movie",
            "rating": 7.5
            # Missing other fields
        }

        result = _dict_to_movie_dict(data)

        assert result["title"] == "Partial Update Movie"
        assert result["rating"] == 7.5
        assert result["genre"] is None
        assert result["release_year"] is None
        assert result["runtime"] is None
        assert result["director"] is None
        assert result["cast"] is None
        assert result["plot"] is None
        assert result["poster_url"] is None

    def test_movies_repo_dict_to_movie_dict_whitespace_handling(self):
        """Test _dict_to_movie_dict whitespace handling"""
        data = {
            "title": "  Whitespace Movie  ",
            "genre": "  Drama  ",
            "director": "  Director Name  ",
            "cast": "  Actor One, Actor Two  ",
            "plot": "  Plot with spaces  "
        }

        result = _dict_to_movie_dict(data)

        # Titles and text fields should preserve whitespace
        assert result["title"] == "  Whitespace Movie  "
        assert result["genre"] == "  Drama  "  # Will be kept, not converted to None
        assert result["director"] == "  Director Name  "
        assert result["cast"] == "  Actor One, Actor Two  "
        assert result["plot"] == "  Plot with spaces  "


if __name__ == "__main__":
    pytest.main([__file__, "-v"])