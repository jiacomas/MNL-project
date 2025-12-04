from __future__ import annotations

import csv
import json
import os
import uuid
from typing import Any, Dict, List, Optional, Tuple

from backend import settings
from backend.schemas.movies import MovieCreate, MovieOut, MovieUpdate
from backend.utils.datetime_utils import (
    ensure_timezone_aware,
    now_utc,
    parse_iso_like,
    to_iso_string,
)

# Configuration from centralized settings, allow env overrides (useful for tests)
MOVIES_CSV_PATH = os.getenv("MOVIES_CSV_PATH", str(settings.MOVIES_CSV_PATH))
MOVIES_JSON_PATH = os.getenv("MOVIES_JSON_PATH", str(settings.MOVIES_JSON_PATH))
EXTERNAL_METADATA_DIR = os.getenv(
    "EXTERNAL_METADATA_DIR", str(settings.EXTERNAL_METADATA_DIR)
)


def _ensure_data_dir() -> None:
    os.makedirs(os.path.dirname(MOVIES_CSV_PATH), exist_ok=True)
    os.makedirs(EXTERNAL_METADATA_DIR, exist_ok=True)


def _parse_date_field(date_str: Any):
    """Parse various date representations to an aware datetime.

    Uses `parse_iso_like` and falls back to current UTC time.
    """
    dt = parse_iso_like(date_str)
    return dt or now_utc()


def _safe_to_int(value: Any) -> Optional[int]:
    """Safely parse an int-like value using existing helpers."""
    try:
        return _parse_int_like(value)
    except Exception:
        return None


def _safe_to_float(value: Any) -> Optional[float]:
    """Safely parse a float, tolerant of commas and bad input."""
    if value is None:
        return None
    try:
        return float(str(value).replace(",", ""))
    except Exception:
        return None


def _process_csv_row(row: Dict[str, Any]) -> Dict[str, Any]:
    """Convert csv row strings to correct types (int/float/datetime)."""
    movie_data = {k: (v if v else None) for k, v in row.items()}

    # Numeric fields (use small helpers to keep complexity low)
    # datePublished is a string (e.g. "2019-04-26"), not an int
    movie_data["duration"] = _safe_to_int(movie_data.get("duration"))
    movie_data["movieIMDbRating"] = _safe_to_float(movie_data.get("movieIMDbRating"))

    # Dates
    movie_data["created_at"] = _parse_date_field(movie_data.get("created_at"))
    movie_data["updated_at"] = _parse_date_field(movie_data.get("updated_at"))

    # Coerce/normalize additional fields to match Movie schema expectations
    try:
        _normalize_movie_fields(movie_data)
    except Exception:
        pass

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
    """Save a list of movie dicts to MOVIES_CSV_PATH"""
    _ensure_data_dir()

    fieldnames: List[str] = []
    seen: set = set()
    for m in movies:
        if not isinstance(m, dict):
            continue
        for k in m.keys():
            if k not in seen:
                fieldnames.append(k)
                seen.add(k)

    with open(MOVIES_CSV_PATH, "w", encoding="utf-8", newline="") as f:
        if not fieldnames:
            # create an empty file and return
            f.truncate(0)
            return

        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()

        for m in movies:
            item = m.copy()
            # Convert datetime to ISO format string for saving using utils
            for d in ["created_at", "updated_at"]:
                # If already a string, keep it; otherwise convert
                if isinstance(item.get(d), str):
                    continue
                item[d] = to_iso_string(item.get(d))
            writer.writerow(item)


def _load_movies_from_json() -> List[Dict[str, Any]]:
    if not os.path.exists(MOVIES_JSON_PATH):
        return []

    try:
        with open(MOVIES_JSON_PATH, "r", encoding="utf-8") as f:
            movies = json.load(f)

        normalized: List[Dict[str, Any]] = []
        for m in movies:
            if not isinstance(m, dict):
                continue

            # Normalize fields (ids, numeric parsing, etc.) before parsing dates
            try:
                _normalize_movie_fields(m)
            except Exception:
                pass

            for d in ["created_at", "updated_at"]:
                m[d] = _parse_date_field(m.get(d))

            normalized.append(m)

        return normalized
    except Exception:
        return []


def _save_movies_to_json(movies: List[Dict[str, Any]]) -> None:
    _ensure_data_dir()
    dump = []
    for m in movies:
        item = m.copy()
        for d in ["created_at", "updated_at"]:
            if isinstance(item.get(d), str):
                continue
            item[d] = to_iso_string(item.get(d))
        dump.append(item)
    with open(MOVIES_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(dump, f, ensure_ascii=False, indent=2)


def _movie_to_dict(movie: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure timestamps are timezone-aware (UTC) & review_count exists."""
    result = movie.copy()
    now = now_utc()

    for d in ["created_at", "updated_at"]:
        val = result.get(d)
        if not isinstance(val, type(now)):
            result[d] = now
        else:
            result[d] = ensure_timezone_aware(val)

    # Ensures review_count is always present for MovieOut validation
    result["review_count"] = result.get("review_count") or 0
    return result


def _parse_suffix_number(s: str) -> Optional[int]:
    """Parse suffixes like '1.2K' or '3M' into integers, return None if not applicable."""
    if not s:
        return None
    s = s.strip()
    if s == "":
        return None
    last = s[-1].upper()
    if last not in ("K", "M"):
        return None
    try:
        num = float(s[:-1].replace(",", ""))
        return int(num * (1_000 if last == "K" else 1_000_000))
    except Exception:
        return None


def _clean_numeric_string(s: str) -> str:
    """Keep only digits, dot and minus from a numeric-like string."""
    return "".join(ch for ch in s if ch.isdigit() or ch in "-.")


def _parse_int_like(value: Any) -> Optional[int]:
    """Parse values like '1.8K', '2,345', '10' into integers when possible."""
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)

    s = str(value).strip()
    if s == "":
        return None

    # Try suffix parsing first (1.2K, 3M, etc.)
    parsed = _parse_suffix_number(s)
    if parsed is not None:
        return parsed

    # Remove commas then clean remaining characters
    cleaned = _clean_numeric_string(s.replace(",", ""))
    if cleaned == "" or cleaned in ("-", "."):
        return None

    try:
        if "." in cleaned:
            return int(float(cleaned))
        return int(cleaned)
    except Exception:
        return None


def _normalize_movie_fields(movie: Dict[str, Any]) -> None:
    """Normalize/coerce incoming movie dict to the shapes expected by schemas.

    - Ensure `movie_id` exists and is a string.
    - Parse 'K'/'M' suffixed numeric strings into integers for totalUserReviews etc.
    - Coerce rating-like fields to float.
    """
    # Ensure movie_id is string for MovieOut
    if movie.get("movie_id") is not None:
        movie["movie_id"] = str(movie["movie_id"])

    # Numeric fields: convert common fields to ints/floats
    int_keys = [
        "totalUserReviews",
        "totalCriticReviews",
        "totalRatingCount",
        "metaScore",
        "duration",
    ]
    for k in int_keys:
        if k in movie:
            parsed = _parse_int_like(movie.get(k))
            if k == "duration":
                movie[k] = int(parsed) if parsed is not None else None
            else:
                movie[k] = parsed

    # rating fields
    for k in ("movieIMDbRating", "rating"):
        if k in movie and movie.get(k) is not None:
            try:
                movie[k] = float(str(movie.get(k)).replace(",", ""))
            except Exception:
                movie[k] = None


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

        # Generate movie_id using UUID5 based on title (same as create_movies_data.py)
        movie_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, movie_create.title))

        # Check for duplicate ID
        for m in movies:
            if m.get("movie_id") == movie_id:
                raise ValueError(
                    f"Movie with title '{movie_create.title}' already exists"
                )

        # Create movie data with auto-generated fields
        data = movie_create.model_dump()
        now = now_utc()

        # Set auto-generated fields
        data["movie_id"] = movie_id
        data["created_at"] = now
        data["updated_at"] = now

        # Initialize calculated fields to 0
        data["movieIMDbRating"] = 0.0
        data["totalRatingCount"] = 0
        data["totalUserReviews"] = 0
        data["totalCriticReviews"] = 0
        data["metaScore"] = 0
        data["review_count"] = 0

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
                movies[i]["updated_at"] = now_utc()
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

        # Validate movie dicts into MovieOut instances, collecting those with ratings
        validated: List[MovieOut] = []
        for m in movies:
            try:
                mo = MovieOut.model_validate(_movie_to_dict(m))
            except Exception:
                continue
            if getattr(mo, "movieIMDbRating", None) is not None:
                validated.append(mo)

        # Sort by movieIMDbRating descending, then title
        validated.sort(
            key=lambda x: (x.movieIMDbRating or 0, x.title or ""), reverse=True
        )
        return validated[:limit]

    def get_recent(self, limit: int = 10) -> List[MovieOut]:
        movies = self._load_movies()
        # Use datetime.min as a fallback for missing created_at to ensure stable sort
        movies.sort(
            key=lambda x: parse_iso_like(x.get("created_at"))
            or now_utc().replace(year=1, month=1, day=1),
            reverse=True,
        )
        return [MovieOut.model_validate(_movie_to_dict(m)) for m in movies[:limit]]

    def search(  # noqa: C901
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
            # Title search (case-insensitive)
            if title and title.lower() not in (m.get("title") or "").lower():
                continue

            # Genre search (case-insensitive, partial match in movieGenres)
            if genre:
                movie_genres = (m.get("movieGenres") or "").lower()
                if genre.lower() not in movie_genres:
                    continue

            # Release year search (parse datePublished YYYY-MM-DD)
            if release_year:
                date_pub = m.get("datePublished")
                if not date_pub:
                    continue
                try:
                    # Extract year from YYYY-MM-DD
                    pub_year = int(date_pub.split("-")[0])
                    if pub_year != release_year:
                        continue
                except (ValueError, IndexError):
                    continue

            filtered.append(m)

        # Sorting
        if sort_by:
            filtered.sort(
                key=lambda x: (x.get(sort_by) is None, x.get(sort_by)),
                reverse=sort_desc,
            )

        total = len(filtered)
        page = filtered[skip : skip + limit]
        return [MovieOut.model_validate(_movie_to_dict(m)) for m in page], total
