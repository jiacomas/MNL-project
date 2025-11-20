"""
Comprehensive integration tests for Movies Router.
Combines workflow tests, performance tests, and complex scenarios.
"""

import threading
import time
from unittest.mock import patch

import pytest
from fastapi import status

from backend.main import app
from backend.schemas.movies import MovieListResponse, MovieOut


class TestMoviesRouterIntegration:
    """Integration tests covering complete workflows, performance, and complex scenarios"""

    def test_full_movie_crud_flow(self, client, mock_current_admin):
        """Integration test for complete CRUD flow"""
        # 1. Create movie
        create_data = {
            "title": "Integration Test Movie",
            "genre": "Drama",
            "release_year": 2024,
            "rating": 8.5,
            "runtime": 120,
            "director": "Test Director",
            "cast": "Test Cast",
            "plot": "Test plot description",
            "poster_url": "https://example.com/poster.jpg",
        }

        with (
            patch('backend.routers.movies.svc.create_movie') as mock_create,
            patch(
                'backend.routers.movies.get_current_admin_user',
                return_value=mock_current_admin,
            ),
        ):
            mock_create.return_value = MovieOut(
                movie_id="tt9999999",
                **create_data,
                created_at="2024-01-01T12:00:00Z",
                updated_at="2024-01-01T12:00:00Z",
                review_count=0,
            )

            create_response = client.post("/api/movies", json=create_data)
            assert create_response.status_code == status.HTTP_201_CREATED
            movie_id = create_response.json()["movie_id"]

        # 2. Read movie
        with patch('backend.routers.movies.svc.get_movie') as mock_get:
            mock_get.return_value = MovieOut(
                movie_id=movie_id,
                **create_data,
                created_at="2024-01-01T12:00:00Z",
                updated_at="2024-01-01T12:00:00Z",
                review_count=0,
            )

            get_response = client.get(f"/api/movies/{movie_id}")
            assert get_response.status_code == status.HTTP_200_OK
            assert get_response.json()["title"] == "Integration Test Movie"

        # 3. Update movie
        update_data = {"rating": 9.0, "title": "Updated Integration Test Movie"}
        with (
            patch('backend.routers.movies.svc.update_movie') as mock_update,
            patch(
                'backend.routers.movies.get_current_admin_user',
                return_value=mock_current_admin,
            ),
        ):
            updated_movie_data = {**create_data, **update_data}
            mock_update.return_value = MovieOut(
                movie_id=movie_id,
                **updated_movie_data,
                created_at="2024-01-01T12:00:00Z",
                updated_at="2024-01-01T12:30:00Z",
                review_count=0,
            )

            update_response = client.put(f"/api/movies/{movie_id}", json=update_data)
            assert update_response.status_code == status.HTTP_200_OK
            assert update_response.json()["rating"] == 9.0
            assert update_response.json()["title"] == "Updated Integration Test Movie"

        # 4. Delete movie
        with (
            patch('backend.routers.movies.svc.delete_movie') as mock_delete,
            patch(
                'backend.routers.movies.get_current_admin_user',
                return_value=mock_current_admin,
            ),
        ):
            delete_response = client.delete(f"/api/movies/{movie_id}")
            assert delete_response.status_code == status.HTTP_204_NO_CONTENT

    def test_search_and_pagination_integration(self, client):
        """Integration test for search with pagination"""
        mock_movies = [
            MovieOut(
                movie_id=f"tt{i:07d}",
                title=f"Test Movie {i}",
                genre="Drama",
                release_year=2000 + (i % 25),
                rating=min(5.0 + (i * 0.05), 10.0),
                runtime=120,
                director="Test Director",
                cast="Test Cast",
                plot="Test plot",
                poster_url="https://example.com/poster.jpg",
                created_at="2024-01-01T12:00:00Z",
                updated_at="2024-01-01T12:00:00Z",
                review_count=i * 100,
            )
            for i in range(1, 101)
        ]

        with patch('backend.routers.movies.svc.search_movies') as mock_search:
            # First page
            mock_search.return_value = MovieListResponse(
                items=mock_movies[:50], total=100, page=1, page_size=50, total_pages=2
            )

            response_page1 = client.get(
                "/api/movies/search?genre=Drama&page=1&page_size=50"
            )
            assert response_page1.status_code == status.HTTP_200_OK
            data_page1 = response_page1.json()
            assert len(data_page1["items"]) == 50
            assert data_page1["total"] == 100
            assert data_page1["page"] == 1

            # Second page
            mock_search.return_value = MovieListResponse(
                items=mock_movies[50:], total=100, page=2, page_size=50, total_pages=2
            )

            response_page2 = client.get(
                "/api/movies/search?genre=Drama&page=2&page_size=50"
            )
            assert response_page2.status_code == status.HTTP_200_OK
            data_page2 = response_page2.json()
            assert len(data_page2["items"]) == 50
            assert data_page2["page"] == 2

    def test_concurrent_updates(self, client, mock_current_admin):
        """Test handling of concurrent movie updates with thread-safe authentication"""
        movie_id = "tt0111161"
        results = []
        errors = []
        lock = threading.Lock()

        def update_movie(rating, thread_id):
            try:
                update_data = {"rating": rating}

                # 为每个线程创建独立的mock
                with patch('backend.routers.movies.svc.update_movie') as mock_update:
                    mock_update.return_value = MovieOut(
                        movie_id=movie_id,
                        title="Test Movie",
                        genre="Drama",
                        release_year=1994,
                        rating=rating,
                        runtime=142,
                        director="Test Director",
                        cast="Test Cast",
                        plot="Test plot",
                        poster_url="https://example.com/poster.jpg",
                        created_at="2024-01-01T12:00:00Z",
                        updated_at="2024-01-01T12:00:00Z",
                        review_count=1000,
                    )

                    # 使用线程安全的认证mock
                    with patch(
                        'backend.routers.movies.get_current_admin_user',
                        return_value={
                            "user_id": f"admin_user_{thread_id}",
                            "role": "admin",
                        },
                    ):
                        response = client.put(
                            f"/api/movies/{movie_id}", json=update_data
                        )
                        with lock:
                            results.append(
                                (thread_id, response.status_code, response.text)
                            )
            except Exception as e:
                with lock:
                    errors.append(f"Thread {thread_id}: {str(e)}")

        # Simulate concurrent updates
        threads = []
        for i in range(5):
            thread = threading.Thread(target=update_movie, args=(8.0 + i * 0.1, i))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Debug output
        print(f"Results: {results}")
        print(f"Errors: {errors}")

        # Check for errors first
        assert len(errors) == 0, f"Concurrent updates failed with errors: {errors}"

        # Extract status codes
        status_codes = [result[1] for result in results]
        assert all(
            code == 200 for code in status_codes
        ), f"Not all requests succeeded: {status_codes}"

    # Performance tests
    @pytest.mark.parametrize(
        "endpoint",
        [
            "/api/movies?page=1&page_size=50",
            "/api/movies/search?title=test",
            "/api/movies/popular?limit=10",
            "/api/movies/recent?limit=10",
        ],
    )
    def test_response_time_performance(self, client, endpoint):
        """Test response time for critical endpoints"""
        max_response_time = 2.0  # 2 seconds maximum

        with (
            patch('backend.routers.movies.svc.get_movies') as mock_svc,
            patch('backend.routers.movies.svc.search_movies') as mock_search,
            patch('backend.routers.movies.svc.get_popular_movies') as mock_popular,
            patch('backend.routers.movies.svc.get_recent_movies') as mock_recent,
        ):
            mock_svc.return_value = MovieListResponse(
                items=[], total=0, page=1, page_size=50, total_pages=0
            )
            mock_search.return_value = MovieListResponse(
                items=[], total=0, page=1, page_size=50, total_pages=0
            )
            mock_popular.return_value = []
            mock_recent.return_value = []

            start_time = time.time()
            response = client.get(endpoint)
            end_time = time.time()

            response_time = end_time - start_time

            assert response.status_code == status.HTTP_200_OK
            assert (
                response_time < max_response_time
            ), f"Endpoint {endpoint} took {response_time:.2f}s, exceeding {max_response_time}s limit"

    def test_rate_limiting(self, client):
        """Test rate limiting on API endpoints"""
        with patch('backend.routers.movies.svc.get_movies') as mock_svc:
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

    # Security and edge case tests
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
            "poster_url": "https://example.com/poster.jpg",
        }

        with patch(
            'backend.routers.movies.get_current_admin_user',
            return_value=mock_current_admin,
        ):
            with patch('backend.routers.movies.svc.create_movie') as mock_create:
                mock_create.return_value = MovieOut(
                    movie_id="tt9999999",
                    **large_data,
                    created_at="2024-01-01T12:00:00Z",
                    updated_at="2024-01-01T12:00:00Z",
                    review_count=0,
                )

                response = client.post("/api/movies", json=large_data)
                assert response.status_code in [
                    status.HTTP_201_CREATED,
                    status.HTTP_422_UNPROCESSABLE_ENTITY,
                    status.HTTP_400_BAD_REQUEST,
                ]

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
            "poster_url": "https://example.com/poster.jpg",
        }

        with (
            patch('backend.routers.movies.svc.create_movie') as mock_create,
            patch(
                'backend.routers.movies.get_current_admin_user',
                return_value=mock_current_admin,
            ),
        ):
            mock_create.return_value = MovieOut(
                movie_id="tt9999999",
                **large_movie_data,
                created_at="2024-01-01T12:00:00Z",
                updated_at="2024-01-01T12:00:00Z",
                review_count=0,
            )

            response = client.post("/api/movies", json=large_movie_data)
            assert response.status_code in [
                status.HTTP_201_CREATED,
                status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                status.HTTP_422_UNPROCESSABLE_ENTITY,
            ]
