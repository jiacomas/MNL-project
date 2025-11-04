"""
Basic functionality tests for Movies Router.
Tests successful API endpoints, parameter validation, and normal workflows.
"""
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from fastapi import status, HTTPException

from backend.main import app
from backend.schemas.movies import MovieOut, MovieListResponse


class TestMoviesRouterBasic:
    """Basic functionality tests for movies router endpoints"""

    @pytest.fixture
    def client(self):
        """Create test client for FastAPI app"""
        return TestClient(app)

    @pytest.fixture
    def sample_movie_data(self):
        """Sample movie data for testing"""
        return {
            "movie_id": "tt0111161",
            "title": "The Shawshank Redemption",
            "genre": "Drama",
            "release_year": 1994,
            "rating": 9.3,
            "runtime": 142,
            "director": "Frank Darabont",
            "cast": "Tim Robbins, Morgan Freeman",
            "plot": "Two imprisoned men bond over a number of years...",
            "poster_url": "https://example.com/poster.jpg",
            "created_at": "2024-01-01T12:00:00Z",
            "updated_at": "2024-01-01T12:00:00Z",
            "review_count": 2500000
        }

    @pytest.fixture
    def sample_movie_out(self, sample_movie_data):
        """Create MovieOut instance from sample data"""
        return MovieOut(**sample_movie_data)

    @pytest.fixture
    def mock_current_user(self):
        """Mock current user for authentication"""
        return {"user_id": "test_user", "role": "user"}

    @pytest.fixture
    def mock_current_admin(self):
        """Mock admin user for authentication"""
        return {"user_id": "admin_user", "role": "admin"}

    # ========== BASIC SUCCESS TESTS ==========

    def test_list_movies_success(self, client, sample_movie_out):
        """Test successful retrieval of movies list"""
        mock_response = MovieListResponse(
            items=[sample_movie_out],
            total=100,
            page=1,
            page_size=50,
            total_pages=2
        )

        with patch('backend.routers.movies.svc.get_movies', return_value=mock_response):
            response = client.get("/api/movies?page=1&page_size=50")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 100
        assert data["page"] == 1
        assert data["page_size"] == 50
        assert data["total_pages"] == 2
        assert len(data["items"]) == 1
        assert data["items"][0]["movie_id"] == "tt0111161"

    def test_search_movies_success(self, client, sample_movie_out):
        """Test successful movie search"""
        mock_response = MovieListResponse(
            items=[sample_movie_out],
            total=1,
            page=1,
            page_size=50,
            total_pages=1
        )

        with patch('backend.routers.movies.svc.search_movies', return_value=mock_response):
            response = client.get("/api/movies/search?title=shawshank&genre=Drama")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["movie_id"] == "tt0111161"

    def test_get_movie_success(self, client, sample_movie_out):
        """Test successful retrieval of movie by ID"""
        with patch('backend.routers.movies.svc.get_movie', return_value=sample_movie_out):
            response = client.get("/api/movies/tt0111161")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["movie_id"] == "tt0111161"
        assert data["title"] == "The Shawshank Redemption"

    def test_get_movie_not_found(self, client):
        """Test retrieval of non-existent movie"""
        with patch('backend.routers.movies.svc.get_movie') as mock_get:
            mock_get.side_effect = HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Movie not found"
            )

            response = client.get("/api/movies/nonexistent")
            assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_create_movie_success_admin(self, client, sample_movie_out, mock_current_admin):
        """Test successful movie creation by admin"""
        movie_data = {
            "title": "New Test Movie",
            "genre": "Drama",
            "release_year": 2024
        }

        with patch('backend.routers.movies.svc.create_movie', return_value=sample_movie_out), \
                patch('backend.routers.movies.get_current_admin_user', return_value=mock_current_admin):
            response = client.post("/api/movies", json=movie_data)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["movie_id"] == "tt0111161"
        assert data["title"] == "The Shawshank Redemption"

    # ========== PARAMETER VALIDATION TESTS ==========

    @pytest.mark.parametrize("page,page_size,expected_status", [
        (1, 50, status.HTTP_200_OK),  # Valid normal values
        (1, 1, status.HTTP_200_OK),  # Lower boundary for page_size
        (1, 200, status.HTTP_200_OK),  # Upper boundary for page_size
        (9999, 50, status.HTTP_200_OK),  # High page number (empty result)
        (0, 50, status.HTTP_422_UNPROCESSABLE_ENTITY),  # Invalid lower boundary
        (1, 0, status.HTTP_422_UNPROCESSABLE_ENTITY),  # Invalid lower boundary
        (1, 201, status.HTTP_422_UNPROCESSABLE_ENTITY),  # Invalid upper boundary
    ])
    def test_list_movies_parameter_validation(self, client, page, page_size, expected_status):
        """Test parameter validation using equivalence partitioning and boundary values"""
        with patch('backend.routers.movies.svc.get_movies') as mock_svc:
            if expected_status == status.HTTP_200_OK:
                mock_svc.return_value = MovieListResponse(
                    items=[],
                    total=0,
                    page=page,
                    page_size=page_size,
                    total_pages=0
                )

            response = client.get(f"/api/movies?page={page}&page_size={page_size}")
            assert response.status_code == expected_status

    @pytest.mark.parametrize("min_year,max_year,min_rating,expected_status", [
        (1990, 2000, 8.0, status.HTTP_200_OK),  # All valid
        (1888, 2100, 0.0, status.HTTP_200_OK),  # Boundary values
        (1888, 2100, 10.0, status.HTTP_200_OK),  # Boundary values
        (1887, 2000, 8.0, status.HTTP_422_UNPROCESSABLE_ENTITY),  # Invalid min_year
        (1990, 2101, 8.0, status.HTTP_422_UNPROCESSABLE_ENTITY),  # Invalid max_year
        (1990, 2000, -1.0, status.HTTP_422_UNPROCESSABLE_ENTITY),  # Invalid min_rating
        (1990, 2000, 11.0, status.HTTP_422_UNPROCESSABLE_ENTITY),  # Invalid min_rating
        (2000, 1990, 8.0, status.HTTP_200_OK),  # Logic error but syntactically valid
    ])
    def test_search_movies_parameter_validation(self, client, min_year, max_year, min_rating, expected_status):
        """Test search parameter validation with equivalence partitioning"""
        with patch('backend.routers.movies.svc.search_movies') as mock_svc:
            mock_svc.return_value = MovieListResponse(
                items=[],
                total=0,
                page=1,
                page_size=50,
                total_pages=0
            )

            url = f"/api/movies/search?min_year={min_year}&max_year={max_year}&min_rating={min_rating}"
            response = client.get(url)
            assert response.status_code == expected_status


if __name__ == "__main__":
    pytest.main([__file__, "-v"])