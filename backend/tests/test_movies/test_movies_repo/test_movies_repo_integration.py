"""
Consolidated unit tests for MovieRepository.
Tests core CRUD operations, equivalence partitioning, boundary values, error handling, helpers, and mocking.
"""

import csv
import json
import os
import tempfile
import uuid
from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from backend.repositories.movies_repo import (
    MovieRepository,
    _dict_to_movie_dict,
    _movie_to_dict,
)
from backend.schemas.movies import MovieCreate, MovieUpdate


class TestMovieRepositoryUnit:
    """Consolidated unit tests for MovieRepository"""

    # ========== FIXTURES ==========

    @pytest.fixture
    def temp_csv_file(self):
        """Create a temporary CSV file for testing"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    'movie_id',
                    'title',
                    'genre',
                    'release_year',
                    'rating',
                    'runtime',
                    'director',
                    'cast',
                    'plot',
                    'poster_url',
                    'created_at',
                    'updated_at',
                ],
            )
            writer.writeheader()
            writer.writerows(
                [
                    {
                        'movie_id': 'tt0111161',
                        'title': 'The Shawshank Redemption',
                        'genre': 'Drama',
                        'release_year': '1994',
                        'rating': '9.3',
                        'runtime': '142',
                        'director': 'Frank Darabont',
                        'cast': 'Tim Robbins, Morgan Freeman',
                        'plot': 'Two imprisoned men bond...',
                        'poster_url': 'https://example.com/poster1.jpg',
                        'created_at': '2024-01-01T12:00:00Z',
                        'updated_at': '2024-01-01T12:00:00Z',
                    },
                    {
                        'movie_id': 'tt0068646',
                        'title': 'The Godfather',
                        'genre': 'Crime, Drama',
                        'release_year': '1972',
                        'rating': '9.2',
                        'runtime': '175',
                        'director': 'Francis Ford Coppola',
                        'cast': 'Marlon Brando, Al Pacino',
                        'plot': 'The aging patriarch...',
                        'poster_url': 'https://example.com/poster2.jpg',
                        'created_at': '2024-01-01T12:00:00Z',
                        'updated_at': '2024-01-01T12:00:00Z',
                    },
                ]
            )
            temp_path = f.name

        yield temp_path
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    @pytest.fixture
    def temp_json_file(self):
        """Create a temporary JSON file for testing"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(
                [
                    {
                        'movie_id': 'tt0111161',
                        'title': 'The Shawshank Redemption',
                        'genre': 'Drama',
                        'release_year': 1994,
                        'rating': 9.3,
                        'runtime': 142,
                        'director': 'Frank Darabont',
                        'cast': 'Tim Robbins, Morgan Freeman',
                        'plot': 'Two imprisoned men bond...',
                        'poster_url': 'https://example.com/poster1.jpg',
                        'created_at': '2024-01-01T12:00:00Z',
                        'updated_at': '2024-01-01T12:00:00Z',
                    },
                    {
                        'movie_id': 'tt0068646',
                        'title': 'The Godfather',
                        'genre': 'Crime, Drama',
                        'release_year': 1972,
                        'rating': 9.2,
                        'runtime': 175,
                        'director': 'Francis Ford Coppola',
                        'cast': 'Marlon Brando, Al Pacino',
                        'plot': 'The aging patriarch...',
                        'poster_url': 'https://example.com/poster2.jpg',
                        'created_at': '2024-01-01T12:00:00Z',
                        'updated_at': '2024-01-01T12:00:00Z',
                    },
                ],
                f,
            )
            temp_path = f.name

        yield temp_path
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    @pytest.fixture
    def csv_repo(self, temp_csv_file):
        """Create MovieRepository instance with CSV backend"""
        with patch('backend.repositories.movies_repo.MOVIES_CSV_PATH', temp_csv_file):
            repo = MovieRepository(use_json=False)
            yield repo

    @pytest.fixture
    def json_repo(self, temp_json_file):
        """Create MovieRepository instance with JSON backend"""
        with patch('backend.repositories.movies_repo.MOVIES_JSON_PATH', temp_json_file):
            repo = MovieRepository(use_json=True)
            yield repo

    @pytest.fixture
    def empty_csv_repo(self):
        """Create MovieRepository instance with empty CSV backend"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    'movie_id',
                    'title',
                    'genre',
                    'release_year',
                    'rating',
                    'runtime',
                    'director',
                    'cast',
                    'plot',
                    'poster_url',
                    'created_at',
                    'updated_at',
                ],
            )
            writer.writeheader()
            temp_path = f.name

        with patch('backend.repositories.movies_repo.MOVIES_CSV_PATH', temp_path):
            repo = MovieRepository(use_json=False)
            yield repo

        if os.path.exists(temp_path):
            os.unlink(temp_path)

    # ========== BASIC CRUD OPERATIONS ==========

    def test_get_all_csv(self, csv_repo):
        """Test getting all movies from CSV repository"""
        movies, total = csv_repo.get_all()
        assert total == 2
        assert len(movies) == 2
        assert movies[0].movie_id == 'tt0111161'
        assert movies[1].movie_id == 'tt0068646'

    def test_get_all_json(self, json_repo):
        """Test getting all movies from JSON repository"""
        movies, total = json_repo.get_all()
        assert total == 2
        assert len(movies) == 2
        assert movies[0].movie_id == 'tt0111161'
        assert movies[1].movie_id == 'tt0068646'

    def test_get_by_id_existing(self, csv_repo):
        """Test getting existing movie by ID"""
        movie = csv_repo.get_by_id('tt0111161')
        assert movie is not None
        assert movie.movie_id == 'tt0111161'
        assert movie.title == 'The Shawshank Redemption'

    def test_get_by_id_nonexistent(self, csv_repo):
        """Test getting non-existent movie by ID"""
        movie = csv_repo.get_by_id('nonexistent_id')
        assert movie is None

    def test_create_movie_basic(self, csv_repo):
        """Test creating a new movie with basic data"""
        movie_create = MovieCreate(
            title="New Test Movie", genre="Comedy", release_year=2024, rating=8.5
        )
        created_movie = csv_repo.create(movie_create)
        assert created_movie is not None
        assert created_movie.title == "New Test Movie"
        assert created_movie.genre == "Comedy"
        assert created_movie.release_year == 2024
        assert created_movie.rating == 8.5
        assert created_movie.movie_id is not None

    def test_update_movie_existing(self, csv_repo):
        """Test updating an existing movie"""
        movie_update = MovieUpdate(title="Updated Title", rating=9.5)
        updated_movie = csv_repo.update('tt0111161', movie_update)
        assert updated_movie is not None
        assert updated_movie.title == "Updated Title"
        assert updated_movie.rating == 9.5
        assert updated_movie.genre == "Drama"  # Preserved

    def test_update_movie_nonexistent(self, csv_repo):
        """Test updating a non-existent movie"""
        movie_update = MovieUpdate(title="Updated Title")
        result = csv_repo.update("nonexistent_id", movie_update)
        assert result is None

    def test_delete_movie_existing(self, csv_repo):
        """Test deleting an existing movie"""
        result = csv_repo.delete('tt0111161')
        assert result is True
        deleted_movie = csv_repo.get_by_id('tt0111161')
        assert deleted_movie is None
        movies, total = csv_repo.get_all()
        assert total == 1

    def test_delete_movie_nonexistent(self, csv_repo):
        """Test deleting a non-existent movie"""
        result = csv_repo.delete('nonexistent_id')
        assert result is False

    # ========== EQUIVALENCE PARTITIONING & BOUNDARY VALUES ==========

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
            movie_create = MovieCreate(title=f"Movie {i}")
            empty_csv_repo.create(movie_create)
        movies, total = empty_csv_repo.get_all(skip=skip, limit=limit)
        assert len(movies) == expected_count
        assert total == 5

    @pytest.mark.parametrize("rating", [0.0, 0.1, 5.0, 7.5, 9.9, 10.0, None])
    def test_rating_field_combined(self, empty_csv_repo, rating):
        """Test rating field with various valid scenarios"""
        movie_create = MovieCreate(title="Rating Test Movie", rating=rating)
        movie = empty_csv_repo.create(movie_create)
        assert movie.rating == rating

    def test_invalid_rating_schema_rejection(self):
        """Test that invalid ratings are rejected by schema validation"""
        with pytest.raises(ValueError, match="greater than or equal to 0"):
            MovieCreate(title="Test Movie", rating=-0.1)
        with pytest.raises(ValueError, match="less than or equal to 10"):
            MovieCreate(title="Test Movie", rating=10.1)

    @pytest.mark.parametrize("release_year", [1895, 1896, 1950, 2000, 2024, None])
    def test_release_year_combined(self, empty_csv_repo, release_year):
        """Test release_year field with various valid scenarios"""
        movie_create = MovieCreate(title="Year Test Movie", release_year=release_year)
        movie = empty_csv_repo.create(movie_create)
        assert movie.release_year == release_year

    @pytest.mark.parametrize(
        "title_input",
        [
            "A",
            "Normal Movie Title",
            "A" * 100,
            "Movie with 123",
            "Movie with spéciål chàrs",
            "🎬 Movie with emoji",
        ],
    )
    def test_title_field_combined(self, empty_csv_repo, title_input):
        """Test title field with various input scenarios"""
        movie_create = MovieCreate(title=title_input)
        movie = empty_csv_repo.create(movie_create)
        assert movie.title == title_input

    # ========== ERROR HANDLING & FAULT INJECTION ==========

    def test_duplicate_movie_creation(self, empty_csv_repo):
        """Test exception handling for duplicate movie creation"""
        movie_create = MovieCreate(movie_id="duplicate123", title="Duplicate Movie")
        first_movie = empty_csv_repo.create(movie_create)
        assert first_movie.movie_id == "duplicate123"
        with pytest.raises(ValueError, match="already exists"):
            empty_csv_repo.create(movie_create)

    def test_corrupted_csv_file_handling(self):
        """Test handling of corrupted CSV file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    'movie_id',
                    'title',
                    'genre',
                    'release_year',
                    'rating',
                    'runtime',
                    'director',
                    'cast',
                    'plot',
                    'poster_url',
                    'created_at',
                    'updated_at',
                ],
            )
            writer.writeheader()
            writer.writerow(
                {
                    'movie_id': 'corrupted',
                    'title': 'Corrupted Movie',
                    'genre': 'Drama',
                    'release_year': 'not_a_number',
                    'rating': 'also_not_number',
                    'runtime': 'abc',
                    'director': 'Test Director',
                    'cast': 'Test Cast',
                    'plot': 'Test Plot',
                    'poster_url': 'https://test.com/poster.jpg',
                    'created_at': 'invalid_date',
                    'updated_at': 'invalid_date',
                }
            )
            temp_path = f.name

        try:
            with patch('backend.repositories.movies_repo.MOVIES_CSV_PATH', temp_path):
                repo = MovieRepository(use_json=False)
                movies, total = repo.get_all()
                assert total == 1
                assert movies[0].title == 'Corrupted Movie'
                assert movies[0].release_year is None
                assert movies[0].rating is None
                assert movies[0].runtime is None
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_corrupted_json_file_handling(self):
        """Test handling of corrupted JSON file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("{invalid json content")
            temp_path = f.name

        try:
            with patch('backend.repositories.movies_repo.MOVIES_JSON_PATH', temp_path):
                repo = MovieRepository(use_json=True)
                movies, total = repo.get_all()
                assert len(movies) == 0
                assert total == 0
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    # ========== HELPER FUNCTION TESTS ==========

    def test_movie_to_dict_complete_data(self):
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
            "review_count": 5,
        }
        result = _movie_to_dict(movie_data)
        assert result["movie_id"] == "tt0111161"
        assert result["title"] == "Test Movie"
        assert result["genre"] == "Drama"
        assert result["review_count"] == 5

    def test_dict_to_movie_dict_auto_generate_id(self):
        """Test _dict_to_movie_dict auto-generates ID when not provided"""
        data = {"title": "Auto ID Movie"}
        result = _dict_to_movie_dict(data)
        assert "movie_id" in result
        assert result["movie_id"] is not None
        try:
            uuid.UUID(result["movie_id"])
        except ValueError:
            pytest.fail("Generated movie_id is not a valid UUID")

    def test_dict_to_movie_dict_empty_strings_to_none(self):
        """Test _dict_to_movie_dict converts empty strings to None"""
        data = {
            "title": "Empty Fields Movie",
            "genre": "",
            "director": "",
            "cast": "",
            "plot": "",
            "poster_url": "",
        }
        result = _dict_to_movie_dict(data)
        assert result["title"] == "Empty Fields Movie"
        assert result["genre"] is None
        assert result["director"] is None
        assert result["cast"] is None
        assert result["plot"] is None
        assert result["poster_url"] is None

    # ========== MOCKING TESTS ==========

    def test_mock_datetime_operations(self):
        """Test datetime operations using mocking"""
        with patch('backend.repositories.movies_repo.datetime') as mock_datetime:
            fixed_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
            mock_datetime.now.return_value = fixed_time
            movie_data = {"title": "Mocked Time Movie", "genre": "Comedy"}
            movie_dict = _dict_to_movie_dict(movie_data)
            assert movie_dict["created_at"] == fixed_time
            assert movie_dict["updated_at"] == fixed_time

    def test_mock_uuid_generation(self):
        """Test UUID generation using mocking"""
        fixed_uuid = "12345678-1234-5678-1234-567812345678"
        with patch('backend.repositories.movies_repo.uuid.uuid4') as mock_uuid:
            mock_uuid.return_value = uuid.UUID(fixed_uuid)
            movie_data = {"title": "Mocked UUID Movie"}
            movie_dict = _dict_to_movie_dict(movie_data)
            assert movie_dict["movie_id"] == fixed_uuid

    def test_mock_file_operations(self, csv_repo):
        """Test repository with mocked file operations"""
        with (
            patch.object(csv_repo, '_load_movies') as mock_load,
            patch.object(csv_repo, '_save_movies') as mock_save,
        ):
            mock_load.return_value = [
                {
                    "movie_id": "mocked123",
                    "title": "Mocked Movie",
                    "genre": "Drama",
                    "release_year": 2024,
                    "rating": 8.5,
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc),
                }
            ]
            movies, total = csv_repo.get_all()
            assert total == 1
            assert movies[0].title == "Mocked Movie"
            mock_load.assert_called_once()

    # ========== SEARCH & FILTER TESTS ==========

    def test_search_by_title(self, csv_repo):
        """Test searching movies by title"""
        movies, total = csv_repo.search(title="shawshank")
        assert total == 1
        assert "Shawshank" in movies[0].title

    def test_search_by_genre(self, csv_repo):
        """Test searching movies by genre"""
        movies, total = csv_repo.search(genre="drama")
        assert total == 2
        assert all("drama" in (movie.genre or "").lower() for movie in movies)

    def test_search_by_rating(self, csv_repo):
        """Test searching movies by minimum rating"""
        movies, total = csv_repo.search(min_rating=9.0)
        assert total == 2
        assert all(movie.rating >= 9.0 for movie in movies)

    def test_get_popular_movies(self, csv_repo):
        """Test getting popular movies sorted by rating"""
        popular_movies = csv_repo.get_popular(limit=2)
        assert len(popular_movies) == 2
        assert popular_movies[0].rating >= popular_movies[1].rating

    def test_get_recent_movies(self, csv_repo):
        """Test getting recently added movies"""
        movie_create = MovieCreate(title="Recent Movie")
        csv_repo.create(movie_create)
        recent_movies = csv_repo.get_recent(limit=3)
        assert len(recent_movies) == 3
        assert recent_movies[0].title == "Recent Movie"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
