from __future__ import annotations

import csv
import json
import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from backend import settings
from backend.schemas.reviews import ReviewOut
from backend.utils.datetime_utils import ensure_timezone_aware, now_utc, parse_iso_like

# Config & CSV columns to match raw data structure
# Prefer explicit env var (tests monkeypatch this), otherwise fall back to settings
BASE_PATH = os.getenv("MOVIE_DATA_PATH", str(settings.MOVIE_DATA_PATH))
CSV_HEADERS = [
    "Date of Review",
    "User",
    "Usefulness Vote",
    "Total Votes",
    "User's Rating out of 10",
    "Review Title",
    "Review",
    "review_id",  # added by our system
]

DATE_INPUT_FORMATS = ["%d %B %Y", "%d %b %y", "%Y-%m-%d"]


# Helpers
def _movie_dir(movie_name: str) -> str:
    '''Return the directory path on disk where a movie's CSV and index live'''
    safe = movie_name.strip().replace("/", "_")
    return os.path.join(BASE_PATH, safe)


def _movie_csv_path(movie_name: str) -> str:
    '''Compute the full CSV file path for a given movie'''
    return os.path.join(_movie_dir(movie_name), "movieReviews.csv")


def _index_path(movie_name: str) -> str:
    '''Compute the full JSON index file path for a given movie'''
    return os.path.join(_movie_dir(movie_name), "index.json")


def _ensure_dir(path: str) -> None:
    '''Ensure a directory exists, creating it recursively if necessary.'''
    os.makedirs(path, exist_ok=True)


def _parse_date(s: str):
    '''Parse a date string using datetime_utils'''
    s = (s or "").strip()
    # Try parse_iso_like first
    dt = parse_iso_like(s)
    if dt:
        return dt
    # Fallback to now if parsing fails
    return now_utc()


def _format_date_for_csv(dt) -> str:
    '''Format a datetime for CSV output as 'DD Month YYYY' (e.g., '27 October 2025')'''
    dt = ensure_timezone_aware(dt)
    return dt.strftime("%d %B %Y")


def _stable_uuid5(movie_name: str, user: str, date_str: str, title: str) -> str:
    '''Generate a stable, name-based UUIDv5 for a review row'''
    key = f"{movie_name}||{user}||{date_str}||{title}"
    return str(uuid.uuid5(uuid.NAMESPACE_URL, key))


# Lightweight index per movie
#   - by_id
#   - by_user
#   - source_mtime


def _load_index(movie_id: str) -> Dict[str, Any]:
    '''Load the per-movie lightweight index from disk'''
    idx_path = _index_path(movie_id)
    if not os.path.exists(idx_path):
        return {"by_id": {}, "by_user": {}, "source_mtime": 0}
    try:
        with open(idx_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"by_id": {}, "by_user": {}, "source_mtime": 0}


def _save_index(movie_id: str, index: Dict[str, Any]) -> None:
    '''Save the per-movie lightweight index to disk'''
    idx_path = _index_path(movie_id)
    _ensure_dir(os.path.dirname(idx_path))
    tmp = idx_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    os.replace(tmp, idx_path)


def _csv_mtime(movie_name: str) -> float:
    '''Get the last modified time of the movie's CSV file'''
    csv_path = _movie_csv_path(movie_name)
    return os.path.getmtime(csv_path) if os.path.exists(csv_path) else 0.0


# Model mapping
def _row_to_dict(movie_name: str, row: Dict[str, str]) -> Dict[str, Any]:
    '''Convert a CSV row to a dictionary suitable for ReviewOut'''
    date_str = row.get("Date of Review", "").strip()
    user = row.get("User", "").strip()
    usefulness = row.get("Usefulness Vote", "").strip()
    total_votes = row.get("Total Votes", "").strip()
    title = row.get("Review Title", "").strip()
    review = row.get("Review", "").strip()

    # rating
    raw_rating = row.get("User's Rating out of 10", "").strip() or ""
    try:
        rating = int(raw_rating)
    except Exception:
        rating = None

    # Prefer stored ID, fallback to stable ID
    review_id = row.get("review_id", "").strip()
    if not review_id:
        review_id = _stable_uuid5(movie_name, user, date_str, title)

    return {
        "review_id": review_id,
        "movie_name": movie_name,
        "username": user or "",
        "rating": rating or 0,
        "title_review": title or "",
        "comment": review or "",
        "created_at": _parse_date(date_str),
        "updated_at": now_utc(),
        "usefulness": usefulness,
        "total_votes": total_votes,
    }


def _dict_to_row(data: Dict[str, Any]) -> Dict[str, str]:
    '''Convert a ReviewOut-like dictionary to a CSV row dictionary'''
    # created date to csv date
    created_iso = data.get("created_at")
    if isinstance(created_iso, datetime):
        created_dt = created_iso
    else:
        created_dt = parse_iso_like(created_iso) or now_utc()
    return {
        "Date of Review": _format_date_for_csv(created_dt),
        "User": data.get("username", ""),
        "Usefulness Vote": str(data.get("usefulness", 0)),
        "Total Votes": str(data.get("total_votes", 0)),
        "User's Rating out of 10": (
            str(data.get("rating")) if data.get("rating") is not None else ""
        ),
        "Review Title": data.get("title_review", "") or "",
        "Review": data.get("comment", "") or "",
        "review_id": data.get("review_id", "")
        or _stable_uuid5(
            data.get("movie_id", ""),
            data.get("username", ""),
            data.get("created_at", ""),
            data.get("title_review", ""),
        ),
    }


# Public repository
class CSVReviewRepo:
    '''
    CSV-backed review repository that supports:
        - Streaming the movie list avoiding full data load
        - Per movie lightweight index (id -> row, user -> id) with staleness detection
        - Append only create, single-pass rewrite for update/delete operations
    '''

    # List reviews
    def list_by_movie(
        self,
        movie_name: str,
        limit: int = 50,
        cursor: Optional[int] = 0,
        min_rating: Optional[int] = None,
    ) -> tuple[List[ReviewOut], Optional[int]]:
        '''List reviews for a given movie with pagination and optional rating filter
        Functional Logic:
        1. Open the CSV file containing the corresponding movie.
        2. Skip the row before the cursor and start reading from the target position.
        3. Convert each CSV row into a ReviewOut object.
        4. If min_rating is set, filter out reviews with low ratings.
        5. Stop reading when the limit is reached or the end of the file is reached.
        6. Return the list of reviews for this page and the starting point for the next page (next_cursor).
        '''
        '''TODO (50k rows):
          For very large files as we designed (≈50,000+), consider returning a smaller default limit (e.g., 25),
          and/or moving to an append-log + compaction model.
        '''
        path = _movie_csv_path(movie_name)
        if not os.path.exists(path):
            return [], None

        start_row: int = cursor if cursor is not None else 0
        out: List[ReviewOut] = []
        next_cursor: Optional[int] = None

        with open(path, newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            # Skip to start_row
            for _ in range(start_row):
                try:
                    next(reader)
                except StopIteration:
                    return [], None  # Reached EOF before start_row

            row_index = start_row
            for row in reader:
                row_index += 1
                d = _row_to_dict(movie_name, row)

                if min_rating is not None and (
                    d["rating"] is None or d["rating"] < min_rating
                ):
                    continue

                if len(d["comment"]) > 2000:
                    d["comment"] = d["comment"][:1997] + "..."
                out.append(ReviewOut.model_validate(d))

                if len(out) >= limit:
                    _peek = next(reader, None)  # consumed locally; harmless
                    next_cursor = row_index if _peek is not None else None
                    break

        return out, next_cursor

    # Access with index
    def _ensure_index(self, movie_name: str) -> Dict[str, Any]:
        '''Load the index, if the CSV mtime differs, rebuild and persist it.'''
        csv_mtime = _csv_mtime(movie_name)
        idx = _load_index(movie_name)

        if idx.get("source_mtime", 0.0) == csv_mtime:
            return idx

        # Rebuild index
        by_id: Dict[str, int] = {}
        by_user: Dict[str, str] = {}
        path = _movie_csv_path(movie_name)
        if os.path.exists(path):
            with open(path, newline="", encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile)
                for i, row in enumerate(reader):
                    d = _row_to_dict(movie_name, row)
                    by_id[str(d["review_id"])] = i  # row number
                    if d["username"] and d["username"] not in by_user:
                        by_user[d["username"]] = d["review_id"]
        idx = {
            "by_id": by_id,
            "by_user": by_user,
            "source_mtime": csv_mtime,
        }
        _save_index(movie_name, idx)
        return idx

    def get_review_by_id(self, movie_name: str, review_id: str) -> Optional[ReviewOut]:
        """Get a single review by its ID using the index for fast lookup"""
        idx = self._ensure_index(movie_name)
        pos = idx.get("by_id", {}).get(review_id)
        if pos is None:
            return None

        path = _movie_csv_path(movie_name)
        if not os.path.exists(path):
            return None  # prevent crash if CSV file missing

        with open(path, newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for i, row in enumerate(reader):
                if i == pos:
                    return ReviewOut.model_validate(_row_to_dict(movie_name, row))
        return None

    def get_review_by_user(self, movie_name: str, user_id: str) -> Optional[ReviewOut]:
        '''Get the first review by a given user'''
        idx = self._ensure_index(movie_name)
        review_id = idx["by_user"].get(user_id)
        if not review_id:
            return None
        return self.get_review_by_id(movie_name, review_id)

    # Create/Update/Delete operations
    def create(self, review: ReviewOut) -> ReviewOut:
        '''Append a new review to the movie CSV file'''
        dir_path = _movie_dir(review.movie_name)
        _ensure_dir(dir_path)
        path = _movie_csv_path(review.movie_name)
        exists = os.path.exists(path)

        row = _dict_to_row(review.model_dump())
        with open(path, "a", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=CSV_HEADERS)
            if not exists:
                writer.writeheader()
            writer.writerow(row)

        # Update index
        self._ensure_index(review.movie_name)  # it will detect mtime and rebuild
        return review

    def update(self, review: ReviewOut) -> ReviewOut:
        '''Update an existing review by rewriting the CSV file'''
        movie_name = review.movie_name
        path = _movie_csv_path(movie_name)
        if not os.path.exists(path):
            raise KeyError("Review does not exist")

        rows: List[Dict[str, str]] = []
        found = False
        with open(path, newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if (row.get("User") or "").strip() == review.username:
                    # Replace with updated row
                    new_row = _dict_to_row(review.model_dump())
                    rows.append(new_row)
                    found = True
                else:
                    rows.append(row)

        if not found:
            raise KeyError("Review not found for update")

        tmp = path + ".tmp"
        with open(tmp, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=CSV_HEADERS)
            writer.writeheader()
            writer.writerows(rows)
        os.replace(tmp, path)

        # Rebuild index
        self._ensure_index(movie_name)  # it will detect mtime and rebuild
        return review

    def delete(self, movie_name: str, review_id: str) -> None:
        '''Delete a review by id by rewriting the CSV file, rebuild index'''
        review_id = str(review_id).strip()
        path = _movie_csv_path(movie_name)
        if not os.path.exists(path):
            return

        rows: List[Dict[str, str]] = []
        removed = False
        with open(path, newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if (row.get("review_id") or "").strip() == review_id:
                    removed = True
                    continue  # skip this row
                rows.append(row)

        if not removed:
            raise KeyError("Review not found for delete")

        tmp = path + ".tmp"
        with open(tmp, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=CSV_HEADERS)
            writer.writeheader()
            writer.writerows(rows)
        os.replace(tmp, path)

        # Rebuild index
        self._ensure_index(movie_name)  # it will detect mtime and rebuild

    def get_all_reviews_flat(self) -> List[ReviewOut]:
        """
        Retrieve all reviews across all movies.
        This is an expensive operation intended for analytics.
        """
        all_reviews: List[ReviewOut] = []
        if not os.path.exists(BASE_PATH):
            return []

        # Iterate over all subdirectories in BASE_PATH
        for entry in os.listdir(BASE_PATH):
            full_path = os.path.join(BASE_PATH, entry)
            if os.path.isdir(full_path):
                # We assume the directory name is the movie_name (sanitized)
                movie_name = entry

                reviews, _ = self.list_by_movie(movie_name, limit=1000000)
                all_reviews.extend(reviews)
        return all_reviews
