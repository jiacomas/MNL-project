"""
Performance and load testing for Movies Router.
Tests response times, performance benchmarks, and load handling.
"""
import pytest
import time
from unittest.mock import patch
from fastapi.testclient import TestClient
from fastapi import status

from backend.app.main import app
from backend.app.schemas.movies import MovieListResponse


class TestMoviesRouterPerformance:
    """Performance and load testing for movies router"""

    @pytest.fixture
    def client(self):
        """Create test client for FastAPI app"""
        return TestClient(app)

    # ========== PERFORMANCE & LOAD TESTING ==========

    def test_response_time_performance(self, client):
        """Test response time for critical endpoints"""
        endpoints = [
            "/api/movies?page=1&page_size=50",
            "/api/movies/search?title=test",
            "/api/movies/popular?limit=10",
            "/api/movies/recent?limit=10"
        ]

        max_response_time = 2.0  # 2 seconds maximum

        for endpoint in endpoints:
            with patch('backend.app.routers.movies.svc.get_movies') as mock_svc, \
                    patch('backend.app.routers.movies.svc.search_movies') as mock_search, \
                    patch('backend.app.routers.movies.svc.get_popular_movies') as mock_popular, \
                    patch('backend.app.routers.movies.svc.get_recent_movies') as mock_recent:
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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])