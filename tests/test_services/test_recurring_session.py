from fastapi import HTTPException

import pytest
from datetime import date, time

from app.services.recurring_session_service import RecurringSessionService
from app.schemas.recurring_session import RecurringSessionCreate
from app.schemas.override import OverrideCancel, OverrideModify


@pytest.mark.asyncio
class TestRecurringSessionService:
    """Test recurring session operations"""

    async def test_create_recurring_session(self, db_session, sample_recurring_session_data):
        """Test creating recurring session with auto-calculated weekday"""
        service = RecurringSessionService(db_session)
        data = RecurringSessionCreate(**sample_recurring_session_data)

        session = await service.create(data)
        await db_session.commit()

        assert session.recurrence_pattern == "weekly"
        assert session.recurrence_value == 0  # Monday (2025-11-24 is Monday)

    async def test_weekday_calculation(self, db_session):
        """Test that recurrence_value matches start_date weekday"""
        service = RecurringSessionService(db_session)

        # Wednesday session
        data = RecurringSessionCreate(
            title="Wednesday Meeting",
            notes=None,
            start_date=date(2025, 11, 26),  # Wednesday
            start_time=time(14, 0),
            end_date=date(2025, 11, 26),
            end_time=time(15, 0),
            recurrence_pattern="weekly",
        )

        session = await service.create(data)
        await db_session.commit()

        assert session.recurrence_value == 2  # Wednesday = 2

    async def test_cancel_instance(self, db_session, sample_recurring_session_data):
        """Test cancelling specific occurrence"""
        service = RecurringSessionService(db_session)

        # Create recurring session
        data = RecurringSessionCreate(**sample_recurring_session_data)
        session = await service.create(data)
        await db_session.commit()

        # Cancel occurrence on 2025-12-01
        cancel_data = OverrideCancel(occurrence_date=date(2025, 12, 1))
        override = await service.cancel_instance(session.id, cancel_data)
        await db_session.commit()

        assert override.override_type == "cancelled"
        assert override.occurrence_date == date(2025, 12, 1)
        assert override.modified_title is None  # No modifications for cancelled

    async def test_modify_instance_time(self, db_session, sample_recurring_session_data):
        """Test modifying time for specific occurrence"""
        service = RecurringSessionService(db_session)

        # Create recurring session (09:00-09:30)
        data = RecurringSessionCreate(**sample_recurring_session_data)
        session = await service.create(data)
        await db_session.commit()

        # Modify occurrence on 2025-12-01 to 10:00-10:30
        modify_data = OverrideModify(
            occurrence_date=date(2025, 12, 1),
            modified_start_time=time(10, 0),
            modified_end_time=time(10, 30),
        )
        override = await service.modify_instance(session.id, modify_data)
        await db_session.commit()

        assert override.override_type == "modified"
        assert override.modified_start_time == time(10, 0)
        assert override.modified_end_time == time(10, 30)
        assert override.modified_title is None  # Only time changed

    async def test_modify_instance_make_overnight(self, db_session, sample_recurring_session_data):
        """Test making specific occurrence overnight"""
        service = RecurringSessionService(db_session)

        # Create recurring session
        data = RecurringSessionCreate(**sample_recurring_session_data)
        session = await service.create(data)
        await db_session.commit()

        # Make December 1st occurrence overnight (09:00 → next day 06:00)
        modify_data = OverrideModify(
            occurrence_date=date(2025, 12, 1),
            modified_start_time=time(9, 0),
            modified_end_time=time(6, 0),
            modified_end_date=date(2025, 12, 2),  # Next day
        )
        override = await service.modify_instance(session.id, modify_data)
        await db_session.commit()

        assert override.modified_end_date == date(2025, 12, 2)

    async def test_cannot_create_duplicate_override(self, canceled_instance):
        service, session = canceled_instance

        cancel_data = OverrideCancel(occurrence_date=date(2025, 12, 1))
        with pytest.raises(HTTPException) as exc_info:
            await service.cancel_instance(session.id, cancel_data)
        assert exc_info.value.status_code == 409

    async def test_delete_override_restores_instance(self, canceled_instance, db_session):
        service, session = canceled_instance

        await service.delete_override(session.id, date(2025, 12, 1))
        await db_session.commit()

        override = await service.get_override(session.id, date(2025, 12, 1))
        assert override is None
