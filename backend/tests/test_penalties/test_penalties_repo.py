import json
from datetime import datetime, timedelta, timezone

import pytest

import backend.repositories.penalties_repo as penalties_repo_module
from backend.repositories.penalties_repo import (
    JSONPenaltyRepository,
    _now_utc,
    _refresh_is_active,
    _serialize_for_json,
    _to_iso,
)
from backend.schemas.penalties import (
    PenaltyCreate,
    PenaltySearchFilters,
    PenaltyUpdate,
    UserPenaltySummary,
)

# Global fixtures (in-memory store)


@pytest.fixture
def memory_store():
    """In-memory storage to simulate JSON file contents."""
    return {"data": []}


@pytest.fixture
def repo(mocker, memory_store) -> JSONPenaltyRepository:
    """
    Repository instance whose load/save are patched to use memory_store
    instead of the real filesystem.
    """

    # Avoid touching real filesystem
    mocker.patch.object(
        penalties_repo_module,
        "_ensure_storage_file",
        lambda path: None,
    )

    def fake_load_raw_penalties(path: str):
        return memory_store["data"]

    mocker.patch.object(
        penalties_repo_module,
        "_load_raw_penalties",
        side_effect=fake_load_raw_penalties,
    )

    def fake_save(self, penalties):
        memory_store["data"] = penalties

    mocker.patch.object(JSONPenaltyRepository, "_save", fake_save)

    return JSONPenaltyRepository(storage_path="ignored.json")


@pytest.fixture
def sample_penalty_data():
    """Sample PenaltyCreate instance for tests."""
    now = _now_utc()
    return PenaltyCreate(
        user_id="user123",
        reason="Spam comments",
        penalty_type="review_restriction",
        severity=2,
        expires_at=now + timedelta(days=7),
    )


# Helper function tests


class TestPenaltyHelpers:
    """Test helper functions for penalty repository."""

    def test_now_utc_returns_timezone_aware_datetime(self):
        """Test that _now_utc returns timezone-aware UTC datetime."""
        result = _now_utc()
        assert result.tzinfo is not None
        assert result.tzinfo.utcoffset(result) == timedelta(0)

    def test_to_iso_converts_datetime_to_iso_string(self):
        """Test that _to_iso converts datetime to ISO string with UTC timezone."""
        dt = datetime(2023, 10, 1, 12, 30, 45, tzinfo=timezone.utc)
        result = _to_iso(dt)
        assert result == "2023-10-01T12:30:45+00:00"

    def test_to_iso_handles_naive_datetime(self):
        """Test that _to_iso handles naive datetime by converting to UTC."""
        dt = datetime(2023, 10, 1, 12, 30, 45)  # naive datetime
        result = _to_iso(dt)
        assert result.endswith("+00:00")

    def test_serialize_for_json_prepares_dict_correctly(self):
        """Test that _serialize_for_json prepares dictionary for JSON serialization."""
        test_data = {
            "id": "test-id",
            "created_at": datetime(2023, 10, 1, 12, 30, 45, tzinfo=timezone.utc),
            "expires_at": datetime(2023, 10, 2, 12, 30, 45, tzinfo=timezone.utc),
            "some_field": "some_value",
        }

        result = _serialize_for_json(test_data)

        assert result["id"] == "test-id"
        assert result["some_field"] == "some_value"
        assert isinstance(result["created_at"], str)
        assert isinstance(result["expires_at"], str)

    def test_serialize_for_json_generates_id_if_missing(self):
        """Test that _serialize_for_json generates UUID if id is missing."""
        test_data = {"some_field": "value"}
        result = _serialize_for_json(test_data)
        assert "id" in result
        assert len(result["id"]) == 32  # UUID hex without hyphens

    def test_refresh_is_active_calculates_active_status(self):
        """Test that _refresh_is_active correctly calculates active status based on expiration."""
        future_date = _now_utc() + timedelta(hours=1)
        past_date = _now_utc() - timedelta(hours=1)

        active_record = {"expires_at": future_date, "is_active": True}
        result = _refresh_is_active(active_record)
        assert result["is_active"] is True

        expired_record = {"expires_at": past_date, "is_active": True}
        result = _refresh_is_active(expired_record)
        assert result["is_active"] is False

    def test_refresh_is_active_preserves_manual_deactivation(self):
        """Test that _refresh_is_active preserves manually deactivated penalties."""
        future_date = _now_utc() + timedelta(hours=1)
        manually_inactive = {"expires_at": future_date, "is_active": False}

        result = _refresh_is_active(manually_inactive)
        assert result["is_active"] is False

    def test_refresh_is_active_handles_none_expiration(self):
        """Test that _refresh_is_active handles None expiration date."""
        record = {"expires_at": None, "is_active": True}
        result = _refresh_is_active(record)
        assert result["is_active"] is True


# JSONPenaltyRepository basic CRUD tests


class TestJSONPenaltyRepository:
    """Test JSONPenaltyRepository class functionality."""

    def test_init_calls_ensure_storage_file(self, mocker):
        """Test that repository init calls _ensure_storage_file with the given path."""
        spy = mocker.spy(penalties_repo_module, "_ensure_storage_file")
        repo = JSONPenaltyRepository(storage_path="some/path/penalties.json")
        assert repo.storage_path == "some/path/penalties.json"
        spy.assert_called_once_with("some/path/penalties.json")

    def test_create_penalty_success(self, repo, sample_penalty_data):
        """Test successful creation of a penalty."""
        result = repo.create(sample_penalty_data)

        assert result.id is not None
        assert result.user_id == "user123"
        assert result.reason == "Spam comments"
        assert result.penalty_type == "review_restriction"
        assert result.severity == 2
        assert result.is_active is True
        assert result.created_at is not None
        assert result.updated_at is not None

    def test_create_penalty_persists_to_memory_store(
        self, repo, sample_penalty_data, memory_store
    ):
        """Test that created penalty is written into in-memory storage."""
        _ = repo.create(sample_penalty_data)

        data = memory_store["data"]
        assert len(data) == 1
        assert data[0]["user_id"] == "user123"
        assert data[0]["reason"] == "Spam comments"

    def test_get_by_id_found(self, repo, sample_penalty_data):
        """Test retrieving penalty by existing ID."""
        created = repo.create(sample_penalty_data)
        retrieved = repo.get_by_id(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.user_id == created.user_id

    def test_get_by_id_not_found(self, repo):
        """Test retrieving penalty by non-existent ID returns None."""
        result = repo.get_by_id("non-existent-id")
        assert result is None

    def test_update_penalty_success(self, repo, sample_penalty_data):
        """Test successful update of a penalty."""
        created = repo.create(sample_penalty_data)
        update_data = PenaltyUpdate(reason="Updated reason", severity=3)

        updated = repo.update(created.id, update_data)

        assert updated is not None
        assert updated.id == created.id
        assert updated.reason == "Updated reason"
        assert updated.severity == 3
        assert updated.updated_at > created.updated_at

    def test_update_penalty_not_found(self, repo):
        """Test updating non-existent penalty returns None."""
        update_data = PenaltyUpdate(reason="New reason")
        result = repo.update("non-existent-id", update_data)
        assert result is None

    def test_update_penalty_partial_fields(self, repo, sample_penalty_data):
        """Test that update only modifies provided fields."""
        created = repo.create(sample_penalty_data)
        original_reason = created.reason

        update_data = PenaltyUpdate(severity=5)  # Only update severity
        updated = repo.update(created.id, update_data)

        assert updated.severity == 5
        assert updated.reason == original_reason

    def test_delete_penalty_success(self, repo, sample_penalty_data):
        """Test successful deletion of a penalty."""
        created = repo.create(sample_penalty_data)
        assert repo.get_by_id(created.id) is not None

        result = repo.delete(created.id)
        assert result is True
        assert repo.get_by_id(created.id) is None

    def test_delete_penalty_not_found(self, repo):
        """Test deleting non-existent penalty returns False."""
        result = repo.delete("non-existent-id")
        assert result is False

    def test_deactivate_penalty_success(self, repo, sample_penalty_data):
        """Test successful deactivation of a penalty."""
        created = repo.create(sample_penalty_data)
        assert created.is_active is True

        result = repo.deactivate(created.id)
        assert result is True

        deactivated = repo.get_by_id(created.id)
        assert deactivated.is_active is False

    def test_deactivate_penalty_not_found(self, repo):
        """Test deactivating non-existent penalty returns False."""
        result = repo.deactivate("non-existent-id")
        assert result is False


# Query & search tests


class TestPenaltyRepositoryQueries:
    """Test query and search functionality of penalty repository."""

    @pytest.fixture
    def repo_with_data(self, mocker, memory_store):
        """Create repository with sample penalty data in memory."""
        # Patch helpers before constructing repo
        mocker.patch.object(
            penalties_repo_module,
            "_ensure_storage_file",
            lambda path: None,
        )

        def fake_load_raw_penalties(path: str):
            return memory_store["data"]

        mocker.patch.object(
            penalties_repo_module,
            "_load_raw_penalties",
            side_effect=fake_load_raw_penalties,
        )

        def fake_save(self, penalties):
            memory_store["data"] = penalties

        mocker.patch.object(JSONPenaltyRepository, "_save", fake_save)

        repo = JSONPenaltyRepository(storage_path="ignored.json")

        # Populate data (all with future expiration, then set one as expired)
        now = _now_utc()
        future = now + timedelta(days=2)
        penalties_data = [
            PenaltyCreate(
                user_id="user1",
                reason="Spam",
                penalty_type="review_restriction",
                severity=1,
                expires_at=future,
            ),
            PenaltyCreate(
                user_id="user1",
                reason="Harassment",
                penalty_type="temporary_ban",
                severity=3,
                expires_at=future,
            ),
            PenaltyCreate(
                user_id="user2",
                reason="Spam",
                penalty_type="review_restriction",
                severity=2,
                expires_at=future,
            ),
            PenaltyCreate(
                user_id="user3",
                reason="Fake account",
                penalty_type="temporary_ban",
                severity=4,
                expires_at=future,
            ),
        ]
        for data in penalties_data:
            repo.create(data)

        # Make the last penalty expired by setting past expires_at in store
        past = now - timedelta(days=1)
        memory_store["data"][-1]["expires_at"] = past.isoformat()

        return repo

    def test_list_by_user_returns_correct_penalties(self, repo_with_data):
        """Test that list_by_user returns penalties for specific user only."""
        penalties, total = repo_with_data.list_by_user("user1")

        assert total == 2
        assert len(penalties) == 2
        assert all(p.user_id == "user1" for p in penalties)

    def test_list_by_user_pagination(self, repo_with_data):
        """Test that list_by_user supports pagination."""
        penalties_page1, total = repo_with_data.list_by_user("user1", skip=0, limit=1)
        assert len(penalties_page1) == 1
        assert total == 2

        penalties_page2, total2 = repo_with_data.list_by_user("user1", skip=1, limit=1)
        assert len(penalties_page2) == 1
        assert total2 == 2

    def test_list_by_user_no_penalties(self, repo_with_data):
        """Test list_by_user for user with no penalties returns empty list."""
        penalties, total = repo_with_data.list_by_user("non-existent-user")
        assert len(penalties) == 0
        assert total == 0

    def test_search_by_user_id(self, repo_with_data):
        """Test search functionality filtering by user_id."""
        filters = PenaltySearchFilters(user_id="user2")
        penalties, total = repo_with_data.search(filters=filters)

        assert total == 1
        assert len(penalties) == 1
        assert penalties[0].user_id == "user2"

    def test_search_by_penalty_type(self, repo_with_data):
        """Test search functionality filtering by penalty_type."""
        filters = PenaltySearchFilters(penalty_type="review_restriction")
        penalties, total = repo_with_data.search(filters=filters)

        assert total == 2
        assert all(p.penalty_type == "review_restriction" for p in penalties)

    def test_search_by_severity(self, repo_with_data):
        """Test search functionality filtering by severity."""
        filters = PenaltySearchFilters(severity=3)
        penalties, total = repo_with_data.search(filters=filters)

        assert total == 1
        assert penalties[0].severity == 3

    def test_search_by_active_status(self, repo_with_data):
        """Test search functionality filtering by active status."""
        filters_active = PenaltySearchFilters(is_active=True)
        penalties_active, total_active = repo_with_data.search(filters=filters_active)

        filters_inactive = PenaltySearchFilters(is_active=False)
        penalties_inactive, total_inactive = repo_with_data.search(
            filters=filters_inactive
        )

        assert total_active == 3
        assert total_inactive == 1
        assert all(p.is_active for p in penalties_active)
        assert all(not p.is_active for p in penalties_inactive)

    def test_search_with_sorting(self, repo_with_data):
        """Test search functionality with sorting."""
        penalties, total = repo_with_data.search(sort_by="severity", sort_desc=True)

        severities = [p.severity for p in penalties]
        assert severities == sorted(severities, reverse=True)

    def test_search_with_pagination(self, repo_with_data):
        """Test search functionality with pagination."""
        penalties_page1, total = repo_with_data.search(skip=0, limit=2)
        penalties_page2, total2 = repo_with_data.search(skip=2, limit=2)

        assert len(penalties_page1) == 2
        assert len(penalties_page2) == 2
        assert total == 4
        assert total2 == 4

    def test_search_without_filters(self, repo_with_data):
        """Test search functionality without any filters."""
        penalties, total = repo_with_data.search()

        assert total == 4
        assert len(penalties) == 4


# Summary tests


class TestPenaltyRepositorySummary:
    """Test user summary functionality."""

    @pytest.fixture
    def repo_with_summary_data(self, mocker, memory_store):
        """Create repository with data for summary testing."""
        mocker.patch.object(
            penalties_repo_module,
            "_ensure_storage_file",
            lambda path: None,
        )

        def fake_load_raw_penalties(path: str):
            return memory_store["data"]

        mocker.patch.object(
            penalties_repo_module,
            "_load_raw_penalties",
            side_effect=fake_load_raw_penalties,
        )

        def fake_save(self, penalties):
            memory_store["data"] = penalties

        mocker.patch.object(JSONPenaltyRepository, "_save", fake_save)

        repo = JSONPenaltyRepository(storage_path="ignored.json")
        now = _now_utc()
        future = now + timedelta(days=3)

        # user1: 2 active + 1 expired（通过修改 memory_store 实现）
        user1_penalties = [
            PenaltyCreate(
                user_id="user1",
                reason="Minor",
                penalty_type="review_restriction",
                severity=1,
                expires_at=future,
            ),
            PenaltyCreate(
                user_id="user1",
                reason="Medium",
                penalty_type="temporary_ban",
                severity=3,
                expires_at=future,
            ),
            PenaltyCreate(
                user_id="user1",
                reason="Expired",
                penalty_type="review_restriction",
                severity=2,
                expires_at=future,  # later turned into past
            ),
        ]

        # user2: permanent ban
        user2_penalties = [
            PenaltyCreate(
                user_id="user2",
                reason="Permanent",
                penalty_type="permanent_ban",
                severity=5,
                expires_at=None,
            ),
        ]

        for penalty in user1_penalties + user2_penalties:
            repo.create(penalty)

        # Make last user1 penalty expired
        past = now - timedelta(days=1)
        # user1 penalties are at index 0,1,2
        memory_store["data"][2]["expires_at"] = past.isoformat()

        return repo

    def test_get_user_summary_calculates_correct_values(self, repo_with_summary_data):
        """Test that get_user_summary calculates correct statistics."""
        summary: UserPenaltySummary = repo_with_summary_data.get_user_summary("user1")

        assert summary.user_id == "user1"
        assert summary.total_penalties == 3
        assert summary.active_penalties == 2
        assert summary.max_severity == 3
        assert summary.has_permanent_ban is False

    def test_get_user_summary_with_permanent_ban(self, repo_with_summary_data):
        """Test get_user_summary for user with permanent ban."""
        summary: UserPenaltySummary = repo_with_summary_data.get_user_summary("user2")

        assert summary.user_id == "user2"
        assert summary.total_penalties == 1
        assert summary.active_penalties == 1
        assert summary.max_severity == 5
        assert summary.has_permanent_ban is True

    def test_get_user_summary_no_penalties(self, repo_with_summary_data):
        """Test get_user_summary for user with no penalties."""
        summary: UserPenaltySummary = repo_with_summary_data.get_user_summary(
            "non-existent-user"
        )

        assert summary.user_id == "non-existent-user"
        assert summary.total_penalties == 0
        assert summary.active_penalties == 0
        assert summary.max_severity == 0
        assert summary.has_permanent_ban is False


# Edge case tests


class TestPenaltyRepositoryEdgeCases:
    """Test edge cases and error conditions."""

    def test_handles_corrupted_json_file(self, mocker):
        """Test that repository handles corrupted JSON file (JSONDecodeError) gracefully."""
        mocker.patch(
            "backend.repositories.penalties_repo.os.path.exists", return_value=True
        )
        mocker.patch("backend.repositories.penalties_repo.os.makedirs")
        mocker.patch(
            "backend.repositories.penalties_repo.open",
            mocker.mock_open(read_data="invalid json"),
            create=True,
        )
        mocker.patch(
            "backend.repositories.penalties_repo.json.load",
            side_effect=json.JSONDecodeError("msg", "doc", 0),
        )

        repo = JSONPenaltyRepository(storage_path="dummy.json")
        penalties, total = repo.list_by_user("user1")
        assert penalties == []
        assert total == 0

    def test_handles_empty_file(self, mocker):
        """Test that repository handles empty file as empty list (via JSONDecodeError)."""
        mocker.patch(
            "backend.repositories.penalties_repo.os.path.exists", return_value=True
        )
        mocker.patch("backend.repositories.penalties_repo.os.makedirs")
        mocker.patch(
            "backend.repositories.penalties_repo.open",
            mocker.mock_open(read_data=""),
            create=True,
        )
        mocker.patch(
            "backend.repositories.penalties_repo.json.load",
            side_effect=json.JSONDecodeError("msg", "doc", 0),
        )

        repo = JSONPenaltyRepository(storage_path="dummy.json")
        penalties, total = repo.list_by_user("user1")
        assert penalties == []
        assert total == 0

    def test_handles_missing_file(self, mocker):
        """Test that repository handles missing file correctly (os.path.exists=False)."""
        mocker.patch(
            "backend.repositories.penalties_repo.os.path.exists", return_value=False
        )
        mocker.patch("backend.repositories.penalties_repo.os.makedirs")

        repo = JSONPenaltyRepository(storage_path="dummy.json")
        penalties, total = repo.list_by_user("user1")
        assert penalties == []
        assert total == 0

    def test_penalty_expiration_auto_update(self, mocker, repo, sample_penalty_data):
        """Test that penalty active status is automatically updated based on current time."""
        # Penalty expires at 12:00
        future_time = datetime(2023, 10, 1, 12, 0, 0, tzinfo=timezone.utc)
        sample_penalty_data.expires_at = future_time

        # First, pretend now is 11:00 -> still active
        mocker.patch(
            "backend.repositories.penalties_repo._now_utc",
            return_value=datetime(2023, 10, 1, 11, 0, 0, tzinfo=timezone.utc),
        )
        created = repo.create(sample_penalty_data)
        assert created.is_active is True

        # Then, pretend now is 13:00 -> should be inactive
        mocker.patch(
            "backend.repositories.penalties_repo._now_utc",
            return_value=datetime(2023, 10, 1, 13, 0, 0, tzinfo=timezone.utc),
        )
        retrieved = repo.get_by_id(created.id)
        assert retrieved.is_active is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
