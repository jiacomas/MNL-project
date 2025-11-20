"""
Basic functional tests for MovieRepository.
Covers CRUD, persistence, caching, and data conversion.
"""

import csv
import json
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

# Assuming MovieRepository is in backend.repositories.movies_repo
# FIX: Import the module-level function _load_movies_from_csv for correct mocking
from backend.repositories.movies_repo import (
    ALL_FIELDS,
    MovieRepository,
    _load_movies_from_csv,
)
from backend.schemas.movies import MovieCreate, MovieUpdate

# --- Fixtures ---


@pytest.fixture
def empty_temp_file():
    """Provides a path to a temporary file that will be cleaned up."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        path = f.name
    yield path
    os.unlink(path)


@pytest.fixture
def populated_csv_data():
    """Returns a list of dictionaries representing valid CSV rows."""
    return [
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
            'review_count': '0',
        },
        {
            'movie_id': 'tt0068646',
            'title': 'The Godfather',
            'genre': 'Crime',
            'release_year': '1972',
            'rating': '9.2',
            'runtime': '175',
            'director': 'Francis Ford Coppola',
            'cast': 'Marlon Brando',
            'plot': 'A crime family saga...',
            'poster_url': 'https://example.com/poster2.jpg',
            'created_at': '2024-01-01T13:00:00Z',
            'updated_at': '2024-01-01T13:00:00Z',
            'review_count': '10',
        },
    ]


@pytest.fixture
def temp_csv_file(empty_temp_file, populated_csv_data):
    """Creates a temporary CSV file populated with two movies."""
    with open(empty_temp_file, 'w', encoding='utf-8', newline='') as f:
        # Use ALL_FIELDS to ensure consistent header writing
        writer = csv.DictWriter(f, fieldnames=ALL_FIELDS)
        writer.writeheader()

        # We only pass data that matches the keys defined in populated_csv_data
        writer.writerows(populated_csv_data)

    return empty_temp_file


@pytest.fixture
def temp_json_file(empty_temp_file):
    """Creates a temporary JSON file populated with one movie."""
    data = [
        {
            'movie_id': 'tt0068646',
            'title': 'The Godfather',
            'genre': 'Crime, Drama',
            'release_year': 1972,
            'rating': 9.2,
            'runtime': 175,
        }
    ]
    with open(empty_temp_file, 'w') as f:
        json.dump(data, f)

    return empty_temp_file


@pytest.fixture
def csv_repo(temp_csv_file):
    """Patches MOVIES_CSV_PATH and returns an initialized CSV repo."""
    with patch('backend.repositories.movies_repo.MOVIES_CSV_PATH', temp_csv_file):
        repo = MovieRepository(use_json=False)
        # Clear the cache before running the test to ensure fresh load
        repo._cache = None
        yield repo


@pytest.fixture
def json_repo(temp_json_file):
    """Patches MOVIES_JSON_PATH and returns an initialized JSON repo."""
    with patch('backend.repositories.movies_repo.MOVIES_JSON_PATH', temp_json_file):
        repo = MovieRepository(use_json=True)
        repo._cache = None
        yield repo


# --- Tests ---


class TestMovieRepositoryFunctional:
    """Tests CRUD and persistence functions."""

    def test_initial_load(self, csv_repo):
        """Tests that the repository loads two movies correctly."""
        movies, total = csv_repo.get_all()
        assert total == 2
        assert movies[0].movie_id == 'tt0111161'
        assert movies[1].title == 'The Godfather'

        # Check type conversion (should be float, int)
        assert isinstance(movies[0].rating, float)
        assert isinstance(movies[0].runtime, int)
        assert movies[0].rating == 9.3

    def test_get_all_json(self, json_repo):
        """Tests initial loading from JSON."""
        movies, total = json_repo.get_all()
        assert total == 1
        assert movies[0].movie_id == 'tt0068646'

    def test_get_by_id_existing(self, csv_repo):
        """Tests retrieval of an existing movie."""
        movie = csv_repo.get_by_id('tt0111161')
        assert movie is not None
        assert movie.title == 'The Shawshank Redemption'

    def test_get_by_id_nonexistent(self, csv_repo):
        """Tests retrieval of a nonexistent movie returns None."""
        assert csv_repo.get_by_id('does_not_exist') is None

    def test_create_movie_new_id_persistence(self, csv_repo):
        """Tests creation and subsequent persistence to file."""
        initial_count = csv_repo.get_all()[1]

        # 1. Create with no ID
        new_movie = csv_repo.create(
            MovieCreate(title="The Test Movie", genre="Sci-Fi", release_year=2024)
        )

        # 2. Check in memory (cache)
        assert new_movie.movie_id
        assert csv_repo.get_by_id(new_movie.movie_id).title == "The Test Movie"
        assert csv_repo.get_all()[1] == initial_count + 1

        # 3. Simulate new repo load (to test persistence)
        csv_repo._cache = None
        persisted_movie = csv_repo.get_by_id(new_movie.movie_id)
        assert persisted_movie.title == "The Test Movie"
        assert csv_repo.get_all()[1] == initial_count + 1

    def test_update_movie_persistence(self, csv_repo):
        """Tests update and subsequent persistence to file."""
        # Update
        updated = csv_repo.update(
            'tt0111161', MovieUpdate(title="Updated Name", rating=10.0)
        )
        assert updated and updated.title == "Updated Name"
        assert updated.rating == 10.0

        # Simulate new repo load (to test persistence)
        csv_repo._cache = None
        reloaded = csv_repo.get_by_id('tt0111161')
        assert reloaded.title == "Updated Name"
        assert reloaded.rating == 10.0

    def test_update_nonexistent(self, csv_repo):
        """Tests updating a nonexistent movie."""
        assert csv_repo.update("bad_id", MovieUpdate(title="X")) is None

    def test_delete_movie_persistence(self, csv_repo):
        """Tests deletion and subsequent persistence to file."""
        initial_count = csv_repo.get_all()[1]

        # 1. Delete
        assert csv_repo.delete("tt0111161") is True
        assert csv_repo.get_by_id("tt0111161") is None
        assert csv_repo.get_all()[1] == initial_count - 1

        # 2. Simulate new repo load (to test persistence)
        csv_repo._cache = None
        assert csv_repo.get_by_id("tt0111161") is None
        assert csv_repo.get_all()[1] == initial_count - 1

    def test_delete_nonexistent(self, csv_repo):
        """Tests deleting a nonexistent movie."""
        assert csv_repo.delete("bad_id") is False


class TestMovieRepositoryAdvanced:
    """Tests caching, sorting, pagination, and data robustness."""

    def test_caching_mechanism(self, temp_csv_file):
        """Ensures the repository uses the cache and avoids re-reading the file."""

        # FIX: The mock wraps the module function directly
        mock_load = MagicMock(wraps=_load_movies_from_csv)

        # Patch targets the function's location within the module
        with patch('backend.repositories.movies_repo._load_movies_from_csv', mock_load):
            repo = MovieRepository(use_json=False)

            # First call loads file
            repo.get_all()
            mock_load.assert_called_once()

            # Second call should use cache, mock_load should not be called again
            repo.get_by_id('tt0111161')
            mock_load.assert_called_once()

            # Create/Update/Delete should refresh the cache
            repo.create(MovieCreate(title="Test Cache", release_year=2024))

            # Third call should now hit the cache again
            repo.get_all()
            mock_load.assert_called_once()

    def test_create_duplicate_id_raises_error(self, csv_repo):
        """Ensures creating a movie with an existing ID raises ValueError."""
        with pytest.raises(ValueError, match="already exists"):
            csv_repo.create(MovieCreate(movie_id="tt0111161", title="Duplicate Movie"))

    def test_get_all_sort_desc(self, csv_repo):
        """Tests sorting by rating in descending order."""
        movies, _ = csv_repo.get_all(sort_by='rating', sort_desc=True)
        # tt0111161 (9.3) should be first, tt0068646 (9.2) second
        assert movies[0].movie_id == 'tt0111161'
        assert movies[1].movie_id == 'tt0068646'

    def test_get_all_pagination(self, csv_repo):
        """Tests skip and limit parameters."""
        # Get one movie starting from the second one (index 1)
        movies, total = csv_repo.get_all(skip=1, limit=1)
        assert total == 2
        assert len(movies) == 1
        assert movies[0].movie_id == 'tt0068646'

    def test_get_popular(self, csv_repo):
        """Tests sorting by popularity (rating)."""
        # Data already sorted by rating desc: tt0111161 (9.3) then tt0068646 (9.2)
        popular = csv_repo.get_popular(limit=1)
        assert len(popular) == 1
        assert popular[0].movie_id == 'tt0111161'

    def test_get_recent(self, csv_repo):
        """Tests sorting by creation date (recent)."""
        # Data created_at: tt0111161 (12:00) then tt0068646 (13:00)
        # Recent should be the one created later (tt0068646)
        recent = csv_repo.get_recent(limit=1)
        assert len(recent) == 1
        assert recent[0].movie_id == 'tt0068646'
