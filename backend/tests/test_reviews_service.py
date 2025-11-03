# test_reviews_service.py
import csv
import importlib

import pytest
from fastapi import HTTPException

from schemas.reviews import ReviewCreate, ReviewUpdate  # Import necessary schemas


@pytest.fixture()
def svc(monkeypatch, tmp_path):
    # Prepare env and seed CSV
    data_dir = tmp_path / "data" / "movies"
    data_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("MOVIE_DATA_PATH", str(data_dir))

    # Reload repo first and service
    from repositories import reviews_repo as repo_mod

    importlib.reload(repo_mod)

    # Seed one movie with 1 existing review (user u1)
    movie_id = "The Dark Knight"
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
        writer.writerow(
            {
                "Date of Review": "20 July 2008",
                "User": "u1",
                "Usefulness Vote": "10",
                "Total Votes": "12",
                "User's Rating out of 10": "9",
                "Review Title": "masterpiece",
                "id": "",
            }
        )

    from app.services import reviews_service as svc_mod

    importlib.reload(svc_mod)
    return svc_mod, movie_id


# Fixtures
@pytest.fixture
def created_review(svc):
    '''
    Fixture: Creates a new review by user 'u2' for subsequent tests,
    ensuring cleanup and setup for each update/delete test.
    '''
    svc_mod, movie_id = svc
    # Create review by u2
    created = svc_mod.create_review(
        ReviewCreate(user_id="u2", movie_id=movie_id, rating=7, comment="good")
    )
    return created, svc_mod, movie_id


# Tests
def test_create_duplicate_blocked(svc):
    svc_mod, movie_id = svc

    from schemas.reviews import ReviewCreate

    # u1 already has a review
    payload = ReviewCreate(user_id="u1", movie_id=movie_id, rating=8, comment="dup")
    with pytest.raises(HTTPException) as e:
        svc_mod.create_review(payload)
    # HTTP 400
    assert e.value.status_code == 400
    assert "already reviewed" in str(e.value.detail).lower()


def test_update_authorization(created_review):
    '''Test that only the author can update or delete their review.'''
    created, svc_mod, movie_id = created_review

    # author updates ok
    updated = svc_mod.update_review(
        movie_id=movie_id,
        review_id=created.id,
        current_user_id="u2",
        payload=ReviewUpdate(rating=8),
    )
    assert updated.rating == 8

    # non-author update forbidden
    with pytest.raises(HTTPException) as e:
        svc_mod.update_review(
            movie_id=movie_id,
            review_id=created.id,
            current_user_id="someone_else",
            payload=ReviewUpdate(comment="hack"),
        )
    assert e.value.status_code == 403
    assert "not authorized" in str(e.value.detail).lower()


def test_delete_authorization(created_review):
    '''Test that only the author can delete their review.'''
    created, svc_mod, movie_id = created_review
    # review_id = created.id

    # non-author delete forbidden
    with pytest.raises(HTTPException) as e:
        svc_mod.delete_review(movie_id, created.id, current_user_id="hacker")
    assert e.value.status_code == 403
    assert "not authorized" in str(e.value.detail).lower()

    # author delete ok
    svc_mod.delete_review(movie_id, created.id, current_user_id="u2")

    # Verify deletion
    items, _ = svc_mod.list_reviews(movie_id, limit=50)
    assert all(it.id != created.id for it in items)
