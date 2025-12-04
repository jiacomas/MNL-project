from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import HTTPException

from backend.repositories.movies_repo import MovieRepository
from backend.schemas.movies import (
    DirectorCount,
    GenreCount,
    MovieAnalyticsFilters,
    MovieAnalyticsResponse,
    MovieCreate,
    MovieListResponse,
    MovieOut,
    MovieSearchFilters,
    MovieUpdate,
    RatingBucket,
    YearCount,
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
    "rating",
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


def get_movie_analytics(
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
    min_rating: Optional[float] = None,
    repo: MovieRepository = movie_repo,
) -> MovieAnalyticsResponse:
    """
    Compute richer analytics for movies, designed for visualization.

    - Fetches up to MAX_ANALYTICS_LIMIT movies.
    - Applies optional filters on release year and rating.
    - Aggregates:
      * rating histogram (0–2, 2–4, 4–6, 6–8, 8–10)
      * release count per year
      * top genres
      * top directors
    """
    # Basic validation on filter ranges
    if start_year and end_year and start_year > end_year:
        raise HTTPException(
            status_code=400, detail="start_year cannot be greater than end_year"
        )
    if min_rating is not None and (min_rating < 0 or min_rating > 10):
        raise HTTPException(
            status_code=400, detail="min_rating must be between 0 and 10"
        )

    MAX_ANALYTICS_LIMIT = 10000

    # First call: take a reasonably large sample for analytics.
    movies, _ = repo.get_all(limit=MAX_ANALYTICS_LIMIT)
    # Second call: ask for total count (same pattern as get_movie_stats).
    _, total = repo.get_all(limit=1)

    filters_model = MovieAnalyticsFilters(
        start_year=start_year, end_year=end_year, min_rating=min_rating
    )

    if not movies:
        # No data at all -> return an empty but well-formed response
        return MovieAnalyticsResponse(
            total_movies=total,
            filtered_movies=0,
            filters=filters_model,
            rating_buckets=[],
            releases_by_year=[],
            genres=[],
            top_directors=[],
        )

    # Aggregation containers
    filtered_movies: List[MovieOut] = []
    year_counts: Dict[int, int] = {}
    genre_counts: Dict[str, int] = {}
    director_counts: Dict[str, int] = {}
    rating_bucket_counts: Dict[str, int] = {
        "0-2": 0,
        "2-4": 0,
        "4-6": 0,
        "6-8": 0,
        "8-10": 0,
    }

    for m in movies:
        # Safely parse year from datePublished
        year: Optional[int] = None
        dp = getattr(m, "datePublished", None)
        if isinstance(dp, str) and len(dp) >= 4:
            try:
                year = int(dp[:4])
            except Exception:
                year = None

        # Safely parse numeric rating
        rating_value: Optional[float] = None
        r = getattr(m, "movieIMDbRating", None)
        if r is not None:
            try:
                rating_value = float(r)
            except Exception:
                rating_value = None

        # Apply filters
        if start_year is not None and (year is None or year < start_year):
            continue
        if end_year is not None and (year is None or year > end_year):
            continue
        if min_rating is not None and (
            rating_value is None or rating_value < min_rating
        ):
            continue

        filtered_movies.append(m)

        # Rating histogram
        if rating_value is not None and rating_value >= 0:
            if rating_value < 2:
                bucket = "0-2"
            elif rating_value < 4:
                bucket = "2-4"
            elif rating_value < 6:
                bucket = "4-6"
            elif rating_value < 8:
                bucket = "6-8"
            else:
                bucket = "8-10"
            rating_bucket_counts[bucket] += 1

        # Year counts
        if year is not None:
            year_counts[year] = year_counts.get(year, 0) + 1

        # Genre counts (reuse same splitting rules as _aggregate_genres)
        mg = getattr(m, "movieGenres", None) or ""
        if mg:
            if "|" in mg:
                parts = [p.strip() for p in mg.split("|")]
            else:
                parts = [p.strip() for p in mg.split(",")]
            for g in parts:
                if g:
                    genre_counts[g] = genre_counts.get(g, 0) + 1

        # Director counts (support comma or pipe separated lists)
        directors_raw = getattr(m, "directors", None) or ""
        if directors_raw:
            if "|" in directors_raw:
                d_parts = [p.strip() for p in directors_raw.split("|")]
            else:
                d_parts = [p.strip() for p in directors_raw.split(",")]
            for d in d_parts:
                if d:
                    director_counts[d] = director_counts.get(d, 0) + 1

    # Build response models
    rating_buckets = [
        RatingBucket(bucket=b, count=rating_bucket_counts[b])
        for b in ["0-2", "2-4", "4-6", "6-8", "8-10"]
    ]

    releases_by_year = [
        YearCount(year=year, count=count)
        for year, count in sorted(year_counts.items(), key=lambda x: x[0])
    ]

    sorted_genres = sorted(genre_counts.items(), key=lambda x: (-x[1], x[0]))
    genres = [GenreCount(genre=name, count=count) for name, count in sorted_genres[:10]]

    sorted_directors = sorted(director_counts.items(), key=lambda x: (-x[1], x[0]))
    top_directors = [
        DirectorCount(director=name, count=count)
        for name, count in sorted_directors[:10]
    ]

    return MovieAnalyticsResponse(
        total_movies=total,
        filtered_movies=len(filtered_movies),
        filters=filters_model,
        rating_buckets=rating_buckets,
        releases_by_year=releases_by_year,
        genres=genres,
        top_directors=top_directors,
    )
