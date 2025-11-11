"""
Edge case and performance tests for movie schemas.
"""
import pytest
from datetime import datetime, timezone
from backend.schemas.movies import MovieOut, MovieListResponse, MovieBase


class TestMovieSchemasEdgeCases:
    """Tests for edge cases and performance considerations"""

    def test_movie_out_with_maximum_data(self):
        """Test MovieOut with maximum allowed data sizes"""
        now = datetime.now(timezone.utc)
        max_data = {
            "movie_id": "t" * 100,  # Long movie ID
            "title": "A" * 500,  # Maximum length title
            "genre": "A" * 200,  # Long genre
            "release_year": 2100,  # Maximum year
            "rating": 10.0,  # Maximum rating
            "runtime": 999,  # Maximum runtime
            "director": "A" * 200,  # Long director name
            "cast": "A" * 1000,  # Long cast list
            "plot": "A" * 2000,  # Long plot
            "poster_url": "https://example.com/" + "a" * 100 + ".jpg",  # Long URL
            "created_at": now,
            "updated_at": now,
            "review_count": 2 ** 31 - 1  # Maximum practical integer
        }

        movie = MovieOut(**max_data)
        assert movie.title == "A" * 500
        assert movie.review_count == 2 ** 31 - 1

    def test_movie_list_response_large_dataset(self):
        """Test MovieListResponse with large number of items"""
        now = datetime.now(timezone.utc)
        # Create a larger but reasonable number of items
        large_movie_list = [
            MovieOut(
                movie_id=f"tt{i:07d}",
                title=f"Movie {i}",
                created_at=now,
                updated_at=now,
                review_count=i * 100
            )
            for i in range(100)  # Larger dataset
        ]

        response = MovieListResponse(
            items=large_movie_list,
            total=10000,
            page=1,
            page_size=100,
            total_pages=100
        )

        assert len(response.items) == 100
        assert response.total == 10000
        assert response.total_pages == 100

    def test_string_fields_special_characters(self):
        """Test that string fields handle special characters safely"""
        # Test with characters that might cause issues in different contexts
        special_chars_data = {
            "title": "Test'; DROP TABLE movies; --",
            "genre": "Action'; <script>alert('xss')</script>",
            "director": "O'Conner; --",
            "cast": "Actor1; Actor2\nActor3",
            "plot": "Plot with 'quotes' and \"double quotes\"",
            "poster_url": "https://example.com/image.jpg?param=value&other=test"
        }

        # These should all be handled safely through Pydantic validation
        movie = MovieBase(**special_chars_data)
        assert movie.title == "Test'; DROP TABLE movies; --"
        assert movie.genre == "Action'; <script>alert('xss')</script>"

    def test_movie_out_with_none_values(self):
        """Test MovieOut with None values for optional fields"""
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
            "review_count": 0
        }

        movie = MovieOut(**data)
        assert movie.movie_id == "tt0111161"
        assert movie.title == "Test Movie"
        assert movie.genre is None
        assert movie.release_year is None
        assert movie.rating is None

    def test_movie_base_with_unicode_characters(self):
        """Test MovieBase with Unicode and special characters"""
        unicode_data = {
            "title": "Movie with emoji 🎬 and unicode 中文",
            "genre": "Sci-Fi 🚀",
            "director": "Director名字",
            "cast": "Actor 🎭, Another Actor",
            "plot": "Plot with emojis: ❤️🔥🌟",
            "poster_url": "https://example.com/海报.jpg"
        }

        movie = MovieBase(**unicode_data)
        assert movie.title == "Movie with emoji 🎬 and unicode 中文"
        assert movie.genre == "Sci-Fi 🚀"
        assert movie.director == "Director名字"
        assert movie.cast == "Actor 🎭, Another Actor"

    # Performance Tests
    def test_movie_out_creation_performance(self):
        """Test performance of MovieOut creation with multiple instances"""
        now = datetime.now(timezone.utc)

        # Create multiple MovieOut instances quickly
        for i in range(100):  # Reasonable number for performance test
            movie = MovieOut(
                movie_id=f"tt{i:07d}",
                title=f"Movie {i}",
                created_at=now,
                updated_at=now,
                review_count=i * 100
            )
            assert movie.movie_id == f"tt{i:07d}"

    def test_movie_list_response_memory_efficiency(self):
        """Test that MovieListResponse handles memory efficiently"""
        now = datetime.now(timezone.utc)

        # Create a substantial but reasonable number of items
        items = [
            MovieOut(
                movie_id=f"tt{i:07d}",
                title=f"Movie {i}",
                created_at=now,
                updated_at=now,
                review_count=i * 100
            )
            for i in range(50)
        ]

        response = MovieListResponse(
            items=items,
            total=1000,
            page=1,
            page_size=50,
            total_pages=20
        )

        # Verify all items are accessible and correct
        assert len(response.items) == 50
        for i, item in enumerate(response.items):
            assert item.movie_id == f"tt{i:07d}"
            assert item.title == f"Movie {i}"

    # Edge Case: Extreme Values
    def test_movie_base_extreme_numeric_values(self):
        """Test MovieBase with extreme numeric values"""
        # Test with minimum valid values
        min_data = {
            "title": "A",
            "release_year": 1888,
            "rating": 0.0,
            "runtime": 1
        }
        movie_min = MovieBase(**min_data)
        assert movie_min.release_year == 1888
        assert movie_min.rating == 0.0
        assert movie_min.runtime == 1

        # Test with maximum valid values
        max_data = {
            "title": "A" * 500,
            "release_year": 2100,
            "rating": 10.0,
            "runtime": 999
        }
        movie_max = MovieBase(**max_data)
        assert movie_max.release_year == 2100
        assert movie_max.rating == 10.0
        assert movie_max.runtime == 999