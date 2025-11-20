from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# Shared strict base schema
class StrictSchema(BaseModel):
    """Base model with shared strict configuration for schemas."""

    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True,
        extra="forbid",  # Forbid unknown/extra fields by default
    )


# ---------- Base Schema ----------
class PenaltyBase(StrictSchema):
    """Base schema for penalty records."""

    penalty_type: Literal["review_restriction", "temporary_ban", "permanent_ban"] = (
        Field(..., description="Type of penalty")
    )
    user_id: str = Field(..., min_length=1, description="ID of the penalized user")
    reason: str = Field(..., min_length=1, description="Reason for the penalty")

    severity: int = Field(
        default=1,
        ge=1,
        le=5,
        description="Severity level from 1 (lowest) to 5 (highest)",
    )

    expires_at: Optional[datetime] = Field(
        None,
        description="Expiration timestamp (None for permanent penalties)",
    )

    @field_validator("user_id", "reason", "penalty_type", mode="before")
    @classmethod
    def strip_and_reject_blank(cls, v: Optional[str]) -> Optional[str]:
        """
        Strip text fields and ensure they are not blank.
        Raises a validation error for empty or whitespace-only strings.
        """
        if v is None:
            return None
        v = v.strip()
        if not v:
            # This message is asserted in tests
            raise ValueError("Field cannot be blank")
        return v


# ---------- Create Schema ----------
class PenaltyCreate(PenaltyBase):
    """Schema for creating a new penalty."""

    @model_validator(mode="after")
    def validate_logic(self) -> PenaltyCreate:
        """
        Enforce business rules for creating penalties:
        - Permanent bans cannot have an expiration date.
        - Temporary bans must provide an expiration date.
        - If expires_at is provided, it must be in the future (UTC-aware comparison).
        """
        # Permanent bans must not have an expiration datetime
        if self.penalty_type == "permanent_ban" and self.expires_at is not None:
            # Message asserted in tests
            raise ValueError("Permanent bans cannot include expires_at")

        # Temporary bans must have an expiration datetime
        if self.penalty_type == "temporary_ban" and self.expires_at is None:
            # Message asserted in tests
            raise ValueError("Temporary bans require an expiration date")

        # If an expiration datetime is provided, ensure it is in the future (UTC)
        if self.expires_at is not None:
            # Normalize expires_at to an aware UTC datetime for safe comparison
            if self.expires_at.tzinfo is None:
                expires_at_utc = self.expires_at.replace(tzinfo=timezone.utc)
            else:
                expires_at_utc = self.expires_at.astimezone(timezone.utc)

            now_utc = datetime.now(timezone.utc)
            if expires_at_utc <= now_utc:
                # Message asserted in tests
                raise ValueError("Expiration date must be in the future")

        return self


# ---------- Update Schema ----------
class PenaltyUpdate(StrictSchema):
    """Schema for updating an existing penalty."""

    reason: Optional[str] = Field(
        None,
        description="Updated reason for the penalty",
    )
    severity: Optional[int] = Field(
        None,
        ge=1,
        le=5,
        description="Updated severity level",
    )
    expires_at: Optional[datetime] = Field(
        None,
        description="Updated expiration datetime",
    )

    @field_validator("reason", mode="before")
    @classmethod
    def normalize_reason(cls, v: Optional[str]) -> Optional[str]:
        """
        Strip the reason field and normalize empty strings to None.
        This makes it easier to distinguish between 'no update' and 'set empty'.
        """
        if v is None:
            return None
        v = v.strip()
        # Return None instead of an empty string
        return v or None

    @model_validator(mode="before")
    @classmethod
    def ensure_at_least_one_field(cls, values: dict) -> dict:
        """
        Ensure that the update payload contains at least one field.
        This check is done on the raw input data, so that a payload like
        {'reason': '   '} is still considered a valid (non-empty) update,
        even though 'reason' will later normalize to None.

        Completely empty payloads (no keys) or all-None explicit inputs
        are rejected.
        """
        if not values or all(v is None for v in values.values()):
            # Message asserted in tests
            raise ValueError("At least one field must be provided")
        return values


# ---------- Output Schema ----------
class PenaltyOut(PenaltyBase):
    """Schema for penalty data returned to clients."""

    id: str = Field(..., description="Unique penalty ID")
    created_at: datetime = Field(..., description="When the penalty was created")
    updated_at: datetime = Field(..., description="When the penalty was last updated")
    is_active: bool = Field(..., description="Whether the penalty is currently active")

    # Override config to ignore extra fields in responses from ORM/DB
    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True,
        extra="ignore",
    )


# ---------- Paginated List ----------
class PenaltyListResponse(StrictSchema):
    """Schema for paginated list of penalties."""

    items: List[PenaltyOut]
    total: int
    page: int
    page_size: int
    total_pages: int


# ---------- Search Filters ----------
class PenaltySearchFilters(StrictSchema):
    """Schema for filtering penalty searches."""

    user_id: Optional[str] = None
    penalty_type: Optional[str] = None
    severity: Optional[int] = None
    is_active: Optional[bool] = None

    @field_validator("user_id", "penalty_type", mode="before")
    @classmethod
    def normalize_text_filters(cls, v: Optional[str]) -> Optional[str]:
        """
        Strip whitespace from text filters and normalize blank strings to None.
        This avoids filters like "" which are not meaningful.
        """
        if v is None:
            return None
        v = v.strip()
        return v or None


# ---------- User Summary ----------
class UserPenaltySummary(StrictSchema):
    """Schema for user penalty summary."""

    user_id: str
    total_penalties: int = 0
    active_penalties: int = 0
    max_severity: int = 0
    has_permanent_ban: bool = False


# Explicit exports
__all__ = [
    "PenaltyBase",
    "PenaltyCreate",
    "PenaltyUpdate",
    "PenaltyOut",
    "PenaltyListResponse",
    "PenaltySearchFilters",
    "UserPenaltySummary",
]
