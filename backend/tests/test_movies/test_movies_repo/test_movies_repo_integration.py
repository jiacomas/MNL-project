"""
Consolidated unit tests for MovieRepository.

Covers:
- Core CRUD operations
- Equivalence partitioning and boundary values
- Error handling and fault injection
- UUID helper test
- Mocking and search/filter behavior
"""

import csv
import os
import tempfile
from unittest.mock import patch

import pytest

from backend.repositories.movies_repo import MovieRepository, _dict_to_movie_dict
from backend.schemas.movies import MovieCreate, MovieUpdate


class TestMovieRepositoryUnit:
    """Consolidated unit tests for MovieRepository"""

    # Fixtures

    @pytest.fixture
    def temp_csv_file(self):
        """Create a temporary CSV file for testing"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "movie_id",
                    "title",
                    "genre",
                    "release_year",
                    "rating",
                    "runtime",
                    "director",
                    "cast",
                    "plot",
                    "poster_url",
                    "created_at",
                    "updated_at",
                ],
            )
            writer.writeheader()
            writer.writerows(
                [
                    {
                        "movie_id": "tt0111161",
                        "title": "The Shawshank Redemption",
                        "genre": "Drama",
                        "release_year": "1994",
                        "rating": "9.3",
                        "runtime": "142",
                        "director": "Frank Darabont",
                        "cast": "Tim Robbins, Morgan Freeman",
                        "plot": "Two imprisoned men bond...",
                        "poster_url": "https://example.com/poster1.jpg",
                        "created_at": "2024-01-01T12:00:00Z",
                        "updated_at": "2024-01-01T12:00:00Z",
                    },
                    {
                        "movie_id": "tt0068646",
                        "title": "The Godfather",
                        "genre": "Crime, Drama",
                        "release_year": "1972",
                        "rating": "9.2",
                        "runtime": "175",
                        "director": "Francis Ford Coppola",
                        "cast": "Marlon Brando, Al Pacino",
                        "plot": "The aging patriarch...",
                        "poster_url": "https://example.com/poster2.jpg",
                        "created_at": "2024-01-01T12:00:00Z",
                        "updated_at": "2024-01-01T12:00:00Z",
                    },
                ]
            )
            temp_path = f.name

        yield temp_path
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    @pytest.fixture
    def csv_repo(self, temp_csv_file):
        """Create MovieRepository instance with CSV backend"""
        with patch("backend.repositories.movies_repo.MOVIES_CSV_PATH", temp_csv_file):
            repo = MovieRepository(use_json=False)
            yield repo

    @pytest.fixture
    def empty_csv_repo(self):
        """Create MovieRepository instance with empty CSV backend"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "movie_id",
                    "title",
                    "genre",
                    "release_year",
                    "rating",
                    "runtime",
                    "director",
                    "cast",
                    "plot",
                    "poster_url",
                    "created_at",
                    "updated_at",
                ],
            )
            writer.writeheader()
            temp_path = f.name

        with patch("backend.repositories.movies_repo.MOVIES_CSV_PATH", temp_path):
            repo = MovieRepository(use_json=False)
            yield repo

        if os.path.exists(temp_path):
            os.unlink(temp_path)

    # CRUD

    def test_get_all_csv(self, csv_repo):
        """Test getting all movies from CSV repository"""
        movies, total = csv_repo.get_all()
        assert total == 2
        assert len(movies) == 2
        assert movies[0].movie_id == "tt0111161"
        assert movies[1].movie_id == "tt0068646"

    def test_get_by_id_existing(self, csv_repo):
        """Test getting existing movie by ID"""
        movie = csv_repo.get_by_id("tt0111161")
        assert movie is not None
        assert movie.movie_id == "tt0111161"
        assert movie.title == "The Shawshank Redemption"

    def test_get_by_id_nonexistent(self, csv_repo):
        """Test getting non-existent movie by ID"""
        movie = csv_repo.get_by_id("nonexistent_id")
        assert movie is None

    def test_create_movie_basic(self, csv_repo):
        """Test creating a new movie with basic data"""
        movie_create = MovieCreate(
            title="New Test Movie", genre="Comedy", release_year=2024, rating=8.5
        )
        created_movie = csv_repo.create(movie_create)
        assert created_movie is not None
        assert created_movie.title == "New Test Movie"

    def test_update_movie_existing(self, csv_repo):
        """Test updating an existing movie"""
        movie_update = MovieUpdate(title="Updated Title", rating=9.5)
        updated_movie = csv_repo.update("tt0111161", movie_update)
        assert updated_movie is not None
        assert updated_movie.title == "Updated Title"
        assert updated_movie.rating == 9.5

    def test_update_movie_nonexistent(self, csv_repo):
        """Test updating a non-existent movie"""
        movie_update = MovieUpdate(title="Updated Title")
        result = csv_repo.update("nonexistent_id", movie_update)
        assert result is None

    def test_delete_movie_existing(self, csv_repo):
        """Test deleting an existing movie"""
        result = csv_repo.delete("tt0111161")
        assert result is True
        deleted_movie = csv_repo.get_by_id("tt0111161")
        assert deleted_movie is None

    def test_delete_movie_nonexistent(self, csv_repo):
        """Test deleting a non-existent movie"""
        result = csv_repo.delete("nonexistent_id")
        assert result is False

    # Pagination + Boundary

    @pytest.mark.parametrize(
        "skip,limit,expected_count",
        [
            (0, 0, 0),
            (0, 1, 1),
            (0, 5, 5),
            (0, 6, 5),
            (0, 100, 5),
            (4, 10, 1),
            (5, 10, 0),
            (999, 10, 0),
        ],
    )
    def test_pagination_combined(self, empty_csv_repo, skip, limit, expected_count):
        """Test pagination with various scenarios"""
        for i in range(5):
            empty_csv_repo.create(MovieCreate(title=f"Movie {i}"))

        movies, total = empty_csv_repo.get_all(skip=skip, limit=limit)
        assert len(movies) == expected_count
        assert total == 5

    @pytest.mark.parametrize("rating", [0.0, 0.1, 5.0, 7.5, 9.9, 10.0, None])
    def test_rating_field_combined(self, empty_csv_repo, rating):
        """Test rating field with various valid scenarios"""
        movie = empty_csv_repo.create(MovieCreate(title="Rating", rating=rating))
        assert movie.rating == rating

    def test_invalid_rating_schema_rejection(self):
        """Test that invalid ratings are rejected by schema validation"""
        with pytest.raises(ValueError):
            MovieCreate(title="Test Movie", rating=-0.1)
        with pytest.raises(ValueError):
            MovieCreate(title="Test Movie", rating=10.1)

    @pytest.mark.parametrize("release_year", [1895, 1896, 1950, 2000, 2024, None])
    def test_release_year_combined(self, empty_csv_repo, release_year):
        """Test release_year field with various valid scenarios"""
        movie = empty_csv_repo.create(
            MovieCreate(title="Year", release_year=release_year)
        )
        assert movie.release_year == release_year

    # Error handling & Fault Injection

    def test_duplicate_movie_creation(self, empty_csv_repo):
        """Test exception handling for duplicate movie creation"""
        movie_create = MovieCreate(movie_id="dup123", title="Dup")
        empty_csv_repo.create(movie_create)

        with pytest.raises(ValueError):
            empty_csv_repo.create(movie_create)

    def test_corrupted_csv_file_handling(self):
        """Test handling of corrupted CSV file"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "movie_id",
                    "title",
                    "genre",
                    "release_year",
                    "rating",
                    "runtime",
                    "director",
                    "cast",
                    "plot",
                    "poster_url",
                    "created_at",
                    "updated_at",
                ],
            )
            writer.writeheader()
            writer.writerow(
                {
                    "movie_id": "corrupted",
                    "title": "Corrupted",
                    "genre": "Drama",
                    "release_year": "xxx",
                    "rating": "zzz",
                    "runtime": "abc",
                    "director": "D",
                    "cast": "C",
                    "plot": "P",
                    "poster_url": "U",
                    "created_at": "invalid",
                    "updated_at": "invalid",
                }
            )
            temp_path = f.name

        try:
            with patch("backend.repositories.movies_repo.MOVIES_CSV_PATH", temp_path):
                repo = MovieRepository(use_json=False)
                movies, total = repo.get_all()
                assert total == 1
                assert movies[0].title == "Corrupted"
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    # Mocking

    def test_mock_uuid_generation(self):
        """Test UUID generation using mocking"""
        fixed_uuid = "12345678-1234-5678-1234-567812345678"
        with patch("backend.repositories.movies_repo.uuid.uuid4") as mock_uuid:
            mock_uuid.return_value = fixed_uuid
            movie_dict = _dict_to_movie_dict({"title": "Mocked"})
            assert movie_dict["movie_id"] == fixed_uuid

    # Search and filter

    def test_search_by_title(self, csv_repo):
        """Test searching movies by title"""
        movies, total = csv_repo.search(title="shawshank")
        assert total == 1

    def test_search_by_rating(self, csv_repo):
        """Test searching movies by minimum rating"""
        movies, total = csv_repo.search(min_rating=9.0)
        assert total == 2

    def test_get_popular_movies(self, csv_repo):
        """Test getting popular movies sorted by rating"""
        popular_movies = csv_repo.get_popular(limit=2)
        assert len(popular_movies) == 2

    def test_get_recent_movies(self, csv_repo):
        """Test getting recently added movies"""
        csv_repo.create(MovieCreate(title="Recent"))
        recent_movies = csv_repo.get_recent(limit=3)
        assert recent_movies[0].title == "Recent"
