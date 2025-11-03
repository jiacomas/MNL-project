# test_reviews_router.py
import csv
import importlib
from typing import Any, Dict

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture()
def test_app(monkeypatch, tmp_path):
    data_dir = tmp_path / "data" / "movies"
    data_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("MOVIE_DATA_PATH", str(data_dir))

    from repositories import reviews_repo as repo_mod

    importlib.reload(repo_mod)
    from services import reviews_service as svc_mod

    importlib.reload(svc_mod)

    # Build app and include router
    from routers import reviews as reviews_router

    importlib.reload(reviews_router)

    app = FastAPI()
    app.include_router(reviews_router.router)

    # Override auth dependency
    def _fake_user():
        return "u_test"

    if hasattr(reviews_router, "get_current_user_id"):
        app.dependency_overrides[reviews_router.get_current_user_id] = _fake_user

    client = TestClient(app)
    return client, data_dir


def seed_movie(data_dir, movie_id, rows):
    mdir = data_dir / movie_id
    mdir.mkdir(parents=True, exist_ok=True)
    p = mdir / "movieReviews.csv"
    with p.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "Date of Review",
                "User",
                "Usefulness Vote",
                "Total Votes",
                "User's Rating out of 10",
                "Review Title",
                "id",
            ],
        )
        writer.writeheader()
        for r in rows:
            writer.writerow(r)


def _create_review_helper(
    client: TestClient, movie_id: str, rating: int = 9
) -> Dict[str, Any]:
    '''Helper to create a review and return its JSON body.'''
    payload = {
        "user_id": "u_test",
        "movie_id": movie_id,
        "rating": rating,
        "comment": "temporary for testing",
    }
    r = client.post("/api/reviews", json=payload)
    assert r.status_code == 201
    created = r.json()
    assert created["user_id"] == "u_test"
    return created


# Test cases
def test_review_listing_and_pagination(test_app):
    '''Tests fetching reviews, filtering, and pagination logic.'''
    client, data_dir = test_app
    movie_id = "Interstellar"

    # Seed 2 rows by other users
    seed_movie(
        data_dir,
        movie_id,
        [
            {
                "Date of Review": "07 November 2014",
                "User": "other1",
                "Usefulness Vote": "2",
                "Total Votes": "3",
                "User's Rating out of 10": "8",
                "Review Title": "great",
                "id": "",
            },
            {
                "Date of Review": "08 November 2014",
                "User": "other2",
                "Usefulness Vote": "1",
                "Total Votes": "2",
                "User's Rating out of 10": "6",
                "Review Title": "ok",
                "id": "",
            },
        ],
    )

    # List first page (limit=1)
    r = client.get(f"/api/reviews/movie/{movie_id}", params={"limit": 1})
    assert r.status_code == 200
    body = r.json()
    assert "items" in body and "nextCursor" in body
    assert len(body["items"]) == 1
    assert body["nextCursor"] == 1

    # Test second page
    r2 = client.get(
        f"/api/reviews/movie/{movie_id}",
        params={"limit": 1, "cursor": body["nextCursor"]},
    )
    assert r2.status_code == 200
    body2 = r2.json()
    assert len(body2["items"]) == 1
    assert body2["nextCursor"] is None
    assert body2["items"][0]["user_id"] == "other2"  # Check pagination order


def test_review_create_endpoint(test_app):
    '''Tests the POST /api/reviews endpoint for creation.'''
    client, data_dir = test_app
    movie_id = "Joker"

    payload = {
        "user_id": "u_test",
        "movie_id": movie_id,
        "rating": 9,
        "comment": "mind-blowing",
    }
    r = client.post("/api/reviews", json=payload)
    assert r.status_code == 201, r.text
    created = r.json()
    assert created["user_id"] == "u_test"
    assert created["rating"] == 9
    assert "id" in created


def test_review_update_and_get_own_authorized(test_app):
    '''Tests PATCH update and GET by user (read) authorization flow.'''
    client, data_dir = test_app
    movie_id = "Joker"

    created = _create_review_helper(client, movie_id, rating=9)
    review_id = created["id"]

    # Update
    r = client.patch(f"/api/reviews/movie/{movie_id}/{review_id}", json={"rating": 10})
    assert r.status_code == 200
    assert r.json()["rating"] == 10

    # Get my review
    r = client.get(f"/api/reviews/movie/{movie_id}/me")
    assert r.status_code == 200
    mine = r.json()
    assert mine is not None and mine["id"] == review_id
    assert mine["rating"] == 10


def test_review_delete_authorized(test_app):
    client, data_dir = test_app
    movie_id = "Dune"

    created = _create_review_helper(client, movie_id, rating=8)
    review_id = created["id"]

    # Check that it exists before deletion
    r_check_before = client.get(f"/api/reviews/movie/{movie_id}/user/u_test")
    assert r_check_before.status_code == 200
    assert r_check_before.json() is not None

    # Delete (authorized)
    r = client.delete(f"/api/reviews/movie/{movie_id}/{review_id}")
    assert r.status_code == 204

    # After delete, my review disappears
    r_check_after = client.get(f"/api/reviews/movie/{movie_id}/user/u_test")
    assert r_check_after.status_code == 200
    assert r_check_after.json() is None

    # Check overall list to ensure total count decreased
    r_list = client.get(f"/api/reviews/movie/{movie_id}", params={"limit": 50})
    assert r_list.status_code == 200
    all_items = r_list.json()["items"]
    assert all(it["id"] != review_id for it in all_items)
