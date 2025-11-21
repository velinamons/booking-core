# app/api/deps.py
from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.calendar_service import CalendarService
from app.services.one_time_session_service import OneTimeSessionService
from app.services.recurring_session_service import RecurringSessionService


# ===== Database dependency =====
# Already have get_db in db/session.py, can re-export here
async def get_database() -> AsyncGenerator[AsyncSession, None]:
    """Re-export database dependency"""
    async for session in get_db():
        yield session


# ===== Service dependencies =====
def get_calendar_service(db: AsyncSession = Depends(get_database)) -> CalendarService:
    """Factory for CalendarService"""
    return CalendarService(db)


def get_one_time_session_service(db: AsyncSession = Depends(get_database)) -> OneTimeSessionService:
    """Factory for OneTimeSessionService"""
    return OneTimeSessionService(db)


def get_recurring_session_service(db: AsyncSession = Depends(get_database)) -> RecurringSessionService:
    """Factory for RecurringSessionService"""
    return RecurringSessionService(db)
