from datetime import date, time, datetime
from sqlalchemy import String, Text, Date, Time, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.ext.hybrid import hybrid_property


class TimestampMixin:
    """Mixin for created_at/updated_at timestamps"""

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class SessionMixin:
    """Mixin with common session fields"""

    # Session details
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Start date+time
    start_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)

    # End date+time
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)

    @hybrid_property
    def is_overnight(self) -> bool:
        """Check if session spans multiple days"""
        return self.end_date > self.start_date

    @hybrid_property
    def duration_minutes(self) -> int:
        """Calculate session duration in minutes."""
        start_dt = datetime.combine(self.start_date, self.start_time)
        end_dt = datetime.combine(self.end_date, self.end_time)
        delta = end_dt - start_dt
        return int(delta.total_seconds() / 60)

    @hybrid_property
    def duration_hours(self) -> float:
        """Calculate session duration in hours."""
        return round(self.duration_minutes / 60, 2)
