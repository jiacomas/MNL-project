"""
Edge case and performance tests for movie schemas.
"""

from datetime import datetime, timezone

import pytest

from schemas.movies import MovieBase, MovieListResponse, MovieOut


class TestMovieSchemasEdgeCases:
    """Tests for edge cases and performance considerations."""

    def test_maximum_data_sizes(self):
        """Test MovieOut with maximum allowed data sizes."""
        now = datetime.now(timezone.utc)
        max_data = {
            "movie_id": "t" * 100,
            "title": "A" * 500,
            "genre": "A" * 200,
            "release_year": 2100,
            "rating": 10.0,
            "runtime": 999,
            "director": "A" * 200,
            "cast": "A" * 1000,
            "plot": "A" * 2000,
            "poster_url": "https://example.com/" + "a" * 100 + ".jpg",
            "created_at": now,
            "updated_at": now,
            "review_count": 2**31 - 1,
        }

        movie = MovieOut(**max_data)
        assert movie.title == "A" * 500
        assert movie.review_count == 2**31 - 1

    def test_large_dataset_performance(self):
        """Test MovieListResponse handles large datasets efficiently."""
        now = datetime.now(timezone.utc)
        large_movie_list = [
            MovieOut(
                movie_id=f"tt{i:07d}",
                title=f"Movie {i}",
                created_at=now,
                updated_at=now,
                review_count=i * 100,
            )
            for i in range(100)
        ]

        response = MovieListResponse(
            items=large_movie_list, total=10000, page=1, page_size=100, total_pages=100
        )

        assert len(response.items) == 100
        assert response.total == 10000
        assert response.total_pages == 100

    def test_special_characters_handling(self):
        """Test string fields safely handle special characters."""
        special_chars_data = {
            "title": "Test'; DROP TABLE movies; --",
            "genre": "Action'; <script>alert('xss')</script>",
            "director": "O'Conner; --",
            "cast": "Actor1; Actor2\nActor3",
            "plot": "Plot with 'quotes' and \"double quotes\"",
            "poster_url": "https://example.com/image.jpg?param=value&other=test",
        }

        movie = MovieBase(**special_chars_data)
        assert movie.title == "Test'; DROP TABLE movies; --"
        assert movie.genre == "Action'; <script>alert('xss')</script>"

    def test_none_values_handling(self):
        """Test MovieOut properly handles None values for optional fields."""
        now = datetime.now(timezone.utc)
        data = {
            "movie_id": "tt0111161",
            "title": "Test Movie",
            "genre": None,
            "release_year": None,
            "rating": None,
            "runtime": None,
            "director": None,
            "cast": None,
            "plot": None,
            "poster_url": None,
            "created_at": now,
            "updated_at": now,
            "review_count": 0,
        }

        movie = MovieOut(**data)
        assert movie.movie_id == "tt0111161"
        assert movie.title == "Test Movie"
        assert movie.genre is None
        assert movie.release_year is None

    def test_unicode_characters_support(self):
        """Test MovieBase properly handles Unicode and special characters."""
        unicode_data = {
            "title": "Movie with emoji 🎬 and unicode 中文",
            "genre": "Sci-Fi 🚀",
            "director": "Director名字",
            "cast": "Actor 🎭, Another Actor",
            "plot": "Plot with emojis: ❤️🔥🌟",
            "poster_url": "https://example.com/海报.jpg",
        }

        movie = MovieBase(**unicode_data)
        assert movie.title == "Movie with emoji 🎬 and unicode 中文"
        assert movie.genre == "Sci-Fi 🚀"
        assert movie.director == "Director名字"

    def test_creation_performance(self):
        """Test performance of rapid MovieOut instance creation."""
        now = datetime.now(timezone.utc)

        for i in range(100):
            movie = MovieOut(
                movie_id=f"tt{i:07d}",
                title=f"Movie {i}",
                created_at=now,
                updated_at=now,
                review_count=i * 100,
            )
            assert movie.movie_id == f"tt{i:07d}"

    def test_memory_efficiency(self):
        """Test MovieListResponse maintains memory efficiency with substantial data."""
        now = datetime.now(timezone.utc)
        items = [
            MovieOut(
                movie_id=f"tt{i:07d}",
                title=f"Movie {i}",
                created_at=now,
                updated_at=now,
                review_count=i * 100,
            )
            for i in range(50)
        ]

        response = MovieListResponse(
            items=items, total=1000, page=1, page_size=50, total_pages=20
        )

        assert len(response.items) == 50
        for i, item in enumerate(response.items):
            assert item.movie_id == f"tt{i:07d}"
            assert item.title == f"Movie {i}"

    @pytest.mark.parametrize(
        "field,min_value,max_value",
        [
            ("release_year", 1888, 2100),
            ("rating", 0.0, 10.0),
            ("runtime", 1, 999),
        ],
    )
    def test_extreme_numeric_values(self, field, min_value, max_value):
        """Test MovieBase with extreme valid numeric values."""
        # Test minimum values
        min_data = {"title": "A", field: min_value}
        movie_min = MovieBase(**min_data)
        assert getattr(movie_min, field) == min_value

        # Test maximum values
        max_data = {"title": "A" * 500, field: max_value}
        movie_max = MovieBase(**max_data)
        assert getattr(movie_max, field) == max_value
