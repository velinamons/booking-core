from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models import OneTimeSession
from app.schemas.one_time_session import OneTimeSessionCreate, OneTimeSessionUpdate


class OneTimeSessionService:
    """Service for one-time session operations (CRUD)"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: OneTimeSessionCreate) -> OneTimeSession:
        """Create new one-time session"""
        session = OneTimeSession(
            title=data.title,
            notes=data.notes,
            start_date=data.start_date,
            start_time=data.start_time,
            end_date=data.end_date,
            end_time=data.end_time,
        )

        self.db.add(session)
        await self.db.flush()  # Get ID without committing
        await self.db.refresh(session)  # Load defaults (created_at, etc.)

        return session

    async def get(self, session_id: int) -> OneTimeSession:
        """Get one-time session by ID"""
        stmt = select(OneTimeSession).where(OneTimeSession.id == session_id)
        result = await self.db.execute(stmt)
        session = result.scalar_one_or_none()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"One-time session with id={session_id} not found"
            )

        return session

    async def update(self, session_id: int, data: OneTimeSessionUpdate) -> OneTimeSession:
        """Update one-time session"""
        session = await self.get(session_id)  # Will raise 404 if not found

        # Update only provided fields
        if data.title is not None:
            session.title = data.title
        if data.notes is not None:
            session.notes = data.notes

        # DateTime fields - must be all provided or none
        if data.start_date is not None:  # All 4 validated in schema
            session.start_date = data.start_date
            session.start_time = data.start_time
            session.end_date = data.end_date
            session.end_time = data.end_time

        await self.db.flush()
        await self.db.refresh(session)

        return session

    async def delete(self, session_id: int) -> None:
        """Delete one-time session"""
        # Check if exists
        await self.get(session_id)

        # Delete
        stmt = delete(OneTimeSession).where(OneTimeSession.id == session_id)
        await self.db.execute(stmt)
        await self.db.flush()

    async def list_all(self, limit: int = 100, offset: int = 0) -> list[OneTimeSession]:
        """List all one-time sessions (paginated)"""
        stmt = (
            select(OneTimeSession)
            .order_by(OneTimeSession.start_date, OneTimeSession.start_time)
            .limit(limit)
            .offset(offset)
        )

        result = await self.db.execute(stmt)
        return list(result.scalars().all())
