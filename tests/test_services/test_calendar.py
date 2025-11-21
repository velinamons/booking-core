# tests/test_services/test_calendar.py
import pytest
from datetime import date, time, timedelta

from app.services.calendar_service import CalendarService
from app.services.one_time_session_service import OneTimeSessionService
from app.services.recurring_session_service import RecurringSessionService
from app.schemas.one_time_session import OneTimeSessionCreate
from app.schemas.recurring_session import RecurringSessionCreate
from app.schemas.override import OverrideCancel, OverrideModify


@pytest.mark.asyncio
class TestCalendarService:
    """Test calendar generation with various scenarios"""

    async def test_calendar_empty_range(self, db_session):
        """Test calendar with no sessions"""
        service = CalendarService(db_session)

        sessions = await service.get_sessions_in_range(start_date=date(2025, 12, 1), end_date=date(2025, 12, 7))

        assert sessions == []

    async def test_calendar_one_time_only(self, db_session, sample_one_time_session_data):
        """Test calendar with only one-time sessions"""
        one_time_service = OneTimeSessionService(db_session)
        calendar_service = CalendarService(db_session)

        # Create 3 one-time sessions
        dates = [date(2025, 12, 1), date(2025, 12, 3), date(2025, 12, 5)]
        for d in dates:
            data = OneTimeSessionCreate(
                **{**sample_one_time_session_data, "start_date": d.isoformat(), "end_date": d.isoformat()}
            )
            await one_time_service.create(data)
        await db_session.commit()

        # Get calendar
        sessions = await calendar_service.get_sessions_in_range(
            start_date=date(2025, 12, 1), end_date=date(2025, 12, 7)
        )

        assert len(sessions) == 3
        assert all(s["session_type"] == "one_time" for s in sessions)

    async def test_calendar_recurring_only(self, db_session, sample_recurring_session_data):
        """Test calendar with recurring sessions (no overrides)"""
        recurring_service = RecurringSessionService(db_session)
        calendar_service = CalendarService(db_session)

        # Create recurring session (every Monday)
        data = RecurringSessionCreate(**sample_recurring_session_data)
        _ = await recurring_service.create(data)
        await db_session.commit()

        # Get calendar for 4 weeks (should have 4 Mondays)
        sessions = await calendar_service.get_sessions_in_range(
            start_date=date(2025, 11, 24),  # Monday
            end_date=date(2025, 12, 21),  # 4 weeks later
        )

        # Should have 4 instances (4 Mondays)
        monday_sessions = [s for s in sessions if s["session_type"] == "recurring"]
        assert len(monday_sessions) == 4

        # Verify dates are Mondays
        for s in monday_sessions:
            session_date = date.fromisoformat(s["start_date"])
            assert session_date.weekday() == 0  # Monday

    async def test_calendar_recurring_with_cancelled(self, db_session, sample_recurring_session_data):
        """Test calendar with cancelled recurring instance"""
        recurring_service = RecurringSessionService(db_session)
        calendar_service = CalendarService(db_session)

        # Create recurring session
        data = RecurringSessionCreate(**sample_recurring_session_data)
        session = await recurring_service.create(data)
        await db_session.commit()

        # Cancel second occurrence (2025-12-01)
        cancel_data = OverrideCancel(occurrence_date=date(2025, 12, 1))
        await recurring_service.cancel_instance(session.id, cancel_data)
        await db_session.commit()

        # Get calendar for 4 weeks
        sessions = await calendar_service.get_sessions_in_range(
            start_date=date(2025, 11, 24), end_date=date(2025, 12, 21)
        )

        # Should have 3 instances (1 cancelled)
        monday_sessions = [s for s in sessions if s["session_type"] == "recurring"]
        assert len(monday_sessions) == 3

        # Verify 2025-12-01 is NOT in results
        dates = [date.fromisoformat(s["start_date"]) for s in monday_sessions]
        assert date(2025, 12, 1) not in dates

    async def test_calendar_recurring_with_modified(self, db_session, sample_recurring_session_data):
        """Test calendar with modified recurring instance"""
        recurring_service = RecurringSessionService(db_session)
        calendar_service = CalendarService(db_session)

        # Create recurring session (09:00-09:30)
        data = RecurringSessionCreate(**sample_recurring_session_data)
        session = await recurring_service.create(data)
        await db_session.commit()

        # Modify second occurrence to 14:00-15:00
        modify_data = OverrideModify(
            occurrence_date=date(2025, 12, 1),
            modified_start_time=time(14, 0),
            modified_end_time=time(15, 0),
        )
        await recurring_service.modify_instance(session.id, modify_data)
        await db_session.commit()

        # Get calendar
        sessions = await calendar_service.get_sessions_in_range(
            start_date=date(2025, 11, 24), end_date=date(2025, 12, 7)
        )

        # Find modified instance
        modified = next(s for s in sessions if date.fromisoformat(s["start_date"]) == date(2025, 12, 1))

        assert modified["start_time"] == "14:00:00"  # Modified time
        assert modified["end_time"] == "15:00:00"
        assert modified["is_modified"] is True

    async def test_calendar_overnight_session_in_range(self, db_session):
        """Test that overnight session appears in correct date range"""
        one_time_service = OneTimeSessionService(db_session)
        calendar_service = CalendarService(db_session)

        # Create overnight session: Nov 30 22:00 → Dec 1 06:00
        data = OneTimeSessionCreate(
            title="Night Shift",
            notes=None,
            start_date=date(2025, 11, 30),
            start_time=time(22, 0),
            end_date=date(2025, 12, 1),
            end_time=time(6, 0),
        )
        await one_time_service.create(data)
        await db_session.commit()

        # Query Dec 1-7 (should include the overnight session)
        sessions = await calendar_service.get_sessions_in_range(
            start_date=date(2025, 12, 1), end_date=date(2025, 12, 7)
        )

        assert len(sessions) == 1
        assert sessions[0]["start_date"] == "2025-11-30"  # Starts Nov 30
        assert sessions[0]["end_date"] == "2025-12-01"  # Ends Dec 1

    async def test_calendar_recurring_overnight_template(self, db_session):
        """Test recurring session with overnight template"""
        recurring_service = RecurringSessionService(db_session)
        calendar_service = CalendarService(db_session)

        # Create recurring overnight session (every Monday 22:00 → Tuesday 06:00)
        data = RecurringSessionCreate(
            title="Weekly Night Shift",
            notes=None,
            start_date=date(2025, 11, 24),  # Monday
            start_time=time(22, 0),
            end_date=date(2025, 11, 25),  # Tuesday
            end_time=time(6, 0),
            recurrence_pattern="weekly",
        )
        _ = await recurring_service.create(data)
        await db_session.commit()

        # Get calendar for 2 weeks
        sessions = await calendar_service.get_sessions_in_range(
            start_date=date(2025, 11, 24), end_date=date(2025, 12, 7)
        )

        # Should have 2 overnight instances
        assert len(sessions) == 2

        for s in sessions:
            start = date.fromisoformat(s["start_date"])
            end = date.fromisoformat(s["end_date"])
            assert start.weekday() == 0  # Monday
            assert end == start + timedelta(days=1)  # Next day

    async def test_calendar_far_future_date(self, db_session, sample_recurring_session_data):
        """Test calendar generation for far future (2028) - per task requirements"""
        recurring_service = RecurringSessionService(db_session)
        calendar_service = CalendarService(db_session)

        # Create recurring session
        data = RecurringSessionCreate(**sample_recurring_session_data)
        _ = await recurring_service.create(data)
        await db_session.commit()

        # Get calendar for one month in 2028
        sessions = await calendar_service.get_sessions_in_range(start_date=date(2028, 1, 1), end_date=date(2028, 1, 31))

        # Should have 5 Mondays in January 2028
        monday_sessions = [s for s in sessions if date.fromisoformat(s["start_date"]).weekday() == 0]
        assert len(monday_sessions) == 5

    async def test_calendar_mixed_sessions_sorted(self, db_session):
        """Test that calendar returns sessions sorted by datetime"""
        one_time_service = OneTimeSessionService(db_session)
        recurring_service = RecurringSessionService(db_session)
        calendar_service = CalendarService(db_session)

        # Create one-time at 14:00
        one_time_data = OneTimeSessionCreate(
            title="Afternoon Meeting",
            notes=None,
            start_date=date(2025, 12, 1),
            start_time=time(14, 0),
            end_date=date(2025, 12, 1),
            end_time=time(15, 0),
        )
        await one_time_service.create(one_time_data)

        # Create recurring at 09:00 (same day)
        recurring_data = RecurringSessionCreate(
            title="Morning Standup",
            notes=None,
            start_date=date(2025, 12, 1),  # Monday
            start_time=time(9, 0),
            end_date=date(2025, 12, 1),
            end_time=time(9, 30),
            recurrence_pattern="weekly",
        )
        await recurring_service.create(recurring_data)
        await db_session.commit()

        # Get calendar
        sessions = await calendar_service.get_sessions_in_range(
            start_date=date(2025, 12, 1), end_date=date(2025, 12, 1)
        )

        # Should have 2 sessions, sorted by time
        assert len(sessions) == 2
        assert sessions[0]["start_time"] == "09:00:00"  # Morning first
        assert sessions[1]["start_time"] == "14:00:00"  # Afternoon second

    async def test_calendar_performance_large_range(self, db_session, sample_recurring_session_data):
        """Test calendar generation performance for 1 year range"""
        recurring_service = RecurringSessionService(db_session)
        calendar_service = CalendarService(db_session)

        # Create recurring session
        data = RecurringSessionCreate(**sample_recurring_session_data)
        await recurring_service.create(data)
        await db_session.commit()

        # Get calendar for 1 year (should generate ~52 instances)
        import time as time_module

        start_time = time_module.time()

        sessions = await calendar_service.get_sessions_in_range(
            start_date=date(2025, 1, 1), end_date=date(2025, 12, 31)
        )

        elapsed = time_module.time() - start_time

        # Should have ~52 Mondays in 2025
        assert 50 <= len(sessions) <= 54
        # Should complete in under 1 second
        assert elapsed < 1.0
