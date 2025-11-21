"""
Integration tests for Movies Router using mocker + JWT.
Ensures full endpoint flow without touching filesystem.
"""

from datetime import timedelta

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.schemas.movies import MovieOut
from backend.services import auth_service

client = TestClient(app)


@pytest.fixture(autouse=True)
def mock_repo_all(mocker):
    """Mock repository methods globally for all tests."""
    mock_repo = mocker.patch("backend.services.movies_service.movie_repo")

    sample = MovieOut(
        movie_id="m1",
        title="Mock Movie",
        genre="Drama",
        release_year=2000,
        rating=8.5,
        runtime=120,
        director="Director",
        cast="Cast",
        plot="A mock movie.",
        poster_url="url",
        created_at="2024-01-01T00:00:00Z",
        updated_at="2024-01-01T00:00:00Z",
        review_count=5,
    )

    # Common mock returns
    mock_repo.get_all.return_value = ([sample], 1)
    mock_repo.search.return_value = ([sample], 1)
    mock_repo.get_by_id.return_value = sample
    mock_repo.create.return_value = sample
    mock_repo.update.return_value = sample
    mock_repo.delete.return_value = True
    mock_repo.get_popular.return_value = [sample]
    mock_repo.get_recent.return_value = [sample]
    return mock_repo


# ----- Helper fixtures -----
@pytest.fixture
def admin_headers():
    """Generate a valid admin JWT header."""
    token = auth_service.create_access_token(
        {"sub": "admin1", "role": "admin", "username": "admin1"},
        expires_delta=timedelta(minutes=30),
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def user_headers():
    """Generate a normal user JWT header."""
    token = auth_service.create_access_token(
        {"sub": "u1", "role": "user", "username": "u1"},
        expires_delta=timedelta(minutes=30),
    )
    return {"Authorization": f"Bearer {token}"}


class TestMoviesRouterIntegration:
    # ---------- CRUD ----------
    def test_full_movie_crud_flow(self, admin_headers):
        r = client.post("/api/movies/", json={"title": "A"}, headers=admin_headers)
        assert r.status_code == 201
        mid = r.json()["movie_id"]

        r = client.get(f"/api/movies/{mid}", headers=admin_headers)
        assert r.status_code == 200

        r = client.patch(
            f"/api/movies/{mid}", json={"rating": 9.9}, headers=admin_headers
        )
        assert r.status_code == 200
        assert "rating" in r.json()

        r = client.delete(f"/api/movies/{mid}", headers=admin_headers)
        assert r.status_code == 204

    # ---------- Pagination & Sorting ----------
    def test_list_movies_pagination(self):
        r = client.get("/api/movies?page=1&page_size=10&sort_by=title&sort_desc=false")
        assert r.status_code == 200
        data = r.json()
        assert "items" in data
        assert "total_pages" in data

    # ---------- Search ----------
    def test_search_movies_basic(self):
        r = client.get("/api/movies/search?title=shawshank")
        assert r.status_code == 200
        assert "items" in r.json()

    # ---------- Popular & Recent ----------
    def test_popular_and_recent_movies(self):
        r1 = client.get("/api/movies/popular")
        r2 = client.get("/api/movies/recent")
        assert r1.status_code == 200
        assert r2.status_code == 200
        assert isinstance(r1.json(), list)
        assert isinstance(r2.json(), list)

    # ---------- Auth ----------
    def test_non_admin_cannot_create_update_delete(self, user_headers):
        for method, endpoint in [
            ("post", "/api/movies/"),
            ("patch", "/api/movies/m1"),
            ("delete", "/api/movies/m1"),
        ]:
            if method == "delete":
                r = getattr(client, method)(endpoint, headers=user_headers)
            else:
                r = getattr(client, method)(
                    endpoint, json={"title": "X"}, headers=user_headers
                )
            assert r.status_code == 403

    # ---------- Validation ----------
    def test_create_invalid_data(self, admin_headers):
        r = client.post("/api/movies/", json={"title": "   "}, headers=admin_headers)
        assert r.status_code in (400, 422)
