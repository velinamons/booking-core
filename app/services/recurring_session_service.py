# app/services/recurring_session_service.py
from datetime import date
from typing import Optional

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models import RecurringSession, RecurringOverride
from app.schemas.recurring_session import RecurringSessionCreate
from app.schemas.override import OverrideCancel, OverrideModify


class RecurringSessionService:
    """Service for recurring session operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: RecurringSessionCreate) -> RecurringSession:
        """
        Create new recurring session.

        Automatically calculates recurrence_value from start_date.weekday().
        """
        # Calculate recurrence_value (0=Monday, 6=Sunday)
        recurrence_value = data.start_date.weekday()

        session = RecurringSession(
            title=data.title,
            notes=data.notes,
            start_date=data.start_date,
            start_time=data.start_time,
            end_date=data.end_date,
            end_time=data.end_time,
            recurrence_pattern=data.recurrence_pattern,
            recurrence_value=recurrence_value,
        )

        self.db.add(session)
        await self.db.flush()
        await self.db.refresh(session)

        return session

    async def get(self, session_id: int) -> RecurringSession:
        """Get recurring session by ID"""
        stmt = select(RecurringSession).where(RecurringSession.id == session_id)
        result = await self.db.execute(stmt)
        session = result.scalar_one_or_none()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Recurring session with id={session_id} not found"
            )

        return session

    async def delete(self, session_id: int) -> None:
        """
        Delete recurring session.

        Also deletes all overrides (CASCADE).
        """
        # Check if exists
        await self.get(session_id)

        # Delete (CASCADE will remove overrides)
        stmt = delete(RecurringSession).where(RecurringSession.id == session_id)
        await self.db.execute(stmt)
        await self.db.flush()

    async def list_all(self, limit: int = 100, offset: int = 0) -> list[RecurringSession]:
        """List all recurring sessions (paginated)"""
        stmt = select(RecurringSession).order_by(RecurringSession.start_date).limit(limit).offset(offset)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    # ===== OVERRIDE OPERATIONS =====

    async def cancel_instance(self, session_id: int, data: OverrideCancel) -> RecurringOverride:
        """
        Cancel specific occurrence of recurring session.

        Creates override with type='cancelled'.
        """
        # Verify recurring session exists
        await self.get(session_id)

        # Check if override already exists for this date
        existing = await self._get_override_for_date(session_id, data.occurrence_date)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=f"Override already exists for date {data.occurrence_date}"
            )

        # Create cancelled override
        override = RecurringOverride(
            recurring_session_id=session_id,
            occurrence_date=data.occurrence_date,
            override_type="cancelled",
            # All modified_* fields remain NULL
        )

        self.db.add(override)
        await self.db.flush()
        await self.db.refresh(override)

        return override

    async def modify_instance(self, session_id: int, data: OverrideModify) -> RecurringOverride:
        """
        Modify specific occurrence of recurring session.

        Creates override with type='modified' and partial modifications.
        """
        # Verify recurring session exists
        await self.get(session_id)

        # Check if override already exists
        existing = await self._get_override_for_date(session_id, data.occurrence_date)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=f"Override already exists for date {data.occurrence_date}"
            )

        # Create modified override
        override = RecurringOverride(
            recurring_session_id=session_id,
            occurrence_date=data.occurrence_date,
            override_type="modified",
            modified_title=data.modified_title,
            modified_notes=data.modified_notes,
            modified_start_time=data.modified_start_time,
            modified_end_time=data.modified_end_time,
            modified_end_date=data.modified_end_date,
        )

        self.db.add(override)
        await self.db.flush()
        await self.db.refresh(override)

        return override

    async def delete_override(self, session_id: int, occurrence_date: date) -> None:
        """
        Delete override for specific occurrence.

        This restores the instance to its original state from template.
        """
        # Verify recurring session exists
        await self.get(session_id)

        # Get override
        override = await self._get_override_for_date(session_id, occurrence_date)
        if not override:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"No override found for date {occurrence_date}"
            )

        # Delete override
        stmt = delete(RecurringOverride).where(RecurringOverride.id == override.id)
        await self.db.execute(stmt)
        await self.db.flush()

    async def get_override(self, session_id: int, occurrence_date: date) -> Optional[RecurringOverride]:
        """Get override for specific occurrence (public method)"""
        await self.get(session_id)  # Verify session exists
        return await self._get_override_for_date(session_id, occurrence_date)

    async def list_overrides(self, session_id: int, limit: int = 100, offset: int = 0) -> list[RecurringOverride]:
        """List all overrides for recurring session"""
        # Verify session exists
        await self.get(session_id)

        stmt = (
            select(RecurringOverride)
            .where(RecurringOverride.recurring_session_id == session_id)
            .order_by(RecurringOverride.occurrence_date)
            .limit(limit)
            .offset(offset)
        )

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    # ===== PRIVATE HELPERS =====

    async def _get_override_for_date(self, session_id: int, occurrence_date: date) -> Optional[RecurringOverride]:
        """Internal helper to get override"""
        stmt = select(RecurringOverride).where(
            RecurringOverride.recurring_session_id == session_id, RecurringOverride.occurrence_date == occurrence_date
        )

        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
