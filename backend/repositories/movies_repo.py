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

# Global Fields for consistent CSV header/order
ALL_FIELDS = [
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
    "review_count",
]


def _ensure_data_dir() -> None:
    os.makedirs(os.path.dirname(MOVIES_CSV_PATH), exist_ok=True)
    os.makedirs(EXTERNAL_METADATA_DIR, exist_ok=True)


def _parse_date_field(date_str: Any) -> datetime:
    """Parse str to datetime, fallback to now with UTC timezone."""
    if not date_str:
        return datetime.now(timezone.utc)

    if isinstance(date_str, str):
        try:
            if date_str.endswith("Z"):
                date_str = date_str[:-1] + "+00:00"
            return datetime.fromisoformat(date_str)
        except Exception:
            pass

    return datetime.now(timezone.utc)


def _process_csv_row(row: Dict[str, Any]) -> Dict[str, Any]:
    """Convert csv row strings to correct types (int/float/datetime)."""
    movie_data = {k: (v if v else None) for k, v in row.items()}

    # Convert numeric fields
    try:
        if movie_data.get("release_year") is not None:
            movie_data["release_year"] = int(movie_data["release_year"])
    except (ValueError, TypeError):
        movie_data["release_year"] = None

    try:
        if movie_data.get("runtime") is not None:
            movie_data["runtime"] = int(movie_data["runtime"])
    except (ValueError, TypeError):
        movie_data["runtime"] = None

    try:
        if movie_data.get("rating") is not None:
            movie_data["rating"] = float(movie_data["rating"])
    except (ValueError, TypeError):
        movie_data["rating"] = None

    # Dates
    movie_data["created_at"] = _parse_date_field(movie_data.get("created_at"))
    movie_data["updated_at"] = _parse_date_field(movie_data.get("updated_at"))

    return movie_data


def _load_movies_from_csv() -> List[Dict[str, Any]]:
    if not os.path.exists(MOVIES_CSV_PATH):
        return []

    try:
        with open(MOVIES_CSV_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                return []
            return [_process_csv_row(row) for row in reader]
    except Exception:
        # File read error, return empty list
        return []


def _save_movies_to_csv(movies: List[Dict[str, Any]]) -> None:
    _ensure_data_dir()

    fieldnames = ALL_FIELDS

    with open(MOVIES_CSV_PATH, "w", encoding="utf-8", newline="") as f:
        # Use ALL_FIELDS for consistent header and ignore extra keys
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()

        for m in movies:
            item = m.copy()
            # Convert datetime to ISO format string for saving
            for d in ["created_at", "updated_at"]:
                if isinstance(item.get(d), datetime):
                    item[d] = item[d].isoformat()
            writer.writerow(item)


def _load_movies_from_json() -> List[Dict[str, Any]]:
    if not os.path.exists(MOVIES_JSON_PATH):
        return []

    try:
        with open(MOVIES_JSON_PATH, "r", encoding="utf-8") as f:
            movies = json.load(f)
        for m in movies:
            for d in ["created_at", "updated_at"]:
                m[d] = _parse_date_field(m.get(d))
        return movies
    except Exception:
        return []


def _save_movies_to_json(movies: List[Dict[str, Any]]) -> None:
    _ensure_data_dir()
    dump = []
    for m in movies:
        item = m.copy()
        for d in ["created_at", "updated_at"]:
            if isinstance(item.get(d), datetime):
                item[d] = item[d].isoformat()
        dump.append(item)
    with open(MOVIES_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(dump, f, ensure_ascii=False, indent=2)


def _movie_to_dict(movie: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure timestamps are timezone-aware (UTC) & review_count exists."""
    result = movie.copy()
    now = datetime.now(timezone.utc)

    for d in ["created_at", "updated_at"]:
        if not isinstance(result.get(d), datetime):
            result[d] = now
        elif result[d].tzinfo is None:
            result[d] = result[d].replace(tzinfo=timezone.utc)

    # Ensures review_count is always present for MovieOut validation
    result["review_count"] = result.get("review_count") or 0
    return result


class MovieRepository:
    """Movie storage using CSV/JSON. Includes caching for performance."""

    def __init__(self, use_json: bool = False):
        self.use_json = use_json
        self._cache: Optional[List[Dict[str, Any]]] = None  # In-memory data cache

    def _load_movies(self) -> List[Dict[str, Any]]:
        # Check cache first
        if self._cache is not None:
            return self._cache

        # Load from file and set cache
        movies = _load_movies_from_json() if self.use_json else _load_movies_from_csv()
        self._cache = movies
        return self._cache

    def _save_movies(self, movies: List[Dict[str, Any]]) -> None:
        # Update cache before writing to file
        self._cache = movies
        return (
            _save_movies_to_json(movies)
            if self.use_json
            else _save_movies_to_csv(movies)
        )

    # ---------------- CRUD ---------------- #

    def get_all(
        self,
        skip: int = 0,
        limit: int = 50,
        sort_by: Optional[str] = None,
        sort_desc: bool = False,
    ) -> Tuple[List[MovieOut], int]:
        movies = self._load_movies()  # Loads from cache
        total = len(movies)

        if sort_by:
            # Sort handles None values by placing them first/last
            movies.sort(
                key=lambda x: (x.get(sort_by) is None, x.get(sort_by)),
                reverse=sort_desc,
            )

        page = movies[skip : skip + limit]
        return [MovieOut.model_validate(_movie_to_dict(m)) for m in page], total

    def get_by_id(self, movie_id: str) -> Optional[MovieOut]:
        for m in self._load_movies():  # Loads from cache
            if m.get("movie_id") == movie_id:
                return MovieOut.model_validate(_movie_to_dict(m))
        return None

    def get_by_title(self, title: str) -> Optional[MovieOut]:
        for m in self._load_movies():  # Loads from cache
            if m.get("title", "").lower() == title.lower():
                return MovieOut.model_validate(_movie_to_dict(m))
        return None

    def create(self, movie_create: MovieCreate) -> MovieOut:
        movies = self._load_movies()  # Loads from cache

        # Check for duplicate ID directly in the cached list
        if movie_create.movie_id:
            for m in movies:
                if m.get("movie_id") == movie_create.movie_id:
                    raise ValueError(
                        f"Movie with ID {movie_create.movie_id} already exists"
                    )

        data = movie_create.model_dump()
        now = datetime.now(timezone.utc)
        data["movie_id"] = data.get("movie_id") or str(uuid.uuid4())
        data["created_at"] = now
        data["updated_at"] = now

        movies.append(data)
        self._save_movies(movies)  # Updates cache and file
        return MovieOut.model_validate(_movie_to_dict(data))

    def update(self, movie_id: str, movie_update: MovieUpdate) -> Optional[MovieOut]:
        movies = self._load_movies()
        for i, m in enumerate(movies):
            if m.get("movie_id") == movie_id:
                update = movie_update.model_dump(exclude_unset=True)
                for k, v in update.items():
                    movies[i][k] = v
                movies[i]["updated_at"] = datetime.now(timezone.utc)
                self._save_movies(movies)  # Updates cache and file
                return self.get_by_id(movie_id)
        return None

    def delete(self, movie_id: str) -> bool:
        movies = self._load_movies()
        new = [m for m in movies if m.get("movie_id") != movie_id]
        if len(new) < len(movies):
            self._save_movies(new)  # Updates cache and file
            return True
        return False

    # ---------------- Extra Queries ---------------- #

    def get_popular(self, limit: int = 10) -> List[MovieOut]:
        movies = self._load_movies()
        movies_with_rating = [m for m in movies if m.get("rating") is not None]
        movies_with_rating.sort(
            key=lambda x: (x.get("rating", 0), x.get("title") or ""), reverse=True
        )
        return [
            MovieOut.model_validate(_movie_to_dict(m))
            for m in movies_with_rating[:limit]
        ]

    def get_recent(self, limit: int = 10) -> List[MovieOut]:
        movies = self._load_movies()
        # Use datetime.min as a fallback for missing created_at to ensure stable sort
        movies.sort(
            key=lambda x: x.get("created_at")
            or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )
        return [MovieOut.model_validate(_movie_to_dict(m)) for m in movies[:limit]]

    def search(
        self,
        title: str | None = None,
        genre: str | None = None,
        release_year: int | None = None,
        skip: int = 0,
        limit: int = 50,
        sort_by: str | None = None,
        sort_desc: bool = False,
    ) -> tuple[list[MovieOut], int]:
        """Simple search filter for movies."""
        movies = self._load_movies()

        # Basic filtering
        filtered = []
        for m in movies:
            if title and title.lower() not in (m.get("title") or "").lower():
                continue
            if genre and genre.lower() not in (m.get("genre") or "").lower():
                continue
            if release_year and m.get("release_year") != release_year:
                continue
            filtered.append(m)

        # Optional sorting
        if sort_by:
            filtered.sort(
                key=lambda x: (x.get(sort_by) is None, x.get(sort_by)),
                reverse=sort_desc,
            )

        total = len(filtered)
        page = filtered[skip : skip + limit]
        return [MovieOut.model_validate(_movie_to_dict(m)) for m in page], total
