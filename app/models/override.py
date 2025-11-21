from datetime import date, time
from sqlalchemy import String, Integer, ForeignKey, Date, Time, Text, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.mixins.models import TimestampMixin
from app.models.base import Base


class RecurringOverride(Base, TimestampMixin):
    """
    Override for specific occurrence of recurring session.

    Stores only the CHANGES (partial override pattern).
    - cancelled: no modified_* fields needed
    - modified: at least one modified_* field required
    """

    __tablename__ = "recurring_overrides"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Foreign key to recurring session
    recurring_session_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("recurring_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Which occurrence date to override
    occurrence_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,  # ✅ ДОДАНО INDEX
    )

    # Override type: 'cancelled' or 'modified'
    override_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,  # ✅ For filtering by type
    )

    # ===== Partial modification fields (all nullable) =====
    modified_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    modified_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    modified_start_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    modified_end_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    modified_end_date: Mapped[date | None] = mapped_column(
        Date, nullable=True, comment="Only if session becomes overnight"
    )

    # ===== Relationship (optional, for easier queries) =====
    # Uncomment if you want to access recurring_session.overrides
    # recurring_session: Mapped["RecurringSession"] = relationship(
    #     "RecurringSession",
    #     back_populates="overrides"
    # )

    __table_args__ = (
        # One override per occurrence date
        UniqueConstraint("recurring_session_id", "occurrence_date", name="uq_override_per_occurrence"),
        # Valid override types
        CheckConstraint("override_type IN ('cancelled', 'modified')", name="ck_valid_override_type"),
        # Cancelled type must have NO modifications
        CheckConstraint(
            "override_type != 'cancelled' OR ("
            "modified_title IS NULL AND "
            "modified_notes IS NULL AND "
            "modified_start_time IS NULL AND "
            "modified_end_time IS NULL AND "
            "modified_end_date IS NULL)",
            name="ck_cancelled_no_modifications",
        ),
        # Modified type must have AT LEAST ONE modification
        CheckConstraint(
            "override_type != 'modified' OR ("
            "modified_title IS NOT NULL OR "
            "modified_notes IS NOT NULL OR "
            "modified_start_time IS NOT NULL OR "
            "modified_end_time IS NOT NULL OR "
            "modified_end_date IS NOT NULL)",
            name="ck_modified_has_changes",
        ),
        # Time consistency: if both times provided, end > start (same day)
        CheckConstraint(
            "modified_start_time IS NULL OR "
            "modified_end_time IS NULL OR "
            "modified_end_date IS NOT NULL OR "  # overnight allowed
            "modified_end_time > modified_start_time",
            name="ck_valid_time_range",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<RecurringOverride(id={self.id}, type='{self.override_type}', "
            f"recurring_id={self.recurring_session_id}, date={self.occurrence_date})>"
        )
