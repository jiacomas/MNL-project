"""
Security and data validation tests for Movies Router.
Tests security scenarios, data validation, and edge cases.
"""
import pytest
import threading
from unittest.mock import patch
from fastapi.testclient import TestClient
from fastapi import status

from backend.main import app
from backend.schemas.movies import MovieOut, MovieListResponse


class TestMoviesRouterSecurity:
    """Security and data validation tests for movies router"""

    @pytest.fixture
    def client(self):
        """Create test client for FastAPI app"""
        return TestClient(app)

    @pytest.fixture
    def mock_current_admin(self):
        """Mock admin user for authentication"""
        return {"user_id": "admin_user", "role": "admin"}

    # ========== SECURITY & DATA VALIDATION TESTS ==========

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

        with patch('backend.routers.movies.get_current_admin_user', return_value=mock_current_admin):
            with patch('backend.routers.movies.svc.create_movie') as mock_create:
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
            with patch('backend.routers.movies.svc.search_movies') as mock_search:
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
                with patch('backend.routers.movies.svc.get_movies') as mock_svc:
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

        with patch('backend.routers.movies.svc.create_movie') as mock_create, \
                patch('backend.routers.movies.get_current_admin_user', return_value=mock_current_admin):
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

    def test_invalid_movie_id_formats(self, client):
        """Test various invalid movie ID formats"""
        invalid_ids = [
            "",  # empty
            "   ",  # whitespace
            "invalid_id",  # no tt prefix
            "tt",  # just prefix
            "tt123",  # too short
            "tt123456789",  # too long
            "tt!@#$%",  # special characters
        ]

        for movie_id in invalid_ids:
            response = client.get(f"/api/movies/{movie_id}")
            assert response.status_code in [
                status.HTTP_404_NOT_FOUND,
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                status.HTTP_200_OK
            ], f"Unexpected status {response.status_code} for movie_id '{movie_id}'"

    def test_edge_case_search_parameters(self, client):
        """Test edge cases for search parameters"""
        edge_cases = [
            ("title", ""),  # empty title
            ("genre", "A" * 100),  # very long genre
            ("min_year", 1888),  # boundary min year
            ("max_year", 2100),  # boundary max year
            ("min_rating", 0.0),  # boundary min rating
            ("min_rating", 10.0),  # boundary max rating
        ]

        for param, value in edge_cases:
            with patch('backend.routers.movies.svc.search_movies') as mock_search:
                mock_search.return_value = MovieListResponse(
                    items=[],
                    total=0,
                    page=1,
                    page_size=50,
                    total_pages=0
                )

                response = client.get(f"/api/movies/search?{param}={value}")
                assert response.status_code in [status.HTTP_200_OK, status.HTTP_422_UNPROCESSABLE_ENTITY]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])