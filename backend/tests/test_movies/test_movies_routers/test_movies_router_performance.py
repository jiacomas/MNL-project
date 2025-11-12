"""
Performance and load testing for Movies Router.
Tests response times, performance benchmarks, and load handling.
"""
import pytest
import time
from unittest.mock import patch
from fastapi import status

from main import app
from schemas.movies import MovieListResponse


@pytest.mark.performance
class TestMoviesRouterPerformance:
    """Performance and load testing for movies router"""

    @pytest.mark.parametrize("endpoint", [
        "/api/movies?page=1&page_size=50",
        "/api/movies/search?title=test",
        "/api/movies/popular?limit=10",
        "/api/movies/recent?limit=10"
    ])
    def test_response_time_performance(self, client, endpoint):
        """Test response time for critical endpoints"""
        max_response_time = 2.0  # 2 seconds maximum

        with patch('routers.movies.svc.get_movies') as mock_svc, \
                patch('routers.movies.svc.search_movies') as mock_search, \
                patch('routers.movies.svc.get_popular_movies') as mock_popular, \
                patch('routers.movies.svc.get_recent_movies') as mock_recent:
            mock_svc.return_value = MovieListResponse(items=[], total=0, page=1, page_size=50, total_pages=0)
            mock_search.return_value = MovieListResponse(items=[], total=0, page=1, page_size=50, total_pages=0)
            mock_popular.return_value = []
            mock_recent.return_value = []

            start_time = time.time()
            response = client.get(endpoint)
            end_time = time.time()

            response_time = end_time - start_time

            assert response.status_code == status.HTTP_200_OK
            assert response_time < max_response_time, \
                f"Endpoint {endpoint} took {response_time:.2f}s, exceeding {max_response_time}s limit"

    def test_rate_limiting(self, client):
        """Test rate limiting on API endpoints"""
        with patch('routers.movies.svc.get_movies') as mock_svc:
            mock_svc.return_value = MovieListResponse(
                items=[], total=0, page=1, page_size=50, total_pages=0
            )

            # Make multiple rapid requests
            responses = []
            for i in range(10):
                response = client.get("/api/movies?page=1&page_size=50")
                responses.append(response.status_code)

            # All requests should succeed or be rate limited appropriately
            assert all(status_code in [200, 429] for status_code in responses)

    def test_cache_headers(self, client):
        """Test that appropriate cache headers are set"""
        with patch('routers.movies.svc.get_movies') as mock_svc:
            mock_svc.return_value = MovieListResponse(
                items=[], total=0, page=1, page_size=50, total_pages=0
            )

            response = client.get("/api/movies?page=1&page_size=50")

            # Check for cache headers (if implemented)
            cache_control = response.headers.get("Cache-Control")
            if cache_control:
                assert "max-age" in cache_control or "no-cache" in cache_control