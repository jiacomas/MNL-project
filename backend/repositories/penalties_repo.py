from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from backend.schemas.penalties import (
    PenaltyCreate,
    PenaltyOut,
    PenaltySearchFilters,
    PenaltyUpdate,
    UserPenaltySummary,
)

# Configuration
PENALTIES_PATH = os.getenv("PENALTIES_PATH", "backend/data/penalties.json")


# ----------------- Helpers ----------------- #


def _now_utc() -> datetime:
    """Return current time as timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


def _ensure_storage_file(path: str) -> None:
    """Ensure the data directory & file exist."""
    dirpath = os.path.dirname(path) or "."
    os.makedirs(dirpath, exist_ok=True)
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)


def _load_raw_penalties(path: str) -> List[Dict[str, Any]]:
    """Load all penalties from JSON file as raw dicts."""
    if not os.path.exists(path):
        return []

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            return []
        return data
    except json.JSONDecodeError:
        # Corrupted or empty file – treat as empty
        return []


def _to_iso(dt: datetime) -> str:
    """Convert datetime to ISO string in UTC."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat()


def _serialize_for_json(obj: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prepare a penalty record dict for JSON writing:
    - Ensure 'id' is a string.
    - Convert datetime fields to ISO strings.
    """
    out = dict(obj)

    # Normalize id
    if not out.get("id"):
        out["id"] = uuid.uuid4().hex
    else:
        out["id"] = str(out["id"])

    # Normalize datetime fields
    for key in ("created_at", "updated_at", "expires_at"):
        value = out.get(key)
        if isinstance(value, datetime):
            out[key] = _to_iso(value)

    return out


def _refresh_is_active(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recalculate 'is_active' based on expires_at and current time.
    If 'is_active' is already False (e.g. manually deactivated),
    keep it False and do not re-activate.
    """
    rec = dict(record)
    # If explicitly inactive, keep it that way
    if rec.get("is_active") is False:
        return rec

    expires_at = rec.get("expires_at")
    if expires_at is None:
        # No expiration – consider still active
        rec["is_active"] = True
        return rec

    # Pydantic can parse ISO strings itself, but here we only need comparison
    # and we accept both str / datetime types
    if isinstance(expires_at, str):
        try:
            # Handle 'Z' suffix if present
            s = expires_at
            if s.endswith("Z"):
                s = s[:-1] + "+00:00"
            expires_dt = datetime.fromisoformat(s)
        except Exception:
            # Fallback: treat as expired if parse fails
            rec["is_active"] = False
            return rec
    elif isinstance(expires_at, datetime):
        expires_dt = expires_at
    else:
        rec["is_active"] = False
        return rec

    if expires_dt.tzinfo is None:
        expires_dt = expires_dt.replace(tzinfo=timezone.utc)

    rec["is_active"] = expires_dt > _now_utc()
    return rec


# ----------------- Repository ----------------- #


class JSONPenaltyRepository:
    """
    Repository for managing penalties stored in a JSON file.

    This repository:
      - Persists penalties as a flat JSON array.
      - Exposes CRUD operations and basic search.
      - Keeps 'is_active' in sync with 'expires_at' on read.
    """

    def __init__(self, storage_path: str = PENALTIES_PATH) -> None:
        self.storage_path = storage_path
        _ensure_storage_file(self.storage_path)

    # ---------- Internal helpers ---------- #

    def _load(self) -> List[Dict[str, Any]]:
        """Load raw penalty records from disk."""
        return _load_raw_penalties(self.storage_path)

    def _save(self, penalties: List[Dict[str, Any]]) -> None:
        """Persist all penalty records to disk (atomic write)."""
        dirpath = os.path.dirname(self.storage_path) or "."
        os.makedirs(dirpath, exist_ok=True)

        serialized = [_serialize_for_json(p) for p in penalties]

        tmp_path = self.storage_path + ".tmp"
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
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

    def _to_model(self, record: Dict[str, Any]) -> PenaltyOut:
        """
        Convert a raw record dict into a PenaltyOut model.
        Also refresh 'is_active' before validation.
        """
        refreshed = _refresh_is_active(record)
        return PenaltyOut.model_validate(refreshed)

    # ---------- CRUD operations ---------- #

    def create(self, payload: PenaltyCreate) -> PenaltyOut:
        """
        Create a new penalty entry.
        The repository is responsible for id, timestamps and is_active.
        """
        now = _now_utc()
        expires_at = payload.expires_at

        # Build raw record
        record: Dict[str, Any] = {
            "id": uuid.uuid4().hex,
            "user_id": payload.user_id,
            "reason": payload.reason,
            "penalty_type": payload.penalty_type,
            "severity": payload.severity,
            "expires_at": expires_at,
            "created_at": now,
            "updated_at": now,
            # is_active will be refreshed on read, but we can set a hint here
            "is_active": True,
        }

        data = self._load()
        data.append(record)
        self._save(data)

        return self._to_model(record)

    def get_by_id(self, penalty_id: str) -> Optional[PenaltyOut]:
        """Retrieve a single penalty by its id."""
        data = self._load()
        for record in data:
            if str(record.get("id")) == str(penalty_id):
                return self._to_model(record)
        return None

    def update(self, penalty_id: str, update: PenaltyUpdate) -> Optional[PenaltyOut]:
        """
        Apply a partial update to an existing penalty.
        Returns the updated penalty or None if not found.
        """
        data = self._load()
        updated_record: Optional[Dict[str, Any]] = None

        for i, record in enumerate(data):
            if str(record.get("id")) != str(penalty_id):
                continue

            # Only apply fields that are not None (PenaltyUpdate handles blank/None logic)
            update_data = update.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                record[key] = value

            record["updated_at"] = _now_utc()
            data[i] = record
            updated_record = record
            break

        if updated_record is None:
            return None

        self._save(data)
        return self._to_model(updated_record)

    def delete(self, penalty_id: str) -> bool:
        """
        Delete a penalty by id.
        Returns True if an entry was deleted, False otherwise.
        """
        data = self._load()
        new_data = [p for p in data if str(p.get("id")) != str(penalty_id)]

        if len(new_data) == len(data):
            return False

        self._save(new_data)
        return True

    def deactivate(self, penalty_id: str) -> bool:
        """
        Manually deactivate a penalty (set is_active=False).
        Returns True if updated, False if not found.
        """
        data = self._load()
        updated = False

        for record in data:
            if str(record.get("id")) == str(penalty_id):
                record["is_active"] = False
                record["updated_at"] = _now_utc()
                updated = True
                break

        if not updated:
            return False

        self._save(data)
        return True

    # ---------- Internal filtering helpers ---------- #

    def _record_matches(
        self,
        record: Dict[str, Any],
        raw_filters: Dict[str, Any],
    ) -> bool:
        """Return True if record matches the given raw filters."""
        user_id = raw_filters.get("user_id")
        ptype = raw_filters.get("penalty_type")
        severity = raw_filters.get("severity")
        active = raw_filters.get("is_active")

        if user_id and record.get("user_id") != user_id:
            return False
        if ptype and record.get("penalty_type") != ptype:
            return False
        if severity is not None and record.get("severity") != severity:
            return False

        # Active filter uses refreshed state
        if active is not None:
            ref = _refresh_is_active(record)
            if ref.get("is_active") is not active:
                return False

        return True

    def _filter_records(
        self,
        data: List[Dict[str, Any]],
        filters: Optional[PenaltySearchFilters],
    ) -> List[Dict[str, Any]]:
        """Apply all search filters and return filtered list."""
        raw_filters = filters.model_dump() if filters is not None else {}
        return [record for record in data if self._record_matches(record, raw_filters)]

    def _sort_records(
        self,
        records: List[Dict[str, Any]],
        sort_by: Optional[str],
        sort_desc: bool,
    ) -> List[Dict[str, Any]]:
        """Sort records optionally by the given field."""
        if not sort_by:
            return records

        def _sort_key(p: Dict[str, Any]):
            val = p.get(sort_by)

            # Try interpret as datetime string
            if isinstance(val, str) and ("T" in val or "-" in val):
                try:
                    s = val[:-1] + "+00:00" if val.endswith("Z") else val
                    dt = datetime.fromisoformat(s)
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    return dt
                except Exception:
                    return val

            return val

        return sorted(
            records,
            key=lambda p: (_sort_key(p) is None, _sort_key(p)),
            reverse=sort_desc,
        )

    def _paginate(
        self,
        records: List[Dict[str, Any]],
        skip: int,
        limit: int,
    ) -> List[Dict[str, Any]]:
        """Return a paginated slice of records."""
        return records[skip : skip + limit]

    # ---------- Query / Search ---------- #

    def search(
        self,
        filters: Optional[PenaltySearchFilters] = None,
        skip: int = 0,
        limit: int = 50,
        sort_by: Optional[str] = "created_at",
        sort_desc: bool = True,
    ) -> Tuple[List[PenaltyOut], int]:
        """
        Search penalties with the given filters and pagination.
        Returns (items, total).
        """
        data = self._load()

        # Step 1: filter
        filtered = self._filter_records(data, filters)

        # Step 2: sort
        sorted_records = self._sort_records(filtered, sort_by, sort_desc)

        # Step 3: paginate
        page = self._paginate(sorted_records, skip, limit)

        # Step 4: convert models
        return [self._to_model(p) for p in page], len(filtered)

    def list_by_user(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 50,
        sort_by: Optional[str] = "created_at",
        sort_desc: bool = True,
    ) -> Tuple[List[PenaltyOut], int]:
        """
        Convenience wrapper to list penalties for a single user.

        Internally delegates to `search` with a user_id filter so that tests
        and existing callers that rely on this method keep working.
        """
        filters = PenaltySearchFilters(user_id=user_id)
        return self.search(
            filters=filters,
            skip=skip,
            limit=limit,
            sort_by=sort_by,
            sort_desc=sort_desc,
        )

    # ---------- Summary ---------- #

    def get_user_summary(self, user_id: str) -> UserPenaltySummary:
        """
        Compute a summary of penalties for a given user.

        - total_penalties: total count in storage
        - active_penalties: count where is_active is True
        - max_severity: maximum severity among all penalties
        - has_permanent_ban: whether user has any active permanent ban
        """
        data = self._load()
        user_records = [p for p in data if str(p.get("user_id")) == user_id]

        total = len(user_records)
        active_count = 0
        max_severity = 0
        has_permanent_ban = False

        for record in user_records:
            refreshed = _refresh_is_active(record)
            if refreshed.get("severity") and isinstance(refreshed["severity"], int):
                max_severity = max(max_severity, refreshed["severity"])

            if refreshed.get("is_active"):
                active_count += 1
                if refreshed.get("penalty_type") == "permanent_ban":
                    has_permanent_ban = True

        return UserPenaltySummary(
            user_id=user_id,
            total_penalties=total,
            active_penalties=active_count,
            max_severity=max_severity,
            has_permanent_ban=has_permanent_ban,
        )
