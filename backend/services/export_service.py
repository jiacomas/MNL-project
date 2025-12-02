from datetime import datetime, timezone
from typing import Any, Dict

from backend.services import bookmarks_service, history_service, reviews_service


def generate_user_export(user_id: str) -> Dict[str, Any]:
    """
    Aggregate all data for a specific user into a single dictionary.

    Includes:
    - Reviews
    - Bookmarks
    - Viewing History
    - Metadata (timestamp, user_id)
    """
    reviews = reviews_service.get_all_reviews_for_user(user_id)
    bookmarks = bookmarks_service.list_bookmarks(user_id)
    history = history_service.list_history(user_id)

    return {
        "meta": {
            "user_id": user_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "version": "1.0",
        },
        "data": {
            "reviews": [r.model_dump() for r in reviews],
            "bookmarks": [b.model_dump() for b in bookmarks],
            "history": history,  # history items are already dicts
        },
    }
