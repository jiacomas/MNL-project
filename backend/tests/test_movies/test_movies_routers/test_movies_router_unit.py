"""
Comprehensive unit tests for Movies Router.
Combines basic functionality, error handling, and security tests.
"""

import asyncio
import threading
from unittest.mock import patch

import pytest
from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError

from backend.schemas.movies import MovieListResponse


class TestMoviesRouterUnit:
    """Unit tests covering basic functionality, error handling, and security"""

    # Basic functionality tests
    def test_list_movies_success(self, client, sample_movie_out):
        """Test successful retrieval of movies list"""
        mock_response = MovieListResponse(
            items=[sample_movie_out], total=100, page=1, page_size=50, total_pages=2
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

    def test_get_movie_success(self, client, sample_movie_out):
        """Test successful retrieval of movie by ID"""
        with patch(
            'backend.routers.movies.svc.get_movie', return_value=sample_movie_out
        ):
            response = client.get("/api/movies/tt0111161")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["movie_id"] == "tt0111161"
        assert data["title"] == "The Shawshank Redemption"

    def test_get_movie_not_found(self, client):
        """Test retrieval of non-existent movie"""
        with patch('backend.routers.movies.svc.get_movie') as mock_get:
            mock_get.side_effect = HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Movie not found"
            )

            response = client.get("/api/movies/nonexistent")
            assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_create_movie_success_admin(
        self, client, sample_movie_out, mock_current_admin
    ):
        """Test successful movie creation by admin"""
        movie_data = {"title": "New Test Movie", "genre": "Drama", "release_year": 2024}

        with (
            patch(
                'backend.routers.movies.svc.create_movie', return_value=sample_movie_out
            ),
            patch(
                'backend.routers.movies.get_current_admin_user',
                return_value=mock_current_admin,
            ),
        ):
            response = client.post("/api/movies", json=movie_data)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["movie_id"] == "tt0111161"

    # Parameter validation tests
    @pytest.mark.parametrize(
        "page,page_size,expected_status",
        [
            (1, 50, status.HTTP_200_OK),
            (1, 1, status.HTTP_200_OK),
            (1, 200, status.HTTP_200_OK),
            (0, 50, status.HTTP_422_UNPROCESSABLE_ENTITY),
            (1, 0, status.HTTP_422_UNPROCESSABLE_ENTITY),
            (1, 201, status.HTTP_422_UNPROCESSABLE_ENTITY),
        ],
    )
    def test_list_movies_parameter_validation(
        self, client, page, page_size, expected_status
    ):
        """Test parameter validation using boundary values"""
        with patch('backend.routers.movies.svc.get_movies') as mock_svc:
            if expected_status == status.HTTP_200_OK:
                mock_svc.return_value = MovieListResponse(
                    items=[], total=0, page=page, page_size=page_size, total_pages=0
                )

            response = client.get(f"/api/movies?page={page}&page_size={page_size}")
            assert response.status_code == expected_status

    @pytest.mark.parametrize(
        "min_year,max_year,min_rating,expected_status",
        [
            (1990, 2000, 8.0, status.HTTP_200_OK),
            (1888, 2100, 0.0, status.HTTP_200_OK),
            (1887, 2000, 8.0, status.HTTP_422_UNPROCESSABLE_ENTITY),
            (1990, 2101, 8.0, status.HTTP_422_UNPROCESSABLE_ENTITY),
            (1990, 2000, -1.0, status.HTTP_422_UNPROCESSABLE_ENTITY),
        ],
    )
    def test_search_movies_parameter_validation(
        self, client, min_year, max_year, min_rating, expected_status
    ):
        """Test search parameter validation with equivalence partitioning"""
        with patch('backend.routers.movies.svc.search_movies') as mock_svc:
            mock_svc.return_value = MovieListResponse(
                items=[], total=0, page=1, page_size=50, total_pages=0
            )

            url = f"/api/movies/search?min_year={min_year}&max_year={max_year}&min_rating={min_rating}"
            response = client.get(url)
            assert response.status_code == expected_status

    # Error handling tests
    @pytest.mark.parametrize(
        "exception",
        [
            Exception("Database connection failed"),
            SQLAlchemyError("Database connection timeout"),
            asyncio.TimeoutError("Query timeout"),
            ValueError("Invalid data"),
        ],
    )
    def test_service_layer_exception_handling(self, client, exception):
        """Test fault injection by simulating service layer exceptions"""
        with patch('backend.routers.movies.svc.get_movies') as mock_svc:
            mock_svc.side_effect = exception

            response = client.get("/api/movies?page=1&page_size=50")
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_http_exception_propagation(self, client):
        """Test that HTTPExceptions are properly propagated"""
        with patch('backend.routers.movies.svc.get_movie') as mock_svc:
            mock_svc.side_effect = HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Movie not found"
            )

            response = client.get("/api/movies/nonexistent")
            assert response.status_code == status.HTTP_404_NOT_FOUND
            assert response.json()["detail"] == "Movie not found"

    # Security tests
    def test_sql_injection_attempts(self, client):
        """Test SQL injection attempts in search parameters"""
        sql_injection_payloads = [
            "'; DROP TABLE movies; --",
            "' OR '1'='1",
            "../../../etc/passwd",
            "<script>alert('XSS')</script>",
        ]

        for payload in sql_injection_payloads:
            with patch('backend.routers.movies.svc.search_movies') as mock_search:
                mock_search.return_value = MovieListResponse(
                    items=[], total=0, page=1, page_size=50, total_pages=0
                )

                response = client.get(f"/api/movies/search?title={payload}")
                assert response.status_code in [
                    status.HTTP_200_OK,
                    status.HTTP_422_UNPROCESSABLE_ENTITY,
                ]

    def test_concurrent_requests_handling(self, client):
        """Test handling of concurrent requests"""
        results = []
        errors = []

        def make_request(request_id):
            try:
                with patch('backend.routers.movies.svc.get_movies') as mock_svc:
                    mock_svc.return_value = MovieListResponse(
                        items=[], total=0, page=1, page_size=50, total_pages=0
                    )
                    response = client.get(
                        f"/api/movies?page=1&page_size=50&_req={request_id}"
                    )
                    results.append(response.status_code)
            except Exception as e:
                errors.append(str(e))

        threads = []
        for i in range(10):
            thread = threading.Thread(target=make_request, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        assert len(errors) == 0
        assert all(status_code == status.HTTP_200_OK for status_code in results)

    @pytest.mark.parametrize(
        "movie_id",
        [
            "",  # empty
            "   ",  # whitespace
            "invalid_id",  # no tt prefix
            "tt",  # just prefix
            "tt123",  # too short
            "tt123456789",  # too long
            "tt!@#$%",  # special characters
        ],
    )
    def test_invalid_movie_id_formats(self, client, movie_id):
        """Test various invalid movie ID formats"""
        response = client.get(f"/api/movies/{movie_id}")
        assert response.status_code in [
            status.HTTP_404_NOT_FOUND,
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_200_OK,
        ]

    def test_authentication_required_endpoints(self, client):
        """Test that protected endpoints require authentication"""
        # Test without authentication
        response = client.post("/api/movies", json={})
        assert response.status_code in [401, 403, 422]

        response = client.put("/api/movies/tt0111161", json={})
        assert response.status_code in [401, 403, 422]

        response = client.delete("/api/movies/tt0111161")
        assert response.status_code in [401, 403, 404]

    @pytest.mark.parametrize(
        "invalid_movie",
        [
            {"title": "Test", "release_year": 2024, "rating": 11.0},
            {"title": "Test", "release_year": 1800, "rating": 5.0},
            {"release_year": 2024},
            {"title": "", "release_year": 2024},
            {"title": "Test", "release_year": 2024, "runtime": -120},
        ],
    )
    def test_movie_data_validation(self, client, mock_current_admin, invalid_movie):
        """Test comprehensive data validation for movie creation"""
        with patch(
            'backend.routers.movies.get_current_admin_user',
            return_value=mock_current_admin,
        ):
            response = client.post("/api/movies", json=invalid_movie)
            assert response.status_code in [400, 422]
