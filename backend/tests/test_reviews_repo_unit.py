# test_reviews_repo_unit.py

import csv
import importlib
from datetime import datetime, timezone

import pytest

from backend.schemas.reviews import ReviewOut


@pytest.fixture()
def repo_with_tmp_dir(tmp_path, mocker):
    """Inject fake MOVIE_DATA_PATH using mocker instead of monkeypatch."""
    fake = tmp_path / "data" / "movies"
    fake.mkdir(parents=True, exist_ok=True)

    # mock env reading in repo
    mocker.patch("backend.repositories.reviews_repo.os.getenv", return_value=str(fake))

    # reload repo to take effect
    from backend.repositories import reviews_repo as repo_mod

    importlib.reload(repo_mod)

    return fake, repo_mod.CSVReviewRepo(), repo_mod


def _seed_csv(dir_path, rows):
    path = dir_path / "movieReviews.csv"
    headers = [
        "Date of Review",
        "User",
        "Usefulness Vote",
        "Total Votes",
        "User's Rating out of 10",
        "Review Title",
        "id",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=headers)
        w.writeheader()
        w.writerows(rows)
    return path


@pytest.fixture()
def seeded_repo(repo_with_tmp_dir):
    """Repo backed by CSV w/ 2 initial reviews."""
    base, repo, _ = repo_with_tmp_dir
    movie_id = "Thor Ragnarok"
    mdir = base / movie_id
    mdir.mkdir(parents=True, exist_ok=True)

    _seed_csv(
        mdir,
        [
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
        ],
    )
    return movie_id, repo


# ---------- TESTS ----------


def test_filter_and_list(seeded_repo):
    movie_id, repo = seeded_repo
    items, nxt = repo.list_by_movie(movie_id)
    assert len(items) == 2 and nxt is None

    only_good, _ = repo.list_by_movie(movie_id, min_rating=7)
    assert len(only_good) == 1
    assert only_good[0].user_id == "u1"


def test_pagination(seeded_repo):
    movie_id, repo = seeded_repo

    p1, c1 = repo.list_by_movie(movie_id, limit=1)
    assert len(p1) == 1 and c1 == 1

    p2, c2 = repo.list_by_movie(movie_id, limit=1, cursor=c1)
    assert len(p2) == 1 and c2 is None
    assert p2[0].user_id == "u2"


def test_get_review_by_user(seeded_repo):
    movie_id, repo = seeded_repo
    u2 = repo.get_review_by_user(movie_id, "u2")
    assert u2 is not None and u2.rating == 6


def test_crud_cycle(seeded_repo):
    movie_id, repo = seeded_repo

    start, _ = repo.list_by_movie(movie_id)
    initial = len(start)

    now = datetime.now(timezone.utc)
    rev = ReviewOut(
        id="x9",
        user_id="u9",
        movie_id=movie_id,
        rating=9,
        comment="wow",
        created_at=now,
        updated_at=now,
    )
    repo.create(rev)
    assert repo.get_review_by_user(movie_id, "u9").rating == 9

    # update
    updated = ReviewOut(**rev.model_dump(exclude={"rating"}), rating=10)
    repo.update(updated)
    assert repo.get_review_by_id(movie_id, "x9").rating == 10

    # delete
    repo.delete(movie_id, "x9")
    assert repo.get_review_by_id(movie_id, "x9") is None

    final, _ = repo.list_by_movie(movie_id)
    assert len(final) == initial
