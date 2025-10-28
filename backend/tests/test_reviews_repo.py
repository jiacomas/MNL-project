# test_reviews_repo.py
import os
import importlib
from datetime import datetime, timezone
import csv

import pytest


@pytest.fixture()
def movies_dir(tmp_path, monkeypatch):
    # Create a temporary data/movies directory
    data_dir = tmp_path / "data" / "movies"
    data_dir.mkdir(parents=True, exist_ok=True)
    # Temporarily set MOVIE_DATA_PATH to this directory
    monkeypatch.setenv("MOVIE_DATA_PATH", str(data_dir))
    # Reload the reviews_repo module to pick up the new path
    from app.repositories import reviews_repo as repo_mod
    importlib.reload(repo_mod)
    # return both the temp dir and the reloaded module
    return data_dir, repo_mod

def _write_csv(dir_path, rows):
    path = dir_path / "movieReviews.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "Date of Review", "User", "Usefulness Vote", "Total Votes",
            "User's Rating out of 10", "Review Title", "id"
        ])
        writer.writeheader()
        for r in rows:
            writer.writerow(r)
    return path


def test_list_get_crud_flow(movies_dir):
    data_dir, repo_mod = movies_dir
    movie_id = "Thor Ragnarok"
    mdir = data_dir / movie_id.replace("/", "_")
    mdir.mkdir(parents=True, exist_ok=True)

    # seed 2 rows with empty ids -> repo generates stable uuid5)
    _write_csv(mdir, [
        {
            "Date of Review": "27 October 2025",
            "User": "u1",
            "Usefulness Vote": "3",
            "Total Votes": "5",
            "User's Rating out of 10": "8",
            "Review Title": "funny & colorful",
            "id": "",
        },
        {
            "Date of Review": "26 October 2025",
            "User": "u2",
            "Usefulness Vote": "1",
            "Total Votes": "2",
            "User's Rating out of 10": "6",
            "Review Title": "good",
            "id": "",
        },
    ])

    repo = repo_mod.CSVReviewRepo()

    # list (no cursor)
    items, next_cursor = repo.list_by_movie(movie_id, limit=50)
    assert len(items) == 2
    assert next_cursor is None
    assert items[0].user_id == "u1"

    # min_rating filter (>=7)
    items2, _ = repo.list_by_movie(movie_id, limit=50, min_rating=7)
    assert len(items2) == 1
    assert items2[0].user_id == "u1"

    # pagination (limit=1)
    page1, cur1 = repo.list_by_movie(movie_id, limit=1)
    assert len(page1) == 1 and cur1 == 1
    page2, cur2 = repo.list_by_movie(movie_id, limit=1, cursor=cur1)
    assert len(page2) == 1 and cur2 is None

    # fetch by user
    mine = repo.get_by_user(movie_id, "u2")
    assert mine is not None and mine.rating == 6

    # create (append)
    from app.schemas.reviews import ReviewOut
    now = datetime.now(timezone.utc)
    new_rev = ReviewOut(
        id="rev-3",
        user_id="u3",
        movie_id=movie_id,
        rating=9,
        comment="love it",
        created_at=now,
        updated_at=now,
    )
    repo.create(new_rev)

    items3, _ = repo.list_by_movie(movie_id, limit=50)
    assert len(items3) == 3
    # index should allow fast get_by_id
    got = repo.get_by_id(movie_id, "rev-3")
    assert got is not None and got.user_id == "u3"

    # update row
    updated = ReviewOut(
        **got.model_dump(exclude={"rating"}),
        rating=10,
    )
    updated = repo.update(updated)
    again = repo.get_by_id(movie_id, updated.id)
    assert again.rating == 10

    # delete row
    repo.delete(movie_id, updated.id)
    after_del, _ = repo.list_by_movie(movie_id, limit=50)
    assert len(after_del) == 2
    assert repo.get_by_id(movie_id, updated.id) is None
