from __future__ import annotations

import csv
import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from schemas.reviews import ReviewOut

# Config & CSV columns to match raw data structure
BASE_PATH = os.getenv("MOVIE_DATA_PATH", "data/movies")
CSV_HEADERS = [
    "Date of Review",
    "User",
    "Usefulness Vote",
    "Total Votes",
    "User's Rating out of 10",
    "Review Title",
    "id",  # added by our system
]

DATE_INPUT_FORMATS = ["%d %B %Y", "%d %b %y", "%Y-%m-%d"]


# Helpers
def _movie_dir(movie_id: str) -> str:
    '''Return the directory path on disk where a movie's CSV and index live'''
    safe = movie_id.strip().replace("/", "_")
    return os.path.join(BASE_PATH, safe)


def _movie_csv_path(movie_id: str) -> str:
    '''Compute the full CSV file path for a given movie'''
    return os.path.join(_movie_dir(movie_id), "movieReviews.csv")


def _index_path(movie_id: str) -> str:
    '''Compute the full JSON index file path for a given movie'''
    return os.path.join(_movie_dir(movie_id), "index.json")


def _ensure_dir(path: str) -> None:
    '''Ensure a directory exists, creating it recursively if necessary.'''
    os.makedirs(path, exist_ok=True)


def _parse_date(s: str) -> datetime:
    '''Parse a date string'''
    s = (s or "").strip()
    for fmt in DATE_INPUT_FORMATS:
        try:
            return datetime.strptime(s, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return datetime.now(timezone.utc)  # Fallback to now if parsing fails


def _format_date_for_csv(dt: datetime) -> str:
    '''Format a datetime for CSV output as 'DD Month YYYY' (e.g., '27 October 2025')'''
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.strftime("%d %B %Y")


def _stable_uuid5(movie_id: str, user: str, date_str: str, title: str) -> str:
    '''Generate a stable, name-based UUIDv5 for a review row'''
    key = f"{movie_id}||{user}||{date_str}||{title}"
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


def _csv_mtime(movie_id: str) -> float:
    '''Get the last modified time of the movie's CSV file'''
    csv_path = _movie_csv_path(movie_id)
    return os.path.getmtime(csv_path) if os.path.exists(csv_path) else 0.0


# Model mapping
def _row_to_dict(movie_id: str, row: Dict[str, str]) -> Dict[str, Any]:
    '''Convert a CSV row to a dictionary suitable for ReviewOut'''
    date_str = row.get("Date of Review", "").strip()
    user = row.get("User", "").strip()
    usefulness = row.get("Usefulness Vote", "").strip()
    total_votes = row.get("Total Votes", "").strip()
    title = row.get("Review Title", "").strip()
    review_id = row.get("id", "").strip()

    # rating
    raw_rating = row.get("User's Rating out of 10", "").strip() or ""
    try:
        rating = int(raw_rating)
    except Exception:
        rating = None

    create_dt = _parse_date(date_str)
    if not review_id:
        review_id = _stable_uuid5(movie_id, user, date_str, title)

    return {
        "id": str(review_id or ""),
        "movie_id": movie_id,
        "user_id": user or "",
        "rating": rating or 0,
        "comment": title if title else None,
        "created_at": create_dt,
        "updated_at": create_dt,
        "csv_usefulness_vote": usefulness,
        "csv_total_votes": total_votes,
    }


def _dict_to_row(data: Dict[str, Any]) -> Dict[str, str]:
    '''Convert a ReviewOut-like dictionary to a CSV row dictionary'''
    # created date to csv date
    created_iso = data.get("created_at")
    if isinstance(created_iso, datetime):
        created_dt = created_iso
    else:
        try:
            created_dt = (
                datetime.fromisoformat(created_iso)
                if created_iso
                else datetime.now(timezone.utc)
            )
        except Exception:
            created_dt = datetime.now(timezone.utc)

    return {
        "Date of Review": _format_date_for_csv(created_dt),
        "User": data.get("user_id", ""),
        "Usefulness Vote": data.get("csv_usefulness_vote", ""),
        "Total Votes": data.get("csv_total_votes", ""),
        "User's Rating out of 10": (
            data.get("rating", "") if data.get("rating") is not None else ""
        ),
        "Review Title": data.get("comment", "") or "",
        "id": data.get("id", "") or str(uuid.uuid4()),
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
        movie_id: str,
        limit: int = 50,
        cursor: Optional[int] = None,
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
        path = _movie_csv_path(movie_id)
        if not os.path.exists(path):
            return [], None

        start_row = cursor or 0
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
                d = _row_to_dict(movie_id, row)

                if min_rating is not None and (
                    d["rating"] is None or d["rating"] < min_rating
                ):
                    continue

                out.append(ReviewOut.model_validate(d))

                if len(out) >= limit:
                    _peek = next(reader, None)  # consumed locally; harmless
                    next_cursor = row_index if _peek is not None else None
                    break

        return out, next_cursor

    # Access with index
    def _ensure_index(self, movie_id: str) -> Dict[str, Any]:
        '''Load the index, if the CSV mtime differs, rebuild and persist it.'''
        csv_mtime = _csv_mtime(movie_id)
        idx = _load_index(movie_id)

        if idx.get("source_mtime", 0.0) == csv_mtime:
            return idx

        # Rebuild index
        by_id: Dict[str, int] = {}
        by_user: Dict[str, str] = {}
        path = _movie_csv_path(movie_id)
        if os.path.exists(path):
            with open(path, newline="", encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile)
                for i, row in enumerate(reader):
                    d = _row_to_dict(movie_id, row)
                    by_id[str(d["id"])] = i  # row number
                    if d["user_id"] and d["user_id"] not in by_user:
                        by_user[d["user_id"]] = d["id"]
        idx = {
            "by_id": by_id,
            "by_user": by_user,
            "source_mtime": csv_mtime,
        }
        _save_index(movie_id, idx)
        return idx

    def get_by_id(self, movie_id: str, review_id: str) -> Optional[ReviewOut]:
        '''Get a single review by its ID using the index for fast lookup'''
        review_id = str(review_id).strip()
        idx = self._ensure_index(movie_id)
        pos = idx["by_id"].get(review_id)  # position (row index of the review in CSV
        if pos is None:
            return None
        path = _movie_csv_path(movie_id)
        with open(path, newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            # Iterate to the target row
            for i, row in enumerate(reader):
                if i == pos:
                    d = _row_to_dict(movie_id, row)
                    return ReviewOut.model_validate(d)
        return None

    def get_by_user(self, movie_id: str, user_id: str) -> Optional[ReviewOut]:
        '''Get the first review by a given user'''
        idx = self._ensure_index(movie_id)
        review_id = idx["by_user"].get(user_id)
        if not review_id:
            return None
        return self.get_by_id(movie_id, review_id)

    # Create/Update/Delete operations
    def create(self, review: ReviewOut) -> ReviewOut:
        '''Append a new review to the movie CSV file'''
        dir_path = _movie_dir(review.movie_id)
        _ensure_dir(dir_path)
        path = _movie_csv_path(review.movie_id)
        exists = os.path.exists(path)

        row = _dict_to_row(review.model_dump())
        with open(path, "a", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=CSV_HEADERS)
            if not exists:
                writer.writeheader()
            writer.writerow(row)

        # Update index
        self._ensure_index(review.movie_id)  # it will detect mtime and rebuild
        return review

    def update(self, review: ReviewOut) -> ReviewOut:
        '''Update an existing review by rewriting the CSV file'''
        movie_id = review.movie_id
        path = _movie_csv_path(movie_id)
        if not os.path.exists(path):
            raise KeyError("Review does not exist")

        rows: List[Dict[str, str]] = []
        found = False
        with open(path, newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if (row.get("id") or "").strip() == review.id:
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
        self._ensure_index(movie_id)  # it will detect mtime and rebuild
        return review

    def delete(self, movie_id: str, review_id: str) -> None:
        '''Delete a review by id by rewriting the CSV file, rebuild index'''
        review_id = str(review_id).strip()
        path = _movie_csv_path(movie_id)
        if not os.path.exists(path):
            return

        rows: List[Dict[str, str]] = []
        removed = False
        with open(path, newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if (row.get("id") or "").strip() == review_id:
                    removed = True
                    continue  # skip this row
                rows.append(row)

        if not removed:
            return  # nothing to delete

        tmp = path + ".tmp"
        with open(tmp, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=CSV_HEADERS)
            writer.writeheader()
            writer.writerows(rows)
        os.replace(tmp, path)

        # Rebuild index
        self._ensure_index(movie_id)  # it will detect mtime and rebuild


# .. note::
#    Parts of this file comments and basic scaffolding were auto-completed by VS Code.
#    Core logic and subsequent modifications were implemented by the author(s).
