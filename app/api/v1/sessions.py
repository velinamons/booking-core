from datetime import date

from fastapi import APIRouter, Depends, Path, status

from app.api.deps import get_one_time_session_service, get_recurring_session_service
from app.schemas import (
    OneTimeSessionCreate,
    OneTimeSessionUpdate,
    OneTimeSessionResponse,
    RecurringSessionCreate,
    RecurringSessionResponse,
    OverrideCancel,
    OverrideModify,
    OverrideResponse,
)
from app.services.one_time_session_service import OneTimeSessionService
from app.services.recurring_session_service import RecurringSessionService

router = APIRouter(prefix="/sessions", tags=["sessions"])


# ========== ONE-TIME SESSIONS ==========


@router.post(
    "/one-time",
    response_model=OneTimeSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create one-time session",
)
async def create_one_time_session(
    data: OneTimeSessionCreate, service: OneTimeSessionService = Depends(get_one_time_session_service)
):
    """Create a new one-time session"""
    return await service.create(data)


@router.get("/one-time/{session_id}", response_model=OneTimeSessionResponse, summary="Get one-time session")
async def get_one_time_session(
    session_id: int = Path(..., ge=1), service: OneTimeSessionService = Depends(get_one_time_session_service)
):
    """Get one-time session by ID"""
    return await service.get(session_id)


@router.put("/one-time/{session_id}", response_model=OneTimeSessionResponse, summary="Update one-time session")
async def update_one_time_session(
    data: OneTimeSessionUpdate,
    session_id: int = Path(..., ge=1),
    service: OneTimeSessionService = Depends(get_one_time_session_service),
):
    """Update one-time session (partial update supported)"""
    return await service.update(session_id, data)


@router.delete("/one-time/{session_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete one-time session")
async def delete_one_time_session(
    session_id: int = Path(..., ge=1), service: OneTimeSessionService = Depends(get_one_time_session_service)
):
    """Delete one-time session permanently"""
    await service.delete(session_id)


@router.get("/one-time", response_model=list[OneTimeSessionResponse], summary="List one-time sessions")
async def list_one_time_sessions(
    limit: int = 100, offset: int = 0, service: OneTimeSessionService = Depends(get_one_time_session_service)
):
    """List all one-time sessions (paginated)"""
    return await service.list_all(limit=limit, offset=offset)


# ========== RECURRING SESSIONS ==========


@router.post(
    "/recurring",
    response_model=RecurringSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create recurring session",
)
async def create_recurring_session(
    data: RecurringSessionCreate, service: RecurringSessionService = Depends(get_recurring_session_service)
):
    """
    Create a new recurring session (weekly).

    The weekday is automatically determined from start_date.
    """
    return await service.create(data)


@router.get("/recurring/{session_id}", response_model=RecurringSessionResponse, summary="Get recurring session")
async def get_recurring_session(
    session_id: int = Path(..., ge=1), service: RecurringSessionService = Depends(get_recurring_session_service)
):
    """Get recurring session template by ID"""
    return await service.get(session_id)


@router.delete("/recurring/{session_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete recurring session")
async def delete_recurring_session(
    session_id: int = Path(..., ge=1), service: RecurringSessionService = Depends(get_recurring_session_service)
):
    """
    Delete recurring session and all its overrides.

    This removes the entire series.
    """
    await service.delete(session_id)


@router.get("/recurring", response_model=list[RecurringSessionResponse], summary="List recurring sessions")
async def list_recurring_sessions(
    limit: int = 100, offset: int = 0, service: RecurringSessionService = Depends(get_recurring_session_service)
):
    """List all recurring session templates (paginated)"""
    return await service.list_all(limit=limit, offset=offset)


# ========== OVERRIDES (Instance Modifications) ==========


@router.post(
    "/recurring/{session_id}/overrides/cancel",
    response_model=OverrideResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cancel specific occurrence",
)
async def cancel_recurring_instance(
    data: OverrideCancel,
    session_id: int = Path(..., ge=1),
    service: RecurringSessionService = Depends(get_recurring_session_service),
):
    """
    Cancel a specific occurrence of recurring session.

    The instance will not appear in calendar queries.
    """
    return await service.cancel_instance(session_id, data)


@router.post(
    "/recurring/{session_id}/overrides/modify",
    response_model=OverrideResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Modify specific occurrence",
)
async def modify_recurring_instance(
    data: OverrideModify,
    session_id: int = Path(..., ge=1),
    service: RecurringSessionService = Depends(get_recurring_session_service),
):
    """
    Modify a specific occurrence of recurring session.

    Can change title, notes, time, and/or make it overnight.
    At least one modification must be provided.
    """
    return await service.modify_instance(session_id, data)


@router.get(
    "/recurring/{session_id}/overrides/{occurrence_date}",
    response_model=OverrideResponse,
    summary="Get override for specific date",
)
async def get_override(
    session_id: int = Path(..., ge=1),
    occurrence_date: date = Path(...),
    service: RecurringSessionService = Depends(get_recurring_session_service),
):
    """Get override (if exists) for specific occurrence date"""
    override = await service.get_override(session_id, occurrence_date)
    if not override:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Override not found")
    return override


@router.delete(
    "/recurring/{session_id}/overrides/{occurrence_date}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete override (restore original)",
)
async def delete_override(
    session_id: int = Path(..., ge=1),
    occurrence_date: date = Path(...),
    service: RecurringSessionService = Depends(get_recurring_session_service),
):
    """
    Delete override for specific occurrence.

    This restores the instance to its original state from the template.
    """
    await service.delete_override(session_id, occurrence_date)


@router.get(
    "/recurring/{session_id}/overrides", response_model=list[OverrideResponse], summary="List all overrides for session"
)
async def list_overrides(
    session_id: int = Path(..., ge=1),
    limit: int = 100,
    offset: int = 0,
    service: RecurringSessionService = Depends(get_recurring_session_service),
):
    """List all overrides for a recurring session"""
    return await service.list_overrides(session_id, limit=limit, offset=offset)
