"""
Basic functionality tests for Movies Router.
Tests successful API endpoints, parameter validation, and normal workflows.
"""
import pytest
from unittest.mock import patch
from fastapi import status, HTTPException

from main import app
from schemas.movies import MovieOut, MovieListResponse


@pytest.mark.basic
class TestMoviesRouterBasic:
    """Basic functionality tests for movies router endpoints"""

    def test_list_movies_success(self, client, sample_movie_out):
        """Test successful retrieval of movies list"""
        mock_response = MovieListResponse(
            items=[sample_movie_out],
            total=100,
            page=1,
            page_size=50,
            total_pages=2
        )

        with patch('routers.movies.svc.get_movies', return_value=mock_response):
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

        with patch('routers.movies.svc.search_movies', return_value=mock_response):
            response = client.get("/api/movies/search?title=shawshank&genre=Drama")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["movie_id"] == "tt0111161"

    def test_get_movie_success(self, client, sample_movie_out):
        """Test successful retrieval of movie by ID"""
        with patch('routers.movies.svc.get_movie', return_value=sample_movie_out):
            response = client.get("/api/movies/tt0111161")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["movie_id"] == "tt0111161"
        assert data["title"] == "The Shawshank Redemption"

    def test_get_movie_not_found(self, client):
        """Test retrieval of non-existent movie"""
        with patch('routers.movies.svc.get_movie') as mock_get:
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

        with patch('routers.movies.svc.create_movie', return_value=sample_movie_out), \
                patch('routers.movies.get_current_admin_user', return_value=mock_current_admin):
            response = client.post("/api/movies", json=movie_data)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["movie_id"] == "tt0111161"
        assert data["title"] == "The Shawshank Redemption"

    @pytest.mark.parametrize("page,page_size,expected_status", [
        (1, 50, status.HTTP_200_OK),
        (1, 1, status.HTTP_200_OK),
        (1, 200, status.HTTP_200_OK),
        (9999, 50, status.HTTP_200_OK),
        (0, 50, status.HTTP_422_UNPROCESSABLE_ENTITY),
        (1, 0, status.HTTP_422_UNPROCESSABLE_ENTITY),
        (1, 201, status.HTTP_422_UNPROCESSABLE_ENTITY),
    ])
    def test_list_movies_parameter_validation(self, client, page, page_size, expected_status):
        """Test parameter validation using equivalence partitioning and boundary values"""
        with patch('routers.movies.svc.get_movies') as mock_svc:
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
        (1990, 2000, 8.0, status.HTTP_200_OK),
        (1888, 2100, 0.0, status.HTTP_200_OK),
        (1888, 2100, 10.0, status.HTTP_200_OK),
        (1887, 2000, 8.0, status.HTTP_422_UNPROCESSABLE_ENTITY),
        (1990, 2101, 8.0, status.HTTP_422_UNPROCESSABLE_ENTITY),
        (1990, 2000, -1.0, status.HTTP_422_UNPROCESSABLE_ENTITY),
        (1990, 2000, 11.0, status.HTTP_422_UNPROCESSABLE_ENTITY),
        (2000, 1990, 8.0, status.HTTP_200_OK),
    ])
    def test_search_movies_parameter_validation(self, client, min_year, max_year, min_rating, expected_status):
        """Test search parameter validation with equivalence partitioning"""
        with patch('routers.movies.svc.search_movies') as mock_svc:
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

    def test_get_popular_movies_success(self, client, sample_movie_out):
        """Test successful retrieval of popular movies"""
        with patch('routers.movies.svc.get_popular_movies', return_value=[sample_movie_out]):
            response = client.get("/api/movies/popular?limit=10")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["movie_id"] == "tt0111161"

    def test_get_recent_movies_success(self, client, sample_movie_out):
        """Test successful retrieval of recent movies"""
        with patch('routers.movies.svc.get_recent_movies', return_value=[sample_movie_out]):
            response = client.get("/api/movies/recent?limit=10")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["movie_id"] == "tt0111161"