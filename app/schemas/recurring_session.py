from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import date, datetime
from typing import Literal

from app.core.mixins.schemas import DateTimeRangeMixin


class RecurringSessionBase(BaseModel):
    """Base fields for recurring session"""

    title: str = Field(..., min_length=1, max_length=255)
    notes: str | None = Field(None, max_length=5000)


class RecurringSessionCreate(RecurringSessionBase, DateTimeRangeMixin):
    """
    Schema for creating recurring session.
    recurrence_value will be auto-calculated from start_date.weekday()
    """

    recurrence_pattern: Literal["weekly"] = "weekly"

    @field_validator("start_date")
    def validate_start_date_weekday(cls, v: date):
        """Ensure start_date weekday will be used for recurrence"""
        # Just a sanity check, actual value calculated in service
        if v.weekday() not in range(7):
            raise ValueError("Invalid weekday")
        return v


class RecurringSessionResponse(RecurringSessionBase, DateTimeRangeMixin):
    """Schema for recurring session response"""

    id: int
    recurrence_pattern: str
    recurrence_value: int  # Day of week (0-6)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
