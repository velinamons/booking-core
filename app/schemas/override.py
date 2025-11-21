# app/schemas/override.py
from pydantic import BaseModel, Field, model_validator, ConfigDict
from datetime import date, time, datetime
from typing import Literal


class OverrideCancel(BaseModel):
    """Cancel specific occurrence of recurring session"""

    occurrence_date: date = Field(..., description="Date of the recurring instance to cancel")


class OverrideModify(BaseModel):
    """Modify specific occurrence of recurring session"""

    occurrence_date: date = Field(..., description="Date of the recurring instance to modify")

    # At least one modification must be provided
    modified_title: str | None = Field(None, min_length=1, max_length=255)
    modified_notes: str | None = Field(None, max_length=5000)
    modified_start_time: time | None = None
    modified_end_time: time | None = None
    modified_end_date: date | None = Field(
        None, description="Only needed if session becomes overnight (different from occurrence_date)"
    )

    @model_validator(mode="after")
    def validate_has_changes(self):
        """At least one modification must be provided"""
        if not any(
            [
                self.modified_title,
                self.modified_notes,
                self.modified_start_time,
                self.modified_end_time,
                self.modified_end_date,
            ]
        ):
            raise ValueError("Must provide at least one modification")
        return self

    @model_validator(mode="after")
    def validate_time_consistency(self):
        """Validate time logic if times are provided"""
        # If both times provided and no end_date override, times must be valid for same day
        if (
            self.modified_start_time is not None
            and self.modified_end_time is not None
            and self.modified_end_date is None
        ):
            if self.modified_end_time <= self.modified_start_time:
                raise ValueError(
                    "modified_end_time must be after modified_start_time "
                    "(or provide modified_end_date for overnight session)"
                )
        return self


class OverrideResponse(BaseModel):
    """Response after creating/fetching override"""

    id: int
    recurring_session_id: int
    occurrence_date: date
    override_type: Literal["cancelled", "modified"]

    # Conditional fields (only for 'modified' type)
    modified_title: str | None = None
    modified_notes: str | None = None
    modified_start_time: time | None = None
    modified_end_time: time | None = None
    modified_end_date: date | None = None

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
