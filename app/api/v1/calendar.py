from datetime import date

from fastapi import APIRouter, Depends, Query
from app.api.deps import get_calendar_service
from app.services.calendar_service import CalendarService

router = APIRouter(prefix="/calendar", tags=["calendar"])


@router.get("/sessions")
async def get_calendar_sessions(
    start_date: date = Query(...),
    end_date: date = Query(...),
    calendar_service: CalendarService = Depends(get_calendar_service),
):
    sessions = await calendar_service.get_sessions_in_range(start_date, end_date)
    return {"sessions": sessions, "count": len(sessions)}
