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
    assert "create_payment_link" in names
    assert "calculate_distance" in names


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


@patch("services.tools.payments.create_payment_link")
def test_dispatch_create_payment_link(mock_create):
    mock_create.return_value = {"reference": "ref_123", "payment_url": "https://paystack.com/pay/123"}
    from services.tools import dispatch_tool
    result = dispatch_tool("create_payment_link", {
        "service_name": "Pentesting",
        "amount": 5000000,
        "email": "test@test.co.za",
    })
    assert result["payment_url"] == "https://paystack.com/pay/123"


@patch("services.tools.distance.calculate_distance")
def test_dispatch_calculate_distance(mock_calc):
    mock_calc.return_value = {"distance_km": 15.3, "business_location": {}, "customer_location": {}}
    from services.tools import dispatch_tool
    result = dispatch_tool("calculate_distance", {"customer_address": "123 Main Road, Sandton"})
    assert result["distance_km"] == 15.3


def test_dispatch_unknown_tool():
    from services.tools import dispatch_tool
    result = dispatch_tool("nonexistent_tool", {})
    assert "error" in result
