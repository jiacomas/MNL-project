# all mock fixture（mock_reviews_service, client, jwt_user_headers, jwt_admin_headers）
# come from backend/tests/conftest.py
from .conftest import now_iso


def test_list_reviews(client, mock_reviews_service):
    mock_reviews_service.list_reviews.return_value = (
        [
            {
                "id": "r1",
                "user_id": "u1",
                "movie_id": "m1",
                "rating": 5,
                "comment": None,
                "created_at": now_iso(),
                "updated_at": now_iso(),
            }
        ],
        123,
    )
    r = client.get("/api/movies/m1/reviews?limit=2")
    assert r.status_code == 200
    data = r.json()
    assert "items" in data
    assert "nextCursor" in data
    mock_reviews_service.list_reviews.assert_called_once_with("m1", 2, None, None)


def test_create_review(client, mock_reviews_service, jwt_user_headers):
    payload = {"movie_id": "m1", "rating": 9, "comment": "Loved it!"}
    mock_reviews_service.create_review.return_value = {
        "id": "r1",
        **payload,
        "user_id": "u1",
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }
    r = client.post("/api/movies/m1/reviews", json=payload, headers=jwt_user_headers)
    assert r.status_code in (200, 201)
    mock_reviews_service.create_review.assert_called_once_with(payload, "u1")


def test_update_review(client, mock_reviews_service, jwt_user_headers):
    payload = {"rating": 10}
    mock_reviews_service.update_review.return_value = {
        "id": "r1",
        "rating": 10,
        "user_id": "u1",
        "movie_id": "m1",
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }
    r = client.patch(
        "/api/movies/m1/reviews/r1", json=payload, headers=jwt_user_headers
    )
    assert r.status_code == 200
    mock_reviews_service.update_review.assert_called_once_with(
        "m1", "r1", "u1", payload
    )


def test_delete_review(client, mock_reviews_service, jwt_admin_headers):
    r = client.delete("/api/movies/m1/reviews/r1", headers=jwt_admin_headers)
    assert r.status_code in (200, 204)
    mock_reviews_service.delete_review.assert_called_once_with(
        "m1", "r1", "admin", is_admin=True
    )


def test_get_my_review(client, mock_reviews_service, jwt_user_headers):
    mock_reviews_service.get_review_by_user.return_value = {
        "id": "r1",
        "rating": 8,
        "user_id": "u1",
        "movie_id": "m1",
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }
    r = client.get("/api/movies/m1/reviews/me", headers=jwt_user_headers)
    assert r.status_code == 200
    mock_reviews_service.get_review_by_user.assert_called_once_with("m1", "u1")


def test_get_review_by_user(client, mock_reviews_service):
    mock_reviews_service.get_review_by_user.return_value = {
        "id": "r1",
        "movie_id": "m1",
        "rating": 8,
        "user_id": "u1",
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }
    r = client.get("/api/movies/m1/reviews/user/u1")
    assert r.status_code == 200
    mock_reviews_service.get_review_by_user.assert_called_once_with("m1", "u1")
