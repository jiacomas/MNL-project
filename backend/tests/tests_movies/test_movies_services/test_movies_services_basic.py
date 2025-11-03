"""
Basic unit tests for Movies Service - Equivalence Partitioning and Boundary Value Testing
"""
import pytest
from unittest.mock import patch, create_autospec
from fastapi import HTTPException, status

from backend.app.services.movies_service import (
    get_movies,
    search_movies,
    get_movie,
    create_movie,
    update_movie,
    delete_movie,
    get_popular_movies,
    get_recent_movies,
    get_movie_recommendations,
    get_movie_stats
)
from backend.app.schemas.movies import (
    MovieCreate,
    MovieUpdate,
    MovieOut,
    MovieSearchFilters,
    MovieListResponse
)
from backend.app.repositories.movies_repo import MovieRepository


class TestMoviesServiceBasic:
    """Basic unit tests with equivalence partitioning and boundary value analysis"""

    @pytest.fixture
    def mock_repo(self):
        return create_autospec(MovieRepository)

    @pytest.fixture
    def sample_movie_out(self):
        return MovieOut(
            movie_id="tt0111161",
            title="The Shawshank Redemption",
            genre="Drama",
            release_year=1994,
            rating=9.3,
            runtime=142,
            director="Frank Darabont",
            cast="Tim Robbins, Morgan Freeman",
            plot="Two imprisoned men bond over a number of years...",
            poster_url="https://example.com/poster.jpg",
            created_at="2024-01-01T12:00:00Z",
            updated_at="2024-01-01T12:00:00Z",
            review_count=2500000
        )

    # ==================== EQUIVALENCE PARTITIONING TESTS ====================

    @pytest.mark.parametrize("page,page_size,expected_skip,expected_limit", [
        # Valid equivalence classes
        (1, 10, 0, 10),  # Minimum valid values
        (2, 50, 50, 50),  # Normal case
        (5, 200, 800, 200),  # Maximum page size
        # Boundary values
        (1, 1, 0, 1),  # Minimum page size
        (1000, 50, 49950, 50),  # Large page number
    ])
    def test_get_movies_equivalence_partitioning(self, mock_repo, sample_movie_out,
                                                 page, page_size, expected_skip, expected_limit):
        """Test get_movies with various equivalence partitions"""
        mock_repo.get_all.return_value = ([sample_movie_out], 1000)

        with patch('backend.app.services.movies_service.movie_repo', mock_repo):
            response = get_movies(page=page, page_size=page_size)

        mock_repo.get_all.assert_called_once_with(
            skip=expected_skip, limit=expected_limit, sort_by=None, sort_desc=False
        )
        assert response.page == page
        assert response.page_size == page_size

    @pytest.mark.parametrize("page,page_size,expected_exception", [
        # Invalid equivalence classes
        (0, 10, HTTPException),  # Page too small
        (-1, 10, HTTPException),  # Negative page
        (1, 0, HTTPException),  # Page size too small
        (1, 201, HTTPException),  # Page size too large
        (1, -1, HTTPException),  # Negative page size
    ])
    def test_get_movies_invalid_equivalence(self, mock_repo, page, page_size, expected_exception):
        """Test get_movies with invalid equivalence partitions"""
        with patch('backend.app.services.movies_service.movie_repo', mock_repo):
            with pytest.raises(expected_exception):
                get_movies(page=page, page_size=page_size)

    # ==================== BOUNDARY VALUE TESTS ====================

    @pytest.mark.parametrize("limit", [1, 25, 50])  # Boundary values for limit
    def test_get_popular_movies_boundary_values(self, mock_repo, sample_movie_out, limit):
        """Test boundary values for popular movies limit"""
        mock_repo.get_popular.return_value = [sample_movie_out]

        with patch('backend.app.services.movies_service.movie_repo', mock_repo):
            movies = get_popular_movies(limit=limit)

        assert len(movies) == 1
        mock_repo.get_popular.assert_called_once_with(limit=limit)

    @pytest.mark.parametrize("invalid_limit", [0, 51, -1])
    def test_get_popular_movies_invalid_boundaries(self, mock_repo, invalid_limit):
        """Test invalid boundary values for popular movies limit"""
        with patch('backend.app.services.movies_service.movie_repo', mock_repo):
            with pytest.raises(HTTPException) as exc_info:
                get_popular_movies(limit=invalid_limit)

            assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST

    # ==================== BASIC SUCCESS TESTS ====================

    def test_get_movies_success(self, mock_repo, sample_movie_out):
        """Test successful retrieval of movies with pagination"""
        mock_repo.get_all.return_value = ([sample_movie_out], 100)

        with patch('backend.app.services.movies_service.movie_repo', mock_repo):
            response = get_movies(page=1, page_size=50)

        assert isinstance(response, MovieListResponse)
        assert len(response.items) == 1
        assert response.items[0].movie_id == "tt0111161"
        assert response.total == 100
        assert response.page == 1
        assert response.page_size == 50
        assert response.total_pages == 2

        mock_repo.get_all.assert_called_once_with(
            skip=0, limit=50, sort_by=None, sort_desc=False
        )

    def test_search_movies_success(self, mock_repo, sample_movie_out):
        """Test successful movie search with filters"""
        mock_repo.search.return_value = ([sample_movie_out], 1)

        filters = MovieSearchFilters(
            title="shawshank",
            genre="Drama",
            min_year=1990,
            max_year=2000,
            min_rating=9.0
        )

        with patch('backend.app.services.movies_service.movie_repo', mock_repo):
            response = search_movies(filters=filters, page=1, page_size=10)

        assert isinstance(response, MovieListResponse)
        assert len(response.items) == 1
        assert response.items[0].title == "The Shawshank Redemption"
        mock_repo.search.assert_called_once()

    def test_get_recent_movies_success(self, mock_repo, sample_movie_out):
        """Test getting recent movies"""
        mock_repo.get_recent.return_value = [sample_movie_out]

        with patch('backend.app.services.movies_service.movie_repo', mock_repo):
            movies = get_recent_movies(limit=5)

        assert len(movies) == 1
        mock_repo.get_recent.assert_called_once_with(limit=5)

    def test_get_movie_recommendations(self, mock_repo, sample_movie_out):
        """Test getting movie recommendations"""
        mock_repo.get_popular.return_value = [sample_movie_out]

        with patch('backend.app.services.movies_service.movie_repo', mock_repo):
            recommendations = get_movie_recommendations("user123", limit=5)

        assert len(recommendations) == 1
        mock_repo.get_popular.assert_called_once_with(limit=5)