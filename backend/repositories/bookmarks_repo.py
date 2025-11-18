from __future__ import annotations

import csv
import json
import os
import uuid
from datetime import datetime, timezone
from typing import Dict, List
from uuid import UUID

from backend.schemas.bookmarks import BookmarkCreate, BookmarkOut

# Configuration
BOOKMARKS_PATH = os.getenv("BOOKMARKS_PATH", "data/bookmarks.json")
BOOKMARKS_EXPORT_DIR = os.getenv("BOOKMARKS_EXPORT_DIR", "data/exports")


# Helpers
def _to_iso(dt: datetime) -> str:
    """Convert datetime to UTC ISO-8601 string."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat()


def _serialize_for_json(obj: Dict) -> Dict:
    """Convert datetime fields to ISO strings for JSON/CSV writing."""
    out = dict(obj)

    # Ensure ID exists and stringify UUID objects
    if "id" not in out or not out["id"]:
        out["id"] = str(uuid.uuid4())
    elif isinstance(out["id"], UUID):
        out["id"] = str(out["id"])

    # Normalize datetimes
    if isinstance(out.get("created_at"), datetime):
        out["created_at"] = _to_iso(out["created_at"])
    if isinstance(out.get("updated_at"), datetime):
        out["updated_at"] = _to_iso(out["updated_at"])
    return out


# Repository Implementation
class JSONBookmarkRepo:
    '''
    Repository for managing user bookmarks stored in a JSON file.
    Provides CRUD operations and supports exporting to CSV.
    '''

    def __init__(self, storage_path: str = BOOKMARKS_PATH):
        '''Initialize repository with file path and ensure directory exists.'''
        self.storage_path = storage_path
        dirpath = os.path.dirname(self.storage_path) or "."
        os.makedirs(dirpath, exist_ok=True)
        if not os.path.exists(self.storage_path):
            with open(self.storage_path, 'w', encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False, indent=2)

    # Internal helpers
    def _load(self) -> List[Dict]:
        '''Load all bookmarks from JSON file.'''
        if not os.path.exists(self.storage_path):
            return []
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            # Corrupted or empty file
            return []

    def _save(self, bookmarks: List[Dict]) -> None:
        '''Write all bookmark data back to JSON file.'''
        # Make sure directory exists
        dirpath = os.path.dirname(self.storage_path) or "."
        os.makedirs(dirpath, exist_ok=True)

        serialized = [_serialize_for_json(b) for b in bookmarks]

        tmp_path = self.storage_path + ".tmp"
        try:
            # Write to a temp file first
            with open(tmp_path, 'w', encoding="utf-8") as f:
                json.dump(serialized, f, ensure_ascii=False, indent=2)
                f.flush()  # flush internal buffer
                os.fsync(f.fileno())  # flush to disk

            # Atomically replace the original file
            os.replace(tmp_path, self.storage_path)
        finally:
            # Clean up temp file if it still exists
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass

    # CRUD Operations
    def list_all(self) -> List[BookmarkOut]:
        '''Return all bookmark data as BookmarkOut instances.'''
        data = self._load()
        return [BookmarkOut.model_validate(b) for b in data]

    def create(self, bookmark_in: BookmarkCreate) -> BookmarkOut:
        '''Add a new bookmark entry (system generates id and timestamps).'''

        # System-generated timestamp
        now = datetime.now(timezone.utc)
        payload = {
            "id": uuid.uuid4(),
            "user_id": bookmark_in.user_id,
            "movie_id": bookmark_in.movie_id,
            "created_at": now,
            "updated_at": now,
        }

        data = self._load()
        data.append(payload)  # raw python objects, no serialization here
        self._save(data)
        return BookmarkOut.model_validate(payload)

    def get_by_user(self, user_id: str) -> List[BookmarkOut]:
        '''Retrieve all bookmarks for a specific user.'''
        data = self._load()
        results = [
            BookmarkOut.model_validate(b) for b in data if b.get("user_id") == user_id
        ]
        return results

    def delete(self, bookmark_id: str) -> bool:
        '''Delete a bookmark by its ID. Returns True if deleted, False if not found.'''
        if isinstance(bookmark_id, UUID):
            bookmark_id = str(bookmark_id)

        data = self._load()
        new_data = [b for b in data if b.get("id") != bookmark_id]

        if len(new_data) == len(data):
            return False

        self._save(new_data)
        return True

    # Export Functionality
    def export_to_csv(self, export_dir: str = BOOKMARKS_EXPORT_DIR) -> str:
        '''Export all bookmarks to a CSV file. Returns the file path.'''
        data = self._load()
        if not data:
            raise ValueError("No bookmarks available for export.")

        rows = data
        os.makedirs(export_dir, exist_ok=True)

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        export_path = os.path.join(export_dir, f"bookmarks_export_{timestamp}.csv")
        tmp_path = export_path + ".tmp"

        try:
            # Write to a temp file first
            with open(tmp_path, 'w', newline='', encoding="utf-8") as csvfile:
                fieldnames = ["id", "user_id", "movie_id", "created_at", "updated_at"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
                csvfile.flush()  # flush internal buffer
                os.fsync(csvfile.fileno())  # flush to disk

            # Atomically replace the original file
            os.replace(tmp_path, export_path)
        finally:
            # Clean up temp file if it still exists
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass

        return export_path
