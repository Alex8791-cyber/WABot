from unittest.mock import patch


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
    slots = result["slots"]
    assert len(slots) > 0
    for slot in slots:
        assert slot["start"] != "2026-04-01T10:00:00Z"
