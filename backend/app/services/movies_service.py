from __future__ import annotations
from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status

from backend.app.schemas.movies import MovieOut, MovieCreate, MovieUpdate, MovieSearchFilters, MovieListResponse
from backend.app.repositories.movies_repo import movie_repo


def get_movies(
        page: int = 1,
        page_size: int = 50,
        sort_by: Optional[str] = None,
        sort_desc: bool = False
) -> MovieListResponse:
    """Get paginated list of movies"""
    if page < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page must be greater than 0"
        )

    if page_size < 1 or page_size > 200:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page size must be between 1 and 200"
        )

    skip = (page - 1) * page_size
    movies, total = movie_repo.get_all(
        skip=skip,
        limit=page_size,
        sort_by=sort_by,
        sort_desc=sort_desc
    )

    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    return MovieListResponse(
        items=movies,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


def search_movies(
        filters: MovieSearchFilters,
        page: int = 1,
        page_size: int = 50
) -> MovieListResponse:
    """Search movies with filters"""
    if page < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page must be greater than 0"
        )

    if page_size < 1 or page_size > 200:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page size must be between 1 and 200"
        )

    skip = (page - 1) * page_size

    movies, total = movie_repo.search(
        title=filters.title,
        genre=filters.genre,
        min_year=filters.min_year,
        max_year=filters.max_year,
        min_rating=filters.min_rating,
        director=filters.director,
        skip=skip,
        limit=page_size
    )

    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    return MovieListResponse(
        items=movies,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


def get_movie(movie_id: str) -> MovieOut:
    """Get movie by ID"""
    movie = movie_repo.get_by_id(movie_id)
    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not found"
        )
    return movie


def create_movie(movie_create: MovieCreate, is_admin: bool = False) -> MovieOut:
    """Create a new movie (admin only)"""
    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create movies"
        )

    try:
        return movie_repo.create(movie_create)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


def update_movie(movie_id: str, movie_update: MovieUpdate, is_admin: bool = False) -> MovieOut:
    """Update a movie (admin only)"""
    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can update movies"
        )

    updated_movie = movie_repo.update(movie_id, movie_update)
    if not updated_movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not found"
        )

    return updated_movie


def delete_movie(movie_id: str, is_admin: bool = False) -> None:
    """Delete a movie (admin only)"""
    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete movies"
        )

    if not movie_repo.delete(movie_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not found"
        )


def get_popular_movies(limit: int = 10) -> List[MovieOut]:
    """Get popular movies (sorted by rating)"""
    if limit < 1 or limit > 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Limit must be between 1 and 50"
        )

    return movie_repo.get_popular(limit=limit)


def get_recent_movies(limit: int = 10) -> List[MovieOut]:
    """Get recently added movies"""
    if limit < 1 or limit > 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Limit must be between 1 and 50"
        )

    return movie_repo.get_recent(limit=limit)


def get_movie_recommendations(user_id: str, limit: int = 10) -> List[MovieOut]:
    """Get movie recommendations for a user based on their preferences"""
    # TODO: Implement recommendation logic based on user's review history
    # For now, return popular movies as placeholder
    return get_popular_movies(limit=limit)


def get_movie_stats() -> Dict[str, Any]:
    """Get movie statistics"""
    movies, total = movie_repo.get_all(limit=10000)  # Get all movies for stats

    if not movies:
        return {
            "total_movies": 0,
            "average_rating": 0,
            "top_genres": [],
            "year_range": {"min": 0, "max": 0}
        }

    # Calculate statistics
    ratings = [movie.rating for movie in movies if movie.rating]
    average_rating = sum(ratings) / len(ratings) if ratings else 0

    # Genre statistics
    genre_count = {}
    for movie in movies:
        if movie.genre:
            genres = [g.strip() for g in movie.genre.split(",")]
            for genre in genres:
                genre_count[genre] = genre_count.get(genre, 0) + 1

    top_genres = sorted(genre_count.items(), key=lambda x: x[1], reverse=True)[:5]

    # Year range
    years = [movie.release_year for movie in movies if movie.release_year]
    min_year = min(years) if years else 0
    max_year = max(years) if years else 0

    return {
        "total_movies": len(movies),
        "average_rating": round(average_rating, 2),
        "top_genres": top_genres,
        "year_range": {"min": min_year, "max": max_year}
    }