from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from backend import settings

SYNC_LOG_FILE = settings.SYNC_LOG_FILE


class SyncLogRepository:
    """Repository for managing external sync logs."""

    def __init__(self, storage_path: Path = SYNC_LOG_FILE):
        self.storage_path = storage_path
        self._ensure_storage()

    def _ensure_storage(self) -> None:
        if not self.storage_path.exists():
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            self.storage_path.write_text("[]", encoding="utf-8")

    def _load(self) -> List[Dict[str, Any]]:
        if not self.storage_path.exists():
            return []
        try:
            return json.loads(self.storage_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []

    def _save(self, logs: List[Dict[str, Any]]) -> None:
        self.storage_path.write_text(json.dumps(logs, indent=4), encoding="utf-8")

    def append_log(self, log_entry: Dict[str, Any]) -> None:
        """Append a new log entry."""
        logs = self._load()
        if not isinstance(logs, list):
            logs = []
        logs.append(log_entry)
        self._save(logs)
