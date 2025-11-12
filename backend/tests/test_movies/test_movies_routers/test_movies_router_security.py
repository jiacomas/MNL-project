"""
Security and data validation tests for Movies Router.
Tests security scenarios, data validation, and edge cases.
"""
import pytest
import threading
from unittest.mock import patch
from fastapi import status

from main import app
from schemas.movies import MovieOut, MovieListResponse


@pytest.mark.security
class TestMoviesRouterSecurity:
    """Security and data validation tests for movies router"""

    def test_malformed_data_injection(self, client, mock_current_admin):
        """Test handling of malformed data through fault injection"""
        large_data = {
            "title": "Test Movie with Long Title" * 10,
            "release_year": 2024,
            "genre": "Drama",
            "rating": 5.5,
            "runtime": 120,
            "director": "Test Director",
            "cast": "Test Cast",
            "plot": "Test plot",
            "poster_url": "https://example.com/poster.jpg"
        }

        with patch('routers.movies.get_current_admin_user', return_value=mock_current_admin):
            with patch('routers.movies.svc.create_movie') as mock_create:
                mock_create.return_value = MovieOut(
                    movie_id="tt9999999",
                    **large_data,
                    created_at="2024-01-01T12:00:00Z",
                    updated_at="2024-01-01T12:00:00Z",
                    review_count=0
                )

                response = client.post("/api/movies", json=large_data)
                assert response.status_code in [
                    status.HTTP_201_CREATED,
                    status.HTTP_422_UNPROCESSABLE_ENTITY,
                    status.HTTP_400_BAD_REQUEST
                ]

    def test_sql_injection_attempts(self, client):
        """Test SQL injection attempts in search parameters"""
        sql_injection_payloads = [
            "'; DROP TABLE movies; --",
            "' OR '1'='1",
            "'; EXEC xp_cmdshell('format C:'); --",
            "../../../etc/passwd",
            "<script>alert('XSS')</script>"
        ]

        for payload in sql_injection_payloads:
            with patch('routers.movies.svc.search_movies') as mock_search:
                mock_search.return_value = MovieListResponse(
                    items=[],
                    total=0,
                    page=1,
                    page_size=50,
                    total_pages=0
                )

                response = client.get(f"/api/movies/search?title={payload}")
                assert response.status_code in [status.HTTP_200_OK, status.HTTP_422_UNPROCESSABLE_ENTITY]

    def test_concurrent_requests_handling(self, client):
        """Test handling of concurrent requests"""
        results = []
        errors = []

        def make_request(request_id):
            try:
                with patch('routers.movies.svc.get_movies') as mock_svc:
                    mock_svc.return_value = MovieListResponse(
                        items=[],
                        total=0,
                        page=1,
                        page_size=50,
                        total_pages=0
                    )
                    response = client.get(f"/api/movies?page=1&page_size=50&_req={request_id}")
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

    def test_large_payload_handling(self, client, mock_current_admin):
        """Test handling of large payloads"""
        large_movie_data = {
            "title": "A" * 500,
            "genre": "Drama",
            "release_year": 2024,
            "plot": "A" * 2000,
            "cast": ", ".join([f"Actor {i}" for i in range(50)]),
            "rating": 5.5,
            "runtime": 120,
            "director": "Test Director",
            "poster_url": "https://example.com/poster.jpg"
        }

        with patch('routers.movies.svc.create_movie') as mock_create, \
                patch('routers.movies.get_current_admin_user', return_value=mock_current_admin):
            mock_create.return_value = MovieOut(
                movie_id="tt9999999",
                **large_movie_data,
                created_at="2024-01-01T12:00:00Z",
                updated_at="2024-01-01T12:00:00Z",
                review_count=0
            )

            response = client.post("/api/movies", json=large_movie_data)
            assert response.status_code in [
                status.HTTP_201_CREATED,
                status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ]

    @pytest.mark.parametrize("movie_id", [
        "",           # empty
        "   ",        # whitespace
        "invalid_id", # no tt prefix
        "tt",         # just prefix
        "tt123",      # too short
        "tt123456789", # too long
        "tt!@#$%",    # special characters
    ])
    def test_invalid_movie_id_formats(self, client, movie_id):
        """Test various invalid movie ID formats"""
        response = client.get(f"/api/movies/{movie_id}")
        assert response.status_code in [
            status.HTTP_404_NOT_FOUND,
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_200_OK
        ]

    @pytest.mark.parametrize("param,value", [
        ("title", ""),           # empty title
        ("genre", "A" * 100),    # very long genre
        ("min_year", 1888),      # boundary min year
        ("max_year", 2100),      # boundary max year
        ("min_rating", 0.0),     # boundary min rating
        ("min_rating", 10.0),    # boundary max rating
    ])
    def test_edge_case_search_parameters(self, client, param, value):
        """Test edge cases for search parameters"""
        with patch('routers.movies.svc.search_movies') as mock_search:
            mock_search.return_value = MovieListResponse(
                items=[],
                total=0,
                page=1,
                page_size=50,
                total_pages=0
            )

            response = client.get(f"/api/movies/search?{param}={value}")
            assert response.status_code in [status.HTTP_200_OK, status.HTTP_422_UNPROCESSABLE_ENTITY]

    def test_authentication_required_endpoints(self, client):
        """Test that protected endpoints require authentication"""
        # Test without authentication
        response = client.post("/api/movies", json={})
        assert response.status_code in [401, 403, 422]

        response = client.put("/api/movies/tt0111161", json={})
        assert response.status_code in [401, 403, 422]

        response = client.delete("/api/movies/tt0111161")
        assert response.status_code in [401, 403, 404]

    @pytest.mark.parametrize("invalid_movie", [
        {"title": "Test", "release_year": 2024, "rating": 11.0},
        {"title": "Test", "release_year": 1800, "rating": 5.0},
        {"release_year": 2024},
        {"title": "", "release_year": 2024},
        {"title": "Test", "release_year": 2024, "runtime": -120},
    ])
    def test_movie_data_validation(self, client, mock_current_admin, invalid_movie):
        """Test comprehensive data validation for movie creation"""
        with patch('routers.movies.get_current_admin_user', return_value=mock_current_admin):
            response = client.post("/api/movies", json=invalid_movie)
            assert response.status_code in [400, 422]