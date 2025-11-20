"""
Integration tests for Movies Service with real repository
Tests actual database interactions and end-to-end workflows
"""

from unittest.mock import patch

import pytest

from backend.repositories.movies_repo import MovieRepository
from backend.schemas.movies import (
    MovieCreate,
    MovieListResponse,
    MovieSearchFilters,
    MovieUpdate,
)
from backend.services.movies_service import (
    create_movie,
    delete_movie,
    get_movie,
    get_movie_stats,
    get_movies,
    search_movies,
    update_movie,
)


class TestMoviesServiceIntegration:
    """Integration tests for Movies Service with real repository"""

    @pytest.fixture
    def real_repository(self):
        """Fixture providing a real repository instance for integration tests"""
        # In a real scenario, this would connect to a test database
        return MovieRepository()  # With test database configuration

    @pytest.mark.integration
    def test_integration_get_movies(self, real_repository):
        """Integration test: get movies with real repository"""
        with patch('backend.services.movies_service.movie_repo', real_repository):
            response = get_movies(page=1, page_size=10)

        assert isinstance(response, MovieListResponse)
        assert response.page == 1
        assert response.page_size == 10

    @pytest.mark.integration
    def test_integration_search_movies(self, real_repository):
        """Integration test: search movies with real repository"""
        filters = MovieSearchFilters(genre="Drama", min_rating=8.0)

        with patch('backend.services.movies_service.movie_repo', real_repository):
            response = search_movies(filters=filters, page=1, page_size=10)

        assert isinstance(response, MovieListResponse)
        # Additional assertions based on expected test data

    @pytest.mark.integration
    def test_integration_movie_crud_workflow(self, real_repository):
        """Integration test: complete CRUD workflow with real repository"""
        # Test data
        movie_create = MovieCreate(
            title="Integration Test Movie", genre="Drama", release_year=2024, rating=8.5
        )

        movie_update = MovieUpdate(rating=9.0)

        with patch('backend.services.movies_service.movie_repo', real_repository):
            # Create movie
            created_movie = create_movie(movie_create, is_admin=True)
            movie_id = created_movie.movie_id

            # Read movie
            retrieved_movie = get_movie(movie_id)
            assert retrieved_movie.title == "Integration Test Movie"

            # Update movie
            updated_movie = update_movie(movie_id, movie_update, is_admin=True)
            assert updated_movie.rating == 9.0

            # Delete movie
            delete_movie(movie_id, is_admin=True)

            # Verify deletion
            with pytest.raises(Exception):  # Should raise 404
                get_movie(movie_id)

    @pytest.mark.integration
    def test_integration_movie_stats_real_data(self, real_repository):
        """Integration test: movie statistics with real data"""
        with patch('backend.services.movies_service.movie_repo', real_repository):
            stats = get_movie_stats()

        assert isinstance(stats, dict)
        assert "total_movies" in stats
        assert "average_rating" in stats
        assert "top_genres" in stats
        assert "year_range" in stats

    @pytest.mark.integration
    def test_integration_complex_search_scenarios(self, real_repository):
        """Integration test: complex search scenarios with real data"""
        test_cases = [
            MovieSearchFilters(genre="Action", min_rating=7.5, min_year=2010),
            MovieSearchFilters(director="Christopher Nolan", max_year=2020),
            MovieSearchFilters(title="the", genre="Drama,Crime", min_rating=8.0),
        ]

        with patch('backend.services.movies_service.movie_repo', real_repository):
            for filters in test_cases:
                response = search_movies(filters=filters, page=1, page_size=20)
                assert isinstance(response, MovieListResponse)
                # Validate that results match filter criteria
                for movie in response.items:
                    if filters.min_rating:
                        assert movie.rating >= filters.min_rating
                    if filters.min_year:
                        assert movie.release_year >= filters.min_year
                    if filters.max_year:
                        assert movie.release_year <= filters.max_year
