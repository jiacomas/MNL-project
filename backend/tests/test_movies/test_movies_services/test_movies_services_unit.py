"""
Comprehensive unit tests for Movies Service
Includes equivalence partitioning, boundary value testing, error handling, fault injection, and state-based testing
"""
import pytest
import time
from unittest.mock import patch
from fastapi import HTTPException, status

from backend.services.movies_service import (
    get_movies,
    search_movies,
    get_movie,
    create_movie,
    update_movie,
    delete_movie,
    get_popular_movies,
    get_movie_stats
)
from backend.schemas.movies import (
    MovieCreate,
    MovieUpdate,
    MovieSearchFilters,
    MovieListResponse,
    MovieOut
)


class TestMoviesServiceUnit:
    """Comprehensive unit tests for Movies Service"""

    # Equivalence Partitioning and Boundary Value Tests
    @pytest.mark.unit
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

        with patch('backend.services.movies_service.movie_repo', mock_repo):
            response = get_movies(page=page, page_size=page_size)

        mock_repo.get_all.assert_called_once_with(
            skip=expected_skip, limit=expected_limit, sort_by=None, sort_desc=False
        )
        assert response.page == page
        assert response.page_size == page_size

    @pytest.mark.unit
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
        with patch('backend.services.movies_service.movie_repo', mock_repo):
            with pytest.raises(expected_exception):
                get_movies(page=page, page_size=page_size)

    @pytest.mark.unit
    @pytest.mark.parametrize("limit", [1, 25, 50])  # Boundary values for limit
    def test_get_popular_movies_boundary_values(self, mock_repo, sample_movie_out, limit):
        """Test boundary values for popular movies limit"""
        mock_repo.get_popular.return_value = [sample_movie_out]

        with patch('backend.services.movies_service.movie_repo', mock_repo):
            movies = get_popular_movies(limit=limit)

        assert len(movies) == 1
        mock_repo.get_popular.assert_called_once_with(limit=limit)

    @pytest.mark.unit
    @pytest.mark.parametrize("invalid_limit", [0, 51, -1])
    def test_get_popular_movies_invalid_boundaries(self, mock_repo, invalid_limit):
        """Test invalid boundary values for popular movies limit"""
        with patch('backend.services.movies_service.movie_repo', mock_repo):
            with pytest.raises(HTTPException) as exc_info:
                get_popular_movies(limit=invalid_limit)

            assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST

    # Basic Functionality Tests
    @pytest.mark.unit
    def test_get_movies_success(self, mock_repo, sample_movie_out):
        """Test successful retrieval of movies with pagination"""
        mock_repo.get_all.return_value = ([sample_movie_out], 100)

        with patch('backend.services.movies_service.movie_repo', mock_repo):
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

    @pytest.mark.unit
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

        with patch('backend.services.movies_service.movie_repo', mock_repo):
            response = search_movies(filters=filters, page=1, page_size=10)

        assert isinstance(response, MovieListResponse)
        assert len(response.items) == 1
        assert response.items[0].title == "The Shawshank Redemption"
        mock_repo.search.assert_called_once()

    # Error Handling Tests
    @pytest.mark.unit
    def test_get_movie_not_found(self, mock_repo):
        """Test getting non-existent movie"""
        mock_repo.get_by_id.return_value = None

        with patch('backend.services.movies_service.movie_repo', mock_repo):
            with pytest.raises(HTTPException) as exc_info:
                get_movie("non-existent-id")

            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.unit
    def test_create_movie_unauthorized(self, mock_repo):
        """Test creating movie without admin privileges"""
        movie_create = MovieCreate(
            title="Unauthorized Movie",
            genre="Drama",
            release_year=2024
        )

        with patch('backend.services.movies_service.movie_repo', mock_repo):
            with pytest.raises(HTTPException) as exc_info:
                create_movie(movie_create, is_admin=False)

            assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.unit
    def test_update_movie_not_found(self, mock_repo):
        """Test updating non-existent movie"""
        movie_update = MovieUpdate(rating=9.5)
        mock_repo.update.return_value = None

        with patch('backend.services.movies_service.movie_repo', mock_repo):
            with pytest.raises(HTTPException) as exc_info:
                update_movie("non-existent-id", movie_update, is_admin=True)

            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    # Fault Injection Tests
    @pytest.mark.unit
    def test_get_movies_repository_exception(self, mock_repo):
        """Test repository raises unexpected exception"""
        mock_repo.get_all.side_effect = Exception("Database connection failed")

        with patch('backend.services.movies_service.movie_repo', mock_repo):
            with pytest.raises(Exception) as exc_info:
                get_movies(page=1, page_size=10)

        assert "Database connection failed" in str(exc_info.value)

    @pytest.mark.unit
    def test_create_movie_invalid_data_fault(self, mock_repo):
        """Test repository-level validation error"""
        movie_create = MovieCreate(
            title="Faulty Movie",
            genre="Drama",
            release_year=2024,
            rating=5.0
        )

        mock_repo.create.side_effect = ValueError("Database constraint violation")

        with patch('backend.services.movies_service.movie_repo', mock_repo):
            with pytest.raises(HTTPException) as exc_info:
                create_movie(movie_create, is_admin=True)

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Database constraint violation" in str(exc_info.value.detail)

    # State-based Tests
    @pytest.mark.unit
    def test_movie_lifecycle_state_changes(self, mock_repo, sample_movie_out):
        """Test complete movie lifecycle state changes"""
        movie_create = MovieCreate(
            title="Lifecycle Test Movie",
            genre="Drama",
            release_year=2024
        )

        movie_update = MovieUpdate(rating=8.5)
        updated_movie = sample_movie_out.model_copy(update={"rating": 8.5})

        # Set up mock responses for each state change
        mock_repo.create.return_value = sample_movie_out
        mock_repo.get_by_id.return_value = sample_movie_out
        mock_repo.update.return_value = updated_movie
        mock_repo.delete.return_value = True

        with patch('backend.services.movies_service.movie_repo', mock_repo):
            # Create movie
            created_movie = create_movie(movie_create, is_admin=True)
            assert created_movie.rating == 9.3

            # Read movie
            retrieved_movie = get_movie("tt0111161")
            assert retrieved_movie.title == "The Shawshank Redemption"

            # Update movie
            updated_result = update_movie("tt0111161", movie_update, is_admin=True)
            assert updated_result.rating == 8.5

            # Delete movie
            delete_movie("tt0111161", is_admin=True)

        # Verify all state transitions were called
        mock_repo.create.assert_called_once()
        mock_repo.get_by_id.assert_called_once_with("tt0111161")
        mock_repo.update.assert_called_once_with("tt0111161", movie_update)
        mock_repo.delete.assert_called_once_with("tt0111161")

    @pytest.mark.unit
    def test_get_movie_stats_success(self, mock_repo, sample_movie_out):
        """Test getting movie statistics with state verification"""
        # Create multiple movies for stats testing
        movies_data = [
            sample_movie_out,
            sample_movie_out.model_copy(update={"movie_id": "tt0068646", "genre": "Crime,Drama", "rating": 9.2}),
            sample_movie_out.model_copy(update={"movie_id": "tt0468569", "genre": "Action,Crime,Drama", "rating": 9.0}),
        ]

        mock_repo.get_all.return_value = (movies_data, 3)

        with patch('backend.services.movies_service.movie_repo', mock_repo):
            stats = get_movie_stats()

        assert stats["total_movies"] == 3
        assert "average_rating" in stats
        assert "top_genres" in stats
        assert "year_range" in stats

        # Verify state calculations
        assert stats["average_rating"] == round((9.3 + 9.2 + 9.0) / 3, 2)
        assert any(genre[0] == "Drama" for genre in stats["top_genres"])

    # Performance Tests
    @pytest.mark.performance
    def test_get_movies_performance_large_dataset(self, mock_repo):
        """Performance test: get_movies with large dataset"""
        # Create a large mock dataset
        large_movie_list = [
            MovieOut(
                movie_id=f"tt{1000000 + i}",
                title=f"Movie {i}",
                genre="Drama",
                release_year=2000 + (i % 25),
                rating=7.0 + (i % 3) * 0.5,
                runtime=120,
                director="Test Director",
                cast="Test Cast",
                plot="Test plot",
                poster_url="https://example.com/poster.jpg",
                created_at="2024-01-01T12:00:00Z",
                updated_at="2024-01-01T12:00:00Z",
                review_count=1000
            ) for i in range(1000)
        ]

        mock_repo.get_all.return_value = (large_movie_list[:50], 1000)

        with patch('backend.services.movies_service.movie_repo', mock_repo):
            start_time = time.time()

            response = get_movies(page=1, page_size=50)

            end_time = time.time()
            execution_time = end_time - start_time

        assert len(response.items) == 50
        assert execution_time < 1.0  # Should complete within 1 second

    @pytest.mark.performance
    def test_search_movies_performance_complex_filters(self, mock_repo):
        """Performance test: search with complex filters"""
        mock_repo.search.return_value = ([], 0)

        complex_filters = MovieSearchFilters(
            title="complex",
            genre="Drama,Action,Comedy",
            min_year=1990,
            max_year=2020,
            min_rating=7.5,
            director="Christopher Nolan"
        )

        with patch('backend.services.movies_service.movie_repo', mock_repo):
            start_time = time.time()

            search_movies(filters=complex_filters, page=1, page_size=50)

            end_time = time.time()
            execution_time = end_time - start_time

        assert execution_time < 2.0  # Complex search should complete within 2 seconds