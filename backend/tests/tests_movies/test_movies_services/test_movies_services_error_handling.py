"""
Error handling and exception tests for Movies Service
"""
import pytest
from unittest.mock import patch, create_autospec
from fastapi import HTTPException, status

from backend.services.movies_service import (
    get_movies,
    get_movie,
    create_movie,
    update_movie,
    delete_movie,
    get_movie_stats
)
from backend.schemas.movies import MovieCreate, MovieUpdate
from backend.repositories.movies_repo import MovieRepository


class TestMoviesServiceErrorHandling:
    """Exception handling and error scenario tests"""

    @pytest.fixture
    def mock_repo(self):
        return create_autospec(MovieRepository)

    def test_get_movies_invalid_page(self, mock_repo):
        """Test get_movies with invalid page number"""
        with patch('backend.services.movies_service.movie_repo', mock_repo):
            with pytest.raises(HTTPException) as exc_info:
                get_movies(page=0, page_size=50)

            assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
            assert "Page must be greater than 0" in str(exc_info.value.detail)

    def test_get_movies_invalid_page_size(self, mock_repo):
        """Test get_movies with invalid page size"""
        with patch('backend.services.movies_service.movie_repo', mock_repo):
            with pytest.raises(HTTPException) as exc_info:
                get_movies(page=1, page_size=0)

            assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
            assert "Page size must be between 1 and 200" in str(exc_info.value.detail)

    def test_get_movie_not_found(self, mock_repo):
        """Test getting non-existent movie"""
        mock_repo.get_by_id.return_value = None

        with patch('backend.services.movies_service.movie_repo', mock_repo):
            with pytest.raises(HTTPException) as exc_info:
                get_movie("non-existent-id")

            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

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

    def test_update_movie_unauthorized(self, mock_repo):
        """Test updating movie without admin privileges"""
        movie_update = MovieUpdate(title="Updated Title")

        with patch('backend.services.movies_service.movie_repo', mock_repo):
            with pytest.raises(HTTPException) as exc_info:
                update_movie("tt0111161", movie_update, is_admin=False)

            assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_movie_unauthorized(self, mock_repo):
        """Test deleting movie without admin privileges"""
        with patch('backend.services.movies_service.movie_repo', mock_repo):
            with pytest.raises(HTTPException) as exc_info:
                delete_movie("tt0111161", is_admin=False)

            assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    def test_update_movie_not_found(self, mock_repo):
        """Test updating non-existent movie"""
        movie_update = MovieUpdate(rating=9.5)
        mock_repo.update.return_value = None

        with patch('backend.services.movies_service.movie_repo', mock_repo):
            with pytest.raises(HTTPException) as exc_info:
                update_movie("non-existent-id", movie_update, is_admin=True)

            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_movie_not_found(self, mock_repo):
        """Test deleting non-existent movie"""
        mock_repo.delete.return_value = False

        with patch('backend.services.movies_service.movie_repo', mock_repo):
            with pytest.raises(HTTPException) as exc_info:
                delete_movie("non-existent-id", is_admin=True)

            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    def test_get_movie_stats_empty(self, mock_repo):
        """Test getting statistics when no movies exist"""
        mock_repo.get_all.return_value = ([], 0)

        with patch('backend.services.movies_service.movie_repo', mock_repo):
            stats = get_movie_stats()

        assert stats["total_movies"] == 0
        assert stats["average_rating"] == 0
        assert stats["top_genres"] == []
        assert stats["year_range"] == {"min": 0, "max": 0}