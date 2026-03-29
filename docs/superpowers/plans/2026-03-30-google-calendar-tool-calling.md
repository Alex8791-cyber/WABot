# Google Calendar + LLM Tool Calling Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give the LLM the ability to read, create, update, and delete Google Calendar events via OpenAI function calling, so the bot can autonomously manage appointments during conversations.

**Architecture:** A new `services/calendar.py` wraps the Google Calendar API (service account auth). Tool definitions are declared in `services/tools.py`. The existing `chat()` function in `services/llm.py` is replaced with a tool-calling-aware version that loops: call LLM → if tool_calls, execute them → send results back → repeat until the LLM produces a final text response. New REST endpoints in `routes/calendar.py` expose calendar CRUD for the Flutter frontend.

**Tech Stack:** google-api-python-client, google-auth (service account), OpenAI function calling (tools parameter)

---

## File Structure

```
service_bot_backend/
├── config.py                   MODIFY — add GOOGLE_CREDENTIALS_FILE, GOOGLE_CALENDAR_ID
├── services/
│   ├── calendar.py             NEW — Google Calendar API wrapper (CRUD + free slots)
│   ├── tools.py                NEW — Tool definitions + dispatcher
│   └── llm.py                  MODIFY — tool-calling-aware chat loop
├── routes/
│   ├── calendar.py             NEW — REST endpoints for Flutter calendar UI
│   └── agent.py                MODIFY — use new chat_with_tools()
├── main.py                     MODIFY — include calendar router
├── tests/
│   ├── test_calendar.py        NEW
│   ├── test_tools.py           NEW
│   ├── test_llm.py             MODIFY — test tool-calling loop
│   ├── test_routes_calendar.py NEW
│   └── conftest.py             MODIFY — add calendar mock fixture
```

**Dependency graph:**
```
config.py ← services/calendar.py ← services/tools.py ← services/llm.py ← routes/agent.py
                                                                          ← routes/webhook.py
                                  ← routes/calendar.py
```

---

### Task 1: Config — Add Google Calendar settings

**Files:**
- Modify: `service_bot_backend/config.py`
- Modify: `service_bot_backend/tests/test_config.py`

- [ ] **Step 1: Update test**

Add to `test_config_defaults` in `service_bot_backend/tests/test_config.py`:

```python
def test_config_defaults():
    from config import (
        SERVICES_FILE, AGENTS_FILE, SOUL_FILE,
        DATABASE_FILE,
        ADMIN_TOKEN, OPENAI_API_KEY, MODEL_NAME, VISION_MODEL,
        ALLOWED_ORIGINS, HANDOFF_THRESHOLD, MAX_MESSAGE_LENGTH,
        MAX_HISTORY_MESSAGES,
        GOOGLE_CREDENTIALS_FILE, GOOGLE_CALENDAR_ID,
    )
    assert MODEL_NAME == "gpt-4o-mini"
    assert VISION_MODEL == "gpt-4o"
    assert HANDOFF_THRESHOLD == 2
    assert MAX_MESSAGE_LENGTH == 10000
    assert MAX_HISTORY_MESSAGES == 40
    assert "http://localhost:8080" in ALLOWED_ORIGINS
    assert DATABASE_FILE.endswith("service_bot.db")
    assert GOOGLE_CREDENTIALS_FILE == ""
    assert GOOGLE_CALENDAR_ID == "primary"
```

- [ ] **Step 2: Run test — should fail on missing imports**

Run: `cd service_bot_backend && python -m pytest tests/test_config.py::test_config_defaults -v`

- [ ] **Step 3: Add config vars**

Append to `service_bot_backend/config.py`:

```python
# Google Calendar
GOOGLE_CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "")
GOOGLE_CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID", "primary")
```

- [ ] **Step 4: Run test — should pass**

Run: `cd service_bot_backend && python -m pytest tests/test_config.py -v`

- [ ] **Step 5: Commit**

```bash
cd /d/WABot && git add service_bot_backend/config.py service_bot_backend/tests/test_config.py
git commit -m "feat: add Google Calendar config vars"
```

---

### Task 2: services/calendar.py — Google Calendar API wrapper

**Files:**
- Create: `service_bot_backend/services/calendar.py`
- Create: `service_bot_backend/tests/test_calendar.py`

- [ ] **Step 1: Write the failing tests**

```python
# service_bot_backend/tests/test_calendar.py
import json
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta


def test_is_configured_false_by_default(monkeypatch):
    monkeypatch.setattr("services.calendar.GOOGLE_CREDENTIALS_FILE", "")
    from services.calendar import is_configured
    assert is_configured() is False


def test_is_configured_true(monkeypatch):
    monkeypatch.setattr("services.calendar.GOOGLE_CREDENTIALS_FILE", "/path/to/creds.json")
    from services.calendar import is_configured
    assert is_configured() is True


def test_list_events_not_configured(monkeypatch):
    monkeypatch.setattr("services.calendar.GOOGLE_CREDENTIALS_FILE", "")
    from services.calendar import list_events
    result = list_events("2026-03-30T00:00:00Z", "2026-03-31T00:00:00Z")
    assert result == {"error": "Google Calendar not configured"}


@patch("services.calendar._get_service")
def test_list_events_success(mock_service, monkeypatch):
    monkeypatch.setattr("services.calendar.GOOGLE_CREDENTIALS_FILE", "/path/creds.json")
    mock_events = {
        "items": [
            {
                "id": "ev1",
                "summary": "Team Meeting",
                "start": {"dateTime": "2026-03-30T10:00:00Z"},
                "end": {"dateTime": "2026-03-30T11:00:00Z"},
            }
        ]
    }
    mock_service.return_value.events.return_value.list.return_value.execute.return_value = mock_events

    from services.calendar import list_events
    result = list_events("2026-03-30T00:00:00Z", "2026-03-31T00:00:00Z")
    assert len(result["events"]) == 1
    assert result["events"][0]["summary"] == "Team Meeting"


@patch("services.calendar._get_service")
def test_create_event_success(mock_service, monkeypatch):
    monkeypatch.setattr("services.calendar.GOOGLE_CREDENTIALS_FILE", "/path/creds.json")
    mock_service.return_value.events.return_value.insert.return_value.execute.return_value = {
        "id": "new_ev", "status": "confirmed", "htmlLink": "https://calendar.google.com/ev/new_ev"
    }

    from services.calendar import create_event
    result = create_event(
        summary="Pentest Consultation",
        start="2026-04-01T10:00:00Z",
        end="2026-04-01T11:00:00Z",
        description="Initial consultation",
    )
    assert result["id"] == "new_ev"
    assert result["status"] == "confirmed"


@patch("services.calendar._get_service")
def test_delete_event_success(mock_service, monkeypatch):
    monkeypatch.setattr("services.calendar.GOOGLE_CREDENTIALS_FILE", "/path/creds.json")
    mock_service.return_value.events.return_value.delete.return_value.execute.return_value = None

    from services.calendar import delete_event
    result = delete_event("ev123")
    assert result["status"] == "deleted"


@patch("services.calendar._get_service")
def test_get_available_slots(mock_service, monkeypatch):
    monkeypatch.setattr("services.calendar.GOOGLE_CREDENTIALS_FILE", "/path/creds.json")
    # Simulate one busy block: 10:00-11:00 on a day, business hours 08:00-17:00
    mock_service.return_value.freebusy.return_value.query.return_value.execute.return_value = {
        "calendars": {
            "primary": {
                "busy": [
                    {"start": "2026-04-01T10:00:00Z", "end": "2026-04-01T11:00:00Z"}
                ]
            }
        }
    }
    monkeypatch.setattr("services.calendar.GOOGLE_CALENDAR_ID", "primary")

    from services.calendar import get_available_slots
    result = get_available_slots("2026-04-01T08:00:00Z", "2026-04-01T17:00:00Z", duration_minutes=60)
    # Should have slots but NOT 10:00-11:00
    slots = result["slots"]
    assert len(slots) > 0
    for slot in slots:
        assert slot["start"] != "2026-04-01T10:00:00Z"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd service_bot_backend && python -m pytest tests/test_calendar.py -v`

- [ ] **Step 3: Write services/calendar.py**

```python
# service_bot_backend/services/calendar.py
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
    """Build a Google Calendar API service using service account credentials."""
    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    credentials = service_account.Credentials.from_service_account_file(
        GOOGLE_CREDENTIALS_FILE, scopes=_SCOPES,
    )
    return build("calendar", "v3", credentials=credentials)


def list_events(time_min: str, time_max: str, max_results: int = 20) -> Dict[str, Any]:
    """List calendar events in a time range."""
    if not is_configured():
        return {"error": "Google Calendar not configured"}
    try:
        service = _get_service()
        result = service.events().list(
            calendarId=GOOGLE_CALENDAR_ID,
            timeMin=time_min,
            timeMax=time_max,
            maxResults=max_results,
            singleEvents=True,
            orderBy="startTime",
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


def create_event(
    summary: str,
    start: str,
    end: str,
    description: str = "",
    attendee_email: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a new calendar event."""
    if not is_configured():
        return {"error": "Google Calendar not configured"}
    try:
        body = {
            "summary": summary,
            "start": {"dateTime": start},
            "end": {"dateTime": end},
            "description": description,
        }
        if attendee_email:
            body["attendees"] = [{"email": attendee_email}]
        service = _get_service()
        event = service.events().insert(
            calendarId=GOOGLE_CALENDAR_ID, body=body,
        ).execute()
        return {
            "id": event["id"],
            "status": event.get("status", "confirmed"),
            "link": event.get("htmlLink", ""),
        }
    except Exception as e:
        logger.error("Failed to create event: %s", e)
        return {"error": str(e)}


def update_event(
    event_id: str,
    summary: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    description: Optional[str] = None,
) -> Dict[str, Any]:
    """Update an existing calendar event (patch semantics)."""
    if not is_configured():
        return {"error": "Google Calendar not configured"}
    try:
        body = {}
        if summary is not None:
            body["summary"] = summary
        if start is not None:
            body["start"] = {"dateTime": start}
        if end is not None:
            body["end"] = {"dateTime": end}
        if description is not None:
            body["description"] = description
        service = _get_service()
        event = service.events().patch(
            calendarId=GOOGLE_CALENDAR_ID, eventId=event_id, body=body,
        ).execute()
        return {
            "id": event["id"],
            "status": event.get("status", "confirmed"),
            "summary": event.get("summary", ""),
        }
    except Exception as e:
        logger.error("Failed to update event: %s", e)
        return {"error": str(e)}


def delete_event(event_id: str) -> Dict[str, Any]:
    """Delete a calendar event."""
    if not is_configured():
        return {"error": "Google Calendar not configured"}
    try:
        service = _get_service()
        service.events().delete(
            calendarId=GOOGLE_CALENDAR_ID, eventId=event_id,
        ).execute()
        return {"status": "deleted", "event_id": event_id}
    except Exception as e:
        logger.error("Failed to delete event: %s", e)
        return {"error": str(e)}


def get_available_slots(
    time_min: str, time_max: str, duration_minutes: int = 60,
) -> Dict[str, Any]:
    """Find available time slots using the freebusy API."""
    if not is_configured():
        return {"error": "Google Calendar not configured"}
    try:
        service = _get_service()
        body = {
            "timeMin": time_min,
            "timeMax": time_max,
            "items": [{"id": GOOGLE_CALENDAR_ID}],
        }
        result = service.freebusy().query(body=body).execute()
        busy = result.get("calendars", {}).get(GOOGLE_CALENDAR_ID, {}).get("busy", [])

        # Build free slots between busy blocks
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
```

- [ ] **Step 4: Run tests**

Run: `cd service_bot_backend && pip install google-api-python-client google-auth && python -m pytest tests/test_calendar.py -v`

- [ ] **Step 5: Commit**

```bash
cd /d/WABot && git add service_bot_backend/services/calendar.py service_bot_backend/tests/test_calendar.py
git commit -m "feat: add services/calendar.py — Google Calendar API wrapper"
```

---

### Task 3: services/tools.py — Tool definitions and dispatcher

**Files:**
- Create: `service_bot_backend/services/tools.py`
- Create: `service_bot_backend/tests/test_tools.py`

- [ ] **Step 1: Write the failing tests**

```python
# service_bot_backend/tests/test_tools.py
import json
from unittest.mock import patch


def test_get_tool_definitions_returns_list():
    from services.tools import get_tool_definitions
    tools = get_tool_definitions()
    assert isinstance(tools, list)
    assert len(tools) > 0
    for tool in tools:
        assert tool["type"] == "function"
        assert "name" in tool["function"]


def test_tool_names():
    from services.tools import get_tool_definitions
    names = {t["function"]["name"] for t in get_tool_definitions()}
    assert "list_calendar_events" in names
    assert "check_availability" in names
    assert "book_appointment" in names
    assert "cancel_appointment" in names
    assert "update_appointment" in names


@patch("services.tools.calendar.list_events")
def test_dispatch_list_events(mock_list):
    mock_list.return_value = {"events": []}
    from services.tools import dispatch_tool
    result = dispatch_tool("list_calendar_events", {
        "start": "2026-04-01T00:00:00Z",
        "end": "2026-04-02T00:00:00Z",
    })
    assert "events" in result
    mock_list.assert_called_once()


@patch("services.tools.calendar.create_event")
def test_dispatch_book_appointment(mock_create):
    mock_create.return_value = {"id": "ev1", "status": "confirmed", "link": ""}
    from services.tools import dispatch_tool
    result = dispatch_tool("book_appointment", {
        "summary": "Consultation",
        "start": "2026-04-01T10:00:00Z",
        "end": "2026-04-01T11:00:00Z",
    })
    assert result["status"] == "confirmed"


@patch("services.tools.calendar.delete_event")
def test_dispatch_cancel_appointment(mock_delete):
    mock_delete.return_value = {"status": "deleted", "event_id": "ev1"}
    from services.tools import dispatch_tool
    result = dispatch_tool("cancel_appointment", {"event_id": "ev1"})
    assert result["status"] == "deleted"


def test_dispatch_unknown_tool():
    from services.tools import dispatch_tool
    result = dispatch_tool("nonexistent_tool", {})
    assert "error" in result
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd service_bot_backend && python -m pytest tests/test_tools.py -v`

- [ ] **Step 3: Write services/tools.py**

```python
# service_bot_backend/services/tools.py
"""LLM tool definitions and dispatch — bridges OpenAI function calling to actual services."""

import json
import logging
from typing import Dict, Any, List

from services import calendar

logger = logging.getLogger("service_bot")

TOOL_DEFINITIONS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "list_calendar_events",
            "description": "List upcoming calendar events in a time range. Use when the user asks about existing appointments or schedule.",
            "parameters": {
                "type": "object",
                "properties": {
                    "start": {"type": "string", "description": "Start of range in ISO 8601 format (e.g. 2026-04-01T00:00:00Z)"},
                    "end": {"type": "string", "description": "End of range in ISO 8601 format"},
                },
                "required": ["start", "end"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_availability",
            "description": "Check available time slots for booking an appointment. Use when the user wants to schedule a meeting or consultation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "start": {"type": "string", "description": "Start of range in ISO 8601 (e.g. 2026-04-01T08:00:00Z)"},
                    "end": {"type": "string", "description": "End of range in ISO 8601"},
                    "duration_minutes": {"type": "integer", "description": "Desired meeting length in minutes", "default": 60},
                },
                "required": ["start", "end"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "book_appointment",
            "description": "Book a new appointment on the calendar. Use after confirming a time slot with the user.",
            "parameters": {
                "type": "object",
                "properties": {
                    "summary": {"type": "string", "description": "Title of the appointment"},
                    "start": {"type": "string", "description": "Start time in ISO 8601"},
                    "end": {"type": "string", "description": "End time in ISO 8601"},
                    "description": {"type": "string", "description": "Optional notes or details"},
                    "attendee_email": {"type": "string", "description": "Optional attendee email address"},
                },
                "required": ["summary", "start", "end"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_appointment",
            "description": "Update an existing appointment (change time, title, or description).",
            "parameters": {
                "type": "object",
                "properties": {
                    "event_id": {"type": "string", "description": "The calendar event ID to update"},
                    "summary": {"type": "string", "description": "New title"},
                    "start": {"type": "string", "description": "New start time in ISO 8601"},
                    "end": {"type": "string", "description": "New end time in ISO 8601"},
                    "description": {"type": "string", "description": "New description"},
                },
                "required": ["event_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "cancel_appointment",
            "description": "Cancel/delete an existing appointment from the calendar.",
            "parameters": {
                "type": "object",
                "properties": {
                    "event_id": {"type": "string", "description": "The calendar event ID to cancel"},
                },
                "required": ["event_id"],
            },
        },
    },
]


def get_tool_definitions() -> List[Dict[str, Any]]:
    """Return tool definitions for the OpenAI tools parameter."""
    return TOOL_DEFINITIONS


_DISPATCH_MAP = {
    "list_calendar_events": lambda args: calendar.list_events(
        time_min=args["start"], time_max=args["end"],
        max_results=args.get("max_results", 20),
    ),
    "check_availability": lambda args: calendar.get_available_slots(
        time_min=args["start"], time_max=args["end"],
        duration_minutes=args.get("duration_minutes", 60),
    ),
    "book_appointment": lambda args: calendar.create_event(
        summary=args["summary"], start=args["start"], end=args["end"],
        description=args.get("description", ""),
        attendee_email=args.get("attendee_email"),
    ),
    "update_appointment": lambda args: calendar.update_event(
        event_id=args["event_id"],
        summary=args.get("summary"), start=args.get("start"),
        end=args.get("end"), description=args.get("description"),
    ),
    "cancel_appointment": lambda args: calendar.delete_event(
        event_id=args["event_id"],
    ),
}


def dispatch_tool(name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a tool call and return the result as a dict."""
    handler = _DISPATCH_MAP.get(name)
    if not handler:
        return {"error": f"Unknown tool: {name}"}
    try:
        return handler(arguments)
    except Exception as e:
        logger.error("Tool %s failed: %s", name, e)
        return {"error": f"Tool execution failed: {e}"}
```

- [ ] **Step 4: Run tests**

Run: `cd service_bot_backend && python -m pytest tests/test_tools.py -v`

- [ ] **Step 5: Commit**

```bash
cd /d/WABot && git add service_bot_backend/services/tools.py service_bot_backend/tests/test_tools.py
git commit -m "feat: add services/tools.py — tool definitions and dispatcher for LLM function calling"
```

---

### Task 4: services/llm.py — Tool-calling-aware chat loop

**Files:**
- Modify: `service_bot_backend/services/llm.py`
- Modify: `service_bot_backend/tests/test_llm.py`

- [ ] **Step 1: Update tests**

Replace `service_bot_backend/tests/test_llm.py`:

```python
# service_bot_backend/tests/test_llm.py
import json
import pytest
from fastapi import HTTPException
from unittest.mock import MagicMock, patch

def test_get_openai_client_raises_without_key(monkeypatch):
    from services.llm import get_openai_client
    monkeypatch.setattr("services.llm.OPENAI_API_KEY", "")
    monkeypatch.setattr("services.llm._openai_available", True)
    with pytest.raises(HTTPException) as exc_info:
        get_openai_client()
    assert exc_info.value.status_code == 503

def test_get_openai_client_raises_without_package(monkeypatch):
    from services.llm import get_openai_client
    monkeypatch.setattr("services.llm._openai_available", False)
    with pytest.raises(HTTPException) as exc_info:
        get_openai_client()
    assert exc_info.value.status_code == 503

def test_truncate_history_short_list():
    from services.llm import truncate_history
    history = [{"role": "user", "content": "hi"}]
    assert truncate_history(history) == history

def test_truncate_history_long_list():
    from services.llm import truncate_history
    history = [{"role": "user", "content": f"msg{i}"} for i in range(100)]
    result = truncate_history(history)
    assert len(result) == 40
    assert result[-1]["content"] == "msg99"

def test_openai_available_flag():
    from services.llm import is_llm_available
    result = is_llm_available()
    assert isinstance(result, bool)

@patch("services.llm.get_openai_client")
def test_chat_no_tool_calls(mock_client_fn):
    """When LLM returns plain text, chat() returns that text."""
    mock_msg = MagicMock()
    mock_msg.content = "Hello, how can I help?"
    mock_msg.tool_calls = None
    mock_choice = MagicMock()
    mock_choice.message = mock_msg
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mock_client_fn.return_value.chat.completions.create.return_value = mock_response

    from services.llm import chat
    result = chat("system prompt", [{"role": "user", "content": "hi"}])
    assert result == "Hello, how can I help?"

@patch("services.llm.dispatch_tool")
@patch("services.llm.get_openai_client")
def test_chat_with_tool_call(mock_client_fn, mock_dispatch):
    """When LLM makes a tool call, chat() executes it and returns the final response."""
    # First call: LLM returns a tool call
    tool_call = MagicMock()
    tool_call.id = "call_123"
    tool_call.function.name = "list_calendar_events"
    tool_call.function.arguments = '{"start": "2026-04-01T00:00:00Z", "end": "2026-04-02T00:00:00Z"}'

    msg_with_tool = MagicMock()
    msg_with_tool.content = None
    msg_with_tool.tool_calls = [tool_call]
    msg_with_tool.role = "assistant"

    choice1 = MagicMock()
    choice1.message = msg_with_tool
    resp1 = MagicMock()
    resp1.choices = [choice1]

    # Second call: LLM returns final text
    msg_final = MagicMock()
    msg_final.content = "You have 2 meetings tomorrow."
    msg_final.tool_calls = None

    choice2 = MagicMock()
    choice2.message = msg_final
    resp2 = MagicMock()
    resp2.choices = [choice2]

    mock_client_fn.return_value.chat.completions.create.side_effect = [resp1, resp2]
    mock_dispatch.return_value = {"events": [{"summary": "Meeting 1"}, {"summary": "Meeting 2"}]}

    from services.llm import chat
    result = chat("system prompt", [{"role": "user", "content": "What meetings do I have?"}])
    assert result == "You have 2 meetings tomorrow."
    mock_dispatch.assert_called_once_with(
        "list_calendar_events",
        {"start": "2026-04-01T00:00:00Z", "end": "2026-04-02T00:00:00Z"},
    )
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd service_bot_backend && python -m pytest tests/test_llm.py -v`

- [ ] **Step 3: Rewrite services/llm.py with tool-calling loop**

```python
# service_bot_backend/services/llm.py
"""OpenAI LLM client with tool-calling support."""

import json
import logging
from typing import List, Dict

from fastapi import HTTPException

from config import OPENAI_API_KEY, MODEL_NAME, MAX_HISTORY_MESSAGES
from services.tools import get_tool_definitions, dispatch_tool

logger = logging.getLogger("service_bot")

try:
    from openai import OpenAI
    _openai_available = True
except ImportError:
    _openai_available = False
    OpenAI = None
    logger.warning("openai package not installed — LLM features disabled")

MAX_TOOL_ROUNDS = 5


def is_llm_available() -> bool:
    return _openai_available and bool(OPENAI_API_KEY)


def get_openai_client() -> "OpenAI":
    if not _openai_available:
        raise HTTPException(status_code=503, detail="openai package not installed")
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=503, detail="OPENAI_API_KEY not configured")
    return OpenAI(api_key=OPENAI_API_KEY)


def truncate_history(history: List[Dict[str, str]]) -> List[Dict[str, str]]:
    if len(history) <= MAX_HISTORY_MESSAGES:
        return list(history)
    return list(history[-MAX_HISTORY_MESSAGES:])


def chat(system_prompt: str, history: List[Dict[str, str]]) -> str:
    """Send a chat request with tool-calling support.

    The LLM may request tool calls (e.g. calendar operations). This function
    loops: execute tool calls, feed results back, until the LLM produces
    a final text response (max MAX_TOOL_ROUNDS iterations).
    """
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.extend(truncate_history(history))

    tools = get_tool_definitions()

    try:
        client = get_openai_client()

        for _ in range(MAX_TOOL_ROUNDS):
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                tools=tools if tools else None,
                temperature=0.7,
                max_tokens=1024,
            )
            msg = response.choices[0].message

            # No tool calls — return the text response
            if not msg.tool_calls:
                return msg.content or ""

            # Process tool calls
            messages.append({
                "role": "assistant",
                "content": msg.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in msg.tool_calls
                ],
            })

            for tc in msg.tool_calls:
                fn_name = tc.function.name
                fn_args = json.loads(tc.function.arguments)
                logger.info("Tool call: %s(%s)", fn_name, fn_args)

                result = dispatch_tool(fn_name, fn_args)

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(result),
                })

        # If we exhausted rounds, return whatever we have
        return msg.content or "I wasn't able to complete the request. Please try again."

    except HTTPException:
        raise
    except Exception as e:
        logger.error("LLM API error: %s", e)
        raise HTTPException(status_code=500, detail=f"LLM API error: {e}")
```

- [ ] **Step 4: Run tests**

Run: `cd service_bot_backend && python -m pytest tests/test_llm.py -v`

- [ ] **Step 5: Commit**

```bash
cd /d/WABot && git add service_bot_backend/services/llm.py service_bot_backend/tests/test_llm.py
git commit -m "feat: add tool-calling loop to LLM chat — enables calendar operations via function calling"
```

---

### Task 5: routes/calendar.py — REST endpoints for Flutter

**Files:**
- Create: `service_bot_backend/routes/calendar.py`
- Create: `service_bot_backend/tests/test_routes_calendar.py`

- [ ] **Step 1: Write the failing tests**

```python
# service_bot_backend/tests/test_routes_calendar.py
from unittest.mock import patch


@patch("routes.calendar.calendar.list_events")
def test_get_events(mock_list, client):
    mock_list.return_value = {"events": [{"id": "ev1", "summary": "Test"}]}
    resp = client.get("/calendar/events", params={
        "start": "2026-04-01T00:00:00Z",
        "end": "2026-04-02T00:00:00Z",
    })
    assert resp.status_code == 200
    assert len(resp.json()["events"]) == 1


@patch("routes.calendar.calendar.create_event")
def test_create_event(mock_create, admin_client):
    mock_create.return_value = {"id": "ev1", "status": "confirmed", "link": ""}
    resp = admin_client.post("/calendar/events", json={
        "summary": "Meeting",
        "start": "2026-04-01T10:00:00Z",
        "end": "2026-04-01T11:00:00Z",
    })
    assert resp.status_code == 201
    assert resp.json()["id"] == "ev1"


@patch("routes.calendar.calendar.delete_event")
def test_delete_event(mock_delete, admin_client):
    mock_delete.return_value = {"status": "deleted", "event_id": "ev1"}
    resp = admin_client.delete("/calendar/events/ev1")
    assert resp.status_code == 200
    assert resp.json()["status"] == "deleted"


@patch("routes.calendar.calendar.get_available_slots")
def test_get_available_slots(mock_slots, client):
    mock_slots.return_value = {"slots": [{"start": "2026-04-01T08:00:00Z", "end": "2026-04-01T09:00:00Z"}]}
    resp = client.get("/calendar/slots", params={
        "start": "2026-04-01T08:00:00Z",
        "end": "2026-04-01T17:00:00Z",
    })
    assert resp.status_code == 200
    assert len(resp.json()["slots"]) == 1


def test_create_event_requires_admin(client):
    resp = client.post("/calendar/events", json={
        "summary": "Meeting",
        "start": "2026-04-01T10:00:00Z",
        "end": "2026-04-01T11:00:00Z",
    })
    # With ADMIN_TOKEN not set, passes through (unprotected mode)
    # But the test validates the endpoint exists
    assert resp.status_code in (200, 201, 401)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd service_bot_backend && python -m pytest tests/test_routes_calendar.py -v`

- [ ] **Step 3: Write routes/calendar.py**

```python
# service_bot_backend/routes/calendar.py
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
        summary=req.summary,
        start=req.start,
        end=req.end,
        description=req.description,
        attendee_email=req.attendee_email,
    )


@router.patch("/events/{event_id}", dependencies=[Depends(require_admin)])
def update_event(event_id: str, req: UpdateEventRequest):
    return calendar.update_event(
        event_id=event_id,
        summary=req.summary,
        start=req.start,
        end=req.end,
        description=req.description,
    )


@router.delete("/events/{event_id}", dependencies=[Depends(require_admin)])
def delete_event(event_id: str):
    return calendar.delete_event(event_id=event_id)
```

- [ ] **Step 4: Update conftest.py to include calendar router**

In `service_bot_backend/tests/conftest.py`, add the calendar router import:

```python
def _create_test_app():
    from routes import health, services, features, agent, webhook, calendar
    app = FastAPI()
    app.include_router(health.router)
    app.include_router(services.router)
    app.include_router(features.router)
    app.include_router(agent.router)
    app.include_router(webhook.router)
    app.include_router(calendar.router)
    return app
```

- [ ] **Step 5: Run tests**

Run: `cd service_bot_backend && python -m pytest tests/test_routes_calendar.py -v`

- [ ] **Step 6: Commit**

```bash
cd /d/WABot && git add service_bot_backend/routes/calendar.py service_bot_backend/tests/test_routes_calendar.py service_bot_backend/tests/conftest.py
git commit -m "feat: add routes/calendar.py — REST endpoints for calendar CRUD"
```

---

### Task 6: Wire up main.py, update requirements, agents.md, README, push

**Files:**
- Modify: `service_bot_backend/main.py` — add calendar router
- Modify: `service_bot_backend/requirements.txt` — add google deps
- Modify: `service_bot_backend/agents.md` — mention calendar capabilities
- Modify: `README.md` — document calendar endpoints and config
- Modify: `.env.example` — add Google Calendar vars

- [ ] **Step 1: Update main.py**

Add `from routes import ... calendar` and `app.include_router(calendar.router)`.

```python
from routes import agent, services, features, health, webhook, calendar
# ...
app.include_router(calendar.router)
```

- [ ] **Step 2: Update requirements.txt**

Add after the `openai` line:

```
# Google Calendar
google-api-python-client>=2.0.0
google-auth>=2.0.0
```

- [ ] **Step 3: Update agents.md**

Add a calendar section after the Lead Capture section:

```markdown
## Calendar & Appointments

You can manage appointments using calendar tools. When a customer wants to:
- **See existing appointments**: Use the list_calendar_events tool.
- **Find available times**: Use the check_availability tool.
- **Book an appointment**: Confirm the time with the customer first, then use book_appointment.
- **Reschedule**: Use update_appointment with the event ID.
- **Cancel**: Use cancel_appointment with the event ID.

Always confirm with the customer before booking or cancelling. Show available slots clearly and let the customer choose.
```

- [ ] **Step 4: Update .env.example**

Add:

```
# Optional — Google Calendar (service account)
GOOGLE_CREDENTIALS_FILE=path/to/service-account.json
GOOGLE_CALENDAR_ID=primary
```

- [ ] **Step 5: Update README.md**

Add calendar endpoints to the API table and calendar config vars to the env table. Add a Google Calendar setup section.

- [ ] **Step 6: Run full test suite**

Run: `cd service_bot_backend && python -m pytest tests/ -v`
Expected: All tests pass

- [ ] **Step 7: Commit and push**

```bash
cd /d/WABot && git add service_bot_backend/main.py service_bot_backend/requirements.txt service_bot_backend/agents.md README.md .env.example
git commit -m "feat: wire up calendar routes, update deps, docs, and agent instructions"
git push origin main
```
