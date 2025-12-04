from __future__ import annotations

import csv
import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict

from backend import settings
from backend.schemas.reviews import ReviewOut

# Config
BASE_PATH = os.getenv("MOVIE_DATA_PATH", str(settings.MOVIE_DATA_PATH))

CSV_HEADERS = [
    "Date of Review",
    "username",
    "Usefulness Vote",
    "Total Votes",
    "User's Rating out of 10",
    "Review Title",
    "Review",
    "review_id",
    "updated_at",
]

DATE_INPUT_FORMATS = ["%d %B %Y", "%d %b %y", "%Y-%m-%d"]


# Helpers
def _movie_dir(movie_name: str) -> str:
    safe = movie_name.strip().replace("/", "_")
    return os.path.join(BASE_PATH, safe)


def _movie_csv_path(movie_name: str) -> str:
    return os.path.join(_movie_dir(movie_name), "movieReviews.csv")


def _index_path(movie_name: str) -> str:
    return os.path.join(_movie_dir(movie_name), "index.json")


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def _parse_date(s: str) -> datetime:
    """Parse CSV date formats with fallback."""
    s = (s or "").strip()
    for fmt in DATE_INPUT_FORMATS:
        try:
            return datetime.strptime(s, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return datetime.now(timezone.utc)


def _format_date(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.strftime("%d %B %Y")


def _generate_uuid(movie_name: str, username: str, created_at: datetime) -> str:
    key = f"{movie_name}||{username}||{created_at.isoformat()}"
    return str(uuid.uuid5(uuid.NAMESPACE_URL, key))


# Row parsing helpers
def _parse_username(row: Dict[str, str]) -> str:
    return (row.get("username") or row.get("User") or "").strip()


def _parse_created_at(row: Dict[str, str]) -> datetime:
    return _parse_date(row.get("Date of Review", ""))


def _parse_review_id(
    movie_name: str, username: str, created_at: datetime, row: Dict[str, str]
) -> str:
    rid = row.get("review_id", "").strip()
    return rid or _generate_uuid(movie_name, username, created_at)


def _parse_rating(row: Dict[str, str]) -> int:
    raw = row.get("User's Rating out of 10", "")
    try:
        return int(raw.strip() or 0)
    except Exception:
        return 0


def _parse_updated_at(row: Dict[str, str], created_at: datetime) -> datetime:
    raw = row.get("updated_at")
    if not raw:
        return created_at
    try:
        return datetime.fromisoformat(raw).replace(tzinfo=timezone.utc)
    except Exception:
        return created_at


def _clean_title(row: Dict[str, str]) -> str | None:
    title = row.get("Review Title")
    if not title:
        return None
    title = title.strip()
    return title if title else None


def _clean_comment(row: Dict[str, str]) -> str | None:
    comment = row.get("Review")
    if not comment:
        return None
    comment = comment.strip()
    if not comment:
        return None
    return comment[:2000]


# Row -> Dict
def _row_to_dict(movie_name: str, row: Dict[str, str]) -> Dict[str, Any]:
    username = _parse_username(row)
    created_at = _parse_created_at(row)
    review_id = _parse_review_id(movie_name, username, created_at, row)
    rating = _parse_rating(row)
    updated_at = _parse_updated_at(row, created_at)
    title = _clean_title(row)
    comment = _clean_comment(row)

    return {
        "review_id": review_id,
        "movie_name": movie_name,
        "username": username,
        "rating": rating,
        "title_review": title,
        "comment": comment,
        "created_at": created_at,
        "updated_at": updated_at,
        "usefulness": int(row.get("Usefulness Vote", 0) or 0),
        "total_votes": int(row.get("Total Votes", 0) or 0),
    }


def _dict_to_row(d: Dict[str, Any]) -> Dict[str, str]:
    created_at = d["created_at"]
    updated_at = d["updated_at"]

    return {
        "Date of Review": _format_date(created_at),
        "username": d.get("username", ""),
        "Usefulness Vote": str(d.get("usefulness", 0)),
        "Total Votes": str(d.get("total_votes", 0)),
        "User's Rating out of 10": str(d.get("rating", "")),
        "Review Title": d.get("title_review") or "",
        "Review": d.get("comment") or "",
        "review_id": d.get("review_id", ""),
        "updated_at": updated_at.isoformat(),
    }


# Index helpers
def _load_index(movie: str) -> Dict[str, Any]:
    path = _index_path(movie)
    if not os.path.exists(path):
        return {"by_id": {}, "source_mtime": 0}

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"by_id": {}, "source_mtime": 0}


def _save_index(movie: str, idx: Dict[str, Any]) -> None:
    path = _index_path(movie)
    _ensure_dir(os.path.dirname(path))
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(idx, f, indent=2)
    os.replace(tmp, path)


def _csv_mtime(movie: str) -> float:
    path = _movie_csv_path(movie)
    return os.path.getmtime(path) if os.path.exists(path) else 0.0


# Repository
class CSVReviewRepo:

    # ---------- LIST ----------
    def list_by_movie(self, movie: str, limit=50, cursor=0, min_rating=None):
        path = _movie_csv_path(movie)
        if not os.path.exists(path):
            return [], None

        with open(path, newline="", encoding="utf-8") as csvfile:
            reader = list(csv.DictReader(csvfile))

        filtered = []
        for row in reader:
            d = _row_to_dict(movie, row)
            if min_rating is not None and d["rating"] < min_rating:
                continue
            filtered.append(d)

        # Pagination slice
        page = filtered[cursor : cursor + limit]
        next_cursor = cursor + limit if cursor + limit < len(filtered) else None

        return [ReviewOut.model_validate(d) for d in page], next_cursor

    # ---------- GET by ID ----------
    def get_review_by_id(self, movie: str, review_id: str):
        idx = self._ensure_index(movie)
        pos = idx["by_id"].get(review_id)
        if pos is None:
            return None

        path = _movie_csv_path(movie)
        with open(path, newline="", encoding="utf-8") as f:
            reader = list(csv.DictReader(f))
            if pos < len(reader):
                return ReviewOut.model_validate(_row_to_dict(movie, reader[pos]))
        return None

    # ---------- GET by USER ----------
    def get_review_by_user(self, movie: str, username: str):
        path = _movie_csv_path(movie)
        print("DEBUG READING FROM:", path)
        if not os.path.exists(path):
            return None

        with open(path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row.get("username", "").strip() == username:
                    return ReviewOut.model_validate(_row_to_dict(movie, row))

        return None

    # ---------- CREATE ----------
    def create(self, review: ReviewOut):
        d = review.model_dump()
        row = _dict_to_row(d)

        path = _movie_csv_path(review.movie_name)
        _ensure_dir(os.path.dirname(path))

        header_line = ",".join(CSV_HEADERS)

        # If file does not exist → create & write header
        if not os.path.exists(path):
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
                writer.writeheader()
                writer.writerow(row)
            self._ensure_index(review.movie_name)
            return review

        # If file exists → open & check first line
        with open(path, "r+", newline="", encoding="utf-8") as f:
            first_line = f.readline().strip()

            # Move pointer to end for append
            f.seek(0, os.SEEK_END)

            writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)

            # Case 1: empty file → write header
            if not first_line:
                writer.writeheader()

            # Case 2: header mismatch (e.g., Kaggle CSV)
            elif first_line != header_line:
                # rewrite entire file: write correct header + keep existing rows
                f.seek(0)
                old_rows = list(csv.DictReader(f, fieldnames=None))
                f.seek(0)
                f.truncate()
                writer.writeheader()
                for old in old_rows:
                    writer.writerow(old)

            # Now append our row
            writer.writerow(row)

        self._ensure_index(review.movie_name)
        return review

    # ---------- UPDATE ----------
    def update(self, review: ReviewOut):
        movie = review.movie_name
        path = _movie_csv_path(movie)
        if not os.path.exists(path):
            raise KeyError("Review not found")

        new_rows = []
        found = False

        d = review.model_dump()

        with open(path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row.get("review_id") == review.review_id:
                    new_rows.append(_dict_to_row(d))
                    found = True
                else:
                    new_rows.append(row)

        if not found:
            raise KeyError("Review not found")

        tmp = path + ".tmp"
        with open(tmp, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
            writer.writeheader()
            writer.writerows(new_rows)

        os.replace(tmp, path)
        self._ensure_index(movie)
        return review

    # ---------- DELETE ----------
    def delete(self, movie: str, review_id: str):
        path = _movie_csv_path(movie)
        if not os.path.exists(path):
            raise KeyError("Review not found")

        new_rows = []
        removed = False

        with open(path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row.get("review_id") == review_id:
                    removed = True
                else:
                    new_rows.append(row)

        if not removed:
            raise KeyError("Review not found")

        tmp = path + ".tmp"
        with open(tmp, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
            writer.writeheader()
            writer.writerows(new_rows)

        os.replace(tmp, path)
        self._ensure_index(movie)

    # ---------- INDEX REBUILD ----------
    def _ensure_index(self, movie: str):
        csv_m = _csv_mtime(movie)
        idx = _load_index(movie)

        if idx.get("source_mtime") == csv_m:
            return idx

        by_id = {}
        path = _movie_csv_path(movie)

        if os.path.exists(path):
            with open(path, newline="", encoding="utf-8") as f:
                for i, row in enumerate(csv.DictReader(f)):
                    d = _row_to_dict(movie, row)
                    by_id[d["review_id"]] = i

        idx = {"by_id": by_id, "source_mtime": csv_m}
        _save_index(movie, idx)
        return idx
