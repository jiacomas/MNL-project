"""
Basic functional tests for MovieRepository.
Covers CRUD, persistence, and basic search/filter behavior.
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
    """Basic functional tests for MovieRepository"""

    # Fixtures

    @pytest.fixture
    def temp_csv_file(self):
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
            path = f.name

        yield path
        os.unlink(path)

    @pytest.fixture
    def temp_json_file(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(
                [
                    {
                        'movie_id': 'tt0111161',
                        'title': 'The Shawshank Redemption',
                        'genre': 'Drama',
                        'release_year': 1994,
                        'rating': 9.3,
                    },
                    {
                        'movie_id': 'tt0068646',
                        'title': 'The Godfather',
                        'genre': 'Crime, Drama',
                        'release_year': 1972,
                        'rating': 9.2,
                    },
                ],
                f,
            )
            path = f.name

        yield path
        os.unlink(path)

    @pytest.fixture
    def csv_repo(self, temp_csv_file):
        with patch('backend.repositories.movies_repo.MOVIES_CSV_PATH', temp_csv_file):
            yield MovieRepository(use_json=False)

    @pytest.fixture
    def json_repo(self, temp_json_file):
        with patch('backend.repositories.movies_repo.MOVIES_JSON_PATH', temp_json_file):
            yield MovieRepository(use_json=True)

    # CRUD

    def test_get_all_csv(self, csv_repo):
        movies, total = csv_repo.get_all()
        assert total == 2
        assert movies[0].movie_id == 'tt0111161'
        assert movies[1].movie_id == 'tt0068646'

    def test_get_all_json(self, json_repo):
        movies, total = json_repo.get_all()
        assert total == 2

    def test_get_by_id_existing(self, csv_repo):
        movie = csv_repo.get_by_id('tt0111161')
        assert movie and movie.title == 'The Shawshank Redemption'

    def test_get_by_id_nonexistent(self, csv_repo):
        assert csv_repo.get_by_id('bad_id') is None

    def test_create_movie(self, csv_repo):
        created = csv_repo.create(MovieCreate(title="X", genre="Drama"))
        assert created.title == "X"
        assert csv_repo.get_by_id(created.movie_id)

    def test_update_movie(self, csv_repo):
        updated = csv_repo.update('tt0111161', MovieUpdate(title="Updated"))
        assert updated and updated.title == "Updated"

    def test_update_nonexistent(self, csv_repo):
        assert csv_repo.update("bad", MovieUpdate(title="X")) is None

    def test_delete_movie(self, csv_repo):
        assert csv_repo.delete("tt0111161") is True
        assert csv_repo.get_by_id("tt0111161") is None

    # Search / Popular / Recent

    def test_search_by_title(self, csv_repo):
        movies, total = csv_repo.search(title="shaw")
        assert total == 1 and "Shawshank" in movies[0].title

    def test_search_by_genre(self, csv_repo):
        movies, total = csv_repo.search(genre="drama")
        assert total == 2

    def test_search_by_rating(self, csv_repo):
        movies, total = csv_repo.search(min_rating=9.0)
        assert total == 2

    def test_popular(self, csv_repo):
        movies = csv_repo.get_popular(limit=2)
        assert len(movies) == 2
        assert movies[0].rating >= movies[1].rating

    def test_recent(self, csv_repo):
        csv_repo.create(MovieCreate(title="Recent One"))
        recent = csv_repo.get_recent(limit=3)
        assert recent[0].title == "Recent One"
