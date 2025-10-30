# backend/app/repositories/reset_tokens_repo.py
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional, Union


class ResetTokensRepo:
    """
    File-backed store for password reset tokens (by JTI).
    JSON shape:
      {
        "<jti>": {"user_id": <str|int>, "used": <bool>}
      }
    """

    def __init__(self, base_dir: Optional[Union[str, Path]] = None) -> None:
        # Prefer explicit arg; else env; else CWD
        env_dir = os.environ.get("SECURITY_DATA_PATH")
        if base_dir is not None:
            base = Path(base_dir)
        elif env_dir:
            base = Path(env_dir)
        else:
            base = Path.cwd()

        self.base_dir = base
        # Many tests expect a subfolder named "security"
        self._dir = self.base_dir if self.base_dir.name == "security" else (self.base_dir / "security")
        self._dir.mkdir(parents=True, exist_ok=True)

        self._file = self._dir / "password_resets.json"
        if not self._file.exists():
            self._file.write_text("{}", encoding="utf-8")

    # ---------- internal IO ----------
    def _read_all(self) -> Dict[str, Any]:
        try:
            text = self._file.read_text(encoding="utf-8")
            if not text.strip():
                return {}
            return json.loads(text)
        except FileNotFoundError:
            self._dir.mkdir(parents=True, exist_ok=True)
            self._file.write_text("{}", encoding="utf-8")
            return {}
        except json.JSONDecodeError:
            return {}

    def _write_all(self, data: Dict[str, Any]) -> None:
        self._dir.mkdir(parents=True, exist_ok=True)
        self._file.write_text(json.dumps(data), encoding="utf-8")

    # ---------- public API ----------
    def clear(self) -> None:
        """Remove all stored tokens (used by tests)."""
        self._write_all({})

    def upsert(self, jti: str, user_id: Union[str, int]) -> None:
        data = self._read_all()
        data[jti] = {"user_id": user_id, "used": False}
        self._write_all(data)

    def is_used(self, jti: str) -> bool:
        rec = self._read_all().get(jti)
        return bool(rec and rec.get("used") is True)

    def mark_used(self, jti: str) -> None:
        data = self._read_all()
        rec = data.get(jti)
        if rec:
            rec["used"] = True
            data[jti] = rec
            self._write_all(data)

    def get(self, jti: str) -> Optional[Dict[str, Any]]:
        return self._read_all().get(jti)

