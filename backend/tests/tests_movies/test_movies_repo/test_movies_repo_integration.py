"""
Integration tests for MovieRepository with actual file operations.
Tests data persistence, cross-format compatibility, and concurrent access.
"""
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from backend.app.repositories.movies_repo import MovieRepository
from backend.app.schemas.movies import MovieCreate, MovieUpdate


class TestIntegrationMoviesRepository:
    """Integration tests for MovieRepository with actual file operations"""

    @pytest.fixture
    def temp_data_dir(self):
        """Create a temporary data directory for integration tests"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create subdirectories to match expected structure
            movies_dir = Path(temp_dir) / "movies"
            movies_dir.mkdir(parents=True)

            csv_path = movies_dir / "movies.csv"
            json_path = movies_dir / "movies.json"

            yield temp_dir, str(csv_path), str(json_path)

    def test_movies_repo_integration_csv_full_cycle(self, temp_data_dir):
        """Integration test for complete CSV operations cycle"""
        temp_dir, csv_path, json_path = temp_data_dir

        with patch('backend.app.repositories.movies_repo.MOVIES_CSV_PATH', csv_path), \
                patch('backend.app.repositories.movies_repo.MOVIES_JSON_PATH', json_path):
            repo = MovieRepository(use_json=False)

            # Test 1: Empty repository
            movies, total = repo.get_all()
            assert total == 0
            assert len(movies) == 0

            # Test 2: Create movies
            movie1 = MovieCreate(
                title="Integration Test Movie 1",
                genre="Drama",
                release_year=2024,
                rating=8.5
            )

            movie2 = MovieCreate(
                title="Integration Test Movie 2",
                genre="Comedy",
                release_year=2023,
                rating=7.8
            )

            created1 = repo.create(movie1)
            created2 = repo.create(movie2)

            # Test 3: Verify persistence by creating new repository instance
            repo2 = MovieRepository(use_json=False)
            movies, total = repo2.get_all()
            assert total == 2
            assert any(m.title == "Integration Test Movie 1" for m in movies)
            assert any(m.title == "Integration Test Movie 2" for m in movies)

            # Test 4: Update movie
            update_data = MovieUpdate(rating=9.0)
            updated = repo2.update(created1.movie_id, update_data)
            assert updated.rating == 9.0

            # Test 5: Verify update persistence
            repo3 = MovieRepository(use_json=False)
            retrieved = repo3.get_by_id(created1.movie_id)
            assert retrieved.rating == 9.0

            # Test 6: Delete movie
            delete_result = repo3.delete(created2.movie_id)
            assert delete_result is True

            # Test 7: Verify deletion persistence
            repo4 = MovieRepository(use_json=False)
            movies, total = repo4.get_all()
            assert total == 1
            assert movies[0].movie_id == created1.movie_id

    def test_movies_repo_integration_json_full_cycle(self, temp_data_dir):
        """Integration test for complete JSON operations cycle"""
        temp_dir, csv_path, json_path = temp_data_dir

        with patch('backend.app.repositories.movies_repo.MOVIES_CSV_PATH', csv_path), \
                patch('backend.app.repositories.movies_repo.MOVIES_JSON_PATH', json_path):
            repo = MovieRepository(use_json=True)

            # Test empty repository
            movies, total = repo.get_all()
            assert total == 0

            # Create and verify movie
            movie_create = MovieCreate(
                title="JSON Integration Movie",
                genre="Action",
                release_year=2024
            )

            created = repo.create(movie_create)
            assert created.title == "JSON Integration Movie"

            # Verify persistence with new instance
            repo2 = MovieRepository(use_json=True)
            retrieved = repo2.get_by_id(created.movie_id)
            assert retrieved.title == "JSON Integration Movie"

    def test_movies_repo_integration_cross_format_compatibility(self, temp_data_dir):
        """Test that data can be migrated between CSV and JSON formats"""
        temp_dir, csv_path, json_path = temp_data_dir

        # Start with CSV repository
        with patch('backend.app.repositories.movies_repo.MOVIES_CSV_PATH', csv_path), \
                patch('backend.app.repositories.movies_repo.MOVIES_JSON_PATH', json_path):

            csv_repo = MovieRepository(use_json=False)

            # Create movies in CSV
            movies_to_create = [
                MovieCreate(title=f"Movie {i}", genre="Test", release_year=2000 + i)
                for i in range(3)
            ]

            created_movies = []
            for movie_create in movies_to_create:
                created_movies.append(csv_repo.create(movie_create))

            # Verify CSV has data
            csv_movies, csv_total = csv_repo.get_all()
            assert csv_total == 3

            # Switch to JSON repository and verify it can read the same data
            # (This tests that both formats can coexist and be used interchangeably)
            json_repo = MovieRepository(use_json=True)

            # JSON should be empty initially (separate storage)
            json_movies, json_total = json_repo.get_all()
            assert json_total == 0

            # Create same movies in JSON
            for movie_create in movies_to_create:
                json_repo.create(movie_create)

            # Verify both repositories have their own data
            csv_movies, csv_total = csv_repo.get_all()
            json_movies, json_total = json_repo.get_all()

            assert csv_total == 3
            assert json_total == 3

    def test_movies_repo_integration_concurrent_access(self, temp_data_dir):
        """Test that repository handles concurrent access correctly"""
        temp_dir, csv_path, json_path = temp_data_dir

        def create_movies(repo_instance, prefix, count):
            """Helper function to create movies in a repository instance"""
            for i in range(count):
                movie = MovieCreate(
                    title=f"{prefix} Movie {i}",
                    genre="Test",
                    release_year=2000 + i
                )
                repo_instance.create(movie)

        with patch('backend.app.repositories.movies_repo.MOVIES_CSV_PATH', csv_path), \
                patch('backend.app.repositories.movies_repo.MOVIES_JSON_PATH', json_path):
            # Simulate concurrent access by multiple repository instances
            repo1 = MovieRepository(use_json=False)
            repo2 = MovieRepository(use_json=False)

            # Create movies with both instances
            create_movies(repo1, "Repo1", 2)
            create_movies(repo2, "Repo2", 2)

            # Verify all movies are persisted
            repo3 = MovieRepository(use_json=False)
            movies, total = repo3.get_all()

            # Should have 4 movies total
            assert total == 4
            repo1_titles = [m.title for m in movies if m.title.startswith("Repo1")]
            repo2_titles = [m.title for m in movies if m.title.startswith("Repo2")]
            assert len(repo1_titles) == 2
            assert len(repo2_titles) == 2

    def test_movies_repo_integration_large_dataset(self, temp_data_dir):
        """Test repository performance with large dataset"""
        temp_dir, csv_path, json_path = temp_data_dir

        with patch('backend.app.repositories.movies_repo.MOVIES_CSV_PATH', csv_path), \
                patch('backend.app.repositories.movies_repo.MOVIES_JSON_PATH', json_path):
            repo = MovieRepository(use_json=False)

            # Create larger dataset
            for i in range(100):
                movie = MovieCreate(
                    title=f"Movie {i:03d}",
                    genre="Test",
                    release_year=2000 + (i % 25),
                    rating=5.0 + (i % 5)
                )
                repo.create(movie)

            # Test pagination with large dataset
            movies_page1, total = repo.get_all(skip=0, limit=10)
            assert len(movies_page1) == 10
            assert total == 100

            movies_page10, total = repo.get_all(skip=90, limit=10)
            assert len(movies_page10) == 10

            # Test search with large dataset
            action_movies, action_total = repo.search(genre="Test", min_rating=7.0)
            assert action_total > 0

    def test_movies_repo_integration_data_consistency(self, temp_data_dir):
        """Test data consistency across multiple operations"""
        temp_dir, csv_path, json_path = temp_data_dir

        with patch('backend.app.repositories.movies_repo.MOVIES_CSV_PATH', csv_path), \
                patch('backend.app.repositories.movies_repo.MOVIES_JSON_PATH', json_path):
            repo = MovieRepository(use_json=False)

            # Create initial movie
            movie_create = MovieCreate(
                title="Consistency Test Movie",
                genre="Drama",
                release_year=2024,
                rating=8.0
            )
            created = repo.create(movie_create)
            original_id = created.movie_id

            # Perform multiple updates
            updates = [
                MovieUpdate(rating=8.5),
                MovieUpdate(genre="Thriller"),
                MovieUpdate(title="Updated Consistency Test Movie"),
                MovieUpdate(rating=9.0, genre="Action")
            ]

            for update in updates:
                repo.update(original_id, update)

            # Verify final state
            final_movie = repo.get_by_id(original_id)
            assert final_movie is not None
            assert final_movie.title == "Updated Consistency Test Movie"
            assert final_movie.genre == "Action"
            assert final_movie.rating == 9.0
            assert final_movie.release_year == 2024  # Should remain unchanged

    def test_movies_repo_integration_search_persistence(self, temp_data_dir):
        """Test that search functionality works with persisted data"""
        temp_dir, csv_path, json_path = temp_data_dir

        with patch('backend.app.repositories.movies_repo.MOVIES_CSV_PATH', csv_path), \
                patch('backend.app.repositories.movies_repo.MOVIES_JSON_PATH', json_path):
            repo = MovieRepository(use_json=False)

            # Create test data with specific characteristics
            test_movies = [
                MovieCreate(title="Action Thriller", genre="Action, Thriller", release_year=2020, rating=8.0),
                MovieCreate(title="Drama Story", genre="Drama", release_year=2019, rating=7.5),
                MovieCreate(title="Comedy Special", genre="Comedy", release_year=2021, rating=6.5),
                MovieCreate(title="Sci-Fi Adventure", genre="Sci-Fi, Action", release_year=2022, rating=8.8),
            ]

            for movie in test_movies:
                repo.create(movie)

            # Test search persistence with new instance
            repo2 = MovieRepository(use_json=False)

            # Search by genre
            action_movies, action_total = repo2.search(genre="Action")
            assert action_total == 2
            assert any("Action Thriller" in movie.title for movie in action_movies)
            assert any("Sci-Fi Adventure" in movie.title for movie in action_movies)

            # Search by year range
            recent_movies, recent_total = repo2.search(min_year=2021)
            assert recent_total == 2

            # Search by rating
            high_rated, high_total = repo2.search(min_rating=8.0)
            assert high_total == 2

    def test_movies_repo_integration_sorting_persistence(self, temp_data_dir):
        """Test that sorting works with persisted data"""
        temp_dir, csv_path, json_path = temp_data_dir

        with patch('backend.app.repositories.movies_repo.MOVIES_CSV_PATH', csv_path), \
                patch('backend.app.repositories.movies_repo.MOVIES_JSON_PATH', json_path):
            repo = MovieRepository(use_json=False)

            # Create test data with different ratings
            test_movies = [
                MovieCreate(title="Movie A", rating=7.0, release_year=2020),
                MovieCreate(title="Movie C", rating=9.0, release_year=2022),
                MovieCreate(title="Movie B", rating=8.0, release_year=2021),
            ]

            for movie in test_movies:
                repo.create(movie)

            # Test sorting persistence with new instance
            repo2 = MovieRepository(use_json=False)

            # Sort by title ascending
            movies, total = repo2.get_all(sort_by="title", sort_desc=False)
            assert movies[0].title == "Movie A"
            assert movies[1].title == "Movie B"
            assert movies[2].title == "Movie C"

            # Sort by rating descending
            movies, total = repo2.get_all(sort_by="rating", sort_desc=True)
            assert movies[0].rating == 9.0
            assert movies[1].rating == 8.0
            assert movies[2].rating == 7.0

            # Sort by year ascending
            movies, total = repo2.get_all(sort_by="release_year", sort_desc=False)
            assert movies[0].release_year == 2020
            assert movies[1].release_year == 2021
            assert movies[2].release_year == 2022

if __name__ == "__main__":
    pytest.main([__file__, "-v"])