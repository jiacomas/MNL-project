# test_reviews_repo.py

import csv
import importlib
from datetime import datetime, timezone

import pytest

from app.schemas.reviews import ReviewOut  # Import necessary schema

# --- Helper Functions & Fixtures ---


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
        for r in rows:
            writer.writerow(r)
    return path


@pytest.fixture()
def seeded_repo(movies_dir):
    '''Fixture to set up the repository instance and seed initial data.'''
    data_dir, repo_mod = movies_dir
    movie_id = "Thor Ragnarok"
    mdir = data_dir / movie_id.replace("/", "_")
    mdir.mkdir(parents=True, exist_ok=True)

    # Seed 2 rows
    _write_csv(
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

    # Return the movie_id, repository instance, and the data directory
    return movie_id, repo_mod.CSVReviewRepo(), data_dir


# --- Separated Test Functions ---


def test_list_and_filtering(seeded_repo):
    '''Tests basic list functionality and min_rating filtering.'''
    movie_id, repo, _ = seeded_repo

    # List all (no cursor)
    items, next_cursor = repo.list_by_movie(movie_id, limit=50)
    assert len(items) == 2
    assert next_cursor is None
    assert items[0].user_id == "u1"

    # min_rating filter (>=7)
    items2, _ = repo.list_by_movie(movie_id, limit=50, min_rating=7)
    assert len(items2) == 1
    assert items2[0].user_id == "u1"


def test_pagination(seeded_repo):
    '''Tests cursor-based pagination logic.'''
    movie_id, repo, _ = seeded_repo

    # pagination (limit=1)
    page1, cur1 = repo.list_by_movie(movie_id, limit=1)
    assert (
        len(page1) == 1 and cur1 == 1
    )  # cur1 should point to the second item (index 1)

    page2, cur2 = repo.list_by_movie(movie_id, limit=1, cursor=cur1)
    assert (
        len(page2) == 1 and cur2 is None
    )  # cur2 should be None as there are no more items
    assert page2[0].user_id == "u2"  # Should fetch the second item


def test_get_by_id_and_user(seeded_repo):
    '''Tests fetching a single review by user ID and by the generated unique ID.'''
    movie_id, repo, _ = seeded_repo

    # fetch by user
    mine = repo.get_by_user(movie_id, "u2")
    assert mine is not None and mine.rating == 6

    # Since we don't know the generated ID, we'll test create/get_by_id in the CRUD flow


def test_crud_lifecycle(seeded_repo):
    '''Tests the full Create, Update, Delete lifecycle.'''
    movie_id, repo, _ = seeded_repo

    # Initial count
    initial_items, _ = repo.list_by_movie(movie_id, limit=50)
    initial_count = len(initial_items)

    # --- CREATE ---
    now = datetime.now(timezone.utc)
    new_rev = ReviewOut(
        id="rev-3-crud",
        user_id="u3",
        movie_id=movie_id,
        rating=9,
        comment="love it",
        created_at=now,
        updated_at=now,
    )
    repo.create(new_rev)

    # Check list count and get_by_id
    items_after_create, _ = repo.list_by_movie(movie_id, limit=50)
    assert len(items_after_create) == initial_count + 1
    got = repo.get_by_id(movie_id, "rev-3-crud")
    assert got is not None and got.user_id == "u3"

    # --- UPDATE ---
    updated_rev = ReviewOut(
        **got.model_dump(exclude={"rating"}),
        rating=10,
    )
    updated_rev = repo.update(updated_rev)

    # Check updated value
    again = repo.get_by_id(movie_id, updated_rev.id)
    assert again.rating == 10

    # --- DELETE ---
    repo.delete(movie_id, updated_rev.id)

    # Check final count and get_by_id failure
    after_del, _ = repo.list_by_movie(movie_id, limit=50)
    assert len(after_del) == initial_count
    assert repo.get_by_id(movie_id, updated_rev.id) is None
