"""
Integration-style unit tests for Movies Router (JWT version).
Covers CRUD + search + pagination + auth behavior.
"""

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


# ----- CRUD flow -----
def test_full_movie_crud_flow(jwt_admin_headers):
    """Full admin CRUD lifecycle."""
    # Create
    r = client.post(
        "/api/movies/", json={"title": "A Movie"}, headers=jwt_admin_headers
    )
    assert r.status_code == 201
    mid = r.json()["movie_id"]

    # Get
    r = client.get(f"/api/movies/{mid}", headers=jwt_admin_headers)
    assert r.status_code == 200
    assert r.json()["title"] == "A Movie"

    # Update
    r = client.patch(
        f"/api/movies/{mid}", json={"rating": 9.0}, headers=jwt_admin_headers
    )
    assert r.status_code == 200
    assert r.json()["rating"] == 9.0

    # Delete
    r = client.delete(f"/api/movies/{mid}", headers=jwt_admin_headers)
    assert r.status_code == 204


# ----- Pagination & Search -----
def test_list_movies_pagination():
    """GET /api/movies basic pagination."""
    r = client.get("/api/movies?page=1&page_size=20")
    assert r.status_code == 200
    data = r.json()
    assert "items" in data and "total_pages" in data


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
def test_non_admin_cannot_create_update_delete(jwt_user_headers):
    """Normal users forbidden from admin operations."""
    endpoints = [
        ("post", "/api/movies/", {"title": "Forbidden"}),
        ("patch", "/api/movies/tt0001", {"rating": 5}),
        ("delete", "/api/movies/tt0001", None),
    ]
    for method, url, payload in endpoints:
        if method == "delete":
            res = getattr(client, method)(url, headers=jwt_user_headers)
        else:
            res = getattr(client, method)(url, json=payload, headers=jwt_user_headers)
        assert res.status_code == 403


# ----- Validation -----
def test_create_invalid_data(jwt_admin_headers):
    """Invalid movie data triggers 422 or 400."""
    bad_payload = {"title": "   "}
    r = client.post("/api/movies/", json=bad_payload, headers=jwt_admin_headers)
    assert r.status_code in (400, 422)
