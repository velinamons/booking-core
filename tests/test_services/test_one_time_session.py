# tests/test_services/test_one_time_session.py
import pytest
from datetime import date, time

from app.services.one_time_session_service import OneTimeSessionService
from app.schemas.one_time_session import OneTimeSessionCreate, OneTimeSessionUpdate


@pytest.mark.asyncio
class TestOneTimeSessionService:
    """Test one-time session CRUD operations"""

    async def test_create_regular_session(self, db_session, sample_one_time_session_data):
        """Test creating regular same-day session"""
        service = OneTimeSessionService(db_session)
        data = OneTimeSessionCreate(**sample_one_time_session_data)

        session = await service.create(data)
        await db_session.commit()

        assert session.id is not None
        assert session.title == "Team Meeting"
        assert session.start_date == date(2025, 11, 24)
        assert not session.is_overnight

    async def test_create_overnight_session(self, db_session, night_shift_session_data):
        """Test creating overnight session (crosses midnight)"""
        service = OneTimeSessionService(db_session)
        data = OneTimeSessionCreate(**night_shift_session_data)

        session = await service.create(data)
        await db_session.commit()

        assert session.is_overnight
        assert session.start_date == date(2025, 11, 24)
        assert session.end_date == date(2025, 11, 25)
        assert session.duration_hours == 8.0

    async def test_create_multi_day_session(self, db_session):
        """Test session spanning 3+ days (e.g., conference)"""
        service = OneTimeSessionService(db_session)
        data = OneTimeSessionCreate(
            title="Conference",
            notes="3-day event",
            start_date=date(2025, 11, 24),
            start_time=time(9, 0),
            end_date=date(2025, 11, 26),  # +2 days
            end_time=time(17, 0),
        )

        session = await service.create(data)
        await db_session.commit()

        assert session.is_overnight
        assert session.duration_hours == 56.0  # 48h + 8h

    async def test_update_partial_fields(self, db_session, sample_one_time_session_data):
        """Test partial update (only title and notes)"""
        service = OneTimeSessionService(db_session)

        # Create
        data = OneTimeSessionCreate(**sample_one_time_session_data)
        session = await service.create(data)
        await db_session.commit()

        # Update only title
        update_data = OneTimeSessionUpdate(title="Updated Meeting")
        updated = await service.update(session.id, update_data)
        await db_session.commit()

        assert updated.title == "Updated Meeting"
        assert updated.start_date == date(2025, 11, 24)  # Unchanged

    async def test_update_datetime_requires_all_fields(self, db_session, sample_one_time_session_data):
        """Test that updating datetime requires all 4 fields"""
        service = OneTimeSessionService(db_session)

        # Create
        data = OneTimeSessionCreate(**sample_one_time_session_data)
        _ = await service.create(data)
        await db_session.commit()

        # Try to update only start_time (should fail validation)
        with pytest.raises(ValueError, match="Must provide all datetime fields"):
            OneTimeSessionUpdate(start_time=time(11, 0))

    async def test_delete_session(self, db_session, sample_one_time_session_data):
        """Test deleting session"""
        service = OneTimeSessionService(db_session)

        # Create
        data = OneTimeSessionCreate(**sample_one_time_session_data)
        session = await service.create(data)
        await db_session.commit()

        # Delete
        await service.delete(session.id)
        await db_session.commit()

        # Verify deleted
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await service.get(session.id)
        assert exc_info.value.status_code == 404
