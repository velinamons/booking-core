from sqlalchemy.orm import Mapped, mapped_column

from app.core.mixins.models import SessionMixin, TimestampMixin
from app.models.base import Base

from sqlalchemy import CheckConstraint


class OneTimeSession(Base, SessionMixin, TimestampMixin):
    __tablename__ = "one_time_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    __table_args__ = (
        CheckConstraint(
            "(start_date < end_date) OR " "(start_date = end_date AND start_time < end_time)",
            name="one_time_valid_datetime_range",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<OneTimeSession(id={self.id}, title='{self.title}', "
            f"starts={self.start_date} {self.start_time},"
            f"ends={self.end_date} {self.end_time})>"
        )
