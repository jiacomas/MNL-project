"""
Integration-style unit tests for Movies Router (JWT version).
Covers CRUD + search + pagination + auth behavior.
"""

from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


# ----- CRUD flow -----
def test_full_movie_crud_flow(jwt_admin_headers):
    """Full admin CRUD lifecycle."""
    # Create
    payload = {
        "title": "A Movie",
        "movieGenres": "Action",
        "directors": "Test Director",
        "datePublished": "2024-01-01",
        "creators": "Test Creator",
        "mainStars": "Actor One",
        "description": "A test movie",
        "duration": 120,
    }
    r = client.post("/api/movies/", json=payload, headers=jwt_admin_headers)
    assert r.status_code == 201
    mid = r.json()["movie_id"]

    # Get
    r = client.get(f"/api/movies/{mid}", headers=jwt_admin_headers)
    assert r.status_code == 200
    assert r.json()["title"] == "A Movie"

    # Update - use allowed field
    r = client.patch(
        f"/api/movies/{mid}", json={"title": "Updated Movie"}, headers=jwt_admin_headers
    )
    assert r.status_code == 200
    assert r.json().get("title") == "Updated Movie"

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


def test_search_movies_with_sorting():
    r = client.get("/api/movies/search?title=shawshank&sort_by=rating&sort_desc=true")
    assert r.status_code == 200
    data = r.json()
    assert "items" in data
    assert isinstance(data["items"], list)


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
    valid_payload = {
        "title": "Forbidden",
        "movieGenres": "Action",
        "directors": "Director",
        "datePublished": "2024-01-01",
        "creators": "Creator",
        "mainStars": "Actor",
        "description": "Description",
        "duration": 120,
    }
    endpoints = [
        ("post", "/api/movies/", valid_payload),
        ("patch", "/api/movies/tt0001", {"title": "Updated"}),
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


def test_search_enhancements_mocked():
    """
    Test enhanced search functionality (release_year, partial genre, case-insensitive)
    using mocked data to avoid touching real files.
    """
    mock_movies = [
        {
            "movie_id": "m1",
            "title": "The Matrix",
            "movieGenres": "Action, Sci-Fi",
            "datePublished": "1999-03-31",
            "description": "Red pill",
            "duration": 136,
            "movieIMDbRating": 8.7,
        },
        {
            "movie_id": "m2",
            "title": "Matrix Reloaded",
            "movieGenres": "Action|Sci-Fi|Thriller",
            "datePublished": "2003-05-15",
            "description": "More agents",
            "duration": 138,
            "movieIMDbRating": 7.2,
        },
        {
            "movie_id": "m3",
            "title": "Inception",
            "movieGenres": "Action, Adventure, Sci-Fi",
            "datePublished": "2010-07-16",
            "description": "Dreams",
            "duration": 148,
            "movieIMDbRating": 8.8,
        },
    ]

    # Patch the _load_movies method of the MovieRepository class
    # This ensures that when the service calls repo.search(), it uses our mock data
    # but still executes the actual search logic (filtering, sorting, etc.)
    with patch(
        "backend.repositories.movies_repo.MovieRepository._load_movies",
        return_value=mock_movies,
    ):

        # 1. Release Year Search (1999 -> The Matrix)
        r = client.get("/api/movies/search?release_year=1999")
        assert r.status_code == 200
        data = r.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["title"] == "The Matrix"

        # 2. Case-Insensitive Title (matrix -> The Matrix, Matrix Reloaded)
        r = client.get("/api/movies/search?title=matrix")
        assert r.status_code == 200
        data = r.json()
        assert len(data["items"]) == 2

        # 3. Partial Genre Matching (sci-fi -> all 3 movies)
        r = client.get("/api/movies/search?genre=sci-fi")
        assert r.status_code == 200
        data = r.json()
        assert len(data["items"]) == 3

        # 4. Combined Filters (Action + 1999 -> The Matrix)
        r = client.get("/api/movies/search?genre=action&release_year=1999")
        assert r.status_code == 200
        data = r.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["title"] == "The Matrix"


def test_movie_analytics_endpoint_basic():
    """GET /api/movies/analytics returns structured analytics payload."""
    r = client.get("/api/movies/analytics")
    assert r.status_code == 200
    data = r.json()
    # Basic shape checks – exact numbers depend on underlying data
    assert "total_movies" in data
    assert "filtered_movies" in data
    assert "rating_buckets" in data
    assert "releases_by_year" in data
    assert "genres" in data
    assert "top_directors" in data
