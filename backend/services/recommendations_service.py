from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Set

from fastapi import HTTPException, status

from schemas.recommendations import RecommendationOut

# Default locations – tests override these with monkeypatch.
BASE_DIR = Path("data")
ITEMS_FILE: Path = BASE_DIR / "items.json"
REVIEWS_FILE: Path = BASE_DIR / "reviews.json"

MIN_RATINGS_REQUIRED = 3
MIN_RECOMMENDATIONS = 5
HIGH_RATING_THRESHOLD = 4


def _load_json_list(path: Path) -> List[Dict[str, Any]]:
    """Load a JSON file and always return a list of dicts."""
    if not path.exists():
        return []

    data = json.loads(path.read_text(encoding="utf-8"))

    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        # Allow simple wrapper forms like {"items":[...]}
        for value in data.values():
            if isinstance(value, list):
                return list(value)
        return [data]

    return []


def _movie_lookup(items: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Map movie_id -> movie dict for quick lookup."""
    return {str(it.get("id")): it for it in items}


def get_recommendations_for_user(user_id: str) -> List[RecommendationOut]:
    """Return movie recommendations for a given user.

    Rules (matching the user story / tests):

    * User must have rated at least 3 movies, otherwise HTTP 400.
    * Recommendations are based on top genres from the user's high-rated movies.
    * We try to return at least 5 recommendations when enough titles exist.
    * Each recommendation includes a human-readable 'reason'.
    """
    items = _load_json_list(ITEMS_FILE)
    reviews = _load_json_list(REVIEWS_FILE)

    movies_by_id = _movie_lookup(items)

    # All reviews for this user
    user_reviews = [r for r in reviews if str(r.get("user_id")) == user_id]
    if len(user_reviews) < MIN_RATINGS_REQUIRED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            # NOTE: this substring is what the test asserts on
            detail="Rate at least 3 movies before getting recommendations.",
        )

    rated_ids: Set[str] = {str(r.get("movie_id")) for r in user_reviews}

    # High-rated reviews (used to infer preference)
    liked_reviews = [
        r for r in user_reviews if int(r.get("rating", 0)) >= HIGH_RATING_THRESHOLD
    ]

    # Count genres across high-rated movies
    genre_counter: Counter[str] = Counter()
    for r in liked_reviews:
        movie = movies_by_id.get(str(r.get("movie_id")))
        if not movie:
            continue
        for g in movie.get("genres", []):
            genre_counter[str(g)] += 1

    top_genres: List[str] = [g for g, _ in genre_counter.most_common(3)]

    recommendations: List[RecommendationOut] = []

    def _already_added(movie_id: str) -> bool:
        mid = str(movie_id)
        return any(r.movie_id == mid for r in recommendations)

    def _add_rec(movie_id: str, reason: str) -> None:
        mid = str(movie_id)
        if _already_added(mid):
            return
        movie = movies_by_id.get(mid)
        if not movie:
            return
        recommendations.append(
            RecommendationOut(
                movie_id=mid,
                title=str(movie.get("title", "")),
                reason=reason,
            )
        )

    # -----------------------------------------------------------
    # 1. Unrated movies matching the user's top genres
    # -----------------------------------------------------------
    for movie in items:
        mid = str(movie.get("id"))
        if mid in rated_ids:
            continue

        movie_genres = [str(g) for g in movie.get("genres", [])]
        if not movie_genres or not top_genres:
            continue

        if any(g in top_genres for g in movie_genres):
            matched = next((g for g in movie_genres if g in top_genres), top_genres[0])
            _add_rec(mid, f"Because you liked {matched} movies")

        if len(recommendations) >= MIN_RECOMMENDATIONS:
            return recommendations

    # -----------------------------------------------------------
    # 2. If we still need more, re-surface high-rated favourites
    # -----------------------------------------------------------
    if len(recommendations) < MIN_RECOMMENDATIONS:
        for r in sorted(
            liked_reviews, key=lambda r: int(r.get("rating", 0)), reverse=True
        ):
            mid = str(r.get("movie_id"))
            movie = movies_by_id.get(mid)
            if not movie:
                continue

            movie_genres = [str(g) for g in movie.get("genres", [])]
            if movie_genres:
                genre = next(
                    (g for g in movie_genres if g in top_genres),
                    movie_genres[0],
                )
            else:
                genre = "these"

            _add_rec(mid, f"Because you liked {genre} movies")

            if len(recommendations) >= MIN_RECOMMENDATIONS:
                return recommendations

    # -----------------------------------------------------------
    # 3. Fallback: fill with any remaining movies
    # -----------------------------------------------------------
    if len(recommendations) < MIN_RECOMMENDATIONS:
        for movie in items:
            mid = str(movie.get("id"))
            if _already_added(mid):
                continue
            _add_rec(mid, "Because you have been rating movies recently")
            if len(recommendations) >= MIN_RECOMMENDATIONS:
                break

    return recommendations
