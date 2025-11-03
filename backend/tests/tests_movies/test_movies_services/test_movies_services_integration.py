"""
Integration tests for Movies Service with real repository
"""
import pytest
from unittest.mock import patch

from backend.app.services.movies_service import (
    get_movies,
    search_movies,
    get_movie_stats
)
from backend.app.schemas.movies import MovieSearchFilters, MovieListResponse
from backend.app.repositories.movies_repo import MovieRepository


class TestMoviesServiceIntegration:
    """Integration tests for Movies Service with real repository"""

    @pytest.fixture
    def real_repository(self):
        """Fixture providing a real repository instance for integration tests"""
        # In a real scenario, this would connect to a test database
        from backend.app.repositories.movies_repo import MovieRepository
        return MovieRepository()  # With test database configuration

    @pytest.mark.integration
    @pytest.mark.skip(reason="Requires test database setup")
    def test_integration_get_movies(self, real_repository):
        """Integration test: get movies with real repository"""
        with patch('backend.app.services.movies_service.movie_repo', real_repository):
            response = get_movies(page=1, page_size=10)

        assert isinstance(response, MovieListResponse)
        assert response.page == 1
        assert response.page_size == 10

    @pytest.mark.integration
    @pytest.mark.skip(reason="Requires test database setup")
    def test_integration_search_movies(self, real_repository):
        """Integration test: search movies with real repository"""
        filters = MovieSearchFilters(
            genre="Drama",
            min_rating=8.0
        )

        with patch('backend.app.services.movies_service.movie_repo', real_repository):
            response = search_movies(filters=filters, page=1, page_size=10)

        assert isinstance(response, MovieListResponse)
        # Additional assertions based on expected test data

    @pytest.mark.integration
    @pytest.mark.skip(reason="Requires test database setup")
    def test_integration_movie_crud_workflow(self, real_repository):
        """Integration test: complete CRUD workflow with real repository"""
        # This test would create, read, update, and delete a movie
        # using the actual database connection
        pass

    @pytest.mark.integration
    @pytest.mark.skip(reason="Requires test database setup")
    def test_integration_movie_stats_real_data(self, real_repository):
        """Integration test: movie statistics with real data"""
        with patch('backend.app.services.movies_service.movie_repo', real_repository):
            stats = get_movie_stats()

        assert isinstance(stats, dict)
        assert "total_movies" in stats
        assert "average_rating" in stats
        assert "top_genres" in stats