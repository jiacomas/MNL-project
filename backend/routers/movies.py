import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.exc import SQLAlchemyError

from backend.schemas.movies import (
    MovieCreate,
    MovieListResponse,
    MovieOut,
    MovieSearchFilters,
    MovieUpdate,
)
from backend.services import movies_service as svc

logger = logging.getLogger(__name__)

_AUTH_ENABLED = True

try:
    from app.deps import get_current_admin_user, get_current_user
except ImportError:
    _AUTH_ENABLED = False

    # Fallback for development without auth
    def get_current_user() -> Dict[str, Any]:
        return {"user_id": "demo_user", "role": "user"}

    def get_current_admin_user() -> Dict[str, Any]:
        return {"user_id": "admin_user", "role": "admin"}


router = APIRouter(prefix="/api/movies", tags=["movies"])


def handle_service_errors(func):
    """处理服务层错误的辅助函数"""

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except HTTPException:
            # Re-raise HTTPExceptions as they are intentional
            raise
        except SQLAlchemyError as e:
            logger.error(f"Database error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error occurred",
            )
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )

    return wrapper


@router.get("", response_model=MovieListResponse)
def list_movies_endpoint(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page"),
    sort_by: Optional[str] = Query(
        None, description="Sort field (title, release_year, rating, etc.)"
    ),
    sort_desc: bool = Query(False, description="Sort descending"),
):
    """Get paginated list of movies"""
    try:
        return svc.get_movies(
            page=page, page_size=page_size, sort_by=sort_by, sort_desc=sort_desc
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing movies: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get("/search", response_model=MovieListResponse)
def search_movies_endpoint(
    title: Optional[str] = Query(None, description="Search in movie titles"),
    genre: Optional[str] = Query(None, description="Filter by genre"),
    min_year: Optional[int] = Query(
        None, ge=1888, le=2100, description="Minimum release year"
    ),
    max_year: Optional[int] = Query(
        None, ge=1888, le=2100, description="Maximum release year"
    ),
    min_rating: Optional[float] = Query(
        None, ge=0, le=10, description="Minimum average rating"
    ),
    director: Optional[str] = Query(None, description="Filter by director"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page"),
):
    """Search movies with filters"""
    try:
        filters = MovieSearchFilters(
            title=title,
            genre=genre,
            min_year=min_year,
            max_year=max_year,
            min_rating=min_rating,
            director=director,
        )

        return svc.search_movies(filters=filters, page=page, page_size=page_size)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching movies: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get("/popular", response_model=list[MovieOut])
def get_popular_movies_endpoint(
    limit: int = Query(
        10, ge=1, le=50, description="Number of popular movies to return"
    )
):
    """Get popular movies (sorted by rating)"""
    try:
        return svc.get_popular_movies(limit=limit)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting popular movies: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get("/recent", response_model=list[MovieOut])
def get_recent_movies_endpoint(
    limit: int = Query(10, ge=1, le=50, description="Number of recent movies to return")
):
    """Get recently added movies"""
    try:
        return svc.get_recent_movies(limit=limit)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting recent movies: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get("/{movie_id}", response_model=MovieOut)
def get_movie_endpoint(movie_id: str = Path(..., description="Movie ID")):
    """Get movie by ID"""
    try:
        return svc.get_movie(movie_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting movie {movie_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.post("", response_model=MovieOut, status_code=status.HTTP_201_CREATED)
def create_movie_endpoint(
    payload: MovieCreate, current_user: Dict[str, Any] = Depends(get_current_admin_user)
):
    """Create a new movie"""
    try:
        return svc.create_movie(payload)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating movie: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.put("/{movie_id}", response_model=MovieOut)
def update_movie_endpoint(
    movie_id: str,
    payload: MovieUpdate,
    current_user: Dict[str, Any] = Depends(get_current_admin_user),
):
    """Update a movie"""
    try:
        return svc.update_movie(movie_id, payload)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating movie {movie_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.delete("/{movie_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_movie_endpoint(
    movie_id: str, current_user: Dict[str, Any] = Depends(get_current_admin_user)
):
    """Delete a movie"""
    try:
        svc.delete_movie(movie_id)
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting movie {movie_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get("/{movie_id}/recommendations", response_model=list[MovieOut])
def get_movie_recommendations_endpoint(
    movie_id: str,
    limit: int = Query(10, ge=1, le=50, description="Number of recommendations"),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Get movie recommendations based on the current movie"""
    try:
        user_id = current_user.get("user_id")
        return svc.get_movie_recommendations(user_id, limit=limit)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting recommendations for movie {movie_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get("/stats/summary", response_model=Dict[str, Any])
def get_movie_stats_endpoint():
    """Get movie statistics summary"""
    try:
        return svc.get_movie_stats()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting movie stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
