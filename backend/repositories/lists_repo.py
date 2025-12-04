from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional
from uuid import UUID

from backend import settings
from backend.schemas.lists import ListCreate, ListOut, ListUpdate

# Configuration
LISTS_PATH = os.getenv("LISTS_PATH", os.path.join(settings.ROOT_DATA_DIR, "lists.json"))


# Helpers
def _to_iso(dt: datetime) -> str:
    """Convert datetime to UTC ISO-8601 string."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat()


def _serialize_for_json(obj: Dict) -> Dict:
    """Convert datetime fields to ISO strings for JSON writing."""
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


def _fill_missing_fields(raw: Dict) -> Dict:
    """Make loading robust against missing fields."""
    now = datetime.now(timezone.utc)
    return {
        "id": raw.get("id") or str(uuid.uuid4()),
        "user_id": raw.get("user_id"),
        "name": raw.get("name", "Untitled List"),
        "description": raw.get("description"),
        "items": raw.get("items", []),
        "created_at": raw.get("created_at", now),
        "updated_at": raw.get("updated_at", now),
    }


class JSONListRepo:
    """
    Repository for managing user lists stored in a JSON file.
    """

    def __init__(self, storage_path: str | None = None):
        self.storage_path = storage_path or LISTS_PATH
        dirpath = os.path.dirname(self.storage_path) or "."
        os.makedirs(dirpath, exist_ok=True)
        if not os.path.exists(self.storage_path):
            with open(self.storage_path, 'w', encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False, indent=2)

    def _load(self) -> List[Dict]:
        if not os.path.exists(self.storage_path):
            return []
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                raw = json.load(f)
            return [_fill_missing_fields(b) for b in raw if isinstance(b, dict)]
        except (json.JSONDecodeError, TypeError):
            return []

    def _save(self, lists: List[Dict]) -> None:
        dirpath = os.path.dirname(self.storage_path) or "."
        os.makedirs(dirpath, exist_ok=True)

        serialized = [_serialize_for_json(b) for b in lists]

        tmp_path = self.storage_path + ".tmp"
        try:
            with open(tmp_path, 'w', encoding="utf-8") as f:
                json.dump(serialized, f, ensure_ascii=False, indent=2)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, self.storage_path)
        finally:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass

    def create(self, list_in: ListCreate, user_id: str) -> ListOut:
        now = datetime.now(timezone.utc)
        data = self._load()

        payload = {
            "id": uuid.uuid4(),
            "user_id": user_id,
            "name": list_in.name,
            "description": list_in.description,
            "items": [],
            "created_at": now,
            "updated_at": now,
        }

        data.append(payload)
        self._save(data)
        return ListOut.model_validate(payload)

    def get_by_user(self, user_id: str) -> List[ListOut]:
        data = self._load()
        filtered = [b for b in data if b.get("user_id") == user_id]
        return [ListOut.model_validate(b) for b in filtered]

    def get_by_id(self, list_id: str) -> Optional[ListOut]:
        data = self._load()
        match = next((b for b in data if str(b.get("id")) == str(list_id)), None)
        if match:
            return ListOut.model_validate(match)
        return None

    def update(self, list_id: str, list_in: ListUpdate) -> Optional[ListOut]:
        data = self._load()
        for i, item in enumerate(data):
            if str(item.get("id")) == str(list_id):
                updated_item = item.copy()
                if list_in.name is not None:
                    updated_item["name"] = list_in.name
                if list_in.description is not None:
                    updated_item["description"] = list_in.description

                updated_item["updated_at"] = datetime.now(timezone.utc)
                data[i] = updated_item
                self._save(data)
                return ListOut.model_validate(updated_item)
        return None

    def delete(self, list_id: str) -> bool:
        data = self._load()
        new_data = [b for b in data if str(b.get("id")) != str(list_id)]

        if len(new_data) == len(data):
            return False

        self._save(new_data)
        return True

    def add_item(self, list_id: str, movie_id: str) -> Optional[ListOut]:
        data = self._load()
        for i, item in enumerate(data):
            if str(item.get("id")) == str(list_id):
                items = item.get("items", [])
                if movie_id not in items:
                    items.append(movie_id)
                    item["items"] = items
                    item["updated_at"] = datetime.now(timezone.utc)
                    data[i] = item
                    self._save(data)
                return ListOut.model_validate(item)
        return None

    def remove_item(self, list_id: str, movie_id: str) -> Optional[ListOut]:
        data = self._load()
        for i, item in enumerate(data):
            if str(item.get("id")) == str(list_id):
                items = item.get("items", [])
                if movie_id in items:
                    items.remove(movie_id)
                    item["items"] = items
                    item["updated_at"] = datetime.now(timezone.utc)
                    data[i] = item
                    self._save(data)
                return ListOut.model_validate(item)
        return None

    def replace_items(self, list_id: str, movie_ids: List[str]) -> Optional[ListOut]:
        """Replace all items in a list with a new set of movie IDs."""
        data = self._load()
        for i, item in enumerate(data):
            if str(item.get("id")) == str(list_id):
                item["items"] = movie_ids
                item["updated_at"] = datetime.now(timezone.utc)
                data[i] = item
                self._save(data)
                return ListOut.model_validate(item)
        return None

    def add_items_bulk(self, list_id: str, movie_ids: List[str]) -> Optional[ListOut]:
        """Add multiple items to a list, avoiding duplicates."""
        data = self._load()
        for i, item in enumerate(data):
            if str(item.get("id")) == str(list_id):
                items = item.get("items", [])
                # Add only new items that aren't already in the list
                for movie_id in movie_ids:
                    if movie_id not in items:
                        items.append(movie_id)
                item["items"] = items
                item["updated_at"] = datetime.now(timezone.utc)
                data[i] = item
                self._save(data)
                return ListOut.model_validate(item)
        return None

    def remove_items_bulk(
        self, list_id: str, movie_ids: List[str]
    ) -> Optional[ListOut]:
        """Remove multiple items from a list."""
        data = self._load()
        for i, item in enumerate(data):
            if str(item.get("id")) == str(list_id):
                items = item.get("items", [])
                # Remove all specified movie IDs
                for movie_id in movie_ids:
                    if movie_id in items:
                        items.remove(movie_id)
                item["items"] = items
                item["updated_at"] = datetime.now(timezone.utc)
                data[i] = item
                self._save(data)
                return ListOut.model_validate(item)
        return None
