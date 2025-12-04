from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status

from backend.deps import require_admin
from backend.schemas.movies import (
    MovieAnalyticsResponse,
    MovieCreate,
    MovieListResponse,
    MovieOut,
    MovieSearchFilters,
    MovieUpdate,
)
from backend.services import movies_service as svc

router = APIRouter(prefix="/api/movies", tags=["movies"])


# ---------- Public Endpoints ----------


@router.get("/", response_model=MovieListResponse)
def list_movies(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    sort_by: str | None = None,
    sort_desc: bool = False,
):
    return svc.get_movies(
        page=page, page_size=page_size, sort_by=sort_by, sort_desc=sort_desc
    )


@router.get("/search", response_model=MovieListResponse)
def search_movies(
    title: str | None = None,
    genre: str | None = None,
    release_year: int | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    sort_by: str | None = Query(
        None,
        description="Sort field: rating or release_year (also supports title, genre, runtime, etc.)",
    ),
    sort_desc: bool = Query(
        False,
        description="Set to true for descending order (e.g., highest rating or newest year first)",
    ),
):
    filters = MovieSearchFilters(
        title=title,
        genre=genre,
        release_year=release_year,
    )
    return svc.search_movies(
        filters=filters,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_desc=sort_desc,
    )


@router.get("/popular", response_model=list[MovieOut])
def get_popular(limit: int = Query(10, ge=1, le=50)):
    return svc.get_popular_movies(limit=limit)


@router.get("/recent", response_model=list[MovieOut])
def get_recent(limit: int = Query(10, ge=1, le=50)):
    return svc.get_recent_movies(limit=limit)


@router.get("/analytics", response_model=MovieAnalyticsResponse)
def get_analytics(
    start_year: int | None = Query(None, ge=1800),
    end_year: int | None = Query(None, ge=1800),
    min_rating: float | None = Query(None, ge=0.0, le=10.0),
):
    return svc.get_movie_analytics(
        start_year=start_year,
        end_year=end_year,
        min_rating=min_rating,
    )


@router.get("/{movie_id}", response_model=MovieOut)
def get_movie(movie_id: str):
    return svc.get_movie(movie_id)


# ---------- Admin Only ----------


@router.post("/", response_model=MovieOut, status_code=status.HTTP_201_CREATED)
def create_movie(
    movie_create: MovieCreate,
    user: dict = Depends(require_admin),
):
    return svc.create_movie(movie_create, is_admin=True)


@router.patch("/{movie_id}", response_model=MovieOut)
def update_movie(
    movie_id: str,
    movie_update: MovieUpdate,
    user: dict = Depends(require_admin),
):
    return svc.update_movie(movie_id, movie_update, is_admin=True)


@router.delete("/{movie_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_movie(
    movie_id: str,
    user: dict = Depends(require_admin),
):
    svc.delete_movie(movie_id, is_admin=True)
