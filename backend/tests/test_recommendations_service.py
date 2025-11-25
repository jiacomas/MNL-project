from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import HTTPException
from pytest_mock import MockerFixture

from backend.services import recommendations_service as rec_mod


def _write(tmp_path: Path, name: str, content: str) -> Path:
    """Utility to write JSON content (as raw string) to a named file."""
    p = tmp_path / name
    p.write_text(content, encoding="utf-8")
    return p


def test_requires_minimum_three_ratings(tmp_path: Path, mocker: MockerFixture) -> None:
    """User must have at least 3 ratings before recommendations are generated."""
    items_file = _write(
        tmp_path,
        "items.json",
        '[{"id": "m1", "title": "Movie 1", "genres": ["Action"]}]',
    )
    reviews_file = _write(
        tmp_path,
        "reviews.json",
        '[{"user_id": "u1", "movie_id": "m1", "rating": 5}]',
    )

    mocker.patch.object(rec_mod, "ITEMS_FILE", items_file)
    mocker.patch.object(rec_mod, "REVIEWS_FILE", reviews_file)

    with pytest.raises(HTTPException) as exc:
        rec_mod.get_recommendations_for_user("u1")

    assert exc.value.status_code == 400
    assert "Rate at least 3 movies" in exc.value.detail


def test_recommendations_based_on_top_genres(
    tmp_path: Path, mocker: MockerFixture
) -> None:
    """
    At least 5 recommendations should appear if enough movies exist.
    Recommendations should prioritize the user's top genres.
    All returned RecommendationOut objects should have a reason string.
    """
    items_file = _write(
        tmp_path,
        "items.json",
        """
        [
          {"id": "m1", "title": "Action One",   "genres": ["Action"]},
          {"id": "m2", "title": "Action Two",   "genres": ["Action", "Adventure"]},
          {"id": "m3", "title": "Drama One",    "genres": ["Drama"]},
          {"id": "m4", "title": "Action Three", "genres": ["Action"]},
          {"id": "m5", "title": "Comedy One",   "genres": ["Comedy"]},
          {"id": "m6", "title": "Adventure X",  "genres": ["Adventure"]},
          {"id": "m7", "title": "Thriller Y",   "genres": ["Thriller"]}
        ]
        """,
    )

    # User u1 has 3 ratings; their top genres are Action + Adventure.
    reviews_file = _write(
        tmp_path,
        "reviews.json",
        """
        [
          {"user_id": "u1", "movie_id": "m1", "rating": 5},
          {"user_id": "u1", "movie_id": "m2", "rating": 4},
          {"user_id": "u1", "movie_id": "m3", "rating": 3}
        ]
        """,
    )

    mocker.patch.object(rec_mod, "ITEMS_FILE", items_file)
    mocker.patch.object(rec_mod, "REVIEWS_FILE", reviews_file)

    recs = rec_mod.get_recommendations_for_user("u1")

    # Expect at least 5 recommendations (when enough items exist)
    assert len(recs) >= 5

    # Every recommendation must have a reason
    for r in recs:
        assert r.reason, "All recommendations must include a reason."

    # The top few recommendations should align with preferred genres:
    top_titles = {r.title for r in recs[:3]}
    assert {"Action Three", "Adventure X"} & top_titles

    # All returned objects should expose expected attributes
    assert all(hasattr(r, "movie_id") for r in recs)
    assert all(hasattr(r, "title") for r in recs)
