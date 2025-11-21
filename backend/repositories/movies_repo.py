from __future__ import annotations

import csv
import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from backend import settings
from backend.schemas.movies import MovieCreate, MovieOut, MovieUpdate

# Configuration from centralized settings, allow env overrides (useful for tests)
MOVIES_CSV_PATH = os.getenv("MOVIES_CSV_PATH", str(settings.MOVIES_CSV_PATH))
MOVIES_JSON_PATH = os.getenv("MOVIES_JSON_PATH", str(settings.MOVIES_JSON_PATH))
EXTERNAL_METADATA_DIR = os.getenv(
    "EXTERNAL_METADATA_DIR", str(settings.EXTERNAL_METADATA_DIR)
)


def _ensure_data_dir() -> None:
    """Ensure the data directory exists"""
    os.makedirs(os.path.dirname(MOVIES_CSV_PATH), exist_ok=True)
    os.makedirs(EXTERNAL_METADATA_DIR, exist_ok=True)


def _convert_field_type(key: str, value: str) -> Any:
    """Convert field value to appropriate type based on key"""
    if not value:
        return None

    if key in ["release_year", "runtime"]:
        try:
            return int(value)
        except (ValueError, TypeError):
            return None
    elif key == "rating":
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    else:
        return value


def _parse_date_field(date_str: Any) -> datetime:
    """Parse date string to datetime object with proper error handling"""
    if not date_str:
        return datetime.now(timezone.utc)

    if isinstance(date_str, str) and "T" in date_str:
        try:
            # ISO format with timezone
            if date_str.endswith("Z"):
                date_str = date_str[:-1] + "+00:00"
            return datetime.fromisoformat(date_str)
        except (ValueError, TypeError):
            return datetime.now(timezone.utc)
    else:
        return datetime.now(timezone.utc)


def _process_csv_row(row: Dict[str, Any]) -> Dict[str, Any]:
    """Process a single CSV row with proper type conversion and error handling"""
    movie_data = {}

    # Process regular fields
    for key, value in row.items():
        movie_data[key] = _convert_field_type(key, value)

    # Process date fields
    for date_field in ["created_at", "updated_at"]:
        movie_data[date_field] = _parse_date_field(movie_data.get(date_field))

    return movie_data


def _load_movies_from_csv() -> List[Dict[str, Any]]:
    """Load movies from CSV file with enhanced error handling"""
    if not os.path.exists(MOVIES_CSV_PATH):
        return []

    movies = []
    try:
        with open(MOVIES_CSV_PATH, "r", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)

            # Check if we have the expected structure
            if reader.fieldnames is None:
                return []

            for row_num, row in enumerate(reader, start=1):
                try:
                    processed_row = _process_csv_row(row)
                    movies.append(processed_row)
                except Exception as e:
                    # Log the error but continue with other rows
                    print(f"Error processing row {row_num}: {e}")
                    continue

    except Exception as e:
        # Handle file-level errors (permission, encoding, etc.)
        print(f"Error reading CSV file: {e}")
        return []

    return movies


def _save_movies_to_csv(movies: List[Dict[str, Any]]) -> None:
    """Save movies to CSV file"""
    _ensure_data_dir()

    if not movies:
        # Create empty file with headers if no movies
        fieldnames = [
            "movie_id",
            "title",
            "genre",
            "release_year",
            "rating",
            "runtime",
            "director",
            "cast",
            "plot",
            "poster_url",
            "created_at",
            "updated_at",
        ]
        with open(MOVIES_CSV_PATH, "w", encoding="utf-8", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
        return

    # Use keys from first movie as fieldnames
    fieldnames = list(movies[0].keys())

    with open(MOVIES_CSV_PATH, "w", encoding="utf-8", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for movie in movies:
            # Convert datetime objects to ISO format strings for CSV storage
            csv_movie = movie.copy()
            for date_field in ["created_at", "updated_at"]:
                if date_field in csv_movie and isinstance(
                    csv_movie[date_field], datetime
                ):
                    csv_movie[date_field] = csv_movie[date_field].isoformat()
            writer.writerow(csv_movie)


def _load_movies_from_json() -> List[Dict[str, Any]]:
    """Load movies from JSON file (alternative storage)"""
    if not os.path.exists(MOVIES_JSON_PATH):
        return []

    try:
        with open(MOVIES_JSON_PATH, "r", encoding="utf-8") as f:
            movies_data = json.load(f)

        # Convert string dates back to datetime objects
        for movie in movies_data:
            for date_field in ["created_at", "updated_at"]:
                if date_field in movie and isinstance(movie[date_field], str):
                    try:
                        date_str = movie[date_field]
                        if date_str.endswith("Z"):
                            date_str = date_str[:-1] + "+00:00"
                        movie[date_field] = datetime.fromisoformat(date_str)
                    except (ValueError, TypeError):
                        movie[date_field] = datetime.now(timezone.utc)

        return movies_data
    except (json.JSONDecodeError, Exception):
        return []


def _save_movies_to_json(movies: List[Dict[str, Any]]) -> None:
    """Save movies to JSON file"""
    _ensure_data_dir()

    # Convert datetime objects to ISO format strings for JSON storage
    movies_for_json = []
    for movie in movies:
        json_movie = movie.copy()
        for date_field in ["created_at", "updated_at"]:
            if date_field in json_movie and isinstance(
                json_movie[date_field], datetime
            ):
                json_movie[date_field] = json_movie[date_field].isoformat()
        movies_for_json.append(json_movie)

    with open(MOVIES_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(movies_for_json, f, ensure_ascii=False, indent=2)


def _movie_to_dict(movie: Dict[str, Any]) -> Dict[str, Any]:
    """Convert movie data to dictionary suitable for MovieOut"""
    # Ensure all required fields are present
    result = {
        "movie_id": movie.get("movie_id", ""),
        "title": movie.get("title", ""),
        "genre": movie.get("genre"),
        "release_year": movie.get("release_year"),
        "rating": movie.get("rating"),
        "runtime": movie.get("runtime"),
        "director": movie.get("director"),
        "cast": movie.get("cast"),
        "plot": movie.get("plot"),
        "poster_url": movie.get("poster_url"),
        "created_at": movie.get("created_at", datetime.now(timezone.utc)),
        "updated_at": movie.get("updated_at", datetime.now(timezone.utc)),
        "review_count": movie.get("review_count", 0),
    }

    # Ensure datetime objects are timezone-aware
    for date_field in ["created_at", "updated_at"]:
        if (
            isinstance(result[date_field], datetime)
            and result[date_field].tzinfo is None
        ):
            result[date_field] = result[date_field].replace(tzinfo=timezone.utc)

    return result


def _dict_to_movie_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """Convert dictionary to movie storage format"""
    now = datetime.now(timezone.utc)

    result = {
        "movie_id": data.get("movie_id", str(uuid.uuid4())),
        "title": data.get("title", ""),
        "genre": data.get("genre"),
        "release_year": data.get("release_year"),
        "rating": data.get("rating"),
        "runtime": data.get("runtime"),
        "director": data.get("director"),
        "cast": data.get("cast"),
        "plot": data.get("plot"),
        "poster_url": data.get("poster_url"),
        "created_at": data.get("created_at", now),
        "updated_at": data.get("updated_at", now),
    }

    # Ensure we don't have empty strings for optional fields
    for field in ["genre", "director", "cast", "plot", "poster_url"]:
        if result[field] == "":
            result[field] = None

    return result


def _apply_movie_filters(
    movie: Dict[str, Any],
    title: Optional[str] = None,
    genre: Optional[str] = None,
    min_year: Optional[int] = None,
    max_year: Optional[int] = None,
    min_rating: Optional[float] = None,
    max_rating: Optional[float] = None,
    director: Optional[str] = None,
) -> bool:
    """Apply search filters to a single movie"""
    if title and title.lower() not in (movie.get("title") or "").lower():
        return False

    if genre and genre.lower() not in (movie.get("genre") or "").lower():
        return False

    movie_year = movie.get("release_year") or 0
    if min_year and movie_year < min_year:
        return False

    if max_year and movie_year > max_year:
        return False

    movie_rating = movie.get("rating") or 0
    if min_rating and movie_rating < min_rating:
        return False

    if max_rating and movie_rating > max_rating:
        return False

    if director and director.lower() not in (movie.get("director") or "").lower():
        return False

    return True


class MovieRepository:
    """
    Repository for movie data management using CSV/JSON storage
    """

    def __init__(self, use_json: bool = False):
        self.use_json = use_json

    def _load_movies(self) -> List[Dict[str, Any]]:
        """Load movies from storage"""
        if self.use_json:
            return _load_movies_from_json()
        else:
            return _load_movies_from_csv()

    def _save_movies(self, movies: List[Dict[str, Any]]) -> None:
        """Save movies to storage"""
        if self.use_json:
            _save_movies_to_json(movies)
        else:
            _save_movies_to_csv(movies)

    def get_all(
        self,
        skip: int = 0,
        limit: int = 50,
        sort_by: Optional[str] = None,
        sort_desc: bool = False,
    ) -> Tuple[List[MovieOut], int]:
        """Get all movies with pagination and sorting"""
        try:
            movies_data = self._load_movies()
        except Exception as e:
            print(f"Error loading movies: {e}")
            return [], 0
        total = len(movies_data)

        # Apply sorting
        if sort_by and movies_data:
            # Handle different field types for sorting
            def get_sort_key(movie):
                value = movie.get(sort_by)
                if value is None:
                    # Put None values at the end
                    return float("-inf") if not sort_desc else float("inf")
                return value

            movies_data.sort(key=get_sort_key, reverse=sort_desc)

        # Apply pagination
        paginated_data = movies_data[skip : skip + limit]

        movies = []
        for movie_data in paginated_data:
            try:
                movie_dict = _movie_to_dict(movie_data)
                movies.append(MovieOut.model_validate(movie_dict))
            except Exception as e:
                # Log the error but continue with other movies
                print(f"Error validating movie data: {e}")
                continue

        return movies, total

    def search(
        self,
        title: Optional[str] = None,
        genre: Optional[str] = None,
        min_year: Optional[int] = None,
        max_year: Optional[int] = None,
        min_rating: Optional[float] = None,
        max_rating: Optional[float] = None,
        director: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[MovieOut], int]:
        """Search movies with filters"""
        movies_data = self._load_movies()

        filtered_movies = []
        for movie in movies_data:
            if _apply_movie_filters(
                movie,
                title=title,
                genre=genre,
                min_year=min_year,
                max_year=max_year,
                min_rating=min_rating,
                max_rating=max_rating,
                director=director,
            ):
                filtered_movies.append(movie)

        total = len(filtered_movies)
        paginated_data = filtered_movies[skip : skip + limit]

        movies = []
        for movie_data in paginated_data:
            try:
                movie_dict = _movie_to_dict(movie_data)
                movies.append(MovieOut.model_validate(movie_dict))
            except Exception as e:
                print(f"Error validating movie data during search: {e}")
                continue

        return movies, total

    def get_by_id(self, movie_id: str) -> Optional[MovieOut]:
        """Get movie by ID"""
        movies_data = self._load_movies()

        for movie_data in movies_data:
            if movie_data.get("movie_id") == movie_id:
                try:
                    movie_dict = _movie_to_dict(movie_data)
                    return MovieOut.model_validate(movie_dict)
                except Exception as e:
                    print(f"Error validating movie {movie_id}: {e}")
                    return None
        return None

    def get_by_title(self, title: str) -> Optional[MovieOut]:
        """Get movie by exact title match"""
        movies_data = self._load_movies()

        for movie_data in movies_data:
            if movie_data.get("title", "").lower() == title.lower():
                try:
                    movie_dict = _movie_to_dict(movie_data)
                    return MovieOut.model_validate(movie_dict)
                except Exception as e:
                    print(f"Error validating movie {title}: {e}")
                    return None
        return None

    def create(self, movie_create: MovieCreate) -> MovieOut:
        """Create a new movie"""
        movies_data = self._load_movies()

        # Check if movie already exists by custom ID
        if movie_create.movie_id:
            existing = self.get_by_id(movie_create.movie_id)
            if existing:
                raise ValueError(
                    f"Movie with ID {movie_create.movie_id} already exists"
                )

        # Create movie data
        movie_dict = _dict_to_movie_dict(movie_create.model_dump())

        # Double-check movie_id is set
        if not movie_dict["movie_id"] or movie_dict["movie_id"] == "":
            movie_dict["movie_id"] = str(uuid.uuid4())

        movies_data.append(movie_dict)
        self._save_movies(movies_data)

        # Return the created movie as MovieOut
        try:
            return MovieOut.model_validate(_movie_to_dict(movie_dict))
        except Exception as e:
            raise ValueError(f"Failed to create movie: {e}")

    def update(self, movie_id: str, movie_update: MovieUpdate) -> Optional[MovieOut]:
        """Update an existing movie"""
        movies_data = self._load_movies()
        updated = False

        for i, movie_data in enumerate(movies_data):
            if movie_data.get("movie_id") == movie_id:
                # Update fields
                update_data = movie_update.model_dump(exclude_unset=True)
                for key, value in update_data.items():
                    if value is not None:
                        movies_data[i][key] = value

                # Update timestamp
                movies_data[i]["updated_at"] = datetime.now(timezone.utc)
                updated = True
                break

        if updated:
            self._save_movies(movies_data)
            return self.get_by_id(movie_id)

        return None

    def delete(self, movie_id: str) -> bool:
        """Delete a movie"""
        movies_data = self._load_movies()

        initial_count = len(movies_data)
        movies_data = [
            movie for movie in movies_data if movie.get("movie_id") != movie_id
        ]

        if len(movies_data) < initial_count:
            self._save_movies(movies_data)
            return True

        return False

    def get_popular(self, limit: int = 10) -> List[MovieOut]:
        """Get popular movies (sorted by rating and review count)"""
        movies_data = self._load_movies()

        # Filter out movies without ratings
        rated_movies = [m for m in movies_data if m.get("rating") is not None]

        # Sort by rating (descending) and then by title
        sorted_movies = sorted(
            rated_movies,
            key=lambda x: (x.get("rating") or 0, x.get("title") or ""),
            reverse=True,
        )

        popular_movies = []
        for movie_data in sorted_movies[:limit]:
            try:
                movie_dict = _movie_to_dict(movie_data)
                popular_movies.append(MovieOut.model_validate(movie_dict))
            except Exception as e:
                print(f"Error validating popular movie: {e}")
                continue

        return popular_movies

    def get_recent(self, limit: int = 10) -> List[MovieOut]:
        """Get recently added movies"""
        movies_data = self._load_movies()

        # Sort by creation date (descending)
        def get_created_at(movie):
            created = movie.get("created_at")
            if isinstance(created, datetime):
                return created
            return datetime.now(timezone.utc)

        sorted_movies = sorted(movies_data, key=get_created_at, reverse=True)

        recent_movies = []
        for movie_data in sorted_movies[:limit]:
            try:
                movie_dict = _movie_to_dict(movie_data)
                recent_movies.append(MovieOut.model_validate(movie_dict))
            except Exception as e:
                print(f"Error validating recent movie: {e}")
                continue

        return recent_movies


# Global repository instance
movie_repo = MovieRepository()
