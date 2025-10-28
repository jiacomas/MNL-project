# test_reviews_service.py
import os
import importlib
import csv
from datetime import datetime, timezone

import pytest

@pytest.fixture()
def svc(monkeypatch, tmp_path):
    # Prepare env and seed CSV
    data_dir = tmp_path / "data" / "movies"
    data_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("MOVIE_DATA_PATH", str(data_dir))

    # Reload repo first and service
    from app.repositories import reviews_repo as repo_mod
    importlib.reload(repo_mod)

    # Seed one movie with 1 existing review (user u1)
    movie_id = "The Dark Knight"
    mdir = data_dir / movie_id
    mdir.mkdir(parents=True, exist_ok=True)
    p = mdir / "movieReviews.csv"
    with p.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "Date of Review", "User", "Usefulness Vote", "Total Votes",
            "User's Rating out of 10", "Review Title", "id"
        ])
        writer.writeheader()
        writer.writerow({
            "Date of Review": "20 July 2008",
            "User": "u1",
            "Usefulness Vote": "10",
            "Total Votes": "12",
            "User's Rating out of 10": "9",
            "Review Title": "masterpiece",
            "id": "",
        })

    from app.services import reviews_service as svc_mod
    importlib.reload(svc_mod)
    return svc_mod, movie_id


def test_create_duplicate_blocked(svc):
    svc_mod, movie_id = svc

    from app.schemas.reviews import ReviewCreate
    # u1 already has a review
    payload = ReviewCreate(user_id="u1", movie_id=movie_id, rating=8, comment="dup")
    with pytest.raises(Exception) as e:
        svc_mod.create_review(payload)
    # HTTP 400
    assert "already reviewed" in str(e.value)


def test_crud_authorization(svc):
    svc_mod, movie_id = svc
    from app.schemas.reviews import ReviewCreate, ReviewUpdate

    # create by u2
    created = svc_mod.create_review(ReviewCreate(
        user_id="u2", movie_id=movie_id, rating=7, comment="good"
    ))
    assert created.user_id == "u2"

    # author updates ok
    updated = svc_mod.update_review(
        movie_id=movie_id,
        review_id=created.id,
        current_user_id="u2",
        payload=ReviewUpdate(rating=8)
    )
    assert updated.rating == 8

    # non-author update forbidden
    with pytest.raises(Exception) as e:
        svc_mod.update_review(
            movie_id=movie_id,
            review_id=created.id,
            current_user_id="someone_else",
            payload=ReviewUpdate(comment="hack")
        )
    assert "Not authorized" in str(e.value)

    # non-author delete forbidden
    with pytest.raises(Exception):
        svc_mod.delete_review(movie_id, created.id, current_user_id="hacker")

    # author delete ok
    svc_mod.delete_review(movie_id, created.id, current_user_id="u2")
    items, _ = svc_mod.list_reviews(movie_id, limit=50)
    assert all(it.id != created.id for it in items)
