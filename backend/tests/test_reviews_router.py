# test_reviews_router.py
import os
import importlib
import csv

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture()
def test_app(monkeypatch, tmp_path):
    data_dir = tmp_path / "data" / "movies"
    data_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("MOVIE_DATA_PATH", str(data_dir))

    from app.repositories import reviews_repo as repo_mod
    importlib.reload(repo_mod)
    from app.services import reviews_service as svc_mod
    importlib.reload(svc_mod)

    # Build app and include router
    from app.routers import reviews as reviews_router
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
        writer = csv.DictWriter(f, fieldnames=[
            "Date of Review", "User", "Usefulness Vote", "Total Votes",
            "User's Rating out of 10", "Review Title", "id"
        ])
        writer.writeheader()
        for r in rows:
            writer.writerow(r)


def test_router_crud_and_pagination(test_app):
    client, data_dir = test_app
    movie_id = "Interstellar"

    # Seed 2 rows by other users
    seed_movie(data_dir, movie_id, [
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
    ])

    # List first page (limit=1)
    r = client.get(f"/api/reviews/movie/{movie_id}", params={"limit": 1})
    assert r.status_code == 200
    body = r.json()
    assert "items" in body and "nextCursor" in body
    assert len(body["items"]) == 1
    assert body["nextCursor"] == 1

    # Create my own review (user is overridden to u_test only on protected ops;
    # here POST accepts payload.user_id by design, so we pass u_test)
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

    # Delete (authorized)
    r = client.delete(f"/api/reviews/movie/{movie_id}/{review_id}")
    assert r.status_code == 204

    # After delete, my review disappears
    r = client.get(f"/api/reviews/movie/{movie_id}", params={"limit": 50})
    assert r.status_code == 200
    all_items = r.json()["items"]
    assert all(it["id"] != review_id for it in all_items)
