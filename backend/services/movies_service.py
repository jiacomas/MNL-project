from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import HTTPException

from backend.repositories.movies_repo import MovieRepository
from backend.schemas.movies import (
    MovieCreate,
    MovieListResponse,
    MovieOut,
    MovieSearchFilters,
    MovieUpdate,
)

movie_repo = MovieRepository()

ALLOWED_SORT_FIELDS = [
    "title",
    "movieGenres",
    "datePublished",
    "movieIMDbRating",
    "duration",
    "directors",
    "created_at",
    "updated_at",
    "review_count",
]


def get_movies(
    page: int = 1,
    page_size: int = 50,
    sort_by: Optional[str] = None,
    sort_desc: bool = False,
    repo: MovieRepository = movie_repo,
) -> MovieListResponse:
    """Return paginated movie list with optional sorting."""
    if page < 1:
        raise HTTPException(status_code=400, detail="Page must be greater than 0")
    if page_size < 1 or page_size > 200:
        raise HTTPException(
            status_code=400, detail="Page size must be between 1 and 200"
        )
    if sort_by and sort_by not in ALLOWED_SORT_FIELDS:
        raise HTTPException(status_code=400, detail=f"Invalid sort field: {sort_by}")

    skip = (page - 1) * page_size
    movies, total = repo.get_all(
        skip=skip, limit=page_size, sort_by=sort_by, sort_desc=sort_desc
    )
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    return MovieListResponse(
        items=movies,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


def search_movies(
    filters: MovieSearchFilters,
    page: int = 1,
    page_size: int = 50,
    sort_by: Optional[str] = None,
    sort_desc: bool = False,
    repo: MovieRepository = movie_repo,
) -> MovieListResponse:
    """Search movies using simple filters with optional sorting."""
    if page < 1:
        raise HTTPException(status_code=400, detail="Page must be greater than 0")
    if page_size < 1 or page_size > 200:
        raise HTTPException(
            status_code=400, detail="Page size must be between 1 and 200"
        )
    if sort_by and sort_by not in ALLOWED_SORT_FIELDS:
        raise HTTPException(status_code=400, detail=f"Invalid sort field: {sort_by}")

    skip = (page - 1) * page_size
    params = filters.model_dump(exclude_none=True)

    movies, total = repo.search(
        title=params.get("title"),
        genre=params.get("genre"),
        release_year=params.get("release_year"),
        skip=skip,
        limit=page_size,
        sort_by=sort_by,
        sort_desc=sort_desc,
    )

    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
    return MovieListResponse(
        items=movies,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


def get_movie(movie_id: str, repo: MovieRepository = movie_repo) -> MovieOut:
    """Return a movie by its ID."""
    movie = repo.get_by_id(movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    return movie


def create_movie(
    movie_create: MovieCreate,
    is_admin: bool = False,
    repo: MovieRepository = movie_repo,
) -> MovieOut:
    """Create a new movie (admin only)."""
    if not is_admin:
        raise HTTPException(status_code=403, detail="Only admins can create movies")
    try:
        return repo.create(movie_create)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


def update_movie(
    movie_id: str,
    movie_update: MovieUpdate,
    is_admin: bool = False,
    repo: MovieRepository = movie_repo,
) -> MovieOut:
    """Update movie details (admin only)."""
    if not is_admin:
        raise HTTPException(status_code=403, detail="Only admins can update movies")

    updated = repo.update(movie_id, movie_update)
    if not updated:
        raise HTTPException(status_code=404, detail="Movie not found")
    return updated


def delete_movie(
    movie_id: str,
    is_admin: bool = False,
    repo: MovieRepository = movie_repo,
) -> None:
    """Delete a movie (admin only)."""
    if not is_admin:
        raise HTTPException(status_code=403, detail="Only admins can delete movies")
    if not repo.delete(movie_id):
        raise HTTPException(status_code=404, detail="Movie not found")


def get_popular_movies(
    limit: int = 10, repo: MovieRepository = movie_repo
) -> List[MovieOut]:
    """Return top-rated movies."""
    if limit < 1 or limit > 50:
        raise HTTPException(status_code=400, detail="Limit must be between 1 and 50")
    return repo.get_popular(limit=limit)


def get_recent_movies(
    limit: int = 10, repo: MovieRepository = movie_repo
) -> List[MovieOut]:
    """Return recently added movies."""
    if limit < 1 or limit > 50:
        raise HTTPException(status_code=400, detail="Limit must be between 1 and 50")
    return repo.get_recent(limit=limit)


def _collect_ratings(movies: List[MovieOut]) -> List[float]:
    """Return a list of numeric ratings from movies, skipping None values."""
    ratings: List[float] = []
    for m in movies:
        r = getattr(m, "movieIMDbRating", None)
        if r is not None:
            try:
                ratings.append(float(r))
            except Exception:
                # ignore non-numeric rating values
                continue
    return ratings


def _aggregate_genres(movies: List[MovieOut]) -> Dict[str, int]:
    """Aggregate genre counts from movie.movieGenres supporting pipe or comma separators."""
    genre_count: Dict[str, int] = {}
    for m in movies:
        mg = getattr(m, "movieGenres", None) or ""
        if not mg:
            continue
        if "|" in mg:
            parts = [p.strip() for p in mg.split("|")]
        else:
            parts = [p.strip() for p in mg.split(",")]
        for g in parts:
            if g:
                genre_count[g] = genre_count.get(g, 0) + 1
    return genre_count


def _derive_years(movies: List[MovieOut]) -> List[int]:
    """Extract publication years (first 4 chars) from datePublished when possible."""
    years: List[int] = []
    for m in movies:
        dp = getattr(m, "datePublished", None)
        if isinstance(dp, str) and len(dp) >= 4:
            try:
                years.append(int(dp[:4]))
            except Exception:
                continue
    return years


def get_movie_stats(repo: MovieRepository = movie_repo) -> Dict[str, Any]:
    """Compute simple movie statistics."""
    MAX_STATS_LIMIT = 5000
    movies, _ = repo.get_all(limit=MAX_STATS_LIMIT)
    _, total = repo.get_all(limit=1)

    if not movies:
        return {
            "total_movies": 0,
            "average_rating": 0,
            "top_genres": [],
            "year_range": {"min": 0, "max": 0},
        }

    ratings = _collect_ratings(movies)
    avg_rating = sum(ratings) / len(ratings) if ratings else 0

    genre_count = _aggregate_genres(movies)
    top_genres = sorted(genre_count.items(), key=lambda x: x[1], reverse=True)[:5]

    years = _derive_years(movies)
    return {
        "total_movies": total,
        "average_rating": round(avg_rating, 2),
        "top_genres": top_genres,
        "year_range": {
            "min": min(years) if years else 0,
            "max": max(years) if years else 0,
        },
    }
