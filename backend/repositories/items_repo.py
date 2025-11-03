"""
Module to handle loading and saving items from/to the JSON data file.
Provides `load_all` and `save_all` functions.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "items.json"


def load_all() -> List[Dict[str, Any]]:
    """Load all items from the JSON data file. Returns an empty list if file does not exist."""
    if not DATA_PATH.exists():
        return []
    with DATA_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_all(items: List[Dict[str, Any]]) -> None:
    """Save all items to the JSON data file atomically using a temporary file."""
    tmp = DATA_PATH.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    os.replace(tmp, DATA_PATH)
