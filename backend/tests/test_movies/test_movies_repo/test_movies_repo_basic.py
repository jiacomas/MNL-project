"""
Basic functional tests for MovieRepository.
Tests core CRUD operations and data persistence with CSV/JSON backends.
"""

import csv
import json
import os
import tempfile
from unittest.mock import patch

import pytest

from backend.repositories.movies_repo import MovieRepository
from backend.schemas.movies import MovieCreate, MovieUpdate


class TestMovieRepositoryBasic:
    """Basic functional tests for MovieRepository class"""

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
                        'plot': 'Two imprisoned men bond over a number of years...',
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
                        'plot': 'The aging patriarch of an organized crime dynasty...',
                        'poster_url': 'https://example.com/poster2.jpg',
                        'created_at': '2024-01-01T12:00:00Z',
                        'updated_at': '2024-01-01T12:00:00Z',
                    },
                ]
            )
            temp_path = f.name

        yield temp_path

        # Cleanup
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
                        'plot': 'Two imprisoned men bond over a number of years...',
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
                        'plot': 'The aging patriarch of an organized crime dynasty...',
                        'poster_url': 'https://example.com/poster2.jpg',
                        'created_at': '2024-01-01T12:00:00Z',
                        'updated_at': '2024-01-01T12:00:00Z',
                    },
                ],
                f,
            )
            temp_path = f.name

        yield temp_path

        # Cleanup
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

    def test_get_all_csv(self, csv_repo):
        """Test getting all movies from CSV repository"""
        movies, total = csv_repo.get_all()

        assert total == 2
        assert len(movies) == 2
        assert movies[0].movie_id == 'tt0111161'
        assert movies[0].title == 'The Shawshank Redemption'
        assert movies[1].movie_id == 'tt0068646'
        assert movies[1].title == 'The Godfather'

    def test_get_all_json(self, json_repo):
        """Test getting all movies from JSON repository"""
        movies, total = json_repo.get_all()

        assert total == 2
        assert len(movies) == 2
        assert movies[0].movie_id == 'tt0111161'
        assert movies[0].title == 'The Shawshank Redemption'
        assert movies[1].movie_id == 'tt0068646'
        assert movies[1].title == 'The Godfather'

    def test_get_by_id_existing(self, csv_repo):
        """Test getting existing movie by ID"""
        movie = csv_repo.get_by_id('tt0111161')

        assert movie is not None
        assert movie.movie_id == 'tt0111161'
        assert movie.title == 'The Shawshank Redemption'
        assert movie.genre == 'Drama'

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

        # Verify movie was persisted
        retrieved_movie = csv_repo.get_by_id(created_movie.movie_id)
        assert retrieved_movie.title == "New Test Movie"

    def test_update_movie_existing(self, csv_repo):
        """Test updating an existing movie"""
        movie_update = MovieUpdate(title="Updated Title", rating=9.5)

        updated_movie = csv_repo.update('tt0111161', movie_update)

        assert updated_movie is not None
        assert updated_movie.title == "Updated Title"
        assert updated_movie.rating == 9.5
        # Ensure other fields are preserved
        assert updated_movie.genre == "Drama"
        assert updated_movie.release_year == 1994

    def test_update_movie_nonexistent(self, csv_repo):
        """Test updating a non-existent movie"""
        movie_update = MovieUpdate(title="Updated Title")
        result = csv_repo.update("nonexistent_id", movie_update)
        assert result is None

    def test_delete_movie_existing(self, csv_repo):
        """Test deleting an existing movie"""
        result = csv_repo.delete('tt0111161')
        assert result is True

        # Verify movie was deleted
        deleted_movie = csv_repo.get_by_id('tt0111161')
        assert deleted_movie is None

        # Verify total count decreased
        movies, total = csv_repo.get_all()
        assert total == 1

    def test_delete_movie_nonexistent(self, csv_repo):
        """Test deleting a non-existent movie"""
        result = csv_repo.delete('nonexistent_id')
        assert result is False

    def test_search_by_title(self, csv_repo):
        """Test searching movies by title"""
        movies, total = csv_repo.search(title="shawshank")

        assert total == 1
        assert len(movies) == 1
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
        # Should be sorted by rating descending
        assert popular_movies[0].rating >= popular_movies[1].rating

    def test_get_recent_movies(self, csv_repo):
        """Test getting recently added movies"""
        # Create a new movie to ensure we have recent additions
        movie_create = MovieCreate(title="Recent Movie")
        csv_repo.create(movie_create)

        recent_movies = csv_repo.get_recent(limit=3)
        assert len(recent_movies) == 3
        # Most recent should be first
        assert recent_movies[0].title == "Recent Movie"


# pytest configuration to ensure GitHub compatibility
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
