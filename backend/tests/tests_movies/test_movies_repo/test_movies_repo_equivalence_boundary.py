"""
Comprehensive equivalence partitioning and boundary value tests for MovieRepository.
Tests input validation, edge cases, and boundary conditions using multiple testing methodologies.
"""
import tempfile
from unittest.mock import patch

import pytest

from backend.repositories.movies_repo import MovieRepository
from backend.schemas.movies import MovieCreate


class TestMoviesRepoEquivalenceBoundary:
    """Comprehensive equivalence partitioning and boundary value tests for MovieRepository"""

    @pytest.fixture
    def csv_repo(self):
        """Create MovieRepository instance with temporary CSV backend"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            # Create empty CSV with headers
            import csv
            writer = csv.DictWriter(f, fieldnames=[
                'movie_id', 'title', 'genre', 'release_year', 'rating',
                'runtime', 'director', 'cast', 'plot', 'poster_url',
                'created_at', 'updated_at'
            ])
            writer.writeheader()
            temp_path = f.name

        with patch('backend.repositories.movies_repo.MOVIES_CSV_PATH', temp_path):
            repo = MovieRepository(use_json=False)
            yield repo

        # Cleanup
        import os
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    # ========== PAGINATION TESTS ==========

    @pytest.mark.parametrize("skip,limit,expected_count", [
        # Combined equivalence partitions and boundary values
        (0, 0, 0),    # Zero limit boundary
        (0, 1, 1),    # Single item
        (0, 5, 5),    # Exact dataset size
        (0, 6, 5),    # Just beyond dataset size
        (0, 100, 5),  # Large limit
        (4, 10, 1),   # Skip to last item
        (5, 10, 0),   # Just beyond data
        (999, 10, 0), # Far beyond boundary
    ])
    def test_movies_repo_get_all_pagination_combined(self, csv_repo, skip, limit, expected_count):
        """Test get_all with combined pagination scenarios"""
        # Create exactly 5 test movies
        for i in range(5):
            movie_create = MovieCreate(title=f"Movie {i}")
            csv_repo.create(movie_create)

        movies, total = csv_repo.get_all(skip=skip, limit=limit)
        assert len(movies) == expected_count
        assert total == 5

    # ========== RATING FIELD TESTS ==========

    @pytest.mark.parametrize("rating", [
        # Combined valid rating scenarios
        0.0,   # Minimum boundary
        0.1,   # Just above minimum
        5.0,   # Middle value
        7.5,   # Decimal rating
        9.9,   # Just below maximum
        10.0,  # Maximum boundary
        None,  # Optional field
    ])
    def test_movies_repo_rating_field_combined(self, csv_repo, rating):
        """Test rating field with combined valid scenarios"""
        movie_create = MovieCreate(
            title="Rating Test Movie",
            rating=rating
        )

        movie = csv_repo.create(movie_create)
        assert movie.rating == rating

    def test_movies_repo_invalid_rating_schema_rejection(self):
        """Test that invalid ratings are rejected by schema validation"""
        # Test invalid rating boundaries
        with pytest.raises(ValueError, match="greater than or equal to 0"):
            MovieCreate(title="Test Movie", rating=-0.1)  # Below minimum

        with pytest.raises(ValueError, match="less than or equal to 10"):
            MovieCreate(title="Test Movie", rating=10.1)  # Above maximum

    # ========== RELEASE YEAR TESTS ==========

    @pytest.mark.parametrize("release_year", [
        # Combined valid year scenarios
        1895,  # Minimum boundary (cinema invention)
        1896,  # Just above minimum
        1950,  # Mid-20th century
        2000,  # Turn of century
        2025,  # Current year
        None,  # Optional field
    ])
    def test_movies_repo_release_year_combined(self, csv_repo, release_year):
        """Test release_year field with combined valid scenarios"""
        movie_create = MovieCreate(
            title="Year Test Movie",
            release_year=release_year
        )

        movie = csv_repo.create(movie_create)
        assert movie.release_year == release_year

    def test_movies_repo_invalid_year_schema_rejection(self):
        """Test that invalid years are rejected by schema validation"""
        with pytest.raises(ValueError):
            MovieCreate(title="Test Movie", release_year=1894)  # Before cinema

    # ========== STRING FIELD TESTS ==========

    @pytest.mark.parametrize("title_input", [
        "A",                                  # Single character (minimum)
        "Normal Movie Title",                 # Typical title
        "A" * 100,                           # Long title
        "Movie with 123",                     # Title with numbers
        "Movie with spéciål chàrs",           # Title with special chars
        "🎬 Movie with emoji",                # Title with emoji
    ])
    def test_movies_repo_title_field_combined(self, csv_repo, title_input):
        """Test title field with various input scenarios"""
        movie_create = MovieCreate(title=title_input)
        movie = csv_repo.create(movie_create)
        assert movie.title == title_input

    def test_movies_repo_invalid_title_schema_rejection(self):
        """Test that invalid titles are rejected by schema validation"""
        with pytest.raises(ValueError):
            MovieCreate(title="")  # Empty title

        with pytest.raises(ValueError):
            MovieCreate(title="   ")  # Whitespace-only title

    @pytest.mark.parametrize("genre_input,expected_result", [
        ("Action", "Action"),                    # Single genre
        ("Drama, Romance", "Drama, Romance"),    # Multiple genres
        ("Sci-Fi/Fantasy", "Sci-Fi/Fantasy"),    # Genre with special chars
        ("", None),                              # Empty string becomes None
        (None, None),                            # None remains None
    ])
    def test_movies_repo_genre_field_combined(self, csv_repo, genre_input, expected_result):
        """Test genre field with various input scenarios"""
        movie_create = MovieCreate(
            title="Genre Test Movie",
            genre=genre_input
        )

        movie = csv_repo.create(movie_create)
        assert movie.genre == expected_result

    # ========== SEARCH FILTER TESTS ==========

    @pytest.mark.parametrize("min_rating,expected_count", [
        (0.0, 3),   # Include all movies
        (5.0, 3),   # Include medium and high rated
        (7.5, 2),   # Include only high rated
        (10.0, 1),  # No movies meet criteria
        (None, 3),  # No rating filter
    ])
    def test_movies_repo_search_min_rating_combined(self, csv_repo, min_rating, expected_count):
        """Test min_rating search filter with combined scenarios"""
        # Create test movies with specific ratings
        test_movies = [
            MovieCreate(title="Low Rated", rating=5.0),
            MovieCreate(title="Medium Rated", rating=7.5),
            MovieCreate(title="High Rated", rating=10.0),
        ]

        for movie in test_movies:
            csv_repo.create(movie)

        movies, total = csv_repo.search(min_rating=min_rating)
        assert total == expected_count

    @pytest.mark.parametrize("min_year,max_year,expected_count", [
        (1999, 2001, 3),   # Range covering all
        (2000, 2000, 1),   # Single year
        (1990, 1995, 0),   # No movies in range
        (None, 2000, 2),   # Only max year specified
        (2000, None, 2),   # Only min year specified
        (None, None, 3),   # No year filter
    ])
    def test_movies_repo_search_year_range_combined(self, csv_repo, min_year, max_year, expected_count):
        """Test year range search filters with combined scenarios"""
        # Create test movies with specific release years
        test_movies = [
            MovieCreate(title="Movie 1999", release_year=1999),
            MovieCreate(title="Movie 2000", release_year=2000),
            MovieCreate(title="Movie 2001", release_year=2001),
        ]

        for movie in test_movies:
            csv_repo.create(movie)

        movies, total = csv_repo.search(min_year=min_year, max_year=max_year)
        assert total == expected_count

    # ========== SORTING TESTS ==========

    @pytest.mark.parametrize("sort_by,sort_desc,expected_first_title", [
        ("title", False, "A Movie"),        # Ascending by title
        ("title", True, "C Movie"),         # Descending by title
        ("rating", False, "B Movie"),       # Ascending by rating
        ("rating", True, "C Movie"),        # Descending by rating
        ("release_year", False, "A Movie"), # Ascending by year
        ("release_year", True, "C Movie"),  # Descending by year
    ])
    def test_movies_repo_sorting_combined(self, csv_repo, sort_by, sort_desc, expected_first_title):
        """Test sorting with various scenarios"""
        # Create test movies with different attributes
        test_movies = [
            MovieCreate(title="B Movie", rating=7.0, release_year=2005),
            MovieCreate(title="A Movie", rating=8.0, release_year=2000),
            MovieCreate(title="C Movie", rating=9.0, release_year=2010),
        ]

        for movie in test_movies:
            csv_repo.create(movie)

        movies, total = csv_repo.get_all(sort_by=sort_by, sort_desc=sort_desc)
        assert movies[0].title == expected_first_title

    # ========== FIELD COMBINATION TESTS ==========

    def test_movies_repo_minimal_fields_creation(self, csv_repo):
        """Test movie creation with only required fields"""
        movie_create = MovieCreate(title="Minimal Movie")
        movie = csv_repo.create(movie_create)

        assert movie.title == "Minimal Movie"
        assert movie.genre is None
        assert movie.release_year is None
        assert movie.rating is None
        assert movie.runtime is None

    def test_movies_repo_complete_fields_creation(self, csv_repo):
        """Test movie creation with all optional fields populated"""
        movie_create = MovieCreate(
            title="Complete Movie",
            genre="Action, Adventure",
            release_year=2024,
            rating=8.5,
            runtime=120,
            director="Test Director",
            cast="Actor One, Actor Two",
            plot="Test plot summary",
            poster_url="https://example.com/poster.jpg"
        )

        movie = csv_repo.create(movie_create)
        assert movie.title == "Complete Movie"
        assert movie.genre == "Action, Adventure"
        assert movie.release_year == 2024
        assert movie.rating == 8.5
        assert movie.runtime == 120
        assert movie.director == "Test Director"
        assert movie.cast == "Actor One, Actor Two"
        assert movie.plot == "Test plot summary"
        assert movie.poster_url == "https://example.com/poster.jpg"

    # ========== EDGE CASE TESTS ==========

    def test_movies_repo_empty_database_operations(self, csv_repo):
        """Test operations on empty database"""
        movies, total = csv_repo.get_all()
        assert total == 0
        assert len(movies) == 0

        movies, total = csv_repo.search(title="anything")
        assert total == 0

        movie = csv_repo.get_by_id("any_id")
        assert movie is None

    def test_movies_repo_single_item_database(self, csv_repo):
        """Test operations on database with exactly one item"""
        movie_create = MovieCreate(title="Single Movie")
        created = csv_repo.create(movie_create)

        movies, total = csv_repo.get_all()
        assert total == 1
        assert len(movies) == 1

        # Test pagination with single item
        movies, total = csv_repo.get_all(skip=0, limit=1)
        assert len(movies) == 1

        movies, total = csv_repo.get_all(skip=1, limit=1)
        assert len(movies) == 0

    def test_movies_repo_empty_string_handling(self, csv_repo):
        """Test handling of empty string values"""
        movie_create = MovieCreate(
            title="Empty Strings Test",
            genre="",
            director="",
            cast="",
            plot="",
            poster_url=""
        )

        movie = csv_repo.create(movie_create)
        # Empty strings should be converted to None
        assert movie.genre is None
        assert movie.director is None
        assert movie.cast is None
        assert movie.plot is None
        assert movie.poster_url is None

    def test_movies_repo_special_characters_handling(self, csv_repo):
        """Test handling of special and Unicode characters"""
        special_title = "Movie with <html> & \"quotes\" 'apostrophes' /slashes\\ and 🎬 emoji"
        movie_create = MovieCreate(title=special_title)

        movie = csv_repo.create(movie_create)
        assert movie.title == special_title

    # ========== PERFORMANCE TESTS ==========

    def test_movies_repo_large_dataset_pagination(self, csv_repo):
        """Test pagination with larger dataset"""
        # Create moderate dataset
        for i in range(100):
            movie_create = MovieCreate(title=f"Movie {i:03d}")
            csv_repo.create(movie_create)

        # Test various pagination scenarios
        test_cases = [
            (0, 10, 10),    # First page
            (90, 10, 10),   # Last full page
            (95, 10, 5),    # Partial last page
            (99, 10, 1),    # Single item page
            (100, 10, 0),   # Beyond data
            (0, 1000, 100), # Large limit
        ]

        for skip, limit, expected in test_cases:
            movies, total = csv_repo.get_all(skip=skip, limit=limit)
            assert len(movies) == expected
            assert total == 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])