from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status

from backend.deps import get_fake_is_admin
from backend.schemas.movies import (
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
):
    filters = MovieSearchFilters(
        title=title,
        genre=genre,
        release_year=release_year,
    )
    return svc.search_movies(filters=filters, page=page, page_size=page_size)


@router.get("/popular", response_model=list[MovieOut])
def get_popular(limit: int = Query(10, ge=1, le=50)):
    return svc.get_popular_movies(limit=limit)


@router.get("/recent", response_model=list[MovieOut])
def get_recent(limit: int = Query(10, ge=1, le=50)):
    return svc.get_recent_movies(limit=limit)


@router.get("/{movie_id}", response_model=MovieOut)
def get_movie(movie_id: str):
    return svc.get_movie(movie_id)


# ---------- Admin Only ----------


@router.post("/", response_model=MovieOut, status_code=status.HTTP_201_CREATED)
def create_movie(
    movie_create: MovieCreate,
    is_admin: bool = Depends(get_fake_is_admin),
):
    return svc.create_movie(movie_create, is_admin=is_admin)


@router.patch("/{movie_id}", response_model=MovieOut)
def update_movie(
    movie_id: str,
    movie_update: MovieUpdate,
    is_admin: bool = Depends(get_fake_is_admin),
):
    return svc.update_movie(movie_id, movie_update, is_admin=is_admin)


@router.delete("/{movie_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_movie(
    movie_id: str,
    is_admin: bool = Depends(get_fake_is_admin),
):
    svc.delete_movie(movie_id, is_admin=is_admin)
