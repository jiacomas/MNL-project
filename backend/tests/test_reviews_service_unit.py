from datetime import datetime, timezone

import pytest
from fastapi import HTTPException

from backend.repositories.reviews_repo import CSVReviewRepo
from backend.schemas.reviews import ReviewCreate, ReviewOut, ReviewUpdate
from backend.services.reviews_service import ReviewsService


# Helper
def make_review(
    review_id="r1",
    movie="m1",
    username="u1",
    rating=8,
    title="T1",
    comment="C1",
    usefulness=0,
    total_votes=0,
):
    now = datetime.now(timezone.utc)
    return ReviewOut(
        review_id=review_id,
        movie_name=movie,
        username=username,
        rating=rating,
        title_review=title,
        comment=comment,
        created_at=now,
        updated_at=now,
        usefulness=usefulness,
        total_votes=total_votes,
    )


# CREATE
def test_create_review_success(mocker):
    repo = mocker.Mock(spec=CSVReviewRepo)
    svc = ReviewsService(repo)

    mocker.patch.object(repo, "get_review_by_user", return_value=None)
    mocker.patch.object(repo, "create", side_effect=lambda r: r)

    payload = ReviewCreate(rating=9, title_review="Good", comment="Nice")

    result = svc.create_review("m1", payload, username="u1")

    assert result.username == "u1"
    assert result.rating == 9
    assert result.title_review == "Good"
    repo.create.assert_called_once()


def test_create_review_conflict(mocker):
    repo = mocker.Mock(spec=CSVReviewRepo)
    svc = ReviewsService(repo)

    repo.get_review_by_user.return_value = make_review()

    payload = ReviewCreate(rating=8, title_review="Hi")

    with pytest.raises(HTTPException) as exc:
        svc.create_review("m1", payload, "u1")

    assert exc.value.status_code == 409


# GET
def test_get_review_success(mocker):
    repo = mocker.Mock(spec=CSVReviewRepo)
    svc = ReviewsService(repo)

    rv = make_review(review_id="r9")
    repo.get_review_by_id.return_value = rv

    out = svc.get_review("m1", "r9")
    assert out.review_id == "r9"


def test_get_review_404(mocker):
    repo = mocker.Mock(spec=CSVReviewRepo)
    svc = ReviewsService(repo)

    repo.get_review_by_id.return_value = None

    with pytest.raises(HTTPException) as exc:
        svc.get_review("m1", "missing")

    assert exc.value.status_code == 404


# GET BY USER
def test_get_review_by_user_success(mocker):
    repo = mocker.Mock(spec=CSVReviewRepo)
    svc = ReviewsService(repo)

    rv = make_review(review_id="u-review", username="alice")
    repo.get_review_by_user.return_value = rv

    out = svc.get_review_by_user("m1", "alice")

    assert out.review_id == "u-review"
    assert out.username == "alice"
    repo.get_review_by_user.assert_called_once_with("m1", "alice")


def test_get_review_by_user_not_found(mocker):
    repo = mocker.Mock(spec=CSVReviewRepo)
    svc = ReviewsService(repo)

    repo.get_review_by_user.return_value = None

    out = svc.get_review_by_user("m1", "nobody")

    assert out is None
    repo.get_review_by_user.assert_called_once_with("m1", "nobody")


# UPDATE
def test_update_review_success_user(mocker):
    repo = mocker.Mock(spec=CSVReviewRepo)
    svc = ReviewsService(repo)

    existing = make_review(review_id="r1", username="u1", title="Old", comment="OldC")
    repo.get_review_by_id.return_value = existing
    repo.update.side_effect = lambda r: r

    payload = ReviewUpdate(title_review="New", comment="NewC", rating=10)

    out = svc.update_review("m1", "r1", payload, username="u1", is_admin=False)

    assert out.title_review == "New"
    assert out.comment == "NewC"
    assert out.rating == 10
    repo.update.assert_called_once()


def test_update_review_forbidden_nonowner(mocker):
    repo = mocker.Mock(spec=CSVReviewRepo)
    svc = ReviewsService(repo)

    existing = make_review(username="owner")
    repo.get_review_by_id.return_value = existing

    payload = ReviewUpdate(comment="Hi")

    with pytest.raises(HTTPException) as exc:
        svc.update_review("m1", "r1", payload, username="other", is_admin=False)

    assert exc.value.status_code == 403


def test_update_review_admin_allowed(mocker):
    repo = mocker.Mock(spec=CSVReviewRepo)
    svc = ReviewsService(repo)

    existing = make_review(username="u1")
    repo.get_review_by_id.return_value = existing
    repo.update.side_effect = lambda r: r

    payload = ReviewUpdate(rating=5)

    out = svc.update_review("m1", "r1", payload, username="adminUser", is_admin=True)

    assert out.rating == 5
    repo.update.assert_called_once()


# DELETE
def test_delete_review_success_user(mocker):
    repo = mocker.Mock(spec=CSVReviewRepo)
    svc = ReviewsService(repo)

    existing = make_review(username="u1")
    repo.get_review_by_id.return_value = existing

    svc.delete_review("m1", "r1", username="u1", is_admin=False)
    repo.delete.assert_called_once()


def test_delete_review_forbidden(mocker):
    repo = mocker.Mock(spec=CSVReviewRepo)
    svc = ReviewsService(repo)

    repo.get_review_by_id.return_value = make_review(username="owner")

    with pytest.raises(HTTPException) as exc:
        svc.delete_review("m1", "r1", username="other", is_admin=False)

    assert exc.value.status_code == 403


def test_delete_review_admin_allowed(mocker):
    repo = mocker.Mock(spec=CSVReviewRepo)
    svc = ReviewsService(repo)

    repo.get_review_by_id.return_value = make_review(username="x")
    svc.delete_review("m1", "r1", username="admin", is_admin=True)

    repo.delete.assert_called_once()


# LIST
def test_list_reviews(mocker):
    repo = mocker.Mock(spec=CSVReviewRepo)
    svc = ReviewsService(repo)

    r1 = make_review(review_id="x1")
    r2 = make_review(review_id="x2")

    repo.list_by_movie.return_value = ([r1, r2], None)

    items, cursor = svc.list_reviews("m1", limit=2)

    assert len(items) == 2
    assert items[0].review_id == "x1"
    repo.list_by_movie.assert_called_once()
