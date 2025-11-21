from datetime import date, time, timedelta, datetime
from typing import Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import OneTimeSession, RecurringSession, RecurringOverride


class SessionInstance:
    """
    Unified representation of session instance (one-time or recurring).
    Used for internal processing before converting to API schemas.
    """

    def __init__(  # noqa: A002
        self,
        id: int | None,
        session_type: str,
        title: str,
        notes: str | None,
        start_date: date,
        start_time: time,
        end_date: date,
        end_time: time,
        recurring_session_id: int | None = None,
        occurrence_date: date | None = None,
        is_modified: bool = False,
    ):
        self.id = id
        self.session_type = session_type
        self.title = title
        self.notes = notes
        self.start_date = start_date
        self.start_time = start_time
        self.end_date = end_date
        self.end_time = end_time
        self.recurring_session_id = recurring_session_id
        self.occurrence_date = occurrence_date
        self.is_modified = is_modified

    @property
    def start_datetime(self) -> datetime:
        """Combined datetime for sorting"""
        return datetime.combine(self.start_date, self.start_time)

    def to_dict(self) -> dict:
        """Convert to dict for API response"""
        return {
            "id": self.id,
            "session_type": self.session_type,
            "title": self.title,
            "notes": self.notes,
            "start_date": self.start_date.isoformat(),
            "start_time": self.start_time.isoformat(),
            "end_date": self.end_date.isoformat(),
            "end_time": self.end_time.isoformat(),
            "recurring_session_id": self.recurring_session_id,
            "occurrence_date": self.occurrence_date.isoformat() if self.occurrence_date else None,
            "is_modified": self.is_modified,
        }


class CalendarService:
    """Service for calendar operations (viewing sessions in date range)"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_sessions_in_range(self, start_date: date, end_date: date) -> list[dict]:
        """
        Get all sessions (one-time + recurring instances) in date range.

        Returns list of dicts ready for JSON serialization.
        """

        # 1. Fetch one-time sessions
        one_time = await self._get_one_time_sessions(start_date, end_date)

        # 2. Generate recurring instances
        recurring = await self._generate_recurring_instances(start_date, end_date)

        # 3. Merge and sort by start datetime
        all_sessions = one_time + recurring
        all_sessions.sort(key=lambda x: x.start_datetime)

        # 4. Convert to dicts for JSON response
        return [s.to_dict() for s in all_sessions]

    async def _get_one_time_sessions(self, start_date: date, end_date: date) -> list[SessionInstance]:
        """Fetch one-time sessions overlapping with date range"""

        stmt = (
            select(OneTimeSession)
            .where(
                and_(
                    # Session starts before or at range end
                    OneTimeSession.start_date <= end_date,
                    # Session ends after or at range start (handles overnight sessions)
                    OneTimeSession.end_date >= start_date,
                )
            )
            .order_by(OneTimeSession.start_date, OneTimeSession.start_time)
        )

        result = await self.db.execute(stmt)
        sessions = list(result.scalars().all())  # ✅ Convert Sequence to list

        # Convert to SessionInstance
        return [
            SessionInstance(
                id=s.id,
                session_type="one_time",
                title=s.title,
                notes=s.notes,
                start_date=s.start_date,
                start_time=s.start_time,
                end_date=s.end_date,
                end_time=s.end_time,
            )
            for s in sessions
        ]

    async def _generate_recurring_instances(self, start_date: date, end_date: date) -> list[SessionInstance]:
        """Generate recurring session instances for date range"""

        # Fetch all recurring sessions
        stmt = select(RecurringSession)
        result = await self.db.execute(stmt)
        recurring_sessions = list(result.scalars().all())  # ✅ Convert to list

        instances = []
        for rs in recurring_sessions:
            # Fetch overrides for this session in date range
            overrides = await self._get_overrides(rs.id, start_date, end_date)
            overrides_map = {o.occurrence_date: o for o in overrides}

            # Find first occurrence in range
            current = self._find_first_occurrence(rs, start_date)

            # Generate all occurrences until end_date
            while current <= end_date:
                if current >= start_date:
                    override = overrides_map.get(current)

                    # Skip cancelled instances
                    if override and override.override_type == "cancelled":
                        pass  # Don't add to instances
                    else:
                        # Build instance with possible override
                        instance = self._build_instance(rs, current, override)
                        instances.append(instance)

                # Move to next week
                current += timedelta(days=7)

        return instances

    async def _get_overrides(
        self, recurring_session_id: int, start_date: date, end_date: date
    ) -> list[RecurringOverride]:
        """Fetch overrides for recurring session in date range"""

        stmt = select(RecurringOverride).where(
            and_(
                RecurringOverride.recurring_session_id == recurring_session_id,
                RecurringOverride.occurrence_date >= start_date,
                RecurringOverride.occurrence_date <= end_date,
            )
        )

        result = await self.db.execute(stmt)
        return list(result.scalars().all())  # ✅ Convert to list

    def _find_first_occurrence(self, recurring_session: RecurringSession, start_date: date) -> date:
        """
        Find first occurrence of recurring session on or after start_date.

        For weekly sessions, find the next day matching recurrence_value.
        """
        # Get the day of week for recurring session (0=Monday, 6=Sunday)
        target_weekday = recurring_session.recurrence_value

        # If recurring session starts after our range, use its start_date
        if recurring_session.start_date >= start_date:
            return recurring_session.start_date

        # Otherwise, find next occurrence of target weekday
        current_weekday = start_date.weekday()
        days_ahead = (target_weekday - current_weekday) % 7

        if days_ahead == 0:
            # Today is the target weekday
            return start_date
        else:
            # Jump to next target weekday
            return start_date + timedelta(days=days_ahead)

    def _build_instance(
        self, recurring_session: RecurringSession, occurrence_date: date, override: Optional[RecurringOverride] = None
    ) -> SessionInstance:
        """
        Build session instance from recurring template and optional override.

        Override can modify title, notes, start_time, end_time, end_date.
        """
        # Start with base values from recurring session
        title = recurring_session.title
        notes = recurring_session.notes
        start_date = occurrence_date  # Always use occurrence date
        start_time = recurring_session.start_time
        end_date = occurrence_date  # Default: same day
        end_time = recurring_session.end_time
        is_modified = False

        # Apply override modifications
        if override and override.override_type == "modified":
            is_modified = True

            if override.modified_title is not None:
                title = override.modified_title
            if override.modified_notes is not None:
                notes = override.modified_notes
            if override.modified_start_time is not None:
                start_time = override.modified_start_time
            if override.modified_end_time is not None:
                end_time = override.modified_end_time
            if override.modified_end_date is not None:
                end_date = override.modified_end_date
            else:
                # If no end_date override, calculate based on original
                # Check if original was overnight
                if recurring_session.is_overnight:
                    days_diff = (recurring_session.end_date - recurring_session.start_date).days
                    end_date = occurrence_date + timedelta(days=days_diff)
        else:
            # No override, use original overnight logic
            if recurring_session.is_overnight:
                days_diff = (recurring_session.end_date - recurring_session.start_date).days
                end_date = occurrence_date + timedelta(days=days_diff)

        return SessionInstance(
            id=None,  # Generated instances don't have their own ID
            session_type="recurring",
            title=title,
            notes=notes,
            start_date=start_date,
            start_time=start_time,
            end_date=end_date,
            end_time=end_time,
            recurring_session_id=recurring_session.id,
            occurrence_date=occurrence_date,
            is_modified=is_modified,
        )
