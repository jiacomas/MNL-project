from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, Path, status

from backend.app.schemas.movies import MovieOut, MovieCreate, MovieUpdate, MovieSearchFilters, MovieListResponse

from backend.app.services import movies_service as svc

_AUTH_ENABLED = True

try:
    from app.deps import get_current_user, get_current_admin_user
except ImportError:
    _AUTH_ENABLED = False

    # Fallback for development without auth
    def get_current_user() -> Dict[str, Any]:
        return {"user_id": "demo_user", "role": "user"}


    def get_current_admin_user() -> Dict[str, Any]:
        return {"user_id": "admin_user", "role": "admin"}

router = APIRouter(prefix="/api/movies", tags=["movies"])


@router.get("", response_model=MovieListResponse)
def list_movies_endpoint(
        page: int = Query(1, ge=1, description="Page number"),
        page_size: int = Query(50, ge=1, le=200, description="Items per page"),
        sort_by: Optional[str] = Query(
            None,
            description="Sort field (title, release_year, rating, etc.)"
        ),
        sort_desc: bool = Query(False, description="Sort descending")
):
    """Get paginated list of movies"""
    return svc.get_movies(
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_desc=sort_desc
    )


@router.get("/search", response_model=MovieListResponse)
def search_movies_endpoint(
        title: Optional[str] = Query(None, description="Search in movie titles"),
        genre: Optional[str] = Query(None, description="Filter by genre"),
        min_year: Optional[int] = Query(None, ge=1888, le=2100, description="Minimum release year"),
        max_year: Optional[int] = Query(None, ge=1888, le=2100, description="Maximum release year"),
        min_rating: Optional[float] = Query(None, ge=0, le=10, description="Minimum average rating"),
        director: Optional[str] = Query(None, description="Filter by director"),
        page: int = Query(1, ge=1, description="Page number"),
        page_size: int = Query(50, ge=1, le=200, description="Items per page")
):
    """Search movies with filters"""
    filters = MovieSearchFilters(
        title=title,
        genre=genre,
        min_year=min_year,
        max_year=max_year,
        min_rating=min_rating,
        director=director
    )

    return svc.search_movies(filters=filters, page=page, page_size=page_size)


@router.get("/popular", response_model=list[MovieOut])
def get_popular_movies_endpoint(
        limit: int = Query(10, ge=1, le=50, description="Number of popular movies to return")
):
    """Get popular movies (sorted by rating)"""
    return svc.get_popular_movies(limit=limit)


@router.get("/recent", response_model=list[MovieOut])
def get_recent_movies_endpoint(
        limit: int = Query(10, ge=1, le=50, description="Number of recent movies to return")
):
    """Get recently added movies"""
    return svc.get_recent_movies(limit=limit)


@router.get("/{movie_id}", response_model=MovieOut)
def get_movie_endpoint(
        movie_id: str = Path(..., description="Movie ID")
):
    """Get movie by ID"""
    return svc.get_movie(movie_id)


@router.post("", response_model=MovieOut, status_code=status.HTTP_201_CREATED)
def create_movie_endpoint(
        payload: MovieCreate,
        current_user: Dict[str, Any] = Depends(get_current_admin_user)
):
    """Create a new movie """
    return svc.create_movie(payload)


@router.put("/{movie_id}", response_model=MovieOut)
def update_movie_endpoint(
        movie_id: str,
        payload: MovieUpdate,
        current_user: Dict[str, Any] = Depends(get_current_admin_user)
):
    """Update a movie"""
    return svc.update_movie(movie_id, payload)


@router.delete("/{movie_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_movie_endpoint(
        movie_id: str,
        current_user: Dict[str, Any] = Depends(get_current_admin_user)
):
    """Delete a movie"""
    svc.delete_movie(movie_id)
    return None


@router.get("/{movie_id}/recommendations", response_model=list[MovieOut])
def get_movie_recommendations_endpoint(
        movie_id: str,
        limit: int = Query(10, ge=1, le=50, description="Number of recommendations"),
        current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get movie recommendations based on the current movie"""
    user_id = current_user.get("user_id")
    return svc.get_movie_recommendations(user_id, limit=limit)


@router.get("/stats/summary", response_model=Dict[str, Any])
def get_movie_stats_endpoint():
    """Get movie statistics summary"""
    return svc.get_movie_stats()

# Note: Parts of this file comments and basic scaffolding were auto-completed by VS Code.
# Core logic and subsequent modifications were implemented by the author(s).