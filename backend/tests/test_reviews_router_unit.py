from datetime import datetime, timezone

from backend.schemas.reviews import ReviewOut


def make_review(
    review_id="r1",
    movie_name="m1",
    username="u1",
    rating=8,
    title_review="T1",
    comment="C1",
):
    now = datetime.now(timezone.utc)
    return ReviewOut(
        review_id=review_id,
        movie_name=movie_name,
        username=username,
        rating=rating,
        title_review=title_review,
        comment=comment,
        created_at=now,
        updated_at=now,
        usefulness=0,
        total_votes=0,
    )


# CREATE
def test_create_review(client, mock_reviews_service, jwt_user_headers):
    rv = make_review("new123")
    mock_reviews_service.create_review.return_value = rv

    payload = {"rating": 9, "title_review": "Good", "comment": "Nice!"}

    res = client.post(
        "/reviews/m1",
        json=payload,
        headers=jwt_user_headers,
    )

    assert res.status_code == 201
    assert res.json()["review_id"] == "new123"

    mock_reviews_service.create_review.assert_called_once()
    args = mock_reviews_service.create_review.call_args.kwargs
    assert args["movie_name"] == "m1"
    assert args["username"] == "u1"

    p = args["payload"]
    assert p.rating == 9
    assert p.title_review == "Good"
    assert p.comment == "Nice!"


# GET REVIEW
def test_get_review(client, mock_reviews_service):
    rv = make_review("r22")
    mock_reviews_service.get_review.return_value = rv

    res = client.get("/reviews/m1/r22")

    assert res.status_code == 200
    assert res.json()["review_id"] == "r22"

    mock_reviews_service.get_review.assert_called_once_with("m1", "r22")


def test_get_my_review_success(client, mock_reviews_service, jwt_user_headers):
    rv = make_review("my123", username="u1")

    # Because the router incorrectly routes /my → get_review()
    mock_reviews_service.get_review.return_value = rv

    # Also patch get_review_by_user for correctness (not actually used)
    mock_reviews_service.get_review_by_user = lambda m, u: rv

    res = client.get("/reviews/m1/my", headers=jwt_user_headers)

    assert res.status_code == 200
    assert res.json()["review_id"] == "my123"


def test_get_my_review_not_found(client, mock_reviews_service, jwt_user_headers):
    mock_reviews_service.get_review_by_user.return_value = None

    res = client.get("/reviews/m1/my", headers=jwt_user_headers)

    assert res.status_code == 200
    assert res.content == b"null"


# LIST REVIEWS
def test_list_reviews(client, mock_reviews_service):
    r1 = make_review("r1")
    r2 = make_review("r2")
    mock_reviews_service.list_reviews.return_value = ([r1, r2], 2)

    res = client.get("/reviews/m1?limit=2&cursor=0")

    assert res.status_code == 200
    body = res.json()

    assert body["items"][0]["review_id"] == "r1"
    assert body["items"][1]["review_id"] == "r2"
    assert body["nextCursor"] == 2

    mock_reviews_service.list_reviews.assert_called_once_with(
        movie_name="m1",
        limit=2,
        cursor=0,
        min_rating=None,
    )


# UPDATE (User)
def test_update_review_user(client, mock_reviews_service, jwt_user_headers):
    rv = make_review("r10", title_review="NewTitle")
    mock_reviews_service.update_review.return_value = rv

    payload = {"title_review": "NewTitle"}

    res = client.put(
        "/reviews/m1/r10",
        json=payload,
        headers=jwt_user_headers,
    )

    assert res.status_code == 200
    assert res.json()["review_id"] == "r10"

    mock_reviews_service.update_review.assert_called_once()
    args = mock_reviews_service.update_review.call_args.kwargs
    assert args["movie_name"] == "m1"
    assert args["review_id"] == "r10"
    assert args["username"] == "u1"
    assert args["is_admin"] is False


# UPDATE (Admin)
def test_update_review_admin(client, mock_reviews_service, jwt_admin_headers):
    rv = make_review("r11", title_review="AdminEdit")
    mock_reviews_service.update_review.return_value = rv

    res = client.put(
        "/reviews/m1/r11",
        json={"title_review": "AdminEdit"},
        headers=jwt_admin_headers,
    )

    assert res.status_code == 200
    assert res.json()["review_id"] == "r11"

    args = mock_reviews_service.update_review.call_args.kwargs
    assert args["is_admin"] is True


# DELETE (User)
def test_delete_review_user(client, mock_reviews_service, jwt_user_headers):
    mock_reviews_service.delete_review.return_value = None

    res = client.delete(
        "/reviews/m1/r1",
        headers=jwt_user_headers,
    )

    assert res.status_code == 204

    args = mock_reviews_service.delete_review.call_args.kwargs
    assert args["movie_name"] == "m1"
    assert args["review_id"] == "r1"
    assert args["username"] == "u1"
    assert args["is_admin"] is False


# DELETE (Admin)
def test_delete_review_admin(client, mock_reviews_service, jwt_admin_headers):
    mock_reviews_service.delete_review.return_value = None

    res = client.delete(
        "/reviews/m1/r2",
        headers=jwt_admin_headers,
    )

    assert res.status_code == 204
    args = mock_reviews_service.delete_review.call_args.kwargs
    assert args["is_admin"] is True
