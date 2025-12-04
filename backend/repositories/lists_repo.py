from __future__ import annotations

import json
import os
import uuid
from typing import Any, Dict, List, Optional

from backend import settings
from backend.schemas.lists import ListCreate, ListOut, ListUpdate
from backend.utils.datetime_utils import (
    ensure_timezone_aware,
    now_utc,
    parse_iso_like,
    to_iso_string,
)

# Storage path (can be overridden by env in tests)
LISTS_PATH = os.getenv("LISTS_PATH", str(settings.ROOT_DATA_DIR / "lists.json"))


def _ensure_storage_file(path: str) -> None:
    dirpath = os.path.dirname(path) or "."
    os.makedirs(dirpath, exist_ok=True)
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)


def _serialize_for_json(obj: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(obj)
    # ensure id
    if not out.get("id"):
        out["id"] = str(uuid.uuid4())
    else:
        out["id"] = str(out["id"])

    # ensure items list
    out["items"] = list(out.get("items") or [])

    # datetimes -> iso
    for key in ("created_at", "updated_at"):
        val = out.get(key)
        if isinstance(val, str):
            continue
        out[key] = to_iso_string(ensure_timezone_aware(val))

    return out


def _load_raw(path: str) -> List[Dict[str, Any]]:
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            return []
        return data
    except json.JSONDecodeError:
        return []


class JSONListRepo:
    """Simple JSON-backed lists repository.

    Stores a flat list of list records with fields:
      - id (hex string)
      - user_id
      - name
      - description
      - items: list[str]
      - created_at, updated_at (ISO strings)
    """

    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path or os.getenv("LISTS_PATH", LISTS_PATH)
        _ensure_storage_file(self.storage_path)

    def _load(self) -> List[Dict[str, Any]]:
        return _load_raw(self.storage_path)

    def _save(self, rows: List[Dict[str, Any]]) -> None:
        dirpath = os.path.dirname(self.storage_path) or "."
        os.makedirs(dirpath, exist_ok=True)
        tmp = self.storage_path + ".tmp"
        serialized = [_serialize_for_json(r) for r in rows]
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(serialized, f, ensure_ascii=False, indent=2)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, self.storage_path)
        finally:
            if os.path.exists(tmp):
                try:
                    os.remove(tmp)
                except OSError:
                    pass

    def _to_model(self, rec: Dict[str, Any]) -> ListOut:
        # normalize datetimes to aware datetimes for Pydantic
        r = dict(rec)
        for k in ("created_at", "updated_at"):
            r[k] = parse_iso_like(r.get(k)) or now_utc()
        # ensure items
        r["items"] = list(r.get("items") or [])
        return ListOut.model_validate(r)

    # CRUD
    def create(self, payload: ListCreate, user_id: str) -> ListOut:
        now = now_utc()
        rec: Dict[str, Any] = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "name": payload.name,
            "description": payload.description,
            "items": [],
            "created_at": now,
            "updated_at": now,
        }
        data = self._load()
        data.append(rec)
        self._save(data)
        return self._to_model(rec)

    def get_by_user(self, user_id: str) -> List[ListOut]:
        data = self._load()
        filtered = [r for r in data if str(r.get("user_id")) == str(user_id)]
        return [self._to_model(r) for r in filtered]

    def get_by_id(self, list_id: str) -> Optional[ListOut]:
        data = self._load()
        for r in data:
            if str(r.get("id")) == str(list_id):
                return self._to_model(r)
        return None

    def update(self, list_id: str, payload: ListUpdate) -> Optional[ListOut]:
        data = self._load()
        updated = None
        for i, r in enumerate(data):
            if str(r.get("id")) != str(list_id):
                continue
            update_data = payload.model_dump(exclude_unset=True)
            for k, v in update_data.items():
                r[k] = v
            r["updated_at"] = now_utc()
            data[i] = r
            updated = r
            break
        if updated is None:
            return None
        self._save(data)
        return self._to_model(updated)

    def delete(self, list_id: str) -> bool:
        data = self._load()
        new = [r for r in data if str(r.get("id")) != str(list_id)]
        if len(new) == len(data):
            return False
        self._save(new)
        return True

    # items management
    def add_item(self, list_id: str, movie_id: str) -> Optional[ListOut]:
        data = self._load()
        for r in data:
            if str(r.get("id")) == str(list_id):
                items = list(r.get("items") or [])
                if movie_id not in items:
                    items.append(movie_id)
                r["items"] = items
                r["updated_at"] = now_utc()
                self._save(data)
                return self._to_model(r)
        return None

    def remove_item(self, list_id: str, movie_id: str) -> Optional[ListOut]:
        data = self._load()
        for r in data:
            if str(r.get("id")) == str(list_id):
                items = [m for m in (r.get("items") or []) if m != movie_id]
                r["items"] = items
                r["updated_at"] = now_utc()
                self._save(data)
                return self._to_model(r)
        return None

    def add_items_bulk(self, list_id: str, movie_ids: List[str]) -> Optional[ListOut]:
        data = self._load()
        for r in data:
            if str(r.get("id")) == str(list_id):
                items = list(r.get("items") or [])
                for m in movie_ids:
                    if m not in items:
                        items.append(m)
                r["items"] = items
                r["updated_at"] = now_utc()
                self._save(data)
                return self._to_model(r)
        return None

    def remove_items_bulk(
        self, list_id: str, movie_ids: List[str]
    ) -> Optional[ListOut]:
        data = self._load()
        for r in data:
            if str(r.get("id")) == str(list_id):
                items = [m for m in (r.get("items") or []) if m not in set(movie_ids)]
                r["items"] = items
                r["updated_at"] = now_utc()
                self._save(data)
                return self._to_model(r)
        return None


__all__ = ["JSONListRepo"]
