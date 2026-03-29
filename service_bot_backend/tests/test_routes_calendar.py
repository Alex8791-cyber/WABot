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


def test_create_event_requires_admin(client, monkeypatch):
    monkeypatch.setattr("auth.ADMIN_TOKEN", "secret")
    resp = client.post("/calendar/events", json={
        "summary": "Meeting",
        "start": "2026-04-01T10:00:00Z",
        "end": "2026-04-01T11:00:00Z",
    })
    assert resp.status_code == 401
