"""
Exception handling and fault injection tests for Movies Repository.
Tests error conditions, corrupted data, and exception scenarios.
"""
import csv
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from backend.app.repositories.movies_repo import MovieRepository
from backend.app.schemas.movies import MovieCreate, MovieUpdate


class TestMoviesRepoExceptionHandling:
    """Exception handling and fault injection tests for MovieRepository"""

    def test_movies_repo_duplicate_movie_creation(self):
        """Test exception handling for duplicate movie creation"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.DictWriter(f, fieldnames=[
                'movie_id', 'title', 'genre', 'release_year', 'rating',
                'runtime', 'director', 'cast', 'plot', 'poster_url',
                'created_at', 'updated_at'
            ])
            writer.writeheader()
            temp_path = f.name

        try:
            with patch('backend.app.repositories.movies_repo.MOVIES_CSV_PATH', temp_path):
                repo = MovieRepository(use_json=False)

                movie_create = MovieCreate(
                    movie_id="duplicate123",
                    title="Duplicate Movie"
                )

                # First creation should succeed
                first_movie = repo.create(movie_create)
                assert first_movie.movie_id == "duplicate123"

                # Second creation should raise ValueError
                with pytest.raises(ValueError, match="already exists"):
                    repo.create(movie_create)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_movies_repo_update_nonexistent_movie(self):
        """Test updating a movie that doesn't exist"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.DictWriter(f, fieldnames=[
                'movie_id', 'title', 'genre', 'release_year', 'rating',
                'runtime', 'director', 'cast', 'plot', 'poster_url',
                'created_at', 'updated_at'
            ])
            writer.writeheader()
            temp_path = f.name

        try:
            with patch('backend.app.repositories.movies_repo.MOVIES_CSV_PATH', temp_path):
                repo = MovieRepository(use_json=False)

                movie_update = MovieUpdate(title="Updated Title")
                result = repo.update("nonexistent_id", movie_update)
                assert result is None
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_movies_repo_corrupted_csv_file(self):
        """Test handling of corrupted CSV file with fault injection"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            # Write a CSV that has the right headers but corrupted data
            writer = csv.DictWriter(f, fieldnames=[
                'movie_id', 'title', 'genre', 'release_year', 'rating',
                'runtime', 'director', 'cast', 'plot', 'poster_url',
                'created_at', 'updated_at'
            ])
            writer.writeheader()
            # Write corrupted row with wrong data types
            writer.writerow({
                'movie_id': 'corrupted',
                'title': 'Corrupted Movie',
                'genre': 'Drama',
                'release_year': 'not_a_number',  # Invalid type
                'rating': 'also_not_number',     # Invalid type
                'runtime': 'abc',               # Invalid type
                'director': 'Test Director',
                'cast': 'Test Cast',
                'plot': 'Test Plot',
                'poster_url': 'https://test.com/poster.jpg',
                'created_at': 'invalid_date',   # Invalid date
                'updated_at': 'invalid_date'    # Invalid date
            })
            temp_path = f.name

        try:
            with patch('backend.app.repositories.movies_repo.MOVIES_CSV_PATH', temp_path):
                repo = MovieRepository(use_json=False)
                # Should handle corruption gracefully
                movies, total = repo.get_all()

                # Should still load the movie but with None for invalid fields
                assert total == 1
                assert len(movies) == 1
                assert movies[0].title == 'Corrupted Movie'
                # Invalid numeric fields should be None
                assert movies[0].release_year is None
                assert movies[0].rating is None
                assert movies[0].runtime is None

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_movies_repo_corrupted_json_file(self):
        """Test handling of corrupted JSON file with fault injection"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            # Write invalid JSON content
            f.write("{invalid json content")
            temp_path = f.name

        try:
            with patch('backend.app.repositories.movies_repo.MOVIES_JSON_PATH', temp_path):
                repo = MovieRepository(use_json=True)
                # Should handle corruption gracefully
                movies, total = repo.get_all()
                assert len(movies) == 0
                assert total == 0
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_movies_repo_missing_data_directory(self, tmp_path):
        """Test repository operation when data directory doesn't exist"""
        non_existent_path = tmp_path / "nonexistent" / "movies.csv"

        with patch('backend.app.repositories.movies_repo.MOVIES_CSV_PATH', str(non_existent_path)):
            repo = MovieRepository(use_json=False)

            # Should handle missing directory gracefully
            movies, total = repo.get_all()
            assert len(movies) == 0
            assert total == 0

            # Should be able to create new movie (directory should be created)
            movie_create = MovieCreate(title="Test Movie")
            movie = repo.create(movie_create)
            assert movie.title == "Test Movie"

    def test_movies_repo_file_permission_denied(self, tmp_path):
        """Test handling of permission denied errors"""
        read_only_file = tmp_path / "readonly.csv"
        read_only_file.touch()
        read_only_file.chmod(0o444)  # Read-only

        try:
            with patch('backend.app.repositories.movies_repo.MOVIES_CSV_PATH', str(read_only_file)):
                repo = MovieRepository(use_json=False)

                # Reading should work
                movies, total = repo.get_all()
                assert len(movies) == 0

                # Writing should fail gracefully
                movie_create = MovieCreate(title="Test Movie")
                with pytest.raises(Exception):  # Should raise some exception
                    repo.create(movie_create)
        finally:
            # Restore permissions for cleanup
            read_only_file.chmod(0o644)

    def test_movies_repo_invalid_movie_data_handling(self):
        """Test handling of invalid movie data in storage"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.DictWriter(f, fieldnames=[
                'movie_id', 'title', 'genre', 'release_year', 'rating',
                'runtime', 'director', 'cast', 'plot', 'poster_url',
                'created_at', 'updated_at'
            ])
            writer.writeheader()
            # Write row with invalid data types
            writer.writerow({
                'movie_id': 'invalid_movie',
                'title': 'Invalid Movie',
                'genre': 'Drama',
                'release_year': 'not_a_number',  # Invalid
                'rating': 'also_not_number',     # Invalid
                'runtime': '123',               # Valid
                'director': 'Test Director',
                'cast': 'Test Cast',
                'plot': 'Test Plot',
                'poster_url': 'https://test.com/poster.jpg',
                'created_at': 'invalid_date',   # Invalid
                'updated_at': 'invalid_date'    # Invalid
            })
            temp_path = f.name

        try:
            with patch('backend.app.repositories.movies_repo.MOVIES_CSV_PATH', temp_path):
                repo = MovieRepository(use_json=False)

                # Should handle invalid data gracefully
                movies, total = repo.get_all()
                assert total == 1

                # The invalid movie should be accessible
                movie = repo.get_by_id('invalid_movie')
                assert movie is not None
                assert movie.title == 'Invalid Movie'
                # Invalid numeric fields should be None
                assert movie.release_year is None
                assert movie.rating is None
                # Valid runtime should be preserved
                assert movie.runtime == 123

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_movies_repo_empty_file_handling(self):
        """Test handling of empty files"""
        # Test empty CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            # Write only headers
            writer = csv.DictWriter(f, fieldnames=[
                'movie_id', 'title', 'genre', 'release_year', 'rating',
                'runtime', 'director', 'cast', 'plot', 'poster_url',
                'created_at', 'updated_at'
            ])
            writer.writeheader()
            temp_path = f.name

        try:
            with patch('backend.app.repositories.movies_repo.MOVIES_CSV_PATH', temp_path):
                repo = MovieRepository(use_json=False)
                movies, total = repo.get_all()
                assert total == 0
                assert len(movies) == 0
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_movies_repo_malformed_dates_handling(self):
        """Test handling of malformed date strings"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.DictWriter(f, fieldnames=[
                'movie_id', 'title', 'genre', 'release_year', 'rating',
                'runtime', 'director', 'cast', 'plot', 'poster_url',
                'created_at', 'updated_at'
            ])
            writer.writeheader()
            writer.writerow({
                'movie_id': 'date_test',
                'title': 'Date Test Movie',
                'genre': 'Drama',
                'release_year': '2024',
                'rating': '8.5',
                'runtime': '120',
                'director': 'Test Director',
                'cast': 'Test Cast',
                'plot': 'Test Plot',
                'poster_url': 'https://test.com/poster.jpg',
                'created_at': 'not-a-real-date',  # Malformed date
                'updated_at': '2024-01-01T12:00:00Z'  # Valid date
            })
            temp_path = f.name

        try:
            with patch('backend.app.repositories.movies_repo.MOVIES_CSV_PATH', temp_path):
                repo = MovieRepository(use_json=False)

                # Should handle malformed dates gracefully
                movies, total = repo.get_all()
                assert total == 1
                assert movies[0].title == 'Date Test Movie'

                # Should have fallback to current time for invalid dates
                assert movies[0].created_at is not None
                assert movies[0].updated_at is not None

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)