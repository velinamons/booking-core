from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, CheckConstraint

from app.core.mixins.models import SessionMixin, TimestampMixin
from app.models.base import Base


class RecurringSession(Base, SessionMixin, TimestampMixin):
    """
    Recurring session template.
    recurrence_value is auto-calculated from start_date.weekday()
    """

    __tablename__ = "recurring_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    recurrence_pattern: Mapped[str] = mapped_column(String(20), nullable=False)
    recurrence_value: Mapped[int] = mapped_column(Integer, nullable=False)

    __table_args__ = (
        CheckConstraint(
            "(start_date < end_date) OR " "(start_date = end_date AND start_time < end_time)",
            name="recurring_valid_datetime_range",
        ),
        CheckConstraint(
            "recurrence_pattern != 'weekly' OR (recurrence_value >= 0 AND recurrence_value <= 6)",
            name="recurring_valid_weekly_day",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<RecurringSession(id={self.id}, title='{self.title}', "
            f"pattern='{self.recurrence_pattern}', starts={self.start_date} {self.start_time})>"
        )
