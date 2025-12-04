from datetime import datetime, timezone

from backend.schemas.reviews import ReviewOut


# helper: make ReviewOut
def make_review(
    review_id="rid1",
    movie_name="m1",
    username="u1",
    rating=8,
    title="T1",
    comment="C1",
):
    now = datetime.now(timezone.utc)
    return ReviewOut(
        review_id=review_id,
        movie_name=movie_name,
        username=username,
        rating=rating,
        title_review=title,
        comment=comment,
        created_at=now,
        updated_at=now,
        usefulness=0,
        total_votes=0,
    )


# POST /reviews/{movie_name}
def test_create_review(client, mock_reviews_service, jwt_user_headers):
    rv = make_review("new123")

    mock_reviews_service.create_review.return_value = rv

    payload = {
        "rating": 9,
        "title_review": "Good",
        "comment": "Nice!",
    }

    res = client.post(
        "/reviews/m1",
        json=payload,
        headers=jwt_user_headers,
    )

    assert res.status_code == 201
    assert res.json()["review_id"] == "new123"

    mock_reviews_service.create_review.assert_called_once()
    call = mock_reviews_service.create_review.call_args.kwargs
    assert call["movie_name"] == "m1"
    assert call["username"] == "u1"
    assert call["payload"].rating == 9
    assert call["payload"].title_review == "Good"
    assert call["payload"].comment == "Nice!"


# GET /reviews/{movie}/{id}
def test_get_review(client, mock_reviews_service):
    rv = make_review("r99")
    mock_reviews_service.get_review.return_value = rv

    res = client.get("/reviews/mA/r99")

    assert res.status_code == 200
    assert res.json()["review_id"] == "r99"

    mock_reviews_service.get_review.assert_called_once_with("mA", "r99")


# GET /reviews/{movie}?limit=&cursor=&min_rating=
def test_list_reviews(client, mock_reviews_service):
    rv1 = make_review("r1", rating=9)
    rv2 = make_review("r2", rating=8)

    mock_reviews_service.list_reviews.return_value = ([rv1, rv2], None)

    res = client.get("/reviews/m1?limit=10&cursor=0&min_rating=5")

    assert res.status_code == 200
    data = res.json()
    assert len(data["items"]) == 2
    assert data["items"][0]["review_id"] == "r1"

    mock_reviews_service.list_reviews.assert_called_once_with(
        movie_name="m1",
        limit=10,
        cursor=0,
        min_rating=5,
    )


# PUT /reviews/{movie}/{id}  (user updates own review)
def test_update_review_user(client, mock_reviews_service, jwt_user_headers):
    rv = make_review("r10", title="NewTitle")
    mock_reviews_service.update_review.return_value = rv

    payload = {"title_review": "NewTitle"}

    res = client.put(
        "/reviews/m1/r10",
        json=payload,
        headers=jwt_user_headers,
    )

    assert res.status_code == 200
    assert res.json()["review_id"] == "r10"

    call = mock_reviews_service.update_review.call_args.kwargs
    assert call["movie_name"] == "m1"
    assert call["review_id"] == "r10"
    assert call["username"] == "u1"
    assert call["is_admin"] is False
    assert call["payload"].title_review == "NewTitle"


# PUT /reviews/{movie}/{id}  (admin)
def test_update_review_admin(client, mock_reviews_service, jwt_admin_headers):
    rv = make_review("ra1", title="A")
    mock_reviews_service.update_review.return_value = rv

    payload = {"title_review": "A"}

    res = client.put(
        "/reviews/m2/ra1",
        json=payload,
        headers=jwt_admin_headers,
    )

    assert res.status_code == 200

    call = mock_reviews_service.update_review.call_args.kwargs
    assert call["is_admin"] is True


# DELETE /reviews/{movie}/{id}  (user owns it)
def test_delete_review_user(client, mock_reviews_service, jwt_user_headers):
    mock_reviews_service.delete_review.return_value = None

    res = client.delete(
        "/reviews/m1/r1",
        headers=jwt_user_headers,
    )

    assert res.status_code == 204

    call = mock_reviews_service.delete_review.call_args.kwargs
    assert call["movie_name"] == "m1"
    assert call["review_id"] == "r1"
    assert call["username"] == "u1"
    assert call["is_admin"] is False


# DELETE /reviews/{movie}/{id}  (admin)
def test_delete_review_admin(client, mock_reviews_service, jwt_admin_headers):
    mock_reviews_service.delete_review.return_value = None

    res = client.delete(
        "/reviews/m9/x777",
        headers=jwt_admin_headers,
    )

    assert res.status_code == 204

    call = mock_reviews_service.delete_review.call_args.kwargs
    assert call["is_admin"] is True
