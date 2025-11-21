# app/schemas/calendar.py
from typing import Literal

from pydantic import BaseModel, Field, model_validator
from datetime import date, time


class CalendarSessionResponse(BaseModel):
    """
    Unified response for calendar view.
    Represents both one-time sessions and recurring instances.
    """

    # Type identifier
    session_type: Literal["one_time", "recurring"] = Field(..., description="Type of session")

    # Common session fields
    title: str
    notes: str | None
    start_date: date
    start_time: time
    end_date: date
    end_time: time

    # Type-specific identifiers
    id: int | None = Field(None, description="Session ID (only for one_time sessions, null for recurring instances)")
    recurring_session_id: int | None = Field(None, description="Parent recurring session ID (only for recurring type)")
    occurrence_date: date | None = Field(None, description="Original occurrence date (only for recurring instances)")
    is_modified: bool = Field(default=False, description="Whether this recurring instance has overrides applied")


class CalendarRangeRequest(BaseModel):
    """Query parameters for calendar range"""

    start_date: date = Field(..., description="Start of date range (inclusive)")
    end_date: date = Field(..., description="End of date range (inclusive)")

    @model_validator(mode="after")
    def validate_range(self):
        if self.end_date < self.start_date:
            raise ValueError("end_date must be >= start_date")
        return self


class CalendarRangeResponse(BaseModel):
    """Response for calendar range query"""

    start_date: date
    end_date: date
    total_count: int
    sessions: list[CalendarSessionResponse]
