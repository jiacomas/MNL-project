"""
Fault injection and robustness tests for Movies Service
"""
import pytest
from unittest.mock import patch, create_autospec
from fastapi import HTTPException, status

from backend.app.services.movies_service import (
    get_movies,
    search_movies,
    create_movie,
    update_movie,
    get_movie_stats
)
from backend.app.schemas.movies import MovieCreate, MovieUpdate, MovieSearchFilters
from backend.app.repositories.movies_repo import MovieRepository


class TestMoviesServiceFaultInjection:
    """Fault injection and robustness testing"""

    @pytest.fixture
    def mock_repo(self):
        return create_autospec(MovieRepository)

    def test_get_movies_repository_exception(self, mock_repo):
        """Test fault injection: repository raises unexpected exception"""
        mock_repo.get_all.side_effect = Exception("Database connection failed")

        with patch('backend.app.services.movies_service.movie_repo', mock_repo):
            with pytest.raises(Exception) as exc_info:
                get_movies(page=1, page_size=10)

        assert "Database connection failed" in str(exc_info.value)

    def test_create_movie_invalid_data_fault(self, mock_repo):
        """Test fault injection: repository-level validation error"""
        movie_create = MovieCreate(
            title="Faulty Movie",
            genre="Drama",
            release_year=2024,
            rating=5.0
        )

        # Simulate repository-level validation error
        mock_repo.create.side_effect = ValueError("Database constraint violation")

        with patch('backend.app.services.movies_service.movie_repo', mock_repo):
            with pytest.raises(HTTPException) as exc_info:
                create_movie(movie_create, is_admin=True)

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Database constraint violation" in str(exc_info.value.detail)

    def test_create_movie_pydantic_validation_error(self):
        """Test that Pydantic validation prevents invalid data creation"""
        with pytest.raises(ValueError):
            MovieCreate(
                title="Test Movie",
                genre="Drama",
                release_year=2024,
                rating=-5.0  # Invalid - will fail Pydantic validation
            )

    def test_update_movie_concurrent_modification(self, mock_repo):
        """Test fault injection: concurrent modification scenario"""
        movie_update = MovieUpdate(rating=9.5)

        # Simulate concurrent modification by having the repository return None
        mock_repo.update.return_value = None

        with patch('backend.app.services.movies_service.movie_repo', mock_repo):
            with pytest.raises(HTTPException) as exc_info:
                update_movie("tt0111161", movie_update, is_admin=True)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    def test_search_movies_database_error(self, mock_repo):
        """Test exception handling: database error during search"""
        mock_repo.search.side_effect = Exception("Search index unavailable")

        filters = MovieSearchFilters(title="test")

        with patch('backend.app.services.movies_service.movie_repo', mock_repo):
            with pytest.raises(Exception) as exc_info:
                search_movies(filters=filters, page=1, page_size=10)

        assert "Search index unavailable" in str(exc_info.value)

    def test_get_movie_stats_calculation_error(self, mock_repo):
        """Test exception handling: error during stats calculation"""
        mock_repo.get_all.side_effect = Exception("Statistics calculation failed")

        with patch('backend.app.services.movies_service.movie_repo', mock_repo):
            with pytest.raises(Exception) as exc_info:
                get_movie_stats()

        assert "Statistics calculation failed" in str(exc_info.value)

    def test_create_movie_network_timeout(self, mock_repo):
        """Test exception handling: network timeout during creation"""
        movie_create = MovieCreate(title="Network Test Movie")
        mock_repo.create.side_effect = TimeoutError("Database connection timeout")

        with patch('backend.app.services.movies_service.movie_repo', mock_repo):
            with pytest.raises(TimeoutError) as exc_info:
                create_movie(movie_create, is_admin=True)

        assert "timeout" in str(exc_info.value).lower()