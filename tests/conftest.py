# tests/conftest.py
from datetime import date

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from httpx import AsyncClient, ASGITransport

from app.models.base import Base
from app.main import app
from app.db.session import get_db
from app.schemas import RecurringSessionCreate, OverrideCancel
from app.services.recurring_session_service import RecurringSessionService

# Test database URL (use separate DB for tests)
TEST_DATABASE_URL = "postgresql+asyncpg://booking_user:booking_pass@localhost:5432/booking_db_test"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    import asyncio

    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_engine():
    """Create test database engine"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop all tables after test
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(db_engine):
    """Create async database session for tests"""
    async_session = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture(scope="function")
async def client(db_session):
    """Create test HTTP client with overridden DB dependency"""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db  # type: ignore[index]

    # Create client with ASGI transport
    async with AsyncClient(
        transport=ASGITransport(app=app),  # type: ignore[arg-type]
        base_url="http://test",
    ) as ac:
        yield ac

    # Cleanup
    app.dependency_overrides.clear()  # type: ignore[index]


# ===== Helper Fixtures =====


@pytest.fixture
def sample_one_time_session_data():
    """Sample data for creating one-time session"""
    return {
        "title": "Team Meeting",
        "notes": "Discuss Q4 plans",
        "start_date": "2025-11-24",
        "start_time": "10:00:00",
        "end_date": "2025-11-24",
        "end_time": "11:00:00",
    }


@pytest.fixture
def sample_recurring_session_data():
    """Sample data for creating recurring session"""
    return {
        "title": "Weekly Standup",
        "notes": "Every Monday",
        "start_date": "2025-11-24",
        "start_time": "09:00:00",
        "end_date": "2025-11-24",
        "end_time": "09:30:00",
        "recurrence_pattern": "weekly",
    }


@pytest.fixture
def night_shift_session_data():
    """Overnight session (22:00 → 06:00 next day)"""
    return {
        "title": "Night Shift",
        "notes": "Security patrol",
        "start_date": "2025-11-24",
        "start_time": "22:00:00",
        "end_date": "2025-11-25",
        "end_time": "06:00:00",
    }


@pytest_asyncio.fixture
async def canceled_instance(db_session, sample_recurring_session_data):
    """Create recurring session with one cancelled instance"""
    service = RecurringSessionService(db_session)

    data = RecurringSessionCreate(**sample_recurring_session_data)
    session = await service.create(data)
    await db_session.commit()

    cancel_data = OverrideCancel(occurrence_date=date(2025, 12, 1))
    await service.cancel_instance(session.id, cancel_data)
    await db_session.commit()

    return service, session
