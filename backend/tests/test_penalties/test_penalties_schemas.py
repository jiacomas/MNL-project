from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from backend.schemas.penalties import (
    PenaltyBase,
    PenaltyCreate,
    PenaltyListResponse,
    PenaltyOut,
    PenaltySearchFilters,
    PenaltyUpdate,
    UserPenaltySummary,
)


class TestPenaltyBase:
    """Test cases for PenaltyBase schema."""

    def test_penalty_base_valid_data(self):
        """Test PenaltyBase with valid data."""
        valid_data = {
            "penalty_type": "temporary_ban",
            "user_id": "user_12345",
            "reason": "Spam behavior detected",
            "severity": 3,
            "expires_at": datetime.now(timezone.utc) + timedelta(days=7),
        }

        penalty = PenaltyBase(**valid_data)
        assert penalty.penalty_type == "temporary_ban"
        assert penalty.user_id == "user_12345"
        assert penalty.reason == "Spam behavior detected"
        assert penalty.severity == 3
        assert penalty.expires_at is not None

    def test_penalty_base_string_stripping(self):
        """Test that string fields are properly stripped."""
        data = {
            "penalty_type": "  review_restriction  ",
            "user_id": "  user_12345  ",
            "reason": "  Spam behavior  ",
        }

        penalty = PenaltyBase(**data)
        assert penalty.penalty_type == "review_restriction"
        assert penalty.user_id == "user_12345"
        assert penalty.reason == "Spam behavior"

    def test_penalty_base_blank_strings_rejected(self):
        """Test that blank strings raise validation errors."""
        invalid_data = {
            "penalty_type": "temporary_ban",
            "user_id": "   ",  # Only whitespace
            "reason": "Valid reason",
        }

        with pytest.raises(ValidationError) as exc_info:
            PenaltyBase(**invalid_data)

        assert "Field cannot be blank" in str(exc_info.value)

    def test_penalty_base_invalid_penalty_type(self):
        """Test that invalid penalty types are rejected."""
        invalid_data = {
            "penalty_type": "invalid_type",  # Not in Literal
            "user_id": "user_12345",
            "reason": "Valid reason",
        }

        with pytest.raises(ValidationError):
            PenaltyBase(**invalid_data)

    def test_penalty_base_severity_bounds(self):
        """Test severity level bounds validation."""
        # Test severity below minimum
        with pytest.raises(ValidationError):
            PenaltyBase(
                penalty_type="review_restriction",
                user_id="user_12345",
                reason="Test",
                severity=0,  # Below minimum
            )

        # Test severity above maximum
        with pytest.raises(ValidationError):
            PenaltyBase(
                penalty_type="review_restriction",
                user_id="user_12345",
                reason="Test",
                severity=6,  # Above maximum
            )


class TestPenaltyCreate:
    """Test cases for PenaltyCreate schema."""

    def test_penalty_create_valid_temporary_ban(self):
        """Test valid temporary ban creation."""
        future_date = datetime.now(timezone.utc) + timedelta(days=30)

        data = {
            "penalty_type": "temporary_ban",
            "user_id": "user_12345",
            "reason": "Temporary suspension",
            "severity": 4,
            "expires_at": future_date,
        }

        penalty = PenaltyCreate(**data)
        assert penalty.penalty_type == "temporary_ban"
        assert penalty.expires_at == future_date

    def test_penalty_create_valid_permanent_ban(self):
        """Test valid permanent ban creation."""
        data = {
            "penalty_type": "permanent_ban",
            "user_id": "user_12345",
            "reason": "Serious violation",
            "severity": 5,
            "expires_at": None,  # Must be None for permanent
        }

        penalty = PenaltyCreate(**data)
        assert penalty.penalty_type == "permanent_ban"
        assert penalty.expires_at is None

    def test_penalty_create_permanent_ban_with_expires_at(self):
        """Test that permanent bans cannot have expiration dates."""
        future_date = datetime.now(timezone.utc) + timedelta(days=30)

        data = {
            "penalty_type": "permanent_ban",
            "user_id": "user_12345",
            "reason": "Serious violation",
            "expires_at": future_date,  # Should not be allowed
        }

        with pytest.raises(ValidationError) as exc_info:
            PenaltyCreate(**data)

        assert "Permanent bans cannot include expires_at" in str(exc_info.value)

    def test_penalty_create_temporary_ban_without_expires_at(self):
        """Test that temporary bans require expiration dates."""
        data = {
            "penalty_type": "temporary_ban",
            "user_id": "user_12345",
            "reason": "Temporary suspension",
            "expires_at": None,  # Should not be allowed
        }

        with pytest.raises(ValidationError) as exc_info:
            PenaltyCreate(**data)

        assert "Temporary bans require an expiration date" in str(exc_info.value)

    def test_penalty_create_past_expiration_date(self):
        """Test that past expiration dates are rejected."""
        past_date = datetime.now(timezone.utc) - timedelta(days=1)

        data = {
            "penalty_type": "temporary_ban",
            "user_id": "user_12345",
            "reason": "Test",
            "expires_at": past_date,
        }

        with pytest.raises(ValidationError) as exc_info:
            PenaltyCreate(**data)

        assert "Expiration date must be in the future" in str(exc_info.value)


class TestPenaltyUpdate:
    """Test cases for PenaltyUpdate schema."""

    def test_penalty_update_valid_partial_update(self):
        """Test valid partial updates."""
        # Update only reason
        update1 = PenaltyUpdate(reason="Updated reason")
        assert update1.reason == "Updated reason"
        assert update1.severity is None
        assert update1.expires_at is None

        # Update only severity
        update2 = PenaltyUpdate(severity=2)
        assert update2.reason is None
        assert update2.severity == 2
        assert update2.expires_at is None

        # Update only expiration
        future_date = datetime.now(timezone.utc) + timedelta(days=14)
        update3 = PenaltyUpdate(expires_at=future_date)
        assert update3.reason is None
        assert update3.severity is None
        assert update3.expires_at == future_date

    def test_penalty_update_string_stripping(self):
        """Test that reason field is properly stripped."""
        update = PenaltyUpdate(reason="  Updated reason with spaces  ")
        assert update.reason == "Updated reason with spaces"

    def test_penalty_update_blank_reason_normalized_to_none(self):
        """Test that blank reason is normalized to None."""
        update = PenaltyUpdate(reason="   ")  # Only whitespace
        assert update.reason is None

    def test_penalty_update_empty_update_rejected(self):
        """Test that empty updates are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            PenaltyUpdate()  # No fields provided

        assert "At least one field must be provided" in str(exc_info.value)

    def test_penalty_update_severity_bounds(self):
        """Test severity bounds in updates."""
        # Test valid severity
        update = PenaltyUpdate(severity=3)
        assert update.severity == 3

        # Test invalid severity (below minimum)
        with pytest.raises(ValidationError):
            PenaltyUpdate(severity=0)

        # Test invalid severity (above maximum)
        with pytest.raises(ValidationError):
            PenaltyUpdate(severity=6)


class TestPenaltyOut:
    """Test cases for PenaltyOut schema."""

    def test_penalty_out_valid_data(self):
        """Test PenaltyOut with complete data."""
        now = datetime.now(timezone.utc)
        future_date = now + timedelta(days=30)

        data = {
            "id": "penalty_abc123",
            "penalty_type": "temporary_ban",
            "user_id": "user_12345",
            "reason": "Spam behavior",
            "severity": 3,
            "expires_at": future_date,
            "created_at": now,
            "updated_at": now,
            "is_active": True,
        }

        penalty = PenaltyOut(**data)
        assert penalty.id == "penalty_abc123"
        assert penalty.is_active is True
        assert penalty.created_at == now
        assert penalty.updated_at == now

    def test_penalty_out_extra_fields_ignored(self):
        """Test that PenaltyOut ignores extra fields."""
        now = datetime.now(timezone.utc)

        data = {
            "id": "penalty_abc123",
            "penalty_type": "review_restriction",
            "user_id": "user_12345",
            "reason": "Test",
            "created_at": now,
            "updated_at": now,
            "is_active": True,
            "extra_field": "should_be_ignored",  # This should be ignored
        }

        penalty = PenaltyOut(**data)
        assert not hasattr(penalty, "extra_field")


class TestPenaltyListResponse:
    """Test cases for PenaltyListResponse schema."""

    def test_penalty_list_response_valid(self):
        """Test valid penalty list response."""
        now = datetime.now(timezone.utc)

        penalty_data = {
            "id": "penalty_123",
            "penalty_type": "review_restriction",
            "user_id": "user_12345",
            "reason": "Test reason",
            "severity": 2,
            "expires_at": now + timedelta(days=7),
            "created_at": now,
            "updated_at": now,
            "is_active": True,
        }

        penalty = PenaltyOut(**penalty_data)

        response_data = {
            "items": [penalty],
            "total": 1,
            "page": 1,
            "page_size": 20,
            "total_pages": 1,
        }

        response = PenaltyListResponse(**response_data)
        assert len(response.items) == 1
        assert response.total == 1
        assert response.page == 1
        assert response.page_size == 20
        assert response.total_pages == 1
        assert response.items[0].id == "penalty_123"


class TestPenaltySearchFilters:
    """Test cases for PenaltySearchFilters schema."""

    def test_penalty_search_filters_valid(self):
        """Test valid search filters."""
        filters = PenaltySearchFilters(
            user_id="user_12345",
            penalty_type="temporary_ban",
            severity=3,
            is_active=True,
        )

        assert filters.user_id == "user_12345"
        assert filters.penalty_type == "temporary_ban"
        assert filters.severity == 3
        assert filters.is_active is True

    def test_penalty_search_filters_partial(self):
        """Test partial search filters."""
        filters = PenaltySearchFilters(user_id="user_12345")
        assert filters.user_id == "user_12345"
        assert filters.penalty_type is None
        assert filters.severity is None
        assert filters.is_active is None

    def test_penalty_search_filters_string_stripping(self):
        """Test that string filters are properly stripped."""
        filters = PenaltySearchFilters(
            user_id="  user_12345  ", penalty_type="  temporary_ban  "
        )

        assert filters.user_id == "user_12345"
        assert filters.penalty_type == "temporary_ban"

    def test_penalty_search_filters_blank_strings_normalized(self):
        """Test that blank string filters are normalized to None."""
        filters = PenaltySearchFilters(user_id="   ", penalty_type="   ")
        assert filters.user_id is None
        assert filters.penalty_type is None


class TestUserPenaltySummary:
    """Test cases for UserPenaltySummary schema."""

    def test_user_penalty_summary_valid(self):
        """Test valid user penalty summary."""
        summary = UserPenaltySummary(
            user_id="user_12345",
            total_penalties=3,
            active_penalties=1,
            max_severity=4,
            has_permanent_ban=False,
        )

        assert summary.user_id == "user_12345"
        assert summary.total_penalties == 3
        assert summary.active_penalties == 1
        assert summary.max_severity == 4
        assert summary.has_permanent_ban is False

    def test_user_penalty_summary_defaults(self):
        """Test user penalty summary with default values."""
        summary = UserPenaltySummary(user_id="user_12345")

        assert summary.user_id == "user_12345"
        assert summary.total_penalties == 0
        assert summary.active_penalties == 0
        assert summary.max_severity == 0
        assert summary.has_permanent_ban is False


class TestIntegrationScenarios:
    """Integration test scenarios for penalty schemas."""

    def test_complete_penalty_workflow(self):
        """Test a complete penalty workflow from creation to output."""
        # 1. Create a penalty
        future_date = datetime.now(timezone.utc) + timedelta(days=14)
        create_data = {
            "penalty_type": "temporary_ban",
            "user_id": "user_12345",
            "reason": "Multiple policy violations",
            "severity": 4,
            "expires_at": future_date,
        }
        penalty_create = PenaltyCreate(**create_data)

        # 2. Update the penalty
        update_data = {"reason": "Additional violations discovered", "severity": 5}
        penalty_update = PenaltyUpdate(**update_data)

        # 3. Create output representation
        now = datetime.now(timezone.utc)
        out_data = {
            "id": "penalty_abc123",
            "penalty_type": penalty_create.penalty_type,
            "user_id": penalty_create.user_id,
            "reason": "Additional violations discovered",  # Updated reason
            "severity": 5,  # Updated severity
            "expires_at": penalty_create.expires_at,
            "created_at": now,
            "updated_at": now,
            "is_active": True,
        }
        penalty_out = PenaltyOut(**out_data)

        # 4. Verify the data
        assert penalty_out.id == "penalty_abc123"
        assert penalty_out.penalty_type == "temporary_ban"
        assert penalty_out.reason == "Additional violations discovered"
        assert penalty_out.severity == 5
        assert penalty_out.is_active is True

    def test_search_and_list_workflow(self):
        """Test search filters and list response workflow."""
        # Create search filters
        filters = PenaltySearchFilters(user_id="user_12345", is_active=True)

        # Create a penalty for the list
        now = datetime.now(timezone.utc)
        penalty_out = PenaltyOut(
            id="penalty_123",
            penalty_type="review_restriction",
            user_id="user_12345",
            reason="Test",
            severity=2,
            expires_at=now + timedelta(days=7),
            created_at=now,
            updated_at=now,
            is_active=True,
        )

        # Create list response
        list_response = PenaltyListResponse(
            items=[penalty_out], total=1, page=1, page_size=20, total_pages=1
        )

        # Verify the workflow
        assert filters.user_id == "user_12345"
        assert filters.is_active is True
        assert len(list_response.items) == 1
        assert list_response.items[0].user_id == "user_12345"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
