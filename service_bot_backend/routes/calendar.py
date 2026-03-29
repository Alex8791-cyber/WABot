"""REST endpoints for Google Calendar — used by Flutter frontend."""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from auth import require_admin
from services import calendar

router = APIRouter(prefix="/calendar", tags=["calendar"])


class CreateEventRequest(BaseModel):
    summary: str
    start: str
    end: str
    description: str = ""
    attendee_email: Optional[str] = None


class UpdateEventRequest(BaseModel):
    summary: Optional[str] = None
    start: Optional[str] = None
    end: Optional[str] = None
    description: Optional[str] = None


@router.get("/events")
def get_events(
    start: str = Query(..., description="ISO 8601 start time"),
    end: str = Query(..., description="ISO 8601 end time"),
):
    return calendar.list_events(time_min=start, time_max=end)


@router.get("/slots")
def get_available_slots(
    start: str = Query(...),
    end: str = Query(...),
    duration: int = Query(60, description="Slot duration in minutes"),
):
    return calendar.get_available_slots(time_min=start, time_max=end, duration_minutes=duration)


@router.post("/events", status_code=201, dependencies=[Depends(require_admin)])
def create_event(req: CreateEventRequest):
    return calendar.create_event(
        summary=req.summary, start=req.start, end=req.end,
        description=req.description, attendee_email=req.attendee_email,
    )


@router.patch("/events/{event_id}", dependencies=[Depends(require_admin)])
def update_event(event_id: str, req: UpdateEventRequest):
    return calendar.update_event(
        event_id=event_id, summary=req.summary, start=req.start,
        end=req.end, description=req.description,
    )


@router.delete("/events/{event_id}", dependencies=[Depends(require_admin)])
def delete_event(event_id: str):
    return calendar.delete_event(event_id=event_id)
