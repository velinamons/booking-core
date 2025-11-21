from pydantic import BaseModel, Field, ConfigDict, model_validator
from datetime import date, time, datetime

from app.core.mixins.schemas import DateTimeRangeMixin


class OneTimeSessionBase(BaseModel):
    """Base fields for one-time session"""

    title: str = Field(..., min_length=1, max_length=255)
    notes: str | None = Field(None, max_length=5000)


class OneTimeSessionCreate(OneTimeSessionBase, DateTimeRangeMixin):
    """Schema for creating one-time session"""

    pass


class OneTimeSessionUpdate(BaseModel):
    """Schema for updating one-time session (all fields optional)"""

    title: str | None = Field(None, min_length=1, max_length=255)
    notes: str | None = Field(None, max_length=5000)
    start_date: date | None = None
    start_time: time | None = None
    end_date: date | None = None
    end_time: time | None = None

    @model_validator(mode="after")
    def validate_partial_datetime(self):
        """If updating datetime, must provide all 4 fields"""
        datetime_fields = [self.start_date, self.start_time, self.end_date, self.end_time]
        provided = [f for f in datetime_fields if f is not None]

        if 0 < len(provided) < 4:
            raise ValueError("Must provide all datetime fields together: " "start_date, start_time, end_date, end_time")

        # Validate range if all provided
        if len(provided) == 4:
            from datetime import datetime

            start = datetime.combine(self.start_date, self.start_time)
            end = datetime.combine(self.end_date, self.end_time)
            if end <= start:
                raise ValueError("End must be after start")

        return self


class OneTimeSessionResponse(OneTimeSessionBase, DateTimeRangeMixin):
    """Schema for one-time session response"""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
