from pydantic import BaseModel, model_validator
from datetime import date, time


class DateTimeRangeMixin(BaseModel):
    """Mixin for validating date/time ranges"""

    start_date: date
    start_time: time
    end_date: date
    end_time: time

    @model_validator(mode="after")
    def validate_datetime_range(self):
        from datetime import datetime

        start = datetime.combine(self.start_date, self.start_time)
        end = datetime.combine(self.end_date, self.end_time)
        if end <= start:
            raise ValueError("End datetime must be after start datetime")
        return self
