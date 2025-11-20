"""
Unit tests for Movies Router.
Covers CRUD + search + pagination + auth behavior.
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


# ----- CRUD flow -----
@pytest.mark.usefixtures("admin_headers")
def test_full_movie_crud_flow(admin_headers):
    """Full admin CRUD lifecycle."""
    # Create (admin)
    r = client.post("/api/movies/", json={"title": "A Movie"}, headers=admin_headers)
    assert r.status_code == 201
    mid = r.json()["movie_id"]

    # Get
    r = client.get(f"/api/movies/{mid}")
    assert r.status_code == 200
    assert r.json()["title"] == "A Movie"

    # Update (admin)
    r = client.patch(f"/api/movies/{mid}", json={"rating": 9.0}, headers=admin_headers)
    assert r.status_code == 200
    assert r.json()["rating"] == 9.0

    # Delete (admin)
    r = client.delete(f"/api/movies/{mid}", headers=admin_headers)
    assert r.status_code == 204


# ----- Pagination & Search -----
def test_list_movies_pagination():
    """GET /api/movies basic pagination."""
    r = client.get("/api/movies?page=1&page_size=20")
    assert r.status_code == 200
    data = r.json()
    assert "items" in data
    assert "total_pages" in data


def test_search_movies_basic():
    """GET /api/movies/search query."""
    r = client.get("/api/movies/search?title=shawshank")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, dict)
    assert "items" in data


# ----- Popular & Recent -----
def test_popular_and_recent_movies():
    """GET /popular and /recent endpoints."""
    r1 = client.get("/api/movies/popular")
    r2 = client.get("/api/movies/recent")
    assert r1.status_code == 200
    assert r2.status_code == 200


# ----- Auth Protection -----
@pytest.mark.usefixtures("user_headers")
def test_non_admin_cannot_create_update_delete(user_headers):
    """Normal users forbidden from admin operations."""
    # create
    r = client.post("/api/movies/", json={"title": "Forbidden"}, headers=user_headers)
    assert r.status_code == 403

    # update
    r = client.patch("/api/movies/tt0001", json={"rating": 5}, headers=user_headers)
    assert r.status_code == 403

    # delete
    r = client.delete("/api/movies/tt0001", headers=user_headers)
    assert r.status_code == 403


# ----- Validation -----
@pytest.mark.usefixtures("admin_headers")
def test_create_invalid_data(admin_headers):
    """Invalid movie data triggers 422 or 400."""
    bad_payload = {"title": "   "}
    r = client.post("/api/movies/", json=bad_payload, headers=admin_headers)
    assert r.status_code in (400, 422)
