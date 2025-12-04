from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List

from pytest_mock import MockerFixture

from backend.services import admin_summary_service as svc


def _write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=4), encoding="utf-8")


def test_get_admin_summary_basic(tmp_path: Path, mocker: MockerFixture) -> None:
    """Summary should correctly count total users, reviews, and active users."""

    users_file = tmp_path / "users.json"
    reviews_file = tmp_path / "reviews.json"

    now = datetime.now(timezone.utc)

    users: List[Dict[str, Any]] = [
        {
            "user_id": "u1",
            "email": "a@example.com",
            # active within last 24h
            "last_active_at": (now - timedelta(hours=1)).isoformat(),
        },
        {
            "user_id": "u2",
            "email": "b@example.com",
            # inactive (older than 24h)
            "last_active_at": (now - timedelta(days=2)).isoformat(),
        },
    ]
    reviews: List[Dict[str, Any]] = [
        {
            "user_id": "u1",
            "movie_id": "m1",
            "created_at": (now - timedelta(hours=2)).isoformat(),
        },
        {
            "user_id": "u2",
            "movie_id": "m2",
            "created_at": (now - timedelta(days=3)).isoformat(),
        },
    ]

    _write_json(users_file, users)
    _write_json(reviews_file, reviews)

    mocker.patch.object(svc, "USERS_FILE", users_file)
    mocker.patch.object(svc, "REVIEWS_FILE", reviews_file)

    summary = svc.get_admin_summary()

    assert summary["users_total"] == 2
    assert summary["reviews_total"] == 2
    # only u1 is active in last 24h
    assert summary["active_users_24h"] == 1


def test_write_summary_csv(tmp_path: Path, mocker: MockerFixture) -> None:
    """CSV export should include all metrics and a generated_at row."""

    users_file = tmp_path / "users.json"
    reviews_file = tmp_path / "reviews.json"
    export_dir = tmp_path / "exports"

    _write_json(users_file, [{"user_id": "u1"}, {"user_id": "u2"}])
    _write_json(reviews_file, [{"user_id": "u1"}, {"user_id": "u2"}])

    mocker.patch.object(svc, "USERS_FILE", users_file)
    mocker.patch.object(svc, "REVIEWS_FILE", reviews_file)
    mocker.patch.object(svc, "SUMMARY_EXPORT_DIR", export_dir)

    csv_path = svc.write_summary_csv()

    assert csv_path.exists()

    content = csv_path.read_text(encoding="utf-8").splitlines()
    header = content[0]
    assert header == "metric,value"

    metrics = {line.split(",")[0]: line.split(",")[1] for line in content[1:]}

    assert "users_total" in metrics
    assert "active_users_24h" in metrics
    assert "reviews_total" in metrics
    assert "generated_at" in metrics
