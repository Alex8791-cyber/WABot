"""Google Calendar API wrapper — CRUD operations and availability queries."""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from config import GOOGLE_CREDENTIALS_FILE, GOOGLE_CALENDAR_ID

logger = logging.getLogger("service_bot")

_SCOPES = ["https://www.googleapis.com/auth/calendar"]


def is_configured() -> bool:
    return bool(GOOGLE_CREDENTIALS_FILE)


def _get_service():
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    credentials = service_account.Credentials.from_service_account_file(
        GOOGLE_CREDENTIALS_FILE, scopes=_SCOPES,
    )
    return build("calendar", "v3", credentials=credentials)


def list_events(time_min: str, time_max: str, max_results: int = 20) -> Dict[str, Any]:
    if not is_configured():
        return {"error": "Google Calendar not configured"}
    try:
        service = _get_service()
        result = service.events().list(
            calendarId=GOOGLE_CALENDAR_ID, timeMin=time_min, timeMax=time_max,
            maxResults=max_results, singleEvents=True, orderBy="startTime",
        ).execute()
        events = []
        for ev in result.get("items", []):
            events.append({
                "id": ev.get("id"),
                "summary": ev.get("summary", "(No title)"),
                "start": ev.get("start", {}).get("dateTime", ev.get("start", {}).get("date", "")),
                "end": ev.get("end", {}).get("dateTime", ev.get("end", {}).get("date", "")),
                "description": ev.get("description", ""),
            })
        return {"events": events}
    except Exception as e:
        logger.error("Failed to list events: %s", e)
        return {"error": str(e)}


def create_event(summary: str, start: str, end: str, description: str = "", attendee_email: Optional[str] = None) -> Dict[str, Any]:
    if not is_configured():
        return {"error": "Google Calendar not configured"}
    try:
        body = {"summary": summary, "start": {"dateTime": start}, "end": {"dateTime": end}, "description": description}
        if attendee_email:
            body["attendees"] = [{"email": attendee_email}]
        service = _get_service()
        event = service.events().insert(calendarId=GOOGLE_CALENDAR_ID, body=body).execute()
        return {"id": event["id"], "status": event.get("status", "confirmed"), "link": event.get("htmlLink", "")}
    except Exception as e:
        logger.error("Failed to create event: %s", e)
        return {"error": str(e)}


def update_event(event_id: str, summary: Optional[str] = None, start: Optional[str] = None, end: Optional[str] = None, description: Optional[str] = None) -> Dict[str, Any]:
    if not is_configured():
        return {"error": "Google Calendar not configured"}
    try:
        body = {}
        if summary is not None: body["summary"] = summary
        if start is not None: body["start"] = {"dateTime": start}
        if end is not None: body["end"] = {"dateTime": end}
        if description is not None: body["description"] = description
        service = _get_service()
        event = service.events().patch(calendarId=GOOGLE_CALENDAR_ID, eventId=event_id, body=body).execute()
        return {"id": event["id"], "status": event.get("status", "confirmed"), "summary": event.get("summary", "")}
    except Exception as e:
        logger.error("Failed to update event: %s", e)
        return {"error": str(e)}


def delete_event(event_id: str) -> Dict[str, Any]:
    if not is_configured():
        return {"error": "Google Calendar not configured"}
    try:
        service = _get_service()
        service.events().delete(calendarId=GOOGLE_CALENDAR_ID, eventId=event_id).execute()
        return {"status": "deleted", "event_id": event_id}
    except Exception as e:
        logger.error("Failed to delete event: %s", e)
        return {"error": str(e)}


def get_available_slots(time_min: str, time_max: str, duration_minutes: int = 60) -> Dict[str, Any]:
    if not is_configured():
        return {"error": "Google Calendar not configured"}
    try:
        service = _get_service()
        body = {"timeMin": time_min, "timeMax": time_max, "items": [{"id": GOOGLE_CALENDAR_ID}]}
        result = service.freebusy().query(body=body).execute()
        busy = result.get("calendars", {}).get(GOOGLE_CALENDAR_ID, {}).get("busy", [])

        slot_duration = timedelta(minutes=duration_minutes)
        range_start = datetime.fromisoformat(time_min.replace("Z", "+00:00"))
        range_end = datetime.fromisoformat(time_max.replace("Z", "+00:00"))

        busy_parsed = []
        for b in busy:
            bs = datetime.fromisoformat(b["start"].replace("Z", "+00:00"))
            be = datetime.fromisoformat(b["end"].replace("Z", "+00:00"))
            busy_parsed.append((bs, be))
        busy_parsed.sort()

        slots = []
        current = range_start
        for busy_start, busy_end in busy_parsed:
            while current + slot_duration <= busy_start:
                slots.append({
                    "start": current.isoformat().replace("+00:00", "Z"),
                    "end": (current + slot_duration).isoformat().replace("+00:00", "Z"),
                })
                current += slot_duration
            current = max(current, busy_end)
        while current + slot_duration <= range_end:
            slots.append({
                "start": current.isoformat().replace("+00:00", "Z"),
                "end": (current + slot_duration).isoformat().replace("+00:00", "Z"),
            })
            current += slot_duration

        return {"slots": slots}
    except Exception as e:
        logger.error("Failed to get available slots: %s", e)
        return {"error": str(e)}
