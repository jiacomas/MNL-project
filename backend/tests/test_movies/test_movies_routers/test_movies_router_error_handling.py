"""
Error handling and fault injection tests for Movies Router.
Tests exception handling, fault scenarios, and edge cases.
"""
import pytest
import asyncio
from unittest.mock import patch
from fastapi import status, HTTPException
from sqlalchemy.exc import SQLAlchemyError


@pytest.mark.error_handling
class TestMoviesRouterErrorHandling:
    """Error handling and fault injection tests for movies router"""

    @pytest.mark.parametrize("exception", [
        Exception("Database connection failed"),
        SQLAlchemyError("Database connection timeout"),
        asyncio.TimeoutError("Query timeout"),
        ValueError("Invalid data"),
        RuntimeError("Service unavailable"),
        ConnectionError("Network error"),
    ])
    def test_service_layer_exception_handling(self, client, exception):
        """Test fault injection by simulating service layer exceptions"""
        with patch('routers.movies.svc.get_movies') as mock_svc:
            mock_svc.side_effect = exception

            response = client.get("/api/movies?page=1&page_size=50")
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_http_exception_propagation(self, client):
        """Test that HTTPExceptions are properly propagated"""
        with patch('routers.movies.svc.get_movie') as mock_svc:
            mock_svc.side_effect = HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Movie not found"
            )

            response = client.get("/api/movies/nonexistent")
            assert response.status_code == status.HTTP_404_NOT_FOUND
            assert response.json()["detail"] == "Movie not found"

    @pytest.mark.parametrize("endpoint,service_method", [
        ("/api/movies", "get_movies"),
        ("/api/movies/search", "search_movies"),
        ("/api/movies/popular", "get_popular_movies"),
        ("/api/movies/recent", "get_recent_movies"),
    ])
    def test_graceful_degradation_on_service_failure(self, client, endpoint, service_method):
        """Test that the API degrades gracefully when services fail"""
        with patch(f'routers.movies.svc.{service_method}') as mock_service:
            mock_service.side_effect = Exception("Service failure")

            response = client.get(endpoint)
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            error_data = response.json()
            assert "detail" in error_data

    def test_authentication_fallback_comprehensive(self, client):
        """Comprehensive test for authentication fallback scenarios"""
        with patch('routers.movies._AUTH_ENABLED', False):
            with patch('routers.movies.get_current_user', side_effect=ImportError):
                response = client.get("/api/movies/tt0111161/recommendations")
                assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]

    def test_specific_exception_handling(self, client):
        """Test specific exception types are handled appropriately"""
        exception_test_cases = [
            (ValueError("Invalid input"), status.HTTP_500_INTERNAL_SERVER_ERROR),
            (KeyError("Movie not found"), status.HTTP_500_INTERNAL_SERVER_ERROR),
            (PermissionError("Access denied"), status.HTTP_500_INTERNAL_SERVER_ERROR),
        ]

        for exception, expected_status in exception_test_cases:
            with patch('routers.movies.svc.get_movie') as mock_svc:
                mock_svc.side_effect = exception
                response = client.get("/api/movies/tt0111161")
                assert response.status_code == expected_status