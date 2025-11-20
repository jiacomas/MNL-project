"""
Minimal but complete tests for movie schemas.
"""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from backend.schemas.movies import (
    MovieBase,
    MovieCreate,
    MovieListResponse,
    MovieOut,
    MovieSearchFilters,
    MovieUpdate,
)

# ---------- MovieBase ----------


def test_movie_base_normalizes_title():
    movie = MovieBase(title="  Test  ")
    assert movie.title == "Test"


def test_movie_base_rejects_empty_title():
    with pytest.raises(ValidationError):
        MovieBase(title="   ")


# ---------- MovieCreate ----------


def test_movie_create_id_normalizes():
    m = MovieCreate(title="Test", movie_id="  tt22  ")
    assert m.movie_id == "tt22"

    m2 = MovieCreate(title="Test", movie_id="   ")
    assert m2.movie_id is None


# ---------- MovieUpdate ----------


def test_movie_update_requires_at_least_one():
    with pytest.raises(ValidationError):
        MovieUpdate()


def test_movie_update_valid_partial():
    m = MovieUpdate(genre="  Drama  ")
    assert m.genre == "Drama"


# ---------- MovieOut ----------


def test_movie_out_fields():
    now = datetime.now(timezone.utc)
    out = MovieOut(
        movie_id="id",
        title="Test",
        created_at=now,
        updated_at=now,
    )
    assert out.review_count == 0

    with pytest.raises(ValidationError):
        MovieOut(title="T", created_at=now, updated_at=now)


# ---------- MovieSearchFilters ----------


def test_search_filters_strip_text_fields():
    f = MovieSearchFilters(title=" hello ", genre=" Drama ")
    assert f.title == "hello"
    assert f.genre == "Drama"


# ---------- MovieListResponse ----------


def test_movie_list_response_basic():
    now = datetime.now(timezone.utc)
    item = MovieOut(movie_id="tt", title="T", created_at=now, updated_at=now)
    r = MovieListResponse(items=[item], total=1, page=1, page_size=10, total_pages=1)
    assert r.total == 1
    assert r.page == 1
    assert r.items[0].title == "T"


# ---------- Unicode / XSS edge ----------


def test_movie_base_unicode_and_html():
    m = MovieBase(title="测试 🎬", genre="<script>alert(1)</script>")
    assert "🎬" in m.title
    assert "<script>" in m.genre
