"""
Integration tests for Movies Router.
Tests complete workflows, data flow, and service integration.
"""
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from fastapi import status

from backend.main import app
from backend.schemas.movies import MovieOut, MovieListResponse


class TestMoviesRouterIntegration:
    """Integration tests for movies router endpoints"""

    @pytest.fixture
    def client(self):
        """Create test client for FastAPI app"""
        return TestClient(app)

    @pytest.fixture
    def mock_current_admin(self):
        """Mock admin user for authentication"""
        return {"user_id": "admin_user", "role": "admin"}

    # ========== INTEGRATION TESTS ==========

    @pytest.mark.integration
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
            "poster_url": "https://example.com/poster.jpg"
        }

        with patch('backend.routers.movies.svc.create_movie') as mock_create, \
                patch('backend.routers.movies.get_current_admin_user', return_value=mock_current_admin):
            mock_create.return_value = MovieOut(
                movie_id="tt9999999",
                **create_data,
                created_at="2024-01-01T12:00:00Z",
                updated_at="2024-01-01T12:00:00Z",
                review_count=0
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
                review_count=0
            )

            get_response = client.get(f"/api/movies/{movie_id}")
            assert get_response.status_code == status.HTTP_200_OK
            assert get_response.json()["title"] == "Integration Test Movie"

        # 3. Update movie
        update_data = {"rating": 9.0, "title": "Updated Integration Test Movie"}
        with patch('backend.routers.movies.svc.update_movie') as mock_update, \
                patch('backend.routers.movies.get_current_admin_user', return_value=mock_current_admin):
            updated_movie_data = {**create_data, **update_data}
            mock_update.return_value = MovieOut(
                movie_id=movie_id,
                **updated_movie_data,
                created_at="2024-01-01T12:00:00Z",
                updated_at="2024-01-01T12:30:00Z",
                review_count=0
            )

            update_response = client.put(f"/api/movies/{movie_id}", json=update_data)
            assert update_response.status_code == status.HTTP_200_OK
            assert update_response.json()["rating"] == 9.0
            assert update_response.json()["title"] == "Updated Integration Test Movie"

        # 4. Delete movie
        with patch('backend.routers.movies.svc.delete_movie') as mock_delete, \
                patch('backend.routers.movies.get_current_admin_user', return_value=mock_current_admin):
            delete_response = client.delete(f"/api/movies/{movie_id}")
            assert delete_response.status_code == status.HTTP_204_NO_CONTENT

    @pytest.mark.integration
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
                review_count=i * 100
            ) for i in range(1, 101)
        ]

        with patch('backend.routers.movies.svc.search_movies') as mock_search:
            # First page
            mock_search.return_value = MovieListResponse(
                items=mock_movies[:50],
                total=100,
                page=1,
                page_size=50,
                total_pages=2
            )

            response_page1 = client.get("/api/movies/search?genre=Drama&page=1&page_size=50")
            assert response_page1.status_code == status.HTTP_200_OK
            data_page1 = response_page1.json()
            assert len(data_page1["items"]) == 50
            assert data_page1["total"] == 100
            assert data_page1["page"] == 1

            # Second page
            mock_search.return_value = MovieListResponse(
                items=mock_movies[50:],
                total=100,
                page=2,
                page_size=50,
                total_pages=2
            )

            response_page2 = client.get("/api/movies/search?genre=Drama&page=2&page_size=50")
            assert response_page2.status_code == status.HTTP_200_OK
            data_page2 = response_page2.json()
            assert len(data_page2["items"]) == 50
            assert data_page2["page"] == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])