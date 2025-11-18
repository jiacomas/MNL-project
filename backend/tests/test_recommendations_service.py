from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import HTTPException
from services import recommendations_service as rec_mod


def _write(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(content, encoding="utf-8")
    return p


def test_requires_minimum_three_ratings(tmp_path, monkeypatch) -> None:
    """Recommendations only appear after the user has rated at least 3 movies."""
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

    monkeypatch.setattr(rec_mod, "ITEMS_FILE", items_file)
    monkeypatch.setattr(rec_mod, "REVIEWS_FILE", reviews_file)

    with pytest.raises(HTTPException) as exc:
        rec_mod.get_recommendations_for_user("u1")

    assert exc.value.status_code == 400
    assert "Rate at least 3 movies" in exc.value.detail


def test_recommendations_based_on_top_genres(tmp_path, monkeypatch) -> None:
    """At least 5 recs; based on genres from high-rated movies; reasons included."""
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

    # u1 has three ratings; two are high-rated Action / Adventure movies
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

    monkeypatch.setattr(rec_mod, "ITEMS_FILE", items_file)
    monkeypatch.setattr(rec_mod, "REVIEWS_FILE", reviews_file)

    recs = rec_mod.get_recommendations_for_user("u1")

    # At least 5 movies recommended (if available)
    assert len(recs) >= 5

    # All recs must have a reason string
    for r in recs:
        assert r.reason

    # Top recommendations should be in the user's preferred genres
    top_titles = {r.title for r in recs[:3]}
    assert {"Action Three", "Adventure X"} & top_titles

    # Endpoint returns RecommendationOut objects
    assert all(hasattr(r, "movie_id") for r in recs)
    assert all(hasattr(r, "title") for r in recs)
