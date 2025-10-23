# backend/app/test/test_reviews.py
import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI

from app.routers.reviews import router, get_service
from app.services.reviews_service import ReviewService, InMemoryReviewRepo

# ---- Build an app with injectable Service for tests ----
def test_pytest_smoke():
    assert True
    
def build_app_for_tests() -> FastAPI:
    app = FastAPI()
    # Prepare a single in-memory repo shared across requests in this test app
    shared_repo = InMemoryReviewRepo()
    svc = ReviewService(shared_repo)

    def override_service():
        return svc

    app.dependency_overrides[get_service] = override_service
    app.include_router(router)
    return app

@pytest.fixture(scope="function")
def client():
    app = build_app_for_tests()
    return TestClient(app)

def test_create_review(client):
    payload = {"user_id": "u1", "movie_id": "m1", "rating": 8, "comment": "Nice!"}
    r = client.post("/api/reviews", json=payload)
    assert r.status_code == 201
    data = r.json()
    assert data["user_id"] == "u1"
    assert data["movie_id"] == "m1"
    assert data["rating"] == 8
    assert "id" in data
    assert "created_at" in data and "updated_at" in data

def test_prevent_duplicate_review(client):
    payload = {"user_id": "u1", "movie_id": "m1", "rating": 7}
    r1 = client.post("/api/reviews", json=payload)
    assert r1.status_code == 201
    r2 = client.post("/api/reviews", json=payload)
    assert r2.status_code == 400
    assert "already reviewed" in r2.json()["detail"]

def test_edit_review_by_author_and_timestamp_changes(client):
    # create
    create = client.post("/api/reviews", json={"user_id": "u2", "movie_id": "m2", "rating": 5}).json()
    rid = create["id"]
    old_updated = create["updated_at"]
    # edit
    r = client.put(f"/api/reviews/{rid}?user_id=u2", json={"rating": 9})
    assert r.status_code == 200
    edited = r.json()
    assert edited["rating"] == 9
    assert edited["updated_at"] != old_updated  # timestamp should change

def test_edit_forbidden_for_non_author(client):
    created = client.post("/api/reviews", json={"user_id": "author", "movie_id": "m3", "rating": 6}).json()
    rid = created["id"]
    r = client.put(f"/api/reviews/{rid}?user_id=intruder", json={"rating": 10})
    assert r.status_code == 403

def test_delete_review_by_author(client):
    created = client.post("/api/reviews", json={"user_id": "u3", "movie_id": "m3", "rating": 9}).json()
    rid = created["id"]
    # delete as author
    r = client.delete(f"/api/reviews/{rid}?user_id=u3")
    assert r.status_code == 204
    # ensure not listed anymore
    r2 = client.get("/api/movies/m3/reviews")
    assert r2.status_code == 200
    assert all(x["id"] != rid for x in r2.json())

def test_delete_forbidden_for_non_author(client):
    created = client.post("/api/reviews", json={"user_id": "owner", "movie_id": "m4", "rating": 7}).json()
    rid = created["id"]
    r = client.delete(f"/api/reviews/{rid}?user_id=not_owner")
    assert r.status_code == 403

def test_list_and_get_user_review(client):
    client.post("/api/reviews", json={"user_id": "mike", "movie_id": "m5", "rating": 7})
    client.post("/api/reviews", json={"user_id": "sue", "movie_id": "m5", "rating": 8})
    # list movie reviews
    r = client.get("/api/movies/m5/reviews")
    assert r.status_code == 200
    arr = r.json()
    assert len(arr) == 2
    # get specific user review
    r2 = client.get("/api/movies/m5/reviews/mike")
    assert r2.status_code == 200
    assert r2.json()["rating"] == 7
